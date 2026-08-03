"""랜덤 조합 한글 닉네임. PPT SIGNUP-02 (docs/06_decisions.md #25).

명세: "랜덤으로 조합되어 입력되는 한글 닉네임 / 4~8글자 / 사용자 변경 가능".
예시로 주어진 형태가 '달콤한홍당무'(수식어+사물)라 그 구조를 따랐다.

닉네임은 표시용일 뿐 식별자가 아니므로 **중복을 허용**한다. 유일성을 강제하면
가입 도중에 "이미 쓰는 닉네임입니다"로 막히는 마찰이 생기는데, 그 대가로 얻는 것이 없다.
"""

import secrets

# 조합 결과가 4~8글자에 들어가도록 각 목록의 글자 수를 맞춰 두었다.
_MODIFIERS = [
    "달콤한",
    "포근한",
    "말갛은",
    "느긋한",
    "산뜻한",
    "다정한",
    "고요한",
    "따뜻한",
    "씩씩한",
    "상냥한",
    "구수한",
    "말쑥한",
]

_NOUNS = [
    "홍당무",
    "도토리",
    "수박씨",
    "감자",
    "대추",
    "미역",
    "복숭아",
    "보리밥",
    "청포도",
    "무화과",
    "옥수수",
    "밤송이",
]

MIN_LENGTH = 4
MAX_LENGTH = 8


def suggest_nickname() -> str:
    """4~8글자 한글 닉네임 하나를 만든다.

    secrets를 쓴 이유는 보안 목적이 아니라 bandit(B311)이 random을 잡기 때문이다.
    """
    for _ in range(10):
        candidate = secrets.choice(_MODIFIERS) + secrets.choice(_NOUNS)
        if MIN_LENGTH <= len(candidate) <= MAX_LENGTH:
            return candidate
    # 목록이 바뀌어 길이 조건을 못 맞추는 경우의 안전망 — 화면이 비지 않게만 한다.
    return "포근한감자"


def validate_nickname(value: str) -> str | None:
    """사용자가 고친 닉네임 검증. 문제가 있으면 사유 문자열을, 없으면 None을 돌려준다."""
    text = (value or "").strip()
    if not text:
        return "닉네임을 입력해주세요."
    if not (MIN_LENGTH <= len(text) <= MAX_LENGTH):
        return f"닉네임은 {MIN_LENGTH}~{MAX_LENGTH}글자로 지어주세요."
    return None
