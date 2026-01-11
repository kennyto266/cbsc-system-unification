package com.cbsc.trading.api;

import com.cbsc.trading.api.models.*;

import java.util.Map;

/**
 * Authentication API
 *
 * Handles user authentication, token management, and API key operations.
 */
public class AuthApi {
    private final CBSCApiClient client;

    public AuthApi(CBSCApiClient client) {
        this.client = client;
    }

    /**
     * Get access token using OAuth2 client credentials flow
     *
     * @param tokenRequest The token request with credentials
     * @return TokenResponse containing access and refresh tokens
     * @throws ApiException If authentication fails
     */
    public TokenResponse getToken(TokenRequest tokenRequest) throws ApiException {
        ApiResponse response = client.post("/api/v1/auth/token", tokenRequest);
        return response.as(TokenResponse.class);
    }

    /**
     * Refresh access token using refresh token
     *
     * @param refreshToken The refresh token
     * @return TokenResponse with new access token
     * @throws ApiException If refresh fails
     */
    public TokenResponse refreshToken(String refreshToken) throws ApiException {
        RefreshTokenRequest request = new RefreshTokenRequest(refreshToken);
        ApiResponse response = client.post("/api/v1/auth/refresh", request);
        return response.as(TokenResponse.class);
    }

    /**
     * User login with username and password
     *
     * @param login User login credentials
     * @return TokenResponse containing access and refresh tokens
     * @throws ApiException If login fails
     */
    public TokenResponse login(UserLogin login) throws ApiException {
        ApiResponse response = client.post("/api/v1/auth/login", login);
        return response.as(TokenResponse.class);
    }

    /**
     * Register a new user account
     *
     * @param user User creation details
     * @return UserResponse for the created user
     * @throws ApiException If registration fails
     */
    public UserResponse register(UserCreate user) throws ApiException {
        ApiResponse response = client.post("/api/v1/auth/register", user);
        return response.as(UserResponse.class);
    }

    /**
     * Get current authenticated user information
     *
     * @return UserResponse for the current user
     * @throws ApiException If request fails
     */
    public UserResponse getCurrentUser() throws ApiException {
        ApiResponse response = client.get("/api/v1/auth/me");
        return response.as(UserResponse.class);
    }

    /**
     * Logout current user (revoke tokens)
     *
     * @throws ApiException If logout fails
     */
    public void logout() throws ApiException {
        client.post("/api/v1/auth/logout", null);
    }

    /**
     * List API keys for current user
     *
     * @return List of API keys
     * @throws ApiException If request fails
     */
    public ApiKeyListResponse listApiKeys() throws ApiException {
        ApiResponse response = client.get("/api/v1/auth/api-keys");
        return response.as(ApiKeyListResponse.class);
    }

    /**
     * Create a new API key
     *
     * @param request API key creation request
     * @return ApiKeyResponse for the created key
     * @throws ApiException If creation fails
     */
    public ApiKeyResponse createApiKey(Map<String, Object> request) throws ApiException {
        ApiResponse response = client.post("/api/v1/auth/api-keys", request);
        return response.as(ApiKeyResponse.class);
    }

    /**
     * Convenience method to authenticate and set tokens on client
     *
     * @param clientId OAuth2 client ID
     * @param clientSecret OAuth2 client secret
     * @throws ApiException If authentication fails
     */
    public void authenticate(String clientId, String clientSecret) throws ApiException {
        TokenRequest tokenRequest = new TokenRequest(
                GrantType.CLIENT_CREDENTIALS,
                clientId,
                clientSecret
        );

        TokenResponse tokenResponse = getToken(tokenRequest);
        client.setTokens(tokenResponse.getAccessToken(), tokenResponse.getRefreshToken());
    }
}