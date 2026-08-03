import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.diagnosis.models import DiagnosisResult, DiagnosisStat


@pytest.mark.django_db
def test_health_check_is_public():
    resp = APIClient().get("/api/health/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.django_db
def test_run_diagnosis_works_without_login():
    """docs/02_architecture_constraints.md §6 — 문진은 로그인 없이 시작한다."""
    resp = APIClient().post("/api/diagnosis/run/", {"answers": []}, format="json")
    assert resp.status_code == 200
    assert 1 <= resp.json()["raw"] <= 64
    # DiagnosisResult는 아직 안 생긴다 — 저장은 로그인 이후(save_diagnosis)에만.
    assert DiagnosisResult.objects.count() == 0
    # 익명 집계만 남는다.
    assert DiagnosisStat.objects.count() == 1


@pytest.mark.django_db
def test_run_diagnosis_can_force_failure_for_retry_ui_testing():
    resp = APIClient().post("/api/diagnosis/run/", {"force_fail": True}, format="json")
    assert resp.status_code == 502

    resp = APIClient().post("/api/diagnosis/run/", {"force_timeout": True}, format="json")
    assert resp.status_code == 504


@pytest.mark.django_db
def test_save_diagnosis_requires_login():
    resp = APIClient().post("/api/diagnosis/save/", {"raw": 7}, format="json")
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_save_diagnosis_persists_result_when_logged_in():
    user = User.objects.create_user(username="member1", password="pass1234!")
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/diagnosis/save/", {"raw": 7, "provider": "mock"}, format="json")

    assert resp.status_code == 201
    result = DiagnosisResult.objects.get(user=user)
    assert result.raw_value == 7


@pytest.mark.django_db
def test_mock_only_offers_types_whose_stations_are_actually_filled():
    """★ mock 판별은 **4정거장이 실제로 채워지는 체질**만 고른다.

    화면이 깨지는 게 아니라 **시연이 안 되는** 상태가 따로 있다. 약점 태그가
    콘텐츠 연결의 축이라, 태그가 있어도 그 태그에 걸린 콘텐츠가 없으면 정거장이
    빈다. 눈에 보이는 오류가 아니라서 테스트가 없으면 아무도 못 알아챈다.

    ★ '태그 개수'로 거르면 안 된다 — 태그 2개짜리가 정거장이 비는 실제 사례가
      있었다(TEM54). 대리 지표가 아니라 실제로 무엇이 끌려오는지를 본다.
    """
    from apps.content.models import Article, Food, Herb, HerbCard, Nutrient, NutrientCard, TemType, Weakness
    from apps.diagnosis.providers import MockDiagnosisProvider

    cold = Weakness.objects.create(id="WEAK-01", name="추위")
    lonely = Weakness.objects.create(id="WEAK-09", name="콘텐츠없는약점")

    # 태그는 있지만 걸린 콘텐츠가 없는 체질 — 정거장이 빈다.
    TemType.objects.create(id="TEM01", name="빈체질", body_min=1, body_max=2).weaknesses.add(lonely)
    # 4정거장이 다 차는 체질.
    TemType.objects.create(id="TEM05", name="찬체질", body_min=1, body_max=2).weaknesses.add(cold)

    NutrientCard.objects.create(nutrient=Nutrient.objects.create(id="NUT-01", name="마그네슘")).weaknesses.add(cold)
    HerbCard.objects.create(herb=Herb.objects.create(id="HRB-01", name="육계")).weaknesses.add(cold)
    Article.objects.create(id="ART-01", kind="생활", title="따뜻하게").weaknesses.add(cold)
    Food.objects.create(id="FOOD-01", polarity="권장", component="단백질").weaknesses.add(cold)
    Food.objects.create(id="FOOD-02", polarity="제한", component="찬음식").weaknesses.add(cold)

    picks = {MockDiagnosisProvider().submit([]) for _ in range(30)}
    assert picks == {5}, f"정거장이 비는 체질이 데모 결과로 나왔다: {picks}"


@pytest.mark.django_db
def test_mock_falls_back_when_no_type_meets_the_demo_bar():
    """기준을 채우는 체질이 하나도 없으면 막히지 않고 기준을 낮춘다.

    깐깐하게 거르다가 후보가 0이 되면 판별 자체가 멈춘다 — 안전장치가 기능을
    잡아먹는 상황이라, 여기서는 닫는 게 아니라 낮추는 쪽이 맞다.
    """
    from apps.content.models import TemType, Weakness
    from apps.diagnosis.providers import MockDiagnosisProvider

    TemType.objects.create(id="TEM07", name="얇은체질", body_min=1, body_max=2).weaknesses.add(
        Weakness.objects.create(id="WEAK-01", name="추위")
    )

    assert MockDiagnosisProvider().submit([]) == 7
