import datetime
import decimal
import json


def _json_safe(value):
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return str(value)
    return value


def model_to_safe_dict(instance) -> dict:
    """모델 인스턴스의 concrete 필드를 JSON 저장 가능한 dict로 바꾼다.

    FK는 pk만, M2M은 건드리지 않는다(별도 through 모델이 각자 감사된다).

    ★ 여기서는 아직 가리지 않는다. 마스킹은 before/after가 **둘 다 있는 자리**에서
      해야 "바뀌었다"는 사실을 남길 수 있어서, redact_pair()가 맡는다.
    """
    data = {}
    for field in instance._meta.concrete_fields:
        data[field.attname] = _json_safe(getattr(instance, field.attname))
    return data


MASK = "***"
MASK_CHANGED = "***(변경됨)"


def _mask(value):
    """빈 값은 빈 채로 둔다 — '값이 없다가 생겼다'가 보여야 하기 때문."""
    return MASK if value not in (None, "") else value


def redact_pair(before: dict | None, after: dict | None, secret_fields) -> tuple[dict | None, dict | None]:
    """민감 필드의 **원문을 지우되 변경 여부는 남긴다**.

    감사로그의 목적은 "누가 언제 무엇을 바꿨는가"이지 "값이 무엇이었는가"가 아니다.
    그래서 원문 대신 마스크를 넣되, 앞뒤가 다르면 (변경됨)을 붙여 사실만 남긴다.

    ★ 지문(해시 앞자리)을 남기는 방법도 있지만 쓰지 않는다 — 생년월일처럼 경우의
      수가 적은 값은 지문만으로 되맞춰 복원할 수 있어서 가린 의미가 없다.
    """
    if not secret_fields:
        return before, after

    for name in secret_fields:
        old = before.get(name) if before else None
        new = after.get(name) if after else None
        changed = before is not None and after is not None and old != new

        if before is not None and name in before:
            before[name] = _mask(old)
        if after is not None and name in after:
            after[name] = MASK_CHANGED if changed and new not in (None, "") else _mask(new)

    return before, after


def to_json(data: dict | None) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False, default=str)
