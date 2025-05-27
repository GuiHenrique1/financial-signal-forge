
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowUp, ArrowDown, Target, Clock, TrendingUp } from 'lucide-react';

interface Signal {
  id: string;
  pair: string;
  timeframe: string;
  direction: 'BUY' | 'SELL';
  strength: number;
  entry_price: number;
  current_price: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  take_profit_3: number;
  distance_pips?: number;
  proximity_score?: number;
  timestamp: string;
  reasons: string[];
}

interface SignalsTableProps {
  signals: Signal[];
  onCopySignal?: (signal: Signal) => void;
}

const SignalsTable: React.FC<SignalsTableProps> = ({ signals, onCopySignal }) => {
  const getDirectionIcon = (direction: string) => {
    return direction === 'BUY' ? 
      <ArrowUp className="w-4 h-4 text-green-500" /> : 
      <ArrowDown className="w-4 h-4 text-red-500" />;
  };

  const getDirectionBadge = (direction: string) => {
    return (
      <Badge className={direction === 'BUY' ? 'bg-green-500 hover:bg-green-600' : 'bg-red-500 hover:bg-red-600'}>
        {getDirectionIcon(direction)}
        {direction}
      </Badge>
    );
  };

  const getProximityBadge = (distance_pips?: number, proximity_score?: number) => {
    if (!distance_pips) return null;
    
    const getColor = () => {
      if (distance_pips <= 5) return 'bg-green-500';
      if (distance_pips <= 10) return 'bg-yellow-500';
      return 'bg-orange-500';
    };

    const getLabel = () => {
      if (distance_pips <= 5) return 'Muito Próximo';
      if (distance_pips <= 10) return 'Próximo';
      return 'Distante';
    };

    return (
      <Badge className={`${getColor()} text-white`}>
        <Target className="w-3 h-3 mr-1" />
        {distance_pips}p - {getLabel()}
      </Badge>
    );
  };

  const getStrengthBadge = (strength: number) => {
    const percentage = Math.round(strength * 100);
    const getColor = () => {
      if (percentage >= 80) return 'bg-green-500';
      if (percentage >= 60) return 'bg-yellow-500';
      return 'bg-gray-500';
    };

    return (
      <Badge className={`${getColor()} text-white`}>
        <TrendingUp className="w-3 h-3 mr-1" />
        {percentage}%
      </Badge>
    );
  };

  if (signals.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">
            <Target className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">Nenhum sinal próximo encontrado</p>
            <p className="text-sm">Aguardando sinais dentro da faixa de proximidade configurada</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Sinais Ativos por Proximidade</h3>
        <Badge variant="outline" className="text-blue-600">
          {signals.length} sinal{signals.length !== 1 ? 'is' : ''} próximo{signals.length !== 1 ? 's' : ''}
        </Badge>
      </div>

      {signals.map((signal) => (
        <Card key={signal.id} className="border-l-4 border-l-blue-500">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                {signal.pair.replace('_', '/')}
                {getDirectionBadge(signal.direction)}
              </CardTitle>
              <div className="flex items-center gap-2">
                {getProximityBadge(signal.distance_pips, signal.proximity_score)}
                {getStrengthBadge(signal.strength)}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Timeframe:</span>
                <p className="font-medium">{signal.timeframe}</p>
              </div>
              <div>
                <span className="text-gray-500">Preço Atual:</span>
                <p className="font-medium">{signal.current_price}</p>
              </div>
              <div>
                <span className="text-gray-500">Entrada:</span>
                <p className="font-medium text-blue-600">{signal.entry_price}</p>
              </div>
              <div>
                <span className="text-gray-500">Distância:</span>
                <p className="font-medium text-orange-600">{signal.distance_pips || 0} pips</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Stop Loss:</span>
                <p className="font-medium text-red-600">{signal.stop_loss}</p>
              </div>
              <div>
                <span className="text-gray-500">TP1:</span>
                <p className="font-medium text-green-600">{signal.take_profit_1}</p>
              </div>
              <div>
                <span className="text-gray-500">TP2:</span>
                <p className="font-medium text-green-600">{signal.take_profit_2}</p>
              </div>
              <div>
                <span className="text-gray-500">TP3:</span>
                <p className="font-medium text-green-600">{signal.take_profit_3}</p>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-gray-500 text-sm">Análise Técnica:</span>
              <div className="flex flex-wrap gap-1">
                {signal.reasons.map((reason, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {reason}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t">
              <div className="flex items-center text-xs text-gray-500">
                <Clock className="w-3 h-3 mr-1" />
                {new Date(signal.timestamp).toLocaleString('pt-BR')}
              </div>
              {onCopySignal && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onCopySignal(signal)}
                  className="text-xs"
                >
                  Copiar Sinal
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default SignalsTable;
