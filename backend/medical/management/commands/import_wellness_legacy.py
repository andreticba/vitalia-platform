# backend/medical/management/commands/import_wellness_legacy.py em 2025-12-14 11:48

import psycopg2
import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from medical.models import (
    Bone, BoneLandmark, Joint, JointBone, Muscle, MuscleBoneAttachment,
    Exercise, ExerciseMuscle, ResistanceRoutine, ResistanceWorkout, WorkoutSet,
    BodySegment, SkeletonDivision, BoneType, SpecificRegionMuscle, MuscleRole
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Importa dados do banco legado Wellness360 para a Vitalia.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando ETL do Legacy Wellness360...'))

        # Configuração da conexão com o banco legado
        db_settings = settings.DATABASES['default']
        conn_params = {
            "dbname": "wellness_legacy",
            "user": db_settings['USER'],
            "password": db_settings['PASSWORD'],
            "host": db_settings['HOST'],
            "port": db_settings['PORT'],
        }

        try:
            legacy_conn = psycopg2.connect(**conn_params)
            cursor = legacy_conn.cursor()
            self.stdout.write(self.style.SUCCESS('Conectado ao banco wellness_legacy com sucesso.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Falha ao conectar no banco legado: {e}'))
            return

        # Dicionários para mapear ID Antigo (Prisma CUID) -> Objeto Novo (Django UUID)
        # Isso é fundamental para recriar os relacionamentos
        self.id_map = {
            'users': {},
            'bones': {},
            'joints': {},
            'muscles': {},
            'exercises': {},
            'routines': {},
            'workouts': {}
        }

        try:
            with transaction.atomic():
                self.import_users(cursor)
                self.import_bones(cursor)
                self.import_joints(cursor)
                self.import_muscles(cursor)
                self.import_exercises(cursor)
                self.import_resistance_plans(cursor)
                
            self.stdout.write(self.style.SUCCESS('--------------------------------------------------'))
            self.stdout.write(self.style.SUCCESS('IMPORTAÇÃO CONCLUÍDA COM SUCESSO!'))
            self.stdout.write(self.style.SUCCESS('--------------------------------------------------'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro crítico durante a importação: {e}'))
            # A transação atômica fará rollback automático aqui
        finally:
            legacy_conn.close()

    def _normalize_enum(self, value, default=None):
        """Helper para limpar strings de Enums do Prisma"""
        if not value:
            return default
        # Prisma às vezes retorna em minúsculo ou com aspas
        return value.upper().replace("'", "")

    def import_users(self, cursor):
        self.stdout.write("Importando Usuários (Autores)...")
        # Ajuste o nome da tabela se necessário (ex: "users" ou "User")
        cursor.execute('SELECT id, email, name FROM "users"') 
        rows = cursor.fetchall()
        
        # Usuário System para fallback
        system_user, _ = User.objects.get_or_create(username="legacy_system", defaults={"email": "system@vitalia.ai"})
        
        for row in rows:
            old_id, email, name = row
            # Tenta encontrar usuário existente pelo email, ou usa o system
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Se não existe, não criamos usuário novo para não poluir auth, 
                # atribuímos ao system ou criamos um placeholder inativo
                user, _ = User.objects.get_or_create(username=email.split('@')[0], defaults={
                    "email": email,
                    "is_active": False 
                })
            
            self.id_map['users'][old_id] = user
        self.stdout.write(f"  - {len(rows)} usuários processados.")

    def import_bones(self, cursor):
        self.stdout.write("Importando Ossos...")
        # Nota: Aspas duplas nas colunas camelCase do Prisma são obrigatórias no Postgres
        cursor.execute('SELECT id, name, "scientificName", division, "boneType", "bodySegment", description FROM "bones"')
        rows = cursor.fetchall()
        
        count = 0
        for row in rows:
            old_id, name, sci_name, division, b_type, segment, desc = row
            
            bone = Bone.objects.create(
                name=name,
                scientific_name=sci_name,
                division=self._normalize_enum(division, SkeletonDivision.AXIAL),
                bone_type=self._normalize_enum(b_type, BoneType.LONG),
                body_segment=self._normalize_enum(segment, BodySegment.FULL_BODY),
                description=desc or ""
            )
            self.id_map['bones'][old_id] = bone
            count += 1
            
            # Importar Landmarks deste osso
            cursor.execute('SELECT id, name, description FROM "bone_landmarks" WHERE "boneId" = %s', (old_id,))
            landmarks = cursor.fetchall()
            for l_row in landmarks:
                _, l_name, l_desc = l_row
                BoneLandmark.objects.create(bone=bone, name=l_name, description=l_desc or "")
                
        self.stdout.write(f"  - {count} ossos importados.")

    def import_joints(self, cursor):
        self.stdout.write("Importando Articulações...")
        cursor.execute('SELECT id, name, "structuralType", description FROM "joints"')
        rows = cursor.fetchall()
        
        for row in rows:
            old_id, name, struct_type, desc = row
            
            joint = Joint.objects.create(
                name=name,
                structural_type=self._normalize_enum(struct_type, 'SINOVIAL'),
                description=desc or ""
            )
            self.id_map['joints'][old_id] = joint
            
            # Relacionamento Joint -> Bone
            cursor.execute('SELECT "boneId", role FROM "joint_bones" WHERE "jointId" = %s', (old_id,))
            joint_bones = cursor.fetchall()
            for jb in joint_bones:
                old_bone_id, role = jb
                if old_bone_id in self.id_map['bones']:
                    JointBone.objects.create(
                        joint=joint,
                        bone=self.id_map['bones'][old_bone_id],
                        role=role or ""
                    )

    def import_muscles(self, cursor):
        self.stdout.write("Importando Músculos...")
        cursor.execute('SELECT id, name, "scientificName", "bodySegment", "specificRegion", origin, insertion, description, "createdById" FROM "muscles"')
        rows = cursor.fetchall()
        
        for row in rows:
            old_id, name, sci_name, segment, region, origin, insertion, desc, creator_id = row
            
            creator = self.id_map['users'].get(creator_id)
            
            muscle = Muscle.objects.create(
                name=name,
                scientific_name=sci_name,
                body_segment=self._normalize_enum(segment, BodySegment.FULL_BODY),
                specific_region=self._normalize_enum(region, SpecificRegionMuscle.FULL_BODY),
                origin_text=origin or "",
                insertion_text=insertion or "",
                description=desc or "",
                created_by=creator
            )
            self.id_map['muscles'][old_id] = muscle
            
        self.stdout.write(f"  - {len(rows)} músculos importados.")

    def import_exercises(self, cursor):
        self.stdout.write("Importando Exercícios...")
        cursor.execute('SELECT id, name, description, difficulty, "createdById" FROM "exercises"')
        rows = cursor.fetchall()
        
        for row in rows:
            old_id, name, desc, difficulty, creator_id = row
            creator = self.id_map['users'].get(creator_id)
            
            exercise = Exercise.objects.create(
                name=name,
                description=desc or "",
                difficulty=self._normalize_enum(difficulty, 'BEGINNER'),
                created_by=creator
            )
            self.id_map['exercises'][old_id] = exercise
            
            # Relacionamento Exercício -> Músculo
            cursor.execute('SELECT "muscleId", "roleInExercise" FROM "exercise_muscles" WHERE "exerciseId" = %s', (old_id,))
            ex_muscles = cursor.fetchall()
            for em in ex_muscles:
                old_muscle_id, role = em
                if old_muscle_id in self.id_map['muscles']:
                    ExerciseMuscle.objects.create(
                        exercise=exercise,
                        muscle=self.id_map['muscles'][old_muscle_id],
                        role=self._normalize_enum(role, MuscleRole.PRIME_AGONIST)
                    )
        self.stdout.write(f"  - {len(rows)} exercícios importados.")

    def import_resistance_plans(self, cursor):
        self.stdout.write("Importando Rotinas de Treino (Legacy)...")
        # Import TrainingPlan -> ResistanceRoutine
        cursor.execute('SELECT id, name, goal, "creatorId" FROM "training_plans"')
        plans = cursor.fetchall()
        
        for plan_row in plans:
            old_plan_id, name, goal, creator_id = plan_row
            creator = self.id_map['users'].get(creator_id)
            
            routine = ResistanceRoutine.objects.create(
                name=name,
                goal=goal or "",
                created_by=creator
            )
            self.id_map['routines'][old_plan_id] = routine
            
            # Import Workouts -> ResistanceWorkout
            cursor.execute('SELECT id, name, description FROM "workouts" WHERE "trainingPlanId" = %s', (old_plan_id,))
            workouts = cursor.fetchall()
            
            for wk_row in workouts:
                old_wk_id, wk_name, wk_desc = wk_row
                workout = ResistanceWorkout.objects.create(
                    routine=routine,
                    name=wk_name,
                    description=wk_desc or ""
                )
                
                # Import WorkoutExercises -> WorkoutSet
                cursor.execute(
                    'SELECT "exerciseId", "orderIndex", sets, reps, "loadKg", "restSeconds", notes '
                    'FROM "workout_exercises" WHERE "workoutId" = %s ORDER BY "orderIndex"', 
                    (old_wk_id,)
                )
                exercises = cursor.fetchall()
                
                for ex_row in exercises:
                    old_ex_id, order, sets, reps, load, rest, notes = ex_row
                    
                    if old_ex_id in self.id_map['exercises']:
                        WorkoutSet.objects.create(
                            workout=workout,
                            exercise=self.id_map['exercises'][old_ex_id],
                            order_index=order,
                            sets=sets,
                            reps=str(reps), # Converte int/string mixed para string
                            load_kg=float(load) if load else None,
                            rest_seconds=rest,
                            notes=notes or ""
                        )
        
        self.stdout.write(f"  - {len(plans)} rotinas de treino importadas.")