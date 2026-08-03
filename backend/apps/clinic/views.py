"""협력 한의원 마스터 CRUD (adm_040).

콘텐츠 마스터와 같은 뼈대(MasterViewSet)를 쓴다. 다만 **약점 태그가 없는 마스터**라
weakness_required를 끈다 — 한의원은 약점으로 끌어오는 콘텐츠가 아니라 목록 그 자체다.
"""

from apps.content.base import MasterViewSet

from .models import Clinic
from .serializers import ClinicDetailSerializer, ClinicListSerializer


class ClinicViewSet(MasterViewSet):
    resource = "adm_040"
    queryset = Clinic.objects.all()
    id_prefix = "CLINIC-"
    list_serializer_class = ClinicListSerializer
    detail_serializer_class = ClinicDetailSerializer
    search_fields = ["name", "director", "address", "sigungu", "intro"]
    filter_fields = {"sido": "sido"}
    weakness_required = False
