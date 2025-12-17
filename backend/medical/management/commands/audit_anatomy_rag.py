# backend/medical/management/commands/audit_anatomy_rag.py em 2025-12-14 11:48

import json
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from medical.models import Bone, BoneType, Muscle
from core.models import AuditLog
from core.services import RAGService
from core.clients import ollama_client

class Command(BaseCommand):
    help = 'Audita e corrige dados de Anatomia (Ossos/Músculos) usando RAG e Literatura Ingerida.'

    def add_arguments(self, parser):
        parser.add_argument('--target', type=str, choices=['bones', 'muscles'], default='bones', help='O que auditar?')
        parser.add_argument('--dry-run', action='store_true', help='Apenas simula e mostra o que mudaria.')
        parser.add_argument('--limit', type=int, default=10, help='Quantos itens auditar por vez (para teste).')

    def handle(self, *args, **options):
        self.rag = RAGService()
        self.dry_run = options['dry_run']
        target = options['target']
        limit = options['limit']

        self.stdout.write(self.style.WARNING(f"Iniciando Auditoria ({target.upper()})... Modo Dry-Run: {self.dry_run}"))

        if target == 'bones':
            self.audit_bones(limit)
        elif target == 'muscles':
            self.audit_muscles(limit)

    def audit_bones(self, limit):
        bones = Bone.objects.all().order_by('name')[:limit]
        
        for bone in bones:
            self.stdout.write(f"\n🔍 Auditando Osso: {bone.name}...")
            
            # 1. Expansão de Consulta (A Ponte do Latim)
            # Perguntamos ao LLM os termos de busca antes de ir ao vetor
            search_terms = self._get_search_terms(bone.name, "bone")
            query = f"{bone.name} OR {search_terms}"
            
            # 2. Recuperação (Retrieval)
            evidence_list = self.rag.search_for_audit(query, limit=3)
            if not evidence_list:
                self.stdout.write(self.style.ERROR("  > Nenhuma evidência encontrada nos livros."))
                continue

            context_text = "\n".join([f"[{e['source']}]: {e['content']}" for e in evidence_list])

            # 3. Análise (Generation)
            prompt = f"""
            Aja como um Anatomista Sênior. Use o CONTEXTO abaixo (que pode estar em Inglês) para corrigir os dados do banco (em Português).

            DADOS ATUAIS NO BANCO:
            - Nome: {bone.name}
            - Nome Científico: {bone.scientific_name}
            - Tipo Atual: {bone.bone_type}
            - Descrição Atual: {bone.description}

            CONTEXTO (LITERATURA):
            {context_text}

            TAREFA:
            1. Identifique o Nome Científico (Latim) correto.
            2. Classifique o Tipo do osso (LONG, SHORT, FLAT, IRREGULAR, SESAMOID).
            3. Escreva uma descrição técnica resumida em PORTUGUÊS BRASILEIRO.
            
            REGRA: Se o contexto não tiver a informação, mantenha o valor atual ou retorne null.

            SAÍDA JSON:
            {{
                "scientific_name": "...",
                "bone_type": "...",
                "description_pt": "...",
                "justification": "Por que mudou? Cite a fonte.",
                "confidence": "HIGH/LOW"
            }}
            """
            
            ai_result = self._call_llm(prompt)
            if ai_result:
                self._apply_bone_changes(bone, ai_result, evidence_list)

    def audit_muscles(self, limit):
        # Foca nos que não têm descrição ou têm dados suspeitos
        muscles = Muscle.objects.all().order_by('name')[:limit]

        for muscle in muscles:
            self.stdout.write(f"\n💪 Auditando Músculo: {muscle.name}...")
            
            search_terms = self._get_search_terms(muscle.name, "muscle")
            query = f"{muscle.name} anatomy origin insertion action {search_terms}"
            
            evidence_list = self.rag.search_for_audit(query, limit=4)
            if not evidence_list:
                self.stdout.write(self.style.ERROR("  > Sem evidência."))
                continue

            context_text = "\n".join([f"[{e['source']}]: {e['content']}" for e in evidence_list])

            prompt = f"""
            Aja como um Cinesiologista. Use o CONTEXTO (Inglês/Português) para corrigir os dados do músculo (Português).

            MÚSCULO: {muscle.name}
            
            CONTEXTO EXTRAÍDO DOS LIVROS:
            {context_text}

            TAREFA:
            1. Extraia a Origem e Inserção descritiva (em PT-BR).
            2. Resuma a Ação Principal (em PT-BR).
            
            SAÍDA JSON:
            {{
                "origin_text": "...",
                "insertion_text": "...",
                "description": "Ação principal...",
                "scientific_name": "Nome em Latim (se houver)",
                "found_in_text": true
            }}
            """
            
            ai_result = self._call_llm(prompt)
            if ai_result and ai_result.get('found_in_text'):
                self._apply_muscle_changes(muscle, ai_result, evidence_list)

    def _get_search_terms(self, name, type_obj):
        """Usa o LLM (Zero-Shot) para descobrir o nome em Latim/Inglês para melhorar a busca."""
        prompt = f"Retorne apenas o nome em Latim e em Inglês para o {type_obj} '{name}'. Formato: 'LatinName OR EnglishName'."
        try:
            resp = ollama_client.generate(settings.OLLAMA_GENERATION_MODEL, prompt)
            return resp.get('response', '').strip().replace('"', '')
        except:
            return ""

    def _call_llm(self, prompt):
        try:
            resp = ollama_client.generate(
                settings.OLLAMA_GENERATION_MODEL, 
                prompt, 
                is_json=True,
                options={"temperature": 0.1}
            )
            return json.loads(resp.get('response', '{}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  > Erro LLM: {e}"))
            return None

    def _apply_bone_changes(self, bone, data, evidence):
        """Aplica as mudanças e loga no AuditLog."""
        changes = []
        
        # Normalização de Tipo
        type_map = {
            'LONG': BoneType.LONG, 'LONGO': BoneType.LONG,
            'FLAT': BoneType.FLAT, 'PLANO': BoneType.FLAT,
            'SHORT': BoneType.SHORT, 'CURTO': BoneType.SHORT,
            'IRREGULAR': BoneType.IRREGULAR,
            'SESAMOID': BoneType.SESAMOID
        }
        
        new_type = type_map.get(data.get('bone_type', '').upper())
        if new_type and new_type != bone.bone_type:
            changes.append(f"Tipo: {bone.bone_type} -> {new_type}")
            bone.bone_type = new_type

        new_sci = data.get('scientific_name')
        if new_sci and new_sci != bone.scientific_name:
            changes.append(f"Latim: {bone.scientific_name} -> {new_sci}")
            bone.scientific_name = new_sci

        new_desc = data.get('description_pt')
        if new_desc and len(new_desc) > len(bone.description or ""):
            changes.append("Descrição atualizada (Enriquecida)")
            bone.description = new_desc

        if changes:
            self.stdout.write(self.style.SUCCESS(f"  > Modificações propostas: {', '.join(changes)}"))
            
            if not self.dry_run:
                bone.save()
                # Cria Log de Evidência
                AuditLog.objects.create(
                    action=AuditLog.ActionType.AI_DECISION,
                    target_object_id=str(bone.id), # Cast para string pois é UUID
                    # target_content_type... (precisaria buscar o ContentType do Bone, simplificando aqui)
                    details={
                        "changes": changes,
                        "justification": data.get('justification'),
                        "source_evidence": [e['source'] for e in evidence[:2]] # Salva as fontes usadas
                    },
                    ai_reasoning_snapshot=data
                )
                self.stdout.write("  > Salvo no banco e auditado.")
        else:
            self.stdout.write("  > Nenhuma mudança necessária.")

    def _apply_muscle_changes(self, muscle, data, evidence):
        # Lógica similar para músculos, atualizando origin_text, insertion_text...
        if not self.dry_run:
            muscle.origin_text = data.get('origin_text', muscle.origin_text)
            muscle.insertion_text = data.get('insertion_text', muscle.insertion_text)
            muscle.description = data.get('description', muscle.description)
            muscle.scientific_name = data.get('scientific_name', muscle.scientific_name)
            muscle.save()
            self.stdout.write(self.style.SUCCESS(f"  > Músculo {muscle.name} atualizado com dados dos livros."))