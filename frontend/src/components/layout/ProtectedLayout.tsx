// frontend/src/components/layout/ProtectedLayout.tsx em 2025-12-14 11:48

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppSelector } from '@/store/hooks';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Loader2 } from 'lucide-react';

export function ProtectedLayout({ children }: { children: React.ReactNode }) {
  // Agora lemos também o isInitialized
  // @ts-ignore (se o TS reclamar do tipo estendido, pode ignorar por enquanto ou atualizar o types/auth.ts)
  const { isAuthenticated, user, isInitialized } = useAppSelector((state) => state.auth);
  const router = useRouter();

  useEffect(() => {
    // Só toma decisão de redirecionar se o sistema JÁ inicializou
    if (isInitialized && !isAuthenticated) {
      console.warn('[ProtectedLayout] Acesso negado. Redirecionando...');
      router.push('/login');
    }
  }, [isInitialized, isAuthenticated, router]);

  // Se não inicializou, mostra Loading (mesmo que AuthInitializer já mostre, segurança dupla)
  if (!isInitialized) {
    return (
        <div className="flex h-screen items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
    );
  }

  // Se inicializou mas não tá logado, retorna null (o useEffect vai redirecionar)
  if (!isAuthenticated || !user) {
    return null; 
  }

  return (
    <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
      <div className="hidden border-r bg-muted/40 md:block">
        <Sidebar />
      </div>
      <div className="flex flex-col">
        <Header />
        <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}