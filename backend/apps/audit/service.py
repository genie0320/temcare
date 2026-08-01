from . import context
from .models import AccessLog, AuditLog
from .serialize import to_json


def record(action: str, target_table: str, target_id, before: dict | None = None, after: dict | None = None) -> None:
    """배치 처리 등 시그널이 뜨지 않는 경로에서 명시적으로 감사 기록을 남길 때 쓴다.

    QuerySet.update()/delete(), bulk_create()/bulk_update(), raw SQL을 정말 써야만
    하는 경우 이 함수를 대신 호출한다. docs/02_architecture_constraints.md §1.
    """
    AuditLog.objects.create(
        actor_id=context.get_actor_id(),
        actor_type=context.get_actor_type(),
        ip=context.get_ip(),
        action=action,
        target_table=target_table,
        target_id=str(target_id) if target_id is not None else None,
        before_json=to_json(before),
        after_json=to_json(after),
    )


def record_denied(resource: str, action: str, path: str = "") -> None:
    """권한 밖 접근 시도를 남긴다. docs/02_architecture_constraints.md §2 체크리스트.

    데이터가 바뀌지 않았어도 '누가 무엇을 시도했는가'는 보안 사건이다. 익명 요청까지
    남기면 로그가 스캐너 트래픽으로 덮이므로, **로그인한 운영자가 자기 역할 밖을
    시도한 경우**(내부자 위험)만 기록한다 — permissions.py에서 그렇게 호출한다.
    """
    record(
        action="deny",
        target_table=resource,
        target_id=None,
        before=None,
        after={"attempted_action": action, "path": path},
    )


def record_relation_change(instance, relation_label: str, before_ids, after_ids) -> None:
    """관계(약점 태그·큐레이션 등) 변경을 부모 레코드의 감사 기록으로 남긴다.

    연결 테이블은 순수 through 모델이라 AuditedModel이 아니다. 부모 save() 시그널은
    뜨지만 부모 필드는 그대로여서 before/after가 동일하게 찍힌다 — 즉 '무엇이 바뀌었는지'가
    감사로그에서 사라진다. 그 구멍을 메우려고 여기서 diff를 명시적으로 남긴다.
    docs/02_architecture_constraints.md §1.
    """
    record(
        action="update",
        target_table=instance._meta.db_table,
        target_id=instance.pk,
        before={relation_label: sorted(before_ids)},
        after={relation_label: sorted(after_ids)},
    )


def record_access(target_user, fields: str, purpose: str) -> None:
    """회원 개인정보(건강정보 포함) 열람 시 호출한다. purpose(열람 사유)는 필수.

    시그널로 안 잡히므로(단순 조회는 모델을 안 건드림) 조회 뷰에서 명시적으로 호출해야 한다.
    """
    if not purpose:
        raise ValueError("access_log purpose는 필수다 — 열람 사유 없이 개인정보를 열람할 수 없다.")
    AccessLog.objects.create(
        actor_id=context.get_actor_id() or "unknown",
        ip=context.get_ip(),
        target_user=str(target_user),
        fields=fields,
        purpose=purpose,
    )
