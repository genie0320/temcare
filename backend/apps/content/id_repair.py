"""시드 id 어긋남 교정. docs/06_decisions.md #38-1, docs/10_content_import.md §5.

`prototype/ollacare.sqlite`가 체질 id를 잘못 붙였다. 로컬 DB의 `TEM05`에 들어 있는
내용(TE 5형 / 추위+소화불량+변비 / '매일 겨울을 사는…')은 원본 시트 기준으로
**`TEM18`**이고, 시트의 진짜 `TEM05`는 'E 4형 / 부종 / 물 먹은 스펀지'다.

★ 실데이터를 id 기준으로 덮어쓰면 두 유형이 뒤섞인다. 그래서 콘텐츠를 넣기 전에
  이미 만들어진 DB를 옮겨 놓는다. 새로 만드는 DB는 seed_demo가 애초에 옳은 id로
  넣으므로(_TEM_TYPE_ID_FIX) 여기 걸리지 않는다.

★ 감사로그 우회 4종(QuerySet 일괄 수정·삭제, bulk_*, 원시 SQL)을 쓰지 않는다
  (CLAUDE.md §5). 인스턴스 단위 create()/save()/delete()만 쓰므로 옮기는 과정이
  그대로 감사로그에 남는다.
  자식 테이블(TemTypeWeakness 등)은 AuditedModel이 아니라 시그널이 뜨지 않으므로
  audit.record()로 따로 남긴다.
"""

from apps.audit import service as audit

# 잘못 붙은 id → 원본 시트 기준의 옳은 id
LEGACY_TEM_TYPE_IDS = {"TEM05": "TEM18"}


def _move_children(old, new) -> None:
    """자식 행을 새 체질로 옮긴다. 순수 값 테이블이라 감사로그를 직접 남긴다."""
    from .models import TemTypeCuration, TemTypeIllness, TemTypeWeakness

    moved: dict[str, list] = {}

    weakness_rows = list(TemTypeWeakness.objects.filter(tem_type=old))
    for row in weakness_rows:
        TemTypeWeakness.objects.get_or_create(tem_type=new, weakness=row.weakness)
        row.delete()
    moved["weakness_ids"] = [row.weakness_id for row in weakness_rows]

    illness_rows = list(TemTypeIllness.objects.filter(tem_type=old))
    for row in illness_rows:
        TemTypeIllness.objects.create(tem_type=new, illness=row.illness, pct=row.pct, sort=row.sort)
        row.delete()
    moved["illnesses"] = [{"illness_id": row.illness_id, "pct": row.pct} for row in illness_rows]

    curation_rows = list(TemTypeCuration.objects.filter(tem_type=old))
    for row in curation_rows:
        TemTypeCuration.objects.create(
            tem_type=new, kind=row.kind, ref_id=row.ref_id, polarity=row.polarity, sort=row.sort
        )
        row.delete()
    moved["curations"] = [{"kind": row.kind, "ref_id": row.ref_id} for row in curation_rows]

    audit.record(
        action="update",
        target_table=new._meta.db_table,
        target_id=new.pk,
        before={"tem_type_id": old.pk},
        after={"tem_type_id": new.pk, **moved},
    )


def _move_diagnosis_rows(old_id: str, new_id: str) -> None:
    """이미 나간 판별 결과·통계도 같이 옮긴다.

    결과가 가리키는 것은 '체질'이지 'id 문자열'이 아니다. 내용이 TEM18로 옮겨갔으므로
    그 결과를 받은 회원의 화면도 TEM18을 가리켜야 한다. 안 옮기면 그 회원들의 결과
    화면이 통째로 "이 체질의 콘텐츠가 아직 없어요"가 된다.
    """
    from apps.diagnosis.models import DiagnosisResult, DiagnosisStat

    for result in DiagnosisResult.objects.filter(type_id=old_id):
        result.type_id = new_id
        result.save()  # AuditedModel — 시그널이 감사로그를 남긴다

    # 통계는 (type_id, day) 유일 제약이 있다. 같은 날 새 id 행이 이미 있으면 합친다.
    for stat in DiagnosisStat.objects.filter(type_id=old_id):
        existing = DiagnosisStat.objects.filter(type_id=new_id, day=stat.day).first()
        if existing is None:
            stat.type_id = new_id
            stat.save()
        else:
            existing.count += stat.count
            existing.save()
            stat.delete()


def repair_tem_type_ids(log=None) -> list[tuple[str, str]]:
    """잘못 붙은 체질 id를 옳은 id로 옮긴다. 멱등 — 이미 옮겼으면 아무것도 하지 않는다."""
    from .models import TemType

    moved: list[tuple[str, str]] = []
    for old_id, new_id in LEGACY_TEM_TYPE_IDS.items():
        old = TemType.objects.filter(pk=old_id).first()
        if old is None:
            continue
        if TemType.objects.filter(pk=new_id).exists():
            # 옳은 id가 이미 있는데 잘못된 id도 남아 있다 = 두 유형이 섞이기 직전이다.
            # 조용히 지우면 무엇이 사라졌는지 알 수 없으므로 멈추고 알린다.
            raise RuntimeError(
                f"{old_id}와 {new_id}가 동시에 있다. 어느 쪽이 원장 원본인지 확인한 뒤 손으로 정리할 것 "
                f"(docs/10_content_import.md §5)."
            )

        new = TemType.objects.create(
            id=new_id,
            name=old.name,
            nickname=old.nickname,
            body_value=old.body_value,
            body_min=old.body_min,
            body_max=old.body_max,
            body_desc=old.body_desc,
            herb_title=old.herb_title,
            herb_desc=old.herb_desc,
            status=old.status,
            sort=old.sort,
            updated_by=old.updated_by,
        )
        _move_children(old, new)
        _move_diagnosis_rows(old_id, new_id)
        old.delete()

        moved.append((old_id, new_id))
        if log is not None:
            log(f"체질 id 교정: {old_id} → {new_id} (docs/06_decisions.md #38)")
    return moved
