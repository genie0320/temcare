from django.urls import path

from . import views

urlpatterns = [
    path("items/", views.consent_items, name="consent-items"),
    path("terms/<str:document_id>/", views.terms_detail, name="consent-terms-detail"),
]
