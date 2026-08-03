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


def _seeded_raws() -> list[int]:
    """콘텐츠가 실제로 들어 있는 체질의 raw 목록.

    ★ mock 전용 장치다. 실연동(JunchartDiagnosisProvider)은 이런 걸 알지 않는다 —
      판별 결과는 우리 콘텐츠 사정과 무관하게 결정되는 값이다.

    이게 없으면 시연이 성립하지 않는다. `tem_type` 시드가 64개 중 6개뿐이라
    임의 1~64를 그대로 쓰면 **열에 아홉이 "이 체질의 콘텐츠가 아직 없어요"** 로
    끝난다. 화면을 보여주려는 자리에서 이건 치명적이다.
    """
    from apps.content.models import Article, Food, HerbCard, NutrientCard, TemType

    from .mapping import RAW_MAX, RAW_MIN, raw_to_type_id

    # 약점이 하나도 없는 체질(TEM64 무결형)은 제외한다. 처방·건강신호·질환이 전부
    # 약점 태그로 끌려오므로, 약점이 없으면 결과 다음의 모든 화면이 텅 빈다.
    #
    # ★ 그런데 "약점 1개 이상"으로는 부족했다(2026-08-03). 화면은 안 깨지지만
    #   **시연이 안 되는** 상태가 따로 있다. 실측:
    #     TEM48·TEM54 → 정거장 4개 중 2개가 비어 있다(식이·생활 없음)
    #     TEM01       → 4개가 다 차지만 식탁 신호등에 '제한'(빨간불)이 없다
    #     TEM05·TEM46 → 4개가 다 차고 신호등도 양쪽이 있다
    #
    #   ★ 태그 개수로 거르려다 틀렸다. TEM54는 태그가 2개인데도 정거장이 빈다 —
    #     태그 수는 콘텐츠 양의 대리 지표일 뿐이라 맞지 않는다. **실제로 무엇이
    #     끌려오는지**를 봐야 한다.
    #
    #   콘텐츠를 지어내지 않고 이미 있는 것 중에서 고르는 것뿐이다. 실연동
    #   (JunchartDiagnosisProvider)에는 이 장치가 없다 — 판별 결과는 우리 콘텐츠
    #   사정과 무관하게 결정되는 값이기 때문이다.
    def demos_well(tem_type) -> bool:
        weakness_ids = [w.pk for w in tem_type.weaknesses.all() if w.status == "게시"]
        if not weakness_ids:
            return False
        tagged = {"weaknesses__id__in": weakness_ids}
        foods = Food.objects.filter(status="게시", **tagged).distinct()
        return all(
            (
                NutrientCard.objects.filter(**tagged).exists(),
                Article.objects.filter(status="게시", **tagged).exists(),
                HerbCard.objects.filter(**tagged).exists(),
                # 식탁 신호등은 권장·제한이 **둘 다** 있어야 신호등으로 읽힌다.
                foods.filter(polarity="권장").exists(),
                foods.filter(polarity="제한").exists(),
            )
        )

    published = TemType.objects.filter(status="게시").prefetch_related("weaknesses")
    seeded = {t.pk for t in published if demos_well(t)}
    if not seeded:
        # 시연 기준을 채우는 체질이 아직 없는 초기 시드·테스트에서는 기준을 낮춘다.
        seeded = set(
            TemType.objects.filter(status="게시", weaknesses__isnull=False)
            .distinct()
            .values_list("id", flat=True)
        )
    return [raw for raw in range(RAW_MIN, RAW_MAX + 1) if raw_to_type_id(raw) in seeded]


class MockDiagnosisProvider(DiagnosisProvider):
    """1차. 임의 결과값 반환 + 인위적 지연/실패/타임아웃 시뮬레이션.

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
        # 시드가 하나도 없으면(테스트 등) 원래대로 1~64에서 고른다.
        candidates = _seeded_raws() or list(range(1, 65))
        return random.choice(candidates)  # nosec B311 — 보안용 난수 아님, mock 데모 결과값일 뿐


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
