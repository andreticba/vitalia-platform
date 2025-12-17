// frontend/src/features/auth/authApi.ts em 2025-12-14 11:48

import api from '@/lib/api';
import { LoginSchema } from './authSchema'; // Criaremos abaixo
import { UserProfile } from '@/types/auth';

interface TokenResponse {
  access: string;
  refresh: string;
}

export const authApi = {
  /**
   * Realiza o login e, em seguida, busca os dados do usuário.
   * Padrão "Two-Step Login" para garantir identidade completa.
   */
  login: async (credentials: LoginSchema): Promise<{ tokens: TokenResponse; user: UserProfile }> => {
    // 1. Obter Tokens
    const { data: tokens } = await api.post<TokenResponse>('/auth/token/', credentials);
    
    // 2. Obter Perfil (usando o token recém-adquirido)
    const { data: user } = await api.get<UserProfile>('/core/users/me/', {
      headers: { Authorization: `Bearer ${tokens.access}` }
    });

    return { tokens, user };
  }
};
