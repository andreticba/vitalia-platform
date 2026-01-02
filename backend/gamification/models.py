# backend/gamification/models.py em 2025-12-14 11:48

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class GamificationLevel(models.Model):
    """
    Tabela de níveis (Ex: Nível 1 = Novato, Nível 10 = Mestre Vitalia).
    Define a 'inflação' do sistema: quanto XP precisa para subir.
    """
    level_number = models.PositiveIntegerField(unique=True)
    xp_required = models.PositiveIntegerField(help_text="XP total necessário para atingir este nível.")
    title = models.CharField(max_length=100, help_text="Ex: Iniciante, Explorador, Guardião.")
    icon_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['level_number']

    def __str__(self): return f"Lvl {self.level_number} - {self.title}"

class Badge(models.Model):
    """
    Conquistas desbloqueáveis (Achievements).
    """
    slug = models.SlugField(unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_url = models.URLField(blank=True)
    xp_bonus = models.PositiveIntegerField(default=50)
    
    # Regra de Negócio (Simplificada para MVP)
    trigger_event = models.CharField(max_length=100, blank=True, help_text="Ex: 'streak_7_days', 'first_workout'")

    def __str__(self): return self.name

class UserBadge(models.Model):
    """
    Relacionamento: Quem ganhou o quê e quando.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

class PointTransaction(models.Model):
    """
    O Ledger (Livro Razão) de Pontos. 
    Auditabilidade total: sabemos exatamente de onde veio cada ponto.
    """
    class TransactionType(models.TextChoices):
        ACTIVITY_COMPLETED = 'ACTIVITY', _('Atividade Concluída')
        STREAK_BONUS = 'STREAK', _('Bônus de Sequência')
        BADGE_EARNED = 'BADGE', _('Conquista Desbloqueada')
        MANUAL_ADJUSTMENT = 'ADJUST', _('Ajuste Manual (Suporte)')
        MARKETPLACE_SPEND = 'SPEND', _('Resgate no Marketplace')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='point_transactions')
    amount = models.IntegerField(help_text="Pode ser negativo para gastos.")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    description = models.CharField(max_length=255)
    
    # Rastreabilidade (Opcional)
    reference_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID da atividade ou badge que gerou isso.")
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        signal = "+" if self.amount >= 0 else ""
        return f"{self.user.username}: {signal}{self.amount} ({self.get_transaction_type_display()})"