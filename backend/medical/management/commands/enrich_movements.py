# backend/medical/management/commands/enrich_movements.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Joint, JointMovement

class Command(BaseCommand):
    help = 'Enriquece a Cinesiologia: Define movimentos articulares, Planos e Amplitudes (ROM).'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando mapeamento cinesiológico...'))

        # Lista Mestra de Movimentos
        # Formato: (Nome da Articulação, Nome do Movimento, ROM Médio (Graus), Plano)
        # Notas: ROM baseados em Norkin & White / Kapandji. NULL usado para movimentos complexos/deslizamentos.
        movements_data = [
            # ========================================================
            # 1. MEMBRO SUPERIOR
            # ========================================================
            
            # --- Ombro (Glenoumeral) ---
            ("Articulação Glenoumeral (Ombro)", "Flexão", 180, "Sagital"),
            ("Articulação Glenoumeral (Ombro)", "Extensão", 60, "Sagital"),
            ("Articulação Glenoumeral (Ombro)", "Abdução", 180, "Frontal"),
            ("Articulação Glenoumeral (Ombro)", "Adução", 50, "Frontal"), # Hiperadução/Adução horizontal
            ("Articulação Glenoumeral (Ombro)", "Rotação Medial (Interna)", 70, "Transverso"),
            ("Articulação Glenoumeral (Ombro)", "Rotação Lateral (Externa)", 90, "Transverso"),
            ("Articulação Glenoumeral (Ombro)", "Abdução Horizontal", 45, "Transverso"),
            ("Articulação Glenoumeral (Ombro)", "Adução Horizontal", 135, "Transverso"),
            ("Articulação Glenoumeral (Ombro)", "Circundução", None, "Multiplanar"),

            # --- Cíngulo Escapular (Esternoclavicular/Acromioclavicular) ---
            # Movimentos funcionais da Escápula
            ("Articulação Esternoclavicular", "Elevação", 45, "Frontal"),
            ("Articulação Esternoclavicular", "Depressão", 10, "Frontal"),
            ("Articulação Esternoclavicular", "Protração (Abdução)", 15, "Transverso"),
            ("Articulação Esternoclavicular", "Retração (Adução)", 15, "Transverso"),
            ("Articulação Esternoclavicular", "Rotação Posterior", 30, "Sagital"), # Durante flexão do braço

            # --- Cotovelo ---
            ("Articulação do Cotovelo", "Flexão", 150, "Sagital"),
            ("Articulação do Cotovelo", "Extensão", 0, "Sagital"), # Hiperextensão possível (-5 a -10)

            # --- Antebraço (Radioulnar) ---
            ("Articulação Radioulnar Proximal", "Pronação", 80, "Transverso"),
            ("Articulação Radioulnar Proximal", "Supinação", 80, "Transverso"),

            # --- Punho (Radiocarpal) ---
            ("Articulação Radiocarpal (Punho)", "Flexão", 80, "Sagital"),
            ("Articulação Radiocarpal (Punho)", "Extensão", 70, "Sagital"),
            ("Articulação Radiocarpal (Punho)", "Desvio Radial (Abdução)", 20, "Frontal"),
            ("Articulação Radiocarpal (Punho)", "Desvio Ulnar (Adução)", 30, "Frontal"),

            # --- Polegar (Carpometacarpal) ---
            ("Articulação Carpometacarpal do Polegar", "Flexão", 15, "Frontal"), # Plano modificado no polegar
            ("Articulação Carpometacarpal do Polegar", "Extensão", 20, "Frontal"),
            ("Articulação Carpometacarpal do Polegar", "Abdução", 70, "Sagital"),
            ("Articulação Carpometacarpal do Polegar", "Adução", 0, "Sagital"),
            ("Articulação Carpometacarpal do Polegar", "Oposição", None, "Multiplanar"),

            # ========================================================
            # 2. MEMBRO INFERIOR
            # ========================================================

            # --- Quadril (Coxofemoral) ---
            ("Articulação Coxofemoral (Quadril)", "Flexão", 120, "Sagital"),
            ("Articulação Coxofemoral (Quadril)", "Extensão", 30, "Sagital"),
            ("Articulação Coxofemoral (Quadril)", "Abdução", 45, "Frontal"),
            ("Articulação Coxofemoral (Quadril)", "Adução", 30, "Frontal"),
            ("Articulação Coxofemoral (Quadril)", "Rotação Medial (Interna)", 35, "Transverso"),
            ("Articulação Coxofemoral (Quadril)", "Rotação Lateral (Externa)", 45, "Transverso"),
            ("Articulação Coxofemoral (Quadril)", "Circundução", None, "Multiplanar"),

            # --- Joelho ---
            ("Articulação do Joelho", "Flexão", 135, "Sagital"),
            ("Articulação do Joelho", "Extensão", 0, "Sagital"),
            ("Articulação do Joelho", "Rotação Medial", 10, "Transverso"), # Só ocorre com joelho flexionado
            ("Articulação do Joelho", "Rotação Lateral", 30, "Transverso"), # Só ocorre com joelho flexionado

            # --- Tornozelo (Talocrural) ---
            ("Articulação Talocrural (Tornozelo)", "Dorsiflexão", 20, "Sagital"),
            ("Articulação Talocrural (Tornozelo)", "Flexão Plantar", 50, "Sagital"),

            # --- Pé (Subtalar/Transversa) ---
            ("Articulação Subtalar", "Inversão", 35, "Frontal"), # Movimento combinado, predominância frontal
            ("Articulação Subtalar", "Eversão", 15, "Frontal"),

            # ========================================================
            # 3. COLUNA E CABEÇA (AXIAL)
            # ========================================================

            # --- Cervical (Atlanto-occipital + Intervertebrais) ---
            ("Articulação Atlanto-occipital", "Flexão (Cabeça)", 10, "Sagital"), # Movimento do "Sim"
            ("Articulação Atlanto-occipital", "Extensão (Cabeça)", 25, "Sagital"),
            ("Articulação Atlanto-axial", "Rotação (Cabeça)", 45, "Transverso"), # Movimento do "Não"

            ("Discos Intervertebrais", "Flexão Cervical", 45, "Sagital"), # Segmento C2-C7
            ("Discos Intervertebrais", "Extensão Cervical", 45, "Sagital"),
            ("Discos Intervertebrais", "Flexão Lateral Cervical", 45, "Frontal"),
            ("Discos Intervertebrais", "Rotação Cervical", 60, "Transverso"),

            # --- Toracolombar ---
            ("Discos Intervertebrais", "Flexão Toracolombar", 80, "Sagital"), # T1-S1
            ("Discos Intervertebrais", "Extensão Toracolombar", 25, "Sagital"),
            ("Discos Intervertebrais", "Flexão Lateral Toracolombar", 35, "Frontal"),
            ("Discos Intervertebrais", "Rotação Torácica", 45, "Transverso"), # Lombar roda muito pouco (5 graus)

            # --- ATM (Mandíbula) ---
            ("Articulação Temporomandibular (ATM)", "Depressão (Abrir)", 40, "Sagital"), # mm de abertura
            ("Articulação Temporomandibular (ATM)", "Elevação (Fechar)", 0, "Sagital"),
            ("Articulação Temporomandibular (ATM)", "Protrusão", 5, "Transverso"),
            ("Articulação Temporomandibular (ATM)", "Retração", 5, "Transverso"),
            ("Articulação Temporomandibular (ATM)", "Lateralização", 10, "Frontal"),
        ]

        success_count = 0
        error_count = 0

        with transaction.atomic():
            for joint_name, mov_name, rom, plane in movements_data:
                try:
                    joint = Joint.objects.get(name=joint_name)
                    
                    # Update ou Create
                    obj, created = JointMovement.objects.update_or_create(
                        joint=joint,
                        name=mov_name,
                        defaults={
                            'rom_degrees': rom,
                            'plane': plane
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"Criado: {mov_name} em {joint_name}")
                    
                    success_count += 1

                except Joint.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Articulação não encontrada: {joint_name}"))
                    error_count += 1

        self.stdout.write(self.style.SUCCESS('--------------------------------------'))
        self.stdout.write(self.style.SUCCESS(f'Movimentos Cinesiológicos processados: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Falhas: {error_count}'))
        self.stdout.write(self.style.SUCCESS('Base de Biomecânica de Movimento: Carregada.'))