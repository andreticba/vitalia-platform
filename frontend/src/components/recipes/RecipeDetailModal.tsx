// frontend/src/components/recipes/RecipeDetailModal.tsx

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { 
  AlertTriangle, 
  CheckCircle2, 
  ChefHat, 
  Clock, 
  Heart, 
  Scale, 
  ShieldCheck, 
  Users 
} from "lucide-react";
import { FamilyRecipe } from "@/types/social";
import { useAppSelector } from "@/store/hooks";

interface RecipeDetailModalProps {
  recipe: FamilyRecipe | null;
  isOpen: boolean;
  onClose: () => void;
  onValidate?: (id: string) => void; // Ação para profissionais
}

export function RecipeDetailModal({ recipe, isOpen, onClose, onValidate }: RecipeDetailModalProps) {
  const { user } = useAppSelector((state) => state.auth);
  
  if (!recipe) return null;

  // Verifica se o usuário atual é um profissional de saúde
  const isProfessional = user?.roles.some(r => 
    ['Profissional de Saúde', 'Nutricionista'].includes(r.name)
  );

  // Verifica riscos
  const hasSafetyFlags = recipe.safety_flags && recipe.safety_flags.length > 0;
  const isHighRisk = recipe.detected_allergens.some(a => a.severity_level === 'HIGH');

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] flex flex-col p-0 gap-0">
        
        {/* Cabeçalho com Contexto Visual */}
        <div className="p-6 pb-2">
          <div className="flex justify-between items-start gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Badge variant={
                  recipe.status === 'PUBLISHED' ? 'default' : 
                  recipe.status === 'FLAGGED' ? 'destructive' : 'outline'
                }>
                  {recipe.status_display}
                </Badge>
                {recipe.is_public && <Badge variant="secondary">Público</Badge>}
              </div>
              <DialogTitle className="text-2xl font-bold text-primary">
                {recipe.title}
              </DialogTitle>
              <DialogDescription className="flex items-center gap-2 mt-1">
                <ChefHat className="h-4 w-4" /> 
                Receita de <span className="font-medium text-foreground">{recipe.author.username}</span>
              </DialogDescription>
            </div>

            {/* Selo de Validação */}
            {recipe.validated_by ? (
              <div className="flex flex-col items-end text-xs text-green-600 bg-green-50 px-3 py-1.5 rounded-lg border border-green-100">
                <div className="flex items-center gap-1 font-semibold">
                  <ShieldCheck className="h-4 w-4" />
                  Validado por Profissional
                </div>
                <span>{recipe.validated_by.name}</span>
              </div>
            ) : hasSafetyFlags ? (
              <div className="flex flex-col items-end text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-100">
                <div className="flex items-center gap-1 font-semibold">
                  <AlertTriangle className="h-4 w-4" />
                  Atenção Necessária
                </div>
                <span>IA detectou alertas</span>
              </div>
            ) : null}
          </div>
        </div>

        <Separator />

        <ScrollArea className="flex-1 p-6">
          <div className="grid gap-6">
            
            {/* Seção Emocional (O Coração da Vitalia) */}
            <section className="bg-amber-50/50 dark:bg-amber-950/20 p-4 rounded-xl border border-amber-100 dark:border-amber-900/50">
              <h3 className="flex items-center gap-2 font-semibold text-amber-700 dark:text-amber-400 mb-2">
                <Heart className="h-4 w-4" />
                Valor Afetivo & Memória
              </h3>
              <p className="italic text-sm text-muted-foreground">
                "{recipe.emotional_value || "Uma receita especial de família..."}"
              </p>
              {recipe.origin_story && (
                <p className="text-sm mt-2 pt-2 border-t border-amber-200/50 dark:border-amber-800/50">
                  <span className="font-semibold text-xs uppercase tracking-wide opacity-70">Origem:</span> {recipe.origin_story}
                </p>
              )}
            </section>

            {/* Métricas e Preparo */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-muted/30 p-3 rounded-lg text-center">
                <Clock className="h-5 w-5 mx-auto mb-1 text-primary" />
                <div className="text-sm font-medium">{recipe.preparation_time_minutes || "-"} min</div>
                <div className="text-[10px] text-muted-foreground uppercase">Tempo</div>
              </div>
              <div className="bg-muted/30 p-3 rounded-lg text-center">
                <Users className="h-5 w-5 mx-auto mb-1 text-primary" />
                <div className="text-sm font-medium">{recipe.servings}</div>
                <div className="text-[10px] text-muted-foreground uppercase">Porções</div>
              </div>
              
              {/* Estimativa da IA (Nutrição) */}
              <div className="bg-muted/30 p-3 rounded-lg text-center col-span-2 border border-dashed border-primary/20">
                <Scale className="h-5 w-5 mx-auto mb-1 text-primary" />
                <div className="text-sm font-medium">
                  ~{recipe.nutritional_info_snapshot?.calories_kcal || "?"} kcal
                </div>
                <div className="text-[10px] text-muted-foreground uppercase">Estimativa IA / porção</div>
              </div>
            </div>

            {/* Ingredientes e Modo de Preparo */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2 text-sm uppercase tracking-wider text-muted-foreground">Ingredientes</h4>
                <div className="bg-muted/20 p-4 rounded-lg text-sm whitespace-pre-line leading-relaxed">
                  {recipe.ingredients_text}
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2 text-sm uppercase tracking-wider text-muted-foreground">Modo de Preparo</h4>
                <div className="bg-muted/20 p-4 rounded-lg text-sm whitespace-pre-line leading-relaxed">
                  {recipe.preparation_method}
                </div>
              </div>
            </div>

            {/* Painel de Segurança Alimentar (IA) */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground">
                <ShieldCheck className="h-4 w-4" /> 
                Análise de Segurança (IA)
              </h4>
              
              <div className="flex flex-wrap gap-2">
                {recipe.detected_allergens.length === 0 && !hasSafetyFlags ? (
                  <span className="text-sm text-muted-foreground">Nenhum risco detectado.</span>
                ) : null}

                {recipe.detected_allergens.map(allergen => (
                  <Badge 
                    key={allergen.id} 
                    variant={allergen.severity_level === 'HIGH' ? 'destructive' : 'secondary'}
                    className="gap-1"
                  >
                    {allergen.name}
                    {allergen.severity_level === 'HIGH' && " (Alto Risco)"}
                  </Badge>
                ))}
              </div>

              {hasSafetyFlags && (
                <div className="bg-red-50 dark:bg-red-950/20 p-3 rounded-md border border-red-100 dark:border-red-900">
                  <ul className="list-disc list-inside text-sm text-red-700 dark:text-red-300 space-y-1">
                    {recipe.safety_flags.map((flag, idx) => (
                      <li key={idx}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

          </div>
        </ScrollArea>

        <DialogFooter className="p-6 pt-2 border-t bg-muted/10">
          <Button variant="outline" onClick={onClose}>
            Fechar
          </Button>
          
          {/* BOTÃO HITL: Só aparece para Profissionais em receitas não validadas */}
          {isProfessional && !recipe.validated_by && (
            <Button 
              className="gap-2 bg-green-600 hover:bg-green-700 text-white"
              onClick={() => onValidate && onValidate(recipe.id)}
            >
              <CheckCircle2 className="h-4 w-4" />
              Validar Segurança
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}