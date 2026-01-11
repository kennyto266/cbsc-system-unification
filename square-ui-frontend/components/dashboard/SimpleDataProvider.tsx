'use client';

import React, { createContext, useContext, ReactNode, useState, useEffect } from 'react';

interface SimpleData {
  hibor?: any;
  monetaryBase?: any;
  exchangeRate?: any;
  marketRegime?: any;
}

interface SimpleDataContextType {
  data: SimpleData;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

const SimpleDataContext = createContext<SimpleDataContextType | undefined>(undefined);

export function SimpleDataProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<SimpleData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all data in parallel
      const [monetaryResponse, exchangeResponse, hiborResponse] = await Promise.all([
        fetch('/api/government/monetary-base?days=1'),
        fetch('/api/government/exchange-rate?days=1'),
        fetch('/api/government/hibor?days=1')
      ]);

      const newData: SimpleData = {};

      // Process monetary base data
      if (monetaryResponse.ok) {
        const monetaryData = await monetaryResponse.json();
        if (monetaryData.success) {
          newData.monetaryBase = monetaryData.latest;
        }
      }

      // Process exchange rate data
      if (exchangeResponse.ok) {
        const exchangeData = await exchangeResponse.json();
        if (exchangeData.success) {
          newData.exchangeRate = exchangeData.latest;
        }
      }

      // Process HIBOR data
      if (hiborResponse.ok) {
        const hiborData = await hiborResponse.json();
        if (hiborData.success) {
          newData.hibor = hiborData.latest;
        }
      }

      // Generate market regime (mock data)
      newData.marketRegime = {
        state: Math.random() > 0.5 ? 'BULL' : 'BEAR',
        confidence: (Math.random() * 30 + 70).toFixed(1),
        signal_strength: (Math.random() * 100).toFixed(1),
        last_updated: new Date().toISOString()
      };

      setData(newData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      console.error('SimpleDataProvider error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Set up periodic refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);

    return () => clearInterval(interval);
  }, []);

  const refresh = () => {
    fetchData();
  };

  const value: SimpleDataContextType = {
    data,
    loading,
    error,
    refresh
  };

  return (
    <SimpleDataContext.Provider value={value}>
      {children}
    </SimpleDataContext.Provider>
  );
}

export function useSimpleData() {
  const context = useContext(SimpleDataContext);
  if (!context) {
    throw new Error('useSimpleData must be used within SimpleDataProvider');
  }
  return context;
}