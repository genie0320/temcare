"""콘텐츠 마스터 API 테스트.

방침: 화면 10개가 같은 뼈대를 쓰므로 **공통 규칙은 파라미터화해서 한 번만** 쓰고,
화면마다 진짜로 다른 것(카드 구조·큐레이션·참고정보)만 개별 테스트로 둔다.
같은 코드경로를 10번 확인하는 클론 테스트는 통과 개수만 늘릴 뿐 지켜주는 게 없다.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import AdminPermission, AdminProfile, AdminRole, User
from apps.audit.models import AuditLog
from apps.content.models import (
    Article,
    Food,
    HealthSign,
    HerbCard,
    Illness,
    LifeArticle,
    Nutrient,
    NutrientCard,
    Point,
    Product,
    TemType,
    Weakness,
)

_UNIQ = iter(range(1, 100_000))


def _make_admin(role_id, resources_actions):
    role, _ = AdminRole.objects.get_or_create(id=role_id, defaults={"name": role_id, "sort": 0})
    for resource, action in resources_actions:
        AdminPermission.objects.get_or_create(
            role=role, resource=resource, action=action, defaults={"allowed": True}
        )
    user = User.objects.create_user(
        username=f"{role_id}-{next(_UNIQ)}@test.local", password="pass1234!", is_staff=True
    )
    AdminProfile.objects.create(user=user, role=role)
    return user


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _weakness(suffix="01", name="추위"):
    return Weakness.objects.create(id=f"WEAK-{suffix}", name=name)


class MasterSpec:
    """화면마다 다른 것만 담는다. 공통 규칙 테스트가 이걸 돌려가며 쓴다."""

    def __init__(self, name, path, resource, first_id, create, *, weakness_required=True, model=None):
        self.name = name
        self.path = path
        self.resource = resource
        self.first_id = first_id
        self.create = create
        self.weakness_required = weakness_required
        self.model = model

    def __repr__(self):
        return self.name


MASTERS = [
    MasterSpec(
        "weakness", "weaknesses", "adm_003", "WEAK-01",
        {"name": "새약점", "wtype": "약점", "catchphrase": "테스트용"},
        weakness_required=False, model=Weakness,
    ),
    MasterSpec(
        "food", "foods", "adm_025", "FOOD-01",
        {"polarity": "제한", "foods": "시금치·케일", "component": "칼륨", "description": "설명"},
        model=Food,
    ),
    MasterSpec(
        "point", "points", "adm_026", "ACU-01",
        {"name": "합곡", "hanja": "合谷", "description": "두통 완화", "location": "갈퀴막"},
        model=Point,
    ),
    MasterSpec(
        "health_sign", "health-signs", "adm_007a", "SIG-01",
        {"name": "척추/관절이 아프다", "note": "짧은 관점"}, model=HealthSign,
    ),
    MasterSpec(
        "illness", "illnesses", "adm_007b", "ILL-01",
        {"name": "소화기질환", "description": "질환 상세"}, model=Illness,
    ),
    MasterSpec(
        "product", "products", "adm_027", "PRD-01",
        {"name": "생강 온열팩", "description": "상품 설명", "url": "https://example.com/item"},
        weakness_required=False, model=Product,
    ),
    MasterSpec(
        "article", "articles", "adm_024", "ART-01",
        {"kind": "식이", "title": "위장마사지", "body": "<p>본문</p>"}, model=Article,
    ),
    MasterSpec(
        "life_article", "life-articles", "adm_009", "LIFE-01",
        {"category": "체온", "title": "찬 음료 대신 따뜻한 차", "body": "<p>본문</p>"},
        weakness_required=False, model=LifeArticle,
    ),
]

WEAKNESS_TAGGED = [m for m in MASTERS if m.weakness_required]


@pytest.mark.django_db
@pytest.mark.parametrize("spec", MASTERS, ids=repr)
def test_master_requires_login(spec):
    assert APIClient().get(f"/api/content/{spec.path}/").status_code in (401, 403)


@pytest.mark.django_db
@pytest.mark.parametrize("spec", MASTERS, ids=repr)
def test_master_write_denied_for_read_only_role(spec):
    """read만 있는 역할은 쓰기가 막힌다. write는 read에 딸려오지 않는다."""
    client = _client(_make_admin(f"ro_{spec.name}", [(spec.resource, "read")]))
    assert client.post(f"/api/content/{spec.path}/", spec.create, format="json").status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("spec", MASTERS, ids=repr)
def test_master_create_and_delete_are_audited(spec):
    """생성·삭제가 감사로그에 남는다(AuditedModel 상속이 실제로 동작하는지)."""
    client = _client(
        _make_admin(
            f"ed_{spec.name}",
            [(spec.resource, "read"), (spec.resource, "write"), (spec.resource, "delete")],
        )
    )
    payload = dict(spec.create)
    if spec.weakness_required:
        payload["weakness_ids"] = [_weakness().id]

    resp = client.post(f"/api/content/{spec.path}/", payload, format="json")
    assert resp.status_code == 201, resp.content
    created_id = resp.json()["id"]
    assert created_id == spec.first_id  # 서버 채번

    table = spec.model._meta.db_table
    assert AuditLog.objects.filter(action="create", target_table=table, target_id=created_id).exists()

    assert client.delete(f"/api/content/{spec.path}/{created_id}/").status_code == 204
    assert AuditLog.objects.filter(action="delete", target_table=table, target_id=created_id).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("spec", WEAKNESS_TAGGED, ids=repr)
def test_master_create_without_weakness_tag_is_rejected(spec):
    """약점 태그 없는 콘텐츠는 저장을 막는다.

    태그가 없으면 고객 화면(처방 스트림)이 이 콘텐츠를 영영 끌어오지 못한다 —
    저장은 성공했는데 아무 데도 안 나오는 조용한 실종을 막는 방어선이다.
    docs/02_architecture_constraints.md §7, docs/05_screen_conventions.md §G.
    """
    client = _client(_make_admin(f"nw_{spec.name}", [(spec.resource, "read"), (spec.resource, "write")]))

    resp = client.post(f"/api/content/{spec.path}/", {**spec.create, "weakness_ids": []}, format="json")
    assert resp.status_code == 400, f"{spec.name}: 약점 0개인데 저장됐다"
    assert "weakness_ids" in resp.json()

    resp = client.post(f"/api/content/{spec.path}/", spec.create, format="json")
    assert resp.status_code == 400, f"{spec.name}: weakness_ids 키를 아예 빼면 통과해버린다"


@pytest.mark.django_db
@pytest.mark.parametrize("spec", WEAKNESS_TAGGED, ids=repr)
def test_master_cannot_strip_all_weakness_tags(spec):
    """이미 있는 콘텐츠에서 약점 태그를 전부 제거하는 것도 막는다(수정 경로)."""
    client = _client(_make_admin(f"st_{spec.name}", [(spec.resource, "read"), (spec.resource, "write")]))
    w = _weakness()
    created = client.post(
        f"/api/content/{spec.path}/", {**spec.create, "weakness_ids": [w.id]}, format="json"
    ).json()

    resp = client.patch(f"/api/content/{spec.path}/{created['id']}/", {"weakness_ids": []}, format="json")
    assert resp.status_code == 400
    detail = client.get(f"/api/content/{spec.path}/{created['id']}/").json()
    assert detail["weakness_ids"] == [w.id], "거부됐는데 태그가 지워졌다"


@pytest.mark.django_db
@pytest.mark.parametrize("spec", WEAKNESS_TAGGED, ids=repr)
def test_master_weakness_count_is_not_validated(spec):
    """★ 약점 '개수'는 검증하지 않는다 — IDEA끼리 조합되는 예외(TEM54)가 있다.

    이 테스트는 기능이 아니라 **미래의 과잉검증을 막는 자물쇠**다. 누군가 '약점은 2개여야
    한다' 같은 규칙을 넣으면 여기서 깨진다. docs/05_screen_conventions.md §G.
    """
    client = _client(_make_admin(f"cnt_{spec.name}", [(spec.resource, "read"), (spec.resource, "write")]))
    many = [_weakness(f"{i:02d}", f"약점{i}").id for i in range(1, 6)]

    one = client.post(f"/api/content/{spec.path}/", {**spec.create, "weakness_ids": many[:1]}, format="json")
    assert one.status_code == 201, "약점 1개를 거부하면 안 된다"

    five = client.post(f"/api/content/{spec.path}/", {**spec.create, "weakness_ids": many}, format="json")
    assert five.status_code == 201, "약점 5개를 거부하면 안 된다"


@pytest.mark.django_db
@pytest.mark.parametrize("spec", WEAKNESS_TAGGED, ids=repr)
def test_master_update_replaces_weakness_tags_not_appends(spec):
    """태그 수정은 '교체'다. 누적되면 지운 태그가 살아남아 고객 화면에 잘못 노출된다."""
    client = _client(_make_admin(f"rep_{spec.name}", [(spec.resource, "read"), (spec.resource, "write")]))
    w1, w2 = _weakness("01", "추위"), _weakness("02", "변비")
    created = client.post(
        f"/api/content/{spec.path}/", {**spec.create, "weakness_ids": [w1.id]}, format="json"
    ).json()

    resp = client.patch(
        f"/api/content/{spec.path}/{created['id']}/", {"weakness_ids": [w2.id]}, format="json"
    )
    assert resp.status_code == 200, resp.content
    assert resp.json()["weakness_ids"] == [w2.id]


# ── 약점 마스터 고유 ─────────────────────────────────────────────
@pytest.mark.django_db
def test_weakness_crud_round_trip():
    user = _make_admin("editor", [("adm_003", "read"), ("adm_003", "write"), ("adm_003", "delete")])
    client = _client(user)

    assert client.get("/api/content/weaknesses/").json() == []

    resp = client.post(
        "/api/content/weaknesses/",
        {"name": "새약점", "wtype": "약점", "catchphrase": "테스트용"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    created = resp.json()
    assert created["id"] == "WEAK-01"

    resp = client.patch(f"/api/content/weaknesses/{created['id']}/", {"name": "고친약점"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["name"] == "고친약점"
    assert resp.json()["updated_by"] == user.username

    assert client.delete(f"/api/content/weaknesses/{created['id']}/").status_code == 204
    assert Weakness.objects.count() == 0


@pytest.mark.django_db
def test_client_cannot_choose_id_or_forge_updated_by():
    """id·updated_by는 서버가 정한다. 클라이언트가 보낸 값은 무시돼야 한다.

    (예전 테스트는 body에 id를 아예 안 보내서, read_only가 풀려도 통과했다.)
    """
    user = _make_admin("editor", [("adm_003", "read"), ("adm_003", "write")])
    client = _client(user)

    resp = client.post(
        "/api/content/weaknesses/",
        {"id": "HACKED-99", "name": "약점", "wtype": "약점", "updated_by": "다른사람"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "WEAK-01", "클라이언트가 보낸 id가 그대로 먹혔다"
    assert body["updated_by"] == user.username, "updated_by를 클라이언트가 위조할 수 있다"


@pytest.mark.django_db
def test_weakness_list_serializer_excludes_detail_only_fields():
    client = _client(_make_admin("editor", [("adm_003", "read")]))
    Weakness.objects.create(id="WEAK-01", name="추위", aphorism="긴 격언 문장", speaker="원장")

    row = client.get("/api/content/weaknesses/").json()[0]
    assert "aphorism" not in row and "speaker" not in row


# ── 64유형(adm_002) 고유: 약점 + 발병율 + 큐레이션 ───────────────
@pytest.mark.django_db
def test_tem_type_create_with_children():
    client = _client(_make_admin("editor", [("adm_002", "read"), ("adm_002", "write")]))
    w1 = _weakness("01", "추위")
    illness = Illness.objects.create(id="ILL-01", name="소화기질환")
    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민D")
    card = NutrientCard.objects.create(nutrient=nutrient, perspective="대사회복")
    food = Food.objects.create(id="FOOD-01", polarity="권장", foods="생강")

    resp = client.post(
        "/api/content/tem-types/",
        {
            "name": "TE-5",
            "nickname": "겨울나무",
            "body_min": 1,
            "body_max": 3,
            "weakness_ids": [w1.id],
            "illnesses": [{"illness_id": illness.id, "pct": 30}],
            "nutrient_card_ids": [str(card.id)],
            "food_ids": [food.id],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "TEM01"
    assert body["weakness_ids"] == [w1.id]
    assert body["illnesses"] == [{"illness_id": illness.id, "pct": 30}]
    assert body["nutrient_card_ids"] == [str(card.id)]
    assert body["food_ids"] == [food.id]
    # 체형 단일값은 서버가 범위에서 파생한다
    assert TemType.objects.get(id="TEM01").body_value == round((1 + 3) / 2 * 25)


@pytest.mark.django_db
def test_tem_type_update_replaces_children_not_appends():
    client = _client(_make_admin("editor", [("adm_002", "read"), ("adm_002", "write")]))
    w1, w2 = _weakness("01", "추위"), _weakness("02", "변비")
    i1 = Illness.objects.create(id="ILL-01", name="소화기질환")
    i2 = Illness.objects.create(id="ILL-02", name="순환기질환")
    created = client.post(
        "/api/content/tem-types/",
        {"name": "TE-5", "weakness_ids": [w1.id], "illnesses": [{"illness_id": i1.id, "pct": 30}]},
        format="json",
    ).json()

    resp = client.patch(
        f"/api/content/tem-types/{created['id']}/",
        {"weakness_ids": [w2.id], "illnesses": [{"illness_id": i2.id, "pct": 55}]},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    assert resp.json()["weakness_ids"] == [w2.id]
    assert resp.json()["illnesses"] == [{"illness_id": i2.id, "pct": 55}]


@pytest.mark.django_db
def test_illness_percentages_are_not_forced_to_sum_to_100():
    """★ 발병율 합계 100% 검증을 하지 않는다 — 질환별 독립 발병율이기 때문.

    이것도 미래의 과잉검증을 막는 자물쇠다. docs/06_decisions.md #4.
    """
    client = _client(_make_admin("editor", [("adm_002", "read"), ("adm_002", "write")]))
    w = _weakness()
    i1 = Illness.objects.create(id="ILL-01", name="A")
    i2 = Illness.objects.create(id="ILL-02", name="B")

    resp = client.post(
        "/api/content/tem-types/",
        {
            "name": "TE-1",
            "weakness_ids": [w.id],
            # 합계 155% — 거부되면 안 된다
            "illnesses": [{"illness_id": i1.id, "pct": 80}, {"illness_id": i2.id, "pct": 75}],
        },
        format="json",
    )
    assert resp.status_code == 201, "합계가 100이 아니라고 거부하면 안 된다"


@pytest.mark.django_db
def test_tem_type_list_shows_weakness_names_not_ids():
    client = _client(_make_admin("editor", [("adm_002", "read")]))
    w = Weakness.objects.create(id="WEAK-01", name="추위")
    tem = TemType.objects.create(id="TEM01", name="TE-5")
    tem.weaknesses.add(w)

    row = client.get("/api/content/tem-types/").json()[0]
    assert row["weakness_names"] == ["추위"]


@pytest.mark.django_db
def test_curation_candidates_are_filtered_by_selected_weakness():
    """큐레이션 후보는 선택한 약점을 가진 것만 나온다(§7 자동 후보 구성의 핵심)."""
    client = _client(_make_admin("editor", [("adm_002", "read")]))
    w1, w2 = _weakness("01", "추위"), _weakness("02", "소화불량")
    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민 B")
    matching = NutrientCard.objects.create(nutrient=nutrient, perspective="대사회복")
    matching.weaknesses.add(w1)
    other = NutrientCard.objects.create(nutrient=nutrient, perspective="신경안정")
    other.weaknesses.add(w2)

    rows = client.get(f"/api/content/tem-type-candidates/nutrient-cards/?weaknesses={w1.id}").json()
    ids = [item["id"] for item in rows]
    assert str(matching.id) in ids
    assert str(other.id) not in ids


@pytest.mark.django_db
def test_food_candidates_expose_polarity_badge():
    client = _client(_make_admin("editor", [("adm_002", "read")]))
    w = _weakness()
    food = Food.objects.create(id="FOOD-01", polarity="제한", foods="포드맵", component="양파")
    food.weaknesses.add(w)

    row = client.get(f"/api/content/tem-type-candidates/foods/?weaknesses={w.id}").json()[0]
    assert row["polarity"] == "제한"


# ── 카드형 마스터(영양소·약재) 고유 ──────────────────────────────
CARD_MASTERS = [
    ("nutrient", "nutrients", "adm_022", "NUT-01", "perspective", {"name": "비타민D"}, NutrientCard),
    ("herb", "herbs", "adm_023", "HRB-01", "mechanism", {"name": "진피", "hanja": "陳皮"}, HerbCard),
]
_CARD_IDS = [c[0] for c in CARD_MASTERS]
_CARD_ARGS = "name,path,resource,first_id,text_field,base,card_model"


@pytest.mark.django_db
@pytest.mark.parametrize(_CARD_ARGS, CARD_MASTERS, ids=_CARD_IDS)
def test_card_master_create_with_cards(name, path, resource, first_id, text_field, base, card_model):
    client = _client(_make_admin(f"ed_{name}", [(resource, "read"), (resource, "write")]))
    w1, w2 = _weakness("01", "추위"), _weakness("02", "변비")

    resp = client.post(
        f"/api/content/{path}/",
        {
            **base,
            "cards": [
                {text_field: "관점A", "description": "설명A", "weakness_ids": [w1.id]},
                {text_field: "관점B", "description": "설명B", "weakness_ids": [w2.id]},
            ],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert resp.json()["id"] == first_id
    assert card_model.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(_CARD_ARGS, CARD_MASTERS, ids=_CARD_IDS)
def test_card_master_rejects_card_without_weakness(name, path, resource, first_id, text_field, base, card_model):
    """카드형은 카드가 약점을 문다 — 약점 없는 카드는 고객 화면에 안 나온다."""
    client = _client(_make_admin(f"nw_{name}", [(resource, "read"), (resource, "write")]))

    resp = client.post(
        f"/api/content/{path}/",
        {**base, "cards": [{text_field: "관점A", "description": "설명", "weakness_ids": []}]},
        format="json",
    )
    assert resp.status_code == 400, "약점 없는 카드가 저장됐다"
    assert card_model.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(_CARD_ARGS, CARD_MASTERS, ids=_CARD_IDS)
def test_card_master_update_replaces_cards_not_appends(name, path, resource, first_id, text_field, base, card_model):
    client = _client(_make_admin(f"rp_{name}", [(resource, "read"), (resource, "write")]))
    w = _weakness()
    created = client.post(
        f"/api/content/{path}/",
        {**base, "cards": [{text_field: "관점A", "description": "A", "weakness_ids": [w.id]}]},
        format="json",
    ).json()

    resp = client.patch(
        f"/api/content/{path}/{created['id']}/",
        {"cards": [{text_field: "관점B", "description": "B", "weakness_ids": [w.id]}]},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    assert card_model.objects.count() == 1
    assert getattr(card_model.objects.first(), text_field) == "관점B"


@pytest.mark.django_db
def test_nutrient_list_shows_weakness_names_and_card_count():
    client = _client(_make_admin("editor", [("adm_022", "read")]))
    w = Weakness.objects.create(id="WEAK-01", name="추위")
    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민D")
    card = NutrientCard.objects.create(nutrient=nutrient, perspective="대사")
    card.weaknesses.add(w)

    row = client.get("/api/content/nutrients/").json()[0]
    assert row["weakness_names"] == ["추위"]
    assert row["card_count"] == 1


@pytest.mark.django_db
def test_nutrient_delete_cascades_cards():
    client = _client(_make_admin("editor", [("adm_022", "read"), ("adm_022", "delete")]))
    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민D")
    NutrientCard.objects.create(nutrient=nutrient, perspective="대사")

    assert client.delete("/api/content/nutrients/NUT-01/").status_code == 204
    assert NutrientCard.objects.count() == 0


# ── 요법관리(adm_024) 고유: 참고정보 3종 ─────────────────────────
@pytest.mark.django_db
def test_article_create_with_references():
    client = _client(_make_admin("editor", [("adm_024", "read"), ("adm_024", "write")]))
    w = _weakness()
    food = Food.objects.create(id="FOOD-01", foods="생강차")
    point = Point.objects.create(id="ACU-01", name="합곡")
    product = Product.objects.create(id="PRD-01", name="생강 온열팩")

    resp = client.post(
        "/api/content/articles/",
        {
            "kind": "식이",
            "title": "위장마사지",
            "body": "<p>본문</p>",
            "weakness_ids": [w.id],
            "food_ids": [food.id],
            "point_ids": [point.id],
            "product_ids": [product.id],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["food_ids"] == [food.id]
    assert body["point_ids"] == [point.id]
    assert body["product_ids"] == [product.id]


@pytest.mark.django_db
def test_article_update_replaces_references_not_appends():
    client = _client(_make_admin("editor", [("adm_024", "read"), ("adm_024", "write")]))
    w = _weakness()
    f1 = Food.objects.create(id="FOOD-01", foods="생강차")
    f2 = Food.objects.create(id="FOOD-02", foods="대추차")
    created = client.post(
        "/api/content/articles/",
        {"kind": "식이", "title": "T", "weakness_ids": [w.id], "food_ids": [f1.id]},
        format="json",
    ).json()

    resp = client.patch(f"/api/content/articles/{created['id']}/", {"food_ids": [f2.id]}, format="json")
    assert resp.status_code == 200
    assert resp.json()["food_ids"] == [f2.id]


# ── 템라이프(adm_009) 고유: 콘텐츠 마스터 8종 연결 + 관련 기사 ────
@pytest.mark.django_db
def test_life_article_create_with_all_content_link_kinds():
    """8종 전부 kind+ref_id로 저장되고, 서로 다른 kind끼리 섞여도 구분된다."""
    client = _client(_make_admin("editor", [("adm_009", "read"), ("adm_009", "write")]))
    nutrient = Nutrient.objects.create(id="NUT-01", name="비타민D")
    food = Food.objects.create(id="FOOD-01", foods="생강차")
    point = Point.objects.create(id="ACU-01", name="합곡")
    sign = HealthSign.objects.create(id="SIG-01", name="척추/관절이 아프다")
    illness = Illness.objects.create(id="ILL-01", name="소화기질환")
    product = Product.objects.create(id="PRD-01", name="생강 온열팩")
    article = Article.objects.create(id="ART-01", kind="식이", title="위장마사지")

    resp = client.post(
        "/api/content/life-articles/",
        {
            "category": "체온",
            "title": "겨울철 몸 데우는 법",
            "body": "<p>본문</p>",
            "nutrient_ids": [nutrient.id],
            "food_ids": [food.id],
            "point_ids": [point.id],
            "health_sign_ids": [sign.id],
            "illness_ids": [illness.id],
            "product_ids": [product.id],
            "article_ids": [article.id],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["id"] == "LIFE-01"
    assert body["nutrient_ids"] == [nutrient.id]
    assert body["food_ids"] == [food.id]
    assert body["point_ids"] == [point.id]
    assert body["health_sign_ids"] == [sign.id]
    assert body["illness_ids"] == [illness.id]
    assert body["product_ids"] == [product.id]
    assert body["article_ids"] == [article.id]
    assert body["herb_ids"] == []


@pytest.mark.django_db
def test_life_article_update_replaces_content_links_not_appends():
    """kind별로 나뉜 폴리모픽 테이블이라, 한 kind를 교체해도 다른 kind가 지워지면 안 된다."""
    client = _client(_make_admin("editor", [("adm_009", "read"), ("adm_009", "write")]))
    f1 = Food.objects.create(id="FOOD-01", foods="생강차")
    f2 = Food.objects.create(id="FOOD-02", foods="대추차")
    point = Point.objects.create(id="ACU-01", name="합곡")
    created = client.post(
        "/api/content/life-articles/",
        {"category": "체온", "title": "T", "food_ids": [f1.id], "point_ids": [point.id]},
        format="json",
    ).json()

    resp = client.patch(f"/api/content/life-articles/{created['id']}/", {"food_ids": [f2.id]}, format="json")
    assert resp.status_code == 200, resp.content
    assert resp.json()["food_ids"] == [f2.id]
    assert resp.json()["point_ids"] == [point.id], "food_ids만 바꿨는데 point 연결이 사라졌다"


@pytest.mark.django_db
def test_life_article_related_articles_are_self_referential_and_replace_not_append():
    client = _client(_make_admin("editor", [("adm_009", "read"), ("adm_009", "write")]))
    a1 = client.post(
        "/api/content/life-articles/", {"category": "체온", "title": "글1"}, format="json"
    ).json()
    a2 = client.post(
        "/api/content/life-articles/", {"category": "먹고싸고", "title": "글2"}, format="json"
    ).json()
    a3 = client.post(
        "/api/content/life-articles/", {"category": "멘탈", "title": "글3"}, format="json"
    ).json()

    resp = client.patch(
        f"/api/content/life-articles/{a1['id']}/", {"related_article_ids": [a2["id"]]}, format="json"
    )
    assert resp.status_code == 200, resp.content
    assert resp.json()["related_article_ids"] == [a2["id"]]

    resp = client.patch(
        f"/api/content/life-articles/{a1['id']}/", {"related_article_ids": [a3["id"]]}, format="json"
    )
    assert resp.status_code == 200
    assert resp.json()["related_article_ids"] == [a3["id"]], "교체가 아니라 누적됐다"


@pytest.mark.django_db
def test_life_article_list_exposes_image_for_feed_thumbnail():
    """뉴스피드형 목록이라 image가 목록 화면에도 노출돼야 한다(다른 마스터와 다른 점)."""
    client = _client(_make_admin("editor", [("adm_009", "read")]))
    LifeArticle.objects.create(id="LIFE-01", category="체온", title="글", image="life/x.png")

    row = client.get("/api/content/life-articles/").json()[0]
    assert row["image"] == "life/x.png"


# ── 자동완성 옵션 ────────────────────────────────────────────────
@pytest.mark.django_db
def test_component_options_return_distinct_sorted_values():
    client = _client(_make_admin("editor", [("adm_025", "read")]))
    Food.objects.create(id="FOOD-01", polarity="권장", component="칼륨")
    Food.objects.create(id="FOOD-02", polarity="권장", component="칼륨")
    Food.objects.create(id="FOOD-03", polarity="제한", component="나트륨")

    assert client.get("/api/content/food-components/").json() == ["나트륨", "칼륨"]


# ── 이미지 업로드 ────────────────────────────────────────────────
_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def _upload(client, filename, content, content_type, resource="adm_022"):
    return client.post(
        "/api/content/image-upload/",
        {"resource": resource, "file": SimpleUploadedFile(filename, content, content_type=content_type)},
        format="multipart",
    )


@pytest.mark.django_db
def test_image_upload_saves_file_and_returns_url(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    client = _client(_make_admin("editor", [("adm_022", "read"), ("adm_022", "write")]))

    resp = _upload(client, "photo.png", _PNG_BYTES, "image/png")
    assert resp.status_code == 201, resp.content
    assert resp.json()["url"].startswith("/media/adm_022/")


@pytest.mark.django_db
def test_image_upload_denied_without_write_permission(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    client = _client(_make_admin("viewer", [("adm_022", "read")]))

    assert _upload(client, "photo.png", _PNG_BYTES, "image/png").status_code == 403


@pytest.mark.django_db
def test_image_upload_rejects_disguised_non_image(tmp_path, settings):
    """★ 브라우저가 보낸 content_type은 위조할 수 있다 — 파일 내용으로 판정해야 한다.

    SVG/HTML을 image/png라고 우겨서 올리면 저장형 XSS 경로가 된다.
    (예전 테스트는 content_type만 봐서, 위장한 파일을 그대로 통과시켰다.)
    """
    settings.MEDIA_ROOT = tmp_path
    client = _client(_make_admin("editor", [("adm_022", "read"), ("adm_022", "write")]))

    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    assert _upload(client, "evil.png", svg, "image/png").status_code == 400, "내용이 이미지가 아닌데 저장됐다"

    html = b"<html><body><script>alert(1)</script></body></html>"
    assert _upload(client, "evil.jpg", html, "image/jpeg").status_code == 400
