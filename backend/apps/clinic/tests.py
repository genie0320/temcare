"""협력 한의원 API 테스트 — 고객 조회(sc_040)와 관리자 CRUD(adm_040).

여기서 지키려는 것은 셋이다.
1. **고객 목록은 비로그인으로 열린다.** 깔때기의 출구라 문턱을 두면 목적에 반한다.
2. **숨김 상태는 새지 않는다.** 영업이 끝나 내린 한의원이 계속 노출되면 실제 전화가 간다.
3. **관리자 CRUD는 adm_040 권한을 요구한다.** 다른 화면 권한으로 열리면 안 된다.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import AdminPermission, AdminProfile, AdminRole, User
from apps.audit.models import AuditLog
from apps.clinic.models import Clinic

CUSTOMER_PATH = "/api/partner-clinics/"
ADMIN_PATH = "/api/clinics/"


def _admin(resources_actions):
    role, _ = AdminRole.objects.get_or_create(id="editor", defaults={"name": "에디터", "sort": 1})
    for resource, action in resources_actions:
        AdminPermission.objects.get_or_create(
            role=role, resource=resource, action=action, defaults={"allowed": True}
        )
    user = User.objects.create_user(username="ed@test.local", password="pass1234!", is_staff=True)
    AdminProfile.objects.create(user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def clinic(db):
    return Clinic.objects.create(
        id="CLINIC-01",
        name="샘플 한의원",
        director="원장",
        sido="경기",
        sigungu="안양시",
        phone="031-000-0000",
        sort=1,
    )


# ── 고객(sc_040) ──────────────────────────────────────────────────
@pytest.mark.django_db
def test_customer_list_is_public(clinic):
    """비로그인으로 열려야 한다 — 여기가 막히면 깔때기 출구가 막힌다."""
    resp = APIClient().get(CUSTOMER_PATH)
    assert resp.status_code == 200
    assert [c["name"] for c in resp.json()["clinics"]] == ["샘플 한의원"]


@pytest.mark.django_db
def test_customer_list_joins_region(clinic):
    """지역은 화면에서 이어붙이지 않고 서버가 만들어 준다."""
    assert APIClient().get(CUSTOMER_PATH).json()["clinics"][0]["region"] == "경기 안양시"


@pytest.mark.django_db
def test_customer_list_hides_unpublished(clinic):
    """내린 한의원이 남아 있으면 실제로 전화가 간다."""
    clinic.status = "숨김"
    clinic.save()
    assert APIClient().get(CUSTOMER_PATH).json()["clinics"] == []


@pytest.mark.django_db
def test_customer_list_never_leaks_operational_fields(clinic):
    body = APIClient().get(CUSTOMER_PATH).json()["clinics"][0]
    for field in ("status", "sort", "updated_by", "updatedBy"):
        assert field not in body


# ── 관리자(adm_040) ───────────────────────────────────────────────
@pytest.mark.django_db
def test_admin_requires_its_own_resource(db):
    """다른 화면 권한으로는 열리지 않는다 — 역할×리소스 매트릭스의 전제."""
    client = _admin([("adm_022", "read"), ("adm_022", "write")])
    assert client.get(ADMIN_PATH).status_code == 403


@pytest.mark.django_db
def test_admin_can_create_and_ids_are_sequential(db):
    client = _admin([("adm_040", "read"), ("adm_040", "write")])

    first = client.post(ADMIN_PATH, {"name": "가 한의원"}, format="json")
    assert first.status_code == 201, first.data
    assert first.data["id"] == "CLINIC-01"

    second = client.post(ADMIN_PATH, {"name": "나 한의원"}, format="json")
    assert second.data["id"] == "CLINIC-02"


@pytest.mark.django_db
def test_admin_create_does_not_require_weakness_tags(db):
    """한의원은 약점으로 끌어오는 콘텐츠가 아니다 — 태그 필수 검증에서 빠진다."""
    client = _admin([("adm_040", "read"), ("adm_040", "write")])
    assert client.post(ADMIN_PATH, {"name": "다 한의원"}, format="json").status_code == 201


@pytest.mark.django_db
def test_admin_search_matches_name_and_region(clinic):
    client = _admin([("adm_040", "read")])
    assert len(client.get(ADMIN_PATH, {"search": "안양"}).data) == 1
    assert len(client.get(ADMIN_PATH, {"search": "부산"}).data) == 0


@pytest.mark.django_db
def test_admin_edit_is_recorded_in_audit_log(clinic):
    client = _admin([("adm_040", "read"), ("adm_040", "write")])
    before = AuditLog.objects.count()
    resp = client.patch(f"{ADMIN_PATH}{clinic.pk}/", {"phone": "031-111-1111"}, format="json")
    assert resp.status_code == 200
    # 한의원은 영업 정보라 누가 언제 바꿨는지가 남아야 한다(CLAUDE.md §2-1).
    assert AuditLog.objects.count() > before
