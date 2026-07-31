import re

from django.db.models import Q
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import AdminResourcePermission

from .models import Weakness
from .serializers import WeaknessDetailSerializer, WeaknessListSerializer

_ID_RE = re.compile(r"^WEAK-(\d+)$")


def _next_weakness_id() -> str:
    max_n = 0
    for wid in Weakness.objects.values_list("id", flat=True):
        m = _ID_RE.match(wid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"WEAK-{max_n + 1:02d}"


class WeaknessViewSet(ModelViewSet):
    """약점 / IDEA 마스터(adm_003). docs/05_screen_conventions.md의 목록·상세 규격을 따른다."""

    permission_classes = [AdminResourcePermission]
    resource = "adm_003"
    queryset = Weakness.objects.all()

    def get_serializer_class(self):
        return WeaknessListSerializer if self.action == "list" else WeaknessDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(id__icontains=search))
        wtype = self.request.query_params.get("wtype")
        if wtype:
            qs = qs.filter(wtype=wtype)
        return qs

    def _actor_label(self) -> str:
        user = self.request.user
        return user.get_full_name() or user.username

    def perform_create(self, serializer):
        serializer.save(id=_next_weakness_id(), updated_by=self._actor_label())

    def perform_update(self, serializer):
        serializer.save(updated_by=self._actor_label())
