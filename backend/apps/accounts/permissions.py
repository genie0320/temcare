from django.core.exceptions import ImproperlyConfigured
from rest_framework.permissions import BasePermission

from .models import AdminPermission


class AdminResourcePermission(BasePermission):
    """뷰에 선언된 resource/action을 admin_permission 매트릭스로 판정한다.

    docs/02_architecture_constraints.md §2 — 화면마다 개별 검사가 아니라 이 클래스
    하나로 전 관리자 API를 통과시킨다. 두 가지 사용법:

        # 1) 단일 액션 APIView
        class NutrientDetailView(APIView):
            permission_classes = [AdminResourcePermission]
            resource = "adm_022"
            required_action = "write"   # read | write | delete | publish | pii_read

        # 2) DRF ViewSet — action별로 자동 매핑(ACTION_MAP)한다. 필요하면
        #    view.resource_action_map으로 재정의.
        class WeaknessViewSet(ModelViewSet):
            permission_classes = [AdminResourcePermission]
            resource = "adm_003"

    ★ TODO(M1): "권한 없는 접근이 감사로그에 남는가" 체크리스트(§2)는 아직 미구현.
    AuditLog의 action 종류(create/update/delete/publish/export)에 '거부' 개념이
    없어서 관리자 API가 실제로 붙는 M1에서 로그 형태를 같이 정하고 채운다.
    """

    ACTION_MAP = {
        "list": "read",
        "retrieve": "read",
        "create": "write",
        "update": "write",
        "partial_update": "write",
        "destroy": "delete",
    }

    def has_permission(self, request, view):
        resource = getattr(view, "resource", None)
        if resource is None:
            raise ImproperlyConfigured(
                f"{view.__class__.__name__}는 AdminResourcePermission을 쓰려면 resource를 선언해야 한다."
            )

        viewset_action = getattr(view, "action", None)
        if viewset_action is not None:
            # ★ DRF ViewSetMixin이 이미 `action_map`(http method → action명)을 쓰고 있어
            # 이름이 겹치면 안 된다. 커스텀 매핑은 반드시 resource_action_map으로 재정의.
            action_map = getattr(view, "resource_action_map", self.ACTION_MAP)
            required_action = action_map.get(viewset_action)
            if required_action is None:
                raise ImproperlyConfigured(
                    f"{view.__class__.__name__}.action '{viewset_action}'에 대한 권한 매핑이 없다."
                )
        else:
            required_action = getattr(view, "required_action", None)
            if required_action is None:
                raise ImproperlyConfigured(
                    f"{view.__class__.__name__}는 required_action을 선언해야 한다."
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
