from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("weaknesses", views.WeaknessViewSet, basename="weakness")
router.register("tem-types", views.TemTypeViewSet, basename="tem-type")

urlpatterns = router.urls + [
    path("tem-type-candidates/nutrient-cards/", views.NutrientCardCandidatesView.as_view(), name="tem-type-nutrient-candidates"),
    path("tem-type-candidates/herb-cards/", views.HerbCardCandidatesView.as_view(), name="tem-type-herb-candidates"),
    path("tem-type-candidates/foods/", views.FoodCandidatesView.as_view(), name="tem-type-food-candidates"),
    path("illness-options/", views.IllnessOptionsView.as_view(), name="illness-options"),
]
