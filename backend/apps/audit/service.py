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
