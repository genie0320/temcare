from django.urls import path

from . import views

urlpatterns = [
    path("run/", views.run_diagnosis, name="diagnosis-run"),
    path("save/", views.save_diagnosis, name="diagnosis-save"),
]
