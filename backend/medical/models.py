# backend/medical/models.py em 2025-12-14 11:48

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.utils import secure_file_upload_path

# =========================================================
# 1. ENUMS E TAXONOMIA (Knowledge Hub)
# =========================================================

class BodySegment(models.TextChoices):
    HEAD_NECK = 'CABECA_PESCOCO', _('Cabeça e Pescoço')
    TRUNK = 'TRONCO', _('Tronco')
    UPPER_ARM_R = 'MEMBRO_SUPERIOR_DIREITO', _('Membro Superior Direito')
    UPPER_ARM_L = 'MEMBRO_SUPERIOR_ESQUERDO', _('Membro Superior Esquerdo')
    UPPER_ARMS = 'MEMBROS_SUPERIORES', _('Membros Superiores (Geral)')
    LOWER_LEG_R = 'MEMBRO_INFERIOR_DIREITO', _('Membro Inferior Direito')
    LOWER_LEG_L = 'MEMBRO_INFERIOR_ESQUERDO', _('Membro Inferior Esquerdo')
    LOWER_LEGS = 'MEMBROS_INFERIORES', _('Membros Inferiores (Geral)')
    SPINE = 'COLUNA_VERTEBRAL', _('Coluna Vertebral')
    PELVIS = 'PELVE', _('Pelve')
    FULL_BODY = 'CORPO_INTEIRO', _('Corpo Inteiro')
    HAND = 'MAO', _('Mão')
    FOOT = 'PE', _('Pé')

class SpecificRegionMuscle(models.TextChoices):
    FACIAL = 'FACIAL', _('Facial')
    MASTIGATORY = 'MASTIGATORIA', _('Mastigatória')
    CERVICAL_ANT = 'CERVICAL_ANTERIOR', _('Cervical Anterior')
    CERVICAL_LAT = 'CERVICAL_LATERAL', _('Cervical Lateral')
    CERVICAL_POST = 'CERVICAL_POSTERIOR', _('Cervical Posterior')
    SUBOCCIPITAL = 'SUBBOCCIPITAL', _('Suboccipital')
    THORACIC_ANT = 'TORACICA_ANTERIOR', _('Torácica Anterior')
    THORACIC_LAT = 'TORACICA_LATERAL', _('Torácica Lateral')
    THORACIC_POST = 'TORACICA_POSTERIOR', _('Torácica Posterior')
    ABDOMINAL_ANT = 'ABDOMINAL_ANTERIOR', _('Abdominal Anterior')
    ABDOMINAL_LAT = 'ABDOMINAL_LATERAL', _('Abdominal Lateral')
    LUMBAR = 'LOMBAR', _('Lombar')
    PELVIC_FLOOR = 'ASSOALHO_PELVICO', _('Assoalho Pélvico')
    DIAPHRAGMA = 'DIAFRAGMA', _('Diafragma')
    SHOULDER = 'OMBRO', _('Ombro')
    ARM_ANT = 'BRACO_ANTERIOR', _('Braço Anterior')
    ARM_POST = 'BRACO_POSTERIOR', _('Braço Posterior')
    FOREARM_ANT = 'ANTEBRACO_ANTERIOR', _('Antebraço Anterior')
    FOREARM_POST = 'ANTEBRACO_POSTERIOR', _('Antebraço Posterior')
    HAND = 'MAO', _('Mão')
    HIP_ANT = 'QUADRIL_ANTERIOR', _('Quadril Anterior')
    HIP_POST = 'QUADRIL_POSTERIOR', _('Quadril Posterior')
    HIP_LAT = 'QUADRIL_LATERAL', _('Quadril Lateral')
    THIGH_ANT = 'COXA_ANTERIOR', _('Coxa Anterior')
    THIGH_POST = 'COXA_POSTERIOR', _('Coxa Posterior')
    THIGH_MED = 'COXA_MEDIAL', _('Coxa Medial')
    LEG_ANT = 'PERNA_ANTERIOR', _('Perna Anterior')
    LEG_LAT = 'PERNA_LATERAL', _('Perna Lateral')
    LEG_POST = 'PERNA_POSTERIOR', _('Perna Posterior')
    FOOT = 'PE', _('Pé')
    FULL_BODY = 'CORPO_INTEIRO', _('Corpo Inteiro')

class SkeletonDivision(models.TextChoices):
    AXIAL = 'AXIAL', _('Axial')
    APPENDICULAR = 'APENDICULAR', _('Apendicular')

class BoneType(models.TextChoices):
    LONG = 'LONGO', _('Longo')
    SHORT = 'CURTO', _('Curto')
    FLAT = 'PLANO', _('Plano')
    IRREGULAR = 'IRREGULAR', _('Irregular')
    SESAMOID = 'SESAMOIDE', _('Sesamóide')
    PNEUMATIC = 'PNEUMATICO', _('Pneumático')

class JointStructuralType(models.TextChoices):
    FIBROUS = 'FIBROSA', _('Fibrosa')
    CARTILAGINOUS = 'CARTILAGINOSA', _('Cartilaginosa')
    SYNOVIAL = 'SINOVIAL', _('Sinovial')

class SynovialType(models.TextChoices):
    PLANE = 'PLANA', _('Plana')
    HINGE = 'GINGLIMO', _('Gínglimo (Dobradiça)')
    PIVOT = 'TROCOIDE', _('Trocóide (Pivô)')
    CONDYLOID = 'ELIPSOIDEA', _('Elipsóidea (Condilar)')
    SADDLE = 'SELAR', _('Selar')
    BALL_AND_SOCKET = 'ESFEROIDE', _('Esferóide')
    NOT_APPLICABLE = 'NAO_APLICAVEL', _('Não Aplicável')

class AttachmentType(models.TextChoices):
    ORIGIN = 'ORIGEM', _('Origem')
    INSERTION = 'INSERCAO', _('Inserção')

class MuscleRole(models.TextChoices):
    PRIME_AGONIST = 'AGONISTA_PRIMARIO', _('Agonista Primário')
    SECONDARY_AGONIST = 'AGONISTA_SECUNDARIO', _('Agonista Secundário')
    ANTAGONIST = 'ANTAGONISTA', _('Antagonista')
    ECCENTRIC_CONTROLLER = 'CONTROLADOR_EXCENTRICO', _('Controlador Excêntrico')
    AUXILIARY_SYNERGIST = 'SINERGISTA_AUXILIAR', _('Sinergista Auxiliar')
    NEUTRALIZER_SYNERGIST = 'SINERGISTA_NEUTRALIZADOR', _('Sinergista Neutralizador')
    STATIC_STABILIZER = 'ESTABILIZADOR_ESTATICO', _('Estabilizador Estático')
    DYNAMIC_STABILIZER = 'ESTABILIZADOR_DINAMICO', _('Estabilizador Dinâmico')

# =========================================================
# 2. KNOWLEDGE HUB: OSTEOLOGIA E ARTROLOGIA
# =========================================================

class Bone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    scientific_name = models.CharField(max_length=255, blank=True, null=True)
    division = models.CharField(max_length=50, choices=SkeletonDivision.choices)
    bone_type = models.CharField(max_length=50, choices=BoneType.choices)
    body_segment = models.CharField(max_length=50, choices=BodySegment.choices)
    description = models.TextField(blank=True)
    clinical_notes = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.name

class BoneLandmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    bone = models.ForeignKey(Bone, on_delete=models.CASCADE, related_name='landmarks')

    def __str__(self): return f"{self.name} ({self.bone.name})"

class Joint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    structural_type = models.CharField(max_length=50, choices=JointStructuralType.choices)
    synovial_type = models.CharField(max_length=50, choices=SynovialType.choices, default=SynovialType.NOT_APPLICABLE)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.name

class JointBone(models.Model):
    # --- FIX CRÍTICO: Definindo ID como UUID explicitamente ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    joint = models.ForeignKey(Joint, on_delete=models.CASCADE, related_name='bones_connected')
    bone = models.ForeignKey(Bone, on_delete=models.CASCADE, related_name='joints_participating')
    role = models.CharField(max_length=100, blank=True, help_text="Ex: Cabeça, Cavidade")

    class Meta:
        unique_together = ('joint', 'bone')

class JointMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    rom_degrees = models.PositiveIntegerField(null=True, blank=True)
    plane = models.CharField(max_length=100, blank=True)
    joint = models.ForeignKey(Joint, on_delete=models.CASCADE, related_name='movements')

    def __str__(self): return f"{self.name} - {self.joint.name}"

class JointStructure(models.Model):
    """
    Ligamentos, Meniscos, Discos e Bursas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type_description = models.CharField(max_length=100, help_text="LIGAMENTO, MENISCO, BOLSA, DISCO")
    description = models.TextField(blank=True)
    
    biomechanical_function = models.TextField(
        blank=True, 
        help_text="Ex: 'Evita translação anterior', 'Absorve carga axial', 'Reduz atrito'."
    )
    
    joint = models.ForeignKey(Joint, on_delete=models.CASCADE, related_name='structures')

    def __str__(self): return f"{self.name} ({self.joint.name})"

# =========================================================
# 3. KNOWLEDGE HUB: MIOLOGIA (Músculos)
# =========================================================

class Muscle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    scientific_name = models.CharField(max_length=255, blank=True, null=True, unique=True)
    body_segment = models.CharField(max_length=50, choices=BodySegment.choices)
    specific_region = models.CharField(max_length=50, choices=SpecificRegionMuscle.choices)
    origin_text = models.TextField(blank=True)
    insertion_text = models.TextField(blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_muscles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    landmarks = models.ManyToManyField(BoneLandmark, through='MuscleBoneAttachment', related_name='muscles')

    def __str__(self): return self.name

class MuscleBoneAttachment(models.Model):
    # --- FIX CRÍTICO: Definindo ID como UUID explicitamente ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    muscle = models.ForeignKey(Muscle, on_delete=models.CASCADE)
    landmark = models.ForeignKey(BoneLandmark, on_delete=models.CASCADE)
    attachment_type = models.CharField(max_length=50, choices=AttachmentType.choices)

    def __str__(self): return f"{self.muscle.name} -> {self.landmark.name}"

# =========================================================
# 4. KNOWLEDGE HUB: CINESIOLOGIA (Ação Muscular)
# =========================================================

class MuscleAction(models.Model):
    """
    Define explicitamente o que cada músculo faz em uma articulação.
    Ex: Bíceps -> Flexão do Cotovelo -> Agonista Primário.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    muscle = models.ForeignKey(Muscle, on_delete=models.CASCADE, related_name='actions')
    movement = models.ForeignKey(JointMovement, on_delete=models.CASCADE, related_name='muscles_involved')
    
    role = models.CharField(max_length=100, choices=MuscleRole.choices)
    
    notes = models.TextField(
        blank=True, 
        help_text="Detalhes biomecânicos. Ex: 'Maior torque a 90 graus', 'Ativo apenas com supinação'."
    )

    class Meta:
        unique_together = ('muscle', 'movement', 'role')

    def __str__(self): return f"{self.muscle.name} - {self.movement.name} ({self.get_role_display()})"

# =========================================================
# 5. KNOWLEDGE HUB: SEGURANÇA E PATOLOGIA
# =========================================================

class Pathology(models.Model):
    """
    Catálogo de condições médicas e ortopédicas.
    Ex: Hérnia de Disco Lombar, Condromalácia, Hipertensão.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    icd_code = models.CharField(max_length=20, blank=True, null=True, help_text="Código CID-10/11.")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.name

class MovementContraindication(models.Model):
    """
    Regras de ouro de segurança.
    Se o usuário tem Patologia X -> Evitar Movimento Y com Severidade Z.
    """
    class Severity(models.TextChoices):
        ABSOLUTE = 'ABSOLUTE', _('Contraindicação Absoluta (PROIBIDO)')
        RELATIVE = 'RELATIVE', _('Contraindicação Relativa (ADAPTAR)')
        WARNING = 'WARNING', _('Atenção/Monitorar Dor')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pathology = models.ForeignKey(Pathology, on_delete=models.CASCADE, related_name='contraindications')
    movement = models.ForeignKey(JointMovement, on_delete=models.CASCADE, related_name='contraindications')
    
    severity = models.CharField(max_length=50, choices=Severity.choices, default=Severity.WARNING)
    risk_description = models.TextField(help_text="Ex: Aumenta a pressão intradiscal posterior.")

    def __str__(self): return f"{self.pathology.name} -> {self.movement.name} ({self.severity})"

# =========================================================
# 6. KNOWLEDGE HUB: EXERCÍCIOS
# =========================================================

class Exercise(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = 'BEGINNER', _('Iniciante')
        INTERMEDIATE = 'INTERMEDIATE', _('Intermediário')
        ADVANCED = 'ADVANCED', _('Avançado')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)
    difficulty = models.CharField(max_length=50, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    equipment_needed = models.CharField(max_length=255, blank=True, null=True)
    
    muscles = models.ManyToManyField(Muscle, through='ExerciseMuscle', related_name='exercises')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_exercises')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.name

class ExerciseMuscle(models.Model):
    # --- FIX CRÍTICO: Definindo ID como UUID explicitamente ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    muscle = models.ForeignKey(Muscle, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=MuscleRole.choices, default=MuscleRole.PRIME_AGONIST)

    class Meta:
        unique_together = ('exercise', 'muscle')

# =========================================================
# 7. MÓDULO DE RESISTÊNCIA (LEGADO WELLNESS360)
# =========================================================

class ResistanceRoutine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    goal = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.name

class ResistanceWorkout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    routine = models.ForeignKey(ResistanceRoutine, on_delete=models.CASCADE, related_name='workouts')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"{self.name} ({self.routine.name})"

class WorkoutSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workout = models.ForeignKey(ResistanceWorkout, on_delete=models.CASCADE, related_name='sets')
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    order_index = models.PositiveIntegerField(default=0)
    sets = models.PositiveIntegerField()
    reps = models.CharField(max_length=50)
    load_kg = models.FloatField(null=True, blank=True)
    rest_seconds = models.PositiveIntegerField(null=True, blank=True)
    rpe = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order_index']

    def __str__(self): return f"{self.exercise.name} ({self.sets}x{self.reps})"

# =========================================================
# 8. ORQUESTRADOR VITALIA (BEM-ESTAR INTEGRAL)
# =========================================================

class WellnessPlan(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Rascunho (IA Gerando)')
        PENDING_APPROVAL = 'PENDING_APPROVAL', _('Aguardando Aprovação Profissional')
        ACTIVE = 'ACTIVE', _('Ativo (Em Execução)')
        COMPLETED = 'COMPLETED', _('Concluído')
        ARCHIVED = 'ARCHIVED', _('Arquivado')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wellness_plans')
    responsible_professional = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='managed_plans')
    title = models.CharField(max_length=255)
    goals = models.TextField()
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.DRAFT)
    ai_generation_metadata = models.JSONField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    resistance_routine = models.ForeignKey(ResistanceRoutine, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"Plano {self.title} - {self.participant.username}"

class DailySchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(WellnessPlan, on_delete=models.CASCADE, related_name='schedules')
    day_label = models.CharField(max_length=100)
    day_index = models.IntegerField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['day_index']
        unique_together = ('plan', 'day_index')

    def __str__(self): return f"{self.day_label} - {self.plan.title}"

class PrescribedActivity(models.Model):
    class ActivityType(models.TextChoices):
        RESISTANCE_WORKOUT = 'RESISTANCE', _('Treino de Força (Módulo Especializado)')
        CARDIO_TIME = 'CARDIO_TIME', _('Cardio (Duração)')
        CARDIO_DISTANCE = 'CARDIO_DISTANCE', _('Cardio (Distância)')
        FLEXIBILITY = 'FLEXIBILITY', _('Alongamento/Mobilidade')
        MINDFULNESS = 'MINDFULNESS', _('Meditação/Respiração')
        NUTRITION_HABIT = 'NUTRITION', _('Hábito Nutricional')
        CUSTOM = 'CUSTOM', _('Personalizado')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(DailySchedule, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=255)
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices)
    order_index = models.PositiveIntegerField(default=0)
    resistance_ref = models.ForeignKey(ResistanceWorkout, on_delete=models.SET_NULL, null=True, blank=True)
    flexible_data = models.JSONField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['order_index']

    def __str__(self): return f"{self.title} ({self.activity_type})"

# =========================================================
# 9. DATA VAULT: DADOS CLÍNICOS E AVALIAÇÕES
# =========================================================

class MedicalExam(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medical_exams')
    title = models.CharField(max_length=255)
    exam_date = models.DateField()
    laboratory_name = models.CharField(max_length=255, blank=True)
    results_structured = models.JSONField(default=dict)
    attachment = models.FileField(upload_to=secure_file_upload_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PhysicalEvaluation(models.Model):
    class Type(models.TextChoices):
        BODY_COMPOSITION = 'COMPOSICAO_CORPORAL', _('Composição Corporal')
        POSTURAL = 'AVALIACAO_POSTURAL', _('Avaliação Postural')
        FUNCTIONAL = 'AVALIACAO_FUNCIONAL', _('Avaliação Funcional')
        ANAMNESIS = 'ANAMNESE', _('Anamnese & Objetivos')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluations_received')
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='evaluations_performed')
    evaluation_type = models.CharField(max_length=50, choices=Type.choices)
    date = models.DateTimeField(auto_now_add=True)
    measurements_data = models.JSONField(default=dict)
    results_data = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    is_finalized = models.BooleanField(default=False)

    def __str__(self): return f"Avaliação {self.evaluation_type} - {self.patient.username}"