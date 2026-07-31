from django.db import models


class AuditedModel(models.Model):
    """이 클래스를 상속하면 자동으로 audit_log가 기록된다.

    핸들러마다 logAudit()를 호출하는 구조는 반드시 빠뜨리므로 쓰지 않는다
    (docs/02_architecture_constraints.md §1). 대신 apps/audit/signals.py가
    pre_save/post_save/post_delete를 전역으로 감시하다가, 이 클래스의
    서브클래스일 때만 반응한다 — 모델을 만들 때 상속 한 줄이면 끝이고,
    audit 코드를 어디서도 직접 호출할 필요가 없다.

    ★ QuerySet.update() / QuerySet.delete() / bulk_create() / bulk_update() /
    raw SQL은 이 시그널이 발생하지 않는다. 감사로그에 구멍이 생기므로 금지.
    배치 처리가 필요하면 apps/audit/service.py의 record() 를 명시적으로 쓴다.
    """

    class Meta:
        abstract = True
