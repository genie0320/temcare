"""감사로그·접속기록 조회 API (adm_028).

기록하는 쪽(signals.py)은 M1부터 돌고 있었는데 **읽는 쪽이 없었다.** 2년 보관하는
로그를 볼 방법이 없는 상태였다. docs/11_audit_viewer.md.

★ 이 모듈에는 쓰기 경로가 하나도 없다. audit_log는 append-only이고
  (docs/02_architecture_constraints.md §8), 쓰기 경로를 만드는 순간 장부가 장부이기를
  그만둔다. ModelViewSet을 쓰지 않는 것도 그래서다 — 삭제·편집은 영원히 만들지 않는다.
"""

from datetime import date

from django.conf import settings
from django.db.models import Count, Max, Min
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import AdminResourcePermission

from . import service as audit
from .models import AccessLog, AuditLog
from .serializers import AccessLogSerializer, AuditLogDetailSerializer, AuditLogListSerializer

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

# adm_030(파기 관리)이 붙기 전까지 로그를 지우는 코드는 어디에도 없다. 화면에
# "2년 보관"이라고 쓰면 **지키지 않는 약속을 박아두는 것**이 되므로, 정책 문구 대신
# 지금 상태를 그대로 내보낸다. docs/11_audit_viewer.md §7.
PURGE_NOTE = "자동 파기 미구현 — adm_030 파기 관리 예정"


class _AuditReadView(APIView):
    """감사로그 조회 뷰의 공통 뼈대. **GET만 있다.**

    PUBLIC_DEMO 차단이 여기 한 곳에 있다 — 터널은 고객 앱(5173)만 열지만 그 Vite
    proxy가 /api를 같은 Django로 넘기므로, 감사로그 API도 터널 너머에서 도달 가능하다.
    dev-login이 막혀 있어 로그인은 못 하지만 문을 하나 더 잠근다
    (apps/accounts/views.py의 dev_login과 같은 방식). docs/11_audit_viewer.md §4-4.
    """

    permission_classes = [AdminResourcePermission]
    resource = "adm_028"
    required_action = "read"

    def initial(self, request, *args, **kwargs):
        # 권한 검사(super().initial)보다 **먼저** 막는다. 공개된 서버에서는 이 경로가
        # 존재하지 않는 것처럼 보여야 하고, 스캐너 트래픽이 deny 로그로 장부를 덮지도 않는다.
        if getattr(settings, "PUBLIC_DEMO", False):
            raise NotFound("공개 데모에서는 사용할 수 없다.")
        super().initial(request, *args, **kwargs)


def _parse_date(raw: str, label: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValidationError({label: ["YYYY-MM-DD 형식이어야 한다."]}) from exc


def _apply_period(queryset, params):
    """기간 필터(시트2 요소3). USE_TZ=True라 __date 조회가 Asia/Seoul 기준으로 잘린다."""
    if raw := params.get("date_from"):
        queryset = queryset.filter(created_at__date__gte=_parse_date(raw, "date_from"))
    if raw := params.get("date_to"):
        queryset = queryset.filter(created_at__date__lte=_parse_date(raw, "date_to"))
    return queryset


def _paginate(queryset, params, serializer_class):
    """페이지네이션. 감사로그는 계속 쌓이므로 목록은 반드시 서버에서 잘라 보낸다.

    ★ 자른 사실을 count로 항상 같이 보낸다 — 화면이 '이게 전부'라고 착각하면
      감사로그가 비어 보이는 것과 같은 오독이 생긴다.
    """
    try:
        page = max(1, int(params.get("page") or 1))
        page_size = min(MAX_PAGE_SIZE, max(1, int(params.get("page_size") or DEFAULT_PAGE_SIZE)))
    except ValueError as exc:
        raise ValidationError({"page": ["정수여야 한다."]}) from exc

    total = queryset.count()
    start = (page - 1) * page_size
    rows = queryset[start : start + page_size]
    return {
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": serializer_class(rows, many=True).data,
    }


class AuditSummaryView(_AuditReadView):
    """★ "얼만큼" — 이 화면에서 사용자가 실제로 보고 싶은 것.

    어느 대상 테이블에 어떤 행위가 몇 건씩 남고 있는지, 가장 오래된/최근 기록이 언제인지.
    목록보다 이쪽이 먼저다(docs/11_audit_viewer.md §3).

    집계에 .values()/.annotate()를 쓴다 — 금지된 감사로그 우회 4종은 쓰기 계열이고
    이건 읽기다(§4-6).
    """

    def get(self, request):
        return Response(
            {
                "audit_log": self._audit_log_summary(),
                "access_log": self._access_log_summary(),
                # 정책 문구("2년 보관")를 넣지 않는다. 지금 상태만 사실대로 알린다.
                "purge": {"implemented": False, "note": PURGE_NOTE},
            }
        )

    @staticmethod
    def _audit_log_summary() -> dict:
        span = AuditLog.objects.aggregate(oldest_at=Min("created_at"), latest_at=Max("created_at"))

        by_action = list(AuditLog.objects.values("action").annotate(count=Count("id")).order_by("-count"))

        tables = list(
            AuditLog.objects.values("target_table")
            .annotate(total=Count("id"), oldest_at=Min("created_at"), latest_at=Max("created_at"))
            .order_by("-total", "target_table")
        )
        # 테이블 × 액션 교차 건수. 별도 질의로 뽑아 위 결과에 붙인다.
        cross: dict[str, dict[str, int]] = {}
        for row in AuditLog.objects.values("target_table", "action").annotate(count=Count("id")):
            cross.setdefault(row["target_table"], {})[row["action"]] = row["count"]
        for row in tables:
            row["actions"] = cross.get(row["target_table"], {})

        return {
            "total": AuditLog.objects.count(),
            "oldest_at": span["oldest_at"],
            "latest_at": span["latest_at"],
            "by_action": by_action,
            "by_table": tables,
        }

    @staticmethod
    def _access_log_summary() -> dict:
        """건수와 시각만. 개인정보는 한 톨도 나가지 않으므로 pii_read를 요구하지 않는다.

        ★ 오히려 이 숫자가 이 화면의 핵심 진단값이다 — record_access()가 아직 아무 데서도
          호출되지 않아 0건일 것이고, "개인정보 열람이 기록되고 있지 않다"는 사실이
          여기서 눈에 보여야 한다.
        """
        span = AccessLog.objects.aggregate(oldest_at=Min("created_at"), latest_at=Max("created_at"))
        return {
            "total": AccessLog.objects.count(),
            "oldest_at": span["oldest_at"],
            "latest_at": span["latest_at"],
        }


class AuditLogListView(_AuditReadView):
    """데이터 변경 이력 목록(시트2 요소1). 필터: 기간·행위자·액션·대상테이블(요소3)."""

    def get(self, request):
        params = request.query_params
        queryset = AuditLog.objects.all().order_by("-created_at", "-id")
        queryset = _apply_period(queryset, params)
        if actor := params.get("actor"):
            queryset = queryset.filter(actor_id=actor)
        if action := params.get("action"):
            queryset = queryset.filter(action=action)
        if target_table := params.get("target_table"):
            queryset = queryset.filter(target_table=target_table)

        return Response(_paginate(queryset, params, AuditLogListSerializer))


class AuditLogDetailView(_AuditReadView):
    """변경 전/후 **전문**(시트2 요소4). 목록에서 잘라 보낸 것을 여기서 다 준다."""

    def get(self, request, pk):
        try:
            log = AuditLog.objects.get(pk=pk)
        except AuditLog.DoesNotExist as exc:
            raise NotFound("해당 감사로그가 없다.") from exc
        return Response(AuditLogDetailSerializer(log).data)


class AccessLogListView(_AuditReadView):
    """개인정보 열람 이력 목록(시트2 요소2).

    ★★ 이 화면 전체에서 가장 중요한 안전장치가 여기다.

    audit_log는 audit_secret_fields로 개인정보가 마스킹돼 있지만(docs/06_decisions.md #32)
    access_log에는 그런 장치가 **없다** — target_user(회원 식별자) · fields(열람 항목) ·
    purpose(열람 사유)가 원문 그대로 들어 있다. 그래서 같은 화면·같은 resource라도
    행위(action)를 분리한다:

        required_action = "pii_read"    ← read가 아니다

    CLAUDE.md §2-1 "개인정보 열람 권한은 콘텐츠 편집 권한과 분리한다".
    EDITOR_ACTIONS에 pii_read가 없으므로 에디터는 여기서 막힌다. 이 한 줄을 "read"로
    바꾸면 콘텐츠 에디터가 회원 개인정보 열람 이력을 통째로 볼 수 있게 된다.
    """

    required_action = "pii_read"

    def get(self, request):
        params = request.query_params
        queryset = AccessLog.objects.all().order_by("-created_at", "-id")
        queryset = _apply_period(queryset, params)
        filters = {}
        if actor := params.get("actor"):
            queryset = queryset.filter(actor_id=actor)
            filters["actor"] = actor
        if target_user := params.get("target_user"):
            queryset = queryset.filter(target_user=target_user)
            filters["target_user"] = target_user
        for key in ("date_from", "date_to"):
            if value := params.get(key):
                filters[key] = value

        payload = _paginate(queryset, params, AccessLogSerializer)
        # 접속기록을 들여다본 행위 자체를 남긴다 — access_log가 아니라 audit_log에.
        # 이유는 service.record_access_log_view()의 주석 참고(docs/11_audit_viewer.md §7).
        audit.record_access_log_view(filters=filters, returned=len(payload["results"]))
        return Response(payload)
