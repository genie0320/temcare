"""콘텐츠 마스터 CRUD API.

공통 뼈대(중복 제거·약점 필수 검증·관계 감사로그)는 base.MasterViewSet에 있다.
여기 각 ViewSet은 **무엇이 다른지만** 선언한다.
"""

import os
import uuid

from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import AdminResourcePermission
from apps.audit import service as audit

from .base import MasterViewSet, next_id, sync_relation
from .models import (
    Article,
    ArticleFood,
    ArticlePoint,
    ArticleProduct,
    ArticleWeakness,
    Food,
    FoodWeakness,
    HealthSign,
    HealthSignWeakness,
    Herb,
    HerbCard,
    HerbCardWeakness,
    Illness,
    IllnessWeakness,
    LifeArticle,
    LifeArticleLink,
    LifeArticleRelated,
    Nutrient,
    NutrientCard,
    NutrientCardWeakness,
    Point,
    PointWeakness,
    Product,
    TemType,
    TemTypeCuration,
    TemTypeIllness,
    TemTypeWeakness,
    Weakness,
)
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    FoodDetailSerializer,
    FoodListSerializer,
    HealthSignDetailSerializer,
    HealthSignListSerializer,
    HerbDetailSerializer,
    HerbListSerializer,
    IllnessDetailSerializer,
    IllnessListSerializer,
    IllnessOptionSerializer,
    LifeArticleDetailSerializer,
    LifeArticleListSerializer,
    NutrientDetailSerializer,
    NutrientListSerializer,
    PointDetailSerializer,
    PointListSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    TemTypeDetailSerializer,
    TemTypeListSerializer,
    WeaknessDetailSerializer,
    WeaknessListSerializer,
)


class WeaknessViewSet(MasterViewSet):
    """약점 / IDEA 마스터(adm_003). 약점 태그의 '정의' 자체라 약점 필수 규칙은 해당 없다."""

    resource = "adm_003"
    queryset = Weakness.objects.all()
    id_prefix = "WEAK-"
    list_serializer_class = WeaknessListSerializer
    detail_serializer_class = WeaknessDetailSerializer
    search_fields = ["name", "id"]
    filter_fields = {"wtype": "wtype"}
    weakness_required = False


class TemTypeViewSet(MasterViewSet):
    """64유형 마스터(adm_002). 약점 + 예측질환 발병율 + 큐레이션 3종을 자식으로 갖는다."""

    resource = "adm_002"
    queryset = TemType.objects.all()
    id_prefix = "TEM"
    list_serializer_class = TemTypeListSerializer
    detail_serializer_class = TemTypeDetailSerializer
    search_fields = ["name", "id", "nickname"]
    filter_fields = {"weakness": "weaknesses__id"}
    weakness_through = TemTypeWeakness
    weakness_parent_field = "tem_type"

    def _body_kwargs(self, default_min=2, default_max=2) -> dict:
        body_min = int(self.request.data.get("body_min", default_min))
        body_max = int(self.request.data.get("body_max", default_max))
        return {
            "body_min": body_min,
            "body_max": body_max,
            "body_value": round((body_min + body_max) / 2 * 25),
        }

    def get_create_kwargs(self, serializer) -> dict:
        return {**super().get_create_kwargs(serializer), **self._body_kwargs()}

    def get_update_kwargs(self, serializer) -> dict:
        return {
            **super().get_update_kwargs(serializer),
            **self._body_kwargs(serializer.instance.body_min, serializer.instance.body_max),
        }

    def sync_children(self, instance):
        """예측질환 발병율·큐레이션을 요청 본문으로 통째로 교체한다.

        ★ 발병율은 합계 100% 검증을 하지 않는다 — 질환별 독립 발병율이다
          (docs/05_screen_conventions.md §G, docs/06_decisions.md #4).
        """
        data = self.request.data

        if "illnesses" in data:
            before = [
                {"illness_id": link.illness_id, "pct": link.pct} for link in instance.illness_links.order_by("sort")
            ]
            for link in list(instance.illness_links.all()):
                link.delete()
            after = []
            for i, item in enumerate(data.get("illnesses") or []):
                illness_id = item.get("illness_id")
                if not illness_id:
                    continue
                pct = int(item.get("pct") or 0)
                TemTypeIllness.objects.create(tem_type=instance, illness_id=illness_id, pct=pct, sort=i)
                after.append({"illness_id": illness_id, "pct": pct})
            if before != after:
                # TemTypeIllness는 AuditedModel이 아니다(순수 값 테이블). 발병율은 원장이
                # 손으로 넣는 실데이터라 변경 이력이 반드시 필요하다 — 명시적으로 남긴다.
                audit.record(
                    action="update",
                    target_table=instance._meta.db_table,
                    target_id=instance.pk,
                    before={"illnesses": before},
                    after={"illnesses": after},
                )

        curation_keys = {"nutrient": "nutrient_card_ids", "herb": "herb_card_ids", "food": "food_ids"}
        for kind, key in curation_keys.items():
            if key not in data:
                continue
            before = list(
                instance.curations.filter(kind=kind).order_by("sort").values_list("ref_id", flat=True)
            )
            for cur in list(instance.curations.filter(kind=kind)):
                cur.delete()
            after = []
            for i, ref_id in enumerate(data.get(key) or []):
                polarity = ""
                if kind == "food":
                    food = Food.objects.filter(id=ref_id).first()
                    polarity = food.polarity if food else ""
                TemTypeCuration.objects.create(
                    tem_type=instance, kind=kind, ref_id=str(ref_id), polarity=polarity, sort=i
                )
                after.append(str(ref_id))
            if before != after:
                audit.record(
                    action="update",
                    target_table=instance._meta.db_table,
                    target_id=instance.pk,
                    before={key: before},
                    after={key: after},
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


class _CardMasterViewSet(MasterViewSet):
    """영양소·약재처럼 '마스터 1건 + 하위 카드 N건' 구조(§C 반복 카드 리스트).

    약점은 마스터가 아니라 **카드**가 문다. 그래서 약점 필수 검증도 카드 단위로 한다.
    """

    card_model = None
    card_parent_field: str | None = None
    card_through = None
    card_text_field: str | None = None  # 관점(perspective) / 효능기전(mechanism)
    weakness_required = False  # 마스터 레벨 검사는 끄고 카드 레벨로 대체

    def _incoming_cards(self):
        return self.request.data.get("cards") or []

    @staticmethod
    def _is_blank(item, text_field) -> bool:
        return not (
            (item.get(text_field) or "").strip()
            or (item.get("description") or "").strip()
            or (item.get("weakness_ids") or [])
        )

    def _validate_weakness_tags(self, *, creating: bool) -> None:
        """카드마다 약점 최소 1개. 완전히 빈 카드는 저장 전에 버려지므로 검사 대상이 아니다."""
        from rest_framework import serializers as drf_serializers

        if "cards" not in self.request.data:
            if creating:
                raise drf_serializers.ValidationError(
                    {"cards": ["카드가 최소 1개 필요하다. 카드에 약점 태그가 있어야 고객 화면에 노출된다."]}
                )
            return

        cards = [c for c in self._incoming_cards() if not self._is_blank(c, self.card_text_field)]
        if creating and not cards:
            raise drf_serializers.ValidationError(
                {"cards": ["카드가 최소 1개 필요하다. 카드에 약점 태그가 있어야 고객 화면에 노출된다."]}
            )
        for i, item in enumerate(cards):
            if not (item.get("weakness_ids") or []):
                raise drf_serializers.ValidationError(
                    {"cards": [f"{i + 1}번째 카드에 연결 약점이 없다. 약점 태그가 없으면 고객 화면에 노출되지 않는다."]}
                )

    def sync_children(self, instance):
        """카드를 요청 본문으로 통째로 교체한다.

        인스턴스 단위 delete()/create()만 쓴다(QuerySet.delete()/bulk_* 금지 —
        docs/08_tech_stack.md §4). 카드 모델은 AuditedModel이라 각 delete()·create()가
        그대로 감사로그에 남는다.
        """
        if "cards" not in self.request.data:
            return
        for card in list(instance.cards.all()):
            card.delete()
        for i, item in enumerate(self._incoming_cards()):
            if self._is_blank(item, self.card_text_field):
                continue
            card = self.card_model.objects.create(
                **{
                    self.card_parent_field: instance,
                    self.card_text_field: (item.get(self.card_text_field) or "").strip(),
                    "description": (item.get("description") or "").strip(),
                    "sort": i,
                }
            )
            for wid in item.get("weakness_ids") or []:
                self.card_through.objects.create(card=card, weakness_id=wid)


class NutrientViewSet(_CardMasterViewSet):
    """영양소 마스터(adm_022). 카드 = (영양소 × 관점)."""

    resource = "adm_022"
    queryset = Nutrient.objects.all()
    id_prefix = "NUT-"
    list_serializer_class = NutrientListSerializer
    detail_serializer_class = NutrientDetailSerializer
    search_fields = ["name", "id", "cards__perspective"]
    filter_fields = {"weakness": "cards__weaknesses__id"}
    card_model = NutrientCard
    card_parent_field = "nutrient"
    card_through = NutrientCardWeakness
    card_text_field = "perspective"


class NutrientPerspectiveOptionsView(APIView):
    """관점 입력란의 자동완성 후보(spec adm_022 3행: 자유텍스트+기존값 자동완성)."""

    permission_classes = [AdminResourcePermission]
    resource = "adm_022"
    required_action = "read"

    def get(self, request):
        values = NutrientCard.objects.exclude(perspective="").values_list("perspective", flat=True)
        return Response(sorted(set(values)))


class HerbViewSet(_CardMasterViewSet):
    """약재(인생처방) 마스터(adm_023). 카드 = (약재 × 효능기전)."""

    resource = "adm_023"
    queryset = Herb.objects.all()
    id_prefix = "HRB-"
    list_serializer_class = HerbListSerializer
    detail_serializer_class = HerbDetailSerializer
    search_fields = ["name", "id", "hanja", "cards__mechanism"]
    filter_fields = {"weakness": "cards__weaknesses__id"}
    card_model = HerbCard
    card_parent_field = "herb"
    card_through = HerbCardWeakness
    card_text_field = "mechanism"


class HerbMechanismOptionsView(APIView):
    """효능기전 입력란의 자동완성 후보(spec adm_023 3행: 자유텍스트+자동완성)."""

    permission_classes = [AdminResourcePermission]
    resource = "adm_023"
    required_action = "read"

    def get(self, request):
        values = HerbCard.objects.exclude(mechanism="").values_list("mechanism", flat=True)
        return Response(sorted(set(values)))


class FoodViewSet(MasterViewSet):
    """식품군 마스터(adm_025). 단일 레코드 + 약점 체크박스(§B)."""

    resource = "adm_025"
    queryset = Food.objects.all()
    id_prefix = "FOOD-"
    list_serializer_class = FoodListSerializer
    detail_serializer_class = FoodDetailSerializer
    search_fields = ["foods", "id", "component", "description"]
    filter_fields = {"polarity": "polarity", "weakness": "weaknesses__id"}
    weakness_through = FoodWeakness
    weakness_parent_field = "food"


class FoodComponentOptionsView(APIView):
    """핵심성분 입력란의 자동완성 후보(spec adm_025 2행)."""

    permission_classes = [AdminResourcePermission]
    resource = "adm_025"
    required_action = "read"

    def get(self, request):
        values = Food.objects.exclude(component="").values_list("component", flat=True)
        return Response(sorted(set(values)))


class PointViewSet(MasterViewSet):
    """혈자리 마스터(adm_026). `tip`은 spec [v2]에서 UI가 빠졌다(컬럼은 보존)."""

    resource = "adm_026"
    queryset = Point.objects.all()
    id_prefix = "ACU-"
    list_serializer_class = PointListSerializer
    detail_serializer_class = PointDetailSerializer
    search_fields = ["name", "id", "hanja", "description", "location"]
    filter_fields = {"weakness": "weaknesses__id"}
    weakness_through = PointWeakness
    weakness_parent_field = "point"


class HealthSignViewSet(MasterViewSet):
    """건강신호 마스터(adm_007a)."""

    resource = "adm_007a"
    queryset = HealthSign.objects.all()
    id_prefix = "SIG-"
    list_serializer_class = HealthSignListSerializer
    detail_serializer_class = HealthSignDetailSerializer
    search_fields = ["name", "id", "note"]
    filter_fields = {"weakness": "weaknesses__id"}
    weakness_through = HealthSignWeakness
    weakness_parent_field = "sign"


class IllnessViewSet(MasterViewSet):
    """예측질환 마스터(adm_007b). category는 스키마 보존, UI 미노출."""

    resource = "adm_007b"
    queryset = Illness.objects.all()
    id_prefix = "ILL-"
    list_serializer_class = IllnessListSerializer
    detail_serializer_class = IllnessDetailSerializer
    search_fields = ["name", "id", "description"]
    filter_fields = {"weakness": "weaknesses__id"}
    weakness_through = IllnessWeakness
    weakness_parent_field = "illness"


class ProductViewSet(MasterViewSet):
    """제품 마스터(adm_027). 약점 태그가 없다 — 관리법(요법)의 참고정보로만 노출된다."""

    resource = "adm_027"
    queryset = Product.objects.all()
    id_prefix = "PRD-"
    list_serializer_class = ProductListSerializer
    detail_serializer_class = ProductDetailSerializer
    search_fields = ["name", "id", "description", "url"]
    weakness_required = False


class ArticleViewSet(MasterViewSet):
    """요법관리 마스터(adm_024). 약점 + 참고정보 3종(식품군·혈자리·제품) 연결."""

    resource = "adm_024"
    queryset = Article.objects.all()
    id_prefix = "ART-"
    list_serializer_class = ArticleListSerializer
    detail_serializer_class = ArticleDetailSerializer
    search_fields = ["title", "id", "body"]
    filter_fields = {"kind": "kind", "weakness": "weaknesses__id"}
    weakness_through = ArticleWeakness
    weakness_parent_field = "article"

    # 참고정보 연결: 요청 키 → (through 모델, 상대 필드명)
    REFERENCE_LINKS = {
        "food_ids": (ArticleFood, "food"),
        "point_ids": (ArticlePoint, "point"),
        "product_ids": (ArticleProduct, "product"),
    }

    def sync_children(self, instance):
        for key, (through, related_field) in self.REFERENCE_LINKS.items():
            if key not in self.request.data:
                continue
            sync_relation(
                instance,
                through=through,
                parent_field="article",
                related_field=related_field,
                target_ids=self.request.data.get(key) or [],
            )


class LifeArticleViewSet(MasterViewSet):
    """템라이프 마스터(adm_009). 2차 착수 시점에 신설(docs/06_decisions.md #11 갱신).

    요법관리와 달리 약점 태그로 자동 노출되지 않는다 — 카테고리 피드로 큐레이션한다.
    참고정보는 콘텐츠 마스터 8종 전체(kind+ref_id 폴리모픽) + 템라이프끼리의 관련 기사.
    """

    resource = "adm_009"
    queryset = LifeArticle.objects.all()
    id_prefix = "LIFE-"
    list_serializer_class = LifeArticleListSerializer
    detail_serializer_class = LifeArticleDetailSerializer
    search_fields = ["title", "id", "body"]
    filter_fields = {"category": "category"}
    weakness_required = False

    # 다른 템콘텐츠 연결: 요청 키 → LifeArticleLink.kind 값
    CONTENT_LINK_KINDS = {
        "nutrient_ids": "nutrient",
        "herb_ids": "herb",
        "food_ids": "food",
        "point_ids": "point",
        "health_sign_ids": "health_sign",
        "illness_ids": "illness",
        "product_ids": "product",
        "article_ids": "article",
    }

    def sync_children(self, instance):
        data = self.request.data
        for key, kind in self.CONTENT_LINK_KINDS.items():
            if key not in data:
                continue
            self._sync_content_link(instance, kind, data.get(key) or [])
        if "related_article_ids" in data:
            sync_relation(
                instance,
                through=LifeArticleRelated,
                parent_field="from_article",
                related_field="to_article",
                target_ids=data.get("related_article_ids") or [],
            )

    def _sync_content_link(self, instance, kind, target_ids):
        """LifeArticleLink는 kind로 나뉘는 폴리모픽 관계라 sync_relation()을 그대로 못 쓴다
        (parent_field 하나만으로는 kind별 구분이 안 된다). 인스턴스 단위 delete()/create()
        원칙은 동일하게 지킨다(QuerySet.delete()/bulk_* 금지 — docs/08_tech_stack.md §4).
        """
        current = {str(v) for v in instance.content_links.filter(kind=kind).values_list("ref_id", flat=True)}
        target = {str(v) for v in (target_ids or [])}
        removed, added = current - target, target - current
        for ref_id in removed:
            LifeArticleLink.objects.get(life_article=instance, kind=kind, ref_id=ref_id).delete()
        for ref_id in added:
            LifeArticleLink.objects.create(life_article=instance, kind=kind, ref_id=ref_id)
        if removed or added:
            audit.record_relation_change(instance, f"{kind}_content_links", current, target)


_MAX_UPLOAD_BYTES = 5 * 1024 * 1024
_ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# 파일의 실제 앞부분(매직 바이트). 브라우저가 보낸 content_type은 위조할 수 있으므로
# 그것만 믿으면 SVG/HTML을 image/png라고 우겨서 올릴 수 있다(저장형 XSS 경로).
_MAGIC_PREFIXES = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
)


def _sniff_image_ext(file) -> str | None:
    """파일 내용으로 실제 이미지 종류를 판별한다. 모르면 None."""
    head = file.read(16)
    file.seek(0)
    for prefix, ext in _MAGIC_PREFIXES:
        if head.startswith(prefix):
            return ext
    # WebP: "RIFF"...."WEBP"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None


class ImageUploadView(APIView):
    """관리자 화면 공통 이미지 업로드. docs/04_design_system.md §4 — 파일 스토리지에
    저장하고 경로(URL)만 돌려준다. 대상 화면(resource)은 요청 본문으로 받고, 권한은
    AdminResourcePermission이 라우트 진입 지점에서 판정한다(§2).
    """

    permission_classes = [AdminResourcePermission]
    required_action = "write"

    def get_resource(self, request):
        return request.data.get("resource")

    def post(self, request):
        file = request.FILES.get("file")
        if not request.data.get("resource") or not file:
            return Response({"detail": "resource, file은 필수다."}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > _MAX_UPLOAD_BYTES:
            return Response({"detail": "5MB를 넘는 파일은 업로드할 수 없다."}, status=status.HTTP_400_BAD_REQUEST)

        # 확장자·content_type이 아니라 파일 내용으로 판정한다.
        ext = _sniff_image_ext(file)
        if ext is None:
            return Response(
                {"detail": "이미지 파일만 업로드할 수 있다(png/jpg/gif/webp)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resource = request.data.get("resource")
        saved_path = default_storage.save(f"{resource}/{uuid.uuid4().hex}{ext}", file)
        return Response({"url": default_storage.url(saved_path)}, status=status.HTTP_201_CREATED)
