import json
from datetime import date

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.models import AdminPermission, AdminProfile, AdminRole, User
from apps.audit.models import AccessLog, AuditLog
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
    user = User.objects.create(username="tester3", nickname="지워질닉네임")
    pk = user.pk
    user.delete()

    log = AuditLog.objects.filter(target_table="accounts_user", target_id=str(pk), action="delete").latest(
        "created_at"
    )
    assert log.after_json is None
    before = json.loads(log.before_json)
    assert before["nickname"] == "지워질닉네임"
    # username(=이메일)은 개인정보라 삭제 기록에서도 원문이 남지 않는다.
    assert before["username"] == "***"


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


# ── 감사로그에 남으면 안 되는 것 ──────────────────────────────────
#
# 감사로그는 법정 2년 보관이고 운영자가 월 1회 점검으로 열어본다. 여기에 원문이
# 담기면 인증정보·개인정보의 두 번째 사본이 생기고, pii_read 권한 분리가
# 뒷문으로 무력화된다(CLAUDE.md §2-1).


@pytest.mark.django_db
def test_audit_log_never_stores_password():
    """★ 비밀번호 해시가 감사로그에 남으면 안 된다.

    남겨두면 사용자가 비밀번호를 바꿔도 옛 해시가 2년간 로그에 남는다.
    """
    user = User.objects.create_user(username="pw@example.com", email="pw@example.com", password="FirstPass!234")
    user.set_password("SecondPass!234")
    user.save()

    dumps = " ".join(
        (row.before_json or "") + (row.after_json or "")
        for row in AuditLog.objects.filter(target_table="accounts_user")
    )
    assert "pbkdf2" not in dumps, f"비밀번호 해시가 감사로그에 새고 있다: {dumps}"
    assert "FirstPass" not in dumps and "SecondPass" not in dumps


@pytest.mark.django_db
def test_audit_log_masks_personal_data_but_keeps_the_fact_of_change():
    """개인정보는 원문 대신 마스크로 남기되, **바뀌었다는 사실은 남아야** 한다.

    둘 중 하나만 지키면 안 된다 — 원문이 남으면 개인정보가 새고, 변경 사실까지
    지우면 감사로그가 감사 기능을 잃는다.
    """
    user = User.objects.create_user(
        username="pii@example.com", email="pii@example.com", password="x!23456789"
    )
    user.birth_date = date(1988, 4, 11)
    user.gender = "여성"
    user.save()

    AuditLog.objects.all().delete()
    user.birth_date = date(1990, 12, 25)
    user.save()

    log = AuditLog.objects.get(target_table="accounts_user")
    after = json.loads(log.after_json)

    assert "1990" not in log.after_json and "1988" not in (log.before_json or ""), "생년월일 원문이 남았다"
    assert "pii@example.com" not in log.after_json, "이메일 원문이 남았다"
    # 바뀐 칸은 바뀌었다고, 안 바뀐 칸은 조용히.
    assert after["birth_date"] == "***(변경됨)", after["birth_date"]
    assert after["gender"] == "***", after["gender"]
    # 개인정보가 아닌 칸은 그대로 보여야 추적이 된다.
    assert after["status"] == "정상"


@pytest.mark.django_db
def test_audit_log_still_records_content_values_in_full():
    """★ 마스킹이 콘텐츠 마스터까지 번지면 안 된다.

    가릴 대상은 인증정보·개인정보뿐이다. 콘텐츠는 '무엇이 어떻게 바뀌었는가'가
    그대로 보여야 운영자가 되돌릴 수 있다.
    """
    food = Food.objects.create(id="FOOD-09", polarity="권장", component="원래값")
    AuditLog.objects.all().delete()
    food.component = "바뀐값"
    food.save()

    log = AuditLog.objects.get(target_table="food")
    assert json.loads(log.before_json)["component"] == "원래값"
    assert json.loads(log.after_json)["component"] == "바뀐값"


# ── adm_028 감사로그·접속기록 조회 화면 ───────────────────────────
#
# 여기 테스트들은 "동작하는가"가 아니라 "지키는가"를 본다. 아래 셋 중 하나라도
# 지우면 반드시 빨개져야 한다(docs/11_audit_viewer.md §8):
#
#   1. views._AuditReadView.permission_classes
#   2. views.AccessLogListView.required_action = "pii_read"   ← 이번 작업의 핵심
#   3. views._AuditReadView.initial()의 PUBLIC_DEMO 차단

AUDIT_ENDPOINTS = ["/api/audit/summary/", "/api/audit/logs/", "/api/audit/access-logs/"]


def _viewer_client(username, *, actions=("read",), resource="adm_028"):
    """adm_028에 대해 원하는 action만 가진 운영자. 역할은 계정마다 따로 만든다
    (한 테스트 안에서 역할을 공유하면 권한이 서로 새어 검증이 무의미해진다)."""
    role, _ = AdminRole.objects.get_or_create(id=f"r_{username}"[:20], defaults={"name": username})
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
def test_audit_api_requires_adm_028_permission():
    """★ 안전장치 1 — 로그인만으로는 감사로그를 못 본다.

    permission_classes를 지우면 DRF 기본값(IsAuthenticated)이 남아 200이 되고
    이 테스트가 깨진다 — 그게 이 테스트의 목적이다.
    """
    Food.objects.create(id="FOOD-01", polarity="권장")
    log_id = AuditLog.objects.filter(target_table="food").latest("created_at").id

    # 콘텐츠 권한(adm_025)만 있는 에디터. 감사로그 화면 권한은 없다.
    client, _ = _viewer_client("editoronly", actions=("read", "write"), resource="adm_025")

    for url in [*AUDIT_ENDPOINTS, f"/api/audit/logs/{log_id}/"]:
        assert client.get(url).status_code == 403, f"{url}가 권한 없이 열렸다"


@pytest.mark.django_db
def test_anonymous_cannot_read_audit_api():
    client = APIClient()
    for url in AUDIT_ENDPOINTS:
        assert client.get(url).status_code in (401, 403), f"{url}가 비로그인에 열렸다"


@pytest.mark.django_db
def test_access_log_needs_pii_read_not_read():
    """★★ 이번 작업의 핵심 안전장치.

    같은 화면(adm_028)이라도 access_log는 행위를 분리한다. audit_log는 개인정보가
    마스킹돼 있지만 access_log에는 회원 식별자·열람 항목·열람 사유가 **원문 그대로**
    들어 있기 때문이다(CLAUDE.md §2-1).

    AccessLogListView.required_action을 "pii_read"에서 "read"로 바꾸면
    아래 마지막 줄이 200을 받아 깨진다.
    """
    client, _ = _viewer_client("readonlyadm", actions=("read",))

    assert client.get("/api/audit/summary/").status_code == 200
    assert client.get("/api/audit/logs/").status_code == 200
    assert client.get("/api/audit/access-logs/").status_code == 403, (
        "read 권한만으로 개인정보 열람 이력이 열렸다 — pii_read 분리가 무너졌다"
    )


@pytest.mark.django_db
def test_access_log_opens_with_pii_read_and_shows_raw_values():
    """분리가 '아무도 못 본다'가 되면 안 된다 — pii_read가 있으면 원문이 그대로 보여야 한다."""
    AccessLog.objects.create(
        actor_id="9", target_user="42", fields="건강정보", purpose="1:1 문의 답변 확인"
    )
    client, _ = _viewer_client("piiadm", actions=("read", "pii_read"))

    resp = client.get("/api/audit/access-logs/")
    assert resp.status_code == 200, resp.content
    row = resp.json()["results"][0]
    assert row["target_user"] == "42"
    assert row["fields"] == "건강정보"
    assert row["purpose"] == "1:1 문의 답변 확인"


@pytest.mark.django_db
@override_settings(PUBLIC_DEMO=True)
def test_public_demo_blocks_audit_api():
    """★ 안전장치 3 — 터널 시연 중에는 감사로그 API가 아예 없는 것처럼 보여야 한다.

    터널은 고객 앱만 열지만 그 Vite proxy가 /api를 같은 Django로 넘긴다.
    권한이 있는 계정으로도 404여야 한다(권한 검사보다 먼저 막는다).
    """
    client, _ = _viewer_client("demoadm", actions=("read", "pii_read"))
    for url in AUDIT_ENDPOINTS:
        assert client.get(url).status_code == 404, f"{url}가 공개 데모에서 열렸다"


@pytest.mark.django_db
def test_access_log_view_is_recorded_in_audit_log_not_access_log():
    """접속기록을 들여다본 행위는 audit_log에 남고, access_log는 그대로여야 한다.

    docs/11_audit_viewer.md §7 — access_log에 남기면 "내가 접속기록을 봤다"는 기록이
    장부를 채워 정작 봐야 할 회원 개인정보 열람 기록이 묻힌다.
    """
    AccessLog.objects.create(actor_id="9", target_user="42", fields="건강정보", purpose="확인")
    client, user = _viewer_client("piiadm2", actions=("read", "pii_read"))
    access_before = AccessLog.objects.count()
    AuditLog.objects.all().delete()

    assert client.get("/api/audit/access-logs/?target_user=42").status_code == 200

    log = AuditLog.objects.get(action="read")
    assert log.target_table == "access_log"
    assert log.actor_id == str(user.pk), "누가 봤는지가 안 남았다"
    after = json.loads(log.after_json)
    assert after["filters"]["target_user"] == "42"
    assert after["returned"] == 1
    assert AccessLog.objects.count() == access_before, "접속기록 장부가 자기 조회로 채워졌다"


@pytest.mark.django_db
def test_summary_counts_by_table_and_action():
    """★ 사용자가 실제로 보고 싶은 것 — 어느 테이블에 어떤 로그가 얼마나 남고 있나."""
    food = Food.objects.create(id="FOOD-02", polarity="권장")
    food.component = "진저롤"
    food.save()
    client, _ = _viewer_client("sumadm")

    resp = client.get("/api/audit/summary/")
    assert resp.status_code == 200, resp.content
    data = resp.json()

    tables = {row["target_table"]: row for row in data["audit_log"]["by_table"]}
    assert tables["food"]["actions"]["create"] == 1
    assert tables["food"]["actions"]["update"] == 1
    assert tables["food"]["total"] == 2
    assert data["audit_log"]["total"] >= 2
    assert data["audit_log"]["oldest_at"] and data["audit_log"]["latest_at"]
    # access_log는 건수·시각만 — 개인정보가 아니므로 read로 볼 수 있다.
    assert data["access_log"]["total"] == 0
    assert data["access_log"]["oldest_at"] is None


@pytest.mark.django_db
def test_summary_states_purge_is_not_implemented_instead_of_promising_retention():
    """로그를 파기하는 코드가 아직 어디에도 없다. "2년 보관" 같은 정책 문구를 화면에
    박으면 **지키지 않는 약속**이 된다 — 지금 상태를 사실대로 알린다.
    docs/11_audit_viewer.md §7.
    """
    client, _ = _viewer_client("purgeadm")
    data = client.get("/api/audit/summary/").json()

    assert data["purge"]["implemented"] is False
    assert "adm_030" in data["purge"]["note"]
    assert "2년" not in json.dumps(data, ensure_ascii=False), (
        "파기 코드가 없는데 보관 기간을 약속하고 있다"
    )


@pytest.mark.django_db
def test_list_truncates_before_after_but_detail_returns_full_text():
    """목록에 전문을 실으면 콘텐츠 본문이 통째로 들어와 응답이 폭발한다(§4-3).

    ★ 자른 사실(truncated)을 같이 보내야 화면이 '원문을 다 봤다'고 착각하지 않는다.
    """
    long_text = "가" * 900
    Food.objects.create(id="FOOD-03", polarity="권장", description=long_text)
    client, _ = _viewer_client("listadm")

    resp = client.get("/api/audit/logs/?target_table=food")
    assert resp.status_code == 200, resp.content
    row = resp.json()["results"][0]
    assert len(row["after_preview"]) == 200
    assert row["truncated"] is True

    detail = client.get(f"/api/audit/logs/{row['id']}/")
    assert detail.status_code == 200, detail.content
    assert long_text in detail.json()["after_json"], "상세에서도 원문이 잘렸다"


@pytest.mark.django_db
def test_log_list_filters_and_paginates():
    Food.objects.create(id="FOOD-04", polarity="권장")
    Weakness.objects.create(id="WEAK-01", name="추위")
    client, _ = _viewer_client("filteradm")

    only_food = client.get("/api/audit/logs/?target_table=food").json()
    assert only_food["count"] == 1
    assert {row["target_table"] for row in only_food["results"]} == {"food"}

    only_create = client.get("/api/audit/logs/?action=create").json()
    assert only_create["count"] >= 2
    assert {row["action"] for row in only_create["results"]} == {"create"}

    # 기간 필터가 실제로 거른다.
    assert client.get("/api/audit/logs/?date_to=2000-01-01").json()["count"] == 0
    assert client.get("/api/audit/logs/?date_from=2000-01-01").json()["count"] >= 2
    assert client.get("/api/audit/logs/?date_from=어제").status_code == 400

    paged = client.get("/api/audit/logs/?page_size=1").json()
    assert len(paged["results"]) == 1
    assert paged["count"] >= 2, "잘라 보내면서 전체 건수를 안 알려주면 '이게 전부'로 읽힌다"


@pytest.mark.django_db
def test_audit_api_has_no_write_path():
    """audit_log는 append-only다(docs/02_architecture_constraints.md §8).
    권한을 다 가진 슈퍼관리자여도 쓰기 경로 자체가 없어야 한다.
    """
    Food.objects.create(id="FOOD-05", polarity="권장")
    log_id = AuditLog.objects.filter(target_table="food").latest("created_at").id
    client, _ = _viewer_client("wradm", actions=("read", "write", "delete", "publish", "pii_read"))

    assert client.post("/api/audit/logs/", {}, format="json").status_code == 405
    assert client.patch(f"/api/audit/logs/{log_id}/", {}, format="json").status_code == 405
    assert client.delete(f"/api/audit/logs/{log_id}/").status_code == 405
    assert client.post("/api/audit/access-logs/", {}, format="json").status_code == 405
