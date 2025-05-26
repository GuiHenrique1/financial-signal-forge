
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { TrendingUp, TrendingDown, Activity, Clock, AlertCircle, BarChart3 } from 'lucide-react';

interface Signal {
  pair: string;
  timeframe: string;
  signal: 'CALL' | 'PUT' | null;
  timestamp: string;
  strength?: number;
  reason?: string;
}

const Index = () => {
  const [currentSignal, setCurrentSignal] = useState<Signal | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const fetchSignal = async () => {
    setIsLoading(true);
    try {
      // Simulated API call since backend is not connected yet
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockSignal: Signal = {
        pair: 'EUR_USD',
        timeframe: 'M5',
        signal: Math.random() > 0.6 ? (Math.random() > 0.5 ? 'CALL' : 'PUT') : null,
        timestamp: new Date().toISOString(),
        strength: Math.random() * 0.4 + 0.6,
        reason: 'RSI oversold + MACD bullish crossover'
      };
      
      setCurrentSignal(mockSignal);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Error fetching signal:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSignal();
    const interval = setInterval(fetchSignal, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getSignalIcon = (signal: string | null) => {
    if (signal === 'CALL') return <TrendingUp className="h-5 w-5 text-green-500" />;
    if (signal === 'PUT') return <TrendingDown className="h-5 w-5 text-red-500" />;
    return <Activity className="h-5 w-5 text-gray-400" />;
  };

  const getSignalColor = (signal: string | null) => {
    if (signal === 'CALL') return 'bg-green-100 text-green-800 border-green-200';
    if (signal === 'PUT') return 'bg-red-100 text-red-800 border-red-200';
    return 'bg-gray-100 text-gray-600 border-gray-200';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gray-900 flex items-center justify-center gap-3">
            <BarChart3 className="h-10 w-10 text-blue-600" />
            Financial Signal Forge
          </h1>
          <p className="text-xl text-gray-600">Sistema Avançado de Sinais de Trading</p>
        </div>

        {/* Current Signal Card */}
        <Card className="w-full max-w-2xl mx-auto shadow-lg">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center gap-2">
              {getSignalIcon(currentSignal?.signal)}
              Sinal Atual
            </CardTitle>
            <CardDescription>
              Par: {currentSignal?.pair || 'EUR_USD'} | Timeframe: {currentSignal?.timeframe || 'M5'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              {currentSignal?.signal ? (
                <Badge className={`text-lg py-2 px-4 ${getSignalColor(currentSignal.signal)}`}>
                  {currentSignal.signal === 'CALL' ? '📈 COMPRA' : '📉 VENDA'}
                </Badge>
              ) : (
                <Badge className={`text-lg py-2 px-4 ${getSignalColor(null)}`}>
                  ⏳ AGUARDANDO
                </Badge>
              )}
            </div>

            {currentSignal?.signal && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Força do Sinal:</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${currentSignal.signal === 'CALL' ? 'bg-green-500' : 'bg-red-500'}`}
                        style={{ width: `${(currentSignal.strength || 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600">
                      {Math.round((currentSignal.strength || 0) * 100)}%
                    </span>
                  </div>
                </div>
                
                {currentSignal.reason && (
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Razão:</strong> {currentSignal.reason}
                    </p>
                  </div>
                )}
              </div>
            )}

            <Separator />

            <div className="flex items-center justify-between text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                Última atualização: {lastUpdate}
              </div>
              <Button 
                onClick={fetchSignal} 
                disabled={isLoading}
                variant="outline"
                size="sm"
              >
                {isLoading ? 'Atualizando...' : 'Atualizar'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Status da API</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <span className="text-sm">Simulação Ativa</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Última Análise</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-500" />
                <span className="text-sm">{currentSignal?.timestamp ? 
                  new Date(currentSignal.timestamp).toLocaleTimeString() : 
                  'Aguardando...'}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Bot Telegram</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-orange-500" />
                <span className="text-sm">Configuração Pendente</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Info Banner */}
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="text-center space-y-2">
              <h3 className="font-semibold text-blue-900">🚀 Sistema em Modo Demonstração</h3>
              <p className="text-blue-800 text-sm">
                Configure suas APIs (Oanda, Telegram) para ativar os sinais reais de trading.
                Acesse a documentação para instruções completas de configuração.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Index;
