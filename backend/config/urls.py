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
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/content/", include("apps.content.urls")),
]

if settings.DEBUG:
    # 로컬 개발 전용. 배포(§10-1)에서는 nginx가 MEDIA_URL을 직접 서빙한다.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
