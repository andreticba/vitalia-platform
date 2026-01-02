# backend/core/management/commands/seed_simulation.py em 2025-12-14 11:48

import random
import time
import uuid
from django.db.models import Q
from datetime import timedelta, date
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from faker import Faker

# Imports Vitalia Apps
from core.models import (
    Organization, Team, UserProfile, Role, Permission, AuditLog,
    ParticipantProfile, ProfessionalProfile, DataAccessGrant, ConsentLog,
    
)
from medical.models import MedicalExam, WellnessPlan, DailySchedule, PrescribedActivity, ResistanceRoutine, Exercise
from social.models import FamilyRecipe
# from gamification.models import ... (Futuro)

User = get_user_model()
fake = Faker('pt_BR')

# ==============================================================================
# UTILITÁRIOS DE LOG (Visual Rico)
# ==============================================================================
class LogColors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class Command(BaseCommand):
    help = 'Motor de Simulação Vitalia: Gera um Cenário Vivo B2B2C com histórico e progressão temporal.'

    def add_arguments(self, parser):
        # 1. Controle de Tempo
        parser.add_argument(
            '--direction', 
            type=str, 
            choices=['past', 'future'], 
            default='past',
            help='Direção da simulação temporal. "past" cria histórico (backfill), "future" cria agendamentos.'
        )
        parser.add_argument(
            '--days', 
            type=int, 
            default=30, 
            help='Janela de tempo para simular atividades (dias).'
        )

        # 2. Controle de Escopo
        parser.add_argument(
            '--reset', 
            action='store_true', 
            help='[PERIGO] Limpa todos os dados de simulação anteriores antes de começar.'
        )
        parser.add_argument(
            '--mode', 
            type=str, 
            choices=['setup', 'activity', 'full'], 
            default='full',
            help='Escopo da execução. setup=estrutura, activity=diário, full=ambos.'
        )

        # 3. População
        parser.add_argument('--users', type=int, default=40, help='Número de Participantes.')
        parser.add_argument('--pros', type=int, default=12, help='Número de Profissionais.')
        
        # 4. Comportamento
        parser.add_argument('--adherence', type=float, default=0.7, help='Taxa média de adesão (0.0 a 1.0).')

    def log(self, msg, level='INFO', icon='👉'):
        """Logger visual."""
        color = LogColors.BLUE
        if level == 'SUCCESS': color = LogColors.GREEN
        if level == 'WARNING': color = LogColors.YELLOW
        if level == 'ERROR': color = LogColors.RED
        if level == 'HEADER': color = LogColors.HEADER
        
        timestamp = timezone.now().strftime('%H:%M:%S')
        self.stdout.write(f"{LogColors.BOLD}[{timestamp}]{LogColors.RESET} {color}{icon} {msg}{LogColors.RESET}")

    def handle(self, *args, **options):
        self.options = options
        self.log("INICIANDO MOTOR DE SIMULAÇÃO VITALIA", 'HEADER', '🚀')
        self.log(f"Configuração: {options['days']} dias ({options['direction']}) | {options['users']} Users | Mode: {options['mode']}")

        try:
            with transaction.atomic():
                # FASE 0: LIMPEZA (Opcional)
                if options['reset']:
                    self._wipe_simulation_data()

                # FASE 1: SETUP ESTRUTURAL (B2B & B2C)
                if options['mode'] in ['setup', 'full']:
                    self._setup_roles_check()
                    self._setup_organizations()
                    self.professionals = self._setup_professionals()
                    self.participants = self._setup_participants()
                    self._establish_circles_of_care()
                else:
                    # Carrega existentes para modo 'activity'
                    self.log("Modo Activity: Carregando usuários existentes...", 'WARNING')
                    self.participants = list(User.objects.filter(profile__roles__name='Participante'))
                    self.professionals = list(User.objects.filter(profile__roles__name='Profissional de Saúde'))

                # FASE 2: SIMULAÇÃO TEMPORAL (O Dia a Dia)
                if options['mode'] in ['activity', 'full']:
                    self._simulate_timeline()

            self.log("SIMULAÇÃO CONCLUÍDA COM SUCESSO!", 'SUCCESS', '✨')

        except Exception as e:
            import traceback
            self.log(f"Erro Fatal na Simulação: {e}", 'ERROR', '💀')
            self.stdout.write(traceback.format_exc())

# ==========================================================================
    # FASE 0: LIMPEZA (CORRIGIDA)
    # ==========================================================================
    def _wipe_simulation_data(self):
        self.log("Executando Protocolo de Limpeza...", 'WARNING', '🧹')
        
        # 1. Identificar IDs dos usuários simulados para queries rápidas
        sim_users = User.objects.filter(email__contains='@vitalia.sim')
        sim_user_ids = list(sim_users.values_list('id', flat=True))
        
        if not sim_user_ids:
            self.log("Nenhum dado simulado encontrado para limpeza.", 'SUCCESS')
            return

        self.log(f"Alvos identificados: {len(sim_user_ids)} usuários.", 'INFO')

        # 2. Remover DataAccessGrants (A causa do ProtectedError)
        # Precisamos remover qualquer grant onde o usuário simulado seja Dono OU Beneficiário
        deleted_grants, _ = DataAccessGrant.objects.filter(
            Q(owner_id__in=sim_user_ids) | 
            Q(grantee_user_id__in=sim_user_ids)
        ).delete()
        self.log(f"Removidos {deleted_grants} DataAccessGrants (Destravando ConsentLogs).", 'INFO')

        # 3. Remover Conexões Sociais
        # Import dinâmico para evitar circularidade se houver
        from social.models import CareConnection
        deleted_conns, _ = CareConnection.objects.filter(
            Q(participant_id__in=sim_user_ids) |
            Q(supporter_id__in=sim_user_ids)
        ).delete()
        self.log(f"Removidas {deleted_conns} Conexões Sociais.", 'INFO')

        # 4. Remover Planos Médicos e Atividades (Cascade limparia, mas explícito é melhor para performance)
        deleted_plans, _ = WellnessPlan.objects.filter(participant_id__in=sim_user_ids).delete()
        self.log(f"Removidos {deleted_plans} Planos de Bem-Estar.", 'INFO')

        # 5. Agora é seguro deletar os usuários
        # O Cascade cuidará de Profiles, ConsentLogs, MedicalExams, etc.
        deleted_users, _ = User.objects.filter(id__in=sim_user_ids).delete()
        
        # 6. Limpar Organizações Simuladas
        deleted_orgs, _ = Organization.objects.filter(name__startswith="[SIM]").delete()
        
        self.log(f"Limpeza concluída. {deleted_users} usuários e {deleted_orgs} organizações removidos.", 'SUCCESS')

    # ==========================================================================
    # FASE 1: SETUP ESTRUTURAL
    # ==========================================================================
    def _setup_roles_check(self):
        """Garante que os Roles essenciais existam."""
        required = ['Participante', 'Profissional de Saúde', 'Gestor de Clínica']
        for r in required:
            if not Role.objects.filter(name=r).exists():
                self.log(f"Role '{r}' não encontrado. Rode 'seed_roles' primeiro.", 'ERROR')
                raise Exception("Missing Roles")

    def _setup_organizations(self):
        self.log("Construindo Ecossistema B2B...", 'INFO', '🏥')
        
        # 1. Clínica Principal
        self.clinic, _ = Organization.objects.get_or_create(
            name="[SIM] Clínica Bem-Estar Integral",
            defaults={
                'org_type': Organization.OrgType.CLINIC,
                'theme_config': {'primary_color': '#0ea5e9', 'platform_name': 'Bem-Estar App'}
            }
        )
        
        # 2. Laboratórios
        self.lab_analisa, _ = Organization.objects.get_or_create(
            name="[SIM] Laboratório Analisa Bio",
            defaults={'org_type': Organization.OrgType.PARTNER}
        )
        self.studio_perf, _ = Organization.objects.get_or_create(
            name="[SIM] Studio Performance Lab",
            defaults={'org_type': Organization.OrgType.PARTNER}
        )
        
        self.log(f"Organizações Ativas: {self.clinic.name}, {self.lab_analisa.name}", 'SUCCESS')

    def _create_user(self, role_name, org, archetype=None):
        """Factory interna de Usuários."""
        first_name = fake.first_name()
        last_name = fake.last_name()
        username = f"{first_name.lower()}.{last_name.lower()}_{random.randint(10,99)}"
        email = f"{username}@vitalia.sim" # Sufixo para facilitar identificação e limpeza
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            }
        )
        if created:
            user.set_password('vitalia123')
            user.save()
            
            # Perfil
            role = Role.objects.get(name=role_name)
            profile = UserProfile.objects.create(
                user=user,
                full_name=f"{first_name} {last_name}",
                cpf=fake.cpf(),
                primary_organization=org
            )
            profile.roles.add(role)
            
            # Sub-perfis
            if role_name == 'Participante':
                ParticipantProfile.objects.create(
                    profile=profile,
                    autonomy_level=random.choice([1, 2, 3]),
                    personality_type=archetype or 'UNKNOWN'
                )
                # Consentimento padrão
                ConsentLog.objects.create(
                    user=user,
                    consent_type=ConsentLog.ConsentType.DATA_SHARING,
                    granted=True,
                    version="1.0-SIM"
                )
            
            elif role_name == 'Profissional de Saúde':
                specs = random.choice([['Nutrição'], ['Cardiologia'], ['Educação Física']])
                ProfessionalProfile.objects.create(
                    profile=profile,
                    professional_level='SPECIALIST',
                    specialties=specs,
                    is_verified=True
                )
        
        return user

    def _setup_professionals(self):
        self.log("Contratando Equipe Profissional...", 'INFO', '🩺')
        pros = []
        
        # Distribuição de Especialidades
        specs = [
            ('Médico Integrativo', 2),
            ('Nutricionista', 4),
            ('Personal Trainer', 4),
            ('Psicólogo', 2)
        ]
        
        for title, count in specs:
            for _ in range(count):
                u = self._create_user('Profissional de Saúde', self.clinic)
                # Atualiza especialidade simulada
                u.profile.professional_data.specialties = [title]
                u.profile.professional_data.save()
                pros.append(u)
        
        self.log(f"{len(pros)} Profissionais cadastrados e ativos.", 'SUCCESS')
        return pros

    def _setup_participants(self):
        target = self.options['users']
        self.log(f"Recrutando {target} Participantes (Arquétipos)...", 'INFO', '👥')
        
        participants = []
        archetypes = ['ACHIEVER', 'SOCIALIZER', 'CAUTIOUS', 'EXPLORER']
        
        for i in range(target):
            arch = archetypes[i % len(archetypes)] # Distribuição balanceada
            u = self._create_user('Participante', self.clinic, archetype=arch)
            participants.append(u)
            
            if i % 10 == 0:
                self.stdout.write(f"   > Criados {i}/{target}...")
                
        self.log(f"{len(participants)} Participantes prontos para a jornada.", 'SUCCESS')
        return participants

    def _establish_circles_of_care(self):
        self.log("Estabelecendo Círculos de Cuidado e Conexões Sociais...", 'INFO', '🤝')
        
        from social.models import CareConnection # Import dinâmico
        
        clinic_team, _ = Team.objects.get_or_create(organization=self.clinic, name="Equipe Multidisciplinar")
        
        for participant in self.participants:
            # 1. LGPD (Técnico)
            consent = ConsentLog.objects.filter(user=participant).first()
            DataAccessGrant.objects.get_or_create(
                owner=participant,
                grantee_team=clinic_team,
                defaults={'grantor': participant, 'consent_log': consent, 'permissions': ['full_access']}
            )
            
            # 2. Social (Afetivo)
            # Conecta o participante a 3 "Apoiadores" aleatórios (outros participantes ou bots de família)
            # Para simplificar, vamos criar conexões com os Profissionais
            pro = random.choice(self.professionals)
            
            # Profissional segue o Participante (para ver o feed dele)
            CareConnection.objects.get_or_create(
                participant=participant,
                supporter=pro,
                defaults={'connection_type': 'PRO'}
            )
            
            # Participante segue o Profissional (para ver receitas dele)
            CareConnection.objects.get_or_create(
                participant=pro,
                supporter=participant,
                defaults={'connection_type': 'PRO'}
            )

        self.log("Grafo Social estabelecido.", 'SUCCESS')

    # ==========================================================================
    # FASE 2: MOTOR DE SIMULAÇÃO (A MÁQUINA DO TEMPO)
    # ==========================================================================
    def _simulate_timeline(self):
        days = self.options['days']
        direction = self.options['direction']
        
        # Define o range de datas
        today = timezone.now().date()
        if direction == 'past':
            start_date = today - timedelta(days=days)
            end_date = today - timedelta(days=1) # Até ontem
        else:
            start_date = today
            end_date = today + timedelta(days=days)
            
        self.log(f"Iniciando Simulação Temporal: {start_date} até {end_date} ({days} dias)", 'HEADER', '⏳')

        current_date = start_date
        total_activities = 0
        
        # Loop de Dias
        while current_date <= end_date:
            day_str = current_date.strftime('%d/%m')
            # self.stdout.write(f"   > Simulando dia {day_str}...") # Verbose off para speed
            
            # Loop de Participantes
            for user in self.participants:
                # 1. Gera/Atualiza Plano de Bem-Estar (Se não tiver um ativo)
                self._ensure_active_plan(user, current_date)
                
                # 2. Simula Atividades do Dia (Check-in)
                completed = self._simulate_daily_activities(user, current_date)
                total_activities += completed
                
                # 3. Eventos Aleatórios (Exames, Receitas)
                if random.random() < 0.05: # 5% de chance por dia
                    self._generate_random_event(user, current_date)

            current_date += timedelta(days=1)

        self.log(f"Simulação Finalizada. {total_activities} atividades geradas no período.", 'SUCCESS')

    def _ensure_active_plan(self, user, date_ref):
        """Garante que o usuário tenha um plano ativo na data simulada."""
        active_plan = WellnessPlan.objects.filter(
            participant=user, 
            status=WellnessPlan.Status.ACTIVE
        ).first()
        
        if not active_plan:
            # Cria um plano novo
            # Em produção, isso chamaria o AI Service. Aqui, mockamos o resultado.
            pro = random.choice(self.professionals)
            
            plan = WellnessPlan.objects.create(
                participant=user,
                responsible_professional=pro,
                title=f"Plano de Vitalidade {date_ref.strftime('%B')}",
                goals="Melhorar condicionamento cardiovascular e reduzir estresse.",
                status=WellnessPlan.Status.ACTIVE, # Já nasce aprovado para facilitar
                start_date=date_ref,
                end_date=date_ref + timedelta(days=30),
                created_at=timezone.make_aware(timezone.datetime.combine(date_ref, timezone.datetime.min.time()))
            )
            
            # Gera agenda básica (Semana modelo repetida)
            self._generate_schedule_mock(plan)

    def _generate_schedule_mock(self, plan):
        """Popula o DailySchedule do plano com atividades fake."""
        activities_pool = [
            ('Caminhada Matinal', 'CARDIO_DISTANCE', '3km'),
            ('Treino de Força A', 'RESISTANCE', 'Full Body'),
            ('Meditação Guiada', 'MINDFULNESS', '10min'),
            ('Beber 2L de Água', 'NUTRITION', 'Hidratação'),
            ('Alongamento', 'FLEXIBILITY', '15min')
        ]
        
        # Cria 7 dias de agenda
        for day_idx in range(7): # 0=Segunda ... 6=Domingo
            day_label = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][day_idx]
            schedule = DailySchedule.objects.create(
                plan=plan,
                day_label=day_label,
                day_index=day_idx
            )
            
            # Adiciona 2 a 4 atividades por dia
            daily_acts = random.sample(activities_pool, k=random.randint(2, 4))
            for order, (title, type_act, desc) in enumerate(daily_acts):
                PrescribedActivity.objects.create(
                    schedule=schedule,
                    title=title,
                    activity_type=type_act,
                    order_index=order,
                    flexible_data={'description': desc}
                )

    def _simulate_daily_activities(self, user, current_date):
        """
        Simula o usuário completando (ou não) as atividades do dia.
        Aqui entra a lógica de 'Backfilling': Se for passado, marcamos como feito.
        """
        # Acha o plano ativo nesta data
        plan = user.wellness_plans.filter(status='ACTIVE').first()
        if not plan: return 0
        
        # Descobre qual dia da semana é (0-6)
        weekday = current_date.weekday()
        
        # Pega o schedule correspondente
        schedule = plan.schedules.filter(day_index=weekday).first()
        if not schedule: return 0
        
        completed_count = 0
        adherence_rate = self.options['adherence']
        
        for activity in schedule.activities.all():
            # Rola o dado de adesão
            if random.random() < adherence_rate:
                # Se estamos no passado, 'concluímos' a atividade.
                # Como o modelo PrescribedActivity é simples (boolean),
                # para ter histórico temporal real, precisaríamos de uma tabela de 'ActivityLog'.
                # PARA O MVP: Vamos apenas logar no AuditLog para simular o evento temporal.
                
                AuditLog.objects.create(
                    actor=user,
                    action=AuditLog.ActionType.UPDATE,
                    target_object_id=str(activity.id),
                    details={'status': 'COMPLETED', 'simulated_date': str(current_date)},
                    timestamp=timezone.make_aware(timezone.datetime.combine(current_date, timezone.datetime.min.time()))
                )
                
                # Credita Pontos (Simulação direta na carteira para performance)
                if hasattr(user, 'participant_data'):
                    points = 10
                    user.participant_data.gamification_wallet_balance += points
                    user.participant_data.save()
                
                completed_count += 1
                
        return completed_count

    def _generate_random_event(self, user, date_ref):
        """Gera exames ou receitas esporádicas."""
        evt_type = random.choice(['EXAM', 'RECIPE'])
        
        if evt_type == 'EXAM':
            MedicalExam.objects.create(
                patient=user,
                title=f"Hemograma Completo - {date_ref.strftime('%b/%Y')}",
                exam_date=date_ref,
                laboratory_name="Laboratório Analisa Bio",
                results_structured={"hemoglobina": random.uniform(11.0, 16.0), "colesterol": random.randint(150, 250)}
            )
        
        elif evt_type == 'RECIPE':
            FamilyRecipe.objects.create(
                author=user,
                title=f"Receita da Família {fake.word()}",
                ingredients_text="Ingredientes secretos...",
                preparation_method="Misture com amor.",
                status='PUBLISHED',
                is_public=True,
                created_at=timezone.make_aware(timezone.datetime.combine(date_ref, timezone.datetime.min.time()))
            )