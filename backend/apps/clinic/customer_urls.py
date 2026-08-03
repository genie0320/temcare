"""고객용 협력 한의원 경로 — /api/partner-clinics/.

관리자(/api/clinics/)와 분리한 이유는 customer_views.py 상단 주석 참고.
"""

from django.urls import path

from . import customer_views

urlpatterns = [
    path("", customer_views.clinic_list, name="partner-clinic-list"),
]
