# CBSC Strategy Workflow - Installation Guide

Complete installation guide for the CBSC Data Science Strategy Development Framework.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Installation Methods](#installation-methods)
  - [Automated Installation](#automated-installation)
  - [Manual Installation](#manual-installation)
  - [Docker Installation](#docker-installation)
- [Post-Installation](#post-installation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **Python**: 3.10 or higher
- **Memory**: 4GB RAM (8GB recommended)
- **Storage**: 2GB free space
- **OS**: Linux, macOS, or Windows 10+

### Recommended Requirements

- **Python**: 3.11
- **Memory**: 16GB RAM
- **Storage**: 10GB SSD
- **GPU**: NVIDIA GPU with CUDA support (optional)

### Python Dependencies

Core dependencies are automatically installed:
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- plotly >= 5.14.0
- scipy >= 1.10.0
- scikit-learn >= 1.3.0
- jupyter >= 1.0.0

---

## Quick Start

### For Linux/macOS

```bash
# Clone repository
git clone https://github.com/cbsc/cbsc-strategy-workflow.git
cd cbsc-strategy-workflow

# Run installation script
chmod +x scripts/install_dev.sh
./scripts/install_dev.sh

# Activate environment
source .venv/bin/activate

# Verify installation
python scripts/verify_install.py
```

### For Windows

```batch
REM Clone repository
git clone https://github.com/cbsc/cbsc-strategy-workflow.git
cd cbsc-strategy-workflow

REM Run installation script
scripts\install_dev.bat

REM Activate environment
.venv\Scripts\activate.bat

REM Verify installation
python scripts\verify_install.py
```

---

## Installation Methods

### Automated Installation

The automated installation script handles everything:

1. **Python version check** (3.10+ required)
2. **Virtual environment creation**
3. **Dependency installation**
4. **TA-Lib installation** (optional)
5. **Configuration file setup**
6. **Pre-commit hooks**
7. **Project directories**
8. **Verification tests**

**Linux/macOS:**
```bash
./scripts/install_dev.sh
```

**Windows:**
```batch
scripts\install_dev.bat
```

### Manual Installation

If you prefer manual installation or need custom configuration:

#### 1. Create Virtual Environment

```bash
# Python 3.10+
python3 -m venv .venv

# Activate
# Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate.bat
```

#### 2. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

#### 3. Install Package

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Or install with all optional dependencies
pip install -e ".[dev,ml,database]"
```

#### 4. Create Configuration Files

```bash
# Copy environment template
cp .env.template .env

# Copy config template
mkdir -p config
cp config/config.template.yaml config/config.yaml

# Edit configuration
nano .env
nano config/config.yaml
```

#### 5. Create Project Directories

```bash
mkdir -p data/{cache,raw,processed,exports}
mkdir -p logs
mkdir -p notebooks/{research,strategies,backtests}
mkdir -p results/{backtests,optimizations,analysis}
mkdir -p tests/{unit,integration}
```

### Docker Installation

For containerized development environment:

#### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

#### Quick Start

```bash
# Build and start services
cd docker
docker-compose -f docker-compose.ds.yml up -d

# Access Jupyter Lab
# Open browser: http://localhost:8888
```

#### Build Custom Image

```bash
# Build image
docker build -f docker/Dockerfile.dev -t cbsc-strategy-dev:latest .

# Run container
docker run -it --rm \
  -p 8888:8888 \
  -v $(pwd):/workspace \
  cbsc-strategy-dev:latest
```

---

## Post-Installation

### Verify Installation

Run the verification script to ensure everything is working:

```bash
python scripts/verify_install.py
```

Expected output:
```
✓ Python version OK (3.11.x >= 3.10)
✓ pandas
✓ numpy
✓ matplotlib
✓ All required packages importable
✓ cbsc_strategy package importable
✓ .env file exists
✓ config/config.yaml exists
✓ Basic functionality tests passed

Installation verified successfully!
```

### Start Jupyter Lab

```bash
# Activate environment first
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate.bat  # Windows

# Start Jupyter Lab
jupyter lab

# Or with specific options
jupyter lab --ip=127.0.0.1 --port=8888 --no-browser
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=cbsc_strategy --cov-report=html
```

---

## Configuration

### Environment Variables (.env)

Copy `.env.template` to `.env` and configure:

```bash
# API Keys
ALPHA_VANTAGE_KEY=your_key_here
POLYGON_API_KEY=your_key_here

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cbsc_strategy
POSTGRES_USER=cbsc_user
POSTGRES_PASSWORD=your_password

# Features
ENABLE_TA_LIB=true
ENABLE_ML_PREDICTIONS=false
```

### Application Configuration (config/config.yaml)

Main configuration file for the framework:

```yaml
# Data source
data:
  default_source: "yfinance"
  cache:
    enabled: true
    directory: "./data/cache"

# Backtest settings
backtest:
  initial_capital: 100000
  commission:
    type: "percent"
    value: 0.103

# Indicators
indicators:
  registry: "./config/indicators.yaml"

# Logging
logging:
  level: "INFO"
  file: "logs/cbsc.log"
```

### Indicator Registry (config/indicators.yaml)

Defines all available indicators with parameters. See [indicators documentation](docs/INDICATORS.md) for details.

---

## Troubleshooting

### Common Issues

#### Python Version Too Old

**Error:** `Python 3.10+ required`

**Solution:**
```bash
# Install Python 3.11 using pyenv (macOS/Linux)
brew install pyenv
pyenv install 3.11.7
pyenv global 3.11.7

# Or download from python.org (Windows)
# https://www.python.org/downloads/
```

#### TA-Lib Installation Fails

**Error:** `ta-lib installation failed`

**Solution (macOS):**
```bash
brew install ta-lib
pip install ta-lib
```

**Solution (Linux/Ubuntu):**
```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install ta-lib
```

**Solution (Windows):**
Download pre-built wheel from: https://github.com/cgohlke/talib-builds/releases

#### Import Errors

**Error:** `ModuleNotFoundError: No module named 'cbsc_strategy'`

**Solution:**
```bash
# Install package in editable mode
pip install -e .

# Or ensure virtual environment is activated
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate.bat  # Windows
```

#### Permission Errors

**Error:** `Permission denied when writing to logs/`

**Solution:**
```bash
# Create logs directory with proper permissions
mkdir -p logs
chmod 755 logs
```

#### Jupyter Lab Won't Start

**Error:** `Port 8888 already in use`

**Solution:**
```bash
# Use different port
jupyter lab --port=8889

# Or kill existing process
lsof -ti:8888 | xargs kill -9  # Linux/macOS
netstat -ano | findstr :8888  # Windows
```

### Getting Help

If you encounter issues not covered here:

1. **Check logs:** `logs/cbsc.log`
2. **Run verification:** `python scripts/verify_install.py`
3. **Check dependencies:** `pip list`
4. **GitHub Issues:** https://github.com/cbsc/cbsc-strategy-workflow/issues
5. **Documentation:** https://github.com/cbsc/cbsc-strategy-workflow/docs

---

## Next Steps

After successful installation:

1. **Explore examples:** `notebooks/research/`
2. **Read documentation:** `docs/`
3. **Run first backtest:** See Quick Start Guide
4. **Join community:** Discord/Slack link

---

## Uninstallation

To remove the CBSC Strategy Workflow:

```bash
# Deactivate environment
deactivate

# Remove virtual environment
rm -rf .venv

# Remove package installation
pip uninstall cbsc-strategy-workflow

# Remove data (optional)
rm -rf data/ logs/ results/

# Remove Docker images (if using Docker)
docker-compose -f docker/docker-compose.ds.yml down -v
docker rmi cbsc-strategy-dev:latest
```

---

**Last Updated:** 2026-01-11
**Version:** 0.1.0
