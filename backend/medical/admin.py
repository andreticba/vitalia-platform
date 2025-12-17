# backend/medical/admin.py em 2025-12-14 11:48

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import (
    # Anatomia
    Bone, BoneLandmark, Joint, JointBone, JointMovement, JointStructure,
    # Miologia & Cinesiologia
    Muscle, MuscleBoneAttachment, MuscleAction,
    # Patologia
    Pathology, MovementContraindication,
    # Exercícios
    Exercise, ExerciseMuscle,
    # Legado Resistência
    ResistanceRoutine, ResistanceWorkout, WorkoutSet,
    # Vitalia
    WellnessPlan, DailySchedule, PrescribedActivity,
    # Data Vault
    MedicalExam, PhysicalEvaluation
)

# =========================================================
# UTILS & MIXINS
# =========================================================

class BaseAdmin(admin.ModelAdmin):
    """Configuração base para paginação e visualização"""
    list_per_page = 20
    save_on_top = True

# =========================================================
# 1. KNOWLEDGE HUB: OSTEOLOGIA (Ossos)
# =========================================================

class BoneLandmarkInline(admin.TabularInline):
    model = BoneLandmark
    extra = 1
    classes = ('collapse',)
    verbose_name = "Acidente Ósseo (Landmark)"
    verbose_name_plural = "Acidentes Ósseos neste Osso"

@admin.register(Bone)
class BoneAdmin(BaseAdmin):
    list_display = ('name', 'scientific_name', 'body_segment_badge', 'bone_type', 'landmarks_count')
    list_filter = ('division', 'body_segment', 'bone_type')
    search_fields = ('name', 'scientific_name')
    inlines = [BoneLandmarkInline]
    
    fieldsets = (
        ('Identificação', {'fields': ('name', 'scientific_name', 'image_url')}),
        ('Classificação', {'fields': ('division', 'body_segment', 'bone_type')}),
        ('Detalhes Clínicos', {'fields': ('description', 'clinical_notes')}),
    )

    def landmarks_count(self, obj):
        return obj.landmarks.count()
    landmarks_count.short_description = "Qtd. Landmarks"

    def body_segment_badge(self, obj):
        # FIX VISUAL: Fundo suave e Texto Escuro para contraste
        colors = {
            'CABECA_PESCOCO': '#E9D8FD', 'TRONCO': '#FED7D7', 
            'MEMBROS_SUPERIORES': '#C6F6D5', 'MEMBROS_INFERIORES': '#BEE3F8'
        }
        bg_color = next((v for k, v in colors.items() if k in obj.body_segment), '#E2E8F0')
        return format_html(
            '<span style="background-color: {}; color: #1A202C; padding: 3px 8px; border-radius: 10px; font-weight: bold; font-size: 11px;">{}</span>',
            bg_color, obj.get_body_segment_display()
        )
    body_segment_badge.short_description = "Segmento"

@admin.register(BoneLandmark)
class BoneLandmarkAdmin(BaseAdmin):
    list_display = ('name', 'bone', 'description_short')
    search_fields = ('name', 'bone__name')
    autocomplete_fields = ['bone']

    def description_short(self, obj):
        return (obj.description[:75] + '...') if len(obj.description) > 75 else obj.description
    description_short.short_description = "Descrição"

# =========================================================
# 2. KNOWLEDGE HUB: ARTROLOGIA (Articulações)
# =========================================================

class JointBoneInline(admin.TabularInline):
    model = JointBone
    extra = 0
    verbose_name = "Osso Conectado"
    verbose_name_plural = "Ossos que formam esta articulação"
    autocomplete_fields = ['bone']

class JointMovementInline(admin.TabularInline):
    model = JointMovement
    extra = 0
    # Removido 'collapse' para que o admin da Junta mostre os movimentos abertos (como solicitado)
    verbose_name = "Movimento Permitido"
    verbose_name_plural = "Cinesiologia (Movimentos Permitidos)"

class JointStructureInline(admin.TabularInline):
    model = JointStructure
    extra = 0
    verbose_name = "Estrutura de Suporte"
    verbose_name_plural = "Ligamentos, Discos e Bursas"

@admin.register(Joint)
class JointAdmin(BaseAdmin):
    list_display = ('name', 'structural_type', 'synovial_type', 'connected_bones_preview', 'movements_count')
    list_filter = ('structural_type', 'synovial_type')
    search_fields = ('name',)
    inlines = [JointBoneInline, JointStructureInline, JointMovementInline]

    def connected_bones_preview(self, obj):
        bones = [jb.bone.name for jb in obj.bones_connected.all()]
        return ", ".join(bones[:3]) + ("..." if len(bones) > 3 else "")
    connected_bones_preview.short_description = "Ossos Conectados"

    def movements_count(self, obj):
        return obj.movements.count()
    movements_count.short_description = "Movimentos"

@admin.register(JointStructure)
class JointStructureAdmin(BaseAdmin):
    # Link direto para a Junta para navegação rápida
    list_display = ('name', 'joint_link', 'type_description')
    list_filter = ('joint', 'type_description') # Agrupamento por Joint
    search_fields = ('name', 'joint__name')
    autocomplete_fields = ['joint']

    def joint_link(self, obj):
        url = reverse("admin:medical_joint_change", args=[obj.joint.id])
        return format_html('<a href="{}">{}</a>', url, obj.joint.name)
    joint_link.short_description = "Articulação (Pai)"

@admin.register(JointMovement)
class JointMovementAdmin(BaseAdmin):
    # Link direto para a Junta
    list_display = ('name', 'joint_link', 'rom_degrees', 'plane')
    search_fields = ('name', 'joint__name')
    list_filter = ('joint', 'plane') # Agrupamento por Joint
    autocomplete_fields = ['joint']

    def joint_link(self, obj):
        url = reverse("admin:medical_joint_change", args=[obj.joint.id])
        return format_html('<a href="{}">{}</a>', url, obj.joint.name)
    joint_link.short_description = "Articulação (Pai)"

# =========================================================
# 3. KNOWLEDGE HUB: MIOLOGIA (Músculos)
# =========================================================

class MuscleBoneAttachmentInline(admin.TabularInline):
    model = MuscleBoneAttachment
    extra = 0
    verbose_name = "Fixação Óssea"
    verbose_name_plural = "Origens e Inserções"
    autocomplete_fields = ['landmark']
    ordering = ('attachment_type',)

class MuscleActionInline(admin.TabularInline):
    model = MuscleAction
    extra = 0
    verbose_name = "Ação Biomecânica"
    verbose_name_plural = "Ações (Cinesiologia)"
    autocomplete_fields = ['movement']

@admin.register(Muscle)
class MuscleAdmin(BaseAdmin):
    list_display = ('name', 'body_segment', 'specific_region', 'actions_count')
    list_filter = ('body_segment', 'specific_region')
    search_fields = ('name', 'scientific_name')
    inlines = [MuscleBoneAttachmentInline, MuscleActionInline]
    
    fieldsets = (
        ('Identificação', {'fields': ('name', 'scientific_name', 'image_url')}),
        ('Localização', {'fields': ('body_segment', 'specific_region')}),
        ('Descritivo (Legado)', {'fields': ('origin_text', 'insertion_text', 'description'), 'classes': ('collapse',)}),
    )

    def actions_count(self, obj):
        return obj.actions.count()
    actions_count.short_description = "Qtd. Ações"

# =========================================================
# 4. KNOWLEDGE HUB: EXERCÍCIOS
# =========================================================

class ExerciseMuscleInline(admin.TabularInline):
    model = ExerciseMuscle
    extra = 1
    autocomplete_fields = ['muscle']
    verbose_name = "Músculo Ativado"
    verbose_name_plural = "Músculos Envolvidos"

@admin.register(Exercise)
class ExerciseAdmin(BaseAdmin):
    list_display = ('name', 'difficulty_badge', 'muscles_preview')
    search_fields = ('name',)
    list_filter = ('difficulty', 'muscles__body_segment')
    inlines = [ExerciseMuscleInline]
    
    def difficulty_badge(self, obj):
        colors = {'BEGINNER': 'green', 'INTERMEDIATE': 'orange', 'ADVANCED': 'red'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.difficulty, 'black'),
            obj.get_difficulty_display()
        )
    difficulty_badge.short_description = "Dificuldade"

    def muscles_preview(self, obj):
        # FIX: 'muscles_involved' não existe no objeto Exercise. 
        # A relação many-to-many é acessada via 'exercisemuscle_set' (nome padrão do reverse da intermediária)
        # ou via 'muscles' para os objetos Muscle direto.
        # Aqui queremos o ROLE que está na intermediária, então usamos exercisemuscle_set.
        items = obj.exercisemuscle_set.filter(role='AGONISTA_PRIMARIO')[:3]
        names = [item.muscle.name for item in items]
        return ", ".join(names)
    muscles_preview.short_description = "Agonistas Principais"

# =========================================================
# 5. SEGURANÇA E PATOLOGIA
# =========================================================

class MovementContraindicationInline(admin.TabularInline):
    model = MovementContraindication
    extra = 1
    autocomplete_fields = ['movement']
    verbose_name = "Movimento Contraindicado"

@admin.register(Pathology)
class PathologyAdmin(BaseAdmin):
    list_display = ('name', 'icd_code', 'contraindications_count')
    search_fields = ('name', 'icd_code')
    inlines = [MovementContraindicationInline]

    def contraindications_count(self, obj):
        return obj.contraindications.count()
    contraindications_count.short_description = "Restrições"

# =========================================================
# 6. VITALIA ORCHESTRATOR (O Plano de Bem-Estar)
# =========================================================

class PrescribedActivityInline(admin.TabularInline):
    model = PrescribedActivity
    extra = 0
    ordering = ('order_index',)
    fields = ('order_index', 'title', 'activity_type', 'resistance_ref', 'is_completed')
    autocomplete_fields = ['resistance_ref'] 
    verbose_name = "Atividade Prescrita"

@admin.register(DailySchedule)
class DailyScheduleAdmin(BaseAdmin):
    list_display = ('day_label', 'plan_link', 'activities_count')
    list_filter = ('plan',)
    inlines = [PrescribedActivityInline]
    search_fields = ('day_label', 'plan__title')
    
    def plan_link(self, obj):
        url = reverse("admin:medical_wellnessplan_change", args=[obj.plan.id])
        return format_html('<a href="{}">{}</a>', url, obj.plan.title)
    plan_link.short_description = "Pertence ao Plano"

    def activities_count(self, obj):
        return obj.activities.count()
    activities_count.short_description = "Qtd. Atividades"

class DailyScheduleInline(admin.TabularInline):
    model = DailySchedule
    extra = 0
    ordering = ('day_index',)
    fields = ('day_index', 'day_label', 'activities_summary_html')
    readonly_fields = ('activities_summary_html',)
    show_change_link = True
    verbose_name = "Dia da Jornada"
    verbose_name_plural = "Agenda da Jornada (Dias)"

    def activities_summary_html(self, obj):
        activities = obj.activities.all().order_by('order_index')
        if not activities:
            return mark_safe("<span style='color: #ccc; font-style: italic;'>Dia livre (sem atividades)</span>")
        
        html = "<div style='display: flex; gap: 5px; flex-wrap: wrap;'>"
        for act in activities:
            icon = {
                'RESISTANCE': '🏋️', 'CARDIO_TIME': '🏃', 'CARDIO_DISTANCE': '🚴',
                'FLEXIBILITY': '🧘', 'MINDFULNESS': '🧠', 'NUTRITION': '🍎'
            }.get(act.activity_type, '✅')
            
            style = "background: #f0f0f0; border: 1px solid #ddd; padding: 2px 6px; border-radius: 4px; font-size: 12px;"
            html += f"<span style='{style}'>{icon} {act.title}</span>"
        html += "</div>"
        return mark_safe(html)
    activities_summary_html.short_description = "Resumo Visual"

@admin.register(WellnessPlan)
class WellnessPlanAdmin(BaseAdmin):
    list_display = ('title', 'participant_link', 'status_badge', 'professional_link', 'duration_display')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'participant__username', 'participant__profile__full_name')
    autocomplete_fields = ['participant', 'responsible_professional', 'resistance_routine']
    inlines = [DailyScheduleInline]
    
    fieldsets = (
        ('Cabeçalho do Plano', {
            'fields': ('title', 'status', 'participant', 'responsible_professional')
        }),
        ('Metas & Prazos', {
            'fields': ('goals', 'start_date', 'end_date')
        }),
        ('Inteligência & Integração', {
            'fields': ('resistance_routine', 'ai_generation_metadata'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'DRAFT': '#CBD5E0', 'PENDING_APPROVAL': '#F6E05E', 
            'ACTIVE': '#68D391', 'COMPLETED': '#63B3ED', 'ARCHIVED': '#FC8181'
        }
        return format_html(
            '<span style="background-color: {}; padding: 4px 8px; border-radius: 12px; color: #1A202C; font-weight: bold; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#eee'),
            obj.get_status_display()
        )
    status_badge.short_description = "Status Atual"

    def participant_link(self, obj):
        return obj.participant.profile.full_name if hasattr(obj.participant, 'profile') else obj.participant.username
    participant_link.short_description = "Participante"

    def professional_link(self, obj):
        if not obj.responsible_professional: return "-"
        return obj.responsible_professional.profile.full_name
    professional_link.short_description = "Profissional Resp."

    def duration_display(self, obj):
        if obj.start_date and obj.end_date:
            days = (obj.end_date - obj.start_date).days
            return f"{days} dias"
        return "-"
    duration_display.short_description = "Duração"

# =========================================================
# 7. LEGADO RESISTÊNCIA
# =========================================================

class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 0
    autocomplete_fields = ['exercise']
    fields = ('order_index', 'exercise', 'sets', 'reps', 'load_kg', 'rpe')
    verbose_name = "Série"
    verbose_name_plural = "Séries do Treino"

@admin.register(ResistanceWorkout)
class ResistanceWorkoutAdmin(BaseAdmin):
    list_display = ('name', 'routine', 'sets_count_display')
    search_fields = ('name',)
    inlines = [WorkoutSetInline]
    
    def sets_count_display(self, obj):
        return obj.sets.count()
    sets_count_display.short_description = "Exercícios"

@admin.register(ResistanceRoutine)
class ResistanceRoutineAdmin(BaseAdmin):
    list_display = ('name', 'goal', 'created_by')
    search_fields = ('name', 'goal')

# =========================================================
# 8. DATA VAULT (Exames e Avaliações)
# =========================================================

@admin.register(MedicalExam)
class MedicalExamAdmin(BaseAdmin):
    list_display = ('title', 'patient', 'exam_date', 'laboratory_name')
    search_fields = ('patient__username', 'title')
    list_filter = ('exam_date',)

@admin.register(PhysicalEvaluation)
class PhysicalEvaluationAdmin(BaseAdmin):
    list_display = ('patient_link', 'evaluator_link', 'evaluation_type', 'date', 'finalized_bool')
    list_filter = ('evaluation_type', 'is_finalized', 'date')
    search_fields = ('patient__username', 'patient__profile__full_name')
    readonly_fields = ('date',)
    
    fieldsets = (
        ('Metadados', {
            'fields': ('patient', 'evaluator', 'evaluation_type', 'date', 'is_finalized')
        }),
        ('Dados Brutos (JSON)', {
            'fields': ('measurements_data', 'results_data'),
            'classes': ('collapse',),
            'description': "Dados técnicos armazenados em formato JSON."
        }),
        ('Anotações', {
            'fields': ('notes',)
        }),
    )

    def patient_link(self, obj):
        return obj.patient.username
    patient_link.short_description = "Paciente"

    def evaluator_link(self, obj):
        return obj.evaluator.username if obj.evaluator else "-"
    evaluator_link.short_description = "Avaliador"

    def finalized_bool(self, obj):
        return obj.is_finalized
    finalized_bool.boolean = True
    finalized_bool.short_description = "Finalizado"