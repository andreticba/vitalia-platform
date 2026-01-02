# backend/medical/serializers.py em 2025-12-14 11:48

from rest_framework import serializers
from .models import WellnessPlan, DailySchedule, PrescribedActivity
from core.serializers import UserSimpleSerializer

class PrescribedActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescribedActivity
        fields = ['id', 'title', 'activity_type', 'order_index', 'is_completed', 'flexible_data']

class DailyScheduleSerializer(serializers.ModelSerializer):
    activities = PrescribedActivitySerializer(many=True, read_only=True)
    
    class Meta:
        model = DailySchedule
        fields = ['id', 'day_label', 'day_index', 'activities']

class WellnessPlanDetailSerializer(serializers.ModelSerializer):
    """Serializer rico para a visão detalhada do plano (Aprovação HITL)."""
    participant = UserSimpleSerializer(read_only=True)
    schedules = DailyScheduleSerializer(many=True, read_only=True)
    
    class Meta:
        model = WellnessPlan
        fields = [
            'id', 'title', 'goals', 'status', 'start_date', 'end_date',
            'participant', 'ai_generation_metadata', 'schedules', 'created_at'
        ]

class WellnessPlanListSerializer(serializers.ModelSerializer):
    """Serializer leve para listagem no Dashboard."""
    participant_name = serializers.CharField(source='participant.profile.full_name', read_only=True)
    
    class Meta:
        model = WellnessPlan
        fields = ['id', 'title', 'status', 'participant_name', 'created_at']