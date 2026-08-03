from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .mapping import raw_to_type_id
from .models import DiagnosisResult, DiagnosisStat
from .providers import DiagnosisFailedError, DiagnosisTimeoutError, get_provider


def _record_stat(raw_value: int) -> None:
    """익명 집계 +1. docs/06_decisions.md #14 — 식별자를 절대 넣지 않는다.

    type_id는 mapping.raw_to_type_id로 실제 체질 id('TEM07')를 쓴다. 매핑 규칙이
    한 곳에만 있어야 통계와 화면이 같은 체질을 가리킨다.
    DiagnosisStat은 AuditedModel이 아니라 순수 통계라 update()를 써도 감사로그에
    구멍이 생기지 않는다(오히려 F() 표현식으로 동시성 안전하게 +1 하는 게 맞다).
    """
    type_id = raw_to_type_id(raw_value) or str(raw_value)
    stat, _ = DiagnosisStat.objects.get_or_create(type_id=type_id, day=timezone.localdate())
    DiagnosisStat.objects.filter(pk=stat.pk).update(count=F("count") + 1)  # audit: intentional (DiagnosisStat은 AuditedModel 아님)


@api_view(["POST"])
@permission_classes([AllowAny])
def run_diagnosis(request):
    """의도적 예외: 비로그인 상태로 호출 가능. docs/08_tech_stack.md §5.

    문진(sc_009) 직후 결과 대기(sc_009a)에서 호출한다. 응답은 클라이언트에만 보관되고
    여기서는 diagnosis_result를 만들지 않는다(§6) — save_diagnosis가 그 역할이다.
    개발/시연용으로 delay_seconds·force_fail·force_timeout을 body로 강제할 수 있다.
    """
    answers = request.data.get("answers", [])
    provider = get_provider(
        delay_seconds=float(request.data.get("delay_seconds", 0) or 0),
        force_fail=bool(request.data.get("force_fail", False)),
        force_timeout=bool(request.data.get("force_timeout", False)),
    )
    try:
        raw = provider.submit(answers)
    except DiagnosisTimeoutError:
        return Response({"status": "타임아웃"}, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except DiagnosisFailedError:
        return Response({"status": "실패"}, status=status.HTTP_502_BAD_GATEWAY)

    _record_stat(raw)
    return Response({"raw": raw, "status": "완료"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_diagnosis(request):
    """로그인+약관동의 완료 직후(sc_004b 진입 시) 클라이언트가 들고 있던 결과를 저장한다."""
    raw = request.data.get("raw")
    if raw is None:
        return Response({"detail": "raw 값이 필요하다"}, status=status.HTTP_400_BAD_REQUEST)

    result = DiagnosisResult.objects.create(
        user=request.user,
        raw_value=raw,
        type_id=raw_to_type_id(raw),
        provider=request.data.get("provider", "mock"),
        status="완료",
    )
    return Response(
        {"id": result.pk, "raw_value": result.raw_value, "type_id": result.type_id},
        status=status.HTTP_201_CREATED,
    )
