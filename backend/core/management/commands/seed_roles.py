# backend/core/management/commands/seed_roles.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from core.models import Role, Permission
from django.db import transaction

class Command(BaseCommand):
    help = 'Popula o banco de dados com Roles e Permissions iniciais da Vitalia.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando seed de Roles e Permissions...'))

        # 1. Definição das Permissões Granulares (Slug, Nome, Descrição)
        # Estas permissões refletem as ações possíveis no sistema B2B2C
        all_permissions = [
            # --- Dados de Saúde (Core) ---
            ('view_own_health_data', 'Ver Próprios Dados', 'Acesso aos próprios exames e planos'),
            ('view_patient_health_data', 'Ver Dados de Paciente', 'Acesso a dados de terceiros mediante DataAccessGrant'),
            ('edit_medical_records', 'Editar Prontuário', 'Inserir resultados de exames e anamnese'),
            
            # --- Wellness Plan & HITL ---
            ('generate_wellness_plan', 'Gerar Plano (IA)', 'Solicitar geração de plano à IA'),
            ('approve_wellness_plan', 'Aprovar Plano (HITL)', 'Permissão crítica para validar e ativar planos'),
            ('contest_wellness_plan', 'Contestar Plano', 'Direito do participante de pedir revisão'),

            # --- Receitas e Social ---
            ('post_family_recipe', 'Postar Receita', 'Criar receita familiar'),
            ('validate_recipe_safety', 'Validar Segurança Receita', 'Moderação técnica de receitas (Nutricionista)'),
            ('interact_social_feed', 'Interagir no Feed', 'Curtir, comentar e compartilhar conquistas'),

            # --- Gamificação e Marketplace ---
            ('view_leaderboard', 'Ver Leaderboard', 'Acesso aos rankings'),
            ('redeem_rewards', 'Resgatar Recompensas', 'Trocar Vitalia Coins por produtos'),
            ('manage_marketplace_offers', 'Gerir Ofertas', 'Criar itens no marketplace (Parceiros)'),

            # --- Gestão Organizacional (B2B) ---
            ('manage_organization_members', 'Gerir Membros', 'Adicionar/Remover profissionais da clínica'),
            ('view_organization_analytics', 'Ver Analytics', 'Acesso a dashboards de performance'),
            ('manage_platform_settings', 'Gerir Plataforma', 'Superadmin: configurações globais'),
        ]

        created_perms = 0
        perm_objects = {}

        with transaction.atomic():
            for slug, name, desc in all_permissions:
                perm, created = Permission.objects.get_or_create(
                    slug=slug,
                    defaults={'name': name, 'description': desc}
                )
                perm_objects[slug] = perm
                if created:
                    created_perms += 1

        self.stdout.write(self.style.SUCCESS(f'{created_perms} Permissões novas criadas.'))

        # 2. Definição dos Papéis (Roles) e Associação de Permissões
        roles_definitions = [
            {
                'name': 'Participante',
                'description': 'Usuário final da plataforma (Paciente/Cidadão).',
                'is_system': True,
                'permissions': [
                    'view_own_health_data', 
                    'contest_wellness_plan', 
                    'post_family_recipe',
                    'interact_social_feed',
                    'view_leaderboard',
                    'redeem_rewards'
                ]
            },
            {
                'name': 'Profissional de Saúde',
                'description': 'Médico, Nutricionista ou Treinador. Requer validação.',
                'is_system': True,
                'permissions': [
                    'view_patient_health_data',
                    'edit_medical_records',
                    'generate_wellness_plan',
                    'approve_wellness_plan', # HITL
                    'validate_recipe_safety',
                    'view_organization_analytics',
                    'interact_social_feed'
                ]
            },
            {
                'name': 'Gestor de Clínica',
                'description': 'Administrador de uma Organização B2B.',
                'is_system': False,
                'permissions': [
                    'manage_organization_members',
                    'view_organization_analytics'
                ]
            },
            {
                'name': 'Parceiro Marketplace',
                'description': 'Empresa que oferece produtos/descontos.',
                'is_system': False,
                'permissions': [
                    'manage_marketplace_offers',
                    'view_organization_analytics'
                ]
            },
            {
                'name': 'Admin Vitalia',
                'description': 'Superusuário da plataforma.',
                'is_system': True,
                'permissions': [slug for slug, _, _ in all_permissions] # Todas
            }
        ]

        created_roles = 0
        updated_roles = 0

        with transaction.atomic():
            for role_def in roles_definitions:
                role, created = Role.objects.get_or_create(
                    name=role_def['name'],
                    defaults={
                        'description': role_def['description'],
                        'is_system_role': role_def['is_system']
                    }
                )
                
                # Atualiza permissões (M2M)
                perms_to_add = []
                for perm_slug in role_def['permissions']:
                    if perm_slug in perm_objects:
                        perms_to_add.append(perm_objects[perm_slug])
                    else:
                        self.stdout.write(self.style.ERROR(f'Permissão não encontrada: {perm_slug}'))
                
                role.permissions.set(perms_to_add)
                
                if created:
                    created_roles += 1
                else:
                    updated_roles += 1

        self.stdout.write(self.style.SUCCESS(f'Roles processados: {created_roles} criados, {updated_roles} atualizados.'))
        self.stdout.write(self.style.SUCCESS('Seed de Roles concluído com sucesso!'))
