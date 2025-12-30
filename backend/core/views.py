# backend/core/views.py em 2025-12-14 11:48

from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q

from .models import UserProfile, Role
from .serializers import UserProfileSerializer
from .utils import generate_search_tokens

class CurrentUserView(APIView):
    """
    Retorna os dados do usuário autenticado + perfil + papéis.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
        summary="Obter Perfil do Usuário Logado",
        tags=["Auth"]
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data)

class PatientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para listar pacientes.
    Implementa busca segura via Blind Indexing no campo criptografado 'full_name'.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated] # No futuro: IsProfessional

    @extend_schema(
        parameters=[
            OpenApiParameter(name='search', description='Nome, CPF ou Email', required=False, type=str),
        ],
        summary="Listar Pacientes",
        tags=["Core"]
    )
    def get_queryset(self):
        # Filtra apenas perfis que são Participantes
        queryset = UserProfile.objects.filter(
            roles__name="Participante"
        ).select_related('user', 'participant_data', 'primary_organization')

        # Filtro de Busca (Blind Indexing Implementation)
        search_term = self.request.query_params.get('search', '').strip()
        
        if search_term:
            # 1. Busca por Username ou Email (Campos abertos no User)
            # Otimização: Se contiver '@', prioriza email
            if '@' in search_term:
                queryset = queryset.filter(user__email__icontains=search_term)
            else:
                # 2. Busca por Nome (Criptografado) usando Search Tokens
                # Gera os tokens do termo digitado (ex: "João" -> hash_joao)
                tokens = generate_search_tokens(search_term)
                
                if tokens:
                    # A query verifica se o array search_tokens do banco contém 
                    # TODOS os tokens gerados da busca (busca AND)
                    queryset = queryset.filter(search_tokens__contains=tokens)
                else:
                    # Fallback para busca textual em campos não criptografados se não gerou tokens
                    queryset = queryset.filter(user__username__icontains=search_term)

        return queryset