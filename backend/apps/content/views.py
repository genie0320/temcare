import re

from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import AdminResourcePermission

from .models import (
    Food,
    HerbCard,
    Illness,
    NutrientCard,
    TemType,
    TemTypeCuration,
    TemTypeIllness,
    TemTypeWeakness,
    Weakness,
)
from .serializers import (
    IllnessOptionSerializer,
    TemTypeDetailSerializer,
    TemTypeListSerializer,
    WeaknessDetailSerializer,
    WeaknessListSerializer,
)

_WEAK_ID_RE = re.compile(r"^WEAK-(\d+)$")
_TEM_ID_RE = re.compile(r"^TEM(\d+)$")


def _next_weakness_id() -> str:
    max_n = 0
    for wid in Weakness.objects.values_list("id", flat=True):
        m = _WEAK_ID_RE.match(wid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"WEAK-{max_n + 1:02d}"


def _next_tem_type_id() -> str:
    max_n = 0
    for tid in TemType.objects.values_list("id", flat=True):
        m = _TEM_ID_RE.match(tid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"TEM{max_n + 1:02d}"


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


class TemTypeViewSet(ModelViewSet):
    """64유형 마스터(adm_002). docs/02_architecture_constraints.md §7 — 영양·약재·식품군은
    여기서 직접 큐레이션하고, 건강신호·관리법은 약점 태그로 자동 노출되므로 여기서 다루지 않는다.
    """

    permission_classes = [AdminResourcePermission]
    resource = "adm_002"
    queryset = TemType.objects.all()

    def get_serializer_class(self):
        return TemTypeListSerializer if self.action == "list" else TemTypeDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(nickname__icontains=search) | Q(id__icontains=search))
        weakness = self.request.query_params.get("weakness")
        if weakness:
            qs = qs.filter(weaknesses__id=weakness)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.distinct()

    def _actor_label(self) -> str:
        user = self.request.user
        return user.get_full_name() or user.username

    def perform_create(self, serializer):
        body_min = int(self.request.data.get("body_min", 2))
        body_max = int(self.request.data.get("body_max", 2))
        instance = serializer.save(
            id=_next_tem_type_id(),
            updated_by=self._actor_label(),
            body_min=body_min,
            body_max=body_max,
            body_value=round((body_min + body_max) / 2 * 25),
        )
        self._sync_children(instance)

    def perform_update(self, serializer):
        body_min = int(self.request.data.get("body_min", serializer.instance.body_min))
        body_max = int(self.request.data.get("body_max", serializer.instance.body_max))
        instance = serializer.save(
            updated_by=self._actor_label(),
            body_min=body_min,
            body_max=body_max,
            body_value=round((body_min + body_max) / 2 * 25),
        )
        self._sync_children(instance)

    def _sync_children(self, instance):
        """약점·예측질환·큐레이션(영양/약재/식품)을 요청 본문으로 통째로 교체한다.

        인스턴스 단위 delete()/create()만 쓴다(QuerySet.delete()/bulk_* 금지 —
        docs/08_tech_stack.md §4). 이 자식 테이블들은 AuditedModel이 아니라 감사로그
        의무는 없지만, 실제 감사 대상인 TemType.save()가 방금 시그널을 이미 남겼다.
        """
        data = self.request.data

        if "weakness_ids" in data:
            target = {str(w) for w in (data.get("weakness_ids") or [])}
            current = {str(w) for w in instance.weaknesses.values_list("id", flat=True)}
            for wid in current - target:
                TemTypeWeakness.objects.get(tem_type=instance, weakness_id=wid).delete()
            for wid in target - current:
                TemTypeWeakness.objects.create(tem_type=instance, weakness_id=wid)

        if "illnesses" in data:
            for link in list(instance.illness_links.all()):
                link.delete()
            for i, item in enumerate(data.get("illnesses") or []):
                illness_id = item.get("illness_id")
                if not illness_id:
                    continue
                TemTypeIllness.objects.create(
                    tem_type=instance, illness_id=illness_id, pct=int(item.get("pct") or 0), sort=i
                )

        curation_keys = {"nutrient": "nutrient_card_ids", "herb": "herb_card_ids", "food": "food_ids"}
        for kind, key in curation_keys.items():
            if key not in data:
                continue
            for cur in list(instance.curations.filter(kind=kind)):
                cur.delete()
            for i, ref_id in enumerate(data.get(key) or []):
                polarity = ""
                if kind == "food":
                    food = Food.objects.filter(id=ref_id).first()
                    polarity = food.polarity if food else ""
                TemTypeCuration.objects.create(
                    tem_type=instance, kind=kind, ref_id=str(ref_id), polarity=polarity, sort=i
                )


class _CandidatePickerView(APIView):
    """64유형 큐레이션 피커 공통. 선택된 약점 태그를 가진 후보만 돌려준다(§7 자동 후보)."""

    permission_classes = [AdminResourcePermission]
    resource = "adm_002"
    required_action = "read"

    def _weakness_ids(self):
        raw = self.request.query_params.get("weaknesses", "")
        return [w for w in raw.split(",") if w]


class NutrientCardCandidatesView(_CandidatePickerView):
    def get(self, request):
        weakness_ids = self._weakness_ids()
        if not weakness_ids:
            return Response([])
        cards = (
            NutrientCard.objects.filter(weaknesses__id__in=weakness_ids)
            .select_related("nutrient")
            .distinct()
            .order_by("nutrient__sort", "sort")
        )
        return Response([{"id": str(c.id), "name": c.nutrient.name, "sub": c.perspective} for c in cards])


class HerbCardCandidatesView(_CandidatePickerView):
    def get(self, request):
        weakness_ids = self._weakness_ids()
        if not weakness_ids:
            return Response([])
        cards = (
            HerbCard.objects.filter(weaknesses__id__in=weakness_ids)
            .select_related("herb")
            .distinct()
            .order_by("herb__sort", "sort")
        )
        return Response([{"id": str(c.id), "name": c.herb.name, "sub": c.mechanism} for c in cards])


class FoodCandidatesView(_CandidatePickerView):
    def get(self, request):
        weakness_ids = self._weakness_ids()
        if not weakness_ids:
            return Response([])
        foods = Food.objects.filter(weaknesses__id__in=weakness_ids).distinct().order_by("polarity", "sort")
        return Response(
            [{"id": f.id, "name": f.foods, "sub": f.component, "polarity": f.polarity} for f in foods]
        )


class IllnessOptionsView(APIView):
    """예측질환 발병율 행의 질환 선택 드롭다운. 약점 필터 없이 전체 목록(프로토타입과 동일)."""

    permission_classes = [AdminResourcePermission]
    resource = "adm_002"
    required_action = "read"

    def get(self, request):
        illnesses = Illness.objects.order_by("sort")
        return Response(IllnessOptionSerializer(illnesses, many=True).data)
