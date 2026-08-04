"""감사로그 조회(adm_028) 직렬화.

이 화면의 목적은 운영이 아니라 **진단**이다 — "지금 어느 테이블에 어떤 로그가 얼마나
남고 있나"를 눈으로 확인하는 것. 그래서 로그를 가공하지 않고 원문 그대로 내보낸다.
docs/11_audit_viewer.md §3.
"""

from rest_framework import serializers

from .models import AccessLog, AuditLog

# 목록 응답에 before/after 전문을 실으면 콘텐츠 본문이 통째로 들어와 응답이 폭발한다
# (요법관리 본문 하나가 수 KB다). 목록은 잘라서 보내고 전문은 상세에서만 준다.
# docs/11_audit_viewer.md §4-3.
PREVIEW_CHARS = 200


def _preview(raw: str | None) -> str | None:
    if raw is None:
        return None
    return raw[:PREVIEW_CHARS]


class AuditLogListSerializer(serializers.ModelSerializer):
    before_preview = serializers.SerializerMethodField()
    after_preview = serializers.SerializerMethodField()
    truncated = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "created_at",
            "actor_id",
            "actor_type",
            "ip",
            "action",
            "target_table",
            "target_id",
            "before_preview",
            "after_preview",
            "truncated",
        ]

    def get_before_preview(self, obj) -> str | None:
        return _preview(obj.before_json)

    def get_after_preview(self, obj) -> str | None:
        return _preview(obj.after_json)

    def get_truncated(self, obj) -> bool:
        """잘렸다는 사실을 화면이 알아야 '원문을 다 봤다'고 착각하지 않는다."""
        return any(len(raw or "") > PREVIEW_CHARS for raw in (obj.before_json, obj.after_json))


class AuditLogDetailSerializer(serializers.ModelSerializer):
    """전/후 **전문**. 시트2 요소4(변경 상세 diff)의 데이터원이다."""

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "created_at",
            "actor_id",
            "actor_type",
            "ip",
            "action",
            "target_table",
            "target_id",
            "before_json",
            "after_json",
        ]


class AccessLogSerializer(serializers.ModelSerializer):
    """★ 이 응답에는 마스킹 장치가 없다 — target_user·fields·purpose가 원문 그대로다.

    그래서 이걸 내보내는 뷰만 required_action="pii_read"로 분리한다(views.AccessLogListView).
    """

    class Meta:
        model = AccessLog
        fields = ["id", "created_at", "actor_id", "ip", "target_user", "fields", "purpose"]
