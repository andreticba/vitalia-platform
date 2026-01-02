# backend/medical/urls.py em 2025-12-14 11:48

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WellnessPlanViewSet, PrescribedActivityViewSet, MyDailyScheduleView

router = DefaultRouter()
router.register(r'plans', WellnessPlanViewSet, basename='wellness-plan')
router.register(r'activities', PrescribedActivityViewSet, basename='activity')
router.register(r'my-day', MyDailyScheduleView, basename='my-day')

urlpatterns = [
    path('', include(router.urls)),
]