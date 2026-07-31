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
