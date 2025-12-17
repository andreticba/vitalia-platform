# backend/core/models.py em 2025-12-14 11:48

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from pgvector.django import VectorField

# Importa os campos de criptografia
from django_crypto_fields.fields import EncryptedCharField, EncryptedTextField

# Importa o utilitário de Blind Indexing
from .utils import generate_search_tokens

# --- 1. RBAC Dinâmico e Organização (B2B) ---

class Permission(models.Model):
    """
    Permissões granulares do sistema.
    Ex: 'view_health_data', 'approve_wellness_plan', 'manage_recipes'.
    """
    slug = models.SlugField(max_length=100, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    """
    Papéis dinâmicos que agrupam permissões.
    Ex: 'Participante', 'Médico', 'Gestor de Clínica', 'Admin Vitalia'.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, related_name='roles', blank=True)
    is_system_role = models.BooleanField(
        default=False, 
        help_text=_("Papéis de sistema não podem ser deletados (ex: Admin, Participante).")
    )

    def __str__(self):
        return self.name


class Organization(models.Model):
    """
    Representa o Cliente B2B (Clínica, Hospital, Profissional Solo).
    Para profissionais liberais, é uma 'Organização de um homem só'.
    """
    class OrgType(models.TextChoices):
        PLATFORM = 'PLATFORM', _('Plataforma Vitalia')
        CLINIC = 'CLINIC', _('Clínica/Hospital')
        SOLO_PRACTITIONER = 'SOLO', _('Profissional Liberal')
        ACADEMIC = 'ACADEMIC', _('Instituição Acadêmica')
        PARTNER = 'PARTNER', _('Parceiro de Marketplace')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    org_type = models.CharField(max_length=20, choices=OrgType.choices, default=OrgType.SOLO_PRACTITIONER)
    is_active = models.BooleanField(default=True)
    
    # White-Labeling e Configuração
    theme_config = models.JSONField(
        default=dict, 
        blank=True,
        help_text=_("Configurações visuais: cores, logo, terminologia.")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_org_type_display()})"


class Team(models.Model):
    """
    Equipes dentro de uma Organização (ex: 'Cardiologia', 'Nutrição').
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


# --- 2. Identidade e Perfis (Unificado) ---

class UserProfile(models.Model):
    """
    Perfil base estendendo o User do Django.
    Contém os dados PII criptografados e o mecanismo de busca segura.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Dados Pessoais Sensíveis (PII) - Criptografados
    # EncryptedTextField usado para evitar limite de tamanho RSA em nomes longos
    full_name = EncryptedTextField(null=True, blank=True)
    
    # Blind Indexing: Tokens de busca (Hashes) para permitir buscar por nome sem descriptografar
    search_tokens = ArrayField(
        models.CharField(max_length=32),
        blank=True,
        default=list,
        help_text=_("Hashes das partes do nome para busca segura (Blind Index).")
    )
    
    # Estes são pequenos o suficiente para manter CharField (limite ~214 chars no RSA)
    phone_number = EncryptedCharField(max_length=20, null=True, blank=True)
    cpf = EncryptedCharField(max_length=14, null=True, blank=True, unique=True)
    
    # Contexto Organizacional
    primary_organization = models.ForeignKey(
        Organization, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='members',
        help_text=_("A organização principal do usuário (nula para Participantes independentes).")
    )
    
    # RBAC
    roles = models.ManyToManyField(Role, related_name='users', blank=True)
    teams = models.ManyToManyField(Team, related_name='members', blank=True)

    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Intercepta o salvamento para atualizar os tokens de busca
        sempre que o nome mudar.
        """
        if self.full_name:
            # Gera os tokens a partir do texto plano antes dele ser criptografado pelo field
            # Nota: O django-crypto-fields criptografa no get_prep_value, então aqui 
            # self.full_name ainda é legível se foi setado recentemente.
            # Se for update sem mudar o nome, pode ser necessário lógica extra,
            # mas para MVP isso cobre criação e edição explícita.
            try:
                self.search_tokens = generate_search_tokens(self.full_name)
            except Exception:
                # Fallback se full_name já estiver criptografado ou inválido
                pass
        else:
            self.search_tokens = []
            
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            # Índice GIN para busca ultra-rápida no Array de tokens
            GinIndex(fields=['search_tokens'], name='user_name_blind_idx'),
        ]

    def __str__(self):
        return self.user.username


class ParticipantProfile(models.Model):
    """
    Dados específicos do Participante (o Paciente/Usuário Final).
    Focado em engajamento, autonomia e gamificação.
    """
    class AutonomyLevel(models.IntegerChoices):
        LEVEL_1_DEPENDENT = 1, _('Nível 1: Dependente (Início)')
        LEVEL_2_COLLABORATIVE = 2, _('Nível 2: Colaborativo (Intermediário)')
        LEVEL_3_AUTONOMOUS = 3, _('Nível 3: Autônomo (Mestre)')

    class PersonalityType(models.TextChoices):
        ACHIEVER = 'ACHIEVER', _('Realizador')
        SOCIALIZER = 'SOCIALIZER', _('Socializador')
        CAUTIOUS = 'CAUTIOUS', _('Cauteloso/Seguro')
        EXPLORER = 'EXPLORER', _('Explorador')
        UNKNOWN = 'UNKNOWN', _('Não Identificado')

    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='participant_data')
    
    # Gamificação & Comportamento
    autonomy_level = models.IntegerField(choices=AutonomyLevel.choices, default=AutonomyLevel.LEVEL_1_DEPENDENT)
    personality_type = models.CharField(max_length=20, choices=PersonalityType.choices, default=PersonalityType.UNKNOWN)
    
    gamification_wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_streak_days = models.PositiveIntegerField(default=0)
    
    # Saúde Básica (Snapshot)
    birth_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Participante: {self.profile.user.username} (Nível {self.autonomy_level})"


class ProfessionalProfile(models.Model):
    """
    Dados específicos para Profissionais de Saúde e Bem-Estar.
    """
    class ProfessionalLevel(models.TextChoices):
        TRAINEE = 'TRAINEE', _('Em Treinamento')
        SPECIALIST = 'SPECIALIST', _('Especialista Certificado')
        AUTHORITY = 'AUTHORITY', _('Autoridade/Líder')

    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='professional_data')
    
    professional_level = models.CharField(max_length=20, choices=ProfessionalLevel.choices, default=ProfessionalLevel.TRAINEE)
    reputation_score = models.FloatField(default=0.0, help_text="Score de 0 a 5 baseado em feedback e auditoria.")
    specialties = models.JSONField(default=list, blank=True, help_text="Lista de especialidades (ex: ['Cardiologia', 'Nutrição Esportiva']).")
    
    # Auditoria e Capacitação
    is_verified = models.BooleanField(default=False)
    vitalia_academy_progress = models.JSONField(default=dict, blank=True, help_text="Progresso nos cursos obrigatórios.")

    def __str__(self):
        return f"Profissional: {self.profile.user.username} ({self.get_professional_level_display()})"


# --- 3. Governança, Auditoria e Data Vault ---

class ConsentLog(models.Model):
    """
    Registro imutável de consentimento do usuário (LGPD/GDPR).
    """
    class ConsentType(models.TextChoices):
        TERMS_OF_SERVICE = 'TERMS', _('Termos de Serviço')
        DATA_SHARING = 'SHARING', _('Compartilhamento de Dados')
        MARKETING = 'MARKETING', _('Comunicações de Marketing')
        RESEARCH = 'RESEARCH', _('Uso para Pesquisa (Knowledge Hub)')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consents')
    consent_type = models.CharField(max_length=20, choices=ConsentType.choices)
    granted = models.BooleanField(default=False)
    
    # Metadados de Auditoria
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    version = models.CharField(max_length=50, help_text="Versão do documento aceito.")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "CONCEDIDO" if self.granted else "REVOGADO"
        return f"{self.user.username} - {self.consent_type} - {status}"


class DataAccessGrant(models.Model):
    """
    O Coração do Data Vault.
    Define quem (Grantee) pode acessar o quê (Resource) de quem (Owner).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Atores
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_accesses', help_text="O dono do dado (Participante).")
    grantor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grants_issued', help_text="Quem realizou a ação (geralmente o owner).")
    
    # Quem recebe o acesso (Pode ser um usuário específico ou um time inteiro)
    grantee_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='received_accesses')
    grantee_team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='received_accesses')
    
    # O Recurso (Polimórfico - Pode ser um WellnessPlan, um Exame, ou Tudo)
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    target_object_id = models.CharField(max_length=255, null=True, blank=True)
    target_object = GenericForeignKey('target_content_type', 'target_object_id')
    
    # Definição do Acesso
    permissions = models.JSONField(default=list, help_text="Lista de permissões concedidas (ex: ['read', 'approve']).")
    consent_log = models.ForeignKey(ConsentLog, on_delete=models.PROTECT, related_name='active_grants')
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Acesso temporário (opcional).")
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['owner', 'grantee_user']),
            models.Index(fields=['owner', 'grantee_team']),
        ]

    def is_active(self):
        now = timezone.now()
        not_revoked = self.revoked_at is None
        not_expired = self.expires_at is None or self.expires_at > now
        return not_revoked and not_expired

    def __str__(self):
        target = self.target_object or "TODOS"
        return f"Grant: {self.owner} -> {self.grantee_user or self.grantee_team} em {target}"


class AuditLog(models.Model):
    """
    Log de Auditoria de Segurança e Compliance.
    Registra acessos, modificações e decisões da IA.
    """
    class ActionType(models.TextChoices):
        ACCESS = 'ACCESS', _('Acesso a Dados')
        CREATE = 'CREATE', _('Criação')
        UPDATE = 'UPDATE', _('Atualização')
        DELETE = 'DELETE', _('Exclusão/Arquivamento')
        AI_DECISION = 'AI_DECISION', _('Decisão/Sugestão da IA')
        HUMAN_REVIEW = 'HUMAN_REVIEW', _('Revisão Humana (HITL)')
        LOGIN = 'LOGIN', _('Login')
        FAILED_LOGIN = 'FAILED_LOGIN', _('Falha de Login')

    id = models.BigAutoField(primary_key=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ActionType.choices)
    
    # Recurso Afetado
    target_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    target_object_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Detalhes e IA
    details = models.JSONField(default=dict, blank=True)
    ai_reasoning_snapshot = models.JSONField(
        null=True, 
        blank=True, 
        help_text=_("Snapshot do raciocínio da IA (Chain of Thought) para explicabilidade.")
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Audit: {self.action} by {self.actor} at {self.timestamp}"


class Document(models.Model):
    class DocumentStatus(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        PROCESSING = "PROCESSING", "Processando"
        EMBEDDING = "EMBEDDING", "Vetorizando"
        COMPLETED = "COMPLETED", "Concluído"
        FAILED = "FAILED", "Falhou"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="documents")
    uploaded_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    file = models.FileField(upload_to="documents/", null=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_size_bytes = models.PositiveIntegerField(default=0)
    file_hash = models.CharField(max_length=64, db_index=True)
    
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self): return self.file_name

class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    content = models.TextField()
    # Vetor de 4096 dimensões (padrão Llama 3) ou 768 (Nomic). Ajuste se mudar o modelo.
    # O Llama 3 padrão via Ollama costuma ser 4096.
    embedding = VectorField(dimensions=4096) 
    page_number = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    def __str__(self): return f"Chunk de {self.document.file_name}"