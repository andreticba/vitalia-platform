// frontend/src/providers/ThemeProvider.tsx em 2025-12-14 11:48

'use client';

import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

// Mock da API de Tema (Simulando resposta do backend)
const fetchTheme = async () => {
  return new Promise((resolve) => 
    setTimeout(() => resolve({
      // Azul Vibrante (HSL) -> Equivalente ao tailwind blue-600
      primary: '221.2 83.2% 53.3%', 
      primaryForeground: '0 0% 100%', // Texto branco no botão
      radius: '0.75rem', // Arredondamento maior para testar se aplica
    }), 100)
  );
};

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { data: theme } = useQuery({ 
    queryKey: ['theme-config'], 
    queryFn: fetchTheme,
    staleTime: Infinity 
  });

  useEffect(() => {
    if (theme) {
      const root = document.documentElement;
      
      // Injeta as variáveis CSS. O Tailwind usa hsl(var(--primary))
      // @ts-ignore
      root.style.setProperty('--primary', theme.primary);
      // @ts-ignore
      root.style.setProperty('--primary-foreground', theme.primaryForeground);
      // @ts-ignore
      root.style.setProperty('--radius', theme.radius);
      
      console.log('Vitalia Theme Applied:', theme); // Debug para verificar aplicação
    }
  }, [theme]);

  return <>{children}</>;
}
