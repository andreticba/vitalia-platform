// frontend/src/app/login/page.tsx em 2025-12-14 11:48

'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useDispatch } from 'react-redux';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';

import { loginSchema, LoginSchema } from '@/features/auth/authSchema';
import { authApi } from '@/features/auth/authApi';
import { setCredentials, logout } from '@/store/slices/authSlice';
import { useRoleRedirect } from '@/hooks/useRoleRedirect';

export default function LoginPage() {
  const dispatch = useDispatch();
  const { redirectUser } = useRoleRedirect();

  // --- CORREÇÃO DE SEGURANÇA E ESTADO ---
  // Ao entrar na tela de login, garantimos que qualquer sessão anterior seja destruída.
  // Isso resolve o problema de "Menu do Admin aparecendo para o Participante"
  // quando se troca de usuário na mesma aba.
  useEffect(() => {
    dispatch(logout());
    sessionStorage.clear(); // Limpeza redundante de segurança
    localStorage.clear();
  }, [dispatch]);
  // ---------------------------------------

  const form = useForm<LoginSchema>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      dispatch(setCredentials({
        accessToken: data.tokens.access,
        refreshToken: data.tokens.refresh,
        user: data.user
      }));
      
      toast.success(`Bem-vindo de volta, ${data.user.full_name || data.user.user.username}!`);
      redirectUser(data.user);
    },
    onError: (error: any) => {
      console.error('Login failed:', error);
      const msg = error.response?.data?.detail || 'Credenciais inválidas ou erro no servidor.';
      toast.error('Falha no Login', { description: msg });
    }
  });

  const onSubmit = (values: LoginSchema) => {
    loginMutation.mutate(values);
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md border-muted bg-card shadow-lg">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-primary">Vitalia Acesso</CardTitle>
          <CardDescription>
            Entre na sua conta para acessar o ecossistema de saúde.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Usuário</FormLabel>
                    <FormControl>
                      <Input placeholder="seu.usuario" {...field} disabled={loginMutation.isPending} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Senha</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="••••••••" {...field} disabled={loginMutation.isPending} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
                {loginMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Entrando...
                  </>
                ) : (
                  'Entrar'
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex justify-center border-t p-4">
          <p className="text-sm text-muted-foreground">
            Esqueceu a senha? <a href="#" className="text-primary hover:underline">Recuperar acesso</a>
          </p>
        </CardFooter>
      </Card>
    </main>
  );
}