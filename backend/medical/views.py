# backend/medical/views.py em 2025-12-14 11:48

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import WellnessPlan
from .serializers import WellnessPlanListSerializer, WellnessPlanDetailSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import DailySchedule, PrescribedActivity
from .serializers import DailyScheduleSerializer, PrescribedActivitySerializer

class WellnessPlanViewSet(viewsets.ModelViewSet):
    """
    Gestão de Planos de Bem-Estar.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Se for Profissional: Vê planos que ele gerencia
        if user.profile.roles.filter(name__in=['Profissional de Saúde', 'Gestor de Clínica']).exists():
            return WellnessPlan.objects.filter(responsible_professional=user)
        # Se for Participante: Vê seus próprios planos
        return WellnessPlan.objects.filter(participant=user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WellnessPlanDetailSerializer
        return WellnessPlanListSerializer

    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        """Fluxo HITL: Profissional aprova o plano."""
        plan = self.get_object()
        # Aqui adicionaríamos verificação de permissão granular
        plan.status = WellnessPlan.Status.ACTIVE
        plan.save()
        return Response({'status': 'ACTIVE', 'message': 'Plano aprovado e ativado com sucesso.'})

class PrescribedActivityViewSet(viewsets.GenericViewSet):
    """
    Endpoint para interagir com atividades específicas (Check-in).
    """
    queryset = PrescribedActivity.objects.all()
    serializer_class = PrescribedActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        """
        O Participante marca a atividade como feita.
        Gatilho para Gamificação via Signals.
        """
        activity = self.get_object()
        
        # Validação simples de segurança (dono do plano)
        if activity.schedule.plan.participant != request.user:
            return Response({"error": "Não autorizado"}, status=403)

        if not activity.is_completed:
            activity.is_completed = True
            activity.save() # Dispara o signal do gamification
            return Response({'status': 'COMPLETED', 'message': 'Atividade concluída! Pontos creditados.'})
        
        return Response({'status': 'ALREADY_COMPLETED'}, status=200)

class MyDailyScheduleView(viewsets.ViewSet):
    """
    View 'BFF' (Backend for Frontend) para a tela 'Meu Dia'.
    Retorna a agenda de hoje do plano ATIVO.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        # 1. Busca plano ativo
        active_plan = request.user.wellness_plans.filter(status='ACTIVE').first()
        
        if not active_plan:
            return Response({"has_plan": False, "message": "Nenhum plano ativo no momento."})

        # 2. Determina o dia atual no ciclo do plano
        # (Lógica simplificada: dia da semana 0-6. Em produção, seria delta dias)
        today_index = timezone.now().weekday() 
        
        try:
            schedule = active_plan.schedules.get(day_index=today_index)
            serializer = DailyScheduleSerializer(schedule)
            return Response({
                "has_plan": True, 
                "plan_title": active_plan.title,
                "schedule": serializer.data
            })
        except DailySchedule.DoesNotExist:
            return Response({"has_plan": True, "schedule": None, "message": "Dia livre!"})

