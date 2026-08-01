import json

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import AdminPermission, AdminProfile, AdminRole, User
from apps.audit.models import AuditLog
from apps.content.models import Food, Weakness


@pytest.mark.django_db
def test_create_writes_audit_log_with_after_only():
    user = User.objects.create(username="tester", nickname="처음닉네임")

    log = AuditLog.objects.filter(target_table="accounts_user", target_id=str(user.pk)).latest("created_at")

    assert log.action == "create"
    assert log.before_json is None
    after = json.loads(log.after_json)
    assert after["nickname"] == "처음닉네임"


@pytest.mark.django_db
def test_update_writes_audit_log_with_before_and_after():
    user = User.objects.create(username="tester2", nickname="옛날닉네임")

    user.nickname = "새닉네임"
    user.save()

    log = (
        AuditLog.objects.filter(target_table="accounts_user", target_id=str(user.pk), action="update")
        .latest("created_at")
    )

    before = json.loads(log.before_json)
    after = json.loads(log.after_json)
    assert before["nickname"] == "옛날닉네임"
    assert after["nickname"] == "새닉네임"


@pytest.mark.django_db
def test_delete_writes_audit_log():
    user = User.objects.create(username="tester3")
    pk = user.pk
    user.delete()

    log = AuditLog.objects.filter(target_table="accounts_user", target_id=str(pk), action="delete").latest(
        "created_at"
    )
    assert log.after_json is None
    assert json.loads(log.before_json)["username"] == "tester3"


@pytest.mark.django_db
def test_diagnosis_stat_is_not_audited():
    """DiagnosisStat은 AuditedModel이 아니다 — 익명 집계는 감사로그 대상이 아니어야 한다."""
    from apps.diagnosis.models import DiagnosisStat

    before_count = AuditLog.objects.count()
    DiagnosisStat.objects.create(type_id="1", day="2026-07-31", count=1)
    assert AuditLog.objects.count() == before_count


# ── 아래는 실제 HTTP 요청 경로로 확인한다 ─────────────────────────
# 위 테스트들은 모델을 직접 저장해서 actor가 항상 None이다. 그래서 미들웨어가
# 통째로 빠져도 전부 통과했다(2026-08-01 확인). 감사로그에서 '누가'가 비면
# 장부의 의미가 없으므로, 요청 경로로 실제 actor가 찍히는지 여기서 못박는다.
#
# ★ force_authenticate는 Django 미들웨어를 우회하므로 여기서는 쓰지 않는다.
#   반드시 세션 로그인(client.login)으로 실제 요청 흐름을 태운다.


def _admin_client(username="auditadmin", resource="adm_025", actions=("read", "write", "delete")):
    role, _ = AdminRole.objects.get_or_create(id="audit_role", defaults={"name": "감사테스트"})
    for action in actions:
        AdminPermission.objects.get_or_create(
            role=role, resource=resource, action=action, defaults={"allowed": True}
        )
    user = User.objects.create_user(username=username, password="pass1234!", is_staff=True)
    AdminProfile.objects.get_or_create(user=user, defaults={"role": role})

    client = APIClient()
    assert client.login(username=username, password="pass1234!"), "세션 로그인 실패"
    return client, user


@pytest.mark.django_db
def test_audit_records_actor_and_ip_through_real_request():
    """★ 감사로그에 '누가·어디서'가 실제로 찍히는지.

    AuditContextMiddleware가 빠지면 이 테스트가 깨진다 — 그게 이 테스트의 목적이다.
    docs/02_architecture_constraints.md §1.
    """
    client, user = _admin_client()
    Weakness.objects.create(id="WEAK-01", name="추위")
    AuditLog.objects.all().delete()

    resp = client.post(
        "/api/content/foods/",
        {"polarity": "권장", "foods": "생강", "weakness_ids": ["WEAK-01"]},
        format="json",
    )
    assert resp.status_code == 201, resp.content

    log = AuditLog.objects.filter(action="create", target_table="food").latest("created_at")
    assert log.actor_id == str(user.pk), "감사로그에 행위자가 안 남았다(미들웨어 확인)"
    assert log.actor_type == "admin"
    assert log.ip, "감사로그에 접속 IP가 안 남았다"


@pytest.mark.django_db
def test_weakness_tag_change_is_visible_in_audit_log():
    """★ 관계(약점 태그)만 바꿔도 '무엇이 바뀌었는지'가 남아야 한다.

    연결 테이블은 순수 through 모델이라 시그널이 없다. 부모 저장 시그널만으로는
    before==after로 찍혀서 태그 변경이 장부에서 사라진다 — 그 구멍을 메운 것을 확인한다.
    """
    client, _ = _admin_client(username="tagadmin")
    Weakness.objects.create(id="WEAK-01", name="추위")
    Weakness.objects.create(id="WEAK-02", name="변비")
    created = client.post(
        "/api/content/foods/",
        {"polarity": "권장", "foods": "생강", "weakness_ids": ["WEAK-01"]},
        format="json",
    ).json()
    AuditLog.objects.all().delete()

    resp = client.patch(
        f"/api/content/foods/{created['id']}/", {"weakness_ids": ["WEAK-02"]}, format="json"
    )
    assert resp.status_code == 200, resp.content

    diffs = [
        (json.loads(log.before_json or "{}"), json.loads(log.after_json or "{}"))
        for log in AuditLog.objects.filter(target_table="food", action="update")
    ]
    assert any(
        before.get("weakness_ids") == ["WEAK-01"] and after.get("weakness_ids") == ["WEAK-02"]
        for before, after in diffs
    ), f"태그 변경이 감사로그에 안 남았다: {diffs}"


@pytest.mark.django_db
def test_illness_percentage_change_is_visible_in_audit_log():
    """발병율(%)은 원장이 손으로 넣는 실데이터다 — 값 변경 이력이 남아야 한다."""
    from apps.content.models import Illness

    client, _ = _admin_client(username="pctadmin", resource="adm_002")
    Weakness.objects.create(id="WEAK-01", name="추위")
    Illness.objects.create(id="ILL-01", name="고혈압")
    created = client.post(
        "/api/content/tem-types/",
        {"name": "TE-1", "weakness_ids": ["WEAK-01"], "illnesses": [{"illness_id": "ILL-01", "pct": 30}]},
        format="json",
    ).json()
    AuditLog.objects.all().delete()

    resp = client.patch(
        f"/api/content/tem-types/{created['id']}/",
        {"illnesses": [{"illness_id": "ILL-01", "pct": 80}]},
        format="json",
    )
    assert resp.status_code == 200, resp.content

    diffs = [
        (json.loads(log.before_json or "{}"), json.loads(log.after_json or "{}"))
        for log in AuditLog.objects.filter(target_table="tem_type", action="update")
    ]
    assert any(
        before.get("illnesses") == [{"illness_id": "ILL-01", "pct": 30}]
        and after.get("illnesses") == [{"illness_id": "ILL-01", "pct": 80}]
        for before, after in diffs
    ), f"발병율 변경이 감사로그에 안 남았다: {diffs}"


@pytest.mark.django_db
def test_denied_access_is_recorded():
    """★ 권한 밖 접근 시도가 감사로그에 남는다. docs/02_architecture_constraints.md §2 체크리스트."""
    client, user = _admin_client(username="rodmin", actions=("read",))  # write 없음
    Food.objects.create(id="FOOD-01", polarity="권장")
    AuditLog.objects.all().delete()

    resp = client.patch("/api/content/foods/FOOD-01/", {"component": "몰래수정"}, format="json")
    assert resp.status_code == 403

    log = AuditLog.objects.get(action="deny")
    assert log.target_table == "adm_025"
    assert log.actor_id == str(user.pk)
    assert json.loads(log.after_json)["attempted_action"] == "write"


@pytest.mark.django_db
def test_anonymous_denied_access_is_not_recorded():
    """익명 요청까지 남기면 스캐너 트래픽으로 장부가 덮인다 — 로그인한 운영자만 남긴다."""
    Food.objects.create(id="FOOD-01", polarity="권장")
    AuditLog.objects.all().delete()

    assert APIClient().get("/api/content/foods/").status_code in (401, 403)
    assert AuditLog.objects.filter(action="deny").count() == 0
