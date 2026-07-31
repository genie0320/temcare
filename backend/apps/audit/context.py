"""요청의 actor/ip를 어디서든 꺼내 쓸 수 있게 하는 컨텍스트.

리포지토리(모델 signal)가 actor를 인자로 받게 하면 또 빠뜨린다
(docs/02_architecture_constraints.md §1) — 그래서 미들웨어가 요청 시작 시
여기에 심어두고, signals.py가 인자 없이 꺼내 쓴다. contextvars는 스레드/async
양쪽에서 안전하다.
"""

from contextvars import ContextVar

_actor_id: ContextVar[str | None] = ContextVar("audit_actor_id", default=None)
_actor_type: ContextVar[str] = ContextVar("audit_actor_type", default="system")
_ip: ContextVar[str | None] = ContextVar("audit_ip", default=None)


def set_context(actor_id: str | None, actor_type: str, ip: str | None) -> None:
    _actor_id.set(actor_id)
    _actor_type.set(actor_type)
    _ip.set(ip)


def get_actor_id() -> str | None:
    return _actor_id.get()


def get_actor_type() -> str:
    return _actor_type.get()


def get_ip() -> str | None:
    return _ip.get()
