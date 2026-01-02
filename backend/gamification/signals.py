# backend/gamification/signals.py em 2025-12-14 11:48

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from medical.models import PrescribedActivity
from .models import PointTransaction, UserBadge, Badge
from core.models import ParticipantProfile

@receiver(post_save, sender=PrescribedActivity)
def reward_activity_completion(sender, instance, created, **kwargs):
    """
    Ouve quando uma atividade médica é marcada como 'is_completed=True'.
    """
    # Só processa se for update (não criação), se estiver completada, e se houver mudança de estado
    if created or not instance.is_completed:
        return

    # Evita duplicidade simples verificando se já existe transação para esta atividade
    # (Em produção, usaria idempotência mais robusta com Redis lock)
    if PointTransaction.objects.filter(reference_id=str(instance.id)).exists():
        return

    user = instance.schedule.plan.participant
    
    # 1. Define Pontuação Base (Pode ser sofisticado depois com base na dificuldade do treino)
    points = 10 
    if instance.activity_type == 'RESISTANCE': points = 50
    elif instance.activity_type == 'CARDIO_TIME': points = 30
    
    description = f"Concluiu: {instance.title}"

    with transaction.atomic():
        # 2. Cria a Transação
        PointTransaction.objects.create(
            user=user,
            amount=points,
            transaction_type=PointTransaction.TransactionType.ACTIVITY_COMPLETED,
            description=description,
            reference_id=str(instance.id)
        )

        # 3. Atualiza o Saldo Rápido (Cache no Profile)
        # Nota: O profile é o 'ParticipantProfile', acessível via 'participant_data' no UserProfile
        # Mas aqui 'user' é o User do Django. O reverse relation no UserProfile é 'profile'.
        # E UserProfile -> ParticipantProfile é 'participant_data'.
        try:
            profile = user.profile.participant_data
            profile.gamification_wallet_balance += points
            
            # Lógica de Streak (Simplificada)
            # Se a última atividade foi ontem, +1. Se foi hoje, mantém. Se foi antes, reseta.
            # (Implementar lógica de data aqui futuramente)
            profile.current_streak_days += 1 
            
            profile.save()
        except Exception:
            pass # Se não for participante (ex: admin testando), ignora