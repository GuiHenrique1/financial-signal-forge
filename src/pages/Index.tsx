import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { RefreshCw, TrendingUp, TrendingDown, DollarSign, Target, Shield, Clock, Activity } from "lucide-react";

interface Signal {
  id: string;
  pair: string;
  timeframe: string;
  direction: 'BUY' | 'SELL';
  strength: number;
  entry_price: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  take_profit_3: number;
  risk_reward_1: number;
  risk_reward_2: number;
  risk_reward_3: number;
  timestamp: string;
  reasons: string[];
  mtf_confirmation: boolean;
  mtf_confirmation_percentage: number;
  session: string;
  volatility_info: {
    atr_percentile: number;
    sufficient_volatility: boolean;
  };
}

interface PositionSizing {
  account_balance: number;
  risk_percent: number;
  lot_size: number;
  risk_amount: number;
  max_loss: number;
}

interface PerformanceMetrics {
  total_trades: number;
  win_rate: number;
  total_profit: number;
  profit_factor: number;
  max_drawdown: number;
}

const TradingSignalDashboard = () => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [activeSignals, setActiveSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [selectedPairs, setSelectedPairs] = useState<string[]>(['EUR_USD', 'GBP_USD', 'USD_JPY']);
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>(['H1', 'H4', 'D1']);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  
  // Position sizing calculator
  const [accountBalance, setAccountBalance] = useState<number>(10000);
  const [riskPercent, setRiskPercent] = useState<number>(1.0);
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [positionSizing, setPositionSizing] = useState<PositionSizing | null>(null);
  
  // Filters
  const [minSignalStrength, setMinSignalStrength] = useState<number>(60);
  const [requireMTFConfirmation, setRequireMTFConfirmation] = useState<boolean>(true);
  const [sessionFiltering, setSessionFiltering] = useState<boolean>(true);
  
  const { toast } = useToast();

  // Available pairs and timeframes
  const availablePairs = [
    'EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'NZD_USD', 'USD_CHF', 'USD_CAD',
    'EUR_JPY', 'GBP_JPY', 'AUD_JPY', 'NZD_JPY', 'CHF_JPY', 'CAD_JPY',
    'EUR_GBP', 'EUR_CHF', 'EUR_CAD', 'EUR_AUD', 'GBP_CHF', 'GBP_CAD',
    'XAU_USD', 'XAG_USD', 'WTICO_USD', 'BTC_USD', 'ETH_USD'
  ];
  
  const availableTimeframes = ['M15', 'M30', 'H1', 'H4', 'D1', 'W1'];

  // Demo data for development
  const generateDemoSignal = (): Signal => {
    const pairs = selectedPairs.length > 0 ? selectedPairs : ['EUR_USD', 'GBP_USD', 'USD_JPY'];
    const timeframes = selectedTimeframes.length > 0 ? selectedTimeframes : ['H1', 'H4', 'D1'];
    const directions: ('BUY' | 'SELL')[] = ['BUY', 'SELL'];
    
    const pair = pairs[Math.floor(Math.random() * pairs.length)];
    const timeframe = timeframes[Math.floor(Math.random() * timeframes.length)];
    const direction = directions[Math.floor(Math.random() * directions.length)];
    const strength = 60 + Math.random() * 40; // 60-100%
    
    const basePrice = pair.includes('JPY') ? 140 + Math.random() * 20 : 1.0 + Math.random() * 0.2;
    const pipValue = pair.includes('JPY') ? 0.01 : 0.0001;
    const spread = 10 + Math.random() * 20; // 10-30 pips
    
    const entry_price = basePrice;
    const stop_loss = direction === 'BUY' 
      ? entry_price - (spread * pipValue)
      : entry_price + (spread * pipValue);
    
    const risk = Math.abs(entry_price - stop_loss);
    const tp1 = direction === 'BUY' ? entry_price + risk : entry_price - risk;
    const tp2 = direction === 'BUY' ? entry_price + (risk * 2) : entry_price - (risk * 2);
    const tp3 = direction === 'BUY' ? entry_price + (risk * 3) : entry_price - (risk * 3);

    return {
      id: `signal_${Date.now()}_${Math.random()}`,
      pair,
      timeframe,
      direction,
      strength,
      entry_price,
      stop_loss,
      take_profit_1: tp1,
      take_profit_2: tp2,
      take_profit_3: tp3,
      risk_reward_1: 1.0,
      risk_reward_2: 2.0,
      risk_reward_3: 3.0,
      timestamp: new Date().toISOString(),
      reasons: [
        'RSI oversold recovery',
        'MACD bullish crossover',
        'Price above key support'
      ],
      mtf_confirmation: Math.random() > 0.3,
      mtf_confirmation_percentage: 60 + Math.random() * 40,
      session: 'london',
      volatility_info: {
        atr_percentile: 30 + Math.random() * 50,
        sufficient_volatility: true
      }
    };
  };

  const fetchSignals = async () => {
    setLoading(true);
    try {
      // For demo purposes, generate random signals (8-12 signals instead of 3-5)
      const newSignals = Array.from({ length: 8 + Math.floor(Math.random() * 5) }, generateDemoSignal);
      
      // Filter signals based on user preferences
      const filteredSignals = newSignals.filter(signal => {
        if (signal.strength < minSignalStrength) return false;
        if (requireMTFConfirmation && !signal.mtf_confirmation) return false;
        return true;
      });
      
      setSignals(filteredSignals);
      // Show ALL filtered signals instead of just the top 3
      setActiveSignals(filteredSignals);
      setConnectionStatus('connected');
      setLastUpdate(new Date());
      
      if (filteredSignals.length > 0) {
        toast({
          title: "Signals Updated",
          description: `Found ${filteredSignals.length} new signals`,
        });
      }
    } catch (error) {
      setConnectionStatus('error');
      toast({
        title: "Error",
        description: "Failed to fetch signals",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const calculatePositionSize = (signal: Signal) => {
    if (!signal) return;
    
    const riskAmount = (accountBalance * riskPercent) / 100;
    const pipDistance = Math.abs(signal.entry_price - signal.stop_loss);
    const pipValue = signal.pair.includes('JPY') ? 0.01 : 0.0001;
    const pips = pipDistance / pipValue;
    
    // Simplified lot calculation (would need proper pip value calculation per pair)
    const lotSize = riskAmount / (pips * 10); // Assuming $10 per pip per lot
    const maxLoss = lotSize * pips * 10;
    
    setPositionSizing({
      account_balance: accountBalance,
      risk_percent: riskPercent,
      lot_size: Math.round(lotSize * 100) / 100,
      risk_amount: riskAmount,
      max_loss: maxLoss
    });
  };

  useEffect(() => {
    fetchSignals();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchSignals, 30000);
    return () => clearInterval(interval);
  }, [selectedPairs, selectedTimeframes, minSignalStrength, requireMTFConfirmation]);

  useEffect(() => {
    if (selectedSignal) {
      calculatePositionSize(selectedSignal);
    }
  }, [selectedSignal, accountBalance, riskPercent]);

  // Generate demo performance metrics
  useEffect(() => {
    setPerformanceMetrics({
      total_trades: 147,
      win_rate: 68.5,
      total_profit: 3250.00,
      profit_factor: 1.85,
      max_drawdown: 450.00
    });
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getDirectionIcon = (direction: string) => {
    return direction === 'BUY' ? 
      <TrendingUp className="h-4 w-4 text-green-600" /> : 
      <TrendingDown className="h-4 w-4 text-red-600" />;
  };

  const getDirectionColor = (direction: string) => {
    return direction === 'BUY' ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50';
  };

  const formatPrice = (price: number, pair: string) => {
    const decimals = pair.includes('JPY') ? 3 : 5;
    return price.toFixed(decimals);
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Trading Signal Dashboard</h1>
            <p className="text-gray-600">Professional Forex, Crypto & Commodities Analysis</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(connectionStatus)}`}></div>
              <span className="text-sm text-gray-600">
                {connectionStatus === 'connected' ? 'Live' : 'Disconnected'}
              </span>
            </div>
            
            {lastUpdate && (
              <span className="text-sm text-gray-500">
                Last update: {formatTime(lastUpdate.toISOString())}
              </span>
            )}
            
            <Button
              onClick={fetchSignals}
              disabled={loading}
              variant="outline"
              size="sm"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Performance Overview */}
        {performanceMetrics && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Trades</p>
                    <p className="text-2xl font-bold">{performanceMetrics.total_trades}</p>
                  </div>
                  <Activity className="h-6 w-6 text-blue-600" />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Win Rate</p>
                    <p className="text-2xl font-bold text-green-600">{performanceMetrics.win_rate}%</p>
                  </div>
                  <Target className="h-6 w-6 text-green-600" />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Profit</p>
                    <p className="text-2xl font-bold text-green-600">${performanceMetrics.total_profit}</p>
                  </div>
                  <DollarSign className="h-6 w-6 text-green-600" />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Profit Factor</p>
                    <p className="text-2xl font-bold">{performanceMetrics.profit_factor}</p>
                  </div>
                  <TrendingUp className="h-6 w-6 text-blue-600" />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Max Drawdown</p>
                    <p className="text-2xl font-bold text-red-600">${performanceMetrics.max_drawdown}</p>
                  </div>
                  <Shield className="h-6 w-6 text-red-600" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <Tabs defaultValue="signals" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="signals">Active Signals</TabsTrigger>
            <TabsTrigger value="calculator">Position Calculator</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
          </TabsList>

          {/* Active Signals Tab */}
          <TabsContent value="signals" className="space-y-4">
            {activeSignals.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <p className="text-gray-500">No active signals at the moment</p>
                  <Button onClick={fetchSignals} className="mt-4">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Check for Signals
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div>
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Active Signals ({activeSignals.length})</h3>
                  <Badge variant="outline">
                    Showing all {activeSignals.length} signals
                  </Badge>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  {activeSignals.map((signal) => (
                    <Card key={signal.id} className="hover:shadow-lg transition-shadow">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg flex items-center gap-2">
                            {getDirectionIcon(signal.direction)}
                            {signal.pair.replace('_', '/')}
                          </CardTitle>
                          <Badge variant={signal.direction === 'BUY' ? 'default' : 'destructive'}>
                            {signal.direction}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">{signal.timeframe}</span>
                          <span className="text-gray-600">{formatTime(signal.timestamp)}</span>
                        </div>
                      </CardHeader>
                      
                      <CardContent className="space-y-4">
                        {/* Signal Strength */}
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Signal Strength</span>
                            <span className="font-semibold">{signal.strength.toFixed(0)}%</span>
                          </div>
                          <Progress value={signal.strength} className="h-2" />
                        </div>
                        
                        {/* MTF Confirmation */}
                        {signal.mtf_confirmation && (
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span>MTF Confirmation</span>
                              <span className="font-semibold">{signal.mtf_confirmation_percentage.toFixed(0)}%</span>
                            </div>
                            <Progress value={signal.mtf_confirmation_percentage} className="h-2" />
                          </div>
                        )}

                        {/* Price Levels */}
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Entry:</span>
                            <span className="font-mono font-semibold">{formatPrice(signal.entry_price, signal.pair)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Stop Loss:</span>
                            <span className="font-mono text-red-600">{formatPrice(signal.stop_loss, signal.pair)}</span>
                          </div>
                          <Separator />
                          <div className="flex justify-between">
                            <span className="text-gray-600">TP1 (1:1):</span>
                            <span className="font-mono text-green-600">{formatPrice(signal.take_profit_1, signal.pair)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">TP2 (1:2):</span>
                            <span className="font-mono text-green-600">{formatPrice(signal.take_profit_2, signal.pair)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">TP3 (1:3):</span>
                            <span className="font-mono text-green-600">{formatPrice(signal.take_profit_3, signal.pair)}</span>
                          </div>
                        </div>

                        {/* Signal Reasons */}
                        <div className="pt-2">
                          <p className="text-xs text-gray-600 mb-2">Analysis:</p>
                          <div className="flex flex-wrap gap-1">
                            {signal.reasons.slice(0, 2).map((reason, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {reason}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        {/* Action Button */}
                        <Button
                          onClick={() => setSelectedSignal(signal)}
                          className="w-full"
                          variant="outline"
                        >
                          Calculate Position Size
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          {/* Position Calculator Tab */}
          <TabsContent value="calculator" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Calculator Inputs */}
              <Card>
                <CardHeader>
                  <CardTitle>Position Size Calculator</CardTitle>
                  <CardDescription>
                    Calculate optimal position size based on your risk management rules
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="balance">Account Balance ($)</Label>
                      <Input
                        id="balance"
                        type="number"
                        value={accountBalance}
                        onChange={(e) => setAccountBalance(Number(e.target.value))}
                        placeholder="10000"
                      />
                    </div>
                    <div>
                      <Label htmlFor="risk">Risk Percentage (%)</Label>
                      <Input
                        id="risk"
                        type="number"
                        step="0.1"
                        min="0.1"
                        max="5"
                        value={riskPercent}
                        onChange={(e) => setRiskPercent(Number(e.target.value))}
                        placeholder="1.0"
                      />
                    </div>
                  </div>

                  <div>
                    <Label>Select Signal</Label>
                    <Select value={selectedSignal?.id || ''} onValueChange={(value) => {
                      const signal = activeSignals.find(s => s.id === value);
                      setSelectedSignal(signal || null);
                    }}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a signal to calculate position size" />
                      </SelectTrigger>
                      <SelectContent>
                        {activeSignals.map((signal) => (
                          <SelectItem key={signal.id} value={signal.id}>
                            {signal.pair.replace('_', '/')} {signal.direction} ({signal.timeframe})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              {/* Calculator Results */}
              <Card>
                <CardHeader>
                  <CardTitle>Position Sizing Results</CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedSignal && positionSizing ? (
                    <div className="space-y-4">
                      <Alert>
                        <Shield className="h-4 w-4" />
                        <AlertDescription>
                          <strong>{selectedSignal.pair.replace('_', '/')} {selectedSignal.direction}</strong>
                          <br />
                          Entry: {formatPrice(selectedSignal.entry_price, selectedSignal.pair)} | 
                          SL: {formatPrice(selectedSignal.stop_loss, selectedSignal.pair)}
                        </AlertDescription>
                      </Alert>

                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="p-3 bg-blue-50 rounded-lg">
                          <p className="text-blue-600 font-semibold">Recommended Lot Size</p>
                          <p className="text-2xl font-bold">{positionSizing.lot_size}</p>
                        </div>
                        <div className="p-3 bg-red-50 rounded-lg">
                          <p className="text-red-600 font-semibold">Maximum Risk</p>
                          <p className="text-2xl font-bold">${positionSizing.risk_amount.toFixed(2)}</p>
                        </div>
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Account Balance:</span>
                          <span className="font-semibold">${positionSizing.account_balance.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Risk Percentage:</span>
                          <span className="font-semibold">{positionSizing.risk_percent}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Max Loss:</span>
                          <span className="font-semibold text-red-600">${positionSizing.max_loss.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-8">
                      Select a signal and configure your account settings to calculate position size
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Asset Selection */}
              <Card>
                <CardHeader>
                  <CardTitle>Asset Selection</CardTitle>
                  <CardDescription>Choose which pairs and timeframes to monitor</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Trading Pairs</Label>
                    <div className="grid grid-cols-3 gap-2 mt-2">
                      {availablePairs.map((pair) => (
                        <label key={pair} className="flex items-center space-x-2 text-sm">
                          <input
                            type="checkbox"
                            checked={selectedPairs.includes(pair)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedPairs([...selectedPairs, pair]);
                              } else {
                                setSelectedPairs(selectedPairs.filter(p => p !== pair));
                              }
                            }}
                            className="rounded"
                          />
                          <span>{pair.replace('_', '/')}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <Label>Timeframes</Label>
                    <div className="grid grid-cols-3 gap-2 mt-2">
                      {availableTimeframes.map((tf) => (
                        <label key={tf} className="flex items-center space-x-2 text-sm">
                          <input
                            type="checkbox"
                            checked={selectedTimeframes.includes(tf)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedTimeframes([...selectedTimeframes, tf]);
                              } else {
                                setSelectedTimeframes(selectedTimeframes.filter(t => t !== tf));
                              }
                            }}
                            className="rounded"
                          />
                          <span>{tf}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Signal Filters */}
              <Card>
                <CardHeader>
                  <CardTitle>Signal Filters</CardTitle>
                  <CardDescription>Configure signal quality and confirmation requirements</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label>Minimum Signal Strength: {minSignalStrength}%</Label>
                    <input
                      type="range"
                      min="50"
                      max="90"
                      value={minSignalStrength}
                      onChange={(e) => setMinSignalStrength(Number(e.target.value))}
                      className="w-full mt-2"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Require MTF Confirmation</Label>
                      <p className="text-sm text-gray-600">Only show signals confirmed by higher timeframes</p>
                    </div>
                    <Switch
                      checked={requireMTFConfirmation}
                      onCheckedChange={setRequireMTFConfirmation}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Session Filtering</Label>
                      <p className="text-sm text-gray-600">Filter signals based on trading sessions</p>
                    </div>
                    <Switch
                      checked={sessionFiltering}
                      onCheckedChange={setSessionFiltering}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Performance Analytics</CardTitle>
                <CardDescription>Detailed trading performance analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-gray-500">Performance analytics will be available once you start trading with the signals.</p>
                  <p className="text-sm text-gray-400 mt-2">
                    This section will show win rates, profit factors, drawdown analysis, and more.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default TradingSignalDashboard;
