package com.cbsc.trading.api;

import java.util.Map;

/**
 * Webhooks API
 *
 * Handles webhook management operations including CRUD operations and event delivery.
 */
public class WebhooksApi {
    private final CBSCApiClient client;

    public WebhooksApi(CBSCApiClient client) {
        this.client = client;
    }

    /**
     * Get list of webhooks
     */
    public ApiResponse getWebhooks() throws ApiException {
        return client.get("/api/v1/webhooks");
    }

    /**
     * Create a new webhook
     */
    public ApiResponse createWebhook(Map<String, Object> webhook) throws ApiException {
        return client.post("/api/v1/webhooks", webhook);
    }

    /**
     * Get webhook by ID
     */
    public ApiResponse getWebhook(String webhookId) throws ApiException {
        return client.get("/api/v1/webhooks/" + webhookId);
    }

    /**
     * Update webhook
     */
    public ApiResponse updateWebhook(String webhookId, Map<String, Object> updates) throws ApiException {
        return client.put("/api/v1/webhooks/" + webhookId, updates);
    }

    /**
     * Delete webhook
     */
    public ApiResponse deleteWebhook(String webhookId) throws ApiException {
        return client.delete("/api/v1/webhooks/" + webhookId);
    }

    /**
     * Test webhook
     */
    public ApiResponse testWebhook(String webhookId) throws ApiException {
        return client.post("/api/v1/webhooks/" + webhookId + "/test", null);
    }
}