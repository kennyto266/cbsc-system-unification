package com.cbsc.trading.api.models;

public class ApiUsageResponse {
    private String userId;
    private Long requestCount;
    private Long lastRequestTime;

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public Long getRequestCount() { return requestCount; }
    public void setRequestCount(Long requestCount) { this.requestCount = requestCount; }

    public Long getLastRequestTime() { return lastRequestTime; }
    public void setLastRequestTime(Long lastRequestTime) { this.lastRequestTime = lastRequestTime; }
}