from rest_framework import serializers

from .models import Herb, Illness, Nutrient, TemType, Weakness


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
