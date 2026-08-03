from django.db.models.signals import post_delete, post_save, pre_save

from . import context
from .base import AuditedModel
from .models import AuditLog
from .serialize import model_to_safe_dict, redact_pair, to_json


def _table_name(instance) -> str:
    return instance._meta.db_table


def pre_save_snapshot(sender, instance, raw=False, **kwargs):
    """update 직전의 DB 상태를 instance에 잠깐 얹어둔다(저장은 안 함).

    post_save는 '저장된 이후'의 instance만 받기 때문에, before 값은 여기서
    미리 떠 두는 수밖에 없다. 이게 없으면 audit_log.before_json이 항상 비게 된다.
    """
    if raw or not isinstance(instance, AuditedModel):
        return
    if instance.pk is None:
        instance._audit_before = None
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._audit_before = None
    else:
        instance._audit_before = model_to_safe_dict(old)


def post_save_record(sender, instance, created, raw=False, **kwargs):
    if raw or not isinstance(instance, AuditedModel):
        return
    before = None if created else getattr(instance, "_audit_before", None)
    after = model_to_safe_dict(instance)
    before, after = redact_pair(before, after, instance.audit_secret_fields)
    AuditLog.objects.create(
        actor_id=context.get_actor_id(),
        actor_type=context.get_actor_type(),
        ip=context.get_ip(),
        action="create" if created else "update",
        target_table=_table_name(instance),
        target_id=str(instance.pk),
        before_json=to_json(before),
        after_json=to_json(after),
    )


def post_delete_record(sender, instance, **kwargs):
    if not isinstance(instance, AuditedModel):
        return
    before, _ = redact_pair(model_to_safe_dict(instance), None, instance.audit_secret_fields)
    AuditLog.objects.create(
        actor_id=context.get_actor_id(),
        actor_type=context.get_actor_type(),
        ip=context.get_ip(),
        action="delete",
        target_table=_table_name(instance),
        target_id=str(instance.pk),
        before_json=to_json(before),
        after_json=None,
    )


def connect():
    # sender를 지정하지 않으면 전 모델을 감시한다 — AuditedModel 서브클래스인지는
    # 리시버 안에서 판정한다. 새 모델을 추가할 때 여기 등록하는 걸 잊을 수가 없다.
    pre_save.connect(pre_save_snapshot, dispatch_uid="audit_pre_save_snapshot")
    post_save.connect(post_save_record, dispatch_uid="audit_post_save_record")
    post_delete.connect(post_delete_record, dispatch_uid="audit_post_delete_record")
