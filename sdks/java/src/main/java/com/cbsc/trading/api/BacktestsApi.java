package com.cbsc.trading.api;

import java.util.Map;

/**
 * Backtests API
 *
 * Handles backtest operations including creating, managing, and retrieving backtest results.
 */
public class BacktestsApi {
    private final CBSCApiClient client;

    public BacktestsApi(CBSCApiClient client) {
        this.client = client;
    }

    /**
     * Get list of backtest tasks
     */
    public ApiResponse getBacktests() throws ApiException {
        return client.get("/api/v1/tasks");
    }

    /**
     * Create a new backtest task
     */
    public ApiResponse createBacktest(Map<String, Object> backtest) throws ApiException {
        return client.post("/api/v1/tasks", backtest);
    }

    /**
     * Get backtest by ID
     */
    public ApiResponse getBacktest(String backtestId) throws ApiException {
        return client.get("/api/v1/tasks/" + backtestId);
    }

    /**
     * Delete a backtest task
     */
    public ApiResponse deleteBacktest(String backtestId) throws ApiException {
        return client.delete("/api/v1/tasks/" + backtestId);
    }

    /**
     * Cancel a running backtest task
     */
    public ApiResponse cancelBacktest(String backtestId) throws ApiException {
        return client.post("/api/v1/tasks/" + backtestId + "/cancel", null);
    }
}