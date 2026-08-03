"""고객용 협력 한의원 조회 — sc_040. 읽기 전용.

관리자 경로(/api/clinics/)는 adm_040 권한을 요구하므로 고객이 쓸 수 없다.
콘텐츠 쪽과 같은 이유로 경로를 나눈다(apps/content/customer_views.py 상단 참고).

★ **비로그인으로도 열린다.** 여기 담긴 것은 개인정보가 아니라 협력 한의원의
  공개 영업정보이고, 이 화면은 깔때기의 출구라 문턱을 두면 목적에 반한다.
  단 status='게시'인 곳만 내보낸다.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Clinic

PUBLISHED = "게시"


@api_view(["GET"])
@permission_classes([AllowAny])
def clinic_list(request):
    clinics = Clinic.objects.filter(status=PUBLISHED)
    return Response(
        {
            "clinics": [
                {
                    "id": c.pk,
                    "name": c.name,
                    "director": c.director,
                    "region": c.region,
                    "address": c.address,
                    "phone": c.phone,
                    "hours": c.hours,
                    "intro": c.intro,
                    "image": c.image,
                    "mapUrl": c.map_url,
                    "homepage": c.homepage,
                }
                for c in clinics
            ]
        }
    )
