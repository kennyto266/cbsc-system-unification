package com.cbsc.trading.api;

import java.util.Map;

/**
 * Market Data API
 *
 * Handles market data operations including symbol information, quotes, and historical data.
 */
public class MarketDataApi {
    private final CBSCApiClient client;

    public MarketDataApi(CBSCApiClient client) {
        this.client = client;
    }

    /**
     * Get market symbols list
     */
    public ApiResponse getMarketSymbols() throws ApiException {
        return client.get("/api/v1/market/symbols");
    }

    /**
     * Get symbol details
     */
    public ApiResponse getSymbolDetail(String symbol) throws ApiException {
        return client.get("/api/v1/market/symbols/" + symbol);
    }

    /**
     * Get symbol data
     */
    public ApiResponse getSymbolData(String symbol, String period, String interval) throws ApiException {
        Map<String, String> params = Map.of(
                "period", period != null ? period : "1mo",
                "interval", interval != null ? interval : "1d"
        );
        return client.get("/api/v1/market/symbols/" + symbol + "/data", params);
    }

    /**
     * Get symbol quote
     */
    public ApiResponse getSymbolQuote(String symbol) throws ApiException {
        return client.get("/api/v1/market/symbols/" + symbol + "/quote");
    }
}