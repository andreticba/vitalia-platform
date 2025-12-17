// frontend/src/app/admin/dashboard/page.tsx em 2025-12-14 11:48
'use client';
import { ProtectedLayout } from '@/components/layout/ProtectedLayout';

export default function AdminDashboard() {
  return (
    <ProtectedLayout>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <h3 className="font-semibold leading-none tracking-tight">Total Usuários</h3>
          <div className="text-2xl font-bold mt-2">1,234</div>
        </div>
        {/* Mais cards... */}
      </div>
      <div className="mt-4 p-4 border rounded-lg border-dashed h-96 flex items-center justify-center">
        Área Administrativa (Gestão de Tenants)
      </div>
    </ProtectedLayout>
  );
}
