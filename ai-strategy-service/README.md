# AI Strategy Service

> Backend service for AI-powered quantitative trading strategy generation using GLM 4.7.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

AI Strategy Service is a FastAPI-based backend service that provides REST APIs for generating, testing, and deploying quantitative trading strategies using the GLM 4.7 AI model from 智譜AI.

## Features

- 🤖 **AI Strategy Generation**: Generate Python code from natural language descriptions
- 📓 **Notebook Templates**: Pre-built Jupyter notebook templates for common strategies
- 🚀 **Strategy Execution**: Execute and validate Jupyter notebooks
- 🔄 **CBSC Integration**: Deploy strategies to the CBSC trading system
- 📊 **Performance Metrics**: Calculate and analyze strategy performance
- 🔒 **Secure API**: Authentication and rate limiting

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/your-org/ai-strategy-tool.git
cd ai-strategy-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# GLM API Configuration
GLM_API_KEY=your_glm_api_key_here
GLM_MODEL=glm-4-plus

# CBSC Integration (optional)
CBSC_API_URL=http://localhost:3003
CBSC_API_KEY=your_cbsc_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### 3. Start Server

```bash
# Development mode with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

### 4. Access API Documentation

Open your browser and navigate to:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Strategy Generation

#### POST /api/strategy/generate

Generate a trading strategy from natural language.

```bash
curl -X POST http://localhost:8000/api/strategy/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "20-day moving average crossover strategy",
    "market": "stock",
    "risk_level": "medium"
  }'
```

**Response:**
```json
{
  "code": "# Cell 1\nimport pandas as pd\n...",
  "explanation": "This strategy uses...",
  "parameters": {
    "SHORT_MA": "20",
    "LONG_MA": "50"
  }
}
```

### Strategy Deployment

#### POST /api/strategy/deploy

Deploy a strategy to the CBSC system.

```bash
curl -X POST http://localhost:8000/api/strategy/deploy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_CBSC_API_KEY" \
  -d '{
    "notebook_path": "/path/to/strategy.ipynb",
    "strategy_name": "MA Crossover",
    "user_id": "user-123"
  }'
```

**Response:**
```json
{
  "success": true,
  "strategy_id": "strategy-abc123",
  "message": "Strategy deployed successfully"
}
```

### Notebook Execution

#### POST /api/notebooks/execute

Execute a Jupyter notebook.

```bash
curl -X POST http://localhost:8000/api/notebooks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_path": "/path/to/strategy.ipynb",
    "timeout": 60
  }'
```

### Templates

#### GET /api/templates

List all available strategy templates.

```bash
curl http://localhost:8000/api/templates
```

**Response:**
```json
{
  "templates": [
    {
      "name": "breakout",
      "description": "Classic breakout strategy",
      "category": "trend_following"
    },
    {
      "name": "mean_reversion",
      "description": "Bollinger Bands mean reversion",
      "category": "mean_reversion"
    }
  ]
}
```

## Architecture

```
┌─────────────────────────────────────┐
│         FastAPI Application         │
│  (main.py, routers/strategy.py)    │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────────┐
│ GLM Service │  │ Jupyter Service  │
│ (glm_service.py)│  (jupyter_service.py)│
└─────────────┘  └──────────────────┘
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────────┐
│ GLM-4 API   │  │ Jupyter Kernels  │
└─────────────┘  └──────────────────┘
```

## Project Structure

```
ai-strategy-service/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── routers/
│   └── strategy.py              # Strategy-related endpoints
├── services/
│   ├── glm_service.py           # GLM API integration
│   ├── jupyter_service.py       # Jupyter notebook operations
│   └── cbsc_integration.py      # CBSC system integration
├── templates/
│   └── notebook_templates.py    # Pre-built strategy templates
└── tests/
    ├── test_strategy_generation.py
    ├── test_integration.py
    └── test_e2e.py
```

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_strategy_generation.py -v

# Run async tests only
pytest tests/ -k "asyncio" -v
```

### Development Server

```bash
# Start with auto-reload and debug logging
python -m uvicorn main:app --reload --log-level debug

# Start with specific port
python -m uvicorn main:app --reload --port 8080
```

### Code Style

```bash
# Format code with black
black .

# Check linting with flake8
flake8 .

# Type checking with mypy
mypy .
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GLM_API_KEY` | Yes | - | Your GLM API key from 智譜AI |
| `GLM_MODEL` | No | "glm-4-plus" | GLM model to use |
| `CBSC_API_URL` | No | "http://localhost:3003" | CBSC backend URL |
| `CBSC_API_KEY` | No | - | CBSC API key (for deployment) |
| `HOST` | No | "0.0.0.0" | Server host |
| `PORT` | No | "8000" | Server port |
| `DEBUG` | No | "false" | Enable debug mode |

### GLM API Setup

1. Visit [https://open.bigmodel.cn/](https://open.bigmodel.cn/)
2. Sign up for an account
3. Navigate to API Keys section
4. Generate a new API key
5. Add to `.env` file

## Deployment

### Docker

```bash
# Build image
docker build -t ai-strategy-service .

# Run container
docker run -p 8000:8000 \
  -e GLM_API_KEY=your_key \
  ai-strategy-service

# With docker-compose
docker-compose up -d
```

### Gunicorn (Production)

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-strategy-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-strategy-service
  template:
    metadata:
      labels:
        app: ai-strategy-service
    spec:
      containers:
      - name: api
        image: ai-strategy-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: GLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: glm-secrets
              key: api-key
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### Metrics (Optional)

Enable Prometheus metrics:

```python
# main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

Access metrics at: `http://localhost:8000/metrics`

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

**Problem:** `Port 8000 is already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process or use different port
python -m uvicorn main:app --port 8001
```

### GLM API Errors

**Problem:** `GLM API error: 401 Unauthorized`

**Solution:**
1. Verify API key in `.env` file
2. Check API key hasn't expired
3. Ensure sufficient quota remains

### Jupyter Not Found

**Problem:** `jupyter: command not found`

**Solution:**
```bash
pip install jupyter
python -m ipykernel install --user
```

For more troubleshooting tips, see the [complete setup guide](../docs/setup-guide.md).

## API Reference

Complete API documentation is available at:
- **Interactive docs**: [docs/api-reference.md](../docs/api-reference.md)
- **Swagger UI**: `http://localhost:8000/docs` (when running)

## Contributing

We welcome contributions! Please see our contributing guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](../docs/setup-guide.md)
- 🐛 [Issue Tracker](https://github.com/your-org/ai-strategy-tool/issues)
- 💬 [Discussions](https://github.com/your-org/ai-strategy-tool/discussions)

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [GLM-4 Plus](https://open.bigmodel.cn/) from 智譜AI
- Part of the CBSC quantitative trading platform

---

**Made with ❤️ for quantitative traders and strategy developers**
