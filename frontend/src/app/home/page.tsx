// frontend/src/app/home/page.tsx em 2025-12-14 11:48
'use client';
import { ProtectedLayout } from '@/components/layout/ProtectedLayout';

export default function ParticipantHome() {
  return (
    <ProtectedLayout>
      <div className="grid gap-6">
        <div className="p-6 bg-primary/10 rounded-xl border border-primary/20">
          <h2 className="text-2xl font-bold text-primary">Bom dia! ☀️</h2>
          <p className="mt-2">Sua meta hoje: Caminhar 15 minutos.</p>
        </div>
        
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-4 border rounded-lg h-64">
            <h3 className="font-semibold mb-4">Jardim da Vitalidade</h3>
            {/* Aqui entrará o componente visual de árvore */}
            <div className="w-full h-40 bg-muted rounded flex items-center justify-center text-sm">
              Árvore crescendo...
            </div>
          </div>
          <div className="p-4 border rounded-lg h-64">
            <h3 className="font-semibold mb-4">Próxima Refeição</h3>
            <p>Almoço: Salada de Grão de Bico (Receita Afetiva)</p>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}
