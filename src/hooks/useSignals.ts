
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService, TradingSignal } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { useEffect } from 'react';

export const useSignals = () => {
  const { toast } = useToast();
  
  const query = useQuery({
    queryKey: ['signals'],
    queryFn: () => apiService.getSignals(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Handle errors using useEffect
  useEffect(() => {
    if (query.error) {
      toast({
        title: "Erro ao buscar sinais",
        description: "Usando dados offline como fallback",
        variant: "destructive"
      });
    }
  }, [query.error, toast]);

  return query;
};

export const useLatestSignal = () => {
  return useQuery({
    queryKey: ['latest-signal'],
    queryFn: () => apiService.getLatestSignal(),
    refetchInterval: 15000, // Refetch every 15 seconds
  });
};

export const useProximitySignals = (maxDistance: number = 15) => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  const query = useQuery({
    queryKey: ['proximity-signals', maxDistance],
    queryFn: () => apiService.getProximitySignals(maxDistance),
    refetchInterval: 20000, // Refetch every 20 seconds
  });

  // Show notification for new proximity signals
  useEffect(() => {
    if (query.data && query.data.length > 0) {
      const veryCloseSignals = query.data.filter(signal => (signal.distance_pips || 0) <= 5);
      
      if (veryCloseSignals.length > 0) {
        veryCloseSignals.forEach(signal => {
          toast({
            title: "🎯 Sinal Muito Próximo!",
            description: `${signal.pair.replace('_', '/')} ${signal.direction} - ${signal.distance_pips} pips`,
          });
        });
      }
    }
  }, [query.data, toast]);

  return query;
};

export const useMarketData = () => {
  return useQuery({
    queryKey: ['market-data'],
    queryFn: () => apiService.getMarketData(),
    refetchInterval: 10000, // Refetch every 10 seconds
  });
};

export const useSystemStatus = () => {
  return useQuery({
    queryKey: ['system-status'],
    queryFn: () => apiService.getSystemStatus(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};
