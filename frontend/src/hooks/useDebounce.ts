// frontend/src/hooks/useDebounce.ts

import { useEffect, useState } from 'react';

/**
 * Hook para adiar a atualização de um valor (Debounce).
 * Útil para inputs de busca que disparam chamadas de API.
 * 
 * @param value O valor a ser observado (ex: termo de busca)
 * @param delay O tempo de espera em ms (padrão: 500ms)
 * @returns O valor "atrasado" que só atualiza após o delay
 */
export function useDebounce<T>(value: T, delay: number = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Configura um timer para atualizar o valor
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Limpa o timer se o valor mudar (usuário digitou mais uma letra)
    // ou se o componente desmontar
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}