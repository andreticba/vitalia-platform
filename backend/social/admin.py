# backend/social/admin.py em 2025-12-14 11:48

from django.contrib import admin
from .models import FamilyRecipe, Allergen

@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ('name', 'severity_level')
    search_fields = ('name',)
    list_filter = ('severity_level',)

@admin.register(FamilyRecipe)
class FamilyRecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'is_public', 'created_at')
    list_filter = ('status', 'is_public', 'created_at')
    search_fields = ('title', 'author__username', 'ingredients_text')
    readonly_fields = ('nutritional_info_snapshot', 'safety_flags', 'likes_count')
    filter_horizontal = ('detected_allergens',)
    
    fieldsets = (
        ('Identificação', {
            'fields': ('author', 'title', 'status', 'is_public')
        }),
        ('Afetividade', {
            'fields': ('origin_story', 'emotional_value', 'consumption_context')
        }),
        ('Técnica', {
            'fields': ('ingredients_text', 'preparation_method', 'servings', 'preparation_time_minutes')
        }),
        ('Segurança (IA & HITL)', {
            'fields': ('detected_allergens', 'safety_flags', 'nutritional_info_snapshot', 'validated_by')
        }),
    )
