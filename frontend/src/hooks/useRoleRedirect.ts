// frontend/src/hooks/useRoleRedirect.ts em 2025-12-14 11:48

import { useRouter } from 'next/navigation';
import { UserProfile } from '@/types/auth';

export function useRoleRedirect() {
  const router = useRouter();

  const redirectUser = (user: UserProfile) => {
    const roles = user.roles.map(r => r.name);

    // Prioridade de Redirecionamento
    if (roles.includes('Admin Vitalia')) {
      router.push('/admin/dashboard');
    } else if (roles.includes('Profissional de Saúde') || roles.includes('Gestor de Clínica')) {
      router.push('/professional/dashboard');
    } else if (roles.includes('Participante')) {
      router.push('/app/home'); // Área do Paciente
    } else {
      router.push('/onboarding'); // Fallback para novos usuários sem papel definido
    }
  };

  return { redirectUser };
}
