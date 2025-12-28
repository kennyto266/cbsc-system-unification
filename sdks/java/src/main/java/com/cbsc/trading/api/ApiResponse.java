package com.cbsc.trading.api;

import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * API Response wrapper
 */
public class ApiResponse {
    private final int statusCode;
    private final String body;

    public ApiResponse(int statusCode, String body) {
        this.statusCode = statusCode;
        this.body = body;
    }

    public int getStatusCode() {
        return statusCode;
    }

    public String getBody() {
        return body;
    }

    public boolean isSuccess() {
        return statusCode >= 200 && statusCode < 300;
    }

    /**
     * Convert response body to specified type
     */
    public <T> T as(Class<T> type) throws ApiException {
        try {
            ObjectMapper mapper = new ObjectMapper();
            return mapper.readValue(body, type);
        } catch (Exception e) {
            throw new ApiException("Failed to parse response as " + type.getSimpleName(), e);
        }
    }

    @Override
    public String toString() {
        return "ApiResponse{" +
                "statusCode=" + statusCode +
                ", body='" + body + '\'' +
                '}';
    }
}