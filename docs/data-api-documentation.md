# Data Service API Documentation

## Overview

The Data Service API provides endpoints for accessing market data, economic indicators, and data export functionality for the quant strategy management system.

### Base URL
```
http://localhost:3003/api/v2
```

### Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Market Data Endpoints

### 1. Get Historical Market Data

**Endpoint:** `GET /market-data/{symbol}/history`

**Description:** Retrieve historical market data for a specific symbol.

**Parameters:**
- `symbol` (path): Stock symbol (e.g., AAPL, MSFT, 0700.HK)
- `interval` (query): Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
- `start_date` (query): Start date in YYYY-MM-DD format
- `end_date` (query): End date in YYYY-MM-DD format
- `page` (query): Page number for pagination (default: 1)
- `page_size` (query): Records per page (1-1000, default: 100)
- `adjusted` (query): Include adjusted prices (default: true)
- `include_prepost` (query): Include pre/post market data (default: false)

**Example Request:**
```bash
GET /api/v2/market-data/AAPL/history?interval=1d&start_date=2024-01-01&end_date=2024-01-31&page=1&page_size=50
```

**Example Response:**
```json
{
  "symbol": "AAPL",
  "interval": "1d",
  "currency": "USD",
  "data": [
    {
      "timestamp": "2024-01-02T00:00:00Z",
      "open": 185.50,
      "high": 187.20,
      "low": 184.80,
      "close": 186.90,
      "volume": 52345678,
      "adjusted_close": 186.90
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "total": 20,
    "pages": 1,
    "hasNext": false,
    "hasPrev": false
  },
  "metadata": {
    "startDate": "2024-01-01T00:00:00Z",
    "endDate": "2024-01-31T00:00:00Z",
    "adjusted": true,
    "includePrePost": false,
    "dataPoints": 20
  },
  "timestamp": "2024-12-18T10:00:00Z"
}
```

### 2. Get Real-time Market Data

**Endpoint:** `GET /market-data/{symbol}/realtime`

**Description:** Retrieve the latest market data for a specific symbol.

**Parameters:**
- `symbol` (path): Stock symbol
- `fields` (query): Comma-separated list of fields to return

**Example Request:**
```bash
GET /api/v2/market-data/AAPL/realtime?fields=price,change,volume
```

**Example Response:**
```json
{
  "symbol": "AAPL",
  "price": 195.50,
  "change": 1.20,
  "change_percent": 0.62,
  "volume": 15234567,
  "bid": 195.45,
  "ask": 195.55,
  "high": 196.00,
  "low": 194.80,
  "timestamp": "2024-12-18T15:30:00Z",
  "market_state": "open"
}
```

### 3. Get Bulk Real-time Data

**Endpoint:** `GET /market-data/bulk/realtime`

**Description:** Retrieve real-time data for multiple symbols.

**Parameters:**
- `symbols` (query): List of stock symbols (max 100)
- `fields` (query): Comma-separated list of fields to return

**Example Request:**
```bash
GET /api/v2/market-data/bulk/realtime?symbols=AAPL,MSFT,GOOGL&fields=price,change
```

### 4. Get Market Statistics

**Endpoint:** `GET /market-data/{symbol}/stats`

**Description:** Retrieve statistical analysis of market data.

**Parameters:**
- `symbol` (path): Stock symbol
- `period` (query): Statistics period (1D, 1W, 1M, 3M, 6M, 1Y, ALL)

**Example Response:**
```json
{
  "symbol": "AAPL",
  "period": "1M",
  "data_points": 22,
  "price": {
    "current": 195.50,
    "high": 198.20,
    "low": 182.50,
    "average": 190.30,
    "median": 190.45
  },
  "volatility": {
    "daily": 1.45,
    "annualized": 23.01
  },
  "returns": {
    "total": 5.43,
    "max_drawdown": -8.2,
    "sharpe_ratio": 1.35
  }
}
```

## Economic Indicators Endpoints

### 1. List Economic Indicators

**Endpoint:** `GET /economic-indicators/`

**Description:** Get a list of available economic indicators.

**Parameters:**
- `category` (query): Filter by category (interest_rates, gdp, employment, etc.)
- `country` (query): Country code (default: US)

**Example Response:**
```json
{
  "country": "US",
  "indicators": {
    "interest_rates": {
      "Fed_Funds": {
        "name": "Federal Funds Rate",
        "description": "US Federal Reserve interest rate",
        "unit": "percent",
        "frequency": "daily"
      }
    }
  },
  "categories": ["interest_rates", "gdp", "employment", "inflation", "pmi"]
}
```

### 2. Get Economic Indicator Data

**Endpoint:** `GET /economic-indicators/{indicator}/data`

**Description:** Retrieve historical data for a specific economic indicator.

**Parameters:**
- `indicator` (path): Indicator code (e.g., Fed_Funds, HIBOR, CPI)
- `country` (query): Country code (default: US)
- `start_date` (query): Start date in YYYY-MM-DD
- `end_date` (query): End date in YYYY-MM-DD

**Example Response:**
```json
{
  "indicator": "Fed_Funds",
  "country": "US",
  "data": [
    {
      "date": "2024-01-01T00:00:00Z",
      "value": 5.25,
      "unit": "percent",
      "source": "Federal Reserve"
    }
  ],
  "statistics": {
    "min": 0.25,
    "max": 5.50,
    "average": 2.15,
    "latest": 5.25,
    "change": 0.25
  }
}
```

### 3. Get HIBOR Rates

**Endpoint:** `GET /economic-indicators/hibor`

**Description:** Retrieve Hong Kong Interbank Offered Rates.

**Parameters:**
- `tenor` (query): HIBOR tenor (ON, 1W, 1M, 3M, 6M, 12M)
- `start_date` (query): Start date
- `end_date` (query): End date

### 4. Economic Dashboard

**Endpoint:** `GET /economic-indicators/dashboard`

**Description:** Get a dashboard view of key economic indicators.

**Parameters:**
- `indicators` (query): Comma-separated list of indicators

**Example Response:**
```json
{
  "dashboard": {
    "HIBOR": {
      "value": 3.5,
      "change": 0.1,
      "unit": "percent"
    },
    "CPI": {
      "value": 3.2,
      "change": -0.2,
      "unit": "percent"
    }
  },
  "market_context": {
    "risk_sentiment": "Moderate",
    "alerts": []
  }
}
```

## Data Export Endpoints

### 1. Create Export Job

**Endpoint:** `POST /data/export`

**Description:** Create a background job to export data.

**Request Body:**
```json
{
  "data_type": "market_data",
  "symbols": ["AAPL", "MSFT"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "format": "csv",
  "include_metadata": true,
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "job_id": "uuid-1234-5678",
  "status": "queued",
  "message": "Export job created",
  "estimated_time": "< 1 minute"
}
```

### 2. Get Export Job Status

**Endpoint:** `GET /data/export/{job_id}`

**Description:** Check the status of an export job.

**Response:**
```json
{
  "job_id": "uuid-1234-5678",
  "status": "completed",
  "progress": 100,
  "result_url": "/exports/export_1234_20241218.csv",
  "file_size": 1024000,
  "record_count": 50000
}
```

### 3. Download Export File

**Endpoint:** `GET /data/export/{job_id}/download`

**Description:** Download the exported data file.

**Response:** File download with appropriate content type.

### 4. List Export Jobs

**Endpoint:** `GET /data/export`

**Description:** List all export jobs for the current user.

**Parameters:**
- `status` (query): Filter by status (queued, processing, completed, failed)
- `limit` (query): Maximum number of jobs to return

## Rate Limits

- **Market Data Endpoints:** 1000 requests per minute
- **Economic Indicators:** 500 requests per minute
- **Export Jobs:** 10 concurrent jobs per user
- **Bulk Requests:** 100 requests per hour

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `201` - Created (for new resources)
- `202` - Accepted (for background jobs)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error

Error response format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format",
    "details": "Use YYYY-MM-DD format for dates"
  },
  "timestamp": "2024-12-18T10:00:00Z"
}
```

## SDK and Examples

### Python Example

```python
import requests
import pandas as pd

# Set up authentication
headers = {
    "Authorization": "Bearer <your-jwt-token>",
    "Content-Type": "application/json"
}

# Get historical data
response = requests.get(
    "http://localhost:3003/api/v2/market-data/AAPL/history",
    headers=headers,
    params={
        "interval": "1d",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
)
data = response.json()

# Convert to DataFrame
df = pd.DataFrame(data["data"])
print(df.head())
```

### JavaScript Example

```javascript
// Get real-time data
const headers = {
  "Authorization": `Bearer ${token}`,
  "Content-Type": "application/json"
};

fetch('http://localhost:3003/api/v2/market-data/AAPL/realtime', {
  headers
})
.then(response => response.json())
.then(data => {
  console.log('Current price:', data.price);
  console.log('Change:', data.change_percent);
});
```

## WebSocket Integration

For real-time streaming of market data, the API supports WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:3003/ws/market-data');

ws.onopen = () => {
  // Subscribe to symbols
  ws.send(JSON.stringify({
    action: 'subscribe',
    symbols: ['AAPL', 'MSFT', 'GOOGL']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

## Best Practices

1. **Caching:** Utilize client-side caching for historical data
2. **Batch Requests:** Use bulk endpoints for multiple symbols
3. **Pagination:** Always handle pagination for large datasets
4. **Error Handling:** Implement proper error handling and retries
5. **Rate Limits:** Respect rate limits to avoid being blocked
6. **Date Ranges:** Use reasonable date ranges to avoid timeouts

## Support

For API support and questions:
- Documentation: `/docs`
- Health Check: `/api/v2/data/health`
- Email: api-support@cbsc.com