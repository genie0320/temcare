from django.db import models


class AuditLog(models.Model):
    """데이터 변경 이력. append-only — 애플리케이션 코드에서 UPDATE/DELETE 하지 않는다.

    docs/02_architecture_constraints.md §1, §8.
    """

    ACTION_CHOICES = [
        ("create", "create"),
        ("update", "update"),
        ("delete", "delete"),
        ("publish", "publish"),
        ("export", "export"),
        # 권한 없는 접근 시도. docs/02_architecture_constraints.md §2 체크리스트
        # "권한 없는 접근이 감사로그에 남는가". 데이터 변경은 없었지만 보안 사건이므로
        # 같은 장부에 남긴다 — 내부자의 권한 밖 시도를 사후에 추적할 수 있어야 한다.
        ("deny", "deny"),
        # 개인정보 열람 이력(access_log)을 **조회한** 행위. deny와 같은 이유로 여기 남긴다 —
        # 데이터는 안 바뀌었지만 '누가 접속기록을 들여다봤나'는 추적돼야 한다.
        # ★ access_log가 아니라 audit_log에 남기는 것은 의도된 선택이다(docs/11_audit_viewer.md §7):
        #   access_log에 남기면 "내가 접속기록을 봤다"로 장부가 채워져 정작 봐야 할 기록이 묻히고,
        #   access_log는 열람 사유가 필수라 진단 화면을 열 때마다 사유를 타이핑해야 한다.
        ("read", "read"),
    ]

    actor_id = models.CharField(max_length=64, blank=True, null=True)
    actor_type = models.CharField(max_length=20, default="admin")  # admin | user | system
    ip = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    target_table = models.CharField(max_length=100)
    target_id = models.CharField(max_length=64, blank=True, null=True)
    before_json = models.TextField(blank=True, null=True)
    after_json = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["target_table", "target_id", "-created_at"]),
            models.Index(fields=["actor_id", "-created_at"]),
        ]


class AccessLog(models.Model):
    """개인정보 열람 이력. 시그널로 안 잡히므로 뷰에서 명시적으로 기록한다.

    docs/02_architecture_constraints.md §1: 열람 사유 입력을 강제한다.
    """

    actor_id = models.CharField(max_length=64)
    ip = models.GenericIPAddressField(null=True, blank=True)
    target_user = models.CharField(max_length=64, blank=True, null=True)
    fields = models.CharField(max_length=255, blank=True)  # 열람 항목(건강정보 등)
    purpose = models.TextField()  # ★열람 사유. 필수
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["target_user", "-created_at"]),
        ]


class AuditReview(models.Model):
    """월 1회 이상 점검 기록(법정). docs/02_architecture_constraints.md §1 체크리스트."""

    period = models.CharField(max_length=7)  # 'YYYY-MM'
    reviewer = models.CharField(max_length=100)
    finding = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
