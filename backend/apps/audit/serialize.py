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
    """
    data = {}
    for field in instance._meta.concrete_fields:
        data[field.attname] = _json_safe(getattr(instance, field.attname))
    return data


def to_json(data: dict | None) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False, default=str)
