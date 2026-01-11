package com.cbsc.trading.api.examples;

import com.cbsc.trading.api.CBSCApiClient;
import com.cbsc.trading.api.ApiException;
import com.cbsc.trading.api.models.*;

/**
 * Basic Usage Example
 *
 * Demonstrates basic usage of the CBSC Trading Platform Java SDK
 */
public class BasicUsageExample {

    public static void main(String[] args) {
        // Initialize the API client
        CBSCApiClient client = new CBSCApiClient.Builder()
                .baseUrl("http://localhost:3005") // Use local development server
                .build();

        try {
            // Example 1: Authenticate using client credentials
            System.out.println("=== Authentication Example ===");
            client.getAuthApi().authenticate("your_client_id", "your_client_secret");
            System.out.println("Authentication successful!");

            // Example 2: Get current user information
            System.out.println("\n=== User Information Example ===");
            UserResponse currentUser = client.getAuthApi().getCurrentUser();
            System.out.println("Current user: " + currentUser.getUsername());

            // Example 3: List users
            System.out.println("\n=== List Users Example ===");
            UserListResponse users = client.getUsersApi().getUsers();
            System.out.println("Total users: " + users.getTotal());

            // Example 4: Create a new user
            System.out.println("\n=== Create User Example ===");
            UserCreate newUser = new UserCreate();
            newUser.setUsername("testuser");
            newUser.setEmail("test@example.com");
            newUser.setPassword("securepassword123");
            newUser.setFullName("Test User");

            UserResponse createdUser = client.getUsersApi().createUser(newUser);
            System.out.println("Created user: " + createdUser.getUsername());

            // Example 5: Get market symbols
            System.out.println("\n=== Market Data Example ===");
            ApiResponse symbolsResponse = client.getMarketDataApi().getMarketSymbols();
            System.out.println("Market symbols status: " + symbolsResponse.getStatusCode());

            // Example 6: Get symbol quote
            System.out.println("\n=== Symbol Quote Example ===");
            ApiResponse quoteResponse = client.getMarketDataApi().getSymbolQuote("0700.HK");
            System.out.println("Symbol quote status: " + quoteResponse.getStatusCode());

            // Example 7: Create a backtest
            System.out.println("\n=== Backtest Example ===");
            java.util.Map<String, Object> backtestParams = java.util.Map.of(
                    "symbol", "0700.HK",
                    "strategy", java.util.Map.of("type", "RSI"),
                    "period", "1y"
            );

            ApiResponse backtestResponse = client.getBacktestsApi().createBacktest(backtestParams);
            System.out.println("Backtest creation status: " + backtestResponse.getStatusCode());

            // Example 8: Create a webhook
            System.out.println("\n=== Webhook Example ===");
            java.util.Map<String, Object> webhookConfig = java.util.Map.of(
                    "url", "https://example.com/webhook",
                    "events", java.util.List.of("strategy.created", "backtest.completed")
            );

            ApiResponse webhookResponse = client.getWebhooksApi().createWebhook(webhookConfig);
            System.out.println("Webhook creation status: " + webhookResponse.getStatusCode());

            System.out.println("\n=== All examples completed successfully! ===");

        } catch (ApiException e) {
            System.err.println("API Error: " + e.getMessage());
            System.err.println("Status Code: " + e.getStatusCode());
            if (e.getResponseBody() != null) {
                System.err.println("Response Body: " + e.getResponseBody());
            }
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
            e.printStackTrace();
        }
    }
}