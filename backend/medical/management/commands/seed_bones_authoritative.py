# backend/medical/management/commands/seed_bones_authoritative.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Bone, SkeletonDivision, BoneType, BodySegment

class Command(BaseCommand):
    help = 'Seed Autoritativo: Cria os ~206 ossos do corpo humano com dados taxonômicos blindados.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando Carga Autoritativa do Esqueleto Humano (Source of Truth)...'))

        bones_payload = []

        # ==============================================================================
        # 1. ESQUELETO AXIAL (CRÂNIO, COLUNA, TÓRAX)
        # ==============================================================================

        # --- CRÂNIO (NEUROCRÂNIO) ---
        bones_payload.extend([
            ("Osso Frontal", "Os frontale", SkeletonDivision.AXIAL, BoneType.FLAT, BodySegment.HEAD_NECK),
            ("Osso Parietal", "Os parietale", SkeletonDivision.AXIAL, BoneType.FLAT, BodySegment.HEAD_NECK),
            ("Osso Temporal", "Os temporale", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Osso Occipital", "Os occipitale", SkeletonDivision.AXIAL, BoneType.FLAT, BodySegment.HEAD_NECK),
            ("Osso Esfenoide", "Os sphenoidale", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Osso Etmoide", "Os ethmoidale", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
        ])

        # --- FACE (VISCEROCRÂNIO) ---
        bones_payload.extend([
            ("Mandíbula", "Mandibula", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Maxila", "Maxilla", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Osso Zigomático", "Os zygomaticum", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Osso Nasal", "Os nasale", SkeletonDivision.AXIAL, BoneType.FLAT, BodySegment.HEAD_NECK),
            ("Osso Lacrimal", "Os lacrimale", SkeletonDivision.AXIAL, BoneType.FLAT, BodySegment.HEAD_NECK),
            ("Osso Palatino", "Os palatinum", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Concha Nasal Inferior", "Concha nasalis inferior", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Vômer", "Vomer", SkeletonDivision.AXIAL, BoneType.FLAT, BodySegment.HEAD_NECK),
            ("Hioide", "Os hyoideum", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
        ])

        # --- OUVIDO MÉDIO (OSSÍCULOS) ---
        bones_payload.extend([
            ("Martelo", "Malleus", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Bigorna", "Incus", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Estribo", "Stapes", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
        ])

        # --- COLUNA VERTEBRAL (CERVICAL) ---
        bones_payload.append(("Atlas (C1)", "Atlas", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))
        bones_payload.append(("Áxis (C2)", "Axis", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))
        for i in range(3, 8):
            bones_payload.append((
                f"Vértebra Cervical C{i}", 
                f"Vertebra cervicalis C{self.to_roman(i)}", 
                SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE
            ))

        # --- COLUNA VERTEBRAL (TORÁCICA) ---
        for i in range(1, 13):
            bones_payload.append((
                f"Vértebra Torácica T{i}", 
                f"Vertebra thoracica T{self.to_roman(i)}", 
                SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE
            ))

        # --- COLUNA VERTEBRAL (LOMBAR) ---
        for i in range(1, 6):
            bones_payload.append((
                f"Vértebra Lombar L{i}", 
                f"Vertebra lumbalis L{self.to_roman(i)}", 
                SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE
            ))

        # --- SACRO E CÓCCIX ---
        bones_payload.append(("Sacro", "Os sacrum", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))
        bones_payload.append(("Cóccix", "Os coccygis", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.SPINE))

        # --- TÓRAX (CAIXA TORÁCICA) ---
        bones_payload.append(("Esterno", "Sternum", SkeletonDivision.AXIAL, BoneType.FLAT, BodySegment.TRUNK))
        
        for i in range(1, 13):
            rom = self.to_roman(i)
            if i <= 7:
                desc_type = "verdadeira"
            elif i <= 10:
                desc_type = "falsa"
            else:
                desc_type = "flutuante"
            
            bones_payload.append((
                f"Costela {i}", 
                f"Costa {rom}", 
                SkeletonDivision.AXIAL, BoneType.FLAT, BodySegment.TRUNK
            ))

        # ==============================================================================
        # 2. ESQUELETO APENDICULAR (MEMBROS)
        # ==============================================================================

        # --- CÍNGULO ESCAPULAR E BRAÇO ---
        bones_payload.extend([
            ("Clavícula", "Clavicula", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.UPPER_ARMS),
            ("Escápula", "Scapula", SkeletonDivision.APPENDICULAR, BoneType.FLAT, BodySegment.UPPER_ARMS),
            ("Úmero", "Humerus", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.UPPER_ARMS),
            ("Rádio", "Radius", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.UPPER_ARMS),
            ("Ulna", "Ulna", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.UPPER_ARMS),
        ])

        # --- CARPOS (PUNHO) ---
        carpos = [
            ("Escafoide", "Os scaphoideum"), ("Semilunar", "Os lunatum"), 
            ("Piramidal", "Os triquetrum"), ("Pisiforme", "Os pisiforme"), # Pisiforme é sesamoide
            ("Trapézio", "Os trapezium"), ("Trapezoide", "Os trapezoideum"),
            ("Capitato", "Os capitatum"), ("Hamato", "Os hamatum")
        ]
        for name, latim in carpos:
            tipo = BoneType.SESAMOID if name == "Pisiforme" else BoneType.SHORT
            bones_payload.append((name, latim, SkeletonDivision.APPENDICULAR, tipo, BodySegment.HAND))

        # --- MÃO (METACARPOS E FALANGES) ---
        for i in range(1, 6):
            rom = self.to_roman(i)
            bones_payload.append((f"Metacarpo {rom}", f"Os metacarpale {rom}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.HAND))
            bones_payload.append((f"Falange Proximal da Mão {rom}", f"Phalanx proximalis manus {rom}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.HAND))
            
            if i != 1: # Polegar (I) não tem média
                bones_payload.append((f"Falange Média da Mão {rom}", f"Phalanx media manus {rom}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.HAND))
            
            bones_payload.append((f"Falange Distal da Mão {rom}", f"Phalanx distalis manus {rom}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.HAND))

        # --- CÍNGULO PÉLVICO E PERNA ---
        bones_payload.extend([
            ("Osso do Quadril", "Os coxae", SkeletonDivision.APPENDICULAR, BoneType.FLAT, BodySegment.PELVIS),
            ("Fêmur", "Femur", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.LOWER_LEGS),
            ("Patela", "Patella", SkeletonDivision.APPENDICULAR, BoneType.SESAMOID, BodySegment.LOWER_LEGS),
            ("Tíbia", "Tibia", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.LOWER_LEGS),
            ("Fíbula", "Fibula", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.LOWER_LEGS),
        ])

        # --- TARSOS (TORNOZELO/PÉ) ---
        tarsos = [
            ("Tálus", "Talus"), ("Calcâneo", "Calcaneus"), ("Navicular", "Os naviculare"),
            ("Cuboide", "Os cuboideum"), ("Cuneiforme Medial", "Os cuneiforme mediale"),
            ("Cuneiforme Intermédio", "Os cuneiforme intermedium"), ("Cuneiforme Lateral", "Os cuneiforme laterale")
        ]
        for name, latim in tarsos:
            bones_payload.append((name, latim, SkeletonDivision.APPENDICULAR, BoneType.SHORT, BodySegment.FOOT))

        # --- PÉ (METATARSOS E FALANGES) ---
        for i in range(1, 6):
            rom = self.to_roman(i)
            bones_payload.append((f"Metatarso {rom}", f"Os metatarsale {rom}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.FOOT))
            bones_payload.append((f"Falange Proximal do Pé {rom}", f"Phalanx proximalis pedis {rom}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.FOOT))
            
            if i != 1: # Hálux (I) não tem média
                bones_payload.append((f"Falange Média do Pé {rom}", f"Phalanx media pedis {rom}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.FOOT))
            
            bones_payload.append((f"Falange Distal do Pé {rom}", f"Phalanx distalis pedis {rom}", SkeletonDivision.APPENDICULAR, BoneType.LONG, BodySegment.FOOT))

        # --- ESTRUTURAS AUXILIARES (Tecidos Moles) ---
        # Necessário para ancorar músculos que não se ligam a ossos diretamente
        bones_payload.extend([
            ("Estruturas de Tecido Mole", "Textus connectivus", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.TRUNK),
            ("Cartilagem Tireoide", "Cartilago thyroidea", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Cartilagem Alar Maior", "Cartilago alaris major", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
        ])

        # ==============================================================================
        # EXECUÇÃO DO SEED
        # ==============================================================================
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            # Limpa grupos obsoletos se existirem
            deprecated_groups = [
                "Vértebras Cervicais (C3-C7)", "Vértebras Torácicas (T1-T12)", "Vértebras Lombares (L1-L5)",
                "Costelas Verdadeiras (1-7)", "Costelas Falsas (8-10)", "Costelas Flutuantes (11-12)",
                "Metacarpos (I-V)", "Metatarsos (I-V)"
            ]
            Bone.objects.filter(name__in=deprecated_groups).delete()

            for name, sci_name, div, b_type, segment in bones_payload:
                # 1. Update or Create apenas os dados estruturais
                bone, created = Bone.objects.update_or_create(
                    name=name,
                    defaults={
                        'scientific_name': sci_name,
                        'division': div,
                        'bone_type': b_type,
                        'body_segment': segment,
                    }
                )

                # 2. Lógica de Descrição (Separada para evitar UnboundLocalError e sobrescrita acidental)
                # Se foi criado agora, adiciona um placeholder útil.
                if created:
                    bone.description = f"Estrutura óssea do segmento {bone.get_body_segment_display()}, classificada como {bone.get_bone_type_display()}."
                    bone.save()
                    created_count += 1
                
                # Se já existia mas a descrição está vazia, adiciona placeholder.
                # Se já existia e TEM descrição (ex: vinda do RAG), NÃO toca.
                elif not bone.description:
                    bone.description = f"Estrutura anatômica: {sci_name}."
                    bone.save()
                    updated_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Seed Autoritativo Concluído.'))
        self.stdout.write(self.style.SUCCESS(f'Ossos Criados: {created_count} | Processados/Mantidos: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total de Registros: {Bone.objects.count()}'))

    def to_roman(self, n):
        return ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"][n]