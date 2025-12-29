# CBSC Trading Platform Java SDK

A comprehensive Java SDK for interacting with the CBSC Trading Platform REST API.

## Features

- **Authentication**: OAuth2 client credentials flow, JWT token management
- **Complete API Coverage**: All platform services accessible via typed API clients
- **Error Handling**: Comprehensive error management with detailed error information
- **Type Safety**: Full Java type support for requests and responses
- **Retry Logic**: Built-in retry mechanisms with exponential backoff
- **Logging**: Integrated logging support
- **Easy Configuration**: Builder pattern for client configuration

## Requirements

- Java 11 or higher
- Maven 3.6 or higher

## Installation

Add the SDK to your Maven project:

```xml
<dependency>
    <groupId>com.cbsc.trading</groupId>
    <artifactId>cbsc-trading-api</artifactId>
    <version>1.0.0</version>
</dependency>
```

## Quick Start

### 1. Initialize the Client

```java
import com.cbsc.trading.api.CBSCApiClient;
import com.cbsc.trading.api.models.*;

// Create API client
CBSCApiClient client = new CBSCApiClient.Builder()
    .baseUrl("https://api.cbsc.com")
    .build();
```

### 2. Authenticate

```java
// Authenticate using client credentials
client.getAuthApi().authenticate("your_client_id", "your_client_secret");

// Or authenticate manually
TokenRequest tokenRequest = new TokenRequest(
    GrantType.CLIENT_CREDENTIALS,
    "your_client_id",
    "your_client_secret"
);
TokenResponse tokenResponse = client.getAuthApi().getToken(tokenRequest);
client.setTokens(tokenResponse.getAccessToken(), tokenResponse.getRefreshToken());
```

### 3. Make API Calls

```java
// Get current user
UserResponse currentUser = client.getAuthApi().getCurrentUser();
System.out.println("Current user: " + currentUser.getUsername());

// List users
UserListResponse users = client.getUsersApi().getUsers();
System.out.println("Total users: " + users.getTotal());

// Get market data
ApiResponse symbols = client.getMarketDataApi().getMarketSymbols();
System.out.println("Market symbols status: " + symbols.getStatusCode());

// Create a backtest
Map<String, Object> backtestParams = Map.of(
    "symbol", "0700.HK",
    "strategy", Map.of("type", "RSI"),
    "period", "1y"
);
ApiResponse backtest = client.getBacktestsApi().createBacktest(backtestParams);
```

## API Resources

The SDK provides typed clients for all API resources:

- **AuthApi**: Authentication, token management, API keys
- **UsersApi**: User management operations
- **StrategiesApi**: Trading strategy management
- **PortfoliosApi**: Portfolio and holdings management
- **MarketDataApi**: Market data and quotes
- **BacktestsApi**: Backtest operations and results
- **WebhooksApi**: Webhook management

## Error Handling

The SDK provides comprehensive error handling:

```java
try {
    UserResponse user = client.getUsersApi().getUser("user_id");
} catch (ApiException e) {
    System.err.println("API Error: " + e.getMessage());
    System.err.println("Status Code: " + e.getStatusCode());

    if (e.isClientError()) {
        // Handle 4xx errors (client errors)
    } else if (e.isServerError()) {
        // Handle 5xx errors (server errors)
    }

    if (e.getResponseBody() != null) {
        System.err.println("Error details: " + e.getResponseBody());
    }
}
```

## Configuration Options

The client builder supports various configuration options:

```java
CBSCApiClient client = new CBSCApiClient.Builder()
    .baseUrl("https://api.cbsc.com")                    // API base URL
    .timeout(Duration.ofSeconds(30))                    // Request timeout
    .retryOnFailure(true)                              // Enable retry logic
    .maxRetries(3)                                     // Maximum retry attempts
    .userAgent("MyApp/1.0")                           // Custom user agent
    .build();
```

## Models

The SDK includes typed models for all API requests and responses:

### Authentication Models
- `TokenRequest`: OAuth2 token request
- `TokenResponse`: OAuth2 token response
- `UserLogin`: User login credentials
- `UserCreate`: User creation details

### User Models
- `UserResponse`: User information
- `UserRole`: User role enumeration (ADMIN, DEVELOPER, USER, READONLY)

### Common Models
- `GrantType`: OAuth2 grant type enumeration
- `ApiResponse`: Raw API response wrapper
- `ApiException`: API error information

## Building from Source

1. Clone the repository
2. Navigate to the Java SDK directory
3. Build with Maven:

```bash
mvn clean install
```

## Testing

Run the test suite:

```bash
mvn test
```

Run tests with coverage:

```bash
mvn test jacoco:report
```

## Examples

See the `src/main/java/com/cbsc/trading/api/examples/` directory for complete usage examples.

## Support

For issues and questions:
- Check the [API Documentation](https://docs.cbsc.com/api)
- Review the test cases for usage patterns
- Submit issues on the project repository

## License

This SDK is licensed under the MIT License. See the LICENSE file for details.