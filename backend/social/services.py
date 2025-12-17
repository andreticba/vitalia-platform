# backend/social/services.py em 2025-12-14 11:48

import json
import httpx
import logging
from django.conf import settings
from django.db import transaction
from .models import FamilyRecipe, Allergen

logger = logging.getLogger(__name__)

class RecipeAnalysisService:
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model = f"{settings.OLLAMA_GENERATION_MODEL}"
        
    def analyze_recipe(self, recipe: FamilyRecipe):
        """
        Orquestra a análise da receita:
        1. Recupera alérgenos oficiais.
        2. Envia para o LLM.
        3. Processa o retorno e atualiza o modelo.
        """
        logger.info(f"Iniciando análise de IA para a receita: {recipe.title} (ID: {recipe.id})")
        
        # 1. Contexto Determinístico (A "Verdade" Oficial)
        # Passamos a lista exata para a IA saber o que procurar
        official_allergens = list(Allergen.objects.values_list('name', flat=True))
        
        # 2. Prompt Engineering (Auditor de Segurança)
        prompt = f"""
        Aja como um Nutricionista Clínico e Auditor de Segurança Alimentar Sênior.
        Sua tarefa é analisar uma receita caseira e identificar riscos de saúde e alérgenos.

        ### DADOS DA RECEITA
        Título: {recipe.title}
        Ingredientes: {recipe.ingredients_text}
        Modo de Preparo: {recipe.preparation_method}

        ### LISTA OFICIAL DE ALÉRGENOS (RDC 26/2015)
        {json.dumps(official_allergens, ensure_ascii=False)}

        ### INSTRUÇÕES DE SAÍDA
        Retorne APENAS um JSON válido (sem markdown, sem intro) com a seguinte estrutura:
        {{
            "detected_allergens": ["Nome exato da lista oficial acima"],
            "nutritional_estimates": {{
                "calories_kcal": int,
                "carbs_g": int,
                "protein_g": int,
                "fat_g": int,
                "sodium_mg": int
            }},
            "safety_flags": ["Lista de avisos curtos. Ex: 'Alto teor de sódio', 'Gordura Trans', 'Risco de contaminação cruzada (Aveia)'"],
            "risk_analysis": "Breve parágrafo técnico justificando os riscos."
        }}
        
        Se um ingrediente for ambíguo (ex: 'Shoyu'), infira os alérgenos implícitos (Soja, Trigo).
        """

        try:
            # 3. Chamada ao LLM
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.2} # Baixa temperatura para maior precisão
            }
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.ollama_url, json=payload)
                response.raise_for_status()
                ai_data = response.json().get('response', '{}')
                result = json.loads(ai_data)

            # 4. Persistência dos Resultados
            self._apply_results(recipe, result, official_allergens)
            
            logger.info(f"Análise concluída com sucesso para receita {recipe.id}.")
            return True

        except Exception as e:
            logger.error(f"Erro na análise de IA da receita {recipe.id}: {e}", exc_info=True)
            return False

    def _apply_results(self, recipe: FamilyRecipe, result: dict, official_list: list):
        with transaction.atomic():
            # Atualiza flags e nutrição
            recipe.nutritional_info_snapshot = result.get('nutritional_estimates', {})
            recipe.safety_flags = result.get('safety_flags', [])
            
            # Associa Alérgenos (Many-to-Many)
            detected_names = result.get('detected_allergens', [])
            
            # Filtra apenas os que existem no banco (Segurança Determinística)
            valid_allergens = Allergen.objects.filter(name__in=detected_names)
            recipe.detected_allergens.set(valid_allergens)
            
            # Lógica de Status
            # Se houver safety_flags críticas ou muitos alérgenos, pode ir para FLAGGED
            # Por enquanto, movemos para PENDING_REVIEW para o Humano (Nutri) validar
            if recipe.status == FamilyRecipe.Status.DRAFT:
                recipe.status = FamilyRecipe.Status.PENDING_REVIEW
            
            recipe.save()
