# backend/social/views.py em 2025-12-14 11:48

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FamilyRecipe
from .serializers import FamilyRecipeReadSerializer, FamilyRecipeWriteSerializer, FeedItemSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .models import CareConnection, FamilyRecipe
from gamification.models import PointTransaction

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

class ActivityFeedView(APIView):
    """
    Aggregator do Feed Social.
    Retorna:
    1. Receitas postadas pela minha rede.
    2. Atividades físicas concluídas pelos meus 'protegidos' (Participantes que eu apoio).
    """
    def get(self, request):
        user = request.user
        feed_items = []

        # 1. Quem eu sigo/apoio?
        supporting_ids = list(CareConnection.objects.filter(supporter=user).values_list('participant_id', flat=True))
        # Inclui a mim mesmo para ver minhas próprias conquistas
        supporting_ids.append(user.id)

        # 2. Buscar Receitas (Publicadas pela rede ou públicas globais)
        recipes = FamilyRecipe.objects.filter(
            Q(author_id__in=supporting_ids) | Q(is_public=True)
        ).select_related('author', 'author__profile').order_by('-created_at')[:10]

        for r in recipes:
            feed_items.append({
                "type": "RECIPE",
                "id": str(r.id),
                "title": f"Nova receita: {r.title}",
                "author_name": r.author.profile.full_name,
                "timestamp": r.created_at,
                "details": {"image": None, "tags": r.safety_flags},
                "likes_count": r.likes_count
            })

        # 3. Buscar Conquistas/Atividades (Gamificação)
        # Apenas atividades relevantes (ex: Treino concluído)
        transactions = PointTransaction.objects.filter(
            user_id__in=supporting_ids,
            transaction_type='ACTIVITY'
        ).select_related('user', 'user__profile').order_by('-created_at')[:15]

        for t in transactions:
            feed_items.append({
                "type": "ACTIVITY",
                "id": str(t.id),
                "title": t.description, # ex: "Concluiu: Treino de Força A"
                "author_name": t.user.profile.full_name,
                "timestamp": t.created_at,
                "details": {"points": t.amount},
                "likes_count": 0 
            })

        # Ordenação final por data (descrescente)
        feed_items.sort(key=lambda x: x['timestamp'], reverse=True)

        return Response(FeedItemSerializer(feed_items, many=True).data)