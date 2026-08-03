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

    #: 감사로그에 **값을 남기지 않을** 필드 이름.
    #:
    #: 감사로그는 기본적으로 모델의 모든 칸을 그대로 베껴 담는다. 그런데 이 로그는
    #: 법정 보관기간이 2년이고 운영자가 월 1회 점검으로 열어보는 물건이라, 여기에
    #: 원문이 담기면 **인증정보·개인정보의 두 번째 사본**이 생긴다. 특히
    #: `pii_read`(개인정보 열람) 권한을 콘텐츠 편집 권한과 분리해 둔 의미가
    #: 사라진다 — 감사로그만 볼 수 있으면 이메일·생년월일이 다 보이기 때문이다
    #: (CLAUDE.md §2-1, docs/02_architecture_constraints.md §2).
    #:
    #: 여기 적힌 필드는 값 대신 마스크가 저장된다. 다만 **"바뀌었다"는 사실은
    #: 남는다** — 그게 없으면 감사로그가 감사 기능을 잃는다.
    audit_secret_fields: tuple[str, ...] = ()

    class Meta:
        abstract = True
