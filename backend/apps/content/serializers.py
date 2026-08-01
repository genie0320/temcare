from rest_framework import serializers

from .models import Article, Food, HealthSign, Herb, Illness, Nutrient, Point, Product, TemType, Weakness


class WeaknessListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_003). docs/05_screen_conventions.md §A — 필요한 열만 화이트리스트."""

    linked_content_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Weakness
        fields = [
            "id",
            "name",
            "wtype",
            "catchphrase",
            "status",
            "linked_content_count",
            "updated_at",
        ]


class WeaknessDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_003). docs/08_tech_stack.md §5 — fields='__all__' 금지, 화이트리스트로."""

    class Meta:
        model = Weakness
        fields = [
            "id",
            "name",
            "wtype",
            "catchphrase",
            "speaker",
            "source",
            "aphorism",
            "status",
            "sort",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]


class TemTypeListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_002). 약점 배지는 이름만 노출한다(§A)."""

    weakness_names = serializers.SerializerMethodField()

    class Meta:
        model = TemType
        fields = ["id", "name", "nickname", "status", "weakness_names", "updated_at"]

    def get_weakness_names(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("name", flat=True))


class TemTypeDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_002). 약점·예측질환·큐레이션(영양/약재/식품)은 모델 필드가 아니라
    관계 테이블에서 오므로 SerializerMethodField로 읽고, 쓰기는 뷰(TemTypeViewSet._sync_children)에서
    request.data를 직접 받아 처리한다 — docs/08_tech_stack.md §5 fields='__all__' 금지.
    """

    weakness_ids = serializers.SerializerMethodField()
    illnesses = serializers.SerializerMethodField()
    nutrient_card_ids = serializers.SerializerMethodField()
    herb_card_ids = serializers.SerializerMethodField()
    food_ids = serializers.SerializerMethodField()

    class Meta:
        model = TemType
        fields = [
            "id",
            "name",
            "nickname",
            "body_min",
            "body_max",
            "body_desc",
            "herb_title",
            "herb_desc",
            "status",
            "sort",
            "weakness_ids",
            "illnesses",
            "nutrient_card_ids",
            "herb_card_ids",
            "food_ids",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]

    def get_weakness_ids(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("id", flat=True))

    def get_illnesses(self, obj):
        return [{"illness_id": link.illness_id, "pct": link.pct} for link in obj.illness_links.order_by("sort")]

    def get_nutrient_card_ids(self, obj):
        return list(obj.curations.filter(kind="nutrient").order_by("sort").values_list("ref_id", flat=True))

    def get_herb_card_ids(self, obj):
        return list(obj.curations.filter(kind="herb").order_by("sort").values_list("ref_id", flat=True))

    def get_food_ids(self, obj):
        return list(obj.curations.filter(kind="food").order_by("sort").values_list("ref_id", flat=True))


class IllnessOptionSerializer(serializers.ModelSerializer):
    """예측질환 발병율 행의 질환 선택 드롭다운용 — 이름만 필요하다."""

    class Meta:
        model = Illness
        fields = ["id", "name"]


class NutrientListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_022). 약점 태그는 카드들이 물고 있는 것을 모아 보여준다."""

    weakness_names = serializers.SerializerMethodField()
    card_count = serializers.SerializerMethodField()

    class Meta:
        model = Nutrient
        fields = ["id", "name", "status", "weakness_names", "card_count", "updated_at"]

    def get_weakness_names(self, obj):
        return list(
            Weakness.objects.filter(nutrient_cards__nutrient=obj)
            .distinct()
            .order_by("sort")
            .values_list("name", flat=True)
        )

    def get_card_count(self, obj):
        return obj.cards.count()


class NutrientDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_022). 관점 카드는 모델 필드가 아니므로 읽기는 SerializerMethodField,
    쓰기는 뷰(NutrientViewSet._sync_cards)에서 request.data를 직접 받아 처리한다.
    """

    cards = serializers.SerializerMethodField()

    class Meta:
        model = Nutrient
        fields = [
            "id",
            "name",
            "image",
            "status",
            "sort",
            "cards",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]

    def get_cards(self, obj):
        return [
            {
                "id": card.id,
                "perspective": card.perspective,
                "description": card.description,
                "weakness_ids": list(card.weaknesses.values_list("id", flat=True)),
            }
            for card in obj.cards.all()
        ]


class HerbListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_023). 약점 태그는 카드들이 물고 있는 것을 모아 보여준다."""

    weakness_names = serializers.SerializerMethodField()
    card_count = serializers.SerializerMethodField()

    class Meta:
        model = Herb
        fields = ["id", "name", "hanja", "status", "weakness_names", "card_count", "updated_at"]

    def get_weakness_names(self, obj):
        return list(
            Weakness.objects.filter(herb_cards__herb=obj).distinct().order_by("sort").values_list("name", flat=True)
        )

    def get_card_count(self, obj):
        return obj.cards.count()


class HerbDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_023). 효능 카드는 모델 필드가 아니므로 읽기는 SerializerMethodField,
    쓰기는 뷰(HerbViewSet._sync_cards)에서 request.data를 직접 받아 처리한다.
    """

    cards = serializers.SerializerMethodField()

    class Meta:
        model = Herb
        fields = [
            "id",
            "name",
            "hanja",
            "image",
            "status",
            "sort",
            "cards",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]

    def get_cards(self, obj):
        return [
            {
                "id": card.id,
                "mechanism": card.mechanism,
                "description": card.description,
                "weakness_ids": list(card.weaknesses.values_list("id", flat=True)),
            }
            for card in obj.cards.all()
        ]


class FoodListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_025). §B — 카드가 아니라 단일 레코드 + 약점 체크박스."""

    weakness_names = serializers.SerializerMethodField()

    class Meta:
        model = Food
        fields = ["id", "polarity", "foods", "component", "status", "weakness_names", "updated_at"]

    def get_weakness_names(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("name", flat=True))


class FoodDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_025). 약점은 모델 필드가 아니므로 읽기는 SerializerMethodField,
    쓰기는 뷰(FoodViewSet._sync_weaknesses)에서 request.data를 직접 받아 처리한다.
    """

    weakness_ids = serializers.SerializerMethodField()

    class Meta:
        model = Food
        fields = [
            "id",
            "polarity",
            "foods",
            "component",
            "description",
            "image",
            "status",
            "sort",
            "weakness_ids",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]

    def get_weakness_ids(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("id", flat=True))


class PointListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_026). §B — 단일 레코드 + 약점 체크박스."""

    weakness_names = serializers.SerializerMethodField()

    class Meta:
        model = Point
        fields = ["id", "name", "hanja", "description", "status", "weakness_names", "updated_at"]

    def get_weakness_names(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("name", flat=True))


class PointDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_026). `tip`은 spec [v2]에서 입력란이 빠졌다(컬럼은 보존) — 이
    화면에서 다루지 않으므로 시리얼라이저에도 넣지 않는다.
    """

    weakness_ids = serializers.SerializerMethodField()

    class Meta:
        model = Point
        fields = [
            "id",
            "name",
            "hanja",
            "description",
            "location",
            "image",
            "video",
            "status",
            "sort",
            "weakness_ids",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]

    def get_weakness_ids(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("id", flat=True))


class HealthSignListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_007a). §B 중 가장 단순한 구조 — 단일 레코드 + 약점 체크박스."""

    weakness_names = serializers.SerializerMethodField()

    class Meta:
        model = HealthSign
        fields = ["id", "name", "note", "status", "weakness_names", "updated_at"]

    def get_weakness_names(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("name", flat=True))


class HealthSignDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_007a). 약점은 모델 필드가 아니므로 읽기는 SerializerMethodField,
    쓰기는 뷰(HealthSignViewSet._sync_weaknesses)에서 request.data를 직접 받아 처리한다.
    """

    weakness_ids = serializers.SerializerMethodField()

    class Meta:
        model = HealthSign
        fields = [
            "id",
            "name",
            "note",
            "image",
            "status",
            "sort",
            "weakness_ids",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]

    def get_weakness_ids(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("id", flat=True))


class ArticleListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_024). 유형(kind)·항목명(title)·연결약점만 노출."""

    weakness_names = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ["id", "kind", "title", "status", "weakness_names", "updated_at"]

    def get_weakness_names(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("name", flat=True))


class ArticleDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_024). 약점·식품군·혈자리·제품 연결은 모델 필드가 아니므로 읽기는
    SerializerMethodField, 쓰기는 뷰(ArticleViewSet._sync_*)에서 request.data를 직접 받아 처리한다.
    """

    weakness_ids = serializers.SerializerMethodField()
    food_ids = serializers.SerializerMethodField()
    point_ids = serializers.SerializerMethodField()
    product_ids = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "kind",
            "title",
            "body",
            "image",
            "video",
            "status",
            "sort",
            "weakness_ids",
            "food_ids",
            "point_ids",
            "product_ids",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]

    def get_weakness_ids(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("id", flat=True))

    def get_food_ids(self, obj):
        return list(obj.linked_foods.order_by("sort").values_list("id", flat=True))

    def get_point_ids(self, obj):
        return list(obj.linked_points.order_by("sort").values_list("id", flat=True))

    def get_product_ids(self, obj):
        return list(obj.linked_products.order_by("sort").values_list("id", flat=True))


class ProductListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_027). 약점 태그가 없는 가장 단순한 구조 — 관리법에서 참고정보로 연결된다."""

    class Meta:
        model = Product
        fields = ["id", "name", "url", "status", "updated_at"]


class ProductDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_027)."""

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "image",
            "url",
            "status",
            "sort",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]


class IllnessListSerializer(serializers.ModelSerializer):
    """목록 화면(adm_007b). 건강신호와 동일한 §B 최단순 구조."""

    weakness_names = serializers.SerializerMethodField()

    class Meta:
        model = Illness
        fields = ["id", "name", "description", "status", "weakness_names", "updated_at"]

    def get_weakness_names(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("name", flat=True))


class IllnessDetailSerializer(serializers.ModelSerializer):
    """상세 화면(adm_007b). 약점은 모델 필드가 아니므로 읽기는 SerializerMethodField,
    쓰기는 뷰(IllnessViewSet._sync_weaknesses)에서 request.data를 직접 받아 처리한다.
    category는 스키마엔 있지만 UI 미노출 — 프로토타입처럼 기존 값을 보존만 한다.
    """

    weakness_ids = serializers.SerializerMethodField()

    class Meta:
        model = Illness
        fields = [
            "id",
            "name",
            "description",
            "image",
            "status",
            "sort",
            "weakness_ids",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]

    def get_weakness_ids(self, obj):
        return list(obj.weaknesses.order_by("sort").values_list("id", flat=True))
