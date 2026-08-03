"""고객이 동의 화면(sc_092)을 그리는 데 필요한 조회 API.

관리자 CRUD(adm_016/017/038)는 M4다. 여기 있는 건 읽기 전용 두 개뿐이다.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import ConsentItem, TermsVersion


@api_view(["GET"])
@permission_classes([AllowAny])
def consent_items(request):
    """sc_092가 그릴 동의 항목 목록. 비로그인 상태에서 호출된다(가입 전 화면이므로).

    ★ is_sensitive는 화면에서 반드시 별도 체크박스로 그려야 한다는 신호다 —
      일반 개인정보 동의와 묶으면 개인정보보호법 제23조 위반이다.
    """
    items = ConsentItem.objects.filter(status="게시").select_related("document")
    return Response(
        [
            {
                "id": item.id,
                "name": item.name,
                "required": item.required,
                "isSensitive": item.is_sensitive,
                "channel": item.channel,
                "documentId": item.document_id,
                "description": item.description,
                "sort": item.sort,
            }
            for item in items
        ]
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def terms_detail(request, document_id: str):
    """sc_024(이용약관)·sc_025(개인정보처리방침) 전문. '보기'를 눌렀을 때 읽는다.

    시행일이 지난 게시 버전 중 가장 최신을 준다.
    """
    from django.utils import timezone  # noqa: PLC0415 — 이 뷰에서만 필요

    version = (
        TermsVersion.objects.filter(
            document_id=document_id, status="게시", effective_at__lte=timezone.localdate()
        )
        .order_by("-effective_at")
        .first()
    )
    if version is None:
        return Response({"detail": "게시된 약관이 없어요."}, status=404)

    return Response(
        {
            "documentId": version.document_id,
            "documentName": version.document.name,
            "version": version.version,
            "body": version.body,
            "effectiveAt": version.effective_at.isoformat(),
        }
    )
