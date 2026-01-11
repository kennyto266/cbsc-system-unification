package com.cbsc.trading.api;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.JSR310Module;
import okhttp3.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * CBSC Trading Platform API Client
 *
 * Main client class for interacting with the CBSC Trading Platform REST API.
 * Provides authentication, HTTP request handling, and error management.
 */
public class CBSCApiClient {
    private static final Logger logger = LoggerFactory.getLogger(CBSCApiClient.class);

    private final String baseUrl;
    private final OkHttpClient httpClient;
    private final ObjectMapper objectMapper;
    private String accessToken;
    private String refreshToken;

    // API Resource instances
    private final AuthApi authApi;
    private final UsersApi usersApi;
    private final StrategiesApi strategiesApi;
    private final PortfoliosApi portfoliosApi;
    private final MarketDataApi marketDataApi;
    private final BacktestsApi backtestsApi;
    private final WebhooksApi webhooksApi;

    /**
     * Builder for CBSCApiClient
     */
    public static class Builder {
        private String baseUrl = "https://api.cbsc.com";
        private Duration timeout = Duration.ofSeconds(30);
        private boolean retryOnFailure = true;
        private int maxRetries = 3;
        private String userAgent = "CBSC-Java-SDK/1.0.0";

        public Builder baseUrl(String baseUrl) {
            this.baseUrl = baseUrl;
            return this;
        }

        public Builder timeout(Duration timeout) {
            this.timeout = timeout;
            return this;
        }

        public Builder retryOnFailure(boolean retryOnFailure) {
            this.retryOnFailure = retryOnFailure;
            return this;
        }

        public Builder maxRetries(int maxRetries) {
            this.maxRetries = maxRetries;
            return this;
        }

        public Builder userAgent(String userAgent) {
            this.userAgent = userAgent;
            return this;
        }

        public CBSCApiClient build() {
            return new CBSCApiClient(this);
        }
    }

    private CBSCApiClient(Builder builder) {
        this.baseUrl = builder.baseUrl;

        // Configure ObjectMapper
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JSR310Module());
        this.objectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        this.objectMapper.configure(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS, false);
        this.objectMapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);

        // Configure OkHttpClient
        OkHttpClient.Builder clientBuilder = new OkHttpClient.Builder()
                .connectTimeout(builder.timeout)
                .readTimeout(builder.timeout)
                .writeTimeout(builder.timeout)
                .addInterceptor(new AuthInterceptor())
                .addInterceptor(new UserAgentInterceptor(builder.userAgent));

        if (builder.retryOnFailure) {
            clientBuilder.addInterceptor(new RetryInterceptor(builder.maxRetries));
        }

        this.httpClient = clientBuilder.build();

        // Initialize API resource instances
        this.authApi = new AuthApi(this);
        this.usersApi = new UsersApi(this);
        this.strategiesApi = new StrategiesApi(this);
        this.portfoliosApi = new PortfoliosApi(this);
        this.marketDataApi = new MarketDataApi(this);
        this.backtestsApi = new BacktestsApi(this);
        this.webhooksApi = new WebhooksApi(this);
    }

    /**
     * Execute HTTP GET request
     */
    public ApiResponse get(String path) throws ApiException {
        return execute(path, "GET", null, null);
    }

    /**
     * Execute HTTP GET request with query parameters
     */
    public ApiResponse get(String path, Map<String, String> queryParams) throws ApiException {
        return execute(path, "GET", null, queryParams);
    }

    /**
     * Execute HTTP POST request
     */
    public ApiResponse post(String path, Object body) throws ApiException {
        return execute(path, "POST", body, null);
    }

    /**
     * Execute HTTP PUT request
     */
    public ApiResponse put(String path, Object body) throws ApiException {
        return execute(path, "PUT", body, null);
    }

    /**
     * Execute HTTP DELETE request
     */
    public ApiResponse delete(String path) throws ApiException {
        return execute(path, "DELETE", null, null);
    }

    /**
     * Execute HTTP request
     */
    private ApiResponse execute(String path, String method, Object body, Map<String, String> queryParams)
            throws ApiException {
        try {
            String url = baseUrl + path;

            // Add query parameters
            if (queryParams != null && !queryParams.isEmpty()) {
                HttpUrl.Builder urlBuilder = HttpUrl.parse(url).newBuilder();
                queryParams.forEach(urlBuilder::addQueryParameter);
                url = urlBuilder.build().toString();
            }

            // Build request
            Request.Builder requestBuilder = new Request.Builder()
                    .url(url);

            // Add request body if present
            RequestBody requestBody = null;
            if (body != null) {
                String jsonBody = objectMapper.writeValueAsString(body);
                requestBody = RequestBody.create(
                        jsonBody,
                        MediaType.get("application/json; charset=utf-8")
                );
            }

            // Set method and body
            switch (method.toUpperCase()) {
                case "GET":
                    requestBuilder.get();
                    break;
                case "POST":
                    requestBuilder.post(requestBody != null ? requestBody :
                            RequestBody.create("", MediaType.get("application/json")));
                    break;
                case "PUT":
                    requestBuilder.put(requestBody != null ? requestBody :
                            RequestBody.create("", MediaType.get("application/json")));
                    break;
                case "DELETE":
                    requestBuilder.delete(requestBody);
                    break;
                default:
                    throw new ApiException("Unsupported HTTP method: " + method);
            }

            Request request = requestBuilder.build();

            logger.debug("Executing {} request to {}", method, url);

            try (Response response = httpClient.newCall(request).execute()) {
                String responseBody = response.body() != null ? response.body().string() : "";

                if (!response.isSuccessful()) {
                    throw new ApiException(
                            "HTTP " + response.code() + ": " + response.message(),
                            response.code(),
                            responseBody
                    );
                }

                return new ApiResponse(response.code(), responseBody);
            }

        } catch (JsonProcessingException e) {
            throw new ApiException("Failed to serialize request body", e);
        } catch (IOException e) {
            throw new ApiException("Network error: " + e.getMessage(), e);
        }
    }

    /**
     * Set authentication tokens
     */
    public void setTokens(String accessToken, String refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        logger.debug("Authentication tokens updated");
    }

    /**
     * Get current access token
     */
    public String getAccessToken() {
        return accessToken;
    }

    /**
     * Get current refresh token
     */
    public String getRefreshToken() {
        return refreshToken;
    }

    /**
     * Get object mapper for custom serialization needs
     */
    public ObjectMapper getObjectMapper() {
        return objectMapper;
    }

    // API Resource getters
    public AuthApi getAuthApi() {
        return authApi;
    }

    public UsersApi getUsersApi() {
        return usersApi;
    }

    public StrategiesApi getStrategiesApi() {
        return strategiesApi;
    }

    public PortfoliosApi getPortfoliosApi() {
        return portfoliosApi;
    }

    public MarketDataApi getMarketDataApi() {
        return marketDataApi;
    }

    public BacktestsApi getBacktestsApi() {
        return backtestsApi;
    }

    public WebhooksApi getWebhooksApi() {
        return webhooksApi;
    }

    /**
     * Authentication interceptor
     */
    private class AuthInterceptor implements Interceptor {
        @Override
        public Response intercept(Chain chain) throws IOException {
            Request originalRequest = chain.request();

            if (accessToken != null) {
                Request authenticatedRequest = originalRequest.newBuilder()
                        .header("Authorization", "Bearer " + accessToken)
                        .build();
                return chain.proceed(authenticatedRequest);
            }

            return chain.proceed(originalRequest);
        }
    }

    /**
     * User agent interceptor
     */
    private static class UserAgentInterceptor implements Interceptor {
        private final String userAgent;

        public UserAgentInterceptor(String userAgent) {
            this.userAgent = userAgent;
        }

        @Override
        public Response intercept(Chain chain) throws IOException {
            Request originalRequest = chain.request();
            Request requestWithUserAgent = originalRequest.newBuilder()
                    .header("User-Agent", userAgent)
                    .build();
            return chain.proceed(requestWithUserAgent);
        }
    }

    /**
     * Retry interceptor
     */
    private static class RetryInterceptor implements Interceptor {
        private final int maxRetries;

        public RetryInterceptor(int maxRetries) {
            this.maxRetries = maxRetries;
        }

        @Override
        public Response intercept(Chain chain) throws IOException {
            Request request = chain.request();
            Response response = null;
            IOException lastException = null;

            for (int attempt = 0; attempt <= maxRetries; attempt++) {
                try {
                    response = chain.proceed(request);
                    if (response.isSuccessful() || attempt == maxRetries) {
                        return response;
                    }

                    // Don't retry client errors (4xx)
                    if (response.code() >= 400 && response.code() < 500) {
                        return response;
                    }

                    response.close();

                    // Exponential backoff
                    Thread.sleep((long) Math.pow(2, attempt) * 1000);

                } catch (IOException | InterruptedException e) {
                    lastException = (IOException) e;
                    if (attempt == maxRetries) {
                        break;
                    }
                    try {
                        Thread.sleep((long) Math.pow(2, attempt) * 1000);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new IOException("Request interrupted", ie);
                    }
                }
            }

            throw lastException != null ? lastException : new IOException("Max retries exceeded");
        }
    }
}