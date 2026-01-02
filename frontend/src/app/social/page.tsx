// frontend/src/app/social/page.tsx em 2025-12-14 11:48

'use client';

import { useQuery } from '@tanstack/react-query';
import { Heart, Trophy, Utensils, User } from 'lucide-react';
import api from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';

interface FeedItem {
  type: 'RECIPE' | 'ACTIVITY' | 'BADGE';
  id: string;
  title: string;
  author_name: string;
  timestamp: string;
  details: any;
  likes_count: number;
}

export default function SocialPage() {
  const { data: feed, isLoading } = useQuery<FeedItem[]>({
    queryKey: ['social-feed'],
    queryFn: async () => {
      const { data } = await api.get('/social/feed/');
      return data;
    },
  });

  const getIcon = (type: string) => {
    switch (type) {
      case 'RECIPE': return <Utensils className="h-5 w-5 text-orange-500" />;
      case 'ACTIVITY': return <Heart className="h-5 w-5 text-red-500" />;
      case 'BADGE': return <Trophy className="h-5 w-5 text-yellow-500" />;
      default: return <User className="h-5 w-5" />;
    }
  };

  return (
    <ProtectedLayout>
      <div className="max-w-2xl mx-auto w-full space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-primary">Rede de Apoio</h1>
          <p className="text-muted-foreground">O que sua comunidade está conquistando.</p>
        </div>

        {isLoading && <div>Carregando feed...</div>}

        <div className="space-y-4">
          {feed?.map((item) => (
            <Card key={`${item.type}-${item.id}`} className="hover:bg-muted/5 transition-colors">
              <CardContent className="p-4 flex gap-4">
                <Avatar>
                  <AvatarFallback>{item.author_name.substring(0, 2).toUpperCase()}</AvatarFallback>
                </Avatar>
                
                <div className="flex-1 space-y-1">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-semibold text-sm">
                        {item.author_name}
                        <span className="text-muted-foreground font-normal ml-2">
                          • {new Date(item.timestamp).toLocaleDateString()}
                        </span>
                      </p>
                      <h3 className="text-base font-medium mt-1 flex items-center gap-2">
                        {getIcon(item.type)}
                        {item.title}
                      </h3>
                    </div>
                    {item.type === 'ACTIVITY' && (
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        +{item.details.points} XP
                      </Badge>
                    )}
                  </div>
                  
                  {item.type === 'RECIPE' && (
                    <div className="mt-2 flex gap-2">
                        {item.details.tags?.map((tag: string) => (
                            <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
                        ))}
                    </div>
                  )}
                  
                  <div className="pt-2 flex items-center gap-4 text-xs text-muted-foreground">
                    <button className="flex items-center gap-1 hover:text-red-500 transition-colors">
                        <Heart className="h-4 w-4" /> {item.likes_count} Curtidas
                    </button>
                    <button className="hover:text-primary">Comentar</button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </ProtectedLayout>
  );
}