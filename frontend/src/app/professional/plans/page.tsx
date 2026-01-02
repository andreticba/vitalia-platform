// frontend/src/app/professional/plans/page.tsx em 2025-12-14 11:48

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, CheckCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

// Tipagem inline rápida (idealmente mover para types/medical.ts)
interface WellnessPlan {
  id: string;
  title: string;
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'ACTIVE' | 'COMPLETED';
  participant_name: string;
  created_at: string;
}

export default function PlansPage() {
  const queryClient = useQueryClient();

  const { data: plans, isLoading } = useQuery<WellnessPlan[]>({
    queryKey: ['plans'],
    queryFn: async () => {
      const { data } = await api.get('/medical/plans/');
      return data;
    },
  });

  const approveMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/medical/plans/${id}/approve/`);
    },
    onSuccess: () => {
      toast.success('Plano aprovado e ativado!');
      queryClient.invalidateQueries({ queryKey: ['plans'] });
    },
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING_APPROVAL':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Aguardando Aprovação (IA)</Badge>;
      case 'ACTIVE':
        return <Badge className="bg-green-100 text-green-800">Ativo</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <ProtectedLayout>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-primary">Gestão de Planos</h1>
          <p className="text-muted-foreground">Valide as sugestões da IA e acompanhe a evolução.</p>
        </div>
      </div>

      {isLoading && <div>Carregando planos...</div>}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {plans?.map((plan) => (
          <Card key={plan.id} className="border-l-4 border-l-primary">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg">{plan.title}</CardTitle>
                <FileText className="h-5 w-5 text-muted-foreground" />
              </div>
              <CardDescription>Paciente: {plan.participant_name}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 mb-4">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Gerado em: {new Date(plan.created_at).toLocaleDateString()}
                </span>
              </div>
              {getStatusBadge(plan.status)}
            </CardContent>
            <CardFooter className="flex justify-end gap-2 bg-muted/10 py-3">
              <Button variant="outline" size="sm">Ver Detalhes</Button>
              
              {plan.status === 'PENDING_APPROVAL' && (
                <Button 
                  size="sm" 
                  className="gap-2"
                  onClick={() => approveMutation.mutate(plan.id)}
                  disabled={approveMutation.isPending}
                >
                  <CheckCircle className="h-4 w-4" />
                  Aprovar
                </Button>
              )}
            </CardFooter>
          </Card>
        ))}
      </div>
    </ProtectedLayout>
  );
}