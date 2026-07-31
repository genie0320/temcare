import json

import pytest

from apps.accounts.models import User
from apps.audit.models import AuditLog


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
