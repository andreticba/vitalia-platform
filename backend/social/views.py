# backend/social/views.py

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FamilyRecipe
from .serializers import FamilyRecipeReadSerializer, FamilyRecipeWriteSerializer

class IsAuthorOrReadOnly(permissions.BasePermission):
    """Permite leitura para todos (no contexto permitido), mas edição apenas para o autor."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user

class FamilyRecipeViewSet(viewsets.ModelViewSet):
    """
    Endpoint para o Hub de Receitas Afetivas.
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'ingredients_text', 'origin_story']
    ordering_fields = ['created_at', 'likes_count']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        # Retorna receitas publicadas OU receitas que o próprio usuário criou (mesmo rascunho)
        return FamilyRecipe.objects.filter(
            is_public=True,
            status=FamilyRecipe.Status.PUBLISHED
        ) | FamilyRecipe.objects.filter(author=user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FamilyRecipeWriteSerializer
        return FamilyRecipeReadSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAuthorOrReadOnly()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Gamificação simples: Curtir uma receita."""
        recipe = self.get_object()
        recipe.likes_count += 1
        recipe.save()
        return Response({'likes_count': recipe.likes_count})