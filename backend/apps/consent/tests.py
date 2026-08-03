"""고객 가입 + 동의 기록 (sc_091 · sc_092). docs/07_milestones.md M2.

여기서 지키려는 것은 두 가지다.
1. 필수 동의 없이는 계정이 만들어지지 않는다 — 반쪽 상태가 생기면 안 된다.
2. 민감정보(건강정보) 동의는 일반 개인정보 동의와 **별도 항목**으로 남는다(개인정보보호법 제23조).
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.consent.models import ConsentItem, TermsDocument, TermsVersion, UserConsent

ALL_REQUIRED = ["tos", "privacy", "sensitive", "age14"]


@pytest.fixture
def consent_items(db):
    doc = TermsDocument.objects.create(id="privacy", name="개인정보처리방침", sort=0)
    TermsVersion.objects.create(
        document=doc, version="v0.1", body="[미작성]", effective_at="2026-01-01", status="게시"
    )
    specs = [
        ("tos", "이용약관 동의", True, False, None),
        ("privacy", "개인정보 수집·이용 동의", True, False, doc),
        ("sensitive", "민감정보(건강정보) 수집·이용 동의", True, True, doc),
        ("age14", "만 14세 이상입니다", True, False, None),
        ("mkt", "마케팅 정보 수신 동의", False, False, None),
    ]
    for idx, (item_id, name, required, sensitive, document) in enumerate(specs):
        ConsentItem.objects.create(
            id=item_id, name=name, required=required, is_sensitive=sensitive, document=document, sort=idx
        )
    return ConsentItem.objects.all()


@pytest.mark.django_db
def test_consent_items_are_public(consent_items):
    """sc_092는 가입 전 화면이라 비로그인으로 읽을 수 있어야 한다."""
    resp = APIClient().get("/api/consent/items/")
    assert resp.status_code == 200
    items = {row["id"]: row for row in resp.json()}
    assert items["sensitive"]["isSensitive"] is True
    assert items["mkt"]["required"] is False


@pytest.mark.django_db
def test_signup_creates_user_and_consent_history(consent_items):
    resp = APIClient().post(
        "/api/auth/signup/",
        {
            "email": "someone@example.com",
            "password": "ollacare1234",
            "consents": [*ALL_REQUIRED, "mkt"],
            "birthDate": "1990-03-01",
            "gender": "여성",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.json()

    user = User.objects.get(email="someone@example.com")
    assert user.nickname, "닉네임이 비어 있으면 홈 인사말(sc_101)이 깨진다"
    assert user.birth_date.isoformat() == "1990-03-01"
    assert user.gender == "여성"

    # 동의하지 않은 항목도 agreed=False로 남아야 "안 물어봤다"와 "거절했다"가 구분된다.
    consents = {c.item_id: c.agreed for c in UserConsent.objects.filter(user=user)}
    assert consents == {"tos": True, "privacy": True, "sensitive": True, "age14": True, "mkt": True}


@pytest.mark.django_db
def test_signup_records_declined_optional_consent(consent_items):
    APIClient().post(
        "/api/auth/signup/",
        {"email": "b@example.com", "password": "ollacare1234", "consents": ALL_REQUIRED},
        format="json",
    )
    user = User.objects.get(email="b@example.com")
    assert UserConsent.objects.get(user=user, item_id="mkt").agreed is False


@pytest.mark.django_db
def test_signup_rejected_when_sensitive_consent_missing(consent_items):
    """민감정보 동의를 빼면 가입이 통째로 실패해야 한다 — 계정만 남으면 안 된다."""
    resp = APIClient().post(
        "/api/auth/signup/",
        {
            "email": "nope@example.com",
            "password": "ollacare1234",
            "consents": ["tos", "privacy", "age14"],
        },
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "consent_required"
    assert not User.objects.filter(email="nope@example.com").exists()


@pytest.mark.django_db
def test_signup_rejects_short_password(consent_items):
    resp = APIClient().post(
        "/api/auth/signup/",
        {"email": "c@example.com", "password": "1234", "consents": ALL_REQUIRED},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "weak_password"
    assert not User.objects.filter(email="c@example.com").exists()


@pytest.mark.django_db
def test_signup_rejects_duplicate_email(consent_items):
    payload = {"email": "dup@example.com", "password": "ollacare1234", "consents": ALL_REQUIRED}
    assert APIClient().post("/api/auth/signup/", payload, format="json").status_code == 201
    resp = APIClient().post("/api/auth/signup/", payload, format="json")
    assert resp.status_code == 409
    assert resp.json()["code"] == "duplicate_email"
    assert User.objects.filter(email="dup@example.com").count() == 1


@pytest.mark.django_db
def test_login_and_me_roundtrip(consent_items):
    client = APIClient()
    client.post(
        "/api/auth/signup/",
        {"email": "d@example.com", "password": "ollacare1234", "consents": ALL_REQUIRED},
        format="json",
    )
    client.post("/api/auth/logout/")
    assert client.get("/api/auth/me/").json() == {"authenticated": False}

    resp = client.post("/api/auth/login/", {"email": "d@example.com", "password": "ollacare1234"}, format="json")
    assert resp.status_code == 200
    assert client.get("/api/auth/me/").json()["authenticated"] is True


@pytest.mark.django_db
def test_login_does_not_reveal_whether_account_exists(consent_items):
    """계정 열거 방지 — 없는 계정과 비밀번호 오류의 응답이 같아야 한다."""
    missing = APIClient().post(
        "/api/auth/login/", {"email": "ghost@example.com", "password": "ollacare1234"}, format="json"
    )
    APIClient().post(
        "/api/auth/signup/",
        {"email": "e@example.com", "password": "ollacare1234", "consents": ALL_REQUIRED},
        format="json",
    )
    wrong = APIClient().post("/api/auth/login/", {"email": "e@example.com", "password": "wrongpass123"}, format="json")

    assert missing.status_code == wrong.status_code == 401
    assert missing.json() == wrong.json()


@pytest.mark.django_db
def test_nickname_patch_enforces_length(consent_items):
    client = APIClient()
    client.post(
        "/api/auth/signup/",
        {"email": "f@example.com", "password": "ollacare1234", "consents": ALL_REQUIRED},
        format="json",
    )
    assert client.patch("/api/auth/me/", {"nickname": "가"}, format="json").status_code == 400

    resp = client.patch("/api/auth/me/", {"nickname": "느긋한대추"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "느긋한대추"


@pytest.mark.django_db
def test_customer_cannot_use_admin_me_endpoint(consent_items):
    """고객 세션으로 관리자 me를 부르면 비로그인으로 보여야 한다(권한 경계)."""
    client = APIClient()
    client.post(
        "/api/auth/signup/",
        {"email": "g@example.com", "password": "ollacare1234", "consents": ALL_REQUIRED},
        format="json",
    )
    assert client.get("/api/accounts/me/").json() == {"authenticated": False}


@pytest.mark.django_db
def test_signup_is_refused_when_no_consent_items_are_configured(db):
    """★ 동의 항목이 하나도 없으면 가입을 **거부**한다.

    필수 항목 목록이 비면 "빠진 항목"도 없어져서 검사가 통째로 무력화된다.
    개발 중엔 시드가 항목을 넣어주므로 눈치챌 수 없고, 배포에서 시드가 안 돌면
    동의 증빙이 전혀 없는 계정이 생긴다 — 동의는 소급해서 만들 수 없다.
    """
    ConsentItem.objects.all().delete()

    resp = APIClient().post(
        "/api/auth/signup/",
        {"email": "nolock@example.com", "password": "Passw0rd!234", "consents": []},
        format="json",
    )

    assert resp.status_code == 503, resp.content
    assert resp.json()["code"] == "consent_not_configured"
    assert not User.objects.filter(email="nolock@example.com").exists(), "동의 없이 계정이 만들어졌다"
    assert UserConsent.objects.count() == 0
