from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import AdminPermission, AdminProfile, AdminRole, User
from apps.support.models import AppSetting

ROLES = [
    ("super", "슈퍼관리자", 0),
    ("director", "원장", 1),
    ("editor", "콘텐츠 에디터", 2),
    ("cs", "고객상담", 3),
    ("viewer", "뷰어", 4),
]

# M0 단계에서는 실제 화면 리소스가 아직 없어 데모 계정만 최소로 채운다.
# 관리자 화면(M1)이 붙을 때마다 resource id를 여기 추가한다.
SUPER_RESOURCES = ["demo"]
SUPER_ACTIONS = ["read", "write", "delete", "publish", "pii_read"]


class Command(BaseCommand):
    help = "M0 최소 시드: admin_role/admin_permission, 데모 슈퍼관리자 계정, app_config. 언제든 다시 돌려도 안전(멱등)."

    @transaction.atomic
    def handle(self, *args, **options):
        for role_id, name, sort in ROLES:
            AdminRole.objects.update_or_create(id=role_id, defaults={"name": name, "sort": sort})
        self.stdout.write(self.style.SUCCESS(f"admin_role {len(ROLES)}건"))

        super_role = AdminRole.objects.get(id="super")
        for resource in SUPER_RESOURCES:
            for action in SUPER_ACTIONS:
                AdminPermission.objects.update_or_create(
                    role=super_role, resource=resource, action=action, defaults={"allowed": True}
                )

        admin_user, created = User.objects.get_or_create(
            username="admin@ollacare.local",
            defaults={"email": "admin@ollacare.local", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin_user.set_password("admin1234!")
            admin_user.save()
        AdminProfile.objects.update_or_create(user=admin_user, defaults={"role": super_role})
        self.stdout.write(self.style.SUCCESS(f"데모 관리자 계정: {admin_user.username} / admin1234!"))

        AppSetting.objects.update_or_create(
            key="diagnosis.provider", defaults={"value": "mock", "description": "판별 어댑터 선택"}
        )
        self.stdout.write(self.style.SUCCESS("app_config: diagnosis.provider = mock"))
