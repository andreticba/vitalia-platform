// frontend/src/app/page.tsx em 2025-12-14 11:48
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 gap-4">
      <h1 className="text-4xl font-bold text-primary">Vitalia Platform</h1>
      <p className="text-muted-foreground text-lg">Ecossistema de Saúde B2B2C</p>
      
      <div className="flex gap-4">
        <Button>Login Profissional</Button>
        <Button variant="outline">Sou Participante</Button>
      </div>
    </main>
  );
}
