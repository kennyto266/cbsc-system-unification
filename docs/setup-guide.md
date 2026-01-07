# AI Strategy Development Tool - Setup Guide

Complete guide for installing and configuring the AI Strategy Development Tool.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Advanced Setup](#advanced-setup)

---

## Prerequisites

Before installing the AI Strategy Development Tool, ensure you have the following:

### Required Software

1. **VSCode** (version 1.85.0 or later)
   - Download from: [https://code.visualstudio.com/](https://code.visualstudio.com/)
   - Check version: `code --version`

2. **Python 3.10+**
   - Download from: [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Check version: `python --version`
   - Recommended: Use pyenv or conda for version management

3. **Node.js 18+**
   - Download from: [https://nodejs.org/](https://nodejs.org/)
   - Check version: `node --version`
   - npm comes bundled with Node.js

4. **Git**
   - Download from: [https://git-scm.com/](https://git-scm.com/)
   - Check version: `git --version`

### Required Accounts

1. **GLM API Key** from [智譜AI](https://open.bigmodel.cn/)
   - Sign up for a free account
   - Navigate to API Keys section
   - Generate a new API key
   - Note: Free tier includes 1000 requests/day

2. **CBSC Account** (for deployment integration)
   - Required only if deploying strategies to CBSC system
   - API key available from CBSC dashboard

---

## Installation

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/ai-strategy-tool.git
cd ai-strategy-tool
```

### Step 2: Install VSCode Extension

```bash
# Navigate to VSCode extension directory
cd ai-strategy-vscode

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Install extension in VSCode
code . --install-extension ai-strategy-assistant-0.1.0.vsix
```

Alternatively, install directly from source:

```bash
# Package the extension
npm run package

# Install the generated .vsix file
code --install-extension ai-strategy-assistant-0.1.0.vsix
```

### Step 3: Install Backend Service

```bash
# Navigate to backend service directory
cd ai-strategy-service

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### Step 4: Install Jupyter

```bash
# Install Jupyter notebook
pip install jupyter

# Install IPython kernel
python -m ipykernel install --user --name=python3

# Verify installation
jupyter --version
```

Expected output:
```
jupyter core     : 4.11.1
jupyter-notebook : 6.5.2
qtconsole        : not installed
ipython          : 8.10.0
ipykernel        : 6.23.1
jupyter client   : 8.2.0
jupyter lab      : not installed
nbconvert        : 7.7.3
```

---

## Configuration

### Step 1: Configure GLM API Key

#### For VSCode Extension:

1. Open VSCode
2. Press `Ctrl+,` (Cmd+, on Mac) to open Settings
3. Search for "aiStrategy"
4. Set the following configuration:

```json
{
  "aiStrategy.glmApiKey": "your_actual_glm_api_key_here",
  "aiStrategy.glmModel": "glm-4-plus",
  "aiStrategy.serviceUrl": "http://localhost:8000"
}
```

#### For Backend Service:

1. Edit `ai-strategy-service/.env`:
```bash
# GLM API Configuration
GLM_API_KEY=your_actual_glm_api_key_here
GLM_MODEL=glm-4-plus

# CBSC Integration (optional)
CBSC_API_URL=http://localhost:3003
CBSC_API_KEY=your_cbsc_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Step 2: Start Backend Service

```bash
cd ai-strategy-service

# Activate virtual environment if not already active
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Start FastAPI server with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 3: Verify Installation

1. Test backend health:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy"
}
```

2. Check API documentation:
   - Open browser: `http://localhost:8000/docs`
   - Should see FastAPI auto-generated documentation

3. Test VSCode extension:
   - Open VSCode
   - Press `Ctrl+Shift+P`
   - Type "AI Strategy"
   - Should see AI Strategy commands

---

## Usage

### Creating Your First Strategy

1. **Open VSCode** and activate the extension

2. **Create a new notebook:**
   - Press `Ctrl+Shift+P`
   - Type "Create Strategy Notebook"
   - Press Enter

3. **Open AI Chat:**
   - Press `Ctrl+Shift+P`
   - Type "Open AI Chat"
   - Press Enter

4. **Describe your strategy:**
   In the chat panel, type:
   ```
   Create a 20-day moving average crossover strategy
   with volume confirmation for stock trading
   ```

5. **Insert generated code:**
   - Wait for AI to generate code
   - Click "Insert into Notebook" button
   - Code will be added to your notebook

6. **Execute the notebook:**
   - Run each cell sequentially
   - View outputs and visualizations
   - Modify parameters as needed

### Example Strategies

#### Moving Average Crossover
```
Create a simple moving average crossover strategy:
- Buy when 20-day MA crosses above 50-day MA
- Sell when 20-day MA crosses below 50-day MA
- Add 2% stop loss
```

#### Mean Reversion
```
Create a mean reversion strategy using Bollinger Bands:
- Buy when price touches lower band
- Sell when price returns to mean
- Use 20-day lookback period
```

#### Breakout Strategy
```
Create a breakout strategy:
- Buy when price breaks above 20-day high
- Use volume confirmation (1.5x average)
- Trail stop at 2 ATR
```

---

## Testing

### Run VSCode Extension Tests

```bash
cd ai-strategy-vscode

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Run Backend Service Tests

```bash
cd ai-strategy-service

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_strategy_generation.py -v

# Run async tests only
pytest tests/ -k "asyncio" -v
```

### Run End-to-End Tests

```bash
cd ai-strategy-service

# Run complete workflow test
pytest tests/test_e2e.py -v -s

# Run integration tests
pytest tests/test_integration.py -v
```

### Test Coverage Goals

- Unit tests: >80% coverage
- Integration tests: All critical paths
- E2E tests: Complete user workflows

---

## Troubleshooting

### GLM API Errors

**Problem:** `GLM API error: 401 Unauthorized`

**Solution:**
1. Verify your API key is correct
2. Check API key hasn't expired
3. Ensure sufficient quota remains
4. Check network connectivity to `open.bigmodel.cn`

**Problem:** `GLM API error: 429 Too Many Requests`

**Solution:**
1. You've exceeded rate limits
2. Wait 1 hour before retrying
3. Consider upgrading to paid tier

### Notebook Execution Fails

**Problem:** `jupyter: command not found`

**Solution:**
```bash
# Reinstall Jupyter
pip install --upgrade jupyter

# Verify installation
jupyter --version
```

**Problem:** `Kernel not found: python3`

**Solution:**
```bash
# Install IPython kernel
python -m ipykernel install --user --name=python3

# List available kernels
jupyter kernelspec list
```

**Problem:** `ModuleNotFoundError: No module named 'pandas'`

**Solution:**
```bash
# Install required packages
pip install pandas numpy matplotlib

# Or install all requirements
pip install -r ai-strategy-service/requirements.txt
```

### Extension Not Loading

**Problem:** VSCode extension doesn't activate

**Solution:**
1. Check VSCode version (must be 1.85.0+)
2. Reload VSCode (`Ctrl+Shift+P` → "Reload Window")
3. Check Developer Console:
   - `Help` → `Toggle Developer Tools`
   - Look for error messages
4. Reinstall extension:
   ```bash
   code -- uninstall-extension ai-strategy-assistant
   code --install-extension ai-strategy-assistant-0.1.0.vsix
   ```

### Backend Service Issues

**Problem:** `Port 8000 already in use`

**Solution:**
```bash
# Find process using port 8000
# On Windows:
netstat -ano | findstr :8000
# On Linux/Mac:
lsof -i :8000

# Kill the process or change port:
python -m uvicorn main:app --reload --port 8001
```

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Ensure virtual environment is activated
# Then reinstall dependencies
pip install -r requirements.txt
```

---

## Advanced Setup

### Development Mode

For active development:

```bash
# Backend with hot reload
python -m uvicorn main:app --reload --log-level debug

# VSCode extension in watch mode
cd ai-strategy-vscode
npm run watch
```

### Production Deployment

#### Backend Service (using Gunicorn):

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### Docker Deployment:

```bash
# Build image
docker build -t ai-strategy-service .

# Run container
docker run -p 8000:8000 \
  -e GLM_API_KEY=your_key \
  ai-strategy-service
```

### Environment-Specific Configuration

```bash
# Development
export ENV=development
export DEBUG=true

# Production
export ENV=production
export DEBUG=false
```

---

## Next Steps

1. **Explore Templates:**
   - Check `ai-strategy-service/templates/` for pre-built strategies
   - Modify templates to fit your needs

2. **Deploy to CBSC:**
   - Configure CBSC API credentials
   - Use the deployment endpoint to publish strategies

3. **Customize Prompts:**
   - Modify system prompts in `glm_service.py`
   - Add domain-specific knowledge

4. **Contribute:**
   - Report issues on GitHub
   - Submit pull requests
   - Improve documentation

---

## Support

For issues and questions:

- **Documentation:** [GitHub Wiki](https://github.com/your-org/ai-strategy-tool/wiki)
- **Issues:** [GitHub Issues](https://github.com/your-org/ai-strategy-tool/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/ai-strategy-tool/discussions)

---

## License

MIT License - see LICENSE file for details
