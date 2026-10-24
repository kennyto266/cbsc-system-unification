package com.cbsc.trading.api;

import com.cbsc.trading.api.models.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * CBSC API Client Test
 *
 * Unit tests for the CBSC Trading Platform Java SDK
 */
public class CBSCApiClientTest {

    private CBSCApiClient client;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        client = new CBSCApiClient.Builder()
                .baseUrl("http://localhost:3005")
                .build();
    }

    @Test
    void testClientCreation() {
        assertNotNull(client);
        assertNotNull(client.getAuthApi());
        assertNotNull(client.getUsersApi());
        assertNotNull(client.getStrategiesApi());
        assertNotNull(client.getPortfoliosApi());
        assertNotNull(client.getMarketDataApi());
        assertNotNull(client.getBacktestsApi());
        assertNotNull(client.getWebhooksApi());
    }

    @Test
    void testTokenRequestCreation() {
        TokenRequest tokenRequest = new TokenRequest();
        tokenRequest.setGrantType(GrantType.CLIENT_CREDENTIALS);
        tokenRequest.setClientId("test_client_id");
        tokenRequest.setClientSecret("test_client_secret");
        tokenRequest.setScope("read write");

        assertEquals(GrantType.CLIENT_CREDENTIALS, tokenRequest.getGrantType());
        assertEquals("test_client_id", tokenRequest.getClientId());
        assertEquals("test_client_secret", tokenRequest.getClientSecret());
        assertEquals("read write", tokenRequest.getScope());
    }

    @Test
    void testUserCreateValidation() {
        UserCreate user = new UserCreate();
        user.setUsername("testuser");
        user.setEmail("test@example.com");
        user.setPassword("securepassword123");
        user.setFullName("Test User");
        user.setRole(UserRole.USER);

        assertEquals("testuser", user.getUsername());
        assertEquals("test@example.com", user.getEmail());
        assertEquals("securepassword123", user.getPassword());
        assertEquals("Test User", user.getFullName());
        assertEquals(UserRole.USER, user.getRole());
    }

    @Test
    void testUserLoginCreation() {
        UserLogin login = new UserLogin();
        login.setUsername("testuser");
        login.setPassword("password123");

        assertEquals("testuser", login.getUsername());
        assertEquals("password123", login.getPassword());
    }

    @Test
    void testGrantTypeEnum() {
        assertEquals(GrantType.CLIENT_CREDENTIALS, GrantType.fromValue("client_credentials"));
        assertEquals(GrantType.AUTHORIZATION_CODE, GrantType.fromValue("authorization_code"));
        assertEquals(GrantType.REFRESH_TOKEN, GrantType.fromValue("refresh_token"));

        assertThrows(IllegalArgumentException.class, () -> GrantType.fromValue("invalid"));
    }

    @Test
    void testUserRoleEnum() {
        assertEquals(UserRole.ADMIN, UserRole.fromValue("admin"));
        assertEquals(UserRole.DEVELOPER, UserRole.fromValue("developer"));
        assertEquals(UserRole.USER, UserRole.fromValue("user"));
        assertEquals(UserRole.READONLY, UserRole.fromValue("readonly"));

        assertThrows(IllegalArgumentException.class, () -> UserRole.fromValue("invalid"));
    }

    @Test
    void testTokenResponse() {
        TokenResponse response = new TokenResponse();
        response.setAccessToken("test_access_token");
        response.setRefreshToken("test_refresh_token");
        response.setTokenType("Bearer");
        response.setExpiresIn(3600);

        assertEquals("test_access_token", response.getAccessToken());
        assertEquals("test_refresh_token", response.getRefreshToken());
        assertEquals("Bearer", response.getTokenType());
        assertEquals(Integer.valueOf(3600), response.getExpiresIn());
    }

    @Test
    void testApiClientBuilder() {
        CBSCApiClient customClient = new CBSCApiClient.Builder()
                .baseUrl("https://api.custom.com")
                .timeout(java.time.Duration.ofSeconds(60))
                .maxRetries(5)
                .retryOnFailure(true)
                .userAgent("Custom-Agent/1.0")
                .build();

        assertNotNull(customClient);
        // Note: We can't directly test the builder properties since they're private
        // but we can test that the client was created successfully
    }

    @Test
    void testApiResponse() throws ApiException {
        String jsonBody = "{\"status\":\"success\",\"data\":{\"id\":\"123\"}}";
        ApiResponse response = new ApiResponse(200, jsonBody);

        assertEquals(200, response.getStatusCode());
        assertEquals(jsonBody, response.getBody());
        assertTrue(response.isSuccess());

        // Test parsing to a simple Map
        Map<String, Object> parsed = response.as(Map.class);
        assertNotNull(parsed);
        assertEquals("success", parsed.get("status"));
    }

    @Test
    void testApiException() {
        ApiException exception = new ApiException("Test error", 400, "Error details");

        assertEquals("Test error", exception.getMessage());
        assertEquals(400, exception.getStatusCode());
        assertEquals("Error details", exception.getResponseBody());
        assertTrue(exception.isClientError());
        assertFalse(exception.isServerError());
    }

    @Test
    void testApiExceptionServer() {
        ApiException exception = new ApiException("Server error", 500, null);

        assertEquals("Server error", exception.getMessage());
        assertEquals(500, exception.getStatusCode());
        assertFalse(exception.isClientError());
        assertTrue(exception.isServerError());
    }

    @Test
    void testTokenManagement() {
        CBSCApiClient testClient = new CBSCApiClient.Builder().build();

        assertNull(testClient.getAccessToken());
        assertNull(testClient.getRefreshToken());

        testClient.setTokens("test_access_token", "test_refresh_token");

        assertEquals("test_access_token", testClient.getAccessToken());
        assertEquals("test_refresh_token", testClient.getRefreshToken());
    }

    @Test
    void testRefreshTokenRequest() {
        RefreshTokenRequest request = new RefreshTokenRequest("test_refresh_token");

        assertEquals("test_refresh_token", request.getRefreshToken());

        RefreshTokenRequest request2 = new RefreshTokenRequest();
        request2.setRefreshToken("another_refresh_token");

        assertEquals("another_refresh_token", request2.getRefreshToken());
    }
}