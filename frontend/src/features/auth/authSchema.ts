// frontend/src/features/auth/authSchema.ts em 2025-12-14 11:48

import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().min(1, 'Usuário é obrigatório'),
  password: z.string().min(1, 'Senha é obrigatória'),
});

export type LoginSchema = z.infer<typeof loginSchema>;
