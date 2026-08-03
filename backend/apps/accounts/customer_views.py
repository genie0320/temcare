"""고객용 인증 API. 관리자용(views.py)과 경로를 나눈다 — `/api/auth/*`.

같은 AUTH_USER_MODEL을 쓰지만 성격이 다르다. 관리자 `/api/accounts/me/`는
admin_profile이 없으면 비로그인으로 취급하는데, 고객은 admin_profile이 없는 게
정상이라 같은 엔드포인트를 쓸 수 없다.

가입 흐름(docs/07_milestones.md M2 · docs/06_decisions.md #13):
    sc_091 이메일·비밀번호 입력(클라이언트 보관)
    → sc_092 약관 동의 → **여기서 signup 한 번에 전송**
    → SIGNUP-02 닉네임(PATCH me) → sc_093 → 결과 상세

★ 계정 생성과 동의 기록을 한 트랜잭션으로 묶은 이유: 동의 없이 이메일부터 저장하는
  상태가 단 한 순간도 생기지 않게 하기 위함이다(docs/02_architecture_constraints.md §4).
"""

from datetime import date

from django.contrib.auth import login as django_login, logout as django_logout
from django.db import transaction
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.consent.models import ConsentItem, UserConsent

from .models import User
from .nickname import suggest_nickname, validate_nickname
from .providers import AuthError, get_auth_provider


def _client_ip(request) -> str | None:
    return request.META.get("REMOTE_ADDR")


def _serialize(user) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "status": user.status,
        "birthDate": user.birth_date.isoformat() if user.birth_date else None,
        "gender": user.gender,
        "heightCm": user.height_cm,
        "weightKg": user.weight_kg,
    }


def _auth_error(exc: AuthError, http_status=status.HTTP_400_BAD_REQUEST) -> Response:
    return Response({"detail": exc.message, "code": exc.code}, status=http_status)


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    """비GET 요청 전에 csrftoken 쿠키를 심는다. docs/08_tech_stack.md §3."""
    return Response({"csrfToken": get_token(request)})


@api_view(["GET", "PATCH"])
@permission_classes([AllowAny])
def me(request):
    """GET: 현재 세션의 고객 정보. PATCH: 닉네임 변경(SIGNUP-02 · 더보기)."""
    user = request.user
    if not user.is_authenticated:
        return Response({"authenticated": False})

    if request.method == "PATCH":
        nickname = request.data.get("nickname")
        if nickname is not None:
            reason = validate_nickname(nickname)
            if reason:
                return Response({"detail": reason, "code": "invalid_nickname"}, status=status.HTTP_400_BAD_REQUEST)
            user.nickname = nickname.strip()
            user.save(update_fields=["nickname"])  # audit: 인스턴스 save라 시그널이 뜬다

    return Response({"authenticated": True, **_serialize(user)})


@api_view(["GET"])
@permission_classes([AllowAny])
def nickname_suggestion(request):
    """SIGNUP-02의 '다른 닉네임으로 변경' — 새 후보 하나를 준다."""
    return Response({"nickname": suggest_nickname()})


def _required_item_ids() -> set[str]:
    return set(ConsentItem.objects.filter(required=True, status="게시").values_list("id", flat=True))


def _record_consents(user, agreed_ids: set[str], ip: str | None) -> None:
    """동의 이력을 append-only로 남긴다.

    ★ bulk_create를 쓰지 않는다 — 감사로그 시그널이 뜨지 않는다(CLAUDE.md §5).
      항목이 5~6개뿐이라 개별 create의 비용도 문제되지 않는다.
    """
    for item in ConsentItem.objects.filter(status="게시"):
        UserConsent.objects.create(user=user, item=item, agreed=item.id in agreed_ids, ip=ip)


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """이메일 가입 + 동의 기록을 한 번에 처리한다(sc_091 + sc_092).

    body: {
      email, password,
      consents: ["tos", "privacy", "sensitive", "age14", ...],   # 동의한 항목 id 목록
      birthDate?: "YYYY-MM-DD", gender?: "남성"|"여성"            # PPT SURVEY-01
    }
    """
    if request.user.is_authenticated:
        return Response({"detail": "이미 로그인돼 있어요.", "code": "already_logged_in"}, status=status.HTTP_409_CONFLICT)

    agreed_ids = set(request.data.get("consents") or [])
    required = _required_item_ids()
    missing = required - agreed_ids
    if missing:
        names = list(ConsentItem.objects.filter(id__in=missing).values_list("name", flat=True))
        return Response(
            {"detail": "필수 동의 항목에 모두 동의해야 가입할 수 있어요.", "code": "consent_required", "missing": names},
            status=status.HTTP_400_BAD_REQUEST,
        )

    provider = get_auth_provider(request.data.get("provider", "email"))
    try:
        with transaction.atomic():
            user = provider.signup(request, request.data)

            fields = []
            raw_birth = request.data.get("birthDate")
            if raw_birth:
                try:
                    user.birth_date = date.fromisoformat(raw_birth)
                except (TypeError, ValueError) as exc:
                    raise AuthError("생년월일 형식이 올바르지 않아요.", code="invalid_birth_date") from exc
                fields.append("birth_date")

            gender = request.data.get("gender")
            if gender:
                if gender not in dict(User.GENDER_CHOICES):
                    raise AuthError("성별 값이 올바르지 않아요.", code="invalid_gender")
                user.gender = gender
                fields.append("gender")

            # 키·몸무게(화면설계서 '홈 > TEM문진' #3·#4). 사람의 범위를 벗어난 값은
            # 오타이거나 장난이다 — 저장해두면 나중에 통계를 망친다.
            for key, field, low, high in (
                ("heightCm", "height_cm", 50, 250),
                ("weightKg", "weight_kg", 10, 300),
            ):
                raw = request.data.get(key)
                if raw in (None, ""):
                    continue
                try:
                    value = int(raw)
                except (TypeError, ValueError) as exc:
                    raise AuthError("키·몸무게는 숫자로 입력해주세요.", code="invalid_body_metric") from exc
                if not (low <= value <= high):
                    raise AuthError("키·몸무게 값을 다시 확인해주세요.", code="invalid_body_metric")
                setattr(user, field, value)
                fields.append(field)
            if not user.nickname:
                user.nickname = suggest_nickname()
                fields.append("nickname")
            if fields:
                user.save(update_fields=fields)

            _record_consents(user, agreed_ids, _client_ip(request))
    except AuthError as exc:
        conflict = exc.code == "duplicate_email"
        return _auth_error(exc, status.HTTP_409_CONFLICT if conflict else status.HTTP_400_BAD_REQUEST)

    django_login(request, user)
    return Response({"authenticated": True, **_serialize(user)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    provider = get_auth_provider(request.data.get("provider", "email"))
    try:
        user = provider.login(request, request.data)
    except AuthError as exc:
        return _auth_error(exc, status.HTTP_401_UNAUTHORIZED)

    if user.status in ("탈퇴", "탈퇴예정"):
        return Response({"detail": "탈퇴 처리된 계정이에요.", "code": "withdrawn"}, status=status.HTTP_403_FORBIDDEN)

    django_login(request, user)
    return Response({"authenticated": True, **_serialize(user)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    django_logout(request)
    return Response({"authenticated": False})
