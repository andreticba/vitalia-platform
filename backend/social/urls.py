# backend/social/urls.py em 2025-12-14 11:48

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FamilyRecipeViewSet, ActivityFeedView

router = DefaultRouter()
router.register(r'recipes', FamilyRecipeViewSet, basename='family-recipe')

urlpatterns = [
    path('feed/', ActivityFeedView.as_view(), name='activity-feed'),
    path('', include(router.urls)),
]