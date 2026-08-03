from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("clinics", views.ClinicViewSet, basename="clinic")

urlpatterns = router.urls
