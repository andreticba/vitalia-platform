# backend/social/models.py em 2025-12-14 11:48

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Allergen(models.Model):
    """
    Lista oficial de alérgenos (Baseado na RDC 26/2015 ANVISA).
    Ex: 'Glúten', 'Lactose', 'Amendoim', 'Crustáceos'.
    """
    class Severity(models.TextChoices):
        HIGH = 'HIGH', _('Alto Risco (Anafilaxia Comum)')
        MEDIUM = 'MEDIUM', _('Médio (Intolerância Comum)')
        LOW = 'LOW', _('Baixo Risco')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    severity_level = models.CharField(max_length=20, choices=Severity.choices, default=Severity.HIGH)

    class Meta:
        verbose_name = _("Alérgeno")
        verbose_name_plural = _("Alérgenos")

    def __str__(self):
        return f"{self.name} ({self.get_severity_level_display()})"


class FamilyRecipe(models.Model):
    """
    Receitas cadastradas pelos participantes com foco em memória afetiva.
    Passam por análise de IA e validação profissional.
    """
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Rascunho')
        PENDING_REVIEW = 'PENDING_REVIEW', _('Aguardando Análise')
        PUBLISHED = 'PUBLISHED', _('Publicada no Hub')
        FLAGGED = 'FLAGGED', _('Sinalizada (Risco de Segurança)')
        ARCHIVED = 'ARCHIVED', _('Arquivada')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recipes')
    
    # --- Narrativa e Afeto (O Diferencial Vitalia) ---
    title = models.CharField(max_length=255, verbose_name=_("Nome da Receita"))
    origin_story = models.TextField(
        verbose_name=_("Origem"), 
        help_text=_("De onde você conhece? É uma tradição familiar?"),
        blank=True
    )
    emotional_value = models.TextField(
        verbose_name=_("Valor Afetivo"),
        help_text=_("Quais lembranças positivas traz? Quando costuma fazer?"),
        blank=True
    )
    consumption_context = models.CharField(
        max_length=100, 
        blank=True,
        help_text=_("Ex: Café da manhã, Almoço de Domingo, Ceia de Natal.")
    )
    
    # --- Dados Técnicos ---
    ingredients_text = models.TextField(
        verbose_name=_("Ingredientes"),
        help_text=_("Lista completa dos ingredientes e quantidades.")
    )
    preparation_method = models.TextField(verbose_name=_("Modo de Preparo"))
    servings = models.PositiveIntegerField(default=1, verbose_name=_("Porções"))
    preparation_time_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Tempo de Preparo (min)"))
    
    # --- Segurança Alimentar & IA (Preenchido automaticamente) ---
    detected_allergens = models.ManyToManyField(Allergen, blank=True, related_name='recipes')
    
    nutritional_info_snapshot = models.JSONField(
        null=True, 
        blank=True, 
        help_text=_("JSON estimado pela IA: {kcal, carb, prot, fat, sodium}.")
    )
    
    safety_flags = models.JSONField(
        default=list, 
        blank=True, 
        help_text=_("Lista de avisos da IA: ['Alto Sódio', 'Risco de Engasgo', 'Contém Glúten'].")
    )
    
    # --- Governança (HITL) ---
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    
    validated_by = models.ForeignKey(
        'core.ProfessionalProfile', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='validated_recipes',
        help_text=_("Profissional que validou a segurança da receita.")
    )
    
    # --- Engajamento ---
    is_public = models.BooleanField(default=False, help_text=_("Se visível no Hub Global de Receitas."))
    likes_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Receita Familiar")
        verbose_name_plural = _("Receitas Familiares")

    def __str__(self):
        return self.title
