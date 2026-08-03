"""고객용 결과 조회 경로 — /api/result/*. 관리자(/api/content/*)와 분리한 이유는
customer_views.py 상단 주석 참고.
"""

from django.urls import path

from . import customer_views

urlpatterns = [
    path("teaser/<int:raw>/", customer_views.result_teaser, name="result-teaser"),
    path("me/", customer_views.my_result, name="result-me"),
    path("prescription/", customer_views.my_prescription, name="result-prescription"),
]
