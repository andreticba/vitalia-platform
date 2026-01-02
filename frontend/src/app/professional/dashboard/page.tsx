// frontend/src/app/professional/dashboard/page.tsx em 2025-12-14 11:48

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Loader2, User, Activity, AlertCircle } from 'lucide-react';

import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';

import { usersApi } from '@/features/users/usersApi';
import { useDebounce } from '@/hooks/useDebounce';

export default function ProfessionalDashboard() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 500); // 500ms delay

  const { data: patients, isLoading, isFetching } = useQuery({
    queryKey: ['patients', debouncedSearch],
    queryFn: () => usersApi.getPatients({ search: debouncedSearch || undefined }),
    placeholderData: (prev) => prev, // Mantém a lista anterior enquanto busca a nova
  });

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-6">
        
        {/* Cabeçalho */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-primary">Meus Pacientes</h1>
            <p className="text-muted-foreground mt-1">
              Gerencie os planos de cuidado e acompanhe a evolução.
            </p>
          </div>
          <Button className="gap-2">
            <User className="h-4 w-4" />
            Cadastrar Paciente
          </Button>
        </div>

        {/* Barra de Busca (Padrão Debounce) */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Buscar por nome, e-mail ou CPF..." 
            className="pl-9"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {isFetching && !isLoading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
            </div>
          )}
        </div>

        {/* Loading Inicial */}
        {isLoading && (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {/* Grid de Pacientes */}
        {!isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {patients?.map((patient) => (
              <Card key={patient.id} className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-transparent hover:border-l-primary">
                <CardHeader className="flex flex-row items-center gap-4 pb-2">
                  <Avatar className="h-12 w-12">
                    <AvatarImage src={patient.avatar_url || ''} />
                    <AvatarFallback>{patient.user.username.substring(0, 2).toUpperCase()}</AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col">
                    <CardTitle className="text-base">{patient.full_name || patient.user.username}</CardTitle>
                    <CardDescription className="text-xs">{patient.user.email}</CardDescription>
                  </div>
                </CardHeader>
                
                <CardContent className="pb-3">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Activity className="h-4 w-4 text-green-500" />
                      <span>Aderência: <strong>85%</strong></span>
                    </div>
                    {/* Badge condicional simulando dados de risco */}
                    <Badge variant="outline" className="text-xs font-normal">
                      Nível 1 (Início)
                    </Badge>
                  </div>
                </CardContent>

                <CardFooter className="bg-muted/20 py-2 px-6 flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">Último acesso: Hoje</span>
                  <Button variant="ghost" size="sm" className="h-7 text-xs">Ver Prontuário</Button>
                </CardFooter>
              </Card>
            ))}

            {/* Estado Vazio */}
            {patients?.length === 0 && (
              <div className="col-span-full py-12 text-center border rounded-lg border-dashed bg-muted/10">
                <div className="flex flex-col items-center gap-2 text-muted-foreground">
                  <AlertCircle className="h-8 w-8 opacity-20" />
                  <p>Nenhum paciente encontrado para "{searchTerm}".</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </ProtectedLayout>
  );
}