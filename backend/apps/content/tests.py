import pytest
from rest_framework.test import APIClient

from apps.accounts.models import AdminPermission, AdminProfile, AdminRole, User
from apps.audit.models import AuditLog
from apps.content.models import Weakness


def _make_admin(role_id, resources_actions):
    role, _ = AdminRole.objects.get_or_create(id=role_id, defaults={"name": role_id, "sort": 0})
    for resource, action in resources_actions:
        AdminPermission.objects.create(role=role, resource=resource, action=action, allowed=True)
    user = User.objects.create_user(username=f"{role_id}@test.local", password="pass1234!", is_staff=True)
    AdminProfile.objects.create(user=user, role=role)
    return user


@pytest.mark.django_db
def test_weakness_list_requires_login():
    resp = APIClient().get("/api/content/weaknesses/")
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_weakness_list_denied_without_read_permission():
    user = _make_admin("cs", [("adm_015", "pii_read")])  # 다른 리소스 권한만 있음
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/weaknesses/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_weakness_crud_by_editor_role():
    user = _make_admin("editor", [("adm_003", "read"), ("adm_003", "write"), ("adm_003", "delete")])
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/weaknesses/")
    assert resp.status_code == 200
    assert resp.json() == []

    resp = client.post(
        "/api/content/weaknesses/",
        {"name": "새약점", "wtype": "약점", "catchphrase": "테스트용"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "WEAK-01"  # 서버가 생성 — 클라이언트가 지정 못 함
    assert body["updated_by"] == user.username

    detail_url = f"/api/content/weaknesses/{body['id']}/"
    resp = client.patch(detail_url, {"catchphrase": "수정됨"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["catchphrase"] == "수정됨"

    resp = client.delete(detail_url)
    assert resp.status_code == 204
    assert not Weakness.objects.filter(id=body["id"]).exists()


@pytest.mark.django_db
def test_weakness_write_denied_for_read_only_role():
    user = _make_admin("viewer", [("adm_003", "read")])
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/content/weaknesses/", {"name": "새약점"}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_weakness_changes_are_audited():
    user = _make_admin("editor", [("adm_003", "read"), ("adm_003", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/content/weaknesses/", {"name": "새약점"}, format="json")
    wid = resp.json()["id"]

    log = AuditLog.objects.filter(target_table="weakness", target_id=wid, action="create").latest("created_at")
    assert log.after_json is not None


@pytest.mark.django_db
def test_weakness_list_serializer_excludes_detail_only_fields():
    """docs/08_tech_stack.md §5 — fields='__all__' 금지, 목록엔 aphorism 등 노출 안 함."""
    user = _make_admin("editor", [("adm_003", "read")])
    Weakness.objects.create(id="WEAK-99", name="추위", aphorism="비공개 격언 텍스트")
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/weaknesses/")
    assert resp.status_code == 200
    assert "aphorism" not in resp.json()[0]
