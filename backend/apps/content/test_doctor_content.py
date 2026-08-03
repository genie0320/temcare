"""원장 콘텐츠 입력 테스트. docs/10_content_import.md

지키는 것은 셋이다 — 셋 다 **틀리면 조용히 틀리는** 자리다.

1. 시드 id 어긋남(§5). TEM05에 들어 있는 내용이 사실 TEM18이다. 그냥 두면 실데이터가
   두 유형에 뒤섞이는데, 화면상으로는 아무 오류도 나지 않는다.
2. 약점 태그 없는 카드(§7). 저장은 되고 고객 화면에만 안 나온다 — 관리자는 넣었다고
   믿는다.
3. `make setup` 재실행이 원장 콘텐츠를 프로토타입 시드로 되돌리는 것. 콘텐츠가 조용히
   사라지고, 되돌아간 쪽도 그럴듯해서 눈치채기 어렵다.
"""

import json
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.management.commands import seed_demo
from apps.audit.models import AuditLog
from apps.content.id_repair import repair_tem_type_ids
from apps.content.management.commands.import_doctor_content import DATA_DIR
from apps.content.models import (
    Nutrient,
    NutrientCard,
    TemType,
    TemTypeCuration,
    TemTypeIllness,
    TemTypeWeakness,
    Weakness,
)
from apps.diagnosis.models import DiagnosisResult, DiagnosisStat

pytestmark = pytest.mark.django_db


def _weaknesses():
    for wid, name in [("WEAK-01", "추위"), ("WEAK-02", "소화불량"), ("WEAK-03", "변비")]:
        Weakness.objects.get_or_create(id=wid, defaults={"name": name})


def _legacy_tem05():
    """프로토타입 시드가 만들어 놓는 상태 — 내용은 TEM18인데 id가 TEM05다."""
    _weaknesses()
    tem = TemType.objects.create(
        id="TEM05",
        name="TE-5",
        nickname="매일 겨울을 사는, 고구마 백개 먹은 위장에, 똥 막힌 하수도",
        body_min=1,
        body_max=3,
        body_desc="마른 체형이라도 복부비만인 편이 많아요.",
    )
    for wid in ["WEAK-01", "WEAK-02", "WEAK-03"]:
        TemTypeWeakness.objects.create(tem_type=tem, weakness_id=wid)
    TemTypeCuration.objects.create(tem_type=tem, kind="food", ref_id="FOOD-04", polarity="권장", sort=1)
    return tem


# ── ① 시드 id 어긋남 ─────────────────────────────────────────────
def test_시드_id를_교정하면_내용과_자식이_통째로_TEM18로_옮겨간다():
    _legacy_tem05()

    repair_tem_type_ids()

    assert not TemType.objects.filter(pk="TEM05").exists()
    moved = TemType.objects.get(pk="TEM18")
    assert moved.nickname.startswith("매일 겨울을 사는")
    assert moved.body_min == 1 and moved.body_max == 3
    assert set(moved.weaknesses.values_list("id", flat=True)) == {"WEAK-01", "WEAK-02", "WEAK-03"}
    assert [c.ref_id for c in moved.curations.all()] == ["FOOD-04"]
    # 옛 id에 자식이 남아 있으면 다음 유형을 넣을 때 다시 섞인다.
    assert TemTypeWeakness.objects.filter(tem_type_id="TEM05").count() == 0
    assert TemTypeCuration.objects.filter(tem_type_id="TEM05").count() == 0


def test_이미_나간_판별결과도_새_id를_따라간다(django_user_model):
    """안 옮기면 그 회원의 결과 화면이 통째로 '콘텐츠가 없어요'가 된다."""
    _legacy_tem05()
    user = django_user_model.objects.create_user(username="u@test.local", password="pass1234!")
    DiagnosisResult.objects.create(user=user, type_id="TEM05", raw_value=5)
    DiagnosisStat.objects.create(type_id="TEM05", day="2026-08-03", count=3)

    repair_tem_type_ids()

    assert DiagnosisResult.objects.filter(type_id="TEM05").count() == 0
    assert DiagnosisResult.objects.filter(type_id="TEM18").count() == 1
    assert DiagnosisStat.objects.get(type_id="TEM18", day="2026-08-03").count == 3


def test_통계는_같은_날_행이_이미_있으면_합쳐진다():
    """(type_id, day) 유일 제약이 있다. 그냥 옮기면 IntegrityError로 죽는다."""
    _legacy_tem05()
    DiagnosisStat.objects.create(type_id="TEM05", day="2026-08-03", count=3)
    DiagnosisStat.objects.create(type_id="TEM18", day="2026-08-03", count=2)

    repair_tem_type_ids()

    assert DiagnosisStat.objects.filter(type_id="TEM05").count() == 0
    assert DiagnosisStat.objects.get(type_id="TEM18", day="2026-08-03").count == 5


def test_TEM05와_TEM18이_동시에_있으면_멈춘다():
    """섞이기 직전이다. 어느 쪽이 원장 원본인지 코드가 알 수 없으므로 조용히 지우지 않는다."""
    _legacy_tem05()
    TemType.objects.create(id="TEM18", name="TE 5형")

    with pytest.raises(RuntimeError):
        repair_tem_type_ids()

    assert TemType.objects.filter(pk="TEM05").exists()


def test_교정은_멱등이다():
    _legacy_tem05()
    repair_tem_type_ids()
    assert repair_tem_type_ids() == []
    assert TemType.objects.filter(pk="TEM18").count() == 1


def test_교정_과정이_감사로그에_남는다():
    """콘텐츠가 사라졌다 나타난 것처럼 보이는 변경이라 흔적이 반드시 있어야 한다."""
    _legacy_tem05()
    repair_tem_type_ids()

    logs = AuditLog.objects.filter(target_table="tem_type")
    assert logs.filter(action="create", target_id="TEM18").exists()
    assert logs.filter(action="delete", target_id="TEM05").exists()
    # 자식(약점·큐레이션)은 순수 값 테이블이라 시그널이 없다 — 명시적으로 남겼는가.
    moved = logs.filter(action="update", target_id="TEM18")
    assert any("WEAK-02" in (log.after_json or "") for log in moved)


# ── ② 약점 태그 없는 카드 ────────────────────────────────────────
def test_약점_태그가_없는_카드는_입력이_거부된다(tmp_path):
    """서버가 400으로 막는 규칙과 같은 것을 커맨드에도 건다.

    이게 없으면 '화면으로는 만들 수 없는 카드'가 스크립트로만 생기고, 그 카드는
    고객 화면에 영원히 안 나온다.
    """
    from apps.content.management.commands.import_doctor_content import _require_weakness_tags

    _weaknesses()
    with pytest.raises(CommandError):
        _require_weakness_tags([{"nutrient": "마그네슘", "weakness_ids": []}])


def test_약점_마스터에_없는_태그도_거부된다():
    from apps.content.management.commands.import_doctor_content import _require_weakness_tags

    _weaknesses()
    with pytest.raises(CommandError):
        _require_weakness_tags([{"nutrient": "마그네슘", "weakness_ids": ["WEAK-99"]}])


# ── ③ 실제 입력 한 벌 (TEM18 영양요법) ───────────────────────────
def test_TEM18_영양요법이_카드와_큐레이션으로_들어간다():
    _legacy_tem05()

    call_command("import_doctor_content", "TEM18", verbosity=0)

    spec = json.loads((DATA_DIR / "TEM18.json").read_text(encoding="utf-8"))
    tem = TemType.objects.get(pk="TEM18")
    assert tem.name == spec["tem_type"]["name"]

    # 카드 = (영양소 × 관점). 원장 문장이 그대로 들어갔는가.
    for item in spec["nutrition"]:
        nutrient = Nutrient.objects.get(name=item["nutrient"])
        card = nutrient.cards.get(perspective=item["perspective"])
        assert card.description == item["description"]
        assert set(card.weaknesses.values_list("id", flat=True)) == set(item["weakness_ids"])

    # 조립 — 원장이 쓴 순서가 노출 순서다.
    curated = [c.ref_id for c in tem.curations.filter(kind="nutrient").order_by("sort")]
    assert len(curated) == len(spec["nutrition"])
    assert [NutrientCard.objects.get(pk=int(r)).nutrient.name for r in curated] == [
        i["nutrient"] for i in spec["nutrition"]
    ]


def test_다시_돌려도_카드가_불어나지_않는다():
    _legacy_tem05()
    call_command("import_doctor_content", "TEM18", verbosity=0)
    before = NutrientCard.objects.count()

    call_command("import_doctor_content", "TEM18", verbosity=0)

    assert NutrientCard.objects.count() == before
    assert TemTypeCuration.objects.filter(tem_type_id="TEM18", kind="nutrient").count() == before


def test_입력이_감사로그를_남긴다():
    _legacy_tem05()
    call_command("import_doctor_content", "TEM18", verbosity=0)

    logs = AuditLog.objects.filter(actor_id="import_doctor_content", target_table="nutrient_card")
    assert logs.filter(action="create").count() == 8


# ── ④ 재시드가 원장 콘텐츠를 되돌리지 않는다 ─────────────────────
_HAS_PROTOTYPE = (Path(settings.BASE_DIR).parent / "prototype" / "ollacare.sqlite").exists()
_needs_prototype = pytest.mark.skipif(not _HAS_PROTOTYPE, reason="prototype/ollacare.sqlite 없음")


def _seed():
    """`make setup`의 콘텐츠 시드 부분만 조용히 돌린다."""

    class _Silent:
        def write(self, *args, **kwargs):
            pass

    class _Style:
        def __getattr__(self, _):
            return lambda text: text

    seed_demo._seed_content(_Silent(), _Style())


@_needs_prototype
def test_시드는_애초에_잘못된_id로_넣지_않는다():
    _seed()

    assert not TemType.objects.filter(pk="TEM05").exists()
    assert TemType.objects.filter(pk="TEM18").exists()
    assert set(TemType.objects.get(pk="TEM18").weaknesses.values_list("id", flat=True)) == {
        "WEAK-01",
        "WEAK-02",
        "WEAK-03",
    }
    assert TemTypeIllness.objects.filter(tem_type_id="TEM05").count() == 0
    assert TemTypeCuration.objects.filter(tem_type_id="TEM05").count() == 0


@_needs_prototype
def test_시드는_이미_잘못_들어간_DB도_고친다():
    """이미 시드가 돌아간 다른 컴퓨터의 DB가 이 경우다. `make setup` 한 번으로 낫는다."""
    _legacy_tem05()

    _seed()

    assert not TemType.objects.filter(pk="TEM05").exists(), "잘못된 id가 남아 두 유형이 섞인다"
    assert TemType.objects.get(pk="TEM18").nickname.startswith("매일 겨울을 사는")


@_needs_prototype
def test_재시드가_원장_콘텐츠를_프로토타입_시드로_되돌리지_않는다():
    """`make setup`을 다시 돌리는 것은 흔한 일이다. 그때 원장 콘텐츠가 사라지면 안 된다.

    ★ 시드를 먼저 돌린 뒤에 입력한다 — 실제 순서가 그렇고, 그래야 원장 카드의 pk가
      프로토타입 카드 pk(1~7)와 겹치지 않는다. 겹치면 시드가 큐레이션을 덧붙여도
      '이미 있는 것'으로 보여 이 테스트가 아무것도 못 잡는다(실제로 그랬다).
    """
    _seed()
    call_command("import_doctor_content", "TEM18", verbosity=0)
    name_before = TemType.objects.get(pk="TEM18").name
    curated_before = [
        c.ref_id
        for c in TemTypeCuration.objects.filter(tem_type_id="TEM18", kind="nutrient").order_by("sort")
    ]
    descriptions_before = dict(NutrientCard.objects.values_list("pk", "description"))

    _seed()

    assert not TemType.objects.filter(pk="TEM05").exists(), "시드가 잘못된 id를 되살렸다"
    assert TemType.objects.get(pk="TEM18").name == name_before, "시드가 원장 유형명을 덮어썼다"
    curated_after = [
        c.ref_id
        for c in TemTypeCuration.objects.filter(tem_type_id="TEM18", kind="nutrient").order_by("sort")
    ]
    assert curated_after == curated_before, "시드가 원장 큐레이션을 덮어썼다"
    assert dict(NutrientCard.objects.values_list("pk", "description")) == descriptions_before, (
        "시드가 원장 문장을 프로토타입 문장으로 덮어썼다"
    )
