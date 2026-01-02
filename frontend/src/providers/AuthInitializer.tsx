// frontend/src/providers/AuthInitializer.tsx em 2025-12-14 11:48

"use client";

import { useEffect, useRef } from "react";
import { useDispatch } from "react-redux";
import axios from "axios";
import { setCredentials, logout, initializeAuth, STORAGE_KEYS } from "@/store/slices/authSlice";
import { UserProfile } from "@/types/auth";
import { Loader2 } from "lucide-react";
import { useAppSelector } from "@/store/hooks";

const FullScreenLoader = () => (
  <div className="flex h-screen w-screen items-center justify-center bg-background flex-col gap-4">
    <Loader2 className="h-10 w-10 animate-spin text-primary" />
    <p className="text-muted-foreground text-sm font-medium">
      Conectando ao Data Vault...
    </p>
  </div>
);

export function AuthInitializer({ children }: { children: React.ReactNode }) {
  const dispatch = useDispatch();
  const isInitialized = useAppSelector((state) => state.auth.isInitialized);
  const isMounted = useRef(false);

  useEffect(() => {
    if (isMounted.current) return;
    isMounted.current = true;

    const initAuth = async () => {
      console.log("[AuthInitializer] 🚀 Iniciando Boot...");
      
      const access = typeof window !== 'undefined' ? sessionStorage.getItem(STORAGE_KEYS.ACCESS) : null;
      const refresh = typeof window !== 'undefined' ? sessionStorage.getItem(STORAGE_KEYS.REFRESH) : null;

      if (!access || !refresh) {
        console.log("[AuthInitializer] Nenhum token encontrado. Visitante.");
        dispatch(initializeAuth()); // Marca como inicializado (mas deslogado)
        return;
      }

      try {
        const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        
        // Tenta validar o token existente
        const { data: user } = await axios.get<UserProfile>(
            `${baseURL}/core/users/me/`,
            { headers: { Authorization: `Bearer ${access}` } }
        );

        console.log("[AuthInitializer] ✅ Sessão restaurada:", user.user.username);
        dispatch(setCredentials({ user, accessToken: access, refreshToken: refresh }));

      } catch (error) {
        console.warn("[AuthInitializer] ⚠️ Token expirado. Tentando refresh...");
        
        try {
            const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
            const { data: tokens } = await axios.post(
                `${baseURL}/auth/token/refresh/`,
                { refresh }
            );

            const { data: user } = await axios.get<UserProfile>(
                `${baseURL}/core/users/me/`,
                { headers: { Authorization: `Bearer ${tokens.access}` } }
            );

            console.log("[AuthInitializer] ✅ Sessão renovada.");
            dispatch(setCredentials({
                user,
                accessToken: tokens.access,
                refreshToken: refresh 
            }));

        } catch (refreshError) {
            console.error("[AuthInitializer] ❌ Falha fatal. Logout.", refreshError);
            dispatch(logout()); // Isso também seta isInitialized = true
        }
      }
    };

    initAuth();
  }, [dispatch]);

  // Bloqueia a renderização dos filhos (ProtectedLayout) até o Redux estar pronto
  if (!isInitialized) {
    return <FullScreenLoader />;
  }

  return <>{children}</>;
}