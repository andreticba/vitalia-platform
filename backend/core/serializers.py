# backend/core/serializers.py em 2025-12-14 11:48

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Role, Organization, ProfessionalProfile, ParticipantProfile

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['name', 'description', 'is_system_role']

class OrganizationSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'org_type', 'theme_config']

class ProfessionalProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalProfile
        fields = ['id', 'professional_level', 'reputation_score', 'specialties', 'is_verified']

class ParticipantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipantProfile
        fields = ['id', 'autonomy_level', 'personality_type', 'gamification_wallet_balance', 'current_streak_days']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    roles = RoleSerializer(many=True, read_only=True)
    primary_organization = OrganizationSimpleSerializer(read_only=True)
    
    # Decifra os campos automaticamente para leitura na API
    full_name = serializers.CharField(read_only=True) 
    
    # Nested data (opcional, carrega se existir)
    professional_data = ProfessionalProfileSerializer(read_only=True)
    participant_data = ParticipantProfileSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'full_name', 'avatar_url', 
            'roles', 'primary_organization',
            'professional_data', 'participant_data'
        ]