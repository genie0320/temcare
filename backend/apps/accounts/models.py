from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.audit.base import AuditedModel


class User(AbstractUser, AuditedModel):
    """고객·운영자 공용 AUTH_USER_MODEL. is_staff=True면 운영자.

    schema/02_service_1st.sql의 `user`(고객)와 `admin_account`(운영자)를 하나로 통합했다.
    근거: docs/08_tech_stack.md §3 "★ 스키마 조정 1건".
    """

    STATUS_CHOICES = [
        ("정상", "정상"),
        ("휴면", "휴면"),
        ("제재", "제재"),
        ("탈퇴예정", "탈퇴예정"),
        ("탈퇴", "탈퇴"),
    ]

    nickname = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="정상")
    dormant_at = models.DateTimeField(null=True, blank=True)
    withdraw_at = models.DateTimeField(null=True, blank=True)
    purge_due_at = models.DateTimeField(null=True, blank=True)
    app_version = models.CharField(max_length=20, blank=True)
    device = models.CharField(max_length=100, blank=True)


class UserSocial(AuditedModel):
    """소셜 로그인 연동 (schema.user_social)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="socials")
    provider = models.CharField(max_length=20)  # kakao | google | apple ...
    social_id = models.CharField(max_length=100)
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "social_id"], name="uniq_user_social"),
        ]


class UserStatusLog(models.Model):
    """상태 전환 이력(사유·실행자 필수). schema.user_status_log."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=10, blank=True)
    to_status = models.CharField(max_length=10)
    reason = models.TextField(blank=True)
    actor = models.CharField(max_length=100, blank=True)  # admin User.id 또는 'system'
    created_at = models.DateTimeField(auto_now_add=True)


class AdminRole(AuditedModel):
    """super | director | editor | cs | viewer. schema.admin_role."""

    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    sort = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class AdminProfile(AuditedModel):
    """User와 1:1. 운영자 전용 컬럼(기존 admin_account)."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_profile")
    role = models.ForeignKey(AdminRole, on_delete=models.PROTECT, related_name="admins")
    mfa_enabled = models.BooleanField(default=False)
    allow_ip = models.CharField(max_length=255, blank=True)  # 콤마 구분 화이트리스트(선택)


class AdminPermission(AuditedModel):
    """role × resource(화면 ID) × action 매트릭스. docs/02_architecture_constraints.md §2.

    action은 read | write | delete | publish | pii_read 다섯 가지.
    pii_read는 독립 축이며 write가 있다고 자동으로 따라오지 않는다.
    """

    ACTION_CHOICES = [
        ("read", "read"),
        ("write", "write"),
        ("delete", "delete"),
        ("publish", "publish"),
        ("pii_read", "pii_read"),
    ]

    role = models.ForeignKey(AdminRole, on_delete=models.CASCADE, related_name="permissions")
    resource = models.CharField(max_length=50)  # 화면 ID(adm_015 등) 또는 리소스명
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    allowed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "resource", "action"], name="uniq_admin_permission"),
        ]


class AdminLoginLog(models.Model):
    """schema.admin_login_log."""

    account = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="login_logs")
    email = models.CharField(max_length=255, blank=True)
    success = models.BooleanField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
