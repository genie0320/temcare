"""고객용 결과 조회 API(/api/result/*) 테스트.

관리자 CRUD(tests.py)와 성격이 달라 파일을 나눴다. 여기서 지키려는 것은 셋이다.
1. 티저는 비로그인으로 열리되 **유형명·별명 이상을 흘리지 않는다** — 깔때기의 전제.
2. 상세는 로그인 + 본인 결과로만 열린다.
3. 초안·중복 같은 데이터 상태에 화면이 무너지지 않는다.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.content.models import Illness, TemType, TemTypeIllness, Weakness
from apps.diagnosis.models import DiagnosisResult


@pytest.fixture
def tem05(db):
    tem = TemType.objects.create(id="TEM05", name="TE-5", nickname="매일 겨울을 사는", body_min=1, body_max=3)
    cold = Weakness.objects.create(id="WEAK-01", name="추위", catchphrase="매일 겨울을 사는 몸")
    tem.weaknesses.add(cold)
    return tem


@pytest.fixture
def customer(db):
    return User.objects.create_user(username="c@example.com", email="c@example.com", password="ollacare1234")


@pytest.mark.django_db
def test_teaser_is_public_and_reveals_only_name_and_nickname(tem05):
    resp = APIClient().get("/api/result/teaser/5/")
    assert resp.status_code == 200

    body = resp.json()
    assert body == {"typeId": "TEM05", "name": "TE-5", "nickname": "매일 겨울을 사는", "found": True}
    # 티저가 상세를 대신하면 '자세히 보기 → 가입' 동선이 무너진다.
    assert "weaknesses" not in body
    assert "illnesses" not in body


@pytest.mark.django_db
def test_teaser_reports_missing_type_without_breaking(db):
    """tem_type 시드가 아직 6개뿐이라(📌) 대부분의 raw가 여기 걸린다."""
    resp = APIClient().get("/api/result/teaser/42/")
    assert resp.status_code == 200
    assert resp.json() == {"typeId": "TEM42", "found": False}


@pytest.mark.django_db
def test_teaser_rejects_out_of_range_raw(db):
    assert APIClient().get("/api/result/teaser/99/").status_code == 400


@pytest.mark.django_db
def test_teaser_hides_unpublished_type(tem05):
    tem05.status = "초안"
    tem05.save()
    assert APIClient().get("/api/result/teaser/5/").json()["found"] is False


@pytest.mark.django_db
def test_my_result_requires_login(tem05):
    assert APIClient().get("/api/result/me/").status_code in (401, 403)


@pytest.mark.django_db
def test_my_result_returns_nothing_before_diagnosis(customer):
    client = APIClient()
    client.force_authenticate(customer)
    assert client.get("/api/result/me/").json() == {"hasResult": False}


@pytest.mark.django_db
def test_my_result_uses_latest_diagnosis(customer, tem05):
    TemType.objects.create(id="TEM01", name="TE-1")
    DiagnosisResult.objects.create(user=customer, raw_value=1, type_id="TEM01")
    DiagnosisResult.objects.create(user=customer, raw_value=5, type_id="TEM05")

    client = APIClient()
    client.force_authenticate(customer)
    body = client.get("/api/result/me/").json()

    assert body["typeId"] == "TEM05"
    assert [w["name"] for w in body["weaknesses"]] == ["추위"]
    # 체형은 0~4 인덱스다. 0~100 값이 아니다(docs/06_decisions.md #19).
    assert body["body"] == {"min": 1, "max": 3, "desc": ""}


@pytest.mark.django_db
def test_my_result_collapses_duplicate_illness_links(customer, tem05):
    """같은 질환이 두 번 연결돼 있어도 고객에게는 한 번만 보여야 한다.

    로컬 DB에 실제로 생기는 상태다 — 관리자의 '통째로 교체'와 seed_demo가 겹치면
    sort만 다른 쌍둥이 행이 남는다(docs/06_decisions.md #21).
    """
    illness = Illness.objects.create(id="ILL-01", name="소화기질환", description="설명")
    TemTypeIllness.objects.create(tem_type=tem05, illness=illness, pct=30, sort=0)
    TemTypeIllness.objects.create(tem_type=tem05, illness=illness, pct=30, sort=1)
    DiagnosisResult.objects.create(user=customer, raw_value=5, type_id="TEM05")

    client = APIClient()
    client.force_authenticate(customer)
    illnesses = client.get("/api/result/me/").json()["illnesses"]

    assert [i["id"] for i in illnesses] == ["ILL-01"]


@pytest.mark.django_db
def test_my_result_hides_unpublished_illness(customer, tem05):
    published = Illness.objects.create(id="ILL-01", name="소화기질환")
    draft = Illness.objects.create(id="ILL-02", name="미공개질환", status="초안")
    TemTypeIllness.objects.create(tem_type=tem05, illness=published, pct=30, sort=0)
    TemTypeIllness.objects.create(tem_type=tem05, illness=draft, pct=10, sort=1)
    DiagnosisResult.objects.create(user=customer, raw_value=5, type_id="TEM05")

    client = APIClient()
    client.force_authenticate(customer)
    assert [i["id"] for i in client.get("/api/result/me/").json()["illnesses"]] == ["ILL-01"]


@pytest.mark.django_db
def test_my_result_does_not_leak_other_users_result(customer, tem05):
    other = User.objects.create_user(username="o@example.com", email="o@example.com", password="ollacare1234")
    DiagnosisResult.objects.create(user=other, raw_value=5, type_id="TEM05")

    client = APIClient()
    client.force_authenticate(customer)
    assert client.get("/api/result/me/").json() == {"hasResult": False}
