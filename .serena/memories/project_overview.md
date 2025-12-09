# CBSC Quantitative Trading System - Project Overview

## Project Purpose
This is a sophisticated AI-powered quantitative trading system specializing in CBSC (Callable Bull/Bear Contract) trading strategies for the Hong Kong market. The system combines advanced sentiment analysis, technical indicators, and multi-agent AI architecture to deliver professional-grade trading analytics and strategy development.

## Key Features
- **Multi-Agent AI System**: 7 specialized AI agents collaborating for quantitative trading
- **CBSC Sentiment Analysis**: 4 advanced sentiment strategies (Direct RSI, Sentiment Momentum, Composite Index, Volatility-Adjusted)
- **Technical Analysis Engine**: RSI, MACD, KDJ, Bollinger Bands with custom parameter optimization
- **Real-time Data Integration**: Hong Kong government APIs + real-time market data
- **Interactive Parameter Optimization**: 0-300 parameter space search with multi-process parallel processing
- **Professional Backtesting**: Enhanced backtest engine with transaction costs, slippage, and risk metrics
- **Web Dashboard**: FastAPI + WebSocket real-time monitoring and visualization
- **Marimo Integration**: Interactive notebook-based strategy laboratory

## Technology Stack

### Core Technologies
- **Language**: Python 3.10+ (Windows optimized)
- **Data Processing**: Pandas, NumPy, SciPy
- **Quantitative Finance**: VectorBT, TA-Lib, QuantStats
- **Web Framework**: FastAPI, WebSocket
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Notebook**: Marimo (interactive Python notebooks)
- **Database**: SQLite (with Redis for caching)

### Key Dependencies
- vectorbt>=0.25.0 (backtesting engine)
- pandas>=2.0.0, numpy>=1.24.0 (data processing)
- plotly>=5.15.0 (visualization)
- fastapi>=0.100.0 (web API)
- marimo (interactive notebooks)

## Architecture Overview

### Data Layer
- **CBSC Data**: Real-time warrant sentiment data from Hong Kong exchanges
- **Government APIs**: 6 HKMA official data sources (HIBOR, exchange rates, monetary base)
- **Market Data**: Real-time stock price data via multiple adapters

### Strategy Layer
- **4 CBSC Sentiment Strategies**: Direct RSI, Sentiment Momentum, Composite Index, Volatility-Adjusted
- **Technical Indicators**: RSI, MACD, KDJ, Bollinger Bands
- **Parameter Optimization**: 0-300 range parameter search with multi-core processing

### Application Layer
- **Multi-Agent System**: 7 specialized AI agents (Data Scientist, Portfolio Manager, Risk Analyst, etc.)
- **Backtesting Engine**: Enhanced engine with transaction costs and realistic market conditions
- **Real-time Dashboard**: WebSocket-based monitoring with Chart.js visualization

### Presentation Layer
- **Web Dashboard**: FastAPI + HTML/CSS/JS interface
- **Marimo Laboratory**: Interactive parameter tuning and strategy development
- **REST API**: Comprehensive API for external integrations

## Current Implementation Status

### Completed Components ✅
- Complete CBSC data models and sentiment analysis framework
- 4 advanced CBSC sentiment strategies with parameter optimization
- Enhanced backtesting engine with realistic market conditions
- FastAPI web dashboard with real-time WebSocket updates
- Marimo integration for interactive strategy development
- Multi-agent AI system architecture
- Hong Kong government API integration (6 data sources)

### Key Files and Modules
- `src/models/cbsc_models.py`: CBSC data models and sentiment analysis
- `cbsc_parameter_optimizer.py`: Complete parameter optimization system
- `src/backtest/enhanced_backtest_engine.py`: Professional backtesting engine
- `src/dashboard/dashboard_ui.py`: FastAPI dashboard implementation
- `cbsc_marimo_production.py`: Marimo interactive laboratory
- `frontend_interface.html`: Standalone web interface

## Development Environment
- **Platform**: Windows 10/11 (optimized for Windows)
- **Python**: 3.10+ (recommended 3.11)
- **Performance**: 32-core CPU support, 125.6GB RAM optimization
- **Storage**: JSON file system + CSV historical archives
- **Monitoring**: Prometheus + Grafana integration ready

## Entry Points
1. **Full Dashboard**: `python run_full_dashboard.py`
2. **Simple Dashboard**: `python simple_web_dashboard.py`
3. **CBSC Parameter Optimizer**: `python cbsc_parameter_optimizer.py`
4. **Marimo Laboratory**: `python cbsc_marimo_production.py`
5. **Frontend Interface**: Open `frontend_interface.html` in browser

## Testing and Validation
- Comprehensive test suite for CBSC strategies
- Performance benchmarking (230+ strategies/second processing speed)
- Real data validation with Hong Kong market data
- Security testing and vulnerability assessments

This system represents a world-first implementation of CBSC-focused quantitative trading strategies, combining advanced sentiment analysis with professional-grade backtesting and real-time monitoring capabilities.