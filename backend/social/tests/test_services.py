# backend/social/tests/test_services.py em 2025-12-14 11:48

import pytest
import json
from unittest.mock import MagicMock, patch
from social.services import RecipeAnalysisService
from social.models import FamilyRecipe, Allergen
from django.contrib.auth.models import User

@pytest.mark.django_db
class TestRecipeAnalysisService:
    
    @pytest.fixture
    def setup_data(self):
        # 1. Criar Usuário e Receita
        user = User.objects.create(username="chef_maria")
        recipe = FamilyRecipe.objects.create(
            author=user,
            title="Bolo de Amendoim da Vovó",
            ingredients_text="2 xícaras de farinha de trigo, 1 xícara de amendoim, 3 ovos",
            preparation_method="Misture tudo e asse.",
            status=FamilyRecipe.Status.DRAFT
        )
        
        # 2. Criar Alérgenos Oficiais (Simulando o Seed)
        Allergen.objects.create(name="Trigo", severity_level="HIGH")
        Allergen.objects.create(name="Amendoim", severity_level="HIGH")
        Allergen.objects.create(name="Ovos", severity_level="HIGH")
        Allergen.objects.create(name="Leite", severity_level="HIGH") # Controle negativo
        
        return recipe

    @patch("social.services.httpx.Client")
    def test_analyze_recipe_detection_success(self, mock_client_cls, setup_data):
        """
        (P13) Teste de Integração com Mock:
        Verifica se o serviço processa corretamente o JSON da IA
        e persiste as relações ManyToMany de alérgenos.
        """
        recipe = setup_data
        
        # 1. Preparar o Mock da resposta da IA
        mock_ai_response = {
            "detected_allergens": ["Trigo", "Amendoim", "Ovos"],
            "nutritional_estimates": {"calories_kcal": 350},
            "safety_flags": ["Risco de anafilaxia (Amendoim)"],
            "risk_analysis": "Receita de alto risco."
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": json.dumps(mock_ai_response)}
        
        # Configurar o context manager do httpx
        mock_client_instance = mock_client_cls.return_value.__enter__.return_value
        mock_client_instance.post.return_value = mock_response

        # 2. Executar o Serviço
        service = RecipeAnalysisService()
        success = service.analyze_recipe(recipe)

        # 3. Asserções
        assert success is True
        
        recipe.refresh_from_db()
        
        # Verifica se mudou o status
        assert recipe.status == FamilyRecipe.Status.PENDING_REVIEW
        
        # Verifica Alérgenos
        detected_names = list(recipe.detected_allergens.values_list('name', flat=True))
        assert "Trigo" in detected_names
        assert "Amendoim" in detected_names
        assert "Ovos" in detected_names
        assert "Leite" not in detected_names # Não estava na receita
        
        # Verifica Flags
        assert "Risco de anafilaxia (Amendoim)" in recipe.safety_flags

    @patch("social.services.httpx.Client")
    def test_analyze_recipe_api_failure(self, mock_client_cls, setup_data):
        """
        Verifica o comportamento quando o Ollama falha.
        """
        recipe = setup_data
        
        # Simula erro de conexão
        mock_client_instance = mock_client_cls.return_value.__enter__.return_value
        mock_client_instance.post.side_effect = Exception("Connection refused")

        service = RecipeAnalysisService()
        success = service.analyze_recipe(recipe)

        assert success is False
        
        recipe.refresh_from_db()
        # Não deve ter mudado o status nem associado alérgenos
        assert recipe.status == FamilyRecipe.Status.DRAFT
        assert recipe.detected_allergens.count() == 0
