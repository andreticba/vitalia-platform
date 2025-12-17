# backend/core/management/commands/seed_system_init.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import (
    Organization, Team, UserProfile, Role, 
    ParticipantProfile, ProfessionalProfile
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Inicializa a estrutura organizacional e cria perfis para usuários órfãos.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando inicialização do sistema Vitalia...'))

        with transaction.atomic():
            # 1. Garantir Organização Mestra (Vitalia)
            vitalia_org, created = Organization.objects.get_or_create(
                name="Vitalia Platform",
                defaults={
                    'org_type': Organization.OrgType.PLATFORM,
                    'is_active': True,
                    'theme_config': {
                        "primary_color": "#0F172A", 
                        "platform_name": "Vitalia Core"
                    }
                }
            )
            if created:
                self.stdout.write(f"Organização Mestra criada: {vitalia_org.name}")

            # 2. Garantir Time Mestre
            vitalia_team, created = Team.objects.get_or_create(
                organization=vitalia_org,
                name="Equipe Core",
                defaults={'description': "Administradores e IA"}
            )

            # 3. Buscar Roles Padrão (Criados no seed_roles)
            try:
                role_participant = Role.objects.get(name="Participante")
                role_admin = Role.objects.get(name="Admin Vitalia")
            except Role.DoesNotExist:
                self.stdout.write(self.style.ERROR("ERRO: Roles não encontrados. Rode 'python manage.py seed_roles' antes."))
                return

            # 4. Reparar Usuários Órfãos (Importados do Legado)
            # Busca usuários que não têm UserProfile
            orphan_users = User.objects.filter(profile__isnull=True)
            
            fixed_count = 0
            for user in orphan_users:
                # Cria o UserProfile base
                profile = UserProfile.objects.create(
                    user=user,
                    full_name=user.first_name + " " + user.last_name if user.first_name else user.username,
                    primary_organization=vitalia_org # Por padrão, vincula à plataforma
                )
                
                # Assume que usuários legados são Participantes por padrão
                # (A menos que seja o admin/system)
                if user.is_staff or "admin" in user.username:
                    profile.roles.add(role_admin)
                    # Cria perfil profissional para admins
                    ProfessionalProfile.objects.create(
                        profile=profile,
                        professional_level=ProfessionalProfile.ProfessionalLevel.AUTHORITY,
                        is_verified=True
                    )
                else:
                    profile.roles.add(role_participant)
                    # Cria perfil de participante
                    ParticipantProfile.objects.create(
                        profile=profile,
                        autonomy_level=ParticipantProfile.AutonomyLevel.LEVEL_1_DEPENDENT
                    )
                
                fixed_count += 1
                # self.stdout.write(f"Perfil criado para: {user.username}") # Verbose

            self.stdout.write(self.style.SUCCESS(f'Perfis de Usuário Reparados/Criados: {fixed_count}'))
            self.stdout.write(self.style.SUCCESS('Sistema Inicializado e pronto para Login.'))