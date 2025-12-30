// frontend/src/providers/AuthInitializer.tsx

"use client";

import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import axios from "axios";
import { setCredentials, logout } from "@/store/slices/authSlice";
import { UserProfile } from "@/types/auth";
import { Loader2 } from "lucide-react";

// Componente de Loading Simples para cobrir a tela enquanto verificamos a sessão
const FullScreenLoader = () => (
  <div className="flex h-screen w-screen items-center justify-center bg-background">
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="h-10 w-10 animate-spin text-primary" />
      <p className="text-muted-foreground text-sm">Restaurando sessão segura...</p>
    </div>
  </div>
);

export function AuthInitializer({ children }: { children: React.ReactNode }) {
  const dispatch = useDispatch();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const restoreSession = async () => {
      // 1. Tenta recuperar o refresh token do storage
      // Nota: Não lemos o access token aqui para forçar uma validação de segurança (refresh)
      // ou podemos ler para otimizar, mas o refresh garante que o usuário não foi banido.
      const persistedRefresh = typeof window !== 'undefined' ? localStorage.getItem("refresh") : null;

      if (!persistedRefresh) {
        setIsLoading(false);
        return;
      }

      try {
        // 2. Tenta renovar o token usando a URL da API (hardcoded ou via env)
        // Usamos axios puro aqui para evitar dependências circulares com o interceptor do @/lib/api
        const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        
        const refreshResponse = await axios.post<{ access: string }>(
          `${baseURL}/auth/token/refresh/`,
          { refresh: persistedRefresh }
        );

        const newAccessToken = refreshResponse.data.access;

        // 3. Com o token novo, busca os dados do usuário atualizado
        const userResponse = await axios.get<UserProfile>(
          `${baseURL}/core/users/me/`,
          {
            headers: { Authorization: `Bearer ${newAccessToken}` },
          }
        );

        // 4. Sucesso: Hidrata o Redux
        dispatch(
          setCredentials({
            user: userResponse.data,
            accessToken: newAccessToken,
            refreshToken: persistedRefresh,
          })
        );
      } catch (error) {
        console.warn("Sessão expirada ou inválida:", error);
        // Se falhar, limpa tudo para garantir um estado limpo
        dispatch(logout());
      } finally {
        // 5. Libera a UI
        setIsLoading(false);
      }
    };

    restoreSession();
  }, [dispatch]);

  if (isLoading) {
    return <FullScreenLoader />;
  }

  return <>{children}</>;
}