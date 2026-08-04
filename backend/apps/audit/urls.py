from django.urls import path

from . import views

# 조회 전용이라 라우터(DefaultRouter)를 쓰지 않는다 — 라우터는 쓰기 경로까지
# 자동으로 열어줄 여지를 남긴다. docs/11_audit_viewer.md §4-1.
urlpatterns = [
    path("summary/", views.AuditSummaryView.as_view(), name="audit-summary"),
    path("logs/", views.AuditLogListView.as_view(), name="audit-log-list"),
    path("logs/<int:pk>/", views.AuditLogDetailView.as_view(), name="audit-log-detail"),
    path("access-logs/", views.AccessLogListView.as_view(), name="access-log-list"),
]
