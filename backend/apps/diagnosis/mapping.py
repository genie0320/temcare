"""판별 결과값(raw) → 체질 id 매핑.

판별 API는 1~64 정수 하나를 돌려주고(docs/02_architecture_constraints.md §3),
`tem_type`의 기본키는 'TEM01'~'TEM64'다. 둘을 잇는 규칙을 **한 곳에만** 둔다 —
여기가 흩어지면 통계(diagnosis_stat)와 화면이 서로 다른 체질을 가리키게 된다.

📌 이 규칙은 raw와 id가 같은 번호를 가리킨다는 가정 위에 있다(1 → TEM01).
   준차트 연동 시 다른 규칙이면 이 파일만 고치면 된다.
"""

RAW_MIN = 1
RAW_MAX = 64


def raw_to_type_id(raw: int | None) -> str | None:
    """1 → 'TEM01', 64 → 'TEM64'. 범위를 벗어나면 None."""
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    if not (RAW_MIN <= value <= RAW_MAX):
        return None
    return f"TEM{value:02d}"
