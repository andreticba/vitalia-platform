# backend/social/serializers.py  em 2025-12-14 11:48

from rest_framework import serializers
from core.serializers import UserSimpleSerializer, ProfessionalProfile
from .models import FamilyRecipe, Allergen

class AllergenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergen
        fields = ['id', 'name', 'severity_level', 'description']

class ProfessionalSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para exibir quem validou a receita."""
    name = serializers.CharField(source='profile.full_name', read_only=True)
    
    class Meta:
        model = ProfessionalProfile
        fields = ['id', 'name', 'professional_level']

class FamilyRecipeReadSerializer(serializers.ModelSerializer):
    """
    (P13) Serializer de Leitura: Dados aninhados e formatados para a UI.
    """
    author = UserSimpleSerializer(read_only=True)
    detected_allergens = AllergenSerializer(many=True, read_only=True)
    validated_by = ProfessionalSimpleSerializer(read_only=True)
    
    # Campos calculados para facilitar o Frontend
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_at_fmt = serializers.DateTimeField(source='created_at', format="%d/%m/%Y", read_only=True)

    class Meta:
        model = FamilyRecipe
        fields = [
            'id', 'title', 'origin_story', 'emotional_value', 'consumption_context',
            'ingredients_text', 'preparation_method', 'servings', 'preparation_time_minutes',
            'detected_allergens', 'nutritional_info_snapshot', 'safety_flags',
            'status', 'status_display', 'is_public', 'likes_count',
            'author', 'validated_by', 'created_at_fmt'
        ]

class FamilyRecipeWriteSerializer(serializers.ModelSerializer):
    """
    (P13) Serializer de Escrita: Validação estrita de entrada.
    """
    class Meta:
        model = FamilyRecipe
        fields = [
            'title', 'origin_story', 'emotional_value', 'consumption_context',
            'ingredients_text', 'preparation_method', 'servings', 'preparation_time_minutes',
            'is_public'
        ]
    
    def create(self, validated_data):
        # Associa automaticamente ao usuário logado
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class FeedItemSerializer(serializers.Serializer):
    """
    Serializer polimórfico para o Feed.
    Pode retornar uma Receita, uma Conquista (Badge) ou uma Atividade Física.
    """
    type = serializers.CharField() # 'RECIPE', 'ACTIVITY', 'BADGE'
    id = serializers.CharField()
    title = serializers.CharField()
    author_name = serializers.CharField()
    author_avatar = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField()
    
    # Metadados flexíveis
    details = serializers.JSONField(required=False)
    likes_count = serializers.IntegerField(default=0)