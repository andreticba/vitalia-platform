// frontend/src/components/layout/Sidebar.tsx em 2025-12-14 11:48

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Utensils, 
  Activity, 
  Settings, 
  ShieldCheck, 
  HeartHandshake 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppSelector } from '@/store/hooks'; // Importe do seu hook tipado
import { Button } from '@/components/ui/button';

// Definição dos Links de Navegação
type NavItem = {
  label: string;
  href: string;
  icon: React.ElementType;
  roles: string[]; // Quais papéis podem ver este link
};

const NAV_ITEMS: NavItem[] = [
  // --- Admin ---
  { label: 'Visão Geral', href: '/admin/dashboard', icon: LayoutDashboard, roles: ['Admin Vitalia'] },
  { label: 'Organizações', href: '/admin/organizations', icon: Users, roles: ['Admin Vitalia'] },
  
  // --- Profissional ---
  { label: 'Meus Pacientes', href: '/professional/dashboard', icon: Users, roles: ['Profissional de Saúde', 'Gestor de Clínica'] },
  { label: 'Planos Pendentes', href: '/professional/plans', icon: FileText, roles: ['Profissional de Saúde'] },
  { label: 'Validar Receitas', href: '/professional/recipes', icon: ShieldCheck, roles: ['Profissional de Saúde'] },
  
  // --- Participante (App) ---
  { label: 'Meu Dia', href: '/app/home', icon: Activity, roles: ['Participante'] },
  { label: 'Receitas Afetivas', href: '/app/recipes', icon: Utensils, roles: ['Participante'] },
  { label: 'Rede de Apoio', href: '/app/social', icon: HeartHandshake, roles: ['Participante'] },
  
  // --- Comum ---
  { label: 'Configurações', href: '/settings', icon: Settings, roles: ['Admin Vitalia', 'Profissional de Saúde', 'Participante'] },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAppSelector((state) => state.auth);

  if (!user) return null;

  // Extrai os nomes dos papéis do usuário
  const userRoleNames = user.roles.map(r => r.name);

  // Filtra itens baseados nos papéis
  const authorizedItems = NAV_ITEMS.filter(item => 
    item.roles.some(role => userRoleNames.includes(role))
  );

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card">
      <div className="flex h-14 items-center border-b px-6">
        <span className="text-lg font-bold text-primary">Vitalia</span>
      </div>
      
      <div className="flex-1 overflow-auto py-4">
        <nav className="grid items-start px-4 text-sm font-medium">
          {authorizedItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 transition-all hover:text-primary",
                  isActive 
                    ? "bg-primary/10 text-primary" 
                    : "text-muted-foreground hover:bg-muted"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto border-t p-4">
        <div className="flex items-center gap-3 px-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
            {user.user.username.substring(0, 2).toUpperCase()}
          </div>
          <div className="grid gap-0.5 text-xs">
            <span className="font-semibold">{user.full_name || user.user.username}</span>
            <span className="text-muted-foreground truncate w-32">
              {user.roles[0]?.name || 'Usuário'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
