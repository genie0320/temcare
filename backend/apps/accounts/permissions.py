from django.core.exceptions import ImproperlyConfigured
from rest_framework.permissions import BasePermission

from .models import AdminPermission


class AdminResourcePermission(BasePermission):
    """뷰에 선언된 resource/action을 admin_permission 매트릭스로 판정한다.

    docs/02_architecture_constraints.md §2 — 화면마다 개별 검사가 아니라 이 클래스
    하나로 전 관리자 API를 통과시킨다. 사용법:

        class NutrientDetailView(APIView):
            permission_classes = [AdminResourcePermission]
            resource = "adm_022"
            required_action = "write"   # read | write | delete | publish | pii_read

    ★ TODO(M1): "권한 없는 접근이 감사로그에 남는가" 체크리스트(§2)는 아직 미구현.
    AuditLog의 action 종류(create/update/delete/publish/export)에 '거부' 개념이
    없어서 관리자 API가 실제로 붙는 M1에서 로그 형태를 같이 정하고 채운다.
    """

    def has_permission(self, request, view):
        resource = getattr(view, "resource", None)
        required_action = getattr(view, "required_action", None)
        if resource is None or required_action is None:
            raise ImproperlyConfigured(
                f"{view.__class__.__name__}는 AdminResourcePermission을 쓰려면 "
                "resource와 required_action을 선언해야 한다."
            )

        user = request.user
        if not user.is_authenticated or not hasattr(user, "admin_profile"):
            return False

        return AdminPermission.objects.filter(
            role_id=user.admin_profile.role_id,
            resource=resource,
            action=required_action,
            allowed=True,
        ).exists()
