// frontend/src/features/recipes/RecipeDetailModal.tsx em 2025-12-14 11:48

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { FamilyRecipe } from '@/types/social';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

interface RecipeDetailModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  recipe: FamilyRecipe;
}

export function RecipeDetailModal({ isOpen, onOpenChange, recipe }: RecipeDetailModalProps) {
  if (!recipe) return null;

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity) {
      case 'HIGH': return 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-300';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'LOW': return 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-700/30 dark:text-gray-300';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-primary">{recipe.title}</DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Por {recipe.author.username} • {new Date(recipe.created_at).toLocaleDateString()}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 px-4 py-2 -mx-4">
          <div className="space-y-6 text-sm">
            {/* Valor Afetivo */}
            {recipe.emotional_value && (
              <div>
                <h3 className="font-semibold text-base mb-1">💖 Valor Afetivo</h3>
                <p className="text-muted-foreground">{recipe.emotional_value}</p>
              </div>
            )}

            {/* Origem e Contexto */}
            {(recipe.origin_story || recipe.consumption_context) && (
              <div>
                <h3 className="font-semibold text-base mb-1">📖 Origem & Contexto</h3>
                {recipe.origin_story && <p className="text-muted-foreground">{recipe.origin_story}</p>}
                {recipe.consumption_context && <p className="text-muted-foreground mt-1">Serve para: {recipe.consumption_context}</p>}
              </div>
            )}

            <Separator />

            {/* Ingredientes */}
            <div>
              <h3 className="font-semibold text-base mb-1">🥕 Ingredientes ({recipe.servings} porções)</h3>
              <p className="whitespace-pre-wrap text-muted-foreground">{recipe.ingredients_text}</p>
            </div>

            {/* Modo de Preparo */}
            <div>
              <h3 className="font-semibold text-base mb-1">👩‍🍳 Modo de Preparo</h3>
              <p className="whitespace-pre-wrap text-muted-foreground">{recipe.preparation_method}</p>
            </div>

            <Separator />

            {/* Alérgenos Detectados */}
            {recipe.detected_allergens && recipe.detected_allergens.length > 0 && (
              <div>
                <h3 className="font-semibold text-base mb-2">🚨 Alérgenos Detectados</h3>
                <div className="flex flex-wrap gap-2">
                  {recipe.detected_allergens.map(allergen => (
                    <Badge key={allergen.name} variant="outline" className={cn("text-xs", getSeverityBadgeClass(allergen.severity_level))}>
                      {allergen.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Sinalizações de Segurança */}
            {recipe.safety_flags && recipe.safety_flags.length > 0 && (
              <div>
                <h3 className="font-semibold text-base mb-2">⚠️ Sinalizações de Segurança</h3>
                <ul className="list-disc list-inside text-muted-foreground">
                  {recipe.safety_flags.map((flag, index) => (
                    <li key={index}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Informações Nutricionais (se disponível) */}
            {recipe.nutritional_info_snapshot && Object.keys(recipe.nutritional_info_snapshot).length > 0 && (
              <div>
                <h3 className="font-semibold text-base mb-2">📊 Estimativa Nutricional (por porção)</h3>
                <ul className="text-muted-foreground">
                  {Object.entries(recipe.nutritional_info_snapshot).map(([key, value]) => (
                    <li key={key}>{key.replace('_', ' ').replace('kcal', '(kcal)').replace('g', '(g)').replace('mg', '(mg)')}: <strong>{String(value)}</strong></li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}