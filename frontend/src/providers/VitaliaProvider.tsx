// frontend/src/providers/VitaliaProvider.tsx em 2025-12-14 11:48

'use client';

import { Provider as ReduxProvider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { store } from '@/store';
import { ThemeProvider } from './ThemeProvider';
import { Toaster } from 'sonner';

const queryClient = new QueryClient();

export function VitaliaProvider({ children }: { children: React.ReactNode }) {
  return (
    <ReduxProvider store={store}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          {children}
          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </QueryClientProvider>
    </ReduxProvider>
  );
}
