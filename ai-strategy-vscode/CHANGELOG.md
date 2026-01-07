# Changelog

All notable changes to the AI Strategy Assistant extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-07

### Added
- Initial release of AI Strategy Assistant for VSCode
- GLM 4.7 AI integration for strategy code generation
- Interactive chat interface with AI assistant
- Jupyter notebook template system with pre-built strategies
- Strategy execution and testing capabilities
- CBSC system integration for deploying strategies
- One-click notebook creation and code insertion
- Real-time AI assistance during strategy development

### Features
- Natural language to Python code translation
- Pre-built templates for common strategies:
  - Breakout strategy with moving average confirmation
  - Mean reversion strategy using Bollinger Bands
- Notebook execution via Jupyter integration
- Strategy deployment to existing CBSC backend
- Configuration management through VSCode settings
- Comprehensive error handling and validation

### Technical
- TypeScript-based VSCode extension
- Integration with GLM-4 Plus API
- FastAPI backend service for AI operations
- Support for Jupyter notebook format (nbformat 4.2)
- Async/await patterns for API calls
- Comprehensive test coverage with Jest and pytest

## [Unreleased]

### Planned
- Additional strategy templates (momentum, arbitrage, pairs trading)
- Strategy backtesting visualization
- Performance metrics dashboard
- Multi-language support
- Custom prompt templates
- Strategy versioning and rollback
