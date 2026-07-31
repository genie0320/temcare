from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.csrf, name="accounts-csrf"),
    path("me/", views.me, name="accounts-me"),
    path("login/", views.login, name="accounts-login"),
    path("dev-login/", views.dev_login, name="accounts-dev-login"),
    path("logout/", views.logout, name="accounts-logout"),
]
