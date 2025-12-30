// frontend/src/features/recipes/RecipeCard.tsx em 2025-12-14 11:48

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Heart, Utensils, Flag } from 'lucide-react';
import { FamilyRecipe } from '@/types/social';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { RecipeDetailModal } from './RecipeDetailModal'; // Componente a ser criado

interface RecipeCardProps {
  recipe: FamilyRecipe;
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'HIGH': return 'bg-red-500 hover:bg-red-600 text-white';
      case 'MEDIUM': return 'bg-yellow-500 hover:bg-yellow-600 text-yellow-900';
      default: return 'bg-green-500 hover:bg-green-600 text-white';
    }
  };

  return (
    <>
      <RecipeDetailModal isOpen={isDetailModalOpen} onOpenChange={setIsDetailModalOpen} recipe={recipe} />
      <Card 
        className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
        onClick={() => setIsDetailModalOpen(true)}
      >
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-lg font-medium">
            {recipe.title}
          </CardTitle>
          <Utensils className="h-5 w-5 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground line-clamp-2 min-h-[40px]">
            {recipe.emotional_value || recipe.origin_story || recipe.description}
          </div>
          <div className="flex items-center gap-2 mt-4 text-xs text-muted-foreground">
            <Heart className="h-3 w-3" />
            <span>{recipe.likes_count} Curtidas</span>
            {recipe.detected_allergens && recipe.detected_allergens.length > 0 && (
              <Badge 
                variant="default" 
                className={cn("text-xs flex items-center gap-1", getSeverityColor(recipe.detected_allergens[0].severity_level))}
              >
                <Flag className="h-3 w-3" />
                <span>{recipe.detected_allergens.length} Alérgeno(s)</span>
              </Badge>
            )}
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            Por {recipe.author.username}
          </div>
        </CardContent>
      </Card>
    </>
  );
}