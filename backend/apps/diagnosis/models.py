from django.conf import settings
from django.db import models

from apps.audit.base import AuditedModel


class DiagnosisResult(AuditedModel):
    """schema.diagnosis_result. 로그인+동의 완료 시점에만 생성된다.

    docs/02_architecture_constraints.md §6: 비로그인 문진 응답은 서버에 저장하지 않는다.
    """

    STATUS_CHOICES = [
        ("대기", "대기"),
        ("완료", "완료"),
        ("실패", "실패"),
        ("타임아웃", "타임아웃"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="diagnosis_results")
    type_id = models.CharField(max_length=20, null=True, blank=True)  # tem_type.id (content 앱은 M1에서 추가)
    raw_value = models.IntegerField(null=True, blank=True)  # 1~64
    provider = models.CharField(max_length=20, default="mock")  # mock | junchart
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="완료")
    error_code = models.CharField(max_length=50, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "-created_at"])]


class DiagnosisStat(models.Model):
    """익명 집계 — 개인정보 아님. docs/06_decisions.md #14.

    user_id·IP·정확한 시각 등 식별자를 절대 넣지 않는다. type_id+day 카운트만.
    AuditedModel을 일부러 안 쓴다 — 이건 감사로그 대상이 아니라 순수 통계다.
    """

    type_id = models.CharField(max_length=20)  # tem_type.id
    day = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["type_id", "day"], name="uniq_diagnosis_stat"),
        ]
