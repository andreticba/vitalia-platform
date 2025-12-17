# backend/social/tasks.py em 2025-12-14 11:48

from celery import shared_task
from .models import FamilyRecipe
from .services import RecipeAnalysisService
import logging

logger = logging.getLogger(__name__)

@shared_task(
    queue='ai_reasoning', # Fila dedicada para tarefas pesadas de IA
    bind=True, 
    max_retries=3, 
    default_retry_delay=60
)
def analyze_recipe_risk_task(self, recipe_id):
    try:
        recipe = FamilyRecipe.objects.get(id=recipe_id)
        
        # Evita reprocessar receitas já publicadas ou arquivadas para economizar recursos
        if recipe.status in [FamilyRecipe.Status.PUBLISHED, FamilyRecipe.Status.ARCHIVED]:
            logger.info(f"Receita {recipe_id} já processada ou arquivada. Pulando.")
            return

        service = RecipeAnalysisService()
        success = service.analyze_recipe(recipe)
        
        if not success:
            raise Exception("Falha no serviço de análise de receita.")

    except FamilyRecipe.DoesNotExist:
        logger.warning(f"Receita {recipe_id} não encontrada para análise.")
    except Exception as exc:
        logger.error(f"Erro na task de análise de receita {recipe_id}: {exc}")
        raise self.retry(exc=exc)
