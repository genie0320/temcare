"""판별 API 어댑터. docs/02_architecture_constraints.md §3.

결과를 소비하는 코드가 준차트의 존재를 알면 안 된다 — raw 정수와 status만 안다.
어느 프로바이더를 쓸지는 settings.DIAGNOSIS_PROVIDER(app_config['diagnosis.provider'])로 결정한다.
"""

import random
import time
from abc import ABC, abstractmethod


class DiagnosisTimeoutError(Exception):
    pass


class DiagnosisFailedError(Exception):
    pass


class DiagnosisProvider(ABC):
    @abstractmethod
    def submit(self, answers: list) -> int:
        """문진 응답을 넘기고 1~64 사이의 결과값(raw)을 받는다."""
        raise NotImplementedError


class MockDiagnosisProvider(DiagnosisProvider):
    """1차. 임의 1~64 반환 + 인위적 지연/실패/타임아웃 시뮬레이션.

    sc_009a(결과 대기)의 재시도 UI를 실제 외부 연동 없이 검증하기 위한 것이다.
    """

    def __init__(self, *, delay_seconds: float = 0.0, force_fail: bool = False, force_timeout: bool = False):
        self.delay_seconds = delay_seconds
        self.force_fail = force_fail
        self.force_timeout = force_timeout

    def submit(self, answers: list) -> int:
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if self.force_timeout:
            raise DiagnosisTimeoutError("mock: 타임아웃 시뮬레이션")
        if self.force_fail:
            raise DiagnosisFailedError("mock: 실패 시뮬레이션")
        return random.randint(1, 64)  # nosec B311 — 보안용 난수 아님, mock 데모 결과값일 뿐


class JunchartDiagnosisProvider(DiagnosisProvider):
    """2차. 준차트 실연동 시 이것만 추가한다 — 아직 스펙 없음(📌)."""

    def submit(self, answers: list) -> int:
        raise NotImplementedError("준차트 연동은 2차 범위. docs/02_architecture_constraints.md §3")


def get_provider(**kwargs) -> DiagnosisProvider:
    from django.conf import settings

    name = getattr(settings, "DIAGNOSIS_PROVIDER", "mock")
    if name == "mock":
        return MockDiagnosisProvider(**kwargs)
    if name == "junchart":
        return JunchartDiagnosisProvider()
    raise ValueError(f"알 수 없는 DIAGNOSIS_PROVIDER: {name}")
