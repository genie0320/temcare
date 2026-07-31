from rest_framework import serializers

from .models import Weakness


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
