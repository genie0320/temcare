import pytest
from rest_framework.test import APIClient

from apps.accounts.models import AdminPermission, AdminProfile, AdminRole, User
from apps.audit.models import AuditLog
from apps.content.models import Food, HealthSign, Herb, HerbCard, Illness, Nutrient, NutrientCard, Point, TemType, Weakness


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


@pytest.mark.django_db
def test_nutrient_create_with_cards():
    user = _make_admin("editor", [("adm_022", "read"), ("adm_022", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    w2 = Weakness.objects.create(id="WEAK-02", name="소화불량")

    resp = client.post(
        "/api/content/nutrients/",
        {
            "name": "비타민 B-complex",
            "cards": [
                {"perspective": "대사회복", "description": "에너지 대사를 돕는다", "weakness_ids": [w1.id, w2.id]},
                {"perspective": "신경안정", "description": "신경 전달을 돕는다", "weakness_ids": [w2.id]},
            ],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "NUT-01"  # 서버 채번
    assert len(body["cards"]) == 2
    assert body["cards"][0]["perspective"] == "대사회복"
    assert set(body["cards"][0]["weakness_ids"]) == {w1.id, w2.id}

    nutrient = Nutrient.objects.get(id="NUT-01")
    assert nutrient.cards.count() == 2


@pytest.mark.django_db
def test_nutrient_update_replaces_cards_not_appends():
    user = _make_admin("editor", [("adm_022", "read"), ("adm_022", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민 D")
    old_card = NutrientCard.objects.create(nutrient=nutrient, perspective="옛 관점")
    old_card.weaknesses.add(w1)

    resp = client.patch(
        "/api/content/nutrients/NUT-01/",
        {"cards": [{"perspective": "새 관점", "description": "새 설명", "weakness_ids": [w1.id]}]},
        format="json",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["cards"]) == 1
    assert body["cards"][0]["perspective"] == "새 관점"
    assert not NutrientCard.objects.filter(perspective="옛 관점").exists()


@pytest.mark.django_db
def test_nutrient_list_shows_weakness_names_and_card_count():
    user = _make_admin("editor", [("adm_022", "read")])
    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민 D")
    card = NutrientCard.objects.create(nutrient=nutrient, perspective="관점")
    card.weaknesses.add(w1)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/nutrients/")
    assert resp.status_code == 200
    body = resp.json()[0]
    assert body["weakness_names"] == ["추위"]
    assert body["card_count"] == 1


@pytest.mark.django_db
def test_nutrient_delete_cascades_cards_and_is_audited():
    user = _make_admin("editor", [("adm_022", "read"), ("adm_022", "write"), ("adm_022", "delete")])
    client = APIClient()
    client.force_authenticate(user=user)

    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민 D")
    card = NutrientCard.objects.create(nutrient=nutrient, perspective="관점")
    card_id = card.id

    resp = client.delete("/api/content/nutrients/NUT-01/")
    assert resp.status_code == 204
    assert not Nutrient.objects.filter(id="NUT-01").exists()
    assert not NutrientCard.objects.filter(id=card_id).exists()
    assert AuditLog.objects.filter(target_table="nutrient_card", target_id=str(card_id), action="delete").exists()


@pytest.mark.django_db
def test_nutrient_write_denied_without_adm_022_permission():
    user = _make_admin("cs", [("adm_003", "read")])
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/content/nutrients/", {"name": "비타민 D"}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_image_upload_saves_file_and_returns_url(tmp_path, settings):
    from django.core.files.uploadedfile import SimpleUploadedFile

    settings.MEDIA_ROOT = tmp_path
    user = _make_admin("editor", [("adm_022", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    png_bytes = bytes.fromhex(
        "89504e470d0a1a0a0000000d494844520000000100000001080600000"
        "01f15c4890000000a49444154789c6360000002000155ff0f2a0000000049454e44ae426082"
    )
    upload = SimpleUploadedFile("pic.png", png_bytes, content_type="image/png")

    resp = client.post("/api/content/image-upload/", {"resource": "adm_022", "file": upload}, format="multipart")
    assert resp.status_code == 201, resp.content
    assert resp.json()["url"].startswith("/media/adm_022/")


@pytest.mark.django_db
def test_image_upload_denied_without_write_permission(tmp_path, settings):
    from django.core.files.uploadedfile import SimpleUploadedFile

    settings.MEDIA_ROOT = tmp_path
    user = _make_admin("viewer", [("adm_022", "read")])
    client = APIClient()
    client.force_authenticate(user=user)

    upload = SimpleUploadedFile("pic.png", b"not-a-real-png", content_type="image/png")
    resp = client.post("/api/content/image-upload/", {"resource": "adm_022", "file": upload}, format="multipart")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_image_upload_rejects_non_image_content_type(tmp_path, settings):
    from django.core.files.uploadedfile import SimpleUploadedFile

    settings.MEDIA_ROOT = tmp_path
    user = _make_admin("editor", [("adm_022", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    upload = SimpleUploadedFile("evil.sh", b"#!/bin/sh\necho hi", content_type="application/x-sh")
    resp = client.post("/api/content/image-upload/", {"resource": "adm_022", "file": upload}, format="multipart")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_herb_create_with_cards_and_hanja():
    user = _make_admin("editor", [("adm_023", "read"), ("adm_023", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    w2 = Weakness.objects.create(id="WEAK-02", name="소화불량")

    resp = client.post(
        "/api/content/herbs/",
        {
            "name": "육계",
            "hanja": "肉桂",
            "cards": [
                {"mechanism": "혈액순환·온열", "description": "몸을 데운다", "weakness_ids": [w1.id, w2.id]},
            ],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "HRB-01"  # 서버 채번
    assert body["hanja"] == "肉桂"
    assert len(body["cards"]) == 1
    assert body["cards"][0]["mechanism"] == "혈액순환·온열"
    assert set(body["cards"][0]["weakness_ids"]) == {w1.id, w2.id}


@pytest.mark.django_db
def test_herb_update_replaces_cards_not_appends():
    user = _make_admin("editor", [("adm_023", "read"), ("adm_023", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    herb = Herb.objects.create(id="HRB-01", name="육계")
    old_card = HerbCard.objects.create(herb=herb, mechanism="옛 효능")
    old_card.weaknesses.add(w1)

    resp = client.patch(
        "/api/content/herbs/HRB-01/",
        {"cards": [{"mechanism": "새 효능", "description": "새 설명", "weakness_ids": [w1.id]}]},
        format="json",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["cards"]) == 1
    assert body["cards"][0]["mechanism"] == "새 효능"
    assert not HerbCard.objects.filter(mechanism="옛 효능").exists()


@pytest.mark.django_db
def test_herb_list_shows_weakness_names_and_card_count():
    user = _make_admin("editor", [("adm_023", "read")])
    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    herb = Herb.objects.create(id="HRB-01", name="육계", hanja="肉桂")
    card = HerbCard.objects.create(herb=herb, mechanism="효능")
    card.weaknesses.add(w1)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/herbs/")
    assert resp.status_code == 200
    body = resp.json()[0]
    assert body["weakness_names"] == ["추위"]
    assert body["card_count"] == 1
    assert body["hanja"] == "肉桂"


@pytest.mark.django_db
def test_herb_delete_cascades_cards_and_is_audited():
    user = _make_admin("editor", [("adm_023", "read"), ("adm_023", "write"), ("adm_023", "delete")])
    client = APIClient()
    client.force_authenticate(user=user)

    herb = Herb.objects.create(id="HRB-01", name="육계")
    card = HerbCard.objects.create(herb=herb, mechanism="효능")
    card_id = card.id

    resp = client.delete("/api/content/herbs/HRB-01/")
    assert resp.status_code == 204
    assert not Herb.objects.filter(id="HRB-01").exists()
    assert not HerbCard.objects.filter(id=card_id).exists()
    assert AuditLog.objects.filter(target_table="herb_card", target_id=str(card_id), action="delete").exists()


@pytest.mark.django_db
def test_herb_write_denied_without_adm_023_permission():
    user = _make_admin("cs", [("adm_003", "read")])
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/content/herbs/", {"name": "육계"}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_food_create_with_weaknesses():
    user = _make_admin("editor", [("adm_025", "read"), ("adm_025", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    w2 = Weakness.objects.create(id="WEAK-02", name="소화불량")

    resp = client.post(
        "/api/content/foods/",
        {
            "polarity": "제한",
            "foods": "시금치·케일·브로콜리",
            "component": "칼륨",
            "description": "신장의 나트륨 배출을 돕는다",
            "weakness_ids": [w1.id, w2.id],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "FOOD-01"  # 서버 채번
    assert body["polarity"] == "제한"
    assert set(body["weakness_ids"]) == {w1.id, w2.id}


@pytest.mark.django_db
def test_food_update_replaces_weaknesses_not_appends():
    user = _make_admin("editor", [("adm_025", "read"), ("adm_025", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    w2 = Weakness.objects.create(id="WEAK-02", name="소화불량")
    food = Food.objects.create(id="FOOD-01", foods="고구마")
    food.weaknesses.add(w1)

    resp = client.patch("/api/content/foods/FOOD-01/", {"weakness_ids": [w2.id]}, format="json")
    assert resp.status_code == 200
    assert resp.json()["weakness_ids"] == [w2.id]


@pytest.mark.django_db
def test_food_list_shows_polarity_and_weakness_names():
    user = _make_admin("editor", [("adm_025", "read")])
    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    food = Food.objects.create(id="FOOD-01", foods="생강차", polarity="권장", component="진저롤")
    food.weaknesses.add(w1)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/foods/")
    assert resp.status_code == 200
    body = resp.json()[0]
    assert body["polarity"] == "권장"
    assert body["weakness_names"] == ["추위"]


@pytest.mark.django_db
def test_food_delete_is_audited():
    user = _make_admin("editor", [("adm_025", "read"), ("adm_025", "write"), ("adm_025", "delete")])
    client = APIClient()
    client.force_authenticate(user=user)

    Food.objects.create(id="FOOD-01", foods="고구마")
    resp = client.delete("/api/content/foods/FOOD-01/")
    assert resp.status_code == 204
    assert not Food.objects.filter(id="FOOD-01").exists()
    assert AuditLog.objects.filter(target_table="food", target_id="FOOD-01", action="delete").exists()


@pytest.mark.django_db
def test_food_write_denied_without_adm_025_permission():
    user = _make_admin("cs", [("adm_003", "read")])
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/content/foods/", {"foods": "고구마"}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_food_component_options_returns_distinct_values():
    user = _make_admin("editor", [("adm_025", "read")])
    Food.objects.create(id="FOOD-01", foods="시금치", component="칼륨")
    Food.objects.create(id="FOOD-02", foods="바나나", component="칼륨")
    Food.objects.create(id="FOOD-03", foods="생강차", component="진저롤")
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/food-components/")
    assert resp.status_code == 200
    assert resp.json() == ["진저롤", "칼륨"]


@pytest.mark.django_db
def test_point_create_with_weaknesses():
    user = _make_admin("editor", [("adm_026", "read"), ("adm_026", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")

    resp = client.post(
        "/api/content/points/",
        {
            "name": "합곡",
            "hanja": "合谷",
            "description": "두통·통증 완화에 도움",
            "location": "엄지와 검지 사이 갈퀴막",
            "video": "https://example.com/hapgok",
            "weakness_ids": [w1.id],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "ACU-01"  # 서버 채번
    assert body["hanja"] == "合谷"
    assert body["weakness_ids"] == [w1.id]
    assert "tip" not in body


@pytest.mark.django_db
def test_point_update_replaces_weaknesses_not_appends():
    user = _make_admin("editor", [("adm_026", "read"), ("adm_026", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    w2 = Weakness.objects.create(id="WEAK-02", name="소화불량")
    point = Point.objects.create(id="ACU-01", name="합곡")
    point.weaknesses.add(w1)

    resp = client.patch("/api/content/points/ACU-01/", {"weakness_ids": [w2.id]}, format="json")
    assert resp.status_code == 200
    assert resp.json()["weakness_ids"] == [w2.id]


@pytest.mark.django_db
def test_point_list_shows_weakness_names():
    user = _make_admin("editor", [("adm_026", "read")])
    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    point = Point.objects.create(id="ACU-01", name="합곡", hanja="合谷")
    point.weaknesses.add(w1)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/points/")
    assert resp.status_code == 200
    body = resp.json()[0]
    assert body["weakness_names"] == ["추위"]
    assert body["hanja"] == "合谷"


@pytest.mark.django_db
def test_point_delete_is_audited():
    user = _make_admin("editor", [("adm_026", "read"), ("adm_026", "write"), ("adm_026", "delete")])
    client = APIClient()
    client.force_authenticate(user=user)

    Point.objects.create(id="ACU-01", name="합곡")
    resp = client.delete("/api/content/points/ACU-01/")
    assert resp.status_code == 204
    assert not Point.objects.filter(id="ACU-01").exists()
    assert AuditLog.objects.filter(target_table="point", target_id="ACU-01", action="delete").exists()


@pytest.mark.django_db
def test_point_write_denied_without_adm_026_permission():
    user = _make_admin("cs", [("adm_003", "read")])
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/content/points/", {"name": "합곡"}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_health_sign_create_with_weaknesses():
    user = _make_admin("editor", [("adm_007a", "read"), ("adm_007a", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")

    resp = client.post(
        "/api/content/health-signs/",
        {"name": "척추/관절이 아프다", "note": "짧은 관점", "weakness_ids": [w1.id]},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "SIG-01"  # 서버 채번
    assert body["weakness_ids"] == [w1.id]


@pytest.mark.django_db
def test_health_sign_update_replaces_weaknesses_not_appends():
    user = _make_admin("editor", [("adm_007a", "read"), ("adm_007a", "write")])
    client = APIClient()
    client.force_authenticate(user=user)

    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    w2 = Weakness.objects.create(id="WEAK-02", name="소화불량")
    sign = HealthSign.objects.create(id="SIG-01", name="척추/관절이 아프다")
    sign.weaknesses.add(w1)

    resp = client.patch("/api/content/health-signs/SIG-01/", {"weakness_ids": [w2.id]}, format="json")
    assert resp.status_code == 200
    assert resp.json()["weakness_ids"] == [w2.id]


@pytest.mark.django_db
def test_health_sign_list_shows_weakness_names():
    user = _make_admin("editor", [("adm_007a", "read")])
    w1 = Weakness.objects.create(id="WEAK-01", name="추위")
    sign = HealthSign.objects.create(id="SIG-01", name="척추/관절이 아프다", note="짧은 관점")
    sign.weaknesses.add(w1)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/content/health-signs/")
    assert resp.status_code == 200
    assert resp.json()[0]["weakness_names"] == ["추위"]


@pytest.mark.django_db
def test_health_sign_delete_is_audited():
    user = _make_admin("editor", [("adm_007a", "read"), ("adm_007a", "write"), ("adm_007a", "delete")])
    client = APIClient()
    client.force_authenticate(user=user)

    HealthSign.objects.create(id="SIG-01", name="척추/관절이 아프다")
    resp = client.delete("/api/content/health-signs/SIG-01/")
    assert resp.status_code == 204
    assert not HealthSign.objects.filter(id="SIG-01").exists()
    assert AuditLog.objects.filter(target_table="health_sign", target_id="SIG-01", action="delete").exists()


@pytest.mark.django_db
def test_health_sign_write_denied_without_adm_007a_permission():
    user = _make_admin("cs", [("adm_003", "read")])
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/content/health-signs/", {"name": "척추/관절이 아프다"}, format="json")
    assert resp.status_code == 403
