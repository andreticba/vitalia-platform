# backend/medical/management/commands/enrich_landmarks.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Bone, BoneLandmark

class Command(BaseCommand):
    help = 'Enriquece os Acidentes Ósseos (Landmarks) com suporte a Granularidade (V2).'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando detalhamento dos acidentes ósseos (Granular)...'))

        # Mapa de Expansão (Grupo -> Ossos Individuais)
        self.group_expansion_map = {
            # Coluna
            "Vértebras Cervicais (C3-C7)": [f"Vértebra Cervical C{i}" for i in range(3, 8)],
            "Vértebras Torácicas (T1-T12)": [f"Vértebra Torácica T{i}" for i in range(1, 13)],
            "Vértebras Lombares (L1-L5)": [f"Vértebra Lombar L{i}" for i in range(1, 6)],
            
            # Costelas
            "Costelas Verdadeiras (1-7)": [f"Costela {i}" for i in range(1, 8)],
            "Costelas Falsas (8-10)": [f"Costela {i}" for i in range(8, 11)],
            
            # Extremidades
            "Metacarpos (I-V)": [f"Metacarpo {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Metatarsos (I-V)": [f"Metatarso {r}" for r in ["I", "II", "III", "IV", "V"]],
        }

        # Lista Mestra (Mantida a original, a mágica é na resolução)
        landmarks_data = [
            # ... (ITENS ORIGINAIS DO CRÂNIO MANTIDOS - Copie a lista completa do script anterior se desejar, ou use esta abreviada que foca nas correções) ...
            
            # CRÂNIO E FACE (Sem grupos, busca direta)
            ("Osso Frontal", "Glabela", "Área lisa entre os arcos superciliares."),
            ("Osso Frontal", "Arco Superciliar", "Crista acima da órbita."),
            ("Osso Temporal", "Processo Mastoide", "Projeção atrás da orelha."),
            ("Osso Temporal", "Processo Estiloide", "Projeção fina e pontiaguda."),
            ("Osso Temporal", "Fossa Mandibular", "Articula com a mandíbula."),
            ("Osso Temporal", "Meato Acústico Externo", "Canal do ouvido."),
            ("Osso Occipital", "Linha Nucal Superior", "Crista para fixação muscular."),
            ("Osso Occipital", "Côndilos Occipitais", "Articulam com Atlas."),
            ("Osso Esfenoide", "Sela Turca", "Abriga a hipófise."),
            ("Osso Esfenoide", "Processos Pterigoides", "Origem dos pterigoideos."),
            ("Mandíbula", "Côndilo da Mandíbula", "Cabeça da mandíbula."),
            ("Mandíbula", "Processo Coronoide", "Inserção do Temporal."),
            ("Osso Zigomático", "Processo Temporal", "Arco zigomático."),
            ("Osso Zigomático", "Processo Frontal", "Orbita."),

            # COLUNA (Usa Grupos)
            ("Atlas (C1)", "Massas Laterais", "Suportam o crânio."),
            ("Atlas (C1)", "Arco Anterior", "Articula com o dente."),
            ("Atlas (C1)", "Processo Transverso", "Alavanca muscular."),
            ("Áxis (C2)", "Processo Odontoide (Dente)", "Pivô."),
            ("Áxis (C2)", "Processo Espinhoso", "Bífido."),

            ("Vértebras Cervicais (C3-C7)", "Processo Transverso", "Possui forame transversário."),
            ("Vértebras Cervicais (C3-C7)", "Processo Espinhoso", "Bífido/Proeminente."),
            ("Vértebras Cervicais (C3-C7)", "Corpo Vertebral", "Pequeno e retangular."),

            ("Vértebras Torácicas (T1-T12)", "Processo Espinhoso", "Longo e inclinado."),
            ("Vértebras Torácicas (T1-T12)", "Fóveas Costais", "Articulação com costelas."),
            ("Vértebras Torácicas (T1-T12)", "Processo Transverso", "Articulação com tubérculo costal."),

            ("Vértebras Lombares (L1-L5)", "Corpo Vertebral", "Grande e reniforme."),
            ("Vértebras Lombares (L1-L5)", "Processo Espinhoso", "Curto e quadrangular."),
            ("Vértebras Lombares (L1-L5)", "Processo Mamilar", "No processo articular superior."),
            ("Vértebras Lombares (L1-L5)", "Processo Acessório", "Na base do transverso."),

            ("Sacro", "Promontório", "Borda anterior da base."),
            ("Sacro", "Face Auricular", "Articula com o ílio."),

            # TÓRAX
            ("Esterno", "Manúbrio", "Parte superior."),
            ("Esterno", "Corpo do Esterno", "Parte central."),
            ("Esterno", "Processo Xifoide", "Ponta inferior."),
            ("Esterno", "Ângulo de Louis", "Junção manúbrio-corpo."),

            ("Costelas Verdadeiras (1-7)", "Cabeça da Costela", "Articula com corpo vertebral."),
            ("Costelas Verdadeiras (1-7)", "Tubérculo da Costela", "Articula com transverso."),
            ("Costelas Verdadeiras (1-7)", "Ângulo da Costela", "Curvatura posterior."),

            # MÃOS E PÉS
            ("Escafoide", "Tubérculo do Escafoide", "Palpável."),
            ("Trapézio", "Tubérculo do Trapézio", "Túnel do carpo."),
            
            ("Metacarpos (I-V)", "Base", "Proximal."),
            ("Metacarpos (I-V)", "Cabeça", "Distal."),

            ("Calcâneo", "Sustentáculo do Tálus", "Plataforma medial."),
            ("Calcâneo", "Tuberosidade do Calcâneo", "Inserção do Aquiles."),
            
            ("Metatarsos (I-V)", "Tuberosidade do V Metatarso", "Base lateral."),
            ("Metatarsos (I-V)", "Cabeça", "Apoio."),
        ]

        success_count = 0
        error_count = 0

        with transaction.atomic():
            for bone_name_input, landmark_name, desc in landmarks_data:
                # Resolve o nome (se for grupo, retorna lista; se for único, retorna lista com 1)
                target_bones = self.resolve_bones(bone_name_input)

                if not target_bones:
                    self.stdout.write(self.style.ERROR(f"Osso não encontrado: {bone_name_input} (Landmark: {landmark_name})"))
                    error_count += 1
                    continue

                for bone in target_bones:
                    # Update ou Create
                    obj, created = BoneLandmark.objects.update_or_create(
                        bone=bone,
                        name=landmark_name,
                        defaults={'description': desc}
                    )
                    
                    if created:
                        # self.stdout.write(f"Criado: {landmark_name} em {bone.name}")
                        pass
                    
                    success_count += 1

        self.stdout.write(self.style.SUCCESS('--------------------------------------'))
        self.stdout.write(self.style.SUCCESS(f'Landmarks processados: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Falhas: {error_count}'))
        self.stdout.write(self.style.SUCCESS('Mapeamento de Acidentes Ósseos Concluído.'))

    def resolve_bones(self, bone_name_input):
        """Retorna lista de objetos Bone, expandindo grupos se necessário."""
        # 1. Expansão de Grupo
        if bone_name_input in self.group_expansion_map:
            names = self.group_expansion_map[bone_name_input]
            return list(Bone.objects.filter(name__in=names))
        
        # 2. Busca Direta
        bone = Bone.objects.filter(name__iexact=bone_name_input).first()
        if bone:
            return [bone]
        
        return []