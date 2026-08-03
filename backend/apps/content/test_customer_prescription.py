"""처방 스트림 API(/api/result/prescription/) 테스트.

여기서 잠그려는 것은 넷이다.
1. **초안·숨김 콘텐츠가 새지 않는다.** 처방은 로그인 뒤 화면이라 방심하기 쉽지만,
   게시 전 원고가 고객에게 보이는 건 결과화면보다 오히려 더 나쁘다(약재·식품이라서).
2. **약점 태그가 없으면 나오지 않는다** — 자동 구성의 전제(docs/06_decisions.md #3).
3. **큐레이션이 있으면 그것이 이긴다.** 순서까지 관리자가 정한 대로.
4. **같은 약재가 두 그룹에 겹치지 않는다.** 크레센도의 마지막 장면이라 눈에 띈다.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.content.models import (
    Article,
    Food,
    Herb,
    HerbCard,
    Nutrient,
    NutrientCard,
    TemType,
    TemTypeCuration,
    Weakness,
)
from apps.diagnosis.models import DiagnosisResult

PATH = "/api/result/prescription/"


@pytest.fixture
def weaknesses(db):
    """체질의 약점 순서가 곧 약재 그룹 순서다 — 추위 → 변비."""
    cold = Weakness.objects.create(id="WEAK-01", name="추위", catchphrase="매일 겨울을 사는 몸")
    consti = Weakness.objects.create(id="WEAK-03", name="변비", catchphrase="똥 막힌 하수도")
    return cold, consti


@pytest.fixture
def tem05(db, weaknesses):
    cold, consti = weaknesses
    tem = TemType.objects.create(
        id="TEM05", name="TE-5", herb_title="몸의 축을 데우는 인생처방", herb_desc="근본을 데운다"
    )
    tem.weaknesses.add(cold)
    tem.weaknesses.add(consti)
    return tem


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        username="c@example.com", email="c@example.com", password="ollacare1234"
    )


@pytest.fixture
def client_with_result(customer, tem05):
    DiagnosisResult.objects.create(user=customer, raw_value=5, type_id="TEM05", status="완료")
    api = APIClient()
    api.force_authenticate(customer)
    return api


def _nutrient_card(nid: str, name: str, perspective: str, *tags: Weakness, status="게시"):
    nutrient = Nutrient.objects.create(id=nid, name=name, status=status)
    card = NutrientCard.objects.create(nutrient=nutrient, perspective=perspective)
    for tag in tags:
        card.weaknesses.add(tag)
    return card


def _herb_card(hid: str, name: str, *tags: Weakness, status="게시"):
    herb = Herb.objects.create(id=hid, name=name, status=status)
    card = HerbCard.objects.create(herb=herb, mechanism="온중")
    for tag in tags:
        card.weaknesses.add(tag)
    return card


# ── 접근 제어 ─────────────────────────────────────────────────────
@pytest.mark.django_db
def test_prescription_requires_login(tem05):
    """처방은 가입의 대가다. 비로그인으로 열리면 티저→가입 동선이 통째로 무의미해진다."""
    assert APIClient().get(PATH).status_code == 403


@pytest.mark.django_db
def test_prescription_without_diagnosis(customer):
    api = APIClient()
    api.force_authenticate(customer)
    assert api.get(PATH).json() == {"hasResult": False}


@pytest.mark.django_db
def test_prescription_reports_missing_type(customer, db):
    DiagnosisResult.objects.create(user=customer, raw_value=42, type_id="TEM42", status="완료")
    api = APIClient()
    api.force_authenticate(customer)
    body = api.get(PATH).json()
    assert body["hasResult"] is True and body["found"] is False


# ── 약점 태그 자동 구성 ───────────────────────────────────────────
@pytest.mark.django_db
def test_stations_are_built_from_weakness_tags(client_with_result, weaknesses):
    cold, consti = weaknesses
    _nutrient_card("N1", "마그네슘", "순환·이완", cold)
    Food.objects.create(id="F1", polarity="권장", component="복합탄수화물", foods="현미·귀리")
    Food.objects.get(pk="F1").weaknesses.add(cold)
    Food.objects.create(id="F2", polarity="제한", component="포드맵", foods="양파·마늘").weaknesses.add(
        consti
    )
    Article.objects.create(id="A1", kind="지압·마사지", title="위장마사지").weaknesses.add(cold)
    _herb_card("H1", "육계", cold)

    body = client_with_result.get(PATH).json()
    assert [n["name"] for n in body["nutrition"]] == ["마그네슘"]
    assert [f["component"] for f in body["diet"]["good"]] == ["복합탄수화물"]
    assert [f["component"] for f in body["diet"]["limit"]] == ["포드맵"]
    assert [a["title"] for a in body["life"]] == ["위장마사지"]
    assert body["herb"]["title"] == "몸의 축을 데우는 인생처방"
    assert [g["catchphrase"] for g in body["herb"]["groups"]] == ["매일 겨울을 사는 몸"]


@pytest.mark.django_db
def test_untagged_content_never_reaches_the_customer(client_with_result, db):
    """약점 태그가 없는 콘텐츠는 고객 화면에 나타나지 않는다(결정 #3)."""
    _nutrient_card("N9", "떠도는 영양소", "무관")
    Food.objects.create(id="F9", polarity="권장", component="떠도는 식품군")
    Article.objects.create(id="A9", kind="생활", title="떠도는 요법")
    _herb_card("H9", "떠도는 약재")

    body = client_with_result.get(PATH).json()
    assert body["nutrition"] == []
    assert body["diet"] == {"good": [], "limit": []}
    assert body["life"] == []
    assert body["herb"]["groups"] == []


@pytest.mark.django_db
def test_unpublished_content_never_reaches_the_customer(client_with_result, weaknesses):
    cold, _ = weaknesses
    _nutrient_card("N2", "숨은 영양소", "관점", cold, status="초안")
    Food.objects.create(id="F3", polarity="권장", component="숨은 식품군", status="초안").weaknesses.add(
        cold
    )
    Article.objects.create(id="A2", kind="생활", title="숨은 요법", status="초안").weaknesses.add(cold)
    _herb_card("H2", "숨은 약재", cold, status="초안")

    body = client_with_result.get(PATH).json()
    assert body["nutrition"] == []
    assert body["diet"] == {"good": [], "limit": []}
    assert body["life"] == []
    assert body["herb"]["groups"] == []


# ── 큐레이션(유일한 수동 예외) ────────────────────────────────────
@pytest.mark.django_db
def test_curation_overrides_auto_selection_and_keeps_its_order(client_with_result, tem05, weaknesses):
    cold, _ = weaknesses
    first = _nutrient_card("N3", "마그네슘", "순환", cold)
    second = _nutrient_card("N4", "비타민D", "면역", cold)
    _nutrient_card("N5", "고르지 않은 것", "관점", cold)

    # 관리자가 고른 순서는 sort 1 → 2. 자동 구성이었다면 셋 다 나왔을 것이다.
    TemTypeCuration.objects.create(tem_type=tem05, kind="nutrient", ref_id=str(second.pk), sort=1)
    TemTypeCuration.objects.create(tem_type=tem05, kind="nutrient", ref_id=str(first.pk), sort=2)

    names = [n["name"] for n in client_with_result.get(PATH).json()["nutrition"]]
    assert names == ["비타민D", "마그네슘"]


@pytest.mark.django_db
def test_curation_does_not_apply_to_life_articles(client_with_result, tem05, weaknesses):
    """요법은 큐레이션 대상이 아니다 — 예외는 영양·약재·식품군 셋뿐(결정 #3)."""
    cold, _ = weaknesses
    Article.objects.create(id="A3", kind="생활", title="자동으로 붙는 요법").weaknesses.add(cold)
    TemTypeCuration.objects.create(tem_type=tem05, kind="nutrient", ref_id="999", sort=1)

    assert [a["title"] for a in client_with_result.get(PATH).json()["life"]] == ["자동으로 붙는 요법"]


@pytest.mark.django_db
def test_curated_herb_outside_my_weaknesses_survives_without_a_title(
    client_with_result, tem05, weaknesses
):
    """원장이 고른 약재를 조용히 버리지 않는다. 제목만 비운 그룹으로 남긴다."""
    other = Weakness.objects.create(id="WEAK-05", name="부종", catchphrase="물 먹은 스펀지")
    stray = _herb_card("H3", "택사", other)
    TemTypeCuration.objects.create(tem_type=tem05, kind="herb", ref_id=str(stray.pk), sort=1)

    groups = client_with_result.get(PATH).json()["herb"]["groups"]
    assert len(groups) == 1
    assert groups[0]["weaknessId"] is None and groups[0]["catchphrase"] == ""
    assert [h["name"] for h in groups[0]["items"]] == ["택사"]


# ── 약재 그룹핑 ───────────────────────────────────────────────────
@pytest.mark.django_db
def test_herb_tagged_with_two_weaknesses_appears_only_once(client_with_result, weaknesses):
    """황금처럼 약점을 넘나드는 약재가 두 그룹에 보이면 '왜 두 번 나오지'가 된다."""
    cold, consti = weaknesses
    _herb_card("H4", "황금", cold, consti)

    groups = client_with_result.get(PATH).json()["herb"]["groups"]
    assert [g["weaknessName"] for g in groups] == ["추위"]  # 약점 순서상 처음 만나는 곳
    assert sum(len(g["items"]) for g in groups) == 1


@pytest.mark.django_db
def test_life_item_shows_only_my_own_weaknesses(client_with_result, weaknesses):
    """요법에 붙은 다른 약점까지 보여주면 내 것이 아닌 이야기가 섞인다."""
    cold, _ = weaknesses
    other = Weakness.objects.create(id="WEAK-06", name="불면", catchphrase="잠 못 드는 밤")
    article = Article.objects.create(id="A4", kind="생활", title="저녁 스트레칭")
    article.weaknesses.add(cold)
    article.weaknesses.add(other)

    life = client_with_result.get(PATH).json()["life"]
    assert life[0]["weaknesses"] == ["추위"]
