# backend/medical/management/commands/reset_anatomy.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import (
    Bone, Joint, Muscle, 
    JointStructure, JointMovement, 
    MuscleAction, MuscleBoneAttachment, JointBone,
    Exercise, ExerciseMuscle,
    ResistanceRoutine # Importante para o Cascade
)

class Command(BaseCommand):
    help = 'LIMPEZA PROFUNDA: Apaga Anatomia, Exercícios e Rotinas de Treino para recarga limpa.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.ERROR('⚠️  ATENÇÃO: Iniciando sanitização total do Medical Hub...'))
        
        with transaction.atomic():
            # 1. Limpar Cinesiologia e Estruturas
            self.stdout.write('Apagando Ações Musculares e Estruturas...')
            MuscleAction.objects.all().delete()
            JointStructure.objects.all().delete()
            JointMovement.objects.all().delete()
            
            # 2. Limpar Conexões Anatômicas
            self.stdout.write('Apagando Conexões (JointBone / MuscleAttachments)...')
            JointBone.objects.all().delete()
            MuscleBoneAttachment.objects.all().delete()
            
            # 3. Limpar Treinos (CRÍTICO: Libera os Exercícios para deleção)
            # Ao deletar a Rotina, o Django deleta em cascata: Workouts -> WorkoutSets
            self.stdout.write('Apagando Histórico de Treinos (Rotinas/Workouts/Sets)...')
            ResistanceRoutine.objects.all().delete()
            
            # 4. Limpar Exercícios e Músculos
            # Agora podemos deletar exercícios pois não há Sets apontando para eles
            self.stdout.write('Apagando Catálogo de Exercícios e Associações...')
            ExerciseMuscle.objects.all().delete()
            Exercise.objects.all().delete()
            
            self.stdout.write('Apagando Entidades Anatômicas (Músculos, Articulações, Ossos)...')
            Muscle.objects.all().delete()
            Joint.objects.all().delete()
            Bone.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('✅ Base Sanitizada (0 registros de Anatomia/Treino). Pronta para Seed.'))