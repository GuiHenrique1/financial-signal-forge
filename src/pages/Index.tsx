
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, TrendingDown, Activity, Clock, AlertCircle, BarChart3, Calculator, Target, DollarSign } from 'lucide-react';

interface TradingSignal {
  id: string;
  pair: string;
  timeframe: string;
  direction: 'BUY' | 'SELL';
  strength: number;
  reasons: string[];
  entry_price: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  take_profit_3: number;
  risk_reward_1: number;
  risk_reward_2: number;
  risk_reward_3: number;
  timestamp: string;
  current_price: number;
  indicators: {
    rsi: number;
    macd: number;
    macd_signal: number;
    macd_hist: number;
    sma_fast: number;
    sma_slow: number;
    atr: number;
  };
  status: string;
}

interface PositionSize {
  lot_size?: number;
  units?: number;
  risk_amount: number;
  max_loss: number;
  position_value: number;
  category: string;
}

const Index = () => {
  const [activeSignals, setActiveSignals] = useState<TradingSignal[]>([]);
  const [signalHistory, setSignalHistory] = useState<TradingSignal[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [accountBalance, setAccountBalance] = useState<number>(1000);
  const [riskPercent, setRiskPercent] = useState<number>(1);
  const [selectedPair, setSelectedPair] = useState<string>('all');
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('all');

  // Simulated data for demonstration
  const mockSignals: TradingSignal[] = [
    {
      id: 'EUR_USD_H4_1640995200',
      pair: 'EUR_USD',
      timeframe: 'H4',
      direction: 'BUY',
      strength: 0.75,
      reasons: ['RSI oversold recovery', 'MACD bullish crossover', 'Golden Cross + price above MAs'],
      entry_price: 1.0850,
      stop_loss: 1.0810,
      take_profit_1: 1.0890,
      take_profit_2: 1.0930,
      take_profit_3: 1.0970,
      risk_reward_1: 1.0,
      risk_reward_2: 2.0,
      risk_reward_3: 3.0,
      timestamp: new Date().toISOString(),
      current_price: 1.0850,
      indicators: {
        rsi: 32.5,
        macd: 0.000123,
        macd_signal: 0.000089,
        macd_hist: 0.000034,
        sma_fast: 1.0840,
        sma_slow: 1.0820,
        atr: 0.0025
      },
      status: 'ACTIVE'
    },
    {
      id: 'GBP_USD_H1_1640995300',
      pair: 'GBP_USD',
      timeframe: 'H1',
      direction: 'SELL',
      strength: 0.68,
      reasons: ['RSI overbought decline', 'MACD bearish crossover'],
      entry_price: 1.3420,
      stop_loss: 1.3460,
      take_profit_1: 1.3380,
      take_profit_2: 1.3340,
      take_profit_3: 1.3300,
      risk_reward_1: 1.0,
      risk_reward_2: 2.0,
      risk_reward_3: 3.0,
      timestamp: new Date(Date.now() - 300000).toISOString(),
      current_price: 1.3420,
      indicators: {
        rsi: 72.8,
        macd: -0.000089,
        macd_signal: 0.000034,
        macd_hist: -0.000123,
        sma_fast: 1.3430,
        sma_slow: 1.3450,
        atr: 0.0035
      },
      status: 'ACTIVE'
    }
  ];

  const fetchSignals = async () => {
    setIsLoading(true);
    try {
      // Simulated API call - replace with actual backend
      await new Promise(resolve => setTimeout(resolve, 1000));
      setActiveSignals(mockSignals);
      setSignalHistory([...mockSignals, ...mockSignals.map(s => ({ ...s, id: s.id + '_old', status: 'CLOSED' }))]);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Error fetching signals:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const calculatePositionSize = (signal: TradingSignal): PositionSize => {
    const riskAmount = accountBalance * (riskPercent / 100);
    const priceDistance = Math.abs(signal.entry_price - signal.stop_loss);
    const pipValue = 10; // Simplified for forex pairs
    const pipsDistance = priceDistance / 0.0001;
    const lotSize = riskAmount / (pipsDistance * pipValue);
    
    return {
      lot_size: parseFloat(lotSize.toFixed(3)),
      risk_amount: riskAmount,
      max_loss: parseFloat((lotSize * pipsDistance * pipValue).toFixed(2)),
      position_value: parseFloat((lotSize * 100000 * signal.entry_price).toFixed(2)),
      category: 'forex'
    };
  };

  const getSignalIcon = (direction: string) => {
    return direction === 'BUY' ? 
      <TrendingUp className="h-5 w-5 text-green-500" /> : 
      <TrendingDown className="h-5 w-5 text-red-500" />;
  };

  const getSignalColor = (direction: string) => {
    return direction === 'BUY' ? 
      'bg-green-100 text-green-800 border-green-200' : 
      'bg-red-100 text-red-800 border-red-200';
  };

  const filteredSignals = activeSignals.filter(signal => {
    const pairMatch = selectedPair === 'all' || signal.pair === selectedPair;
    const timeframeMatch = selectedTimeframe === 'all' || signal.timeframe === selectedTimeframe;
    return pairMatch && timeframeMatch;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gray-900 flex items-center justify-center gap-3">
            <BarChart3 className="h-10 w-10 text-blue-600" />
            Professional Trading Signals
          </h1>
          <p className="text-xl text-gray-600">Sistema Avançado de Sinais Forex, Cripto e Commodities</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Sinais Ativos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{activeSignals.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Força Média</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {activeSignals.length > 0 ? 
                  `${Math.round(activeSignals.reduce((acc, s) => acc + s.strength, 0) / activeSignals.length * 100)}%` : 
                  '0%'
                }
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Pares Monitorados</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">7</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Última Atualização</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-gray-500" />
                <span className="text-sm">{lastUpdate || 'Aguardando...'}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="signals" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="signals">Sinais Ativos</TabsTrigger>
            <TabsTrigger value="calculator">Calculadora</TabsTrigger>
            <TabsTrigger value="history">Histórico</TabsTrigger>
          </TabsList>

          <TabsContent value="signals" className="space-y-4">
            {/* Filters */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Filtros</CardTitle>
              </CardHeader>
              <CardContent className="flex gap-4">
                <div>
                  <label className="text-sm font-medium">Par:</label>
                  <select 
                    value={selectedPair} 
                    onChange={(e) => setSelectedPair(e.target.value)}
                    className="ml-2 border rounded px-2 py-1"
                  >
                    <option value="all">Todos</option>
                    <option value="EUR_USD">EUR/USD</option>
                    <option value="GBP_USD">GBP/USD</option>
                    <option value="USD_JPY">USD/JPY</option>
                    <option value="XAU_USD">XAU/USD</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Timeframe:</label>
                  <select 
                    value={selectedTimeframe} 
                    onChange={(e) => setSelectedTimeframe(e.target.value)}
                    className="ml-2 border rounded px-2 py-1"
                  >
                    <option value="all">Todos</option>
                    <option value="H1">H1</option>
                    <option value="H4">H4</option>
                    <option value="D1">D1</option>
                  </select>
                </div>
                <Button onClick={fetchSignals} disabled={isLoading} variant="outline">
                  {isLoading ? 'Atualizando...' : 'Atualizar'}
                </Button>
              </CardContent>
            </Card>

            {/* Active Signals */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {filteredSignals.map((signal) => {
                const positionSize = calculatePositionSize(signal);
                return (
                  <Card key={signal.id} className="shadow-lg">
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getSignalIcon(signal.direction)}
                          <span>{signal.pair.replace('_', '/')}</span>
                          <Badge className={getSignalColor(signal.direction)}>
                            {signal.direction}
                          </Badge>
                        </div>
                        <Badge variant="outline">{signal.timeframe}</Badge>
                      </CardTitle>
                      <CardDescription>
                        Força: {Math.round(signal.strength * 100)}% | {signal.reasons.join(', ')}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-sm font-medium text-gray-600">Entry</div>
                          <div className="text-lg font-bold">{signal.entry_price}</div>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-600">Stop Loss</div>
                          <div className="text-lg font-bold text-red-600">{signal.stop_loss}</div>
                        </div>
                      </div>

                      <Separator />

                      <div>
                        <div className="text-sm font-medium text-gray-600 mb-2">Take Profits</div>
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-sm">TP1:</span>
                            <span className="font-medium">{signal.take_profit_1} (R:R 1:{signal.risk_reward_1})</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm">TP2:</span>
                            <span className="font-medium">{signal.take_profit_2} (R:R 1:{signal.risk_reward_2})</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm">TP3:</span>
                            <span className="font-medium">{signal.take_profit_3} (R:R 1:{signal.risk_reward_3})</span>
                          </div>
                        </div>
                      </div>

                      <Separator />

                      <div>
                        <div className="text-sm font-medium text-gray-600 mb-2">Position Sizing ({riskPercent}% risk)</div>
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-sm">Lote:</span>
                            <span className="font-medium">{positionSize.lot_size}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm">Risco Máximo:</span>
                            <span className="font-medium text-red-600">${positionSize.max_loss}</span>
                          </div>
                        </div>
                      </div>

                      <Separator />

                      <div className="text-xs text-gray-500">
                        Gerado: {new Date(signal.timestamp).toLocaleString()}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {filteredSignals.length === 0 && (
              <Card>
                <CardContent className="text-center py-8">
                  <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600">Nenhum sinal ativo encontrado</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="calculator" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-5 w-5" />
                  Calculadora de Position Sizing
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Saldo da Conta (USD)</label>
                    <input
                      type="number"
                      value={accountBalance}
                      onChange={(e) => setAccountBalance(Number(e.target.value))}
                      className="w-full mt-1 border rounded px-3 py-2"
                      min="100"
                      step="100"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Risco (%)</label>
                    <input
                      type="number"
                      value={riskPercent}
                      onChange={(e) => setRiskPercent(Number(e.target.value))}
                      className="w-full mt-1 border rounded px-3 py-2"
                      min="0.1"
                      max="5"
                      step="0.1"
                    />
                  </div>
                </div>
                
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Cenários de Risco</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="font-medium">1% Risco</div>
                      <div>Risco: ${(accountBalance * 0.01).toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="font-medium">2% Risco</div>
                      <div>Risco: ${(accountBalance * 0.02).toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="font-medium">3% Risco</div>
                      <div>Risco: ${(accountBalance * 0.03).toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Histórico de Sinais</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {signalHistory.slice(0, 10).map((signal) => (
                    <div key={signal.id} className="flex items-center justify-between py-2 border-b">
                      <div className="flex items-center gap-3">
                        {getSignalIcon(signal.direction)}
                        <span className="font-medium">{signal.pair.replace('_', '/')}</span>
                        <Badge variant="outline">{signal.timeframe}</Badge>
                        <Badge className={getSignalColor(signal.direction)}>
                          {signal.direction}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-500">
                        {new Date(signal.timestamp).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
