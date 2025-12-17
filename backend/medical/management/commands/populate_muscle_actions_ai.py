# backend/medical/management/commands/populate_muscle_actions_ai.py em 2025-12-14 11:48

import json
import httpx
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from medical.models import Muscle, JointMovement, MuscleAction, MuscleRole

class Command(BaseCommand):
    help = 'Popula a tabela MuscleAction usando IA Local (Ollama/Llama3) conectada ao banco.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando Inteligência Cinesiológica via Ollama...'))

        # 1. Preparar Contexto
        movements_qs = JointMovement.objects.select_related('joint').all()
        valid_movements_list = [f"{m.name} ({m.joint.name})" for m in movements_qs]
        movement_map = {name.upper(): m_obj for name, m_obj in zip(valid_movements_list, movements_qs)}

        self.stdout.write(f"Carregados {len(valid_movements_list)} movimentos válidos do banco.")

        ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        model = settings.OLLAMA_GENERATION_MODEL

        # 2. Processamento em Lotes
        muscles_qs = Muscle.objects.all().order_by('name')
        # Reduzi o batch para 3 para diminuir a chance de alucinação estrutural
        batch_size = 3 
        total_muscles = muscles_qs.count()
        
        processed_count = 0
        success_actions = 0

        roles_text = "\n".join([f"- {choice[0]}" for choice in MuscleRole.choices])

        for i in range(0, total_muscles, batch_size):
            batch_muscles = muscles_qs[i:i+batch_size]
            batch_names = [m.name for m in batch_muscles]
            
            self.stdout.write(f"Processando lote {i}/{total_muscles}: {', '.join(batch_names)}...")

            prompt = f"""
            Aja como um Especialista em Biomecânica. Mapeie as ações musculares.

            MÚSCULOS ALVO: {json.dumps(batch_names, ensure_ascii=False)}

            MOVIMENTOS POSSÍVEIS (COPIE EXATAMENTE):
            {json.dumps(valid_movements_list, ensure_ascii=False)}

            PAPÉIS (ROLES) PERMITIDOS:
            {roles_text}

            INSTRUÇÕES CRÍTICAS:
            1. Retorne APENAS um JSON. Sem texto antes ou depois.
            2. O formato deve ser ESTRITAMENTE uma LISTA de objetos.
            3. O campo 'movement_name' deve vir da lista 'MOVIMENTOS POSSÍVEIS'.

            MODELO DE SAÍDA:
            [
                {{
                    "muscle": "Nome do Músculo",
                    "actions": [
                        {{
                            "movement_name": "Nome do Movimento (Articulação)",
                            "role": "AGONISTA_PRIMARIO",
                            "notes": "Texto curto."
                        }}
                    ]
                }}
            ]
            """

            try:
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(ollama_url, json={
                        "model": model,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                        "options": {"temperature": 0.1}
                    })
                    
                    if response.status_code != 200:
                        self.stdout.write(self.style.ERROR(f"Erro Ollama: {response.text}"))
                        continue

                    response_json = response.json()
                    raw_text = response_json.get('response', '')
                    
                    # --- SANITIZAÇÃO DA RESPOSTA (O Fix Crítico) ---
                    ai_data = self._clean_and_parse_json(raw_text)

                    if not ai_data:
                        self.stdout.write(self.style.ERROR("  > JSON vazio ou inválido. Pulando."))
                        continue

                    with transaction.atomic():
                        for item in ai_data:
                            # Validação extra: item deve ser dict
                            if not isinstance(item, dict):
                                continue

                            muscle_name = item.get('muscle')
                            muscle_obj = Muscle.objects.filter(name__iexact=muscle_name).first()
                            
                            if not muscle_obj:
                                # Tenta match parcial se falhar o exato
                                # self.stdout.write(self.style.WARNING(f"  > Músculo não encontrado: {muscle_name}"))
                                continue

                            for action in item.get('actions', []):
                                if not isinstance(action, dict): continue
                                
                                mov_key = action.get('movement_name', '').upper()
                                role_key = action.get('role', '').upper()
                                
                                movement_obj = movement_map.get(mov_key)
                                
                                # Validação de Role
                                valid_roles = [c[0] for c in MuscleRole.choices]
                                if role_key not in valid_roles:
                                    role_key = 'AGONISTA_SECUNDARIO' 

                                if movement_obj:
                                    MuscleAction.objects.update_or_create(
                                        muscle=muscle_obj,
                                        movement=movement_obj,
                                        role=role_key,
                                        defaults={'notes': action.get('notes', '')}
                                    )
                                    success_actions += 1

                processed_count += len(batch_muscles)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  > Erro no lote: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Concluído! {success_actions} ações musculares registradas.'))

    def _clean_and_parse_json(self, raw_text):
        """
        Limpa markdown, remove espaços e garante que o retorno seja uma LISTA.
        """
        try:
            # 1. Remove blocos de código markdown ```json ... ```
            cleaned = re.sub(r'```json\s*', '', raw_text)
            cleaned = re.sub(r'```\s*', '', cleaned)
            cleaned = cleaned.strip()

            # 2. Parse
            data = json.loads(cleaned)

            # 3. Normalização para Lista
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Se a IA retornou { "muscles": [...] } ou um objeto único
                if 'muscles' in data and isinstance(data['muscles'], list):
                    return data['muscles']
                elif 'data' in data and isinstance(data['data'], list):
                    return data['data']
                else:
                    # Se for um objeto único solto, encapsula em lista
                    return [data]
            
            return []
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"  > Falha ao decodificar JSON: {raw_text[:100]}..."))
            return []