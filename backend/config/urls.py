from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """체크포인트 1 확인용 — 배포·로컬 어디서든 살아있는지만 본다."""
    return Response({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/diagnosis/", include("apps.diagnosis.urls")),
    # 관리자 인증. 고객과 경로를 나눈 이유는 apps/accounts/customer_views.py 상단 참고.
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/auth/", include("apps.accounts.customer_urls")),
    path("api/consent/", include("apps.consent.urls")),
    # 감사로그·접속기록 조회(adm_028). 조회 전용이고 Super Admin만 — apps/audit/views.py 참고.
    path("api/audit/", include("apps.audit.urls")),
    # 콘텐츠 마스터 CRUD는 관리자 전용. 고객이 읽는 결과는 /api/result/*로 분리했다.
    path("api/content/", include("apps.content.urls")),
    path("api/result/", include("apps.content.customer_urls")),
    # 협력 한의원(깔때기 출구). 관리자 CRUD와 고객 조회를 같은 이유로 나눈다.
    path("api/", include("apps.clinic.urls")),
    path("api/partner-clinics/", include("apps.clinic.customer_urls")),
]

if settings.DEBUG:
    # 로컬 개발 전용. 배포(§10-1)에서는 nginx가 MEDIA_URL을 직접 서빙한다.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
