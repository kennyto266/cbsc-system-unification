# AI Strategy Service - API Reference

Complete API documentation for the AI Strategy Development Tool backend service.

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require an API key in the request header:

```http
Authorization: Bearer YOUR_API_KEY
```

---

## Endpoints

### Health Check

#### GET /health

Check if the service is running.

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-01-07T12:00:00Z"
}
```

---

### Root Endpoint

#### GET /

Get service information.

**Request:**
```http
GET /
```

**Response (200 OK):**
```json
{
  "message": "AI Strategy Service is running",
  "version": "0.1.0",
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "api": "/api/strategy"
  }
}
```

---

## Strategy Generation API

### POST /api/strategy/generate

Generate a trading strategy from natural language description using GLM 4.7 AI.

**Request:**
```http
POST /api/strategy/generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "description": "20-day moving average crossover strategy with volume confirmation",
  "market": "stock",
  "timeframe": "daily",
  "risk_level": "medium"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Natural language description of the strategy |
| `market` | string | No | Market type (default: "stock") |
| `timeframe` | string | No | Data timeframe (default: "daily") |
| `risk_level` | string | No | Risk tolerance: "low", "medium", "high" (default: "medium") |

**Response (200 OK):**
```json
{
  "code": "# Cell 1\nimport pandas as pd\nimport numpy as np\n\n# Cell 2\ndef fetch_data(symbol):\n    ...\n\n# Cell 3\nSHORT_MA = 20\nLONG_MA = 50\n\n# Cell 4\n# Signal generation logic\n...",
  "explanation": "This strategy uses moving average crossovers to generate buy and sell signals...",
  "parameters": {
    "SHORT_MA": "20",
    "LONG_MA": "50",
    "THRESHOLD": "0.02"
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Generated Python code with cell markers |
| `explanation` | string | AI-generated explanation of the strategy |
| `parameters` | object | Extracted strategy parameters |

**Error Responses:**

400 Bad Request:
```json
{
  "detail": "Invalid input: description is required"
}
```

500 Internal Server Error:
```json
{
  "detail": "GLM API error: insufficient quota"
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:8000/api/strategy/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "RSI mean reversion strategy",
    "market": "crypto",
    "risk_level": "low"
  }'
```

**Example using Python:**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/strategy/generate',
    json={
        'description': 'Bollinger Bands breakout strategy',
        'market': 'stock',
        'timeframe': 'hourly',
        'risk_level': 'high'
    }
)

strategy = response.json()
print(strategy['code'])
```

---

## Strategy Deployment API

### POST /api/strategy/deploy

Deploy a generated strategy to the CBSC trading system.

**Request:**
```http
POST /api/strategy/deploy
Content-Type: application/json
Authorization: Bearer YOUR_CBSC_API_KEY
```

**Request Body:**
```json
{
  "notebook_path": "/path/to/strategy.ipynb",
  "strategy_name": "MA Crossover Strategy",
  "user_id": "user-123"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `notebook_path` | string | Yes | Absolute path to the strategy notebook file |
| `strategy_name` | string | Yes | Display name for the strategy |
| `user_id` | string | Yes | User ID who owns this strategy |

**Response (200 OK):**
```json
{
  "success": true,
  "strategy_id": "strategy-abc123",
  "message": "Strategy deployed successfully",
  "dashboard_url": "http://localhost:3003/strategies/strategy-abc123"
}
```

**Error Responses:**

400 Bad Request:
```json
{
  "success": false,
  "error": "Notebook file not found: /path/to/strategy.ipynb"
}
```

401 Unauthorized:
```json
{
  "success": false,
  "error": "Invalid CBSC API key"
}
```

500 Internal Server Error:
```json
{
  "success": false,
  "error": "Failed to connect to CBSC backend"
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:8000/api/strategy/deploy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_cbsc_api_key" \
  -d '{
    "notebook_path": "/home/user/strategies/ma_crossover.ipynb",
    "strategy_name": "MA Crossover",
    "user_id": "user-123"
  }'
```

---

## Strategy Sync API

### GET /api/strategy/sync/{user_id}

Synchronize strategies from CBSC system to the personal dashboard.

**Request:**
```http
GET /api/strategy/sync/user-123
Authorization: Bearer YOUR_CBSC_API_KEY
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | User ID to sync strategies for |

**Response (200 OK):**
```json
{
  "success": true,
  "strategies": [
    {
      "id": "strategy-abc123",
      "name": "MA Crossover Strategy",
      "status": "active",
      "created_at": "2026-01-07T10:00:00Z",
      "performance": {
        "total_return": 15.3,
        "sharpe_ratio": 1.2,
        "max_drawdown": -8.5
      }
    }
  ],
  "count": 1
}
```

**Error Responses:**

404 Not Found:
```json
{
  "success": false,
  "error": "User not found: user-123"
}
```

---

## Template API

### GET /api/templates

List all available strategy templates.

**Request:**
```http
GET /api/templates
```

**Response (200 OK):**
```json
{
  "templates": [
    {
      "name": "breakout",
      "description": "Classic breakout strategy with moving average confirmation",
      "category": "trend_following",
      "difficulty": "beginner"
    },
    {
      "name": "mean_reversion",
      "description": "Mean reversion strategy using Bollinger Bands",
      "category": "mean_reversion",
      "difficulty": "intermediate"
    }
  ]
}
```

### GET /api/templates/{name}

Get a specific template by name.

**Request:**
```http
GET /api/templates/breakout
```

**Response (200 OK):**
```json
{
  "name": "breakout",
  "description": "Classic breakout strategy",
  "notebook": {
    "cells": [
      {
        "cell_type": "code",
        "source": ["import pandas as pd\n", "import numpy as np\n"]
      }
    ],
    "metadata": {
      "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
      }
    },
    "nbformat": 4,
    "nbformat_minor": 4
  }
}
```

---

## Notebook Execution API

### POST /api/notebooks/execute

Execute a Jupyter notebook and return results.

**Request:**
```http
POST /api/notebooks/execute
Content-Type: application/json
```

**Request Body:**
```json
{
  "notebook_path": "/path/to/strategy.ipynb",
  "timeout": 60
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `notebook_path` | string | Yes | Absolute path to the notebook file |
| `timeout` | integer | No | Execution timeout in seconds (default: 60) |

**Response (200 OK):**
```json
{
  "success": true,
  "output": "Cell 1 output\nCell 2 output\n...",
  "execution_time": 3.45,
  "cells_executed": 6
}
```

**Error Responses:**

400 Bad Request:
```json
{
  "success": false,
  "error": "Invalid notebook format"
}
```

408 Request Timeout:
```json
{
  "success": false,
  "error": "Execution timeout after 60 seconds"
}
```

---

## Validation API

### POST /api/notebooks/validate

Validate a Jupyter notebook structure and syntax.

**Request:**
```http
POST /api/notebooks/validate
Content-Type: application/json
```

**Request Body:**
```json
{
  "notebook_path": "/path/to/strategy.ipynb"
}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Cell 3: Unused variable 'temp_data'"
  ],
  "cells_checked": 6
}
```

**Response (400 Bad Request) - Invalid Notebook:**
```json
{
  "valid": false,
  "errors": [
    "Invalid nbformat version: 3 (expected 4)",
    "Cell 5: Syntax error: invalid syntax (<unknown>, line 12)"
  ],
  "warnings": [],
  "cells_checked": 6
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input parameters |
| 401 | Unauthorized - Missing or invalid API key |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server-side error |
| 503 | Service Unavailable - GLM API or CBSC backend down |

---

## Rate Limiting

The API implements the following rate limits:

| Endpoint | Rate Limit |
|----------|------------|
| POST /api/strategy/generate | 10 requests/minute |
| POST /api/strategy/deploy | 5 requests/minute |
| GET /api/strategy/sync/{user_id} | 20 requests/minute |
| Other endpoints | 60 requests/minute |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1704624320
```

---

## WebSocket API (Coming Soon)

Real-time strategy execution updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/execute');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'execute',
    notebook_path: '/path/to/strategy.ipynb'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Cell', data.cell_index, 'completed');
  console.log('Output:', data.output);
};
```

---

## SDK Examples

### Python SDK

```python
from ai_strategy_client import AIStrategyClient

# Initialize client
client = AIStrategyClient(
    api_key="your_api_key",
    base_url="http://localhost:8000"
)

# Generate strategy
strategy = client.generate_strategy(
    description="Momentum strategy with RSI",
    market="stock",
    risk_level="medium"
)

# Deploy strategy
result = client.deploy_strategy(
    notebook_path="/path/to/strategy.ipynb",
    strategy_name="RSI Momentum",
    user_id="user-123"
)

print(f"Deployed: {result['strategy_id']}")
```

### JavaScript/TypeScript SDK

```typescript
import { AIStrategyClient } from '@ai-strategy/sdk';

const client = new AIStrategyClient({
  apiKey: 'your_api_key',
  baseURL: 'http://localhost:8000'
});

// Generate strategy
const strategy = await client.generateStrategy({
  description: 'Grid trading strategy',
  market: 'crypto',
  timeframe: 'hourly'
});

// Deploy strategy
const result = await client.deployStrategy({
  notebookPath: '/path/to/strategy.ipynb',
  strategyName: 'Grid Trading',
  userId: 'user-123'
});

console.log(`Deployed: ${result.strategyId}`);
```

---

## OpenAPI Specification

Interactive API documentation available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

Download OpenAPI JSON:
```bash
curl http://localhost:8000/openapi.json -o openapi.json
```

---

## Changelog

### Version 0.1.0 (2026-01-07)
- Initial API release
- Strategy generation endpoint
- Deployment to CBSC system
- Template management
- Notebook execution and validation
