"""고객 인증 경로 — /api/auth/*. 관리자(/api/accounts/*)와 일부러 분리했다.

이유는 customer_views.py 상단 주석 참고: 관리자 me/login은 admin_profile을 요구하는데
고객은 admin_profile이 없는 게 정상이라 같은 엔드포인트를 공유할 수 없다.
"""

from django.urls import path

from . import customer_views

urlpatterns = [
    path("csrf/", customer_views.csrf, name="auth-csrf"),
    path("me/", customer_views.me, name="auth-me"),
    path("signup/", customer_views.signup, name="auth-signup"),
    path("login/", customer_views.login, name="auth-login"),
    path("logout/", customer_views.logout, name="auth-logout"),
    path("nickname-suggestion/", customer_views.nickname_suggestion, name="auth-nickname-suggestion"),
]
