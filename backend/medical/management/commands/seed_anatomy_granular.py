# backend/medical/management/commands/seed_anatomy_granular.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Bone, SkeletonDivision, BoneType, BodySegment

class Command(BaseCommand):
    help = 'Explosão Anatômica: Expande grupos genéricos em ossos individuais (Total ~206).'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando Explosão Anatômica (Granularidade Máxima)...'))

        # Lista de Ossos Individuais
        # (Nome, Nome Científico, Divisão, Tipo, Segmento)
        granular_bones = []

        # ---------------------------------------------------------
        # 1. COLUNA VERTEBRAL (Explosão de C1 a Cóccix)
        # ---------------------------------------------------------
        # Cervicais (C1 e C2 já existem, vamos garantir e adicionar C3-C7)
        granular_bones.append(("Atlas (C1)", "Atlas", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))
        granular_bones.append(("Áxis (C2)", "Axis", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))
        for i in range(3, 8):
            granular_bones.append((f"Vértebra Cervical C{i}", f"Vertebra cervicalis C{i}", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))

        # Torácicas (T1-T12)
        for i in range(1, 13):
            granular_bones.append((f"Vértebra Torácica T{i}", f"Vertebra thoracica T{i}", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))

        # Lombares (L1-L5) - CRÍTICO PARA PATOLOGIAS
        for i in range(1, 6):
            granular_bones.append((f"Vértebra Lombar L{i}", f"Vertebra lumbalis L{i}", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))

        # Sacro e Cóccix
        granular_bones.append(("Sacro", "Os sacrum", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))
        granular_bones.append(("Cóccix", "Os coccygis", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))

        # ---------------------------------------------------------
        # 2. CAIXA TORÁCICA (Explosão das Costelas)
        # ---------------------------------------------------------
        granular_bones.append(("Esterno", "Sternum", SkeletonDivision.AXIAL, BoneType.FLAT, BodySegment.TRUNK))
        
        # Costelas 1 a 12
        for i in range(1, 13):
            b_type = BoneType.FLAT
            if i <= 7:
                desc = "Costela Verdadeira"
            elif i <= 10:
                desc = "Costela Falsa"
            else:
                desc = "Costela Flutuante"
            
            granular_bones.append((f"Costela {i}", f"Costa {i}", SkeletonDivision.AXIAL, b_type, BodySegment.TRUNK))

        # ---------------------------------------------------------
        # 3. MÃO (Explosão de Metacarpos e Falanges)
        # ---------------------------------------------------------
        # Carpos já existem no seed anterior, vamos manter.
        # Metacarpos I-V
        romanos = ["I", "II", "III", "IV", "V"]
        for idx, r in enumerate(romanos):
            granular_bones.append((f"Metacarpo {r}", f"Os metacarpale {r}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.HAND))
            
            # Falanges (O Polegar "I" só tem Proximal e Distal)
            granular_bones.append((f"Falange Proximal da Mão {r}", f"Phalanx proximalis manus {r}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.HAND))
            
            if r != "I": # Polegar não tem média
                granular_bones.append((f"Falange Média da Mão {r}", f"Phalanx media manus {r}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.HAND))
            
            granular_bones.append((f"Falange Distal da Mão {r}", f"Phalanx distalis manus {r}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.HAND))

        # ---------------------------------------------------------
        # 4. PÉ (Explosão de Metatarsos e Falanges)
        # ---------------------------------------------------------
        # Tarsos já existem.
        # Metatarsos I-V
        for idx, r in enumerate(romanos):
            granular_bones.append((f"Metatarso {r}", f"Os metatarsale {r}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.FOOT))
            
            # Falanges (O Hálux "I" só tem Proximal e Distal)
            granular_bones.append((f"Falange Proximal do Pé {r}", f"Phalanx proximalis pedis {r}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.FOOT))
            
            if r != "I": # Hálux não tem média
                granular_bones.append((f"Falange Média do Pé {r}", f"Phalanx media pedis {r}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.FOOT))
            
            granular_bones.append((f"Falange Distal do Pé {r}", f"Phalanx distalis pedis {r}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.FOOT))

        # ---------------------------------------------------------
        # 5. EXECUÇÃO
        # ---------------------------------------------------------
        created_count = 0
        updated_count = 0

        # Lista de grupos genéricos antigos para remover (limpeza)
        deprecated_groups = [
            "Vértebras Cervicais (C3-C7)",
            "Vértebras Torácicas (T1-T12)",
            "Vértebras Lombares (L1-L5)",
            "Costelas Verdadeiras (1-7)",
            "Costelas Falsas (8-10)",
            "Costelas Flutuantes (11-12)",
            "Metacarpos (I-V)",
            "Metatarsos (I-V)",
            "Falanges Proximais (Mão)", "Falanges Médias (Mão)", "Falanges Distais (Mão)",
            "Falanges Proximais (Pé)", "Falanges Médias (Pé)", "Falanges Distais (Pé)"
        ]

        with transaction.atomic():
            # 1. Remover grupos obsoletos para evitar confusão
            deleted, _ = Bone.objects.filter(name__in=deprecated_groups).delete()
            if deleted > 0:
                self.stdout.write(self.style.NOTICE(f'Grupos genéricos removidos: {deleted}'))

            # 2. Criar/Atualizar Ossos Granulares
            for name, sci_name, div, b_type, segment in granular_bones:
                obj, created = Bone.objects.update_or_create(
                    name=name,
                    defaults={
                        'scientific_name': sci_name,
                        'division': div,
                        'bone_type': b_type,
                        'body_segment': segment
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Explosão Concluída!'))
        self.stdout.write(self.style.SUCCESS(f'Novos Ossos Individuais: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total de Ossos no Knowledge Hub: {Bone.objects.count()}'))