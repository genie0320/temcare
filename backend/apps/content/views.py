import os
import re
import uuid

from django.core.files.storage import default_storage
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import AdminPermission
from apps.accounts.permissions import AdminResourcePermission

from .models import (
    Food,
    FoodWeakness,
    Herb,
    HerbCard,
    HerbCardWeakness,
    Illness,
    Nutrient,
    NutrientCard,
    NutrientCardWeakness,
    Point,
    PointWeakness,
    TemType,
    TemTypeCuration,
    TemTypeIllness,
    TemTypeWeakness,
    Weakness,
)
from .serializers import (
    FoodDetailSerializer,
    FoodListSerializer,
    HerbDetailSerializer,
    HerbListSerializer,
    IllnessOptionSerializer,
    NutrientDetailSerializer,
    NutrientListSerializer,
    PointDetailSerializer,
    PointListSerializer,
    TemTypeDetailSerializer,
    TemTypeListSerializer,
    WeaknessDetailSerializer,
    WeaknessListSerializer,
)

_WEAK_ID_RE = re.compile(r"^WEAK-(\d+)$")
_TEM_ID_RE = re.compile(r"^TEM(\d+)$")
_NUT_ID_RE = re.compile(r"^NUT-(\d+)$")
_FOOD_ID_RE = re.compile(r"^FOOD-(\d+)$")
_HRB_ID_RE = re.compile(r"^HRB-(\d+)$")
_ACU_ID_RE = re.compile(r"^ACU-(\d+)$")


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


def _next_nutrient_id() -> str:
    max_n = 0
    for nid in Nutrient.objects.values_list("id", flat=True):
        m = _NUT_ID_RE.match(nid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"NUT-{max_n + 1:02d}"


def _next_herb_id() -> str:
    max_n = 0
    for hid in Herb.objects.values_list("id", flat=True):
        m = _HRB_ID_RE.match(hid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"HRB-{max_n + 1:02d}"


def _next_food_id() -> str:
    max_n = 0
    for fid in Food.objects.values_list("id", flat=True):
        m = _FOOD_ID_RE.match(fid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"FOOD-{max_n + 1:02d}"


def _next_point_id() -> str:
    max_n = 0
    for pid in Point.objects.values_list("id", flat=True):
        m = _ACU_ID_RE.match(pid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"ACU-{max_n + 1:02d}"


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


class NutrientViewSet(ModelViewSet):
    """영양소 마스터(adm_022). docs/05_screen_conventions.md §C 반복 카드 리스트 —
    마스터 1건(영양소) + 하위 카드 N건(관점별), 카드마다 약점 n:m.
    """

    permission_classes = [AdminResourcePermission]
    resource = "adm_022"
    queryset = Nutrient.objects.all()

    def get_serializer_class(self):
        return NutrientListSerializer if self.action == "list" else NutrientDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(id__icontains=search) | Q(cards__perspective__icontains=search)
            )
        weakness = self.request.query_params.get("weakness")
        if weakness:
            qs = qs.filter(cards__weaknesses__id=weakness)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.distinct()

    def _actor_label(self) -> str:
        user = self.request.user
        return user.get_full_name() or user.username

    def perform_create(self, serializer):
        instance = serializer.save(id=_next_nutrient_id(), updated_by=self._actor_label())
        self._sync_cards(instance)

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self._actor_label())
        self._sync_cards(instance)

    def _sync_cards(self, instance):
        """관점 카드를 요청 본문으로 통째로 교체한다. 인스턴스 단위 delete()/create()만
        쓴다(QuerySet.delete()/bulk_* 금지 — docs/08_tech_stack.md §4). NutrientCard는
        AuditedModel이라 이 delete()·create() 각각이 감사로그에 남는다.
        """
        data = self.request.data
        if "cards" not in data:
            return
        for card in list(instance.cards.all()):
            card.delete()
        for i, item in enumerate(data.get("cards") or []):
            perspective = (item.get("perspective") or "").strip()
            description = (item.get("description") or "").strip()
            weakness_ids = item.get("weakness_ids") or []
            if not perspective and not description and not weakness_ids:
                continue
            card = NutrientCard.objects.create(
                nutrient=instance, perspective=perspective, description=description, sort=i
            )
            for wid in weakness_ids:
                NutrientCardWeakness.objects.create(card=card, weakness_id=wid)


class NutrientPerspectiveOptionsView(APIView):
    """관점 카드 입력란의 자동완성 후보(spec adm_022 3행: 자유텍스트+기존값 자동완성)."""

    permission_classes = [AdminResourcePermission]
    resource = "adm_022"
    required_action = "read"

    def get(self, request):
        values = NutrientCard.objects.exclude(perspective="").values_list("perspective", flat=True)
        return Response(sorted(set(values)))


class HerbViewSet(ModelViewSet):
    """약재(인생처방) 마스터(adm_023). 영양소(adm_022)와 동일 구조 — 마스터 1건 + 하위
    카드 N건(효능기전별), 카드마다 약점 n:m. 한자/생약명 필드만 추가로 있다.
    """

    permission_classes = [AdminResourcePermission]
    resource = "adm_023"
    queryset = Herb.objects.all()

    def get_serializer_class(self):
        return HerbListSerializer if self.action == "list" else HerbDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(id__icontains=search)
                | Q(hanja__icontains=search)
                | Q(cards__mechanism__icontains=search)
            )
        weakness = self.request.query_params.get("weakness")
        if weakness:
            qs = qs.filter(cards__weaknesses__id=weakness)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.distinct()

    def _actor_label(self) -> str:
        user = self.request.user
        return user.get_full_name() or user.username

    def perform_create(self, serializer):
        instance = serializer.save(id=_next_herb_id(), updated_by=self._actor_label())
        self._sync_cards(instance)

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self._actor_label())
        self._sync_cards(instance)

    def _sync_cards(self, instance):
        """효능 카드를 요청 본문으로 통째로 교체한다. 인스턴스 단위 delete()/create()만
        쓴다(QuerySet.delete()/bulk_* 금지 — docs/08_tech_stack.md §4).
        """
        data = self.request.data
        if "cards" not in data:
            return
        for card in list(instance.cards.all()):
            card.delete()
        for i, item in enumerate(data.get("cards") or []):
            mechanism = (item.get("mechanism") or "").strip()
            description = (item.get("description") or "").strip()
            weakness_ids = item.get("weakness_ids") or []
            if not mechanism and not description and not weakness_ids:
                continue
            card = HerbCard.objects.create(
                herb=instance, mechanism=mechanism, description=description, sort=i
            )
            for wid in weakness_ids:
                HerbCardWeakness.objects.create(card=card, weakness_id=wid)


class HerbMechanismOptionsView(APIView):
    """효능 카드 입력란의 자동완성 후보(spec adm_023 3행: 자유텍스트+자동완성)."""

    permission_classes = [AdminResourcePermission]
    resource = "adm_023"
    required_action = "read"

    def get(self, request):
        values = HerbCard.objects.exclude(mechanism="").values_list("mechanism", flat=True)
        return Response(sorted(set(values)))


class FoodViewSet(ModelViewSet):
    """식품군 마스터(adm_025). 영양소·약재와 달리 카드가 아니라 **단일 레코드 + 약점
    체크박스** 구조다(64유형과 같은 §B 패턴).
    """

    permission_classes = [AdminResourcePermission]
    resource = "adm_025"
    queryset = Food.objects.all()

    def get_serializer_class(self):
        return FoodListSerializer if self.action == "list" else FoodDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(foods__icontains=search)
                | Q(id__icontains=search)
                | Q(component__icontains=search)
                | Q(description__icontains=search)
            )
        polarity = self.request.query_params.get("polarity")
        if polarity:
            qs = qs.filter(polarity=polarity)
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
        instance = serializer.save(id=_next_food_id(), updated_by=self._actor_label())
        self._sync_weaknesses(instance)

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self._actor_label())
        self._sync_weaknesses(instance)

    def _sync_weaknesses(self, instance):
        """약점 태그를 요청 본문으로 통째로 교체한다(TemTypeViewSet._sync_children과 동일 패턴).
        인스턴스 단위 delete()/create()만 쓴다(QuerySet.delete()/bulk_* 금지 — docs/08_tech_stack.md §4).
        """
        data = self.request.data
        if "weakness_ids" not in data:
            return
        target = {str(w) for w in (data.get("weakness_ids") or [])}
        current = {str(w) for w in instance.weaknesses.values_list("id", flat=True)}
        for wid in current - target:
            FoodWeakness.objects.get(food=instance, weakness_id=wid).delete()
        for wid in target - current:
            FoodWeakness.objects.create(food=instance, weakness_id=wid)


class FoodComponentOptionsView(APIView):
    """핵심성분 입력란의 자동완성 후보(spec adm_025 2행: 자유텍스트+자동완성)."""

    permission_classes = [AdminResourcePermission]
    resource = "adm_025"
    required_action = "read"

    def get(self, request):
        values = Food.objects.exclude(component="").values_list("component", flat=True)
        return Response(sorted(set(values)))


class PointViewSet(ModelViewSet):
    """혈자리 마스터(adm_026). 식품군(adm_025)과 같은 §B 구조 — 단일 레코드 + 약점
    체크박스. `tip`은 spec [v2]에서 UI가 빠졌으므로 여기서 다루지 않는다(컬럼은 보존).
    """

    permission_classes = [AdminResourcePermission]
    resource = "adm_026"
    queryset = Point.objects.all()

    def get_serializer_class(self):
        return PointListSerializer if self.action == "list" else PointDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(id__icontains=search)
                | Q(hanja__icontains=search)
                | Q(description__icontains=search)
                | Q(location__icontains=search)
            )
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
        instance = serializer.save(id=_next_point_id(), updated_by=self._actor_label())
        self._sync_weaknesses(instance)

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self._actor_label())
        self._sync_weaknesses(instance)

    def _sync_weaknesses(self, instance):
        """약점 태그를 요청 본문으로 통째로 교체한다. 인스턴스 단위 delete()/create()만
        쓴다(QuerySet.delete()/bulk_* 금지 — docs/08_tech_stack.md §4).
        """
        data = self.request.data
        if "weakness_ids" not in data:
            return
        target = {str(w) for w in (data.get("weakness_ids") or [])}
        current = {str(w) for w in instance.weaknesses.values_list("id", flat=True)}
        for wid in current - target:
            PointWeakness.objects.get(point=instance, weakness_id=wid).delete()
        for wid in target - current:
            PointWeakness.objects.create(point=instance, weakness_id=wid)


_MAX_UPLOAD_BYTES = 5 * 1024 * 1024
_ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
_ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


class ImageUploadView(APIView):
    """관리자 화면 공통 이미지 업로드. docs/04_design_system.md §4 — 파일 스토리지에
    저장하고 경로(URL)만 돌려준다. 어느 화면(resource)에서 왔는지는 요청 본문으로
    받아 그 리소스의 write 권한을 검사한다(화면마다 전용 뷰를 새로 만들지 않기 위함).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        resource = request.data.get("resource")
        file = request.FILES.get("file")
        if not resource or not file:
            return Response({"detail": "resource, file은 필수다."}, status=status.HTTP_400_BAD_REQUEST)
        if file.content_type not in _ALLOWED_IMAGE_TYPES:
            return Response({"detail": "이미지 파일만 업로드할 수 있다."}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > _MAX_UPLOAD_BYTES:
            return Response({"detail": "5MB를 넘는 파일은 업로드할 수 없다."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        has_write = (
            hasattr(user, "admin_profile")
            and AdminPermission.objects.filter(
                role_id=user.admin_profile.role_id, resource=resource, action="write", allowed=True
            ).exists()
        )
        if not has_write:
            return Response(status=status.HTTP_403_FORBIDDEN)

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in _ALLOWED_IMAGE_EXTS:
            ext = ".png"
        saved_path = default_storage.save(f"{resource}/{uuid.uuid4().hex}{ext}", file)
        return Response({"url": default_storage.url(saved_path)}, status=status.HTTP_201_CREATED)
