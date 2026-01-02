# backend/medical/services.py em 2025-12-14 11:48

import json
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from core.clients import ollama_client
from core.models import AuditLog
from medical.models import (
    MedicalExam, PhysicalEvaluation, 
    WellnessPlan, DailySchedule, PrescribedActivity, 
    Exercise, Pathology, MovementContraindication
)

logger = logging.getLogger(__name__)

class WellnessMaestro:
    """
    O Maestro da Vitalia.
    Orquestra a geração de planos de saúde personalizados usando IA Híbrida.
    """
    
    def __init__(self, participant_user):
        self.user = participant_user
        self.profile = participant_user.profile.participant_data
        self.model = settings.OLLAMA_GENERATION_MODEL

    def generate_initial_plan(self, professional_user) -> WellnessPlan:
        """
        Gera um plano inicial (DRAFT) para revisão do profissional.
        """
        logger.info(f"Maestro: Iniciando geração de plano para {self.user.username}...")

        # 1. Coleta de Contexto (O "Prontuário Virtual")
        context = self._gather_context()
        
        # 2. Análise de Segurança (Grounding Determinístico)
        contraindications = self._analyze_safety_constraints(context)
        
        # 3. Geração da Estrutura do Plano (LLM)
        ai_plan_structure = self._prompt_llm_for_plan(context, contraindications)
        
        # 4. Materialização no Banco de Dados
        plan = self._persist_plan(ai_plan_structure, professional_user, context)
        
        return plan

    def _gather_context(self) -> dict:
        """Coleta dados mais recentes do Data Vault."""
        last_exam = MedicalExam.objects.filter(patient=self.user).order_by('-exam_date').first()
        last_eval = PhysicalEvaluation.objects.filter(patient=self.user, is_finalized=True).order_by('-date').first()
        
        return {
            "age": 45, # Calcular basedo em birth_date
            "goals": "Melhorar energia e reduzir dores lombares", # Mock, viria da Anamnese
            "autonomy_level": self.profile.get_autonomy_level_display(),
            "latest_exam": last_exam.results_structured if last_exam else {},
            "body_comp": last_eval.results_data if last_eval else {},
            "history": "Sedentário há 5 anos. Histórico de hipertensão leve." # Mock
        }

    def _analyze_safety_constraints(self, context) -> list:
        """
        (P22) Grounding: Cruza dados do paciente com regras rígidas de patologia do banco.
        Não deixa a IA decidir segurança sozinha.
        """
        constraints = []
        # Exemplo: Se tiver 'Hérnia' no histórico, busca contraindicações no banco
        # Numa implementação real, usaríamos códigos CID-10 estruturados
        if "lombar" in str(context).lower():
            # Busca contraindicações de movimento para patologias lombares
            blocked_movements = MovementContraindication.objects.filter(
                pathology__name__icontains="Lombar"
            ).values_list('movement__name', flat=True)
            
            if blocked_movements:
                constraints.append(f"EVITAR ABSOLUTAMENTE movimentos: {', '.join(blocked_movements)}")
        
        return constraints

    def _prompt_llm_for_plan(self, context, constraints) -> dict:
        """
        Chain-of-Thought Prompting para gerar a agenda semanal.
        """
        prompt = f"""
        Aja como um Treinador Clínico Sênior da Vitalia.
        Crie um plano semanal de bem-estar para este paciente.

        PERFIL DO PACIENTE:
        - Nível de Autonomia: {context['autonomy_level']}
        - Histórico: {context['history']}
        - Objetivos: {context['goals']}

        RESTRIÇÕES DE SEGURANÇA (CRÍTICO):
        {json.dumps(constraints, ensure_ascii=False)}

        TAREFA:
        Gere um JSON com uma agenda de 7 dias (Segunda a Domingo).
        Para cada dia, sugira 1 a 3 atividades (Treino, Nutrição, Mindfulness).
        
        FORMATO JSON ESPERADO:
        {{
            "title": "Título Motivador do Plano",
            "clinical_reasoning": "Por que escolheu essa abordagem?",
            "schedule": [
                {{
                    "day": "Segunda-feira",
                    "activities": [
                        {{ "type": "RESISTANCE", "title": "Treino A - Adaptação", "desc": "Foco em mobilidade" }},
                        {{ "type": "NUTRITION", "title": "Hidratação", "desc": "Beber 2.5L de água" }}
                    ]
                }}
                ... (até Domingo)
            ]
        }}
        """
        
        response = ollama_client.generate(self.model, prompt, is_json=True)
        return json.loads(response.get('response', '{}'))

    def _persist_plan(self, ai_data, professional, context_snapshot):
        """Salva o plano como PENDING_APPROVAL."""
        with transaction.atomic():
            # 1. Cria o Plano
            plan = WellnessPlan.objects.create(
                participant=self.user,
                responsible_professional=professional,
                title=ai_data.get('title', 'Plano Personalizado Vitalia'),
                goals=ai_data.get('clinical_reasoning', 'Gerado via IA'),
                status=WellnessPlan.Status.PENDING_APPROVAL,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timedelta(days=30),
                ai_generation_metadata={
                    "snapshot": context_snapshot,
                    "reasoning": ai_data.get('clinical_reasoning')
                }
            )

            # 2. Cria a Agenda (DailySchedule + Activities)
            schedule_list = ai_data.get('schedule', [])
            for idx, day_data in enumerate(schedule_list):
                daily = DailySchedule.objects.create(
                    plan=plan,
                    day_label=day_data.get('day', f'Dia {idx+1}'),
                    day_index=idx
                )
                
                for act_idx, act in enumerate(day_data.get('activities', [])):
                    PrescribedActivity.objects.create(
                        schedule=daily,
                        title=act.get('title'),
                        activity_type=act.get('type', 'CUSTOM'),
                        order_index=act_idx,
                        flexible_data={'description': act.get('desc')}
                    )
            
            # 3. Auditoria (P10)
            AuditLog.objects.create(
                actor=professional, # Atribuímos ao Pro (sistema agindo em nome)
                action=AuditLog.ActionType.AI_DECISION,
                target_object_id=str(plan.id),
                details={"event": "plan_generation"},
                ai_reasoning_snapshot=ai_data
            )
            
            return plan