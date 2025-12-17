# backend/medical/management/commands/enrich_relationships.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Joint, Bone, JointBone

class Command(BaseCommand):
    help = 'Cria relacionamentos osteoarticulares com suporte a Granularidade (V2).'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando mapeamento de relacionamentos osteoarticulares (Granular)...'))

        # Mapa de Expansão (O mesmo do script de landmarks)
        self.group_expansion_map = {
            "Vértebras Cervicais (C3-C7)": [f"Vértebra Cervical C{i}" for i in range(3, 8)],
            "Vértebras Torácicas (T1-T12)": [f"Vértebra Torácica T{i}" for i in range(1, 13)],
            "Vértebras Lombares (L1-L5)": [f"Vértebra Lombar L{i}" for i in range(1, 6)],
            "Metacarpos (I-V)": [f"Metacarpo {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Falanges Proximais (Mão)": [f"Falange Proximal da Mão {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Falanges Médias (Mão)": [f"Falange Média da Mão {r}" for r in ["II", "III", "IV", "V"]],
            "Falanges Distais (Mão)": [f"Falange Distal da Mão {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Metatarsos (I-V)": [f"Metatarso {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Falanges Proximais (Pé)": [f"Falange Proximal do Pé {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Falanges Médias (Pé)": [f"Falange Média do Pé {r}" for r in ["II", "III", "IV", "V"]],
            "Falanges Distais (Pé)": [f"Falange Distal do Pé {r}" for r in ["I", "II", "III", "IV", "V"]],
        }

        # Lista de Relacionamentos (Mantida e enriquecida)
        relationships = [
            # ... (ITENS INDIVIDUAIS MANTIDOS) ...
            ("Articulação Glenoumeral (Ombro)", "Escápula", "Cavidade Glenoide"),
            ("Articulação Glenoumeral (Ombro)", "Úmero", "Cabeça do Úmero"),
            ("Articulação Esternoclavicular", "Esterno", "Manúbrio"),
            ("Articulação Esternoclavicular", "Clavícula", "Extremidade Esternal"),
            ("Articulação Acromioclavicular", "Escápula", "Acrômio"),
            ("Articulação Acromioclavicular", "Clavícula", "Extremidade Acromial"),
            ("Articulação do Cotovelo", "Úmero", "Tróclea e Capítulo"),
            ("Articulação do Cotovelo", "Ulna", "Incisura Troclear"),
            ("Articulação do Cotovelo", "Rádio", "Cabeça do Rádio"),
            ("Articulação Radioulnar Proximal", "Rádio", "Cabeça do Rádio"),
            ("Articulação Radioulnar Proximal", "Ulna", "Incisura Radial"),
            ("Articulação Radiocarpal (Punho)", "Rádio", "Face Articular"),
            ("Articulação Radiocarpal (Punho)", "Escafoide", "Proximal"),
            ("Articulação Radiocarpal (Punho)", "Semilunar", "Proximal"),
            ("Articulação Radiocarpal (Punho)", "Piramidal", "Proximal"),
            ("Articulação Carpometacarpal do Polegar", "Trapézio", "Sela"),
            ("Articulação Sacroilíaca", "Sacro", "Face Auricular"),
            ("Articulação Sacroilíaca", "Osso do Quadril", "Face Auricular"),
            ("Sínfise Púbica", "Osso do Quadril", "Face Sinfisal"),
            ("Articulação Coxofemoral (Quadril)", "Osso do Quadril", "Acetábulo"),
            ("Articulação Coxofemoral (Quadril)", "Fêmur", "Cabeça"),
            ("Articulação do Joelho", "Fêmur", "Côndilos"),
            ("Articulação do Joelho", "Tíbia", "Platô"),
            ("Articulação do Joelho", "Patela", "Face Posterior"),
            ("Articulação Talocrural (Tornozelo)", "Tíbia", "Inferior"),
            ("Articulação Talocrural (Tornozelo)", "Fíbula", "Maléolo Lateral"),
            ("Articulação Talocrural (Tornozelo)", "Tálus", "Tróclea"),
            ("Articulação Subtalar", "Tálus", "Inferior"),
            ("Articulação Subtalar", "Calcâneo", "Superior"),
            ("Articulação Temporomandibular (ATM)", "Osso Temporal", "Fossa Mandibular"),
            ("Articulação Temporomandibular (ATM)", "Mandíbula", "Côndilo"),
            ("Articulação Atlanto-occipital", "Osso Occipital", "Côndilos"),
            ("Articulação Atlanto-occipital", "Atlas (C1)", "Massas Laterais"),
            ("Articulação Atlanto-axial", "Atlas (C1)", "Arco Anterior"),
            ("Articulação Atlanto-axial", "Áxis (C2)", "Dente"),
            ("Sutura Sagital", "Osso Parietal", "Borda Medial"),
            ("Sutura Lambdoide", "Osso Occipital", "Borda Superior"),
            ("Sutura Lambdoide", "Osso Parietal", "Borda Posterior"),
            ("Sutura Coronal", "Osso Frontal", "Borda Posterior"),
            ("Sutura Coronal", "Osso Parietal", "Borda Anterior"),

            # --- GRUPOS QUE DERAM ERRO (AGORA RESOLVIDOS) ---
            ("Articulação Carpometacarpal do Polegar", "Metacarpos (I-V)", "Base (Apenas I)"), # Ajuste manual no loop se quiser, ou deixa genérico
            
            # MÃO (Grupos)
            ("Articulações Metacarpofalângicas (Mão)", "Metacarpos (I-V)", "Cabeça"),
            ("Articulações Metacarpofalângicas (Mão)", "Falanges Proximais (Mão)", "Base"),
            ("Articulações Interfalângicas (Mão)", "Falanges Proximais (Mão)", "Cabeça"),
            ("Articulações Interfalângicas (Mão)", "Falanges Médias (Mão)", "Base/Cabeça"),
            ("Articulações Interfalângicas (Mão)", "Falanges Distais (Mão)", "Base"),

            # PÉ (Grupos)
            ("Articulações Metatarsofalângicas (Pé)", "Metatarsos (I-V)", "Cabeça"),
            ("Articulações Metatarsofalângicas (Pé)", "Falanges Proximais (Pé)", "Base"),
            ("Articulações Interfalângicas (Pé)", "Falanges Proximais (Pé)", "Cabeça"),
            ("Articulações Interfalângicas (Pé)", "Falanges Médias (Pé)", "Base/Cabeça"),
            ("Articulações Interfalângicas (Pé)", "Falanges Distais (Pé)", "Base"),

            # COLUNA (Grupos)
            ("Discos Intervertebrais", "Vértebras Cervicais (C3-C7)", "Corpo"),
            ("Discos Intervertebrais", "Vértebras Torácicas (T1-T12)", "Corpo"),
            ("Discos Intervertebrais", "Vértebras Lombares (L1-L5)", "Corpo"),
            ("Discos Intervertebrais", "Sacro", "Base"),
            
            ("Articulações Zigapofisárias (Facetas)", "Vértebras Cervicais (C3-C7)", "Processos Articulares"),
            ("Articulações Zigapofisárias (Facetas)", "Vértebras Torácicas (T1-T12)", "Processos Articulares"),
            ("Articulações Zigapofisárias (Facetas)", "Vértebras Lombares (L1-L5)", "Processos Articulares"),
        ]

        success_count = 0
        error_count = 0

        with transaction.atomic():
            for joint_name, bone_name_input, role_desc in relationships:
                try:
                    joint = Joint.objects.get(name=joint_name)
                    
                    target_bones = self.resolve_bones(bone_name_input)
                    if not target_bones:
                        # Fallback: Tenta pegar o Metacarpo I especificamente para o polegar
                        if joint_name == "Articulação Carpometacarpal do Polegar" and "Metacarpos" in bone_name_input:
                             target_bones = list(Bone.objects.filter(name="Metacarpo I"))
                        else:
                            self.stdout.write(self.style.ERROR(f"Osso(s) não encontrado(s): {bone_name_input}"))
                            error_count += 1
                            continue

                    for bone in target_bones:
                        JointBone.objects.update_or_create(
                            joint=joint,
                            bone=bone,
                            defaults={'role': role_desc}
                        )
                        success_count += 1

                except Joint.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Articulação não encontrada: {joint_name}"))
                    error_count += 1

        self.stdout.write(self.style.SUCCESS('--------------------------------------'))
        self.stdout.write(self.style.SUCCESS(f'Conexões criadas: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Erros: {error_count}'))
        self.stdout.write(self.style.SUCCESS('Knowledge Hub: Grafo Osteoarticular Concluído.'))

    def resolve_bones(self, bone_name_input):
        if bone_name_input in self.group_expansion_map:
            names = self.group_expansion_map[bone_name_input]
            return list(Bone.objects.filter(name__in=names))
        
        bone = Bone.objects.filter(name__iexact=bone_name_input).first()
        if bone: return [bone]
        return []