"""고객 인증 어댑터. docs/06_decisions.md #23.

판별 API(apps/diagnosis/providers.py)와 **같은 구조**다. 가입 이후의 코드(동의 기록·
닉네임·결과 저장)가 "이 사람이 어떻게 로그인했는지"를 알면 안 된다.

    AuthProvider (interface)
    ├── EmailAuthProvider    ← 1차. 이메일+비밀번호
    └── KakaoAuthProvider    ← 2차. 비즈앱 전환 후 이것만 추가

1차가 이메일인 이유: 카카오 로그인에서 이메일 같은 개인정보를 받으려면 비즈앱
전환(사업자등록·비즈니스 채널)이 선행돼야 하고 그 일정이 우리 손 밖에 있다.
"""

from abc import ABC, abstractmethod

from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction

from .models import User


class AuthError(Exception):
    """인증·가입 실패. 사용자에게 그대로 보여줄 수 있는 문구를 담는다."""

    def __init__(self, message: str, code: str = "auth_failed"):
        super().__init__(message)
        self.message = message
        self.code = code


class AuthProvider(ABC):
    """provider 이름은 UserSocial.provider와 같은 값을 쓴다(email | kakao | ...)."""

    name: str

    @abstractmethod
    def signup(self, request, credentials: dict) -> User:
        """계정을 만들고 User를 돌려준다. 이미 있으면 AuthError."""
        raise NotImplementedError

    @abstractmethod
    def login(self, request, credentials: dict) -> User:
        """자격증명을 검증하고 User를 돌려준다. 실패하면 AuthError."""
        raise NotImplementedError


class EmailAuthProvider(AuthProvider):
    """1차. 이메일 + 비밀번호.

    AUTH_USER_MODEL이 AbstractUser라 username이 필수다 — 고객은 아이디 개념이 없으므로
    username에 이메일을 그대로 넣는다(관리자 계정도 같은 방식이다).
    """

    name = "email"

    MIN_PASSWORD_LENGTH = 8

    def _validate(self, email: str, password: str) -> None:
        if not email or "@" not in email:
            raise AuthError("이메일 주소를 정확히 입력해주세요.", code="invalid_email")
        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise AuthError(
                f"비밀번호는 {self.MIN_PASSWORD_LENGTH}자 이상이어야 해요.", code="weak_password"
            )

    def signup(self, request, credentials: dict) -> User:
        email = (credentials.get("email") or "").strip().lower()
        password = credentials.get("password") or ""
        self._validate(email, password)

        try:
            with transaction.atomic():
                # create_user가 비밀번호를 해시한다 — 평문 저장 금지(docs/08 §9).
                return User.objects.create_user(username=email, email=email, password=password)
        except IntegrityError as exc:
            raise AuthError("이미 가입된 이메일이에요. 로그인해주세요.", code="duplicate_email") from exc

    def login(self, request, credentials: dict) -> User:
        email = (credentials.get("email") or "").strip().lower()
        password = credentials.get("password") or ""
        user = authenticate(request, username=email, password=password)
        if user is None:
            # 존재하지 않는 계정과 비밀번호 오류를 구분해 알려주지 않는다(계정 열거 방지).
            raise AuthError("이메일 또는 비밀번호가 올바르지 않아요.", code="invalid_credentials")
        return user


class KakaoAuthProvider(AuthProvider):
    """2차. 카카오 비즈앱 전환(사업자등록·비즈니스 채널) 후 여기만 채운다.

    결정 #13: JS SDK 팝업이 아니라 **서버 리다이렉트 방식**으로 구현한다 —
    카카오톡 인앱브라우저 유입이 주력 경로가 될 것이기 때문.
    """

    name = "kakao"

    def signup(self, request, credentials: dict) -> User:
        raise NotImplementedError("카카오 로그인은 2차 범위. docs/06_decisions.md #23")

    def login(self, request, credentials: dict) -> User:
        raise NotImplementedError("카카오 로그인은 2차 범위. docs/06_decisions.md #23")


_PROVIDERS: dict[str, type[AuthProvider]] = {
    "email": EmailAuthProvider,
    "kakao": KakaoAuthProvider,
}


def get_auth_provider(name: str = "email") -> AuthProvider:
    provider_cls = _PROVIDERS.get(name)
    if provider_cls is None:
        raise AuthError(f"지원하지 않는 로그인 방식이에요: {name}", code="unknown_provider")
    return provider_cls()
