# backend/social/signals.py em 2025-12-14 11:48

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FamilyRecipe
from .tasks import analyze_recipe_risk_task

@receiver(post_save, sender=FamilyRecipe)
def trigger_recipe_analysis(sender, instance, created, **kwargs):
    """
    Sempre que uma receita é salva:
    1. Se for nova (created), dispara análise.
    2. Se foi editada e está em DRAFT ou PENDING, dispara novamente (pois ingredientes podem ter mudado).
    """
    if created or instance.status in [FamilyRecipe.Status.DRAFT, FamilyRecipe.Status.PENDING_REVIEW]:
        # Usa on_commit para garantir que a transação do banco terminou antes do Celery tentar ler
        from django.db import transaction
        transaction.on_commit(lambda: analyze_recipe_risk_task.delay(instance.id))
