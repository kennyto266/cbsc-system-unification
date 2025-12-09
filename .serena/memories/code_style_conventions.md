# CBSC Quantitative Trading System - Code Style and Conventions

## General Code Style

### Python Standards
- **Python Version**: 3.10+ (optimized for Windows)
- **Style Guide**: PEP 8 with minor adaptations
- **Line Length**: 88 characters (Black default)
- **Encoding**: UTF-8
- **Indentation**: 4 spaces (no tabs)

### Naming Conventions

#### Variables and Functions
```python
# Use snake_case for variables and functions
rsi_period = 14
sentiment_threshold = 0.7
def calculate_cbsc_strategy():
    pass

# Descriptive names preferred
total_return_percentage = 0.15  # Good
trp = 0.15  # Avoid abbreviations
```

#### Classes and Constants
```python
# Use PascalCase for classes
class CBSCStrategyOptimizer:
    pass

class WarrantSentimentModel:
    pass

# Use UPPER_CASE for constants
DEFAULT_RSI_PERIOD = 14
MAX_PARAMETER_COMBINATIONS = 1000
RISK_FREE_RATE = 0.02
```

#### File and Module Names
```python
# Use snake_case for files
cbsc_parameter_optimizer.py
strategy_performance_dashboard.py
enhanced_backtest_engine.py

# Module imports at top
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
```

### Type Hints
```python
# Comprehensive type hints for all public functions
from typing import Dict, List, Optional, Tuple, Any, Union

def calculate_strategy_metrics(
    returns: pd.Series,
    risk_free_rate: float = 0.02
) -> Dict[str, float]:
    """Calculate strategy performance metrics."""
    pass

class CBSCPortfolioPosition(BaseModel):
    contract: CBSCContract
    quantity: int
    entry_price: float
    entry_date: datetime
```

### Docstrings and Comments
```python
def sentiment_momentum_strategy(
    data: pd.DataFrame, 
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate sentiment momentum strategy signals.
    
    Args:
        data: DataFrame with OHLCV and sentiment data
        params: Strategy parameters including windows and thresholds
        
    Returns:
        Dictionary containing:
        - signals: Trading signals (buy/sell/hold)
        - metrics: Performance metrics
        - positions: Position sizing information
        
    Raises:
        ValueError: If required data columns are missing
        
    Example:
        >>> params = {'sentiment_short_window': 5, 'momentum_threshold': 0.1}
        >>> result = sentiment_momentum_strategy(data, params)
    """
    # Implementation details...
```

## Project-Specific Conventions

### CBSC Data Models
```python
# Use Pydantic models for data validation
from pydantic import BaseModel, Field, validator

class CBSCContract(BaseModel):
    """CBSC contract specification model."""
    
    ticker: str = Field(..., description="牛熊證代碼")
    cbsc_type: CBSCType = Field(..., description="CBSC類型")
    call_price: float = Field(..., gt=0, description="收回價")
    
    @validator('maturity_date')
    def validate_maturity_date(cls, v, values):
        if 'issue_date' in values and v <= values['issue_date']:
            raise ValueError('到期日期必須在發行日期之後')
        return v
```

### Strategy Implementation Pattern
```python
class CBSCStrategyBase:
    """Base class for all CBSC strategies."""
    
    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.validate_parameters()
    
    def validate_parameters(self) -> None:
        """Validate strategy parameters."""
        raise NotImplementedError
    
    def calculate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Calculate trading signals."""
        raise NotImplementedError
    
    def backtest_strategy(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run backtest with strategy parameters."""
        signals = self.calculate_signals(data)
        return self._calculate_performance_metrics(signals, data)
```

### Error Handling
```python
# Use specific exceptions and meaningful error messages
class CBSCTradeExecutionError(Exception):
    """Exception raised when CBSC trade execution fails."""
    pass

def execute_cbsc_trade(signal: CBSCStrategySignal) -> bool:
    try:
        # Trade execution logic
        return True
    except ValueError as e:
        logger.error(f"Invalid signal parameters: {e}")
        raise CBSCTradeExecutionError(f"Invalid signal: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in trade execution: {e}")
        raise CBSCTradeExecutionError(f"Execution failed: {e}")
```

### Logging Conventions
```python
import logging

# Use structured logging with context
logger = logging.getLogger(__name__)

def process_strategy_data(data: pd.DataFrame, strategy_name: str) -> Dict:
    logger.info(f"Processing strategy data for {strategy_name}", 
                extra={'strategy': strategy_name, 'data_points': len(data)})
    
    try:
        result = calculate_strategy_metrics(data)
        logger.info(f"Strategy calculation completed", 
                   extra={'strategy': strategy_name, 'success': True})
        return result
    except Exception as e:
        logger.error(f"Strategy calculation failed: {e}", 
                    extra={'strategy': strategy_name, 'error': str(e)})
        raise
```

## Testing Conventions

### Test File Organization
```python
# Test files should be named: test_[module_name].py
# test_cbsc_models.py
# test_parameter_optimizer.py
# test_backtest_engine.py

import pytest
from unittest.mock import Mock, patch
import pandas as pd

class TestCBSCParameterOptimizer:
    """Test suite for CBSC parameter optimizer."""
    
    @pytest.fixture
    def sample_data(self):
        """Fixture providing sample data for testing."""
        return pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=100),
            'Afternoon_Close': np.random.randn(100).cumsum() + 100,
            'Bull_Ratio': np.random.random(100),
            'Bull_Turnover_HKD': np.random.randint(1000000, 10000000, 100)
        })
    
    def test_parameter_space_definition(self):
        """Test parameter space definition."""
        optimizer = CBSCParameterOptimizer()
        space = optimizer.define_parameter_space()
        
        assert 'sentiment_momentum' in space
        assert 'volume_reversal' in space
        assert isinstance(space['sentiment_momentum']['sentiment_short_window'], list)
```

### Mock and Fixture Usage
```python
# Use pytest fixtures for reusable test data
@pytest.fixture
def mock_cbsc_contract():
    return CBSCContract(
        ticker="73888.HK",
        underlying_ticker="0700.HK",
        cbsc_type=CBSCType.BULL,
        call_price=180.0,
        strike_price=280.0
    )

# Use mocks for external dependencies
@patch('src.data_adapters.cbsc_adapter.requests.get')
def test_data_loading(mock_get):
    mock_get.return_value.json.return_value = {'data': 'test'}
    adapter = CBSCDataAdapter()
    result = adapter.fetch_data()
    assert result is not None
```

## Database and API Conventions

### API Endpoint Patterns
```python
# RESTful API naming conventions
@app.get("/api/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get strategy by ID."""
    pass

@app.post("/api/strategies/{strategy_id}/optimize")
async def optimize_strategy(strategy_id: str, params: OptimizationParameters):
    """Optimize strategy with given parameters."""
    pass

@app.get("/api/cbsc/contracts")
async def list_cbsc_contracts(
    page: int = 1,
    limit: int = 20,
    cbsc_type: Optional[CBSCType] = None
):
    """List CBSC contracts with pagination."""
    pass
```

### Configuration Management
```python
# Use environment-specific configurations
class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_host: str = Field(default="localhost", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # CBSC Configuration
    cbsc_data_source: str = Field(default="hkex", env="CBSC_DATA_SOURCE")
    max_parameter_combinations: int = Field(default=1000, env="MAX_PARAM_COMBINATIONS")
    
    class Config:
        env_file = ".env"
```

## Performance Conventions

### Data Processing
```python
# Use vectorized operations with pandas/numpy
def calculate_rsi_vectorized(prices: pd.Series, period: int = 14) -> pd.Series:
    """Vectorized RSI calculation for performance."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.where(loss != 0, 1)
    return 100 - (100 / (1 + rs))

# Avoid loops in favor of vectorized operations
# Bad:
# for i in range(len(data)):
#     result[i] = calculate_indicator(data[i])

# Good:
# result = data.rolling(window).apply(calculate_indicator)
```

### Memory Management
```python
# Use context managers for resource cleanup
with pd.read_csv('large_dataset.csv', chunksize=10000) as reader:
    for chunk in reader:
        process_chunk(chunk)
        del chunk  # Explicit cleanup for large datasets

# Use generators for large datasets
def generate_trading_signals(data: pd.DataFrame):
    """Generator for memory-efficient signal processing."""
    for date, row in data.iterrows():
        yield calculate_signal(row)
```

## Security Conventions

### Input Validation
```python
# Validate all external inputs
from pydantic import validator

class TradeRequest(BaseModel):
    symbol: str
    quantity: int
    price: float
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^\d{4}\.HK$', v):
            raise ValueError('Invalid Hong Kong stock symbol format')
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0 or v > 1000000:
            raise ValueError('Quantity must be positive and reasonable')
        return v
```

### Error Handling
```python
# Never expose sensitive information in error messages
def connect_to_database():
    try:
        return DatabaseConnection(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseConnectionError("Unable to connect to database")  # Don't expose details
```

## Documentation Conventions

### Code Documentation
```python
# Use meaningful comments that explain 'why' not 'what'
# Bad:
# increment counter by 1
counter += 1

# Good:
# Account for weekend gap in market data
counter += 1

# Document complex algorithms with step-by-step comments
def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio for return series.
    
    Steps:
    1. Calculate excess returns by subtracting risk-free rate
    2. Compute annualized volatility using 252 trading days
    3. Calculate annualized returns
    4. Compute Sharpe ratio as returns/volatility
    """
    excess_returns = returns - risk_free_rate / 252
    volatility = excess_returns.std() * np.sqrt(252)
    annual_return = excess_returns.mean() * 252
    return annual_return / volatility if volatility > 0 else 0
```

These conventions ensure code consistency, readability, and maintainability across the CBSC quantitative trading system.