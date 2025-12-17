# backend/core/serializers.py em 2025-12-14 11:48

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Role, Organization

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

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    roles = RoleSerializer(many=True, read_only=True)
    primary_organization = OrganizationSimpleSerializer(read_only=True)
    
    # Decifra os campos automaticamente para leitura na API
    full_name = serializers.CharField(read_only=True) 
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'full_name', 'avatar_url', 
            'roles', 'primary_organization'
        ]
