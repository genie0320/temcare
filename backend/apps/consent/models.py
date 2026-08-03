"""약관·동의. schema/02_service_1st.sql 82~127행을 그대로 옮긴 것.

고객이 sc_092(약관 동의)에서 남기는 동의 기록이 여기 쌓인다. 관리자 화면
(adm_016 동의 이력 · adm_017 약관 · adm_038 동의 항목)은 M4지만, **기록 자체는
M2 완료 조건**이다 — 동의는 소급해서 만들어낼 수 없기 때문이다.
"""

from django.conf import settings
from django.db import models

from apps.audit.base import AuditedModel


class TermsDocument(AuditedModel):
    """약관 문서 종류. schema.terms_document — tos | privacy | marketing ..."""

    id = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=100)
    sort = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort", "id"]

    def __str__(self):
        return self.name


class TermsVersion(AuditedModel):
    """약관 버전. schema.terms_version.

    ★ body는 원문 스냅샷이다. 약관이 개정돼도 "그 사람이 그때 동의한 문안"이
    남아야 하므로 문서를 덮어쓰지 않고 버전을 새로 만든다.
    """

    STATUS_CHOICES = [
        ("초안", "초안"),
        ("예약", "예약"),
        ("게시", "게시"),
        ("폐기", "폐기"),
    ]

    document = models.ForeignKey(TermsDocument, on_delete=models.CASCADE, related_name="versions")
    version = models.CharField(max_length=20)  # 'v3.2'
    body = models.TextField()
    effective_at = models.DateField()  # 시행일(예약 게시)
    is_major = models.BooleanField(default=False)  # 중대 변경 → 재동의 필요(sc_032, 2차)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="초안")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "version"], name="uniq_terms_version"),
        ]
        ordering = ["document", "-effective_at"]

    def __str__(self):
        return f"{self.document_id} {self.version}"


class ConsentItem(AuditedModel):
    """동의 '항목' 정의 (adm_038). schema.consent_item.

    id 예: tos | privacy | sensitive | age14 | mkt_push
    ★ is_sensitive=True(건강정보)는 일반 개인정보 동의와 **반드시 별도 체크박스**여야
      한다(개인정보보호법 제23조). 화면에서 묶어 받으면 위법이다.
    """

    id = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=200)
    required = models.BooleanField(default=True)  # False=선택(마케팅 등)
    is_sensitive = models.BooleanField(default=False)
    channel = models.CharField(max_length=20, blank=True)  # 마케팅 전용: push | sms | email
    document = models.ForeignKey(
        TermsDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name="consent_items"
    )
    description = models.TextField(blank=True)
    sort = models.IntegerField(default=0)
    status = models.CharField(max_length=10, default="게시")

    class Meta:
        ordering = ["sort", "id"]

    def __str__(self):
        return self.name


class UserConsent(AuditedModel):
    """동의 '이력' (adm_016). schema.user_consent — **append-only**.

    철회도 UPDATE가 아니라 agreed=False인 새 행을 추가한다. "언제 동의했고 언제
    철회했는가"가 증빙이므로 과거 행을 고치면 증빙이 사라진다.
    현재 상태를 보려면 (user, item)별 최신 행을 읽는다.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consents")
    item = models.ForeignKey(ConsentItem, on_delete=models.PROTECT, related_name="user_consents")
    version = models.ForeignKey(
        TermsVersion, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_consents"
    )
    agreed = models.BooleanField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "item", "-created_at"])]
        ordering = ["-created_at"]
