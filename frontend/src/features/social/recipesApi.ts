// frontend/src/features/social/recipesApi.ts

import api from '@/lib/api';
import { FamilyRecipe, FamilyRecipeInput } from '@/types/social';

// Interface para tipar os parâmetros de filtro suportados pelo Backend
export interface RecipeFilters {
  search?: string;
  // Futuramente podemos adicionar: page, page_size, is_public, etc.
}

export const recipesApi = {
  // Agora aceita um objeto de filtros opcional
  getAll: async (params?: RecipeFilters): Promise<FamilyRecipe[]> => {
    // O axios serializa automaticamente o objeto params para ?search=valor
    const { data } = await api.get<FamilyRecipe[]>('/social/recipes/', { 
      params 
    });
    return data;
  },

  getById: async (id: string): Promise<FamilyRecipe> => {
    const { data } = await api.get<FamilyRecipe>(`/social/recipes/${id}/`);
    return data;
  },

  create: async (payload: FamilyRecipeInput): Promise<FamilyRecipe> => {
    const { data } = await api.post<FamilyRecipe>('/social/recipes/', payload);
    return data;
  },
  
  like: async (id: string): Promise<{ likes_count: number }> => {
    const { data } = await api.post<{ likes_count: number }>(`/social/recipes/${id}/like/`);
    return data;
  }
};