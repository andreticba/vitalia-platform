# backend/core/views.py em 2025-12-14 11:48

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserProfileSerializer

class CurrentUserView(APIView):
    """
    Retorna os dados do usuário autenticado + perfil + papéis.
    Essencial para o SPA saber para onde redirecionar após login.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data)
