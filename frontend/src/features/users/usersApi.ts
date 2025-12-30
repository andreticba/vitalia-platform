// frontend/src/features/users/usersApi.ts

import api from '@/lib/api';
import { UserProfile } from '@/types/auth'; // Usando os tipos gerados/aliased

export interface UserFilters {
  search?: string;
}

export const usersApi = {
  getPatients: async (params?: UserFilters): Promise<UserProfile[]> => {
    const { data } = await api.get<UserProfile[]>('/core/patients/', { 
      params 
    });
    return data;
  },

  getById: async (id: number): Promise<UserProfile> => {
    const { data } = await api.get<UserProfile>(`/core/patients/${id}/`);
    return data;
  }
};