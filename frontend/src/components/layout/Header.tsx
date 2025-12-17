// frontend/src/components/layout/Header.tsx em 2025-12-14 11:48

'use client';

import { useAppDispatch } from '@/store/hooks';
import { logout } from '@/store/slices/authSlice';
import { Button } from '@/components/ui/button';
import { LogOut, Bell } from 'lucide-react';
import { useRouter } from 'next/navigation';

export function Header() {
  const dispatch = useAppDispatch();
  const router = useRouter();

  const handleLogout = () => {
    dispatch(logout());
    router.push('/login');
  };

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-6 lg:h-[60px]">
      <div className="flex-1">
        {/* Breadcrumbs ou Título Dinâmico viriam aqui */}
        <h1 className="text-lg font-semibold md:text-xl">Dashboard</h1>
      </div>
      
      <Button variant="ghost" size="icon">
        <Bell className="h-5 w-5 text-muted-foreground" />
      </Button>
      
      <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-2">
        <LogOut className="h-4 w-4" />
        Sair
      </Button>
    </header>
  );
}
