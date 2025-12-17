# backend/core/urls.py em 2025-12-14 11:48

from django.urls import path
from .views import CurrentUserView

urlpatterns = [
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
]
