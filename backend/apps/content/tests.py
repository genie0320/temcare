import pytest
from rest_framework.test import APIClient

from apps.accounts.models import AdminPermission, AdminProfile, AdminRole, User
from apps.audit.models import AuditLog
from apps.content.models import Food, Illness, Nutrient, NutrientCard, TemType, Weakness


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


@pytest.mark.django_db
def test_tem_type_create_with_weaknesses_illness_and_curation():
    user = _make_admin("editor", [("adm_002", "read"), ("adm_002", "write"), ("adm_003", "read")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    w2 = Weakness.objects.create(id="WEAK-02", name="소화불량")
    illness = Illness.objects.create(id="ILL-01", name="소화기질환")
    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민 B-complex")
    card = NutrientCard.objects.create(nutrient=nutrient, perspective="대사회복")
    card.weaknesses.add(w1)

    resp = client.post(
        "/api/content/tem-types/",
        {
            "name": "TE-5",
            "nickname": "매일 겨울을 사는 몸",
            "body_min": 1,
            "body_max": 3,
            "body_desc": "마른 체형이라도 복부비만",
            "weakness_ids": [w1.id, w2.id],
            "illnesses": [{"illness_id": illness.id, "pct": 30}],
            "nutrient_card_ids": [card.id],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "TEM01"  # 서버 채번
    assert set(body["weakness_ids"]) == {w1.id, w2.id}
    assert body["illnesses"] == [{"illness_id": illness.id, "pct": 30}]
    assert body["nutrient_card_ids"] == [str(card.id)]

    tem_type = TemType.objects.get(id="TEM01")
    assert tem_type.body_value == round((1 + 3) / 2 * 25)


@pytest.mark.django_db
def test_tem_type_update_replaces_children_not_appends():
    user = _make_admin("editor", [("adm_002", "read"), ("adm_002", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    w2 = Weakness.objects.create(id="WEAK-02", name="소화불량")
    tem_type = TemType.objects.create(id="TEM01", name="TE-1")
    tem_type.weaknesses.add(w1)

    resp = client.patch(
        "/api/content/tem-types/TEM01/",
        {"weakness_ids": [w2.id]},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["weakness_ids"] == [w2.id]


@pytest.mark.django_db
def test_tem_type_list_shows_weakness_names_not_ids():
    user = _make_admin("editor", [("adm_002", "read")])
    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    tem_type = TemType.objects.create(id="TEM01", name="TE-1")
    tem_type.weaknesses.add(w1)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/tem-types/")
    assert resp.status_code == 200
    assert resp.json()[0]["weakness_names"] == ["추위"]


@pytest.mark.django_db
def test_nutrient_candidates_filtered_by_weakness():
    user = _make_admin("editor", [("adm_002", "read")])
    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    w2 = Weakness.objects.create(id="WEAK-02", name="소화불량")
    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민 B-complex")
    matching = NutrientCard.objects.create(nutrient=nutrient, perspective="대사회복")
    matching.weaknesses.add(w1)
    other = NutrientCard.objects.create(nutrient=nutrient, perspective="신경안정")
    other.weaknesses.add(w2)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get(f"/api/content/tem-type-candidates/nutrient-cards/?weaknesses={w1.id}")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()]
    assert str(matching.id) in ids
    assert str(other.id) not in ids


@pytest.mark.django_db
def test_food_candidates_expose_polarity_badge():
    user = _make_admin("editor", [("adm_002", "read")])
    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    food = Food.objects.create(id="FOOD-01", polarity="제한", foods="포드맵", component="양파·마늘")
    food.weaknesses.add(w1)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get(f"/api/content/tem-type-candidates/foods/?weaknesses={w1.id}")
    assert resp.status_code == 200
    assert resp.json()[0]["polarity"] == "제한"


@pytest.mark.django_db
def test_tem_type_write_denied_without_adm_002_permission():
    user = _make_admin("cs", [("adm_003", "read")])
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/content/tem-types/", {"name": "TE-1"}, format="json")
    assert resp.status_code == 403
