
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface TradingSignal {
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
  indicators?: {
    rsi: number;
    macd: number;
    macd_signal: number;
    macd_hist: number;
  };
}

export interface MarketData {
  pair: string;
  price: number;
  change_24h: number;
  volume: number;
  timestamp: string;
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  data_available: boolean;
  latest_data_age_minutes?: number;
  timestamp: number;
}

class ApiService {
  private async fetchWithTimeout(url: string, options: RequestInit = {}, timeout = 10000): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  async getSignals(): Promise<TradingSignal[]> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/signals`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return Array.isArray(data) ? data : data.signals || [];
    } catch (error) {
      console.error('Error fetching signals:', error);
      // Return mock data as fallback
      return this.getMockSignals();
    }
  }

  async getLatestSignal(): Promise<TradingSignal | null> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/signal`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.signal ? data : null;
    } catch (error) {
      console.error('Error fetching latest signal:', error);
      return null;
    }
  }

  async getMarketData(): Promise<MarketData[]> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/market-data`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching market data:', error);
      return this.getMockMarketData();
    }
  }

  async getSystemStatus(): Promise<SystemStatus> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching system status:', error);
      return {
        status: 'unhealthy',
        data_available: false,
        timestamp: Date.now()
      };
    }
  }

  async getProximitySignals(maxDistance: number = 15): Promise<TradingSignal[]> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/proximity-signals?max_distance=${maxDistance}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return Array.isArray(data) ? data : data.signals || [];
    } catch (error) {
      console.error('Error fetching proximity signals:', error);
      return this.getMockSignals().filter(s => (s.distance_pips || 0) <= maxDistance);
    }
  }

  private getMockSignals(): TradingSignal[] {
    return [
      {
        id: '1',
        pair: 'EUR_USD',
        timeframe: 'H1',
        direction: 'BUY',
        strength: 0.85,
        entry_price: 1.0950,
        current_price: 1.0945,
        stop_loss: 1.0920,
        take_profit_1: 1.0980,
        take_profit_2: 1.1010,
        take_profit_3: 1.1040,
        distance_pips: 5,
        proximity_score: 0.9,
        timestamp: new Date().toISOString(),
        reasons: ['RSI oversold recovery', 'MACD bullish crossover', 'Price above SMA'],
        indicators: {
          rsi: 35.2,
          macd: 0.0012,
          macd_signal: 0.0008,
          macd_hist: 0.0004
        }
      },
      {
        id: '2',
        pair: 'GBP_USD',
        timeframe: 'H4',
        direction: 'SELL',
        strength: 0.72,
        entry_price: 1.2650,
        current_price: 1.2655,
        stop_loss: 1.2680,
        take_profit_1: 1.2620,
        take_profit_2: 1.2590,
        take_profit_3: 1.2560,
        distance_pips: 5,
        proximity_score: 0.8,
        timestamp: new Date().toISOString(),
        reasons: ['RSI overbought decline', 'Bearish divergence'],
        indicators: {
          rsi: 72.8,
          macd: -0.0008,
          macd_signal: -0.0003,
          macd_hist: -0.0005
        }
      }
    ];
  }

  private getMockMarketData(): MarketData[] {
    return [
      {
        pair: 'EUR_USD',
        price: 1.0945,
        change_24h: 0.25,
        volume: 125000,
        timestamp: new Date().toISOString()
      },
      {
        pair: 'GBP_USD',
        price: 1.2655,
        change_24h: -0.15,
        volume: 98000,
        timestamp: new Date().toISOString()
      }
    ];
  }
}

export const apiService = new ApiService();
