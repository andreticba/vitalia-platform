# backend/medical/management/commands/enrich_joints.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Joint, JointStructuralType, SynovialType

class Command(BaseCommand):
    help = 'Enriquece a base de dados de Articulações: Classificação biomecânica e expansão do mapa corporal.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando enriquecimento das articulações...'))

        # Lista Mestra de Articulações
        # Formato: (Nome PT-BR, Tipo Estrutural, Tipo Sinovial, Descrição/Notas)
        joints_data = [
            # ========================================================
            # === ATUALIZAÇÃO DAS 8 EXISTENTES ===
            # ========================================================
            (
                "Articulação Glenoumeral (Ombro)", 
                JointStructuralType.SYNOVIAL, 
                SynovialType.BALL_AND_SOCKET,
                "Principal articulação do ombro. Alta mobilidade, baixa estabilidade."
            ),
            (
                "Articulação do Cotovelo", 
                JointStructuralType.SYNOVIAL, 
                SynovialType.HINGE,
                "Complexo umerulnar e umerorradial. Permite flexão e extensão."
            ),
            (
                "Articulação Coxofemoral (Quadril)", 
                JointStructuralType.SYNOVIAL, 
                SynovialType.BALL_AND_SOCKET,
                "Conexão entre fêmur e pelve. Alta estabilidade para suporte de carga."
            ),
            (
                "Articulação do Joelho", 
                JointStructuralType.SYNOVIAL, 
                SynovialType.HINGE, # Gínglimo modificado
                "Complexo tibiofemoral e patelofemoral. Maior articulação do corpo."
            ),
            (
                "Sutura Coronal", 
                JointStructuralType.FIBROUS, 
                SynovialType.NOT_APPLICABLE,
                "Articulação imóvel entre o osso frontal e os parietais."
            ),
            (
                "Articulação Temporomandibular (ATM)", 
                JointStructuralType.SYNOVIAL, 
                SynovialType.CONDYLOID, # Bicondilar/Gínglimo modificado
                "Permite mastigação e fala. Conecta mandíbula ao osso temporal."
            ),
            (
                "Articulação Radiocarpal (Punho)", 
                JointStructuralType.SYNOVIAL, 
                SynovialType.CONDYLOID,
                "Conecta o rádio aos ossos do carpo (escafoide e semilunar)."
            ),
            (
                "Articulação Talocrural (Tornozelo)", 
                JointStructuralType.SYNOVIAL, 
                SynovialType.HINGE,
                "Articulação principal do tornozelo (tíbia, fíbula e tálus)."
            ),

            # ========================================================
            # === NOVAS ARTICULAÇÕES (EXPANSÃO ESSENCIAL) ===
            # ========================================================

            # --- Cabeça e Coluna (Axial) ---
            (
                "Sutura Sagital",
                JointStructuralType.FIBROUS,
                SynovialType.NOT_APPLICABLE,
                "Entre os dois ossos parietais."
            ),
            (
                "Sutura Lambdoide",
                JointStructuralType.FIBROUS,
                SynovialType.NOT_APPLICABLE,
                "Entre os ossos parietais e o occipital."
            ),
            (
                "Articulação Atlanto-occipital",
                JointStructuralType.SYNOVIAL,
                SynovialType.CONDYLOID,
                "Entre o Atlas (C1) e o crânio. Permite o movimento de 'Sim' com a cabeça."
            ),
            (
                "Articulação Atlanto-axial",
                JointStructuralType.SYNOVIAL,
                SynovialType.PIVOT,
                "Entre Atlas (C1) e Áxis (C2). Permite o movimento de 'Não' (rotação)."
            ),
            (
                "Discos Intervertebrais",
                JointStructuralType.CARTILAGINOUS,
                SynovialType.NOT_APPLICABLE,
                "Sínfises entre os corpos vertebrais. Absorção de impacto."
            ),
            (
                "Articulações Zigapofisárias (Facetas)",
                JointStructuralType.SYNOVIAL,
                SynovialType.PLANE,
                "Articulações entre os arcos vertebrais. Guiam o movimento da coluna."
            ),

            # --- Membro Superior (Cíngulo e Mão) ---
            (
                "Articulação Esternoclavicular",
                JointStructuralType.SYNOVIAL,
                SynovialType.SADDLE,
                "Única conexão óssea direta entre o membro superior e o tronco."
            ),
            (
                "Articulação Acromioclavicular",
                JointStructuralType.SYNOVIAL,
                SynovialType.PLANE,
                "Conecta a clavícula à escápula. Frequentemente lesionada (luxação)."
            ),
            (
                "Articulação Radioulnar Proximal",
                JointStructuralType.SYNOVIAL,
                SynovialType.PIVOT,
                "Permite a pronação e supinação do antebraço (próximo ao cotovelo)."
            ),
            (
                "Articulação Carpometacarpal do Polegar",
                JointStructuralType.SYNOVIAL,
                SynovialType.SADDLE,
                "Articulação em sela clássica. Permite a oposição do polegar."
            ),
            (
                "Articulações Metacarpofalângicas (Mão)",
                JointStructuralType.SYNOVIAL,
                SynovialType.CONDYLOID,
                "Os 'nós' dos dedos. Permitem flexão, extensão, abdução e adução."
            ),
            (
                "Articulações Interfalângicas (Mão)",
                JointStructuralType.SYNOVIAL,
                SynovialType.HINGE,
                "Articulações dobradiça entre as falanges dos dedos."
            ),

            # --- Membro Inferior (Pelve e Pé) ---
            (
                "Articulação Sacroilíaca",
                JointStructuralType.SYNOVIAL,
                SynovialType.PLANE, # Parte sinovial e parte fibrosa
                "Conecta a coluna à pelve. Transfere carga do tronco para as pernas."
            ),
            (
                "Sínfise Púbica",
                JointStructuralType.CARTILAGINOUS,
                SynovialType.NOT_APPLICABLE,
                "União anterior dos ossos do quadril. Pouco móvel."
            ),
            (
                "Articulação Subtalar",
                JointStructuralType.SYNOVIAL,
                SynovialType.PLANE,
                "Abaixo do tálus. Responsável pela inversão e eversão do pé."
            ),
            (
                "Articulações Metatarsofalângicas (Pé)",
                JointStructuralType.SYNOVIAL,
                SynovialType.CONDYLOID,
                "Conexão entre o pé e os dedos."
            ),
            (
                "Articulações Interfalângicas (Pé)",
                JointStructuralType.SYNOVIAL,
                SynovialType.HINGE,
                "Articulações dos dedos do pé."
            ),
        ]

        updated_count = 0
        created_count = 0

        with transaction.atomic():
            for name, struct_type, syn_type, desc in joints_data:
                obj, created = Joint.objects.update_or_create(
                    name=name,
                    defaults={
                        'structural_type': struct_type,
                        'synovial_type': syn_type,
                        'description': desc
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"Criada: {name}")
                else:
                    updated_count += 1
                    # self.stdout.write(f"Atualizada: {name}")

        self.stdout.write(self.style.SUCCESS(f'Processo Finalizado.'))
        self.stdout.write(self.style.SUCCESS(f'Articulações Criadas: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Articulações Atualizadas: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total na Base: {Joint.objects.count()}'))