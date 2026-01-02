# backend/gamification/apps.py em 2025-12-14 11:48

from django.apps import AppConfig

class GamificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gamification'

    def ready(self):
        import gamification.signals