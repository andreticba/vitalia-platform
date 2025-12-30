// frontend/src/providers/ThemeProvider.tsx - Atualizado para White-Label (Vitalia) em 2025-12-14 11:48

'use client';

import React, { useEffect } from 'react';
import { ThemeProvider as NextThemesProvider } from 'next-themes';
import { type ThemeProviderProps } from 'next-themes/dist/types';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api'; // Importa a instância do axios configurada

// Interface para as configurações de tema vindas do backend
interface BackendThemeConfig {
  primary_color?: string;
  platform_name?: string;
  // Outras propriedades como logo_url, secondary_color, etc.
}

// Mock da API de Tema (Simulando resposta do backend baseada no tenant)
// No futuro, isso será substituído por uma chamada real à /api/v1/core/theme-config/
const fetchThemeConfig = async (): Promise<BackendThemeConfig> => {
  // Simula uma chamada API com delay
  return new Promise((resolve) =>
    setTimeout(() => {
      // Exemplo de tema para a Vitalia padrão (azul-esverdeado)
      // No futuro, a API retornaria isso com base no organization_id do usuário logado
      resolve({
        primary_color: '185 60% 35%', // Exemplo de HSL para um teal
        platform_name: 'Vitalia Saúde',
        // ... outras configurações
      });
    }, 200) // Pequeno delay para simular a rede
  );
};

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  const { data: themeConfig, isLoading, isError } = useQuery<BackendThemeConfig>({
    queryKey: ['theme-config'],
    queryFn: fetchThemeConfig,
    staleTime: 1000 * 60 * 60 * 24, // 24 horas de cache
    refetchOnWindowFocus: false,
    retry: 1,
  });

  useEffect(() => {
    if (themeConfig?.primary_color) {
      const root = document.documentElement;
      // Define a cor primária dinâmica vinda do backend
      root.style.setProperty('--primary', themeConfig.primary_color);
      // Opcional: ajustar outras cores ou raios se existirem no themeConfig
      // root.style.setProperty('--radius', themeConfig.radius);
      console.log(`[Vitalia Theme] Tema aplicado: ${themeConfig.platform_name || 'Personalizado'} (Primary: ${themeConfig.primary_color})`);
    } else if (!isLoading && isError) {
      console.error("[Vitalia Theme] Falha ao carregar tema do backend. Usando tema padrão.");
    }
  }, [themeConfig, isLoading, isError]);

  return (
    <NextThemesProvider {...props}>
      {children}
    </NextThemesProvider>
  );
}