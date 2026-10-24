package com.cbsc.trading.api;

import java.util.Map;

/**
 * Portfolios API
 *
 * Handles portfolio management operations including CRUD operations and holdings management.
 */
public class PortfoliosApi {
    private final CBSCApiClient client;

    public PortfoliosApi(CBSCApiClient client) {
        this.client = client;
    }

    /**
     * Get list of portfolios
     *
     * @return PortfolioListResponse containing portfolios
     * @throws ApiException If request fails
     */
    public PortfolioListResponse getPortfolios() throws ApiException {
        ApiResponse response = client.get("/api/v1/portfolios");
        return response.as(PortfolioListResponse.class);
    }

    /**
     * Get portfolio by ID
     *
     * @param portfolioId The portfolio ID
     * @return PortfolioResponse with portfolio details
     * @throws ApiException If portfolio not found or request fails
     */
    public PortfolioResponse getPortfolio(String portfolioId) throws ApiException {
        String path = "/api/v1/portfolios/" + portfolioId;
        ApiResponse response = client.get(path);
        return response.as(PortfolioResponse.class);
    }

    /**
     * Create a new portfolio
     *
     * @param portfolio Portfolio creation details
     * @return PortfolioResponse for the created portfolio
     * @throws ApiException If creation fails
     */
    public PortfolioResponse createPortfolio(Map<String, Object> portfolio) throws ApiException {
        ApiResponse response = client.post("/api/v1/portfolios", portfolio);
        return response.as(PortfolioResponse.class);
    }

    /**
     * Update portfolio
     *
     * @param portfolioId The portfolio ID
     * @param updates Map of fields to update
     * @return PortfolioResponse with updated portfolio information
     * @throws ApiException If update fails
     */
    public PortfolioResponse updatePortfolio(String portfolioId, Map<String, Object> updates) throws ApiException {
        String path = "/api/v1/portfolios/" + portfolioId;
        ApiResponse response = client.put(path, updates);
        return response.as(PortfolioResponse.class);
    }

    /**
     * Delete a portfolio
     *
     * @param portfolioId The portfolio ID
     * @throws ApiException If deletion fails
     */
    public void deletePortfolio(String portfolioId) throws ApiException {
        String path = "/api/v1/portfolios/" + portfolioId;
        client.delete(path);
    }

    /**
     * Add holding to portfolio
     *
     * @param portfolioId The portfolio ID
     * @param holding Holding details
     * @return PortfolioResponse with updated portfolio information
     * @throws ApiException If addition fails
     */
    public PortfolioResponse addHolding(String portfolioId, Map<String, Object> holding) throws ApiException {
        String path = "/api/v1/portfolios/" + portfolioId + "/holdings";
        ApiResponse response = client.post(path, holding);
        return response.as(PortfolioResponse.class);
    }

    /**
     * Remove holding from portfolio
     *
     * @param portfolioId The portfolio ID
     * @param symbol The symbol to remove
     * @return PortfolioResponse with updated portfolio information
     * @throws ApiException If removal fails
     */
    public PortfolioResponse removeHolding(String portfolioId, String symbol) throws ApiException {
        String path = "/api/v1/portfolios/" + portfolioId + "/holdings/" + symbol;
        ApiResponse response = client.delete(path);
        return response.as(PortfolioResponse.class);
    }
}