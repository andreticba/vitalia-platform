// frontend/src/app/home/page.tsx em 2025-12-14 11:48

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Circle, Trophy, Flame } from 'lucide-react';
import { toast } from 'sonner';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { setCredentials } from '@/store/slices/authSlice'; // Para atualizar pontos no redux se necessário
import api from '@/lib/api';

import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';

// Tipos locais
interface Activity {
  id: string;
  title: string;
  activity_type: string;
  is_completed: boolean;
  flexible_data?: { description?: string };
}

interface MyDayResponse {
  has_plan: boolean;
  plan_title?: string;
  schedule?: {
    day_label: string;
    activities: Activity[];
  };
}

export default function ParticipantHome() {
  const queryClient = useQueryClient();
  const { user } = useAppSelector((state) => state.auth);

  // 1. Busca a Agenda do Dia
  const { data: dayData, isLoading } = useQuery<MyDayResponse>({
    queryKey: ['my-day'],
    queryFn: async () => {
      const { data } = await api.get('/medical/my-day/');
      return data;
    },
  });

  // 2. Mutação para Concluir Atividade
  const completeMutation = useMutation({
    mutationFn: async (activityId: string) => {
      await api.patch(`/medical/activities/${activityId}/complete/`);
    },
    onSuccess: () => {
      toast.success('Atividade concluída! +XP', { icon: '🎉' });
      queryClient.invalidateQueries({ queryKey: ['my-day'] });
      // Aqui poderíamos disparar um refetch do profile para atualizar a wallet
      queryClient.invalidateQueries({ queryKey: ['currentUser'] }); 
    },
  });

  // Cálculos de Progresso
  const activities = dayData?.schedule?.activities || [];
  const totalActs = activities.length;
  const completedActs = activities.filter(a => a.is_completed).length;
  const progress = totalActs > 0 ? (completedActs / totalActs) * 100 : 0;

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-6 max-w-2xl mx-auto w-full">
        
        {/* Header Gamificado */}
        <div className="flex items-center justify-between p-6 bg-gradient-to-r from-primary/10 to-transparent rounded-xl border border-primary/20">
          <div>
            <h1 className="text-2xl font-bold text-primary">Olá, {user?.user.username}!</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Vamos manter o ritmo hoje?
            </p>
          </div>
          <div className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="flex items-center gap-1 text-orange-500 font-bold">
                <Flame className="h-5 w-5 fill-orange-500" />
                <span>{user?.participant_data?.current_streak_days || 0}</span>
              </div>
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Dias Seguidos</span>
            </div>
            <div className="flex flex-col items-center">
              <div className="flex items-center gap-1 text-yellow-600 font-bold">
                <Trophy className="h-5 w-5" />
                <span>{user?.participant_data?.gamification_wallet_balance || 0}</span>
              </div>
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Pontos</span>
            </div>
          </div>
        </div>

        {/* Status do Plano */}
        {isLoading ? (
          <Skeleton className="h-40 w-full rounded-xl" />
        ) : !dayData?.has_plan ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center h-40 text-muted-foreground">
              <p>Nenhum plano ativo no momento.</p>
              <p className="text-sm">Aguarde seu profissional enviar o planejamento.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            
            {/* Barra de Progresso do Dia */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm font-medium">
                <span>Progresso Diário ({dayData.schedule?.day_label})</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-3" />
            </div>

            {/* Lista de Atividades */}
            <div className="grid gap-3">
              {activities.map((activity) => (
                <Card 
                  key={activity.id} 
                  className={`transition-all ${activity.is_completed ? 'bg-muted/30 border-transparent' : 'hover:border-primary/50'}`}
                >
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`mt-1 p-2 rounded-full ${activity.is_completed ? 'bg-green-100 text-green-600' : 'bg-primary/10 text-primary'}`}>
                        {/* Ícones dinâmicos baseados no tipo */}
                        {activity.activity_type === 'NUTRITION' ? '🍎' : 
                         activity.activity_type === 'RESISTANCE' ? '🏋️' : '⚡'}
                      </div>
                      <div>
                        <h4 className={`font-semibold ${activity.is_completed ? 'text-muted-foreground line-through' : ''}`}>
                          {activity.title}
                        </h4>
                        {activity.flexible_data?.description && (
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            {activity.flexible_data.description}
                          </p>
                        )}
                      </div>
                    </div>

                    <Button
                      variant={activity.is_completed ? "ghost" : "outline"}
                      size="icon"
                      className={`rounded-full h-12 w-12 shrink-0 ${activity.is_completed ? 'text-green-600' : ''}`}
                      onClick={() => completeMutation.mutate(activity.id)}
                      disabled={activity.is_completed || completeMutation.isPending}
                    >
                      {activity.is_completed ? (
                        <CheckCircle2 className="h-6 w-6" />
                      ) : (
                        <Circle className="h-6 w-6 text-muted-foreground/30" />
                      )}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </ProtectedLayout>
  );
}