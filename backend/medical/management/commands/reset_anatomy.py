# backend/medical/management/commands/reset_anatomy.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import (
    # Anatomia Base
    Bone, Joint, Muscle, BoneLandmark,
    # Conexões e Estruturas
    JointStructure, JointMovement, JointBone, 
    MuscleAction, MuscleBoneAttachment,
    # Exercícios e Treinos
    Exercise, ExerciseMuscle,
    ResistanceRoutine, ResistanceWorkout, WorkoutSet,
    # Segurança e Patologia (NOVO)
    Pathology, MovementContraindication
)

class Command(BaseCommand):
    help = 'SANITIZAÇÃO TOTAL: Apaga todo o Knowledge Hub (Anatomia, Exercícios, Patologias) para reconstrução limpa.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.ERROR('⚠️  ATENÇÃO: Iniciando PROTOCOLO DE DESTRUIÇÃO do Knowledge Hub...'))
        
        try:
            with transaction.atomic():
                # 1. Camada de Segurança (Patologias dependem de Movimentos, mas Movimentos dependem de Juntas)
                # Apagamos as contraindicações primeiro para liberar Movimentos e Patologias
                self._wipe(MovementContraindication, "Contraindicações de Movimento")
                self._wipe(Pathology, "Patologias")

                # 2. Cinesiologia e Estruturas
                self._wipe(MuscleAction, "Ações Musculares")
                self._wipe(JointStructure, "Estruturas Articulares (Ligamentos/Meniscos)")
                self._wipe(JointMovement, "Movimentos Articulares")
                
                # 3. Conexões Anatômicas (Tabelas Pivot)
                self._wipe(JointBone, "Conexões Articulação-Osso")
                self._wipe(MuscleBoneAttachment, "Fixações Musculares (Origem/Inserção)")
                
                # 4. Dados de Treino (Legacy - Remove dependências de Exercício)
                self._wipe(WorkoutSet, "Séries de Treino") # Apaga os sets primeiro
                self._wipe(ResistanceWorkout, "Treinos (Workouts)")
                self._wipe(ResistanceRoutine, "Rotinas de Resistência")
                
                # 5. Exercícios e Músculos
                self._wipe(ExerciseMuscle, "Associações Exercício-Músculo")
                self._wipe(Exercise, "Catálogo de Exercícios")
                self._wipe(Muscle, "Músculos")
                
                # 6. Anatomia Estrutural (A Base)
                self._wipe(BoneLandmark, "Acidentes Ósseos (Landmarks)") # Crítico apagar antes dos ossos
                self._wipe(Joint, "Articulações")
                self._wipe(Bone, "Ossos")

            self.stdout.write(self.style.SUCCESS('✅ SANITIZAÇÃO CONCLUÍDA. O sistema está limpo e pronto para o Seed.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ ERRO CRÍTICO DURANTE O RESET: {e}'))
            raise e

    def _wipe(self, model_class, label):
        count = model_class.objects.count()
        if count > 0:
            model_class.objects.all().delete()
            self.stdout.write(f"   -> Apagados {count} registros de {label}.")
        else:
            self.stdout.write(f"   -> {label} já estava limpo.")