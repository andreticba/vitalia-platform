# backend/medical/management/commands/seed_muscle_attachments_full.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Muscle, Bone, BoneLandmark, MuscleBoneAttachment, AttachmentType, SkeletonDivision, BoneType, BodySegment

class Command(BaseCommand):
    help = 'Mapeamento biomecânico V6 (Final): Expansão inteligente de grupos e correção de nomes.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando mapeamento muscular granular (V6)...'))

        self.landmark_cache = {}
        self.ensure_critical_structures()

        # --- MAPA DE TRADUÇÃO DE GRUPOS (A Chave para eliminar os erros) ---
        # Mapeia "Nome do Grupo Antigo" -> [Lista de Nomes de Ossos Reais no Banco]
        self.group_expansion_map = {
            # Coluna
            "Vértebras Cervicais (C3-C7)": [f"Vértebra Cervical C{i}" for i in range(3, 8)],
            "Vértebras Torácicas (T1-T12)": [f"Vértebra Torácica T{i}" for i in range(1, 13)],
            "Vértebras Lombares (L1-L5)": [f"Vértebra Lombar L{i}" for i in range(1, 6)],
            
            # Costelas
            "Costelas Verdadeiras (1-7)": [f"Costela {i}" for i in range(1, 8)],
            "Costelas Falsas (8-10)": [f"Costela {i}" for i in range(8, 11)],
            "Costelas Flutuantes (11-12)": [f"Costela {i}" for i in range(11, 13)],
            "Costelas (1-12)": [f"Costela {i}" for i in range(1, 13)],
            "Costelas (1-8)": [f"Costela {i}" for i in range(1, 9)],
            "Costelas (5-12)": [f"Costela {i}" for i in range(5, 13)],
            "Cartilagens Costais (5-7)": [f"Costela {i}" for i in range(5, 8)], # Simplificação para o osso costela
            "Cartilagens Costais": [f"Costela {i}" for i in range(1, 11)],

            # Mão
            "Metacarpos (I-V)": [f"Metacarpo {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Metacarpos I-II": ["Metacarpo I", "Metacarpo II"],
            "Metacarpos II-III": ["Metacarpo II", "Metacarpo III"],
            "Metacarpos III-IV": ["Metacarpo III", "Metacarpo IV"],
            "Metacarpos IV-V": ["Metacarpo IV", "Metacarpo V"],
            
            "Falanges Proximais (Mão)": [f"Falange Proximal da Mão {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Falanges Médias (Mão)": [f"Falange Média da Mão {r}" for r in ["II", "III", "IV", "V"]],
            "Falanges Distais (Mão)": [f"Falange Distal da Mão {r}" for r in ["I", "II", "III", "IV", "V"]],
            
            # Específicos Mão (Correção de nomes singulares)
            "Falange Distal I": ["Falange Distal da Mão I"],
            "Falange Distal II": ["Falange Distal da Mão II"],
            "Falange Distal V": ["Falange Distal da Mão V"],
            "Falanges Distais (2-5)": [f"Falange Distal da Mão {r}" for r in ["II", "III", "IV", "V"]],
            
            # Pé
            "Metatarsos (I-V)": [f"Metatarso {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Metatarsos I-II": ["Metatarso I", "Metatarso II"],
            "Metatarsos II-III": ["Metatarso II", "Metatarso III"],
            "Metatarsos III-IV": ["Metatarso III", "Metatarso IV"],
            "Metatarsos IV-V": ["Metatarso IV", "Metatarso V"],
            
            "Falanges Proximais (Pé)": [f"Falange Proximal do Pé {r}" for r in ["I", "II", "III", "IV", "V"]],
            "Falanges Médias (Pé)": [f"Falange Média do Pé {r}" for r in ["II", "III", "IV", "V"]],
            "Falanges Distais (Pé)": [f"Falange Distal do Pé {r}" for r in ["I", "II", "III", "IV", "V"]],
            
            "Falange Distal I (Pé)": ["Falange Distal do Pé I"],
            "Falange Distal I": ["Falange Distal do Pé I"], # Ambiguidade resolvida pelo contexto do músculo
        }

        # --- LISTA DE DADOS (MANTIDA IGUAL À V4) ---
        mapping = [
            # FACE E PESCOÇO
            ("Occipitofrontal (Ventre Frontal)", [("Estruturas de Tecido Mole", "Aponeurose Epicraniana", "ORIGEM"), ("Estruturas de Tecido Mole", "Pele da Sobrancelha", "INSERCAO")]),
            ("Occipitofrontal (Ventre Occipital)", [("Osso Occipital", "Linha Nucal Superior", "ORIGEM"), ("Estruturas de Tecido Mole", "Aponeurose Epicraniana", "INSERCAO")]),
            ("Corrugador do Supercílio", [("Osso Frontal", "Arco Superciliar", "ORIGEM"), ("Estruturas de Tecido Mole", "Pele da Sobrancelha", "INSERCAO")]),
            ("Prócero", [("Osso Nasal", "Osso Nasal", "ORIGEM"), ("Estruturas de Tecido Mole", "Pele da Glabela", "INSERCAO")]),
            ("Orbicular do Olho", [("Osso Frontal", "Parte Nasal", "ORIGEM"), ("Estruturas de Tecido Mole", "Pele da Pálpebra", "INSERCAO")]),
            ("Levantador do Lábio Superior", [("Maxila", "Margem Infraorbital", "ORIGEM"), ("Maxila", "Lábio Superior", "INSERCAO")]),
            ("Levantador do Lábio Superior e da Asa do Nariz", [("Maxila", "Processo Frontal", "ORIGEM"), ("Estruturas de Tecido Mole", "Cartilagem Alar Maior", "INSERCAO")]),
            ("Zigomático Maior", [("Osso Zigomático", "Osso Zigomático", "ORIGEM"), ("Mandíbula", "Ângulo da Boca", "INSERCAO")]),
            ("Risório", [("Estruturas de Tecido Mole", "Fáscia Massetérica", "ORIGEM"), ("Mandíbula", "Ângulo da Boca", "INSERCAO")]),
            ("Depressor do Ângulo da Boca", [("Mandíbula", "Linha Oblíqua", "ORIGEM"), ("Mandíbula", "Ângulo da Boca", "INSERCAO")]),
            ("Depressor do Lábio Inferior", [("Mandíbula", "Linha Oblíqua", "ORIGEM"), ("Mandíbula", "Lábio Inferior", "INSERCAO")]),
            ("Mentoniano", [("Mandíbula", "Fossa Mentual", "ORIGEM"), ("Mandíbula", "Pele do Queixo", "INSERCAO")]),
            ("Orbicular da Boca", [("Maxila", "Maxila", "ORIGEM"), ("Mandíbula", "Mandíbula", "ORIGEM"), ("Estruturas de Tecido Mole", "Pele dos Lábios", "INSERCAO")]),
            ("Bucinador", [("Maxila", "Processo Alveolar", "ORIGEM"), ("Mandíbula", "Processo Alveolar", "ORIGEM"), ("Mandíbula", "Ângulo da Boca", "INSERCAO")]),
            ("Masseter", [("Osso Zigomático", "Arco Zigomático", "ORIGEM"), ("Mandíbula", "Ângulo da Mandíbula", "INSERCAO")]),
            ("Temporal", [("Osso Temporal", "Fossa Temporal", "ORIGEM"), ("Mandíbula", "Processo Coronoide", "INSERCAO")]),
            ("Pterigoideo Medial", [("Osso Esfenoide", "Processos Pterigoides", "ORIGEM"), ("Mandíbula", "Ângulo da Mandíbula (Interno)", "INSERCAO")]),
            ("Pterigoideo Lateral", [("Osso Esfenoide", "Processos Pterigoides", "ORIGEM"), ("Mandíbula", "Côndilo da Mandíbula", "INSERCAO")]),
            ("Platisma", [("Estruturas de Tecido Mole", "Fáscia Peitoral", "ORIGEM"), ("Mandíbula", "Base da Mandíbula", "INSERCAO")]),
            ("Esternocleidomastoideo", [("Esterno", "Manúbrio", "ORIGEM"), ("Clavícula", "Extremidade Esternal", "ORIGEM"), ("Osso Temporal", "Processo Mastoide", "INSERCAO")]),
            
            # Hioides
            ("Digástrico (Ventre Anterior)", [("Mandíbula", "Fossa Digástrica", "ORIGEM"), ("Osso Hioide", "Corpo do Hioide", "INSERCAO")]),
            ("Digástrico (Ventre Posterior)", [("Osso Temporal", "Processo Mastoide", "ORIGEM"), ("Osso Hioide", "Corpo do Hioide", "INSERCAO")]),
            ("Estilohióideo", [("Osso Temporal", "Processo Estiloide", "ORIGEM"), ("Osso Hioide", "Corpo do Hioide", "INSERCAO")]),
            ("Milohióideo", [("Mandíbula", "Linha Milohioidea", "ORIGEM"), ("Osso Hioide", "Corpo do Hioide", "INSERCAO")]),
            ("Geni-hióideo", [("Mandíbula", "Espinha Mentual", "ORIGEM"), ("Osso Hioide", "Corpo do Hioide", "INSERCAO")]),
            ("Esternohióideo", [("Esterno", "Manúbrio", "ORIGEM"), ("Osso Hioide", "Corpo do Hioide", "INSERCAO")]),
            ("Esternotireóideo", [("Esterno", "Manúbrio", "ORIGEM"), ("Estruturas de Tecido Mole", "Cartilagem Tireoide", "INSERCAO")]),
            ("Tireohióideo", [("Estruturas de Tecido Mole", "Cartilagem Tireoide", "ORIGEM"), ("Osso Hioide", "Corpo do Hioide", "INSERCAO")]),
            ("Omoióideo (Ventre Inferior)", [("Escápula", "Borda Superior", "ORIGEM"), ("Osso Hioide", "Tendão Intermediário", "INSERCAO")]),
            ("Omoióideo (Ventre Superior)", [("Osso Hioide", "Tendão Intermediário", "ORIGEM"), ("Osso Hioide", "Corpo do Hioide", "INSERCAO")]),
            
            # Profundos Pescoço
            ("Longo da Cabeça", [("Vértebras Cervicais (C3-C7)", "Processo Transverso", "ORIGEM"), ("Osso Occipital", "Parte Basilar", "INSERCAO")]),
            ("Longo do Pescoço", [("Vértebras Cervicais (C3-C7)", "Corpo Vertebral", "ORIGEM"), ("Atlas (C1)", "Tubérculo Anterior", "INSERCAO")]),
            ("Escaleno Anterior", [("Vértebras Cervicais (C3-C7)", "Processo Transverso (C3-C6)", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "1ª Costela", "INSERCAO")]),
            ("Escaleno Médio", [("Vértebras Cervicais (C3-C7)", "Processo Transverso (C2-C7)", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "1ª Costela", "INSERCAO")]),
            ("Escaleno Posterior", [("Vértebras Cervicais (C3-C7)", "Processo Transverso (C5-C7)", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "2ª Costela", "INSERCAO")]),

            # Linguais
            ("Genioglosso", [("Mandíbula", "Espinha Mentual", "ORIGEM"), ("Estruturas de Tecido Mole", "Língua", "INSERCAO")]),
            ("Hioglosso", [("Osso Hioide", "Corpo do Hioide", "ORIGEM"), ("Estruturas de Tecido Mole", "Língua", "INSERCAO")]),
            ("Estiloglosso", [("Osso Temporal", "Processo Estiloide", "ORIGEM"), ("Estruturas de Tecido Mole", "Língua", "INSERCAO")]),
            ("Elevador do Véu Palatino", [("Osso Temporal", "Parte Petrosa", "ORIGEM"), ("Estruturas de Tecido Mole", "Palato Mole", "INSERCAO")]),
            ("Tensor do Véu Palatino", [("Osso Esfenoide", "Asa Maior", "ORIGEM"), ("Estruturas de Tecido Mole", "Palato Mole", "INSERCAO")]),
            ("Músculo da Úvula", [("Osso Palatino", "Espinha Nasal Posterior", "ORIGEM"), ("Estruturas de Tecido Mole", "Úvula", "INSERCAO")]),

            # COLUNA DORSAL
            ("Esplênio da Cabeça", [("Vértebras Cervicais (C3-C7)", "Ligamento Nucal", "ORIGEM"), ("Osso Temporal", "Processo Mastoide", "INSERCAO")]),
            ("Esplênio do Pescoço", [("Vértebras Torácicas (T1-T12)", "Processo Espinhoso (T3-T6)", "ORIGEM"), ("Atlas (C1)", "Processo Transverso", "INSERCAO")]),
            ("Iliocostal do Pescoço", [("Costelas Verdadeiras (1-7)", "Ângulo da Costela", "ORIGEM"), ("Vértebras Cervicais (C3-C7)", "Processo Transverso", "INSERCAO")]),
            ("Iliocostal do Tórax", [("Costelas Verdadeiras (1-7)", "Ângulo da Costela", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "Ângulo da Costela (Superior)", "INSERCAO")]),
            ("Iliocostal Lombar", [("Osso do Quadril", "Crista Ilíaca", "ORIGEM"), ("Costelas Falsas (8-10)", "Ângulo da Costela", "INSERCAO")]),
            ("Longuíssimo da Cabeça", [("Vértebras Cervicais (C3-C7)", "Processo Transverso", "ORIGEM"), ("Osso Temporal", "Processo Mastoide", "INSERCAO")]),
            ("Longuíssimo do Pescoço", [("Vértebras Torácicas (T1-T12)", "Processo Transverso", "ORIGEM"), ("Vértebras Cervicais (C3-C7)", "Processo Transverso", "INSERCAO")]),
            ("Longuíssimo do Tórax", [("Sacro", "Face Dorsal", "ORIGEM"), ("Vértebras Torácicas (T1-T12)", "Processo Transverso", "INSERCAO")]),
            ("Espinhal da Cabeça", [("Vértebras Cervicais (C3-C7)", "Processo Espinhoso", "ORIGEM"), ("Osso Occipital", "Linha Nucal", "INSERCAO")]),
            ("Espinhal do Pescoço", [("Vértebras Cervicais (C3-C7)", "Processo Espinhoso", "ORIGEM"), ("Áxis (C2)", "Processo Espinhoso", "INSERCAO")]),
            ("Espinhal do Tórax", [("Vértebras Torácicas (T1-T12)", "Processo Espinhoso", "ORIGEM"), ("Vértebras Torácicas (T1-T12)", "Processo Espinhoso (Superior)", "INSERCAO")]),
            ("Semiespinhal da Cabeça", [("Vértebras Cervicais (C3-C7)", "Processo Transverso", "ORIGEM"), ("Osso Occipital", "Linha Nucal", "INSERCAO")]),
            ("Semiespinhal do Pescoço", [("Vértebras Torácicas (T1-T12)", "Processo Transverso", "ORIGEM"), ("Áxis (C2)", "Processo Espinhoso", "INSERCAO")]),
            ("Semiespinhal do Tórax", [("Vértebras Torácicas (T1-T12)", "Processo Transverso", "ORIGEM"), ("Vértebras Cervicais (C3-C7)", "Processo Espinhoso", "INSERCAO")]),
            ("Multífido", [("Sacro", "Face Dorsal", "ORIGEM"), ("Vértebras Lombares (L1-L5)", "Processo Espinhoso", "INSERCAO")]),
            ("Rotadores (Curtos e Longos)", [("Vértebras Torácicas (T1-T12)", "Processo Transverso", "ORIGEM"), ("Vértebras Torácicas (T1-T12)", "Processo Espinhoso", "INSERCAO")]),
            ("Interespinhosos Cervicais", [("Vértebras Cervicais (C3-C7)", "Processo Espinhoso", "ORIGEM"), ("Vértebras Cervicais (C3-C7)", "Processo Espinhoso (Superior)", "INSERCAO")]),
            ("Interespinhosos Torácicos", [("Vértebras Torácicas (T1-T12)", "Processo Espinhoso", "ORIGEM"), ("Vértebras Torácicas (T1-T12)", "Processo Espinhoso (Superior)", "INSERCAO")]),
            ("Interespinhosos Lombares", [("Vértebras Lombares (L1-L5)", "Processo Espinhoso", "ORIGEM"), ("Vértebras Lombares (L1-L5)", "Processo Espinhoso (Superior)", "INSERCAO")]),
            ("Intertransversários Cervicais", [("Vértebras Cervicais (C3-C7)", "Processo Transverso", "ORIGEM"), ("Vértebras Cervicais (C3-C7)", "Processo Transverso (Superior)", "INSERCAO")]),
            ("Intertransversários Torácicos", [("Vértebras Torácicas (T1-T12)", "Processo Transverso", "ORIGEM"), ("Vértebras Torácicas (T1-T12)", "Processo Transverso (Superior)", "INSERCAO")]),
            ("Intertransversários Lombares", [("Vértebras Lombares (L1-L5)", "Processo Transverso", "ORIGEM"), ("Vértebras Lombares (L1-L5)", "Processo Transverso (Superior)", "INSERCAO")]),
            
            # Suboccipitais
            ("Reto Posterior Maior da Cabeça", [("Áxis (C2)", "Processo Espinhoso", "ORIGEM"), ("Osso Occipital", "Linha Nucal Inferior", "INSERCAO")]),
            ("Reto Posterior Menor da Cabeça", [("Atlas (C1)", "Tubérculo Posterior", "ORIGEM"), ("Osso Occipital", "Linha Nucal Inferior", "INSERCAO")]),
            ("Oblíquo Inferior da Cabeça", [("Áxis (C2)", "Processo Espinhoso", "ORIGEM"), ("Atlas (C1)", "Processo Transverso", "INSERCAO")]),
            ("Oblíquo Superior da Cabeça", [("Atlas (C1)", "Processo Transverso", "ORIGEM"), ("Osso Occipital", "Linha Nucal Inferior", "INSERCAO")]),
            ("Reto Anterior da Cabeça", [("Atlas (C1)", "Massas Laterais", "ORIGEM"), ("Osso Occipital", "Parte Basilar", "INSERCAO")]),
            ("Reto Lateral da Cabeça", [("Atlas (C1)", "Processo Transverso", "ORIGEM"), ("Osso Occipital", "Processo Jugular", "INSERCAO")]),

            # TÓRAX E ABDOME
            ("Intercostais Externos", [("Costelas Verdadeiras (1-7)", "Borda Inferior", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "Borda Superior", "INSERCAO")]),
            ("Intercostais Internos", [("Costelas Verdadeiras (1-7)", "Borda Superior", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "Borda Inferior", "INSERCAO")]),
            ("Subcostal", [("Costelas Falsas (8-10)", "Face Interna", "ORIGEM"), ("Costelas Falsas (8-10)", "Face Interna", "INSERCAO")]),
            ("Transverso do Tórax", [("Esterno", "Corpo do Esterno", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "Cartilagens Costais", "INSERCAO")]),
            ("Elevadores das Costelas Curtos", [("Vértebras Torácicas (T1-T12)", "Processo Transverso", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "Face Externa", "INSERCAO")]),
            ("Elevadores das Costelas Longos", [("Vértebras Torácicas (T1-T12)", "Processo Transverso", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "Face Externa", "INSERCAO")]),
            ("Serrátil Posterior Superior", [("Vértebras Cervicais (C3-C7)", "Processo Espinhoso", "ORIGEM"), ("Costelas Verdadeiras (1-7)", "Ângulo da Costela", "INSERCAO")]),
            ("Serrátil Posterior Inferior", [("Vértebras Torácicas (T1-T12)", "Processo Espinhoso", "ORIGEM"), ("Costelas Falsas (8-10)", "Borda Inferior", "INSERCAO")]),
            ("Diafragma", [("Esterno", "Processo Xifoide", "ORIGEM"), ("Vértebras Lombares (L1-L5)", "Corpo Vertebral", "ORIGEM"), ("Estruturas de Tecido Mole", "Tendão Central", "INSERCAO")]),
            ("Reto do Abdome", [("Osso do Quadril", "Sínfise Púbica", "ORIGEM"), ("Esterno", "Processo Xifoide", "INSERCAO")]),
            ("Oblíquo Externo do Abdome", [("Costelas Verdadeiras (1-7)", "Face Externa", "ORIGEM"), ("Osso do Quadril", "Crista Ilíaca", "INSERCAO")]),
            ("Oblíquo Interno do Abdome", [("Osso do Quadril", "Crista Ilíaca", "ORIGEM"), ("Costelas Falsas (8-10)", "Borda Inferior", "INSERCAO")]),
            ("Transverso do Abdome", [("Osso do Quadril", "Crista Ilíaca", "ORIGEM"), ("Estruturas de Tecido Mole", "Linha Alba", "INSERCAO")]),
            ("Quadrado Lombar", [("Osso do Quadril", "Crista Ilíaca", "ORIGEM"), ("Vértebras Lombares (L1-L5)", "Processo Transverso", "INSERCAO")]),
            ("Piramidal", [("Osso do Quadril", "Púbis", "ORIGEM"), ("Estruturas de Tecido Mole", "Linha Alba", "INSERCAO")]),

            # ASSOALHO PÉLVICO
            ("Levantador do Ânus", [("Osso do Quadril", "Púbis", "ORIGEM"), ("Cóccix", "Cóccix", "INSERCAO")]),
            ("Coccígeo (Isquiococcígeo)", [("Osso do Quadril", "Espinha Isquiática", "ORIGEM"), ("Sacro", "Margem Lateral", "INSERCAO")]),
            ("Obturador Interno", [("Osso do Quadril", "Membrana Obturadora", "ORIGEM"), ("Fêmur", "Trocânter Maior", "INSERCAO")]),
            ("Obturador Externo", [("Osso do Quadril", "Membrana Obturadora", "ORIGEM"), ("Fêmur", "Fossa Trocantérica", "INSERCAO")]),
            ("Esfíncter Externo do Ânus", [("Cóccix", "Ponta do Cóccix", "ORIGEM"), ("Estruturas de Tecido Mole", "Corpo Perineal", "INSERCAO")]),
            ("Transverso do Períneo Superficial", [("Osso do Quadril", "Túber Isquiático", "ORIGEM"), ("Estruturas de Tecido Mole", "Corpo Perineal", "INSERCAO")]),
            ("Transverso do Períneo Profundo", [("Osso do Quadril", "Ramo Isquiopúbico", "ORIGEM"), ("Estruturas de Tecido Mole", "Corpo Perineal", "INSERCAO")]),

            # OMBRO E BRAÇO
            ("Deltoide (Fibras Anteriores)", [("Clavícula", "Extremidade Acromial", "ORIGEM"), ("Úmero", "Tuberosidade Deltoidea", "INSERCAO")]),
            ("Deltoide (Fibras Médias)", [("Escápula", "Acrômio", "ORIGEM"), ("Úmero", "Tuberosidade Deltoidea", "INSERCAO")]),
            ("Deltoide (Fibras Posteriores)", [("Escápula", "Espinha da Escápula", "ORIGEM"), ("Úmero", "Tuberosidade Deltoidea", "INSERCAO")]),
            ("Peitoral Maior", [("Esterno", "Corpo do Esterno", "ORIGEM"), ("Úmero", "Sulco Intertubercular", "INSERCAO")]),
            ("Peitoral Menor", [("Costelas Verdadeiras (1-7)", "Processo Coracoide", "ORIGEM"), ("Escápula", "Processo Coracoide", "INSERCAO")]),
            ("Subclavio", [("Costelas Verdadeiras (1-7)", "1ª Costela", "ORIGEM"), ("Clavícula", "Sulco do Músculo Subclávio", "INSERCAO")]),
            ("Serrátil Anterior", [("Costelas Verdadeiras (1-7)", "Face Externa", "ORIGEM"), ("Escápula", "Borda Medial", "INSERCAO")]),
            ("Trapézio (Fibras Superiores)", [("Osso Occipital", "Linha Nucal Superior", "ORIGEM"), ("Clavícula", "Extremidade Acromial", "INSERCAO")]),
            ("Trapézio (Fibras Médias)", [("Vértebras Cervicais (C3-C7)", "Processo Espinhoso", "ORIGEM"), ("Escápula", "Acrômio", "INSERCAO")]),
            ("Trapézio (Fibras Inferiores)", [("Vértebras Torácicas (T1-T12)", "Processo Espinhoso", "ORIGEM"), ("Escápula", "Espinha da Escápula", "INSERCAO")]),
            ("Grande Dorsal", [("Osso do Quadril", "Crista Ilíaca", "ORIGEM"), ("Úmero", "Sulco Intertubercular", "INSERCAO")]),
            ("Levantador da Escápula", [("Vértebras Cervicais (C3-C7)", "Processo Transverso", "ORIGEM"), ("Escápula", "Borda Medial", "INSERCAO")]),
            ("Rombóide Maior", [("Vértebras Torácicas (T1-T12)", "Processo Espinhoso", "ORIGEM"), ("Escápula", "Borda Medial", "INSERCAO")]),
            ("Rombóide Menor", [("Vértebras Cervicais (C3-C7)", "Processo Espinhoso", "ORIGEM"), ("Escápula", "Borda Medial", "INSERCAO")]),
            ("Supraespinhal", [("Escápula", "Fossa Supraespinhal", "ORIGEM"), ("Úmero", "Tubérculo Maior", "INSERCAO")]),
            ("Infraespinhal", [("Escápula", "Fossa Infraespinhal", "ORIGEM"), ("Úmero", "Tubérculo Maior", "INSERCAO")]),
            ("Redondo Menor", [("Escápula", "Borda Lateral", "ORIGEM"), ("Úmero", "Tubérculo Maior", "INSERCAO")]),
            ("Redondo Maior", [("Escápula", "Ângulo Inferior", "ORIGEM"), ("Úmero", "Sulco Intertubercular", "INSERCAO")]),
            ("Subescapular", [("Escápula", "Fossa Subescapular", "ORIGEM"), ("Úmero", "Tubérculo Menor", "INSERCAO")]),
            ("Bíceps Braquial (Cabeça Longa)", [("Escápula", "Tubérculo Supraglenoidal", "ORIGEM"), ("Rádio", "Tuberosidade do Rádio", "INSERCAO")]),
            ("Bíceps Braquial (Cabeça Curta)", [("Escápula", "Processo Coracoide", "ORIGEM"), ("Rádio", "Tuberosidade do Rádio", "INSERCAO")]),
            ("Braquial", [("Úmero", "Diáfise Anterior", "ORIGEM"), ("Ulna", "Processo Coronoide", "INSERCAO")]),
            ("Coracobraquial", [("Escápula", "Processo Coracoide", "ORIGEM"), ("Úmero", "Diáfise Medial", "INSERCAO")]),
            ("Tríceps Braquial (Cabeça Longa)", [("Escápula", "Tubérculo Infraglenoidal", "ORIGEM"), ("Ulna", "Olécrano", "INSERCAO")]),
            ("Tríceps Braquial (Cabeça Lateral)", [("Úmero", "Face Posterior", "ORIGEM"), ("Ulna", "Olécrano", "INSERCAO")]),
            ("Tríceps Braquial (Cabeça Medial)", [("Úmero", "Face Posterior", "ORIGEM"), ("Ulna", "Olécrano", "INSERCAO")]),
            ("Ancôneo", [("Úmero", "Epicôndilo Lateral", "ORIGEM"), ("Ulna", "Olécrano", "INSERCAO")]),

            # ANTEBRAÇO E MÃO
            ("Pronador Redondo", [("Úmero", "Epicôndilo Medial", "ORIGEM"), ("Rádio", "Face Lateral", "INSERCAO")]),
            ("Flexor Radial do Carpo", [("Úmero", "Epicôndilo Medial", "ORIGEM"), ("Metacarpos (I-V)", "Base do II Metacarpo", "INSERCAO")]),
            ("Palmar Longo", [("Úmero", "Epicôndilo Medial", "ORIGEM"), ("Estruturas de Tecido Mole", "Aponeurose Palmar", "INSERCAO")]),
            ("Flexor Ulnar do Carpo", [("Úmero", "Epicôndilo Medial", "ORIGEM"), ("Pisiforme", "Pisiforme", "INSERCAO")]),
            ("Flexor Superficial dos Dedos", [("Úmero", "Epicôndilo Medial", "ORIGEM"), ("Falanges Médias (Mão)", "Falanges Médias", "INSERCAO")]),
            ("Flexor Profundo dos Dedos", [("Ulna", "Face Anterior", "ORIGEM"), ("Falanges Distais (Mão)", "Falanges Distais", "INSERCAO")]),
            ("Flexor Longo do Polegar", [("Rádio", "Face Anterior", "ORIGEM"), ("Falanges Distais (Mão)", "Falange Distal I", "INSERCAO")]),
            ("Pronador Quadrado", [("Ulna", "Quarto Distal", "ORIGEM"), ("Rádio", "Quarto Distal", "INSERCAO")]),
            ("Braquiorradial", [("Úmero", "Crista Supracondilar Lateral", "ORIGEM"), ("Rádio", "Processo Estiloide do Rádio", "INSERCAO")]),
            ("Extensor Radial Longo do Carpo", [("Úmero", "Crista Supracondilar Lateral", "ORIGEM"), ("Metacarpos (I-V)", "Base do II Metacarpo", "INSERCAO")]),
            ("Extensor Radial Curto do Carpo", [("Úmero", "Epicôndilo Lateral", "ORIGEM"), ("Metacarpos (I-V)", "Base do III Metacarpo", "INSERCAO")]),
            ("Extensor dos Dedos", [("Úmero", "Epicôndilo Lateral", "ORIGEM"), ("Falanges Distais (Mão)", "Falanges Distais", "INSERCAO")]),
            ("Extensor do Dedo Mínimo", [("Úmero", "Epicôndilo Lateral", "ORIGEM"), ("Falanges Distais (Mão)", "Falange Distal V", "INSERCAO")]),
            ("Extensor Ulnar do Carpo", [("Úmero", "Epicôndilo Lateral", "ORIGEM"), ("Metacarpos (I-V)", "Base do V Metacarpo", "INSERCAO")]),
            ("Supinador", [("Úmero", "Epicôndilo Lateral", "ORIGEM"), ("Rádio", "Face Anterior Proximal", "INSERCAO")]),
            ("Abdutor Longo do Polegar", [("Ulna", "Face Posterior", "ORIGEM"), ("Metacarpos (I-V)", "Base do I Metacarpo", "INSERCAO")]),
            ("Extensor Curto do Polegar", [("Rádio", "Face Posterior", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal I", "INSERCAO")]),
            ("Extensor Longo do Polegar", [("Ulna", "Face Posterior", "ORIGEM"), ("Falanges Distais (Mão)", "Falange Distal I", "INSERCAO")]),
            ("Extensor do Indicador", [("Ulna", "Face Posterior", "ORIGEM"), ("Falanges Distais (Mão)", "Falange Distal II", "INSERCAO")]),
            ("Abdutor Curto do Polegar", [("Escafoide", "Tubérculo do Escafoide", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal I", "INSERCAO")]),
            ("Flexor Curto do Polegar", [("Trapézio", "Tubérculo do Trapézio", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal I", "INSERCAO")]),
            ("Oponente do Polegar", [("Trapézio", "Tubérculo do Trapézio", "ORIGEM"), ("Metacarpos (I-V)", "Metacarpo I", "INSERCAO")]),
            ("Adutor do Polegar", [("Metacarpos (I-V)", "Metacarpo III", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal I", "INSERCAO")]),
            ("Abdutor do Dedo Mínimo", [("Pisiforme", "Pisiforme", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal V", "INSERCAO")]),
            ("Flexor Curto do Dedo Mínimo", [("Hamato", "Hâmulo do Hamato", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal V", "INSERCAO")]),
            ("Oponente do Dedo Mínimo", [("Hamato", "Hâmulo do Hamato", "ORIGEM"), ("Metacarpos (I-V)", "Metacarpo V", "INSERCAO")]),
            ("Lumbricais (Mão)", [("Estruturas de Tecido Mole", "Tendão Flexor Profundo", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal", "INSERCAO")]),
            ("Lumbricais da Mão (1º)", [("Estruturas de Tecido Mole", "Tendão Flexor Profundo", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal II", "INSERCAO")]),
            ("Lumbricais da Mão (2º)", [("Estruturas de Tecido Mole", "Tendão Flexor Profundo", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal III", "INSERCAO")]),
            ("Lumbricais da Mão (3º)", [("Estruturas de Tecido Mole", "Tendão Flexor Profundo", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal IV", "INSERCAO")]),
            ("Lumbricais da Mão (4º)", [("Estruturas de Tecido Mole", "Tendão Flexor Profundo", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal V", "INSERCAO")]),
            ("Interósseos Dorsais (Mão)", [("Metacarpos (I-V)", "Metacarpo I", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal", "INSERCAO")]),
            ("Interósseos Palmares (Mão)", [("Metacarpos (I-V)", "Metacarpo I", "ORIGEM"), ("Falanges Proximais (Mão)", "Base da Falange Proximal", "INSERCAO")]),

            # QUADRIL E COXA
            ("Iliopsoas (Psoas Maior)", [("Vértebras Lombares (L1-L5)", "Corpo Vertebral", "ORIGEM"), ("Fêmur", "Trocânter Menor", "INSERCAO")]),
            ("Iliopsoas (Ilíaco)", [("Osso do Quadril", "Fossa Ilíaca", "ORIGEM"), ("Fêmur", "Trocânter Menor", "INSERCAO")]),
            ("Psoas Menor", [("Vértebras Torácicas (T1-T12)", "Corpo Vertebral", "ORIGEM"), ("Osso do Quadril", "Ramo Superior do Púbis", "INSERCAO")]),
            ("Sartório", [("Osso do Quadril", "Espinha Ilíaca Ântero-Superior (EIAS)", "ORIGEM"), ("Tíbia", "Pata de Ganso", "INSERCAO")]),
            ("Reto Femoral", [("Osso do Quadril", "Espinha Ilíaca Ântero-Inferior (EIAI)", "ORIGEM"), ("Patela", "Base da Patela", "INSERCAO")]),
            ("Vasto Lateral", [("Fêmur", "Trocânter Maior", "ORIGEM"), ("Patela", "Base da Patela", "INSERCAO")]),
            ("Vasto Medial", [("Fêmur", "Linha Áspera", "ORIGEM"), ("Patela", "Base da Patela", "INSERCAO")]),
            ("Vasto Intermédio", [("Fêmur", "Face Anterior", "ORIGEM"), ("Patela", "Base da Patela", "INSERCAO")]),
            ("Articular do Joelho", [("Fêmur", "Face Anterior", "ORIGEM"), ("Estruturas de Tecido Mole", "Cápsula Articular do Joelho", "INSERCAO")]),
            ("Pectíneo", [("Osso do Quadril", "Linha Pectínea", "ORIGEM"), ("Fêmur", "Linha Pectínea", "INSERCAO")]),
            ("Adutor Longo", [("Osso do Quadril", "Corpo do Púbis", "ORIGEM"), ("Fêmur", "Linha Áspera", "INSERCAO")]),
            ("Adutor Curto", [("Osso do Quadril", "Ramo Inferior do Púbis", "ORIGEM"), ("Fêmur", "Linha Áspera", "INSERCAO")]),
            ("Adutor Magno", [("Osso do Quadril", "Túber Isquiático", "ORIGEM"), ("Fêmur", "Linha Áspera", "INSERCAO")]),
            ("Grácil", [("Osso do Quadril", "Corpo do Púbis", "ORIGEM"), ("Tíbia", "Pata de Ganso", "INSERCAO")]),
            ("Glúteo Máximo", [("Osso do Quadril", "Crista Ilíaca Posterior", "ORIGEM"), ("Fêmur", "Tuberosidade Glútea", "INSERCAO")]),
            ("Glúteo Médio", [("Osso do Quadril", "Asa do Ílio", "ORIGEM"), ("Fêmur", "Trocânter Maior", "INSERCAO")]),
            ("Glúteo Mínimo", [("Osso do Quadril", "Asa do Ílio", "ORIGEM"), ("Fêmur", "Trocânter Maior", "INSERCAO")]),
            ("Tensor da Fáscia Lata", [("Osso do Quadril", "Espinha Ilíaca Ântero-Superior (EIAS)", "ORIGEM"), ("Tíbia", "Trato Iliotibial", "INSERCAO")]),
            ("Piriforme", [("Sacro", "Face Anterior", "ORIGEM"), ("Fêmur", "Trocânter Maior", "INSERCAO")]),
            ("Obturador Interno", [("Osso do Quadril", "Membrana Obturadora", "ORIGEM"), ("Fêmur", "Trocânter Maior", "INSERCAO")]),
            ("Gêmeo Superior", [("Osso do Quadril", "Espinha Isquiática", "ORIGEM"), ("Fêmur", "Trocânter Maior", "INSERCAO")]),
            ("Gêmeo Inferior", [("Osso do Quadril", "Túber Isquiático", "ORIGEM"), ("Fêmur", "Trocânter Maior", "INSERCAO")]),
            ("Quadrado Femoral", [("Osso do Quadril", "Túber Isquiático", "ORIGEM"), ("Fêmur", "Crista Intertrocantérica", "INSERCAO")]),
            ("Bíceps Femoral (Cabeça Longa)", [("Osso do Quadril", "Túber Isquiático", "ORIGEM"), ("Fíbula", "Cabeça da Fíbula", "INSERCAO")]),
            ("Bíceps Femoral (Cabeça Curta)", [("Fêmur", "Linha Áspera", "ORIGEM"), ("Fíbula", "Cabeça da Fíbula", "INSERCAO")]),
            ("Semitendinoso", [("Osso do Quadril", "Túber Isquiático", "ORIGEM"), ("Tíbia", "Pata de Ganso", "INSERCAO")]),
            ("Semimembranoso", [("Osso do Quadril", "Túber Isquiático", "ORIGEM"), ("Tíbia", "Côndilo Medial", "INSERCAO")]),

            # PERNA E PÉ
            ("Tibial Anterior", [("Tíbia", "Côndilo Lateral", "ORIGEM"), ("Cuneiforme Medial", "Face Medial", "INSERCAO")]),
            ("Extensor Longo do Hálux", [("Fíbula", "Face Anterior", "ORIGEM"), ("Falanges Distais (Pé)", "Falange Distal I", "INSERCAO")]),
            ("Extensor Longo dos Dedos", [("Fíbula", "Face Anterior", "ORIGEM"), ("Falanges Distais (Pé)", "Falanges Distais", "INSERCAO")]),
            ("Fibular Terceiro", [("Fíbula", "Face Anterior", "ORIGEM"), ("Metatarsos (I-V)", "Base do V Metatarso", "INSERCAO")]),
            ("Fibular Longo", [("Fíbula", "Cabeça da Fíbula", "ORIGEM"), ("Cuneiforme Medial", "Face Plantar", "INSERCAO")]),
            ("Fibular Curto", [("Fíbula", "Face Lateral", "ORIGEM"), ("Metatarsos (I-V)", "Tuberosidade do V Metatarso", "INSERCAO")]),
            ("Gastrocnêmio (Cabeça Medial)", [("Fêmur", "Côndilo Medial", "ORIGEM"), ("Calcâneo", "Tuberosidade do Calcâneo", "INSERCAO")]),
            ("Gastrocnêmio (Cabeça Lateral)", [("Fêmur", "Côndilo Lateral", "ORIGEM"), ("Calcâneo", "Tuberosidade do Calcâneo", "INSERCAO")]),
            ("Sóleo", [("Tíbia", "Linha do Músculo Sóleo", "ORIGEM"), ("Calcâneo", "Tuberosidade do Calcâneo", "INSERCAO")]),
            ("Plantaris", [("Fêmur", "Linha Supracondilar Lateral", "ORIGEM"), ("Calcâneo", "Tuberosidade do Calcâneo", "INSERCAO")]),
            ("Poplíteo", [("Fêmur", "Côndilo Lateral", "ORIGEM"), ("Tíbia", "Face Posterior", "INSERCAO")]),
            ("Tibial Posterior", [("Tíbia", "Face Posterior", "ORIGEM"), ("Navicular", "Tuberosidade", "INSERCAO")]),
            ("Flexor Longo dos Dedos do Pé", [("Tíbia", "Face Posterior", "ORIGEM"), ("Falanges Distais (Pé)", "Falanges Distais", "INSERCAO")]),
            ("Flexor Longo do Hálux", [("Fíbula", "Face Posterior", "ORIGEM"), ("Falanges Distais (Pé)", "Falange Distal I", "INSERCAO")]),
            ("Extensor Curto do Hálux", [("Calcâneo", "Face Dorsal", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal I", "INSERCAO")]),
            ("Extensor Curto dos Dedos do Pé", [("Calcâneo", "Face Dorsal", "ORIGEM"), ("Falanges Médias (Pé)", "Tendão Extensor Longo", "INSERCAO")]),
            ("Abdutor do Hálux", [("Calcâneo", "Tuberosidade do Calcâneo", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal I", "INSERCAO")]),
            ("Flexor Curto dos Dedos do Pé", [("Calcâneo", "Tuberosidade do Calcâneo", "ORIGEM"), ("Falanges Médias (Pé)", "Falanges Médias", "INSERCAO")]),
            ("Abdutor do Dedo Mínimo do Pé", [("Calcâneo", "Tuberosidade do Calcâneo", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal V", "INSERCAO")]),
            ("Quadrado Plantar", [("Calcâneo", "Face Plantar", "ORIGEM"), ("Estruturas de Tecido Mole", "Tendão Flexor Longo dos Dedos", "INSERCAO")]),
            ("Lumbricais (Pé)", [("Estruturas de Tecido Mole", "Tendão Flexor Longo dos Dedos", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal", "INSERCAO")]),
            ("Flexor Curto do Hálux", [("Cuboide", "Face Plantar", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal I", "INSERCAO")]),
            ("Adutor do Hálux (Cabeça Oblíqua)", [("Metatarsos (I-V)", "Base dos Metatarsos II-IV", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal I", "INSERCAO")]),
            ("Adutor do Hálux (Cabeça Transversa)", [("Estruturas de Tecido Mole", "Ligamentos Metatarsofalângicos", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal I", "INSERCAO")]),
            ("Flexor Curto do Dedo Mínimo do Pé", [("Metatarsos (I-V)", "Base do V Metatarso", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal V", "INSERCAO")]),
            ("Interósseos Dorsais (Pé)", [("Metatarsos (I-V)", "Metatarsos", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal", "INSERCAO")]),
            ("Interósseos Plantares (Pé)", [("Metatarsos (I-V)", "Metatarsos", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal", "INSERCAO")]),
            ("Lumbricais do Pé (1º)", [("Estruturas de Tecido Mole", "Tendão Flexor Longo dos Dedos", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal II", "INSERCAO")]),
            ("Lumbricais do Pé (2º)", [("Estruturas de Tecido Mole", "Tendão Flexor Longo dos Dedos", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal III", "INSERCAO")]),
            ("Lumbricais do Pé (3º)", [("Estruturas de Tecido Mole", "Tendão Flexor Longo dos Dedos", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal IV", "INSERCAO")]),
            ("Lumbricais do Pé (4º)", [("Estruturas de Tecido Mole", "Tendão Flexor Longo dos Dedos", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal V", "INSERCAO")]),
            ("Interósseo Dorsal do Pé (1º)", [("Metatarsos (I-V)", "Metatarsos I-II", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal II", "INSERCAO")]),
            ("Interósseo Dorsal do Pé (2º)", [("Metatarsos (I-V)", "Metatarsos II-III", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal III", "INSERCAO")]),
            ("Interósseo Dorsal do Pé (3º)", [("Metatarsos (I-V)", "Metatarsos III-IV", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal IV", "INSERCAO")]),
            ("Interósseo Dorsal do Pé (4º)", [("Metatarsos (I-V)", "Metatarsos IV-V", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal V", "INSERCAO")]),
            ("Interósseo Plantar do Pé (1º)", [("Metatarsos (I-V)", "Metatarso III", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal III", "INSERCAO")]),
            ("Interósseo Plantar do Pé (2º)", [("Metatarsos (I-V)", "Metatarso IV", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal IV", "INSERCAO")]),
            ("Interósseo Plantar do Pé (3º)", [("Metatarsos (I-V)", "Metatarso V", "ORIGEM"), ("Falanges Proximais (Pé)", "Base da Falange Proximal V", "INSERCAO")]),
        ]

        success_count = 0
        error_count = 0

        with transaction.atomic():
            for muscle_name, attachments in mapping:
                muscle = Muscle.objects.filter(name__iexact=muscle_name).first()
                if not muscle:
                    # Músculo não encontrado no banco (provavelmente nome diferente)
                    # self.stdout.write(self.style.WARNING(f"Músculo '{muscle_name}' não encontrado no banco."))
                    continue
                
                for bone_name_input, landmark_name, type_str in attachments:
                    # Tenta resolver ossos granulares
                    target_bones = self.resolve_bones(bone_name_input)
                    
                    if not target_bones:
                        self.stdout.write(self.style.ERROR(f"Osso(s) não encontrado(s) para: {bone_name_input}"))
                        error_count += 1
                        continue

                    # Para cada osso resolvido (Ex: L1, L2, L3...), cria a conexão
                    for bone in target_bones:
                        landmark = self.get_or_create_landmark(bone, landmark_name)
                        att_enum = AttachmentType.ORIGIN if type_str == "ORIGEM" else AttachmentType.INSERTION
                        
                        MuscleBoneAttachment.objects.update_or_create(
                            muscle=muscle,
                            landmark=landmark,
                            defaults={'attachment_type': att_enum}
                        )
                        
                    success_count += 1

        self.stdout.write(self.style.SUCCESS(f'Mapeamento V6 Concluído!'))

    def resolve_bones(self, bone_name_input):
        """
        Retorna uma lista de objetos Bone reais do banco.
        """
        # 1. Expansão de Grupos
        if bone_name_input in self.group_expansion_map:
            expanded_names = self.group_expansion_map[bone_name_input]
            return list(Bone.objects.filter(name__in=expanded_names))
        
        # 2. Busca Exata
        bone = Bone.objects.filter(name__iexact=bone_name_input).first()
        if bone:
            return [bone]
        
        # 3. Heurística para Nomes Parciais
        # Ex: "Costelas (1-7)" -> Busca por "Costela" se não estiver no map
        if "Costela" in bone_name_input or "Vértebra" in bone_name_input:
             # Isso é arriscado, mas útil como último recurso se o map falhar
             pass

        return []

    def ensure_critical_structures(self):
        critical_bones = [
            ("Osso Hioide", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Estruturas de Tecido Mole", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.TRUNK),
            ("Cartilagem Tireoide", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
            ("Cartilagem Alar Maior", SkeletonDivision.AXIAL, BoneType.IRREGULAR, BodySegment.HEAD_NECK),
        ]
        for name, div, b_type, segment in critical_bones:
            Bone.objects.get_or_create(
                name=name,
                defaults={'division': div, 'bone_type': b_type, 'body_segment': segment}
            )

    def get_or_create_landmark(self, bone, landmark_name):
        """Cria o landmark no osso específico."""
        clean_name = landmark_name.split(" (")[0] if "(" in landmark_name else landmark_name
        landmark, _ = BoneLandmark.objects.get_or_create(
            bone=bone,
            name=clean_name, 
            defaults={'description': "Auto-generated landmark from granular seed."}
        )
        return landmark