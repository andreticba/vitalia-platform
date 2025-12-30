// frontend/src/app/recipes/page.tsx - Receitas Afetivas (Participante) em 2025-12-14 11:48

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PlusCircle, Search, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import { recipesApi } from '@/features/social/recipesApi';
import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { RecipeCard } from '@/components/recipes/RecipeCard';
import { RecipeDetailModal } from '@/components/recipes/RecipeDetailModal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { FamilyRecipe } from '@/types/social';
import { useDebounce } from '@/hooks/useDebounce'; // Importamos o hook criado

export default function RecipesPage() {
  // Estado local do input (atualiza instantaneamente para a UI não travar)
  const [searchTerm, setSearchTerm] = useState('');
  
  // Valor "atrasado" que será enviado para a API apenas quando o usuário parar de digitar
  const debouncedSearch = useDebounce(searchTerm, 600); 
  
  const [selectedRecipe, setSelectedRecipe] = useState<FamilyRecipe | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Busca as receitas da API (Server-Side Filtering)
  const { data: recipes, isLoading, isError, refetch, isFetching } = useQuery({
    // A chave da query agora inclui o termo de busca. 
    // Quando 'debouncedSearch' mudar, o React Query dispara o refetch automaticamente.
    queryKey: ['recipes', debouncedSearch],
    
    queryFn: () => recipesApi.getAll({ 
      search: debouncedSearch || undefined // Envia undefined se vazio para não sujar a URL
    }),
    
    // Mantém os dados anteriores na tela enquanto carrega os novos (UX melhor)
    placeholderData: (previousData) => previousData, 
  });

  // NOTA: Removemos a filtragem local (client-side). 
  // Agora a variável 'recipes' já vem filtrada do servidor (PostgreSQL), 
  // garantindo performance mesmo com milhões de registros.

  const handleCardClick = (recipe: FamilyRecipe) => {
    setSelectedRecipe(recipe);
    setIsModalOpen(true);
  };

  const handleValidate = async (id: string) => {
    // Simulação da chamada de validação
    toast.success("Receita validada com sucesso!", {
        description: "A análise de segurança foi confirmada e registrada no Hub."
    });
    setIsModalOpen(false);
  };

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-6">
        
        <RecipeDetailModal 
            recipe={selectedRecipe}
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            onValidate={handleValidate}
        />

        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-primary">Culinária Afetiva</h1>
            <p className="text-muted-foreground mt-1">
              Receitas que conectam sua saúde às suas memórias.
            </p>
          </div>
          <Button className="gap-2">
            <PlusCircle className="h-4 w-4" />
            Nova Receita
          </Button>
        </div>

        {/* Barra de Busca */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Buscar por nome, ingrediente ou memória..." 
            className="pl-9 max-w-md"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {/* Indicador visual discreto de que a busca está acontecendo em background */}
          {isFetching && !isLoading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
            </div>
          )}
        </div>

        {/* Estado de Carregamento Inicial */}
        {isLoading && (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {/* Estado de Erro */}
        {isError && (
          <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-center border border-destructive/20">
            <p className="font-semibold">Não foi possível carregar as receitas.</p>
            <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-4 border-destructive/30 hover:bg-destructive/20">
              Tentar Novamente
            </Button>
          </div>
        )}

        {/* Grid de Receitas */}
        {!isLoading && !isError && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {recipes?.map((recipe) => (
              <RecipeCard 
                key={recipe.id} 
                recipe={recipe} 
                onClick={() => handleCardClick(recipe)} 
              />
            ))}
            
            {/* Estado Vazio (Busca sem resultados) */}
            {recipes?.length === 0 && (
              <div className="col-span-full py-16 text-center text-muted-foreground bg-muted/10 rounded-xl border border-dashed border-muted">
                <div className="flex flex-col items-center gap-2">
                  <Search className="h-8 w-8 opacity-20" />
                  <p className="font-medium">Nenhuma receita encontrada no Hub.</p>
                  {searchTerm && (
                    <p className="text-sm">
                      Não encontramos nada para "{searchTerm}". <br/>
                      <Button variant="link" onClick={() => setSearchTerm('')} className="px-0">Limpar busca</Button>
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </ProtectedLayout>
  );
}