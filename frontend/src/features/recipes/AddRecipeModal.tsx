// frontend/src/features/recipes/AddRecipeModal.tsx em 2025-12-14 11:48

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api';
import { FamilyRecipe } from '@/types/social';

// Esquema de validação para o formulário de receita
const recipeFormSchema = z.object({
  title: z.string().min(1, 'O título é obrigatório'),
  origin_story: z.string().max(500, 'Máximo de 500 caracteres').optional(),
  emotional_value: z.string().max(500, 'Máximo de 500 caracteres').optional(),
  consumption_context: z.string().max(100, 'Máximo de 100 caracteres').optional(),
  ingredients_text: z.string().min(10, 'Detalhe os ingredientes'),
  preparation_method: z.string().min(10, 'Detalhe o modo de preparo'),
  servings: z.coerce.number().min(1, 'No mínimo 1 porção').optional(),
  preparation_time_minutes: z.coerce.number().min(1, 'Tempo em minutos').optional(),
  is_public: z.boolean().default(false), // Pode ser um switch
});

type RecipeFormData = z.infer<typeof recipeFormSchema>;

interface AddRecipeModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const createRecipe = async (data: RecipeFormData): Promise<FamilyRecipe> => {
  const response = await api.post<FamilyRecipe>('/social/recipes/', data);
  return response.data;
};

export function AddRecipeModal({ isOpen, onOpenChange }: AddRecipeModalProps) {
  const queryClient = useQueryClient();
  const form = useForm<RecipeFormData>({
    resolver: zodResolver(recipeFormSchema),
    defaultValues: {
      title: '',
      origin_story: '',
      emotional_value: '',
      consumption_context: '',
      ingredients_text: '',
      preparation_method: '',
      servings: 1,
      preparation_time_minutes: 30,
      is_public: false,
    },
  });

  const { mutate, isPending } = useMutation({
    mutationFn: createRecipe,
    onSuccess: () => {
      toast.success('Receita adicionada! Nossa IA irá analisá-la em breve.');
      queryClient.invalidateQueries({ queryKey: ['userRecipes'] });
      form.reset();
      onOpenChange(false);
    },
    onError: (error: any) => {
      console.error("Falha ao criar receita:", error);
      toast.error('Erro ao adicionar receita.', {
        description: error.response?.data?.detail || 'Verifique os dados e tente novamente.'
      });
    },
  });

  const onSubmit = (data: RecipeFormData) => {
    mutate(data);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Adicionar Nova Receita Afetiva</DialogTitle>
          <DialogDescription>
            Compartilhe um preparo especial e seu significado.
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="flex-1 p-4 -mx-4">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 px-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nome da Receita</FormLabel>
                    <FormControl>
                      <Input placeholder="Bolo de Fubá da Vovó" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="origin_story"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Origem (Opcional)</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Essa receita é da minha família, passada de geração em geração..."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="emotional_value"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Valor Afetivo (Opcional)</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Traz lembranças da infância, de momentos felizes em família..."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="consumption_context"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Contexto de Consumo (Opcional)</FormLabel>
                    <FormControl>
                      <Input placeholder="Café da manhã, Almoço de Domingo, Lanche da tarde" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="ingredients_text"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Ingredientes (Lista Detalhada)</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Ex: 2 xícaras de farinha de trigo, 3 ovos, 1 xícara de açúcar, 1/2 xícara de óleo, 1 xícara de leite, 1 colher de fermento..."
                        {...field}
                        rows={5}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="preparation_method"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Modo de Preparo</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Ex: Em um bowl grande, misture os ovos e o açúcar. Adicione o óleo e o leite. Em seguida, incorpore a farinha e o fermento..."
                        {...field}
                        rows={5}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="servings"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Porções</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="preparation_time_minutes"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tempo de Preparo (min)</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              {/* Campo para is_public pode ser um Switch aqui */}
            </form>
          </Form>
        </ScrollArea>
        <DialogFooter className="mt-4">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>
            Cancelar
          </Button>
          <Button type="submit" form="add-recipe-form" disabled={isPending}>
            {isPending ? 'Salvando...' : 'Salvar Receita'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}