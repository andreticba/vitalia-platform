# backend/medical/management/commands/enrich_structures.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Joint, JointStructure

class Command(BaseCommand):
    help = 'Enriquece as Estruturas Articulares: Adiciona Ligamentos, Meniscos, Discos e Bursas.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando detalhamento das estruturas articulares...'))

        # Lista Mestra de Estruturas
        # Formato: (Nome da Articulação, Nome da Estrutura, Tipo, Descrição)
        structures_data = [
            # ========================================================
            # 1. OMBRO E CÍNGULO (Bursas são críticas aqui)
            # ========================================================
            ("Articulação Glenoumeral (Ombro)", "Lábio Glenoidal", "CARTILAGEM", "Fibrocartilagem que aprofunda a cavidade glenoide, aumentando a estabilidade."),
            ("Articulação Glenoumeral (Ombro)", "Ligamentos Glenoumerais (Sup/Med/Inf)", "LIGAMENTO", "Reforços anteriores da cápsula articular. Evitam luxação anterior."),
            ("Articulação Glenoumeral (Ombro)", "Ligamento Coracoacromial", "LIGAMENTO", "Forma o arco coracoacromial. Impede o deslocamento superior da cabeça do úmero."),
            ("Articulação Glenoumeral (Ombro)", "Bolsa Subacromial", "BOLSA", "Reduz atrito entre o supraespinhal e o acrômio. Local comum de bursite."),
            ("Articulação Glenoumeral (Ombro)", "Tendão da Cabeça Longa do Bíceps", "TENDAO", "Passa pelo sulco intertubercular; atua como estabilizador anterior."),

            ("Articulação Acromioclavicular", "Ligamento Acromioclavicular", "LIGAMENTO", "Reforça a cápsula superiormente."),
            ("Articulação Acromioclavicular", "Ligamento Coracoclavicular", "LIGAMENTO", "Principal estabilizador vertical (composto pelos ligamentos Conoide e Trapezoide)."),

            # ========================================================
            # 2. COTOVELO E ANTEBRAÇO
            # ========================================================
            ("Articulação do Cotovelo", "Ligamento Colateral Ulnar", "LIGAMENTO", "Estabiliza contra estresse em valgo (muito exigido em arremessos)."),
            ("Articulação do Cotovelo", "Ligamento Colateral Radial", "LIGAMENTO", "Estabiliza contra estresse em varo."),
            ("Articulação Radioulnar Proximal", "Ligamento Anular", "LIGAMENTO", "Envolve a cabeça do rádio, mantendo-a junto à ulna durante a pronação/supinação."),

            # ========================================================
            # 3. PUNHO E MÃO
            # ========================================================
            ("Articulação Radiocarpal (Punho)", "Complexo de Fibrocartilagem Triangular (TFCC)", "DISCO/LIGAMENTO", "Estabiliza o lado ulnar do punho e absorve carga."),
            ("Articulação Radiocarpal (Punho)", "Ligamento Colateral Radial do Carpo", "LIGAMENTO", "Estabiliza o lado lateral do punho."),
            ("Articulação Radiocarpal (Punho)", "Ligamento Colateral Ulnar do Carpo", "LIGAMENTO", "Estabiliza o lado medial do punho."),
            
            # Túnel do Carpo (Estrutura funcional, não articular pura, mas vital)
            ("Articulação Radiocarpal (Punho)", "Retináculo dos Flexores", "LIGAMENTO", "Teto do túnel do carpo. Comprime o nervo mediano se inflamado."),

            # ========================================================
            # 4. QUADRIL E PELVE
            # ========================================================
            ("Articulação Coxofemoral (Quadril)", "Lábio do Acetábulo", "CARTILAGEM", "Anel de fibrocartilagem que aprofunda o acetábulo e selamento a vácuo."),
            ("Articulação Coxofemoral (Quadril)", "Ligamento Iliofemoral", "LIGAMENTO", "Ligamento em Y (Bigelow). O mais forte do corpo. Evita hiperextensão."),
            ("Articulação Coxofemoral (Quadril)", "Ligamento Pubofemoral", "LIGAMENTO", "Evita abdução excessiva."),
            ("Articulação Coxofemoral (Quadril)", "Ligamento Isquiofemoral", "LIGAMENTO", "Estabiliza posteriormente e limita a rotação medial."),
            ("Articulação Coxofemoral (Quadril)", "Ligamento da Cabeça do Fêmur", "LIGAMENTO", "Conduz a artéria para a cabeça do fêmur."),

            ("Articulação Sacroilíaca", "Ligamentos Sacroilíacos (Ant/Post)", "LIGAMENTO", "Extremamente fortes, suportam o peso do tronco."),

            # ========================================================
            # 5. JOELHO (Complexo)
            # ========================================================
            ("Articulação do Joelho", "Menisco Medial", "MENISCO", "Formato de C, fixo à cápsula. Absorção de choque e estabilidade."),
            ("Articulação do Joelho", "Menisco Lateral", "MENISCO", "Formato quase circular (O), mais móvel que o medial."),
            ("Articulação do Joelho", "Ligamento Cruzado Anterior (LCA)", "LIGAMENTO", "Impede translação anterior da tíbia e rotação excessiva."),
            ("Articulação do Joelho", "Ligamento Cruzado Posterior (LCP)", "LIGAMENTO", "Impede translação posterior da tíbia. Principal estabilizador do joelho fletido."),
            ("Articulação do Joelho", "Ligamento Colateral Tibial (Medial)", "LIGAMENTO", "Estabiliza contra estresse em valgo. Fibras profundas ligadas ao menisco medial."),
            ("Articulação do Joelho", "Ligamento Colateral Fibular (Lateral)", "LIGAMENTO", "Estabiliza contra estresse em varo."),
            ("Articulação do Joelho", "Ligamento Patelar", "LIGAMENTO", "Continuação do tendão do quadríceps. Transmite força para a tíbia."),
            ("Articulação do Joelho", "Bolsa Pré-patelar", "BOLSA", "Entre a pele e a patela. Inflama em 'joelho de doméstica'."),

            # ========================================================
            # 6. TORNOZELO E PÉ
            # ========================================================
            ("Articulação Talocrural (Tornozelo)", "Ligamento Talofibular Anterior (LTFA)", "LIGAMENTO", "Mais fraco e mais comum em entorses (inversão)."),
            ("Articulação Talocrural (Tornozelo)", "Ligamento Calcaneofibular", "LIGAMENTO", "Estabiliza lateralmente."),
            ("Articulação Talocrural (Tornozelo)", "Ligamento Talofibular Posterior", "LIGAMENTO", "Estabiliza posteriormente."),
            ("Articulação Talocrural (Tornozelo)", "Ligamento Deltoide", "LIGAMENTO", "Complexo medial forte (4 partes). Previne eversão excessiva."),
            
            ("Articulação Subtalar", "Fáscia Plantar", "FASCIA", "Aponeurose espessa que sustenta o arco longitudinal do pé. Causa de fascite."),
            ("Articulação Subtalar", "Ligamento Mola (Calcaneonavicular)", "LIGAMENTO", "Sustenta a cabeça do tálus e o arco do pé."),

            # ========================================================
            # 7. COLUNA VERTEBRAL (CRÍTICO PARA POSTURA)
            # ========================================================
            ("Discos Intervertebrais", "Anel Fibroso", "CARTILAGEM", "Camada externa resistente do disco. Contém o núcleo."),
            ("Discos Intervertebrais", "Núcleo Pulposo", "GELATINOSO", "Centro do disco, absorve choque hidráulico. Extravasa na hérnia."),
            ("Discos Intervertebrais", "Ligamento Longitudinal Anterior", "LIGAMENTO", "Larga faixa anterior aos corpos vertebrais. Limita extensão."),
            ("Discos Intervertebrais", "Ligamento Longitudinal Posterior", "LIGAMENTO", "Faixa posterior aos corpos (dentro do canal). Limita flexão."),
            ("Discos Intervertebrais", "Ligamento Amarelo", "LIGAMENTO", "Elástico, conecta as lâminas das vértebras. Ajuda a retornar à postura ereta."),

            # ========================================================
            # 8. ATM (CABEÇA)
            # ========================================================
            ("Articulação Temporomandibular (ATM)", "Disco Articular (ATM)", "DISCO", "Bicôncavo, divide a articulação em dois compartimentos. Desloca-se nos estalidos."),
            ("Articulação Temporomandibular (ATM)", "Ligamento Lateral (Temporomandibular)", "LIGAMENTO", "Evita deslocamento posterior da mandíbula."),
            ("Articulação Temporomandibular (ATM)", "Ligamento Estilomandibular", "LIGAMENTO", "Limita a protrusão excessiva da mandíbula."),
            ("Articulação Temporomandibular (ATM)", "Ligamento Esfenomandibular", "LIGAMENTO", "Suporte passivo da mandíbula."),
        ]

        success_count = 0
        error_count = 0

        with transaction.atomic():
            for joint_name, struct_name, struct_type, desc in structures_data:
                try:
                    joint = Joint.objects.get(name=joint_name)
                    
                    # Update ou Create
                    obj, created = JointStructure.objects.update_or_create(
                        joint=joint,
                        name=struct_name,
                        defaults={
                            'type_description': struct_type, # Ajuste conforme o nome do campo no seu model
                            'description': desc
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"Criada: {struct_name}")
                    else:
                        # self.stdout.write(f"Atualizada: {struct_name}")
                        pass
                    
                    success_count += 1

                except Joint.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Articulação não encontrada: {joint_name} (Estrutura: {struct_name})"))
                    error_count += 1

        self.stdout.write(self.style.SUCCESS('--------------------------------------'))
        self.stdout.write(self.style.SUCCESS(f'Estruturas processadas: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Falhas: {error_count}'))
        self.stdout.write(self.style.SUCCESS('Base de Estruturas Articulares (Ligamentos/Discos/Bursas): Carregada.'))