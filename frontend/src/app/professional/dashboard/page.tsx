// frontend/src/app/professional/dashboard/page.tsx
'use client';
import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { Button } from '@/components/ui/button';

export default function ProfessionalDashboard() {
  return (
    <ProtectedLayout>
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Pacientes Ativos</h2>
        <Button>Novo Paciente</Button>
      </div>
      <div className="mt-4 p-4 border rounded-lg bg-card h-96">
        <p className="text-muted-foreground">Lista de pacientes e status dos planos (HITL) aparecerá aqui.</p>
      </div>
    </ProtectedLayout>
  );
}
