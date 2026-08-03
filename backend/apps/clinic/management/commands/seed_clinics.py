"""협력 한의원 데모 데이터 + adm_040 권한 부여.

`seed_demo`에 넣지 않고 별도 명령으로 둔 이유는 두 가지다.
  1) 한의원은 프로토타입 sqlite에 없는 신설 테이블이라 이식할 원본이 없다.
  2) 실제 협력 한의원 정보는 **영업이 확정되는 대로 관리자 화면(adm_040)에서**
     입력한다. 시드는 화면을 확인하기 위한 임시 데이터이고, 실데이터가 들어오면
     이 명령을 다시 돌릴 일이 없다.

★ 실재하는 한의원의 상호·주소·전화번호를 지어내지 않는다. 그럴듯한 가짜 업체 정보는
  한 번 들어가면 진짜인 줄 알고 남고, 최악의 경우 무관한 실제 번호로 전화가 간다.
  약관 문안을 [미작성]으로 둔 것과 같은 원칙이다.
"""

from django.core.management.base import BaseCommand

from apps.accounts.models import AdminPermission, AdminRole
from apps.clinic.models import Clinic

RESOURCE = "adm_040"
SUPER_ACTIONS = ["read", "write", "delete", "publish", "pii_read"]
EDITOR_ACTIONS = ["read", "write", "delete", "publish"]

# 명세서 sc_040 비고: 초기 3곳(안양 1 · 지방 2).
CLINICS = [
    {
        "id": "CLINIC-01",
        "name": "[샘플] 안양 협력 한의원",
        "director": "[샘플] 원장",
        "sido": "경기",
        "sigungu": "안양시",
        "address": "[샘플] 실제 주소는 관리자 화면에서 입력합니다.",
        "phone": "",
        "hours": "평일 09:30 – 19:00 · 토 09:30 – 14:00 · 일요일 휴진",
        "intro": "TEM 64체질 정밀 문진(130문항)을 받으실 수 있어요.",
        "sort": 1,
    },
    {
        "id": "CLINIC-02",
        "name": "[샘플] 지방 협력 한의원 A",
        "director": "[샘플] 원장",
        "sido": "",
        "sigungu": "",
        "address": "[샘플] 실제 주소는 관리자 화면에서 입력합니다.",
        "phone": "",
        "hours": "평일 09:00 – 18:30 · 토 09:00 – 13:00",
        "intro": "정밀 문진 후 체질에 맞는 인생처방을 상담해드려요.",
        "sort": 2,
    },
    {
        "id": "CLINIC-03",
        "name": "[샘플] 지방 협력 한의원 B",
        "director": "[샘플] 원장",
        "sido": "",
        "sigungu": "",
        "address": "[샘플] 실제 주소는 관리자 화면에서 입력합니다.",
        "phone": "",
        "hours": "평일 10:00 – 19:00 · 토 10:00 – 14:00",
        "intro": "약식 결과를 가져오시면 이어서 봐드립니다.",
        "sort": 3,
    },
]


class Command(BaseCommand):
    help = "협력 한의원(sc_040) 데모 데이터와 adm_040 권한을 넣는다."

    def handle(self, *args, **options):
        for row in CLINICS:
            # update_or_create가 아니라 get_or_create다 — 관리자가 손으로 고친 값을
            # 시드가 덮어쓰면 안 된다(결정 #21이 남긴 교훈).
            _, created = Clinic.objects.get_or_create(id=row["id"], defaults=row)
            if created:
                self.stdout.write(self.style.SUCCESS(f"한의원 {row['id']} 생성"))

        for role_id, actions in (("super", SUPER_ACTIONS), ("editor", EDITOR_ACTIONS)):
            role = AdminRole.objects.filter(pk=role_id).first()
            if role is None:
                self.stdout.write(self.style.WARNING(f"역할 {role_id} 없음 — seed_demo를 먼저 실행하세요."))
                continue
            for action in actions:
                AdminPermission.objects.get_or_create(role=role, resource=RESOURCE, action=action)
            self.stdout.write(self.style.SUCCESS(f"{role_id} × {RESOURCE} 권한 {len(actions)}건"))
