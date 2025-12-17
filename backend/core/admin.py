# backend/core/admin.py em 2025-12-14 11:48

import json
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone  # Importante para corrigir o fuso horário
from .models import (
    Organization, Team, UserProfile, Role, Permission,
    ParticipantProfile, ProfessionalProfile,
    ConsentLog, DataAccessGrant, AuditLog,
    Document, DocumentChunk
)

# =========================================================
# MIXINS & UTILS
# =========================================================

class BaseAdmin(admin.ModelAdmin):
    list_per_page = 20
    save_on_top = True

def json_prettify(json_data):
    if not json_data:
        return "-"
    json_str = json.dumps(json_data, sort_keys=True, indent=2, ensure_ascii=False)
    # FIX VISUAL: Adicionado 'color: #333' para garantir contraste em fundo claro
    style = "white-space: pre-wrap; font-family: monospace; font-size: 12px; background: #f4f4f4; color: #333; padding: 10px; border-radius: 4px; border: 1px solid #ddd;"
    return format_html('<div style="{}">{}</div>', style, json_str)

# =========================================================
# 1. GESTÃO DE CONHECIMENTO (RAG & DOCUMENTS)
# =========================================================

class DocumentChunkInline(admin.TabularInline):
    """
    Exibe os chunks do documento.
    """
    model = DocumentChunk
    extra = 0
    can_delete = False
    # Removemos o limite rígido de visualização para evitar o TypeError de slice
    # O max_num controla apenas a criação de novos via inline
    max_num = 0 
    fields = ('page_number', 'content_preview', 'view_chunk_link')
    readonly_fields = ('page_number', 'content_preview', 'view_chunk_link')
    verbose_name = "Fragmento (Vetor)"
    verbose_name_plural = "Fragmentos Vetorizados (Amostra)"
    ordering = ('page_number',)
    classes = ('collapse',) # Colapsado por padrão para não poluir se houver muitos

    def content_preview(self, obj):
        return obj.content[:100] + "..." if obj.content else "-"
    content_preview.short_description = "Conteúdo"

    def view_chunk_link(self, obj):
        if obj.id:
            url = reverse("admin:core_documentchunk_change", args=[obj.id])
            return format_html('<a href="{}" class="button" target="_blank">Ver Detalhe ↗</a>', url)
        return "-"
    view_chunk_link.short_description = "Ação"

@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    list_display = ('file_name_display', 'organization', 'status_badge', 'file_size_formatted', 'created_at_fmt', 'updated_at_fmt')
    list_filter = ('organization', 'status', 'created_at')
    search_fields = ('file_name', 'file_hash')
    inlines = [DocumentChunkInline]
    
    fieldsets = (
        ('Metadados do Arquivo', {
            'fields': ('organization', 'uploaded_by_user', 'file', 'file_name', 'file_hash', 'file_size_bytes')
        }),
        ('Status & Datas', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
        ('Estatísticas', {
            'fields': ('chunks_stats',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at', 'file_hash', 'file_size_bytes', 'chunks_stats')

    def file_name_display(self, obj):
        return (obj.file_name[:40] + '..') if len(obj.file_name) > 40 else obj.file_name
    file_name_display.short_description = "Arquivo"

    def created_at_fmt(self, obj):
        # FIX TIMEZONE: Converte para hora local antes de formatar
        return timezone.localtime(obj.created_at).strftime('%d/%m/%Y %H:%M')
    created_at_fmt.short_description = "Criado em"
    created_at_fmt.admin_order_field = 'created_at'

    def updated_at_fmt(self, obj):
        return timezone.localtime(obj.updated_at).strftime('%d/%m/%Y %H:%M')
    updated_at_fmt.short_description = "Atualizado em"
    updated_at_fmt.admin_order_field = 'updated_at'

    def status_badge(self, obj):
        colors = {
            'PENDING': '#CBD5E0', 'PROCESSING': '#F6E05E', 'EMBEDDING': '#63B3ED',
            'COMPLETED': '#68D391', 'FAILED': '#FC8181'
        }
        return format_html(
            '<span style="background-color: {}; padding: 4px 8px; border-radius: 12px; color: #1A202C; font-weight: bold; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#eee'),
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def file_size_formatted(self, obj):
        size = obj.file_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024: return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    file_size_formatted.short_description = "Tamanho"

    def chunks_stats(self, obj):
        count = obj.chunks.count()
        return format_html(
            """<div style="background: #f0fdf4; padding: 10px; border: 1px solid #bbf7d0; border-radius: 6px; color: #166534;">
                <strong>Total de Vetores:</strong> {}<br>
                <strong>Modelo:</strong> llama3
            </div>""",
            count
        )
    chunks_stats.short_description = "Resumo"

@admin.register(DocumentChunk)
class DocumentChunkAdmin(BaseAdmin):
    list_display = ('short_content', 'document_link', 'page_number')
    list_filter = ('document__organization', 'document') # Agrupamento por documento
    search_fields = ('content', 'document__file_name')
    
    # Ocultamos o campo 'metadata' cru (JSONWidget) e mostramos apenas o 'metadata_pretty'
    exclude = ('embedding', 'metadata') 
    readonly_fields = ('document', 'page_number', 'metadata_pretty')

    def short_content(self, obj):
        return obj.content[:80] + "..."
    short_content.short_description = "Conteúdo"

    def document_link(self, obj):
        url = reverse("admin:core_document_change", args=[obj.document.id])
        return format_html('<a href="{}">{}</a>', url, obj.document.file_name)
    document_link.short_description = "Documento Pai"

    def metadata_pretty(self, obj):
        return json_prettify(obj.metadata)
    metadata_pretty.short_description = "Metadados"

# =========================================================
# 2. IDENTIDADE E ORGANIZAÇÃO (B2B)
# =========================================================

class TeamInline(admin.TabularInline):
    model = Team
    extra = 0
    show_change_link = True
    fields = ('name', 'description')
    verbose_name = "Equipe"
    verbose_name_plural = "Equipes"

class OrganizationMembersInline(admin.TabularInline):
    """
    Lista os usuários (UserProfile) associados a esta organização.
    """
    model = UserProfile
    fk_name = "primary_organization"
    extra = 0
    fields = ('full_name', 'user_link', 'role_names')
    readonly_fields = ('full_name', 'user_link', 'role_names')
    can_delete = False
    verbose_name = "Membro"
    verbose_name_plural = "Membros (Usuários Vinculados)"

    def user_link(self, obj):
        url = reverse("admin:core_userprofile_change", args=[obj.id])
        return format_html('<a href="{}">Editar Perfil ↗</a>', url)
    user_link.short_description = "Ação"

    def role_names(self, obj):
        return ", ".join([r.name for r in obj.roles.all()])
    role_names.short_description = "Papéis"

@admin.register(Organization)
class OrganizationAdmin(BaseAdmin):
    list_display = ('name_visual', 'org_type', 'is_active', 'members_count', 'created_at')
    list_filter = ('org_type', 'is_active')
    search_fields = ('name',)
    
    # REORDENAÇÃO: Membros aparecem antes de Times
    inlines = [OrganizationMembersInline, TeamInline]
    
    readonly_fields = ('theme_preview',)

    fieldsets = (
        ('Dados da Organização', {'fields': ('name', 'org_type', 'is_active')}),
        ('White-Label', {'fields': ('theme_config', 'theme_preview'), 'classes': ('collapse',)}),
    )

    def name_visual(self, obj):
        color = obj.theme_config.get('primary_color', '#cbd5e0')
        return format_html(
            '<span style="display:inline-block; width:10px; height:10px; background-color:{}; border-radius:50%; margin-right:8px;"></span>{}',
            color, obj.name
        )
    name_visual.short_description = "Nome"

    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = "Total Membros"

    def theme_preview(self, obj):
        return json_prettify(obj.theme_config)
    theme_preview.short_description = "Configuração JSON"

@admin.register(Team)
class TeamAdmin(BaseAdmin):
    list_display = ('name', 'organization', 'members_count')
    list_filter = ('organization',) # Agrupamento por organização
    search_fields = ('name', 'organization__name')

    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = "Membros"

# =========================================================
# 3. USUÁRIOS E PERFIS
# =========================================================

class ParticipantDataInline(admin.StackedInline):
    model = ParticipantProfile
    can_delete = False
    verbose_name = 'Dados de Participante (Gamificação & Saúde)'
    fields = ('autonomy_level', 'personality_type', 'gamification_wallet_balance', 'current_streak_days')

class ProfessionalDataInline(admin.StackedInline):
    model = ProfessionalProfile
    can_delete = False
    verbose_name = 'Dados Profissionais (Credenciais)'
    fields = ('professional_level', 'reputation_score', 'is_verified', 'specialties')

@admin.register(UserProfile)
class UserProfileAdmin(BaseAdmin):
    list_display = ('user_link', 'full_name', 'primary_organization', 'role_list')
    list_filter = ('primary_organization', 'roles') # Agrupamento por organização
    search_fields = ('user__username', 'full_name', 'cpf')
    filter_horizontal = ('roles', 'teams')
    inlines = [ParticipantDataInline, ProfessionalDataInline]
    
    fieldsets = (
        ('Identidade Criptografada', {
            'fields': ('user', 'full_name', 'cpf', 'phone_number'),
            'description': 'Estes dados são armazenados criptografados no banco.'
        }),
        ('Acesso Organizacional', {
            'fields': ('primary_organization', 'roles', 'teams')
        })
    )

    def user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "Conta de Acesso"

    def role_list(self, obj):
        return ", ".join([r.name for r in obj.roles.all()])
    role_list.short_description = "Papéis"

# Configuração do UserAdmin padrão para injetar o Profile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil Vitalia (Core)'
    filter_horizontal = ('roles', 'teams')
    show_change_link = True
    fields = ('full_name', 'primary_organization', 'roles')
    readonly_fields = ('full_name', 'primary_organization', 'roles')

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_full_name_vitalia', 'get_org', 'is_active')
    list_filter = ('is_active', 'is_staff', 'profile__roles', 'profile__primary_organization')
    
    def get_full_name_vitalia(self, obj):
        return getattr(obj.profile, 'full_name', '-')
    get_full_name_vitalia.short_description = "Nome Real"

    def get_org(self, obj):
        if hasattr(obj, 'profile') and obj.profile.primary_organization:
            return obj.profile.primary_organization.name
        return "-"
    get_org.short_description = "Organização"

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Role)
class RoleAdmin(BaseAdmin):
    list_display = ('name', 'is_system_role', 'permissions_count')
    filter_horizontal = ('permissions',)
    
    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = "Permissões"

@admin.register(Permission)
class PermissionAdmin(BaseAdmin):
    list_display = ('slug', 'name', 'description')
    search_fields = ('name', 'slug')

# =========================================================
# 4. AUDITORIA E DATA VAULT
# =========================================================

@admin.register(DataAccessGrant)
class DataAccessGrantAdmin(BaseAdmin):
    list_display = ('owner', 'target_summary', 'grantee_display', 'status_badge', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('owner__username', 'owner__profile__full_name')
    readonly_fields = ('created_at', 'json_permissions')

    def target_summary(self, obj):
        return obj.target_object or "TODOS"
    target_summary.short_description = "Recurso Alvo"

    def grantee_display(self, obj):
        if obj.grantee_user: return f"User: {obj.grantee_user.username}"
        if obj.grantee_team: return f"Team: {obj.grantee_team.name}"
        return "?"
    grantee_display.short_description = "Concedido Para"

    def status_badge(self, obj):
        active = obj.is_active()
        color = 'green' if active else 'red'
        label = 'ATIVO' if active else 'EXPIRADO/REVOGADO'
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', color, label)
    status_badge.short_description = "Status"

    def json_permissions(self, obj):
        return json_prettify(obj.permissions)
    json_permissions.short_description = "Permissões JSON"

@admin.register(ConsentLog)
class ConsentLogAdmin(BaseAdmin):
    list_display = ('user', 'consent_type_badge', 'granted_bool', 'timestamp', 'ip_address')
    list_filter = ('consent_type', 'granted', 'timestamp')
    search_fields = ('user__username',)
    readonly_fields = [f.name for f in ConsentLog._meta.fields] 

    def consent_type_badge(self, obj):
        return format_html('<span style="background:#eee; padding:2px 5px; border-radius:3px;">{}</span>', obj.get_consent_type_display())
    consent_type_badge.short_description = "Tipo"

    def granted_bool(self, obj):
        return '✅' if obj.granted else '❌'
    granted_bool.short_description = "Aceite"

@admin.register(AuditLog)
class AuditLogAdmin(BaseAdmin):
    list_display = ('timestamp', 'actor', 'action_badge', 'target_summary', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('actor__username', 'details')
    readonly_fields = ('timestamp', 'actor', 'action', 'details_pretty', 'ai_reasoning_pretty')

    def action_badge(self, obj):
        color = 'blue'
        if 'DELETE' in obj.action: color = 'red'
        if 'AI' in obj.action: color = 'purple'
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', color, obj.get_action_display())
    action_badge.short_description = "Ação"

    def target_summary(self, obj):
        return f"{obj.target_content_type} ({obj.target_object_id})"
    target_summary.short_description = "Alvo"

    def details_pretty(self, obj):
        return json_prettify(obj.details)
    details_pretty.short_description = "Detalhes"

    def ai_reasoning_pretty(self, obj):
        return json_prettify(obj.ai_reasoning_snapshot)
    ai_reasoning_pretty.short_description = "Raciocínio da IA (Chain of Thought)"