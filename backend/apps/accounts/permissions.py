from django.core.exceptions import ImproperlyConfigured
from rest_framework.permissions import BasePermission

from apps.audit import service as audit

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

    권한 없는 접근은 audit_log에 `action='deny'`로 남는다(§2 체크리스트). 단 익명 요청은
    남기지 않는다 — 로그인한 운영자가 자기 역할 밖을 시도한 경우만 의미 있는 보안 사건이고,
    익명까지 남기면 스캐너 트래픽으로 장부가 덮인다.
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
        if resource is None and hasattr(view, "get_resource"):
            # 업로드처럼 대상 화면이 요청 본문에 실려오는 경우. 권한 판정은 여전히
            # 라우트 진입 지점(이 클래스)에서 한 번에 한다 — §2.
            resource = view.get_resource(request)
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

        allowed = AdminPermission.objects.filter(
            role_id=user.admin_profile.role_id,
            resource=resource,
            action=required_action,
            allowed=True,
        ).exists()

        if not allowed:
            audit.record_denied(resource, required_action, path=request.path)
        return allowed
