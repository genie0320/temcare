from rest_framework import serializers

from .models import Clinic

# 관리자(adm_040)용. 고객(sc_040)은 customer_views에서 직접 dict를 만든다 —
# 고객에게는 status·updated_by 같은 운영 필드를 내보내지 않기 위해서다.


class ClinicListSerializer(serializers.ModelSerializer):
    region = serializers.CharField(read_only=True)

    class Meta:
        model = Clinic
        fields = ["id", "name", "director", "region", "phone", "status", "sort", "updated_at", "updated_by"]


class ClinicDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = [
            "id",
            "name",
            "director",
            "sido",
            "sigungu",
            "address",
            "phone",
            "hours",
            "intro",
            "image",
            "map_url",
            "homepage",
            "status",
            "sort",
            "created_at",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by"]
