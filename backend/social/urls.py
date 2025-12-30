# backend/social/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FamilyRecipeViewSet

router = DefaultRouter()
router.register(r'recipes', FamilyRecipeViewSet, basename='family-recipe')

urlpatterns = [
    path('', include(router.urls)),
]