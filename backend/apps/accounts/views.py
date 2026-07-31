from django.conf import settings
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import AdminLoginLog


def _client_ip(request) -> str | None:
    return request.META.get("REMOTE_ADDR")


def _serialize_admin(user) -> dict:
    profile = getattr(user, "admin_profile", None)
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": profile.role_id if profile else None,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    """프론트가 로그인 전에 호출해 csrftoken 쿠키를 심는다. docs/08_tech_stack.md §3."""
    return Response({"csrfToken": get_token(request)})


@api_view(["GET"])
@permission_classes([AllowAny])
def me(request):
    """현재 세션의 관리자 정보. 비로그인이면 authenticated=false만 돌려준다."""
    user = request.user
    if not user.is_authenticated or not hasattr(user, "admin_profile"):
        return Response({"authenticated": False})
    return Response({"authenticated": True, **_serialize_admin(user)})


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """관리자 이메일+비밀번호 로그인. docs/08_tech_stack.md §3 — 세션 쿠키 발급."""
    email = request.data.get("email", "")
    password = request.data.get("password", "")
    user = authenticate(request, username=email, password=password)

    success = bool(user and hasattr(user, "admin_profile"))
    AdminLoginLog.objects.create(
        account=user if success else None,
        email=email,
        success=success,
        ip=_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
    )
    if not success:
        return Response({"detail": "이메일 또는 비밀번호가 올바르지 않다."}, status=status.HTTP_401_UNAUTHORIZED)

    django_login(request, user)
    return Response({"authenticated": True, **_serialize_admin(user)})


@api_view(["POST"])
@permission_classes([AllowAny])
def dev_login(request):
    """개발 전용 빠른 로그인 — 비밀번호 없이 시드 관리자 계정으로 진입한다.

    docs/08_tech_stack.md §6-4: DEBUG=True에서만 열리고 프로덕션에서는 물리적으로 차단된다.
    """
    if not settings.DEBUG:
        return Response({"detail": "DEBUG 모드에서만 사용할 수 있다."}, status=status.HTTP_404_NOT_FOUND)

    from .models import User  # noqa: PLC0415 — DEBUG 전용 경로라 지연 임포트로 충분

    try:
        user = User.objects.get(username="admin@ollacare.local")
    except User.DoesNotExist:
        return Response(
            {"detail": "시드 관리자 계정이 없다. `make setup`(seed_demo)을 먼저 실행할 것."},
            status=status.HTTP_404_NOT_FOUND,
        )

    AdminLoginLog.objects.create(
        account=user, email=user.email, success=True, ip=_client_ip(request), user_agent="dev-login"
    )
    django_login(request, user)
    return Response({"authenticated": True, **_serialize_admin(user)})


@api_view(["POST"])
@permission_classes([AllowAny])
def logout(request):
    django_logout(request)
    return Response({"authenticated": False})
