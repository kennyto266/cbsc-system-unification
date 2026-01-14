# Changelog

All notable changes to the CBSC Strategy SDK will be documented in this file.

## [1.0.0] - 2026-01-11

### Added
- Strategy workspace with unified interface for strategy development
- Historical data retrieval with caching support
- Real-time data streaming capabilities
- Vectorized backtesting engine with progress tracking
- Parameter optimization framework
- Performance metrics library (Sharpe, Sortino, max drawdown, etc.)
- Circular buffer for efficient data handling
- Tick data buffer with OHLCV aggregation
- Configuration management with environment variable support
- Comprehensive error handling and validation
- Pydantic models for data validation
- Type hints throughout the codebase

### Changed
- Improved Pydantic model support in data buffer operations
- Relaxed validation for better configuration flexibility
- Updated to use modern Python type annotations
- Enhanced test coverage for core modules

### Fixed
- Fixed Pydantic model serialization in to_dataframe()
- Corrected Enum syntax errors in data adapters
- Fixed indentation issues in message queue
- Resolved test assertion failures
- Fixed time-based aggregation test expectations

### Security
- No critical vulnerabilities found
- All 201 core tests passing

## [0.1.0] - 2025-12-15

### Added
- Initial release
- Basic workspace functionality
