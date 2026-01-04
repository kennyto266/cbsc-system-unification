# CBSC Risk Management API v2

Advanced risk analysis and management API for quantitative trading strategies.

## Overview

This API provides comprehensive risk management capabilities including:

- Real-time risk metrics calculation
- Customizable alert configurations
- Dynamic risk adjustments
- Risk report generation
- WebSocket-based real-time streaming
- Advanced security and rate limiting

## Features

### Risk Metrics
- **Value at Risk (VaR)**: Historical and parametric calculations at 95% and 99% confidence levels
- **Expected Shortfall**: Conditional VaR calculations for tail risk assessment
- **Drawdown Analysis**: Maximum drawdown, current drawdown, and recovery time metrics
- **Volatility Metrics**: Daily, monthly, and annualized volatility with regime detection
- **Correlation Analysis**: Portfolio correlation and concentration metrics
- **Performance Ratios**: Sharpe, Sortino, Calmar, and Information ratios

### Alert System
- Configurable thresholds for any risk metric
- Multi-level alerts (Warning, Error, Critical)
- Customizable notification channels
- Cooldown periods to prevent alert fatigue
- Alert history and resolution tracking

### Dynamic Adjustments
- Position scaling based on risk budget
- Volatility targeting
- Dynamic rebalancing
- Stop-loss adjustments
- Emergency exit mechanisms

### Real-time Monitoring
- WebSocket connections for live data streaming
- Risk metric updates
- Alert notifications
- Adjustment recommendations

## API Endpoints

### Base URL
```
http://localhost:8002/api/v2/risk
```

### Authentication
All endpoints require JWT authentication (except health endpoints).

```bash
Authorization: Bearer <your_jwt_token>
```

### Risk Metrics

#### Get Portfolio Risk Metrics
```http
GET /portfolio/{portfolio_id}
```

#### Get Strategy Risk Metrics
```http
GET /strategy/{strategy_id}
```

#### Get Available Metrics
```http
GET /metrics
```

#### Get Historical Data
```http
GET /history?portfolio_id={id}&start_date={date}&end_date={date}
```

### Alert Configuration

#### List Alerts
```http
GET /alerts?portfolio_id={id}&strategy_id={id}&enabled_only=true
```

#### Create Alert
```http
POST /alerts
Content-Type: application/json

{
  "name": "VaR Alert",
  "metric_type": "var",
  "portfolio_id": "portfolio_123",
  "threshold_warning": -0.02,
  "threshold_error": -0.03,
  "threshold_critical": -0.05,
  "comparison_operator": "less_than",
  "cooldown_period": 300,
  "enabled": true,
  "notification_channels": ["email", "webhook"]
}
```

#### Update Alert
```http
PUT /alerts/{alert_id}
```

#### Delete Alert
```http
DELETE /alerts/{alert_id}
```

### Report Generation

#### List Reports
```http
GET /reports?portfolio_id={id}&strategy_id={id}
```

#### Generate Report
```http
POST /reports
Content-Type: application/json

{
  "portfolio_id": "portfolio_123",
  "report_type": "comprehensive",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "metrics": ["var", "volatility", "drawdown"],
  "format": "pdf",
  "include_charts": true,
  "include_recommendations": true
}
```

#### Get Report Details
```http
GET /reports/{report_id}
```

#### Download Report
```http
GET /reports/{report_id}/download
```

### Dynamic Adjustments

#### Get Adjustment History
```http
GET /adjustments?portfolio_id={id}
```

#### Evaluate Adjustments
```http
POST /adjustments
Content-Type: application/json

{
  "portfolio_id": "portfolio_123",
  "current_positions": {
    "AAPL": 100000,
    "GOOGL": 50000
  },
  "risk_budget": 0.02,
  "target_leverage": 1.0,
  "adjustment_type": "position_scaling",
  "max_adjustment_pct": 0.3
}
```

#### Get Recommendations
```http
GET /recommendations?portfolio_id={id}&priority=high
```

### WebSocket Endpoints

#### Risk Monitoring Stream
```
ws://localhost:8003/ws/risk/monitoring/{connection_id}?user_id={user_id}
```

#### Alert Stream
```
ws://localhost:8003/ws/risk/alerts/{connection_id}?user_id={user_id}
```

### WebSocket Message Format

#### Subscribe to Updates
```json
{
  "type": "subscribe",
  "subscription_type": "portfolio",
  "target_id": "portfolio_123"
}
```

#### Risk Update Message
```json
{
  "type": "risk_update",
  "timestamp": "2024-01-15T10:30:00Z",
  "portfolio_id": "portfolio_123",
  "risk_metrics": {
    "var_metrics": {
      "confidence_95_historical": -0.025,
      "confidence_99_historical": -0.04
    },
    "volatility_metrics": {
      "annualized": 0.18
    }
  }
}
```

#### Alert Message
```json
{
  "type": "alert",
  "timestamp": "2024-01-15T10:30:00Z",
  "alert": {
    "id": "alert_123",
    "level": "HIGH",
    "message": "VaR exceeded threshold",
    "portfolio_id": "portfolio_123"
  }
}
```

## Installation

1. **Clone the repository**
```bash
git clone <repository_url>
cd CODEX--
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run database migrations**
```bash
python -m alembic upgrade head
```

5. **Start the API server**
```bash
cd src/api/risk_management_v2
python main.py
```

## Configuration

### Environment Variables

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8002
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@localhost/risk_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Risk Engine
RISK_CALCULATION_INTERVAL=60
VAR_CONFIDENCE_LEVELS=[0.95, 0.99]
VOLATILITY_WINDOWS=[21, 63, 252]

# WebSocket
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8003
WEBSOCKET_MAX_CONNECTIONS=1000

# InfluxDB
INFLUXDB_HOST=localhost
INFLUXDB_PORT=8086
INFLUXDB_DATABASE=risk_metrics
```

## Rate Limiting

The API implements rate limiting based on:

- **Default**: 100 requests/hour
- **Alerts**: 50 requests/hour
- **Reports**: 20 requests/hour
- **Adjustments**: 20 requests/hour

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time (Unix timestamp)

## Security Features

- JWT-based authentication
- Permission-based authorization
- Rate limiting with Redis
- Request size limiting
- Security headers (CSP, XSS Protection, etc.)
- Audit logging for all requests
- CORS configuration

## Monitoring

### Health Checks

- **Basic Health**: `GET /health`
- **Readiness Check**: `GET /health/ready`
- **Liveness Check**: `GET /health/live`

### Metrics

Prometheus metrics are available at `/metrics` when enabled.

### Logging

All requests are logged with:
- Timestamp
- User ID
- Method and path
- Status code
- Duration
- Request ID

## Testing

Run the test suite:

```bash
pytest src/api/risk_management_v2/tests/ -v
```

Run with coverage:

```bash
pytest --cov=src/api/risk_management_v2 --cov-report=html
```

## Performance

- Risk calculations are cached for 5 minutes
- Database queries use connection pooling
- WebSocket connections are efficiently managed
- Asynchronous processing for long-running tasks

## Integration with CBSC System

This API integrates with:

- **CBSC Main System**: Port 3003
- **Strategy Management**: Port 3004
- **Monitoring Service**: Port 3005

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL configuration
   - Verify database is running
   - Check connection credentials

2. **Redis Connection Errors**
   - Verify Redis is running
   - Check REDIS_URL configuration
   - Test connection with `redis-cli`

3. **WebSocket Connection Issues**
   - Check WebSocket port accessibility
   - Verify user authentication
   - Check browser console for errors

4. **Rate Limiting Issues**
   - Check Redis connection
   - Verify client identifier (IP or user ID)
   - Review rate limit configuration

### Debug Mode

Enable debug mode for detailed logging:

```bash
DEBUG=true python main.py
```

## Support

For support and questions:

- Email: dev-team@cbsc.com
- Documentation: `http://localhost:8002/docs`
- API Reference: `http://localhost:8002/redoc`

## License

Copyright © 2024 CBSC. All rights reserved.