# backend/medical/management/commands/audit_anatomy_enrichment.py em 2025-12-14 11:48

import json
from django.core.management.base import BaseCommand
from django.conf import settings
from medical.models import Bone
from core.models import AuditLog
from core.services import RAGService
from core.clients import ollama_client

class Command(BaseCommand):
    help = 'Enriquece Descrições e Notas Clínicas dos Ossos usando RAG (Blindado para PT-BR).'

    def handle(self, *args, **kwargs):
        self.rag = RAGService()
        
        # Pega todos os ossos ordenados
        bones = Bone.objects.all().order_by('name')
        total = bones.count()
        
        self.stdout.write(self.style.WARNING(f'Iniciando Enriquecimento Textual para {total} ossos...'))

        for i, bone in enumerate(bones):
            # Se já tem notas clínicas detalhadas, podemos pular
            if len(bone.clinical_notes) > 50: 
                continue

            self.stdout.write(f"[{i+1}/{total}] Enriquecendo: {bone.name} ({bone.scientific_name})...")
            
            # 1. Recuperação (Retrieval) - Busca híbrida (PT/EN/Latim)
            query = f"{bone.name} {bone.scientific_name or ''} anatomy clinical relevance fractures landmarks function"
            
            # Busca no Knowledge Base
            evidence_list = self.rag.search_for_audit(query, limit=4)
            
            if not evidence_list:
                self.stdout.write(self.style.ERROR("  > Sem evidência nos livros. Pulando."))
                continue

            context_text = "\n".join([f"- {e['content']}" for e in evidence_list])

            # 2. Geração (Prompt Blindado para PT-BR)
            prompt = f"""
            Você é um Professor de Anatomia e Ortopedia Brasileiro.
            Sua tarefa é ler o contexto (que pode estar em Inglês) e gerar conteúdo técnico estritamente em PORTUGUÊS DO BRASIL.

            OSSO ALVO: "{bone.name}" (Latim: {bone.scientific_name})

            CONTEXTO (LITERATURA - FONTE DA VERDADE):
            {context_text}

            DIRETRIZES DE TRADUÇÃO E ESTILO:
            1. IDIOMA DE SAÍDA: APENAS PORTUGUÊS (PT-BR). Não use inglês.
            2. Se o texto fonte disser "Neck of femur", escreva "Colo do fêmur".
            3. Mantenha tom acadêmico e clínico.

            CAMPOS A GERAR:
            1. description: Resuma a localização, forma, com quem se articula e função biomecânica.
            2. clinical_notes: Relevância clínica (o que acontece se quebrar?), marcos de palpação ou patologias associadas.
            
            FORMATO JSON OBRIGATÓRIO:
            {{
                "description": "Texto em português...",
                "clinical_notes": "Texto em português..."
            }}
            """

            try:
                # Chamada ao LLM
                response = ollama_client.generate(
                    settings.OLLAMA_GENERATION_MODEL, 
                    prompt, 
                    is_json=True,
                    options={"temperature": 0.1} # Baixa criatividade para garantir adesão à instrução
                )
                
                # Tratamento robusto do retorno
                raw_json = response.get('response', '{}')
                ai_data = json.loads(raw_json)

                # 3. Persistência
                new_desc = ai_data.get('description')
                new_notes = ai_data.get('clinical_notes')
                
                updated = False
                
                # Só salva se tiver conteúdo relevante e estiver em Português (heurística simples)
                if new_desc and len(new_desc) > len(bone.description or ""):
                    bone.description = new_desc
                    updated = True
                
                if new_notes and len(new_notes) > 10:
                    bone.clinical_notes = new_notes
                    updated = True

                if updated:
                    bone.save()
                    self.stdout.write(self.style.SUCCESS("  > Atualizado com sucesso."))
                    
                    # Log de Auditoria (Evidência)
                    AuditLog.objects.create(
                        action='AI_DECISION',
                        target_object_id=str(bone.id),
                        # target_content_type será preenchido se necessário, ou usamos GenericFK
                        details={
                            "field": "enrichment_pt_br",
                            "source_evidence": [e['source'] for e in evidence_list[:2]]
                        },
                        ai_reasoning_snapshot=ai_data
                    )
                else:
                    self.stdout.write("  > Nenhuma informação nova relevante gerada.")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  > Erro ao processar: {e}"))

        self.stdout.write(self.style.SUCCESS('Enriquecimento PT-BR Concluído!'))