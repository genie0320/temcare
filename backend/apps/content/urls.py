from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("weaknesses", views.WeaknessViewSet, basename="weakness")
router.register("tem-types", views.TemTypeViewSet, basename="tem-type")
router.register("nutrients", views.NutrientViewSet, basename="nutrient")
router.register("herbs", views.HerbViewSet, basename="herb")
router.register("foods", views.FoodViewSet, basename="food")
router.register("points", views.PointViewSet, basename="point")
router.register("health-signs", views.HealthSignViewSet, basename="health-sign")
router.register("illnesses", views.IllnessViewSet, basename="illness")
router.register("products", views.ProductViewSet, basename="product")
router.register("articles", views.ArticleViewSet, basename="article")
router.register("life-articles", views.LifeArticleViewSet, basename="life-article")

urlpatterns = router.urls + [
    path("tem-type-candidates/nutrient-cards/", views.NutrientCardCandidatesView.as_view(), name="tem-type-nutrient-candidates"),
    path("tem-type-candidates/herb-cards/", views.HerbCardCandidatesView.as_view(), name="tem-type-herb-candidates"),
    path("tem-type-candidates/foods/", views.FoodCandidatesView.as_view(), name="tem-type-food-candidates"),
    path("illness-options/", views.IllnessOptionsView.as_view(), name="illness-options"),
    path("nutrient-perspectives/", views.NutrientPerspectiveOptionsView.as_view(), name="nutrient-perspectives"),
    path("herb-mechanisms/", views.HerbMechanismOptionsView.as_view(), name="herb-mechanisms"),
    path("food-components/", views.FoodComponentOptionsView.as_view(), name="food-components"),
    path("image-upload/", views.ImageUploadView.as_view(), name="image-upload"),
]
