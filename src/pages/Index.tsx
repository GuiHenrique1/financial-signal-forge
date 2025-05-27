
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Settings,
  Wifi,
  WifiOff,
  Target,
  AlertCircle,
  CheckCircle,
  Zap
} from "lucide-react";
import SignalsTable from "@/components/SignalsTable";
import { useSignals, useProximitySignals, useMarketData, useSystemStatus } from "@/hooks/useSignals";
import { useToast } from "@/hooks/use-toast";

const Index = () => {
  const [proximityDistance, setProximityDistance] = useState(15);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const { toast } = useToast();

  // React Query hooks para dados reais
  const { data: allSignals, isLoading: signalsLoading, error: signalsError } = useSignals();
  const { data: proximitySignals, isLoading: proximityLoading } = useProximitySignals(proximityDistance);
  const { data: marketData, isLoading: marketLoading } = useMarketData();
  const { data: systemStatus } = useSystemStatus();

  const handleCopySignal = (signal: any) => {
    const signalText = `
${signal.direction} ${signal.pair.replace('_', '/')}
Entry: ${signal.entry_price}
SL: ${signal.stop_loss}
TP1: ${signal.take_profit_1}
TP2: ${signal.take_profit_2}
TP3: ${signal.take_profit_3}
Strength: ${Math.round(signal.strength * 100)}%
Distance: ${signal.distance_pips} pips
    `.trim();

    navigator.clipboard.writeText(signalText);
    toast({
      title: "Sinal copiado!",
      description: "O sinal foi copiado para a área de transferência",
    });
  };

  const getStatusColor = () => {
    if (!systemStatus) return 'bg-gray-500';
    switch (systemStatus.status) {
      case 'healthy': return 'bg-green-500';
      case 'degraded': return 'bg-yellow-500';
      case 'unhealthy': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = () => {
    if (!systemStatus) return <AlertCircle className="w-4 h-4" />;
    switch (systemStatus.status) {
      case 'healthy': return <CheckCircle className="w-4 h-4" />;
      case 'degraded': return <AlertCircle className="w-4 h-4" />;
      case 'unhealthy': return <WifiOff className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header com Status */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Trading Signals Pro</h1>
            <p className="text-gray-600">Sinais de trading filtrados por proximidade em tempo real</p>
          </div>
          
          <div className="flex items-center gap-4">
            <Badge className={`${getStatusColor()} text-white flex items-center gap-2`}>
              {getStatusIcon()}
              {systemStatus?.status || 'Connecting...'}
            </Badge>
            
            {autoRefresh && (
              <Badge variant="outline" className="flex items-center gap-1">
                <Wifi className="w-3 h-3" />
                Live
              </Badge>
            )}
          </div>
        </div>

        {/* Alertas de Sistema */}
        {signalsError && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Conexão com servidor offline. Usando dados de exemplo.
            </AlertDescription>
          </Alert>
        )}

        {/* Estatísticas Rápidas */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Sinais Ativos</p>
                  <p className="text-2xl font-bold">{allSignals?.length || 0}</p>
                </div>
                <Activity className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Sinais Próximos</p>
                  <p className="text-2xl font-bold text-green-600">{proximitySignals?.length || 0}</p>
                </div>
                <Target className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Pares Monitorados</p>
                  <p className="text-2xl font-bold">{marketData?.length || 0}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Última Atualização</p>
                  <p className="text-sm font-medium">
                    {systemStatus?.latest_data_age_minutes 
                      ? `${systemStatus.latest_data_age_minutes.toFixed(1)}m atrás`
                      : 'Conectando...'
                    }
                  </p>
                </div>
                <Zap className="w-8 h-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Configurações de Filtro */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Configurações do Filtro de Proximidade
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="proximity">Distância Máxima (pips)</Label>
                <Input
                  id="proximity"
                  type="number"
                  value={proximityDistance}
                  onChange={(e) => setProximityDistance(Number(e.target.value))}
                  min="1"
                  max="100"
                />
              </div>
              
              <div className="flex items-center space-x-2 pt-6">
                <Switch
                  id="auto-refresh"
                  checked={autoRefresh}
                  onCheckedChange={setAutoRefresh}
                />
                <Label htmlFor="auto-refresh">Atualização Automática</Label>
              </div>
              
              <div className="pt-6">
                <Button 
                  onClick={() => window.location.reload()} 
                  variant="outline"
                  className="w-full"
                >
                  Atualizar Agora
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabs de Conteúdo */}
        <Tabs defaultValue="proximity" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="proximity">Sinais por Proximidade</TabsTrigger>
            <TabsTrigger value="all">Todos os Sinais</TabsTrigger>
            <TabsTrigger value="market">Dados de Mercado</TabsTrigger>
          </TabsList>

          <TabsContent value="proximity" className="space-y-4">
            {proximityLoading ? (
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Carregando sinais próximos...</p>
                </CardContent>
              </Card>
            ) : (
              <SignalsTable 
                signals={proximitySignals || []} 
                onCopySignal={handleCopySignal}
              />
            )}
          </TabsContent>

          <TabsContent value="all" className="space-y-4">
            {signalsLoading ? (
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Carregando todos os sinais...</p>
                </CardContent>
              </Card>
            ) : (
              <SignalsTable 
                signals={allSignals || []} 
                onCopySignal={handleCopySignal}
              />
            )}
          </TabsContent>

          <TabsContent value="market" className="space-y-4">
            {marketLoading ? (
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Carregando dados de mercado...</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {marketData?.map((market) => (
                  <Card key={market.pair}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="font-semibold">{market.pair.replace('_', '/')}</h3>
                          <p className="text-2xl font-bold">{market.price}</p>
                        </div>
                        <div className="text-right">
                          <Badge className={market.change_24h >= 0 ? 'bg-green-500' : 'bg-red-500'}>
                            {market.change_24h >= 0 ? '+' : ''}{market.change_24h}%
                          </Badge>
                          <p className="text-sm text-gray-600 mt-1">
                            Vol: {market.volume.toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
