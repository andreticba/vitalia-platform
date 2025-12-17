# backend/medical/management/commands/repair_granular_landmarks.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Bone, BoneLandmark

class Command(BaseCommand):
    help = 'Propaga landmarks comuns para os novos ossos granulares (Ex: Processo Espinhoso em todas as vértebras).'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Reparando Landmarks Granulares...'))

        # Definição de Padrões (Regex-like)
        # Se o osso começa com X, ele deve ter os landmarks Y e Z.
        patterns = [
            # --- COLUNA VERTEBRAL ---
            ("Vértebra Cervical", ["Corpo Vertebral", "Processo Espinhoso", "Processo Transverso", "Forame Transversário", "Lâmina", "Pedículo"]),
            ("Vértebra Torácica", ["Corpo Vertebral", "Processo Espinhoso", "Processo Transverso", "Fóvea Costal Superior", "Fóvea Costal Inferior", "Lâmina", "Pedículo"]),
            ("Vértebra Lombar",   ["Corpo Vertebral", "Processo Espinhoso", "Processo Transverso", "Processo Mamilar", "Processo Acessório", "Lâmina", "Pedículo"]),
            
            # --- COSTELAS ---
            ("Costela", ["Cabeça", "Colo", "Tubérculo", "Ângulo", "Corpo", "Extremidade Anterior"]),
            
            # --- MÃOS ---
            ("Metacarpo", ["Base", "Corpo", "Cabeça"]),
            ("Falange Proximal da Mão", ["Base", "Corpo", "Cabeça"]),
            ("Falange Média da Mão",    ["Base", "Corpo", "Cabeça"]),
            ("Falange Distal da Mão",   ["Base", "Corpo", "Tuberosidade Distal"]),
            
            # --- PÉS ---
            ("Metatarso", ["Base", "Corpo", "Cabeça"]),
            ("Falange Proximal do Pé", ["Base", "Corpo", "Cabeça"]),
            ("Falange Média do Pé",    ["Base", "Corpo", "Cabeça"]),
            ("Falange Distal do Pé",   ["Base", "Corpo", "Tuberosidade Distal"]),
        ]

        count = 0
        with transaction.atomic():
            for name_pattern, landmarks in patterns:
                # Busca todos os ossos que dão match (ex: todas as Lombares)
                bones = Bone.objects.filter(name__icontains=name_pattern)
                
                for bone in bones:
                    for lm_name in landmarks:
                        _, created = BoneLandmark.objects.get_or_create(
                            bone=bone,
                            name=lm_name,
                            defaults={'description': f"Landmark padrão para {bone.name}"}
                        )
                        if created: count += 1

        self.stdout.write(self.style.SUCCESS(f'Reparo concluído! {count} landmarks recriados nos ossos detalhados.'))