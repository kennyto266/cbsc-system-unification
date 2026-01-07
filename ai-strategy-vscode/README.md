# AI Strategy Assistant for VSCode

> Create, test, and deploy quantitative trading strategies with GLM 4.7 AI directly in VSCode.

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/your-org/ai-strategy-tool)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![VSCode](https://img.shields.io/badge/VSCode-1.85.0+-blue.svg)](https://code.visualstudio.com/)

## Overview

AI Strategy Assistant is a VSCode extension that leverages GLM 4.7 AI to help you create, test, and deploy quantitative trading strategies in Jupyter notebooks. Simply describe your strategy idea in plain English, and get working Python code instantly.

### Key Features

- 🤖 **AI-Powered Code Generation**: Transform natural language descriptions into executable Python code
- 💬 **Interactive Chat Interface**: Real-time assistance from GLM 4.7 AI
- 📓 **Jupyter Notebook Integration**: Seamless workflow with Jupyter notebooks
- 🚀 **One-Click Execution**: Run and test strategies directly in VSCode
- 🎯 **Pre-built Templates**: Start with proven strategy templates (breakout, mean reversion, etc.)
- 🔄 **CBSC Integration**: Deploy strategies to the CBSC trading system
- ⚡ **Instant Feedback**: Visualize results and performance metrics

## Quick Start

### 1. Installation

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Install extension in VSCode
code . --install-extension ai-strategy-assistant-0.1.0.vsix
```

Or install from VSCode Marketplace:
1. Open VSCode
2. Press `Ctrl+Shift+X` to open Extensions
3. Search for "AI Strategy Assistant"
4. Click Install

### 2. Configuration

Open VSCode Settings (`Ctrl+,`) and configure:

```json
{
  "aiStrategy.glmApiKey": "your_glm_api_key_here",
  "aiStrategy.glmModel": "glm-4-plus",
  "aiStrategy.serviceUrl": "http://localhost:8000"
}
```

**Get your GLM API key:** [https://open.bigmodel.cn/](https://open.bigmodel.cn/)

### 3. Start Creating

1. Press `Ctrl+Shift+P`
2. Type "Create Strategy Notebook"
3. Open the AI Chat panel
4. Describe your strategy: *"Create a 20-day moving average crossover strategy with volume confirmation"*
5. Click "Insert into Notebook" to add generated code
6. Execute and see results!

## Usage Examples

### Moving Average Crossover

```
Create a moving average crossover strategy:
- Buy when 20-day MA crosses above 50-day MA
- Sell when 20-day MA crosses below 50-day MA
- Add 2% stop loss and 5% take profit
```

### Mean Reversion with Bollinger Bands

```
Create a mean reversion strategy:
- Use Bollinger Bands (20-day, 2 standard deviations)
- Buy when price touches lower band
- Sell when price returns to mean
- Position size: 10% of portfolio
```

### Breakout Strategy

```
Create a breakout strategy:
- Buy when price breaks above 20-day high
- Use volume confirmation (1.5x average)
- Trail stop at 2x ATR
```

## Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| AI Strategy: Create Strategy Notebook | - | Create a new Jupyter notebook for strategy development |
| AI Strategy: Open AI Chat | - | Open the AI chat panel for strategy assistance |
| AI Strategy: Insert into Notebook | - | Generate and insert strategy code into current notebook |

## Extension Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `aiStrategy.glmApiKey` | string | - | Your GLM API key (required) |
| `aiStrategy.glmModel` | string | "glm-4-plus" | GLM model to use for generation |
| `aiStrategy.serviceUrl` | string | "http://localhost:8000" | Backend service URL |
| `aiStrategy.maxTokens` | number | 2000 | Maximum tokens for AI responses |
| `aiStrategy.temperature` | number | 0.7 | AI creativity level (0-1) |

## Architecture

```
┌─────────────────────┐
│  VSCode Extension   │
│  (TypeScript)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  AI Service         │
│  (FastAPI + GLM)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Jupyter Notebooks  │
│  (Python)           │
└─────────────────────┘
```

## File Structure

```
ai-strategy-vscode/
├── src/
│   ├── extension.ts           # Main extension entry point
│   ├── chatProvider.ts        # AI chat interface
│   ├── notebookExecutor.ts    # Notebook execution
│   └── api/
│       └── glmClient.ts       # GLM API client
├── package.json               # Extension manifest
├── tsconfig.json              # TypeScript config
├── CHANGELOG.md               # Version history
└── README.md                  # This file
```

## Development

### Prerequisites

- Node.js 18+
- Python 3.10+
- GLM API key

### Setup

```bash
# Install dependencies
npm install

# Compile in watch mode
npm run watch

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Package extension
npm run package
```

### Testing

```bash
# Unit tests
npm test

# Integration tests
npm run test:e2e

# Coverage report
npm run test:coverage
```

## Troubleshooting

### Extension not activating

1. Check VSCode version (must be 1.85.0+)
2. Reload VSCode window
3. Check Developer Console for errors (`Help` → `Toggle Developer Tools`)

### GLM API errors

- Verify your API key is correct
- Check you have sufficient quota
- Ensure network connectivity to `open.bigmodel.cn`

### Notebook execution fails

- Ensure Jupyter is installed: `pip install jupyter`
- Install IPython kernel: `python -m ipykernel install --user`
- Check Python kernel is available: `jupyter kernelspec list`

For more troubleshooting tips, see the [complete setup guide](../docs/setup-guide.md).

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](../docs/setup-guide.md)
- 🐛 [Issue Tracker](https://github.com/your-org/ai-strategy-tool/issues)
- 💬 [Discussions](https://github.com/your-org/ai-strategy-tool/discussions)
- 📧 Email: support@example.com

## Acknowledgments

- Built with [VSCode Extension API](https://code.visualstudio.com/api)
- Powered by [GLM-4 Plus](https://open.bigmodel.cn/) from 智譜AI
- Inspired by the CBSC quantitative trading community

---

**Made with ❤️ for quantitative traders and strategy developers**
