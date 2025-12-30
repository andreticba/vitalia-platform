// frontend/src/components/recipes/RecipeCard.tsx

import { FamilyRecipe } from '@/types/social';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Heart, Clock, Users, ShieldAlert, ChefHat, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface RecipeCardProps {
  recipe: FamilyRecipe;
  onClick: () => void;
}

export function RecipeCard({ recipe, onClick }: RecipeCardProps) {
  const hasHighRiskAllergen = recipe.detected_allergens.some(a => a.severity_level === 'HIGH');

  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-primary/40 group" onClick={onClick}>
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <CardTitle className="text-xl font-bold text-primary group-hover:text-primary/80 transition-colors">
              {recipe.title}
            </CardTitle>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <ChefHat className="h-3 w-3" /> 
              por {recipe.author.username} • {recipe.created_at_fmt}
            </p>
          </div>
          {hasHighRiskAllergen && (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 text-red-600" title="Contém alérgenos de alto risco">
              <ShieldAlert className="h-5 w-5" />
            </div>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Seção Emocional (Destaque Vitalia) */}
        {(recipe.emotional_value || recipe.origin_story) && (
          <div className="bg-amber-50 dark:bg-amber-950/30 p-3 rounded-md text-sm text-amber-900 dark:text-amber-100 italic border border-amber-100 dark:border-amber-900">
            <div className="flex gap-2">
                <Heart className="h-4 w-4 text-amber-500 fill-amber-500 mt-0.5 shrink-0" />
                <span className="line-clamp-2">
                    "{recipe.emotional_value || recipe.origin_story}"
                </span>
            </div>
          </div>
        )}

        {/* Badges de Alérgenos */}
        <div className="flex flex-wrap gap-1.5">
          {recipe.detected_allergens.slice(0, 3).map(allergen => (
            <Badge 
                key={allergen.id} 
                variant={allergen.severity_level === 'HIGH' ? 'destructive' : 'secondary'}
                className="text-[10px] px-1.5 h-5"
            >
              {allergen.name}
            </Badge>
          ))}
          {recipe.detected_allergens.length > 3 && (
            <Badge variant="outline" className="text-[10px] px-1.5 h-5">
              +{recipe.detected_allergens.length - 3}
            </Badge>
          )}
        </div>
      </CardContent>

      <CardFooter className="bg-muted/20 px-6 py-3 flex justify-between text-xs text-muted-foreground">
        <div className="flex gap-4">
            {recipe.preparation_time_minutes && (
                <div className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    <span>{recipe.preparation_time_minutes} min</span>
                </div>
            )}
            <div className="flex items-center gap-1">
                <Users className="h-3.5 w-3.5" />
                <span>{recipe.servings} porções</span>
            </div>
        </div>
        
        <div className="flex items-center gap-1 text-primary font-medium">
            <Heart className={cn("h-3.5 w-3.5", recipe.likes_count > 0 && "fill-primary")} />
            <span>{recipe.likes_count}</span>
        </div>
      </CardFooter>
    </Card>
  );
}