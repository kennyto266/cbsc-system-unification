# CBSC Quantitative Trading System - Essential Commands

## Development and Testing Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv310
.venv310\Scripts\activate

# Install comprehensive dependencies
pip install -r requirements_comprehensive.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

### Core System Entry Points
```bash
# Start full dashboard with all features
python run_full_dashboard.py

# Start simple dashboard interface
python simple_web_dashboard.py

# Start PowerShell script for server
.\scripts\start_server.ps1

# Run CBSC parameter optimization
python cbsc_parameter_optimizer.py

# Run aggressive CBSC optimization
python aggressive_cbsc_parameter_optimizer.py

# Run complete CBSC strategies optimization
python complete_cbsc_strategies_optimizer.py
```

### CBSC Strategy Development
```bash
# Run CBSC demonstration
python run_cbsc_demo.py

# Run simple CBSC demo
python simple_cbsc_demo.py

# Run optimal CBSC strategy
python optimal_cbsc_strategy.py

# Run complete real CBSC backtest
python complete_real_cbsc_backtest.py

# Run professional CBSC analysis
python professional_cbsc_analysis.py

# Run English CBSC analysis
python cbsc_english_analysis.py
```

### Marimo Interactive Laboratory
```bash
# Run Marimo production system
python cbsc_marimo_production.py

# Run Marimo development versions
python cbsc_lab.py
python cbsc_final_lab.py
python cbsc_working_lab.py
python cbsc_simple_lab.py
```

### Testing Commands
```bash
# Run all CBSC tests
python run_cbsc_tests.py

# Run comprehensive CBSC tests
python test_cbsc_comprehensive.py

# Run CBSC unit tests
python test_cbsc_unit_tests.py

# Run CBSC integration tests
python test_cbsc_integration.py

# Run CBSC performance tests
python test_cbsc_performance.py

# Run CBSC risk tests
python test_cbsc_risk.py

# Run complete system tests
python complete_system_functionality_test.py

# Run security tests
python validate_security_fixes.py
```

### Frontend Development
```bash
# Open frontend interface in browser
start frontend_interface.html

# Run complete frontend system
python complete_frontend_system.py

# Test frontend integration
python frontend_integration_verification.py
```

### Data Processing and Analysis
```bash
# Run data loader
python data_loader.py

# Run signal generator
python signal_generator.py

# Run performance analyzer
python performance_analyzer.py

# Run strategy dashboard
python strategy_performance_dashboard.py

# Run CBSC results summary
python cbsc_results_summary.py

# Run CBSC performance report
python cbsc_performance_report.py
```

### System Validation and Performance
```bash
# Validate system performance
python validate_memory_performance.py

# Validate optimization results
python validate_optimization_results.py

# Run comprehensive system validation
python comprehensive_system_validation.py

# Run core functionality verification
python core_functionality_verification.py

# Run simple system test
python simple_system_test.py

# Run simple verification
python simple_verification.py
```

### GPU and Performance Testing
```bash
# Test GPU integration
python test_gpu_integration.py

# Test GPU optimizer
python test_gpu_optimizer.py

# Test GPU simple
python test_gpu_simple.py

# Run GPU accelerated backtest
python gpu_accelerated_0700_backtest.py

# Run GPU non-price TA engine
python gpu_nonprice_0700_backtest.py
```

### VectorBT and Advanced Analytics
```bash
# Run enhanced VectorBT analysis
python enhanced_vectorbt_analysis.py

# Run fixed VectorBT analysis
python fixed_vectorbt_analysis.py

# Run VectorBT GPU acceleration implementation
python VECTORBT_GPU_ACCELERATION_IMPLEMENTATION_REPORT.py

# Test VectorBT integration
python tests/test_vectorbt_enhancement/
```

### Configuration and Setup
```bash
# Test basic phase1 functionality
python basic_phase1_test.py

# Test simple security
python simple_security_test.py

# Run quick mock data replacement
python quick_mock_replacement.py

# Run configuration manager
python config/config_manager.py

# Test simplified system
python simplified_system_integrity_test.py
```

### Monitoring and Debugging
```bash
# Run real-time performance monitor
python real_time_performance_monitor.py

# Debug GPU RSI
python debug_gpu_rsi.py

# Test system capability
python system_capability_report.json

# Run Telegram alert system
python telegram_alert_system.py
```

## Development Workflow Commands

### Code Quality and Formatting
```bash
# Format code with Black
black src/ tests/

# Lint code with Flake8
flake8 src/ tests/

# Type checking with MyPy
mypy src/

# Run all code quality checks
pytest --black --flake8 --mypy src/
```

### Git Workflow
```bash
# Check git status
git status

# Add changes
git add .

# Commit changes
git commit -m "Commit message"

# Push changes
git push origin main

# Pull latest changes
git pull origin main
```

### Testing and Coverage
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/

# Generate coverage report
pytest --cov=src --cov-report=html tests/

# Run tests with coverage
pytest --cov=src --cov-report=term-missing tests/
```

### Database and Data Management
```bash
# Backup data
python backup_recovery.py

# Test database connection
python database.py

# Test data providers
python data_providers.py

# Test adapters
python src/data_adapters/data_service.py
```

## Production Deployment Commands

### Environment Configuration
```bash
# Copy environment template
cp .env.template .env

# Edit environment file
notepad .env

# Test configuration
python production_config.py

# Validate production setup
python validate_all_fixes.py
```

### Performance Monitoring
```bash
# Run system monitoring
python src/monitoring/cpu_performance_monitor.py

# Test non-price metrics
python src/monitoring/non_price_metrics.py

# Monitor real-time strategy
python src/monitoring/real_time_strategy_monitor.py
```

### Security and Validation
```bash
# Validate security fixes
python validate_security_fixes_windows.py

# Test input validation fixes
python src/security/test_input_validation_fixes.py

# Test SQL injection protection
python src/security/test_sql_injection_protection.py

# Run security audit
python SECURITY_VULNERABILITY_FIX_REPORT.md
```

## Key File Locations

### Main System Files
- `run_full_dashboard.py` - Primary system entry point
- `cbsc_parameter_optimizer.py` - CBSC optimization engine
- `src/dashboard/dashboard_ui.py` - FastAPI dashboard
- `cbsc_marimo_production.py` - Marimo laboratory
- `frontend_interface.html` - Standalone frontend

### Configuration Files
- `requirements_comprehensive.txt` - All dependencies
- `config/app_config.json` - Application configuration
- `.env.template` - Environment variables template
- `pytest.ini` - Test configuration

### Data Files
- `data/` - Historical data storage
- `production_data/` - Production data
- `warrant_sentiment_*.csv` - CBSC sentiment data

### Test Files
- `tests/` - All test suites
- `test_cbsc_*.py` - CBSC-specific tests
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests

These commands cover all major aspects of the CBSC quantitative trading system development, testing, and deployment workflow.