package com.cbsc.trading.api;

import java.util.Map;

/**
 * Strategies API
 *
 * Handles trading strategy management operations including CRUD operations and backtesting.
 */
public class StrategiesApi {
    private final CBSCApiClient client;

    public StrategiesApi(CBSCApiClient client) {
        this.client = client;
    }

    /**
     * Get list of available trading strategies
     *
     * @return StrategyListResponse containing available strategies
     * @throws ApiException If request fails
     */
    public StrategyListResponse getStrategies() throws ApiException {
        ApiResponse response = client.get("/api/v1/strategies");
        return response.as(StrategyListResponse.class);
    }

    /**
     * Get strategy by ID
     *
     * @param strategyId The strategy ID
     * @return StrategyResponse with strategy details
     * @throws ApiException If strategy not found or request fails
     */
    public StrategyResponse getStrategy(String strategyId) throws ApiException {
        String path = "/api/v1/strategies/" + strategyId;
        ApiResponse response = client.get(path);
        return response.as(StrategyResponse.class);
    }

    /**
     * Create a new trading strategy
     *
     * @param strategy Strategy creation details
     * @return StrategyResponse for the created strategy
     * @throws ApiException If creation fails
     */
    public StrategyResponse createStrategy(Map<String, Object> strategy) throws ApiException {
        ApiResponse response = client.post("/api/v1/strategies", strategy);
        return response.as(StrategyResponse.class);
    }

    /**
     * Update trading strategy
     *
     * @param strategyId The strategy ID
     * @param updates Map of fields to update
     * @return StrategyResponse with updated strategy information
     * @throws ApiException If update fails
     */
    public StrategyResponse updateStrategy(String strategyId, Map<String, Object> updates) throws ApiException {
        String path = "/api/v1/strategies/" + strategyId;
        ApiResponse response = client.put(path, updates);
        return response.as(StrategyResponse.class);
    }

    /**
     * Delete a trading strategy
     *
     * @param strategyId The strategy ID
     * @throws ApiException If deletion fails
     */
    public void deleteStrategy(String strategyId) throws ApiException {
        String path = "/api/v1/strategies/" + strategyId;
        client.delete(path);
    }

    /**
     * Backtest a trading strategy
     *
     * @param strategyId The strategy ID
     * @param backtestRequest Backtest parameters
     * @return BacktestResponse with backtest results
     * @throws ApiException If backtest fails
     */
    public BacktestResponse backtestStrategy(String strategyId, Map<String, Object> backtestRequest) throws ApiException {
        String path = "/api/v1/strategies/" + strategyId + "/backtest";
        ApiResponse response = client.post(path, backtestRequest);
        return response.as(BacktestResponse.class);
    }

    /**
     * Get strategy performance metrics
     *
     * @param strategyId The strategy ID
     * @return StrategyPerformanceResponse with performance metrics
     * @throws ApiException If request fails
     */
    public StrategyPerformanceResponse getStrategyPerformance(String strategyId) throws ApiException {
        String path = "/api/v1/strategies/" + strategyId + "/performance";
        ApiResponse response = client.get(path);
        return response.as(StrategyPerformanceResponse.class);
    }
}