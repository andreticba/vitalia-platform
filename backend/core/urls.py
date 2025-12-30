# backend/core/urls.py em 2025-12-14 11:48

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CurrentUserView, PatientViewSet

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')

urlpatterns = [
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
    path('', include(router.urls)),
]