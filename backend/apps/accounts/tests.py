from unittest import mock

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import AdminLoginLog, AdminProfile, AdminRole, User


def _make_admin_user():
    role, _ = AdminRole.objects.get_or_create(id="super", defaults={"name": "슈퍼관리자", "sort": 0})
    user = User.objects.create_user(username="admin@test.local", email="admin@test.local", password="pass1234!")
    AdminProfile.objects.create(user=user, role=role)
    return user


@pytest.mark.django_db
def test_me_returns_not_authenticated_for_anonymous():
    resp = APIClient().get("/api/accounts/me/")
    assert resp.status_code == 200
    assert resp.json() == {"authenticated": False}


@pytest.mark.django_db
def test_login_succeeds_with_correct_password_and_sets_session():
    _make_admin_user()
    client = APIClient()

    resp = client.post("/api/accounts/login/", {"email": "admin@test.local", "password": "pass1234!"}, format="json")

    assert resp.status_code == 200
    assert resp.json()["authenticated"] is True
    assert client.get("/api/accounts/me/").json()["authenticated"] is True
    assert AdminLoginLog.objects.filter(email="admin@test.local", success=True).exists()


@pytest.mark.django_db
def test_login_fails_with_wrong_password_and_logs_attempt():
    _make_admin_user()
    resp = APIClient().post(
        "/api/accounts/login/", {"email": "admin@test.local", "password": "wrong"}, format="json"
    )

    assert resp.status_code == 401
    assert AdminLoginLog.objects.filter(email="admin@test.local", success=False).exists()


@pytest.mark.django_db
def test_login_rejects_customer_without_admin_profile():
    User.objects.create_user(username="customer@test.local", email="customer@test.local", password="pass1234!")

    resp = APIClient().post(
        "/api/accounts/login/", {"email": "customer@test.local", "password": "pass1234!"}, format="json"
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_dev_login_works_when_debug_true():
    _make_admin_user_named("admin@ollacare.local")

    with mock.patch("django.conf.settings.DEBUG", True):
        resp = APIClient().post("/api/accounts/dev-login/")

    assert resp.status_code == 200
    assert resp.json()["authenticated"] is True


@pytest.mark.django_db
def test_dev_login_blocked_when_debug_false():
    _make_admin_user_named("admin@ollacare.local")

    with mock.patch("django.conf.settings.DEBUG", False):
        resp = APIClient().post("/api/accounts/dev-login/")

    assert resp.status_code == 404


def _make_admin_user_named(username):
    role, _ = AdminRole.objects.get_or_create(id="super", defaults={"name": "슈퍼관리자", "sort": 0})
    user = User.objects.create_user(username=username, email=username)
    AdminProfile.objects.create(user=user, role=role)
    return user
