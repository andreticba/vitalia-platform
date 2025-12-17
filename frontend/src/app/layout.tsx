// frontend/src/app/layout.tsx em 2025-12-14 11:48
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { VitaliaProvider } from '@/providers/VitaliaProvider';
import { cn } from '@/lib/utils';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Vitalia - Saúde & Bem-Estar',
  description: 'Plataforma integrada de gestão de saúde.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className={cn("min-h-screen bg-background font-sans antialiased", inter.className)}>
        <VitaliaProvider>
          {children}
        </VitaliaProvider>
      </body>
    </html>
  );
}
