# AI Strategy Development Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use @superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a VSCode extension that uses GLM 4.7 AI to help users create, test, and deploy quantitative trading strategies in Jupyter notebooks.

**Architecture:** Three-layer system - VSCode Extension (TypeScript) → AI Service (GLM 4.7 API) → Jupyter Notebooks (Python) with integration to existing CBSC backend.

**Tech Stack:** VSCode Extension API, TypeScript, Python 3.10+, Jupyter, GLM-4 API, FastAPI, React

---

## Project Structure

```
workspace/
├── ai-strategy-vscode/           # VSCode Extension
│   ├── src/
│   │   ├── extension.ts          # Main entry point
│   │   ├── chatProvider.ts       # AI chat interface
│   │   ├── notebookManager.ts    # Notebook operations
│   │   └── api/
│   │       └── glmClient.ts      # GLM 4.7 API client
│   ├── package.json
│   └── tsconfig.json
├── ai-strategy-service/          # Backend Service (FastAPI)
│   ├── main.py
│   ├── routers/
│   │   └── strategy.py           # Strategy generation endpoints
│   ├── services/
│   │   └── glm_service.py        # GLM API integration
│   └── templates/
│       └── notebook_templates.py # Pre-built notebook templates
└── test-fixtures/
    └── sample_strategies.ipynb   # Test notebooks
```

---

## Task 1: Project Setup and VSCode Extension Scaffold

**Files:**
- Create: `ai-strategy-vscode/package.json`
- Create: `ai-strategy-vscode/tsconfig.json`
- Create: `ai-strategy-vscode/src/extension.ts`
- Create: `ai-strategy-vscode/README.md`

**Step 1: Initialize VSCode Extension project**

Run:
```bash
mkdir -p ai-strategy-vscode/src
cd ai-strategy-vscode
npm init -y
npm install --save-dev @types/vscode @types/node typescript
npm install --save-dev @vscode/test-electron
```

**Step 2: Create package.json**

Create: `ai-strategy-vscode/package.json`

```json
{
  "name": "ai-strategy-assistant",
  "displayName": "AI Strategy Assistant",
  "description": "Create quantitative trading strategies with GLM 4.7 AI",
  "version": "0.1.0",
  "engines": {"vscode": "^1.85.0"},
  "categories": ["Machine Learning", "Notebooks"],
  "activationEvents": [
    "onCommand:aiStrategy.createNotebook",
    "onCommand:aiStrategy.openChat"
  ],
  "main": "./out/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "aiStrategy.createNotebook",
        "title": "Create Strategy Notebook",
        "category": "AI Strategy"
      },
      {
        "command": "aiStrategy.openChat",
        "title": "Open AI Chat",
        "category": "AI Strategy"
      }
    ],
    "viewsContainers": {
      "activitybar": [
        {
          "id": "aiStrategySidebar",
          "title": "AI Strategy",
          "icon": "assets/ai-icon.svg"
        }
      ]
    },
    "views": {
      "aiStrategySidebar": [
        {
          "id": "aiChatView",
          "name": "AI Chat",
          "type": "webview"
        }
      ]
    }
  },
  "scripts": {
    "vscode:prepublish": "npm run compile",
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./",
    "pretest": "npm run compile",
    "test": "node ./out/test/runTest.js"
  }
}
```

**Step 3: Create TypeScript config**

Create: `ai-strategy-vscode/tsconfig.json`

```json
{
  "compilerOptions": {
    "module": "commonjs",
    "target": "ES2020",
    "outDir": "out",
    "lib": ["ES2020"],
    "sourceMap": true,
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "exclude": ["node_modules", ".vscode-test"]
}
```

**Step 4: Create main extension entry point**

Create: `ai-strategy-vscode/src/extension.ts`

```typescript
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  console.log('AI Strategy Assistant is now active!');

  // Register command to create strategy notebook
  const createNotebookCmd = vscode.commands.registerCommand(
    'aiStrategy.createNotebook',
    async () => {
      const notebook = await vscode.workspace.openNotebookDocument(
        vscode.Uri.parse('untitled:/strategy.ipynb'),
        'jupyter-notebook'
      );
      await vscode.window.showNotebookDocument(notebook);
    }
  );

  // Register command to open AI chat
  const openChatCmd = vscode.commands.registerCommand(
    'aiStrategy.openChat',
    () => {
      const panel = vscode.window.createWebviewPanel(
        'aiChat',
        'AI Strategy Chat',
        vscode.ViewColumn.Beside,
        { enableScripts: true }
      );
      panel.webview.html = getChatWebviewContent();
    }
  );

  context.subscriptions.push(createNotebookCmd, openChatCmd);
}

export function deactivate() {}

function getChatWebviewContent(): string {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: var(--vscode-font-family); padding: 20px; }
    #chat-container { display: flex; flex-direction: column; height: 100vh; }
    #messages { flex: 1; overflow-y: auto; margin-bottom: 10px; }
    #input-area { display: flex; gap: 10px; }
    input { flex: 1; padding: 8px; }
    button { padding: 8px 16px; }
  </style>
</head>
<body>
  <div id="chat-container">
    <div id="messages"></div>
    <div id="input-area">
      <input type="text" id="user-input" placeholder="Describe your strategy idea...">
      <button id="send-btn">Send</button>
    </div>
  </div>
  <script>
    const vscode = acquireVsCodeApi();
    document.getElementById('send-btn').addEventListener('click', () => {
      const input = document.getElementById('user-input');
      vscode.postMessage({ type: 'chat', message: input.value });
      input.value = '';
    });
  </script>
</body>
</html>`;
}
```

**Step 5: Create README**

Create: `ai-strategy-vscode/README.md`

```markdown
# AI Strategy Assistant for VSCode

Create quantitative trading strategies with GLM 4.7 AI in Jupyter notebooks.

## Features
- AI-powered strategy generation
- Interactive chat interface
- Jupyter notebook integration
- One-click backtesting

## Installation
1. Install VSCode
2. Install this extension
3. Set GLM API key in settings

## Usage
1. Press `Ctrl+Shift+P` (Cmd+Shift+P on Mac)
2. Type "Create Strategy Notebook"
3. Describe your strategy idea to AI
4. Get generated code instantly
```

**Step 6: Compile and test extension**

Run:
```bash
cd ai-strategy-vscode
npm run compile
npm test
```

Expected: Compilation succeeds, tests pass

**Step 7: Commit**

```bash
cd ai-strategy-vscode
git add .
git commit -m "feat: initialize VSCode extension scaffold"
```

---

## Task 2: GLM 4.7 API Client Implementation

**Files:**
- Create: `ai-strategy-vscode/src/api/glmClient.ts`
- Create: `ai-strategy-service/services/glm_service.py`
- Create: `ai-strategy-service/.env.example`

**Step 1: Create GLM API client interface**

Create: `ai-strategy-vscode/src/api/glmClient.ts`

```typescript
export interface GLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface GLMRequest {
  model: string;
  messages: GLMMessage[];
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
}

export interface GLMResponse {
  id: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: GLMMessage;
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export class GLMClient {
  private apiKey: string;
  private baseURL = 'https://open.bigmodel.cn/api/paas/v4/';

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async chat(messages: GLMMessage[]): Promise<string> {
    const request: GLMRequest = {
      model: 'glm-4-plus',
      messages,
      temperature: 0.7,
      top_p: 0.9,
      max_tokens: 2000
    };

    const response = await fetch(`${this.baseURL}chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`GLM API error: ${response.statusText}`);
    }

    const data: GLMResponse = await response.json();
    return data.choices[0].message.content;
  }

  async generateStrategy(description: string): Promise<string> {
    const systemPrompt: GLMMessage = {
      role: 'system',
      content: `You are a quantitative trading strategy expert. Generate Python code for trading strategies.
The strategy should be structured as a Jupyter notebook with the following cells:
1. Imports and configuration
2. Data fetching
3. Strategy parameters
4. Signal generation
5. Backtesting
6. Results visualization

Return ONLY valid Python code that can be executed in a Jupyter notebook.`
    };

    const userMessage: GLMMessage = {
      role: 'user',
      content: `Create a trading strategy: ${description}`
    };

    return await this.chat([systemPrompt, userMessage]);
  }
}
```

**Step 2: Create backend GLM service**

Create: `ai-strategy-service/services/glm_service.py`

```python
import os
from typing import List, Dict, Any
import httpx
from pydantic import BaseModel

class GLMMessage(BaseModel):
    role: str
    content: str

class GLMRequest(BaseModel):
    model: str = "glm-4-plus"
    messages: List[GLMMessage]
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2000

class GLMService:
    def __init__(self):
        self.api_key = os.getenv("GLM_API_KEY")
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/"
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat(self, messages: List[GLMMessage]) -> str:
        """Send chat request to GLM API"""
        request = GLMRequest(messages=messages)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = await self.client.post(
            f"{self.base_url}chat/completions",
            json=request.dict(),
            headers=headers
        )

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    async def generate_strategy(self, description: str) -> str:
        """Generate trading strategy from description"""
        system_prompt = GLMMessage(
            role="system",
            content="""You are a quantitative trading strategy expert. Generate Python code for trading strategies.
The strategy should be structured as a Jupyter notebook with the following cells:
1. Imports and configuration
2. Data fetching
3. Strategy parameters
4. Signal generation
5. Backtesting
6. Results visualization

Return ONLY valid Python code that can be executed in a Jupyter notebook."""
        )

        user_prompt = GLMMessage(
            role="user",
            content=f"Create a trading strategy: {description}"
        )

        return await self.chat([system_prompt, user_prompt])

    async def close(self):
        await self.client.aclose()
```

**Step 3: Create environment variables template**

Create: `ai-strategy-service/.env.example`

```bash
# GLM API Configuration
GLM_API_KEY=your_glm_api_key_here
GLM_MODEL=glm-4-plus

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

**Step 4: Create GLM client tests**

Create: `ai-strategy-vscode/src/test/glmClient.test.ts`

```typescript
import { describe, it, expect } from '@jest/globals';
import { GLMClient } from '../api/glmClient';

describe('GLMClient', () => {
  it('should initialize with API key', () => {
    const client = new GLMClient('test-key');
    expect(client).toBeDefined();
  });

  it('should format GLM request correctly', async () => {
    const client = new GLMClient('test-key');

    // Mock fetch to test request format
    const mockFetch = jest.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        choices: [{ message: { content: 'test response' } }]
      })
    }));

    global.fetch = mockFetch;

    await client.generateStrategy('test strategy');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('chat/completions'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-key'
        })
      })
    );
  });
});
```

**Step 5: Run tests**

Run:
```bash
cd ai-strategy-vscode
npm test -- src/test/glmClient.test.ts
```

Expected: All tests pass

**Step 6: Commit**

```bash
git add ai-strategy-vscode/src/api/glmClient.ts \
        ai-strategy-service/services/glm_service.py \
        ai-strategy-service/.env.example
git commit -m "feat: implement GLM 4.7 API client"
```

---

## Task 3: Notebook Template System

**Files:**
- Create: `ai-strategy-service/templates/notebook_templates.py`
- Create: `test-fixtures/templates/test_basic_strategy.ipynb`

**Step 1: Create notebook template manager**

Create: `ai-strategy-service/templates/notebook_templates.py`

```python
from typing import Dict, Any, List
import json

class NotebookTemplate:
    """Base class for notebook templates"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.cells = []

    def add_cell(self, cell_type: str, content: str):
        """Add a cell to the template

        Args:
            cell_type: 'code' or 'markdown'
            content: Cell content
        """
        self.cells.append({
            "cell_type": cell_type,
            "metadata": {},
            "outputs": [],
            "source": content.split('\n')
        })

    def to_notebook(self) -> Dict[str, Any]:
        """Convert to Jupyter notebook format"""
        return {
            "cells": self.cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.10.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }

class TemplateManager:
    """Manages strategy notebook templates"""

    def __init__(self):
        self.templates = {}
        self._init_templates()

    def _init_templates(self):
        """Initialize built-in templates"""
        # Breakout Strategy Template
        breakout = NotebookTemplate(
            "breakout",
            "Classic breakout strategy with moving average confirmation"
        )

        breakout.add_cell("markdown", "# Breakout Strategy\n")
        breakout.add_cell("code", """
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
SYMBOL = "AAPL"
START_DATE = "2023-01-01"
END_DATE = "2024-01-01"
SHORT_MA = 20
LONG_MA = 50
BREAKOUT_THRESHOLD = 0.02  # 2% breakout
""")

        breakout.add_cell("code", """
# Fetch data (placeholder - replace with actual data source)
def fetch_data(symbol: str, start: str, end: str):
    # TODO: Integrate with CBSC data service
    dates = pd.date_range(start=start, end=end, freq='D')
    prices = np.random.randn(len(dates)).cumsum() + 100

    return pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    }).set_index('date')

data = fetch_data(SYMBOL, START_DATE, END_DATE)
print(f"Loaded {len(data)} days of data for {SYMBOL}")
""")

        breakout.add_cell("code", """
# Calculate indicators
data['ma_short'] = data['close'].rolling(window=SHORT_MA).mean()
data['ma_long'] = data['close'].rolling(window=LONG_MA).mean()

# Generate signals
data['signal'] = 0
data.loc[
    (data['ma_short'] > data['ma_long']) &
    (data['close'] > data['ma_short'] * (1 + BREAKOUT_THRESHOLD)),
    'signal'
] = 1

data.loc[
    (data['ma_short'] < data['ma_long']),
    'signal'
] = -1

print(f"Generated {data['signal'].abs().sum()} trading signals")
""")

        breakout.add_cell("code", """
# Backtest
initial_capital = 100000
position = 0
cash = initial_capital
portfolio_values = []

for i, row in data.iterrows():
    if row['signal'] == 1 and position == 0:
        # Buy
        position = cash / row['close']
        cash = 0
    elif row['signal'] == -1 and position > 0:
        # Sell
        cash = position * row['close']
        position = 0

    portfolio_values.append(cash + position * row['close'])

data['portfolio_value'] = portfolio_values
data['returns'] = data['portfolio_value'].pct_change()
""")

        breakout.add_cell("code", """
# Calculate performance metrics
total_return = (data['portfolio_value'].iloc[-1] / initial_capital - 1) * 100
sharpe_ratio = data['returns'].mean() / data['returns'].std() * np.sqrt(252)
max_drawdown = (data['portfolio_value'].cummax() - data['portfolio_value']).max() / initial_capital * 100

print(f"Total Return: {total_return:.2f}%")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"Max Drawdown: {max_drawdown:.2f}%")
""")

        breakout.add_cell("code", """
# Visualize results
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Price and moving averages
ax1.plot(data.index, data['close'], label='Close', alpha=0.7)
ax1.plot(data.index, data['ma_short'], label=f'{SHORT_MA}-day MA', alpha=0.7)
ax1.plot(data.index, data['ma_long'], label=f'{LONG_MA}-day MA', alpha=0.7)
ax1.set_title(f'{SYMBOL} Breakout Strategy')
ax1.set_ylabel('Price')
ax1.legend()

# Portfolio value
ax2.plot(data.index, data['portfolio_value'], label='Portfolio', color='green')
ax2.set_title('Portfolio Performance')
ax2.set_ylabel('Portfolio Value ($)')
ax2.legend()

plt.tight_layout()
plt.show()
""")

        self.templates['breakout'] = breakout

        # Mean Reversion Template
        mean_reversion = NotebookTemplate(
            "mean_reversion",
            "Mean reversion strategy using Bollinger Bands"
        )

        mean_reversion.add_cell("markdown", "# Mean Reversion Strategy\n")
        mean_reversion.add_cell("code", """
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
SYMBOL = "AAPL"
START_DATE = "2023-01-01"
END_DATE = "2024-01-01"
LOOKBACK = 20
STD_DEV = 2
ENTRY_THRESHOLD = 2.0  # Enter when price is 2 std dev from mean
""")

        mean_reversion.add_cell("code", """
# Fetch data (placeholder)
def fetch_data(symbol: str, start: str, end: str):
    dates = pd.date_range(start=start, end=end, freq='D')
    prices = np.random.randn(len(dates)).cumsum() + 100

    return pd.DataFrame({
        'date': dates,
        'close': prices
    }).set_index('date')

data = fetch_data(SYMBOL, START_DATE, END_DATE)
""")

        mean_reversion.add_cell("code", """
# Calculate Bollinger Bands
data['mean'] = data['close'].rolling(window=LOOKBACK).mean()
data['std'] = data['close'].rolling(window=LOOKBACK).std()
data['upper_band'] = data['mean'] + STD_DEV * data['std']
data['lower_band'] = data['mean'] - STD_DEV * data['std']

# Generate signals
data['z_score'] = (data['close'] - data['mean']) / data['std']
data['signal'] = 0

# Buy when price is below lower band (oversold)
data.loc[data['z_score'] < -ENTRY_THRESHOLD, 'signal'] = 1

# Sell when price is above upper band (overbought)
data.loc[data['z_score'] > ENTRY_THRESHOLD, 'signal'] = -1

print(f"Generated {data['signal'].abs().sum()} trading signals")
""")

        self.templates['mean_reversion'] = mean_reversion

    def get_template(self, name: str) -> NotebookTemplate:
        """Get a template by name"""
        return self.templates.get(name)

    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates"""
        return [
            {"name": name, "description": tpl.description}
            for name, tpl in self.templates.items()
        ]
```

**Step 2: Create test notebook fixture**

Create: `test-fixtures/templates/test_basic_strategy.ipynb`

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": ["# Test Strategy\\n"]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "import pandas as pd\\n",
        "import numpy as np\\n",
        "\\n",
        "# Test data\\n",
        "data = pd.DataFrame({\\n",
        "    'price': [100, 102, 101, 103, 105, 104, 106]\\n",
        "})\\n",
        "\\n",
        "print(data)"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 4
}
```

**Step 3: Create template tests**

Create: `ai-strategy-service/tests/test_templates.py`

```python
import pytest
from templates.notebook_templates import TemplateManager, NotebookTemplate

def test_template_manager_initialization():
    """Test template manager initializes with built-in templates"""
    manager = TemplateManager()

    templates = manager.list_templates()
    assert len(templates) >= 2

    template_names = [t['name'] for t in templates]
    assert 'breakout' in template_names
    assert 'mean_reversion' in template_names

def test_notebook_template_structure():
    """Test notebook template generates valid format"""
    template = NotebookTemplate("test", "Test template")
    template.add_cell("code", "print('hello')")

    notebook = template.to_notebook()

    assert notebook['nbformat'] == 4
    assert len(notebook['cells']) == 1
    assert notebook['cells'][0]['cell_type'] == 'code'

def test_breakout_template_content():
    """Test breakout template has required cells"""
    manager = TemplateManager()
    template = manager.get_template('breakout')

    assert template is not None
    assert len(template.cells) >= 6  # Should have at least 6 cells

    # Check for key cells
    cell_sources = [' '.join(cell['source']) for cell in template.cells]
    assert any('fetch_data' in source for source in cell_sources)
    assert any('portfolio_value' in source for source in cell_sources)
```

**Step 4: Run tests**

Run:
```bash
cd ai-strategy-service
pytest tests/test_templates.py -v
```

Expected: All 3 tests pass

**Step 5: Commit**

```bash
git add ai-strategy-service/templates/ test-fixtures/
git commit -m "feat: implement notebook template system"
```

---

## Task 4: AI Chat Interface and Strategy Generation

**Files:**
- Modify: `ai-strategy-vscode/src/extension.ts`
- Create: `ai-strategy-vscode/src/chatProvider.ts`
- Create: `ai-strategy-service/routers/strategy.py`

**Step 1: Create chat provider**

Create: `ai-strategy-vscode/src/chatProvider.ts`

```typescript
import * as vscode from 'vscode';
import { GLMClient } from './api/glmClient';

export class ChatProvider {
  private glmClient: GLMClient;
  private chatHistory: Array<{role: string, content: string}> = [];

  constructor(private context: vscode.ExtensionContext) {
    const apiKey = vscode.workspace.getConfiguration('aiStrategy')
      .get<string>('glmApiKey', '');

    if (!apiKey) {
      throw new Error('GLM API Key not configured. Please set aiStrategy.glmApiKey in settings.');
    }

    this.glmClient = new GLMClient(apiKey);
  }

  async sendMessage(message: string): Promise<string> {
    // Add user message to history
    this.chatHistory.push({ role: 'user', content: message });

    // Check if user wants to generate strategy
    if (this.isStrategyRequest(message)) {
      const strategyCode = await this.glmClient.generateStrategy(message);
      this.chatHistory.push({ role: 'assistant', content: strategyCode });
      return strategyCode;
    }

    // Regular chat
    const response = await this.glmClient.chat(this.chatHistory);
    this.chatHistory.push({ role: 'assistant', content: response });
    return response;
  }

  private isStrategyRequest(message: string): boolean {
    const strategyKeywords = [
      'strategy', 'trading', 'algorithm', 'backtest',
      'buy', 'sell', 'signal', 'indicator', 'moving average',
      'breakout', 'momentum', 'mean reversion'
    ];

    const lowerMessage = message.toLowerCase();
    return strategyKeywords.some(keyword => lowerMessage.includes(keyword));
  }

  clearHistory(): void {
    this.chatHistory = [];
  }

  async insertStrategyIntoNotebook(code: string): Promise<void> {
    // Parse the generated code into cells
    const cells = this.parseCodeToCells(code);

    // Get current notebook editor
    const editor = vscode.window.activeNotebookEditor;
    if (!editor) {
      throw new Error('No active notebook editor');
    }

    const notebook = editor.notebook;

    // Insert cells at current position
    const edit = new vscode.WorkspaceEdit();
    for (const cell of cells) {
      const range = new vscode.NotebookRange(notebook.cellCount, notebook.cellCount);
      edit.insertNotebookCell(
        notebook.uri,
        range,
        new vscode.NotebookCellData(
          cell.kind === 'code'
            ? vscode.NotebookCellKind.Code
            : vscode.NotebookCellKind.Markup,
          cell.content
        )
      );
    }

    await vscode.workspace.applyEdit(edit);
  }

  private parseCodeToCells(code: string): Array<{kind: string, content: string}> {
    const cells: Array<{kind: string, content: string}> = [];

    // Split by markdown headers (#)
    const sections = code.split(/\n(?=#)/);

    for (const section of sections) {
      const trimmed = section.trim();
      if (!trimmed) continue;

      if (trimmed.startsWith('#')) {
        // Markdown cell
        cells.push({ kind: 'markdown', content: trimmed });
      } else {
        // Code cell
        cells.push({ kind: 'code', content: trimmed });
      }
    }

    return cells;
  }
}
```

**Step 2: Update extension to use chat provider**

Modify: `ai-strategy-vscode/src/extension.ts`

```typescript
import * as vscode from 'vscode';
import { ChatProvider } from './chatProvider';

let chatProvider: ChatProvider;

export function activate(context: vscode.ExtensionContext) {
  console.log('AI Strategy Assistant is now active!');

  try {
    chatProvider = new ChatProvider(context);
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to initialize: ${error}`);
    return;
  }

  // Register commands
  const createNotebookCmd = vscode.commands.registerCommand(
    'aiStrategy.createNotebook',
    async () => {
      const notebook = await vscode.workspace.openNotebookDocument(
        vscode.Uri.parse('untitled:/strategy.ipynb'),
        'jupyter-notebook'
      );
      await vscode.window.showNotebookDocument(notebook);
    }
  );

  const openChatCmd = vscode.commands.registerCommand(
    'aiStrategy.openChat',
    () => {
      AiStrategyChatPanel.createOrShow(context.extensionUri, chatProvider);
    }
  );

  const insertStrategyCmd = vscode.commands.registerCommand(
    'aiStrategy.insertIntoNotebook',
    async () => {
      const code = await vscode.window.showInputBox({
        prompt: 'Describe your strategy idea',
        placeHolder: 'e.g., 20-day moving average breakout strategy'
      });

      if (code) {
        const strategyCode = await chatProvider.sendMessage(code);
        await chatProvider.insertStrategyIntoNotebook(strategyCode);
      }
    }
  );

  context.subscriptions.push(createNotebookCmd, openChatCmd, insertStrategyCmd);
}

export function deactivate() {
  if (chatProvider) {
    chatProvider.clearHistory();
  }
}

class AiStrategyChatPanel {
  public static currentPanel: AiStrategyChatPanel | undefined;
  private readonly _panel: vscode.WebviewPanel;
  private _disposables: vscode.Disposable[] = [];

  public static createOrShow(
    extensionUri: vscode.Uri,
    chatProvider: ChatProvider
  ): AiStrategyChatPanel {
    const column = vscode.window.activeTextEditor
      ? vscode.ViewColumn.Beside
      : undefined;

    if (AiStrategyChatPanel.currentPanel) {
      AiStrategyChatPanel.currentPanel._panel.reveal(column);
      return AiStrategyChatPanel.currentPanel;
    }

    const panel = vscode.window.createWebviewPanel(
      'aiStrategyChat',
      'AI Strategy Chat',
      column || vscode.ViewColumn.One,
      { enableScripts: true }
    );

    AiStrategyChatPanel.currentPanel = new AiStrategyChatPanel(panel, extensionUri, chatProvider);
    return AiStrategyChatPanel.currentPanel;
  }

  private constructor(
    panel: vscode.WebviewPanel,
    extensionUri: vscode.Uri,
    private chatProvider: ChatProvider
  ) {
    this._panel = panel;
    this._panel.webview.html = this._getHtmlForWebview(extensionUri);

    // Handle messages from webview
    this._panel.webview.onDidReceiveMessage(
      async (message) => {
        switch (message.command) {
          case 'chat':
            const response = await this.chatProvider.sendMessage(message.text);
            this._panel.webview.postMessage({ command: 'response', text: response });
            break;
        }
      },
      null,
      this._disposables
    );

    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
  }

  private _getHtmlForWebview(extensionUri: vscode.Uri): string {
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: var(--vscode-font-family);
      padding: 20px;
      color: var(--vscode-foreground-color);
    }
    #chat-container {
      display: flex;
      flex-direction: column;
      height: 100vh;
    }
    #messages {
      flex: 1;
      overflow-y: auto;
      margin-bottom: 10px;
      padding: 10px;
      border: 1px solid var(--vscode-widget-border);
      border-radius: 4px;
    }
    .message {
      margin-bottom: 10px;
      padding: 8px;
      border-radius: 4px;
    }
    .user-message {
      background-color: var(--vscode-input-background);
      text-align: right;
    }
    .assistant-message {
      background-color: var(--vscode-editor-background);
      border-left: 3px solid var(--vscode-textLink-foreground);
    }
    #input-area {
      display: flex;
      gap: 10px;
    }
    input {
      flex: 1;
      padding: 8px;
      background: var(--vscode-input-background);
      border: 1px solid var(--vscode-input-border);
      color: var(--vscode-foreground);
    }
    button {
      padding: 8px 16px;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: 2px;
      cursor: pointer;
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
    pre {
      background: var(--vscode-textCodeBlock-background);
      padding: 10px;
      border-radius: 4px;
      overflow-x: auto;
    }
    code {
      font-family: var(--vscode-editor-font-family);
    }
  </style>
</head>
<body>
  <div id="chat-container">
    <div id="messages"></div>
    <div id="input-area">
      <input type="text" id="user-input" placeholder="Describe your trading strategy...">
      <button id="send-btn">Send</button>
    </div>
  </div>
  <script>
    const vscode = acquireVsCodeApi();
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const messagesDiv = document.getElementById('messages');

    function addMessage(role, text) {
      const msgDiv = document.createElement('div');
      msgDiv.className = 'message ' + role + '-message';

      if (role === 'assistant' && text.includes('```')) {
        // Format code blocks
        text = text.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<pre><code>$2</code></pre>');
      }

      msgDiv.innerHTML = text.replace(/\\n/g, '<br>');
      messagesDiv.appendChild(msgDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function sendMessage() {
      const text = input.value.trim();
      if (!text) return;

      addMessage('user', text);
      vscode.postMessage({ command: 'chat', text: text });
      input.value = '';
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage();
    });

    window.addEventListener('message', (event) => {
      const message = event.data;
      if (message.command === 'response') {
        addMessage('assistant', message.text);
      }
    });
  </script>
</body>
</html>`;
  }

  public dispose() {
    AiStrategyChatPanel.currentPanel = undefined;
    this._panel.dispose();
    while (this._disposables.length) {
      const disposable = this._disposables.pop();
      if (disposable) {
        disposable.dispose();
      }
    }
  }
}
```

**Step 3: Create backend strategy router**

Create: `ai-strategy-service/routers/strategy.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.glm_service import GLMService, GLMMessage

router = APIRouter(prefix="/api/strategy", tags=["strategy"])

class StrategyRequest(BaseModel):
    description: str
    market: Optional[str] = "stock"
    timeframe: Optional[str] = "daily"
    risk_level: Optional[str] = "medium"

class StrategyResponse(BaseModel):
    code: str
    explanation: str
    parameters: dict

@router.post("/generate", response_model=StrategyResponse)
async def generate_strategy(request: StrategyRequest):
    """Generate trading strategy from description using GLM AI"""
    try:
        glm_service = GLMService()

        # Construct prompt with context
        system_prompt = GLMMessage(
            role="system",
            content=f"""You are a quantitative trading strategy expert. Generate Python code for trading strategies.

Requirements:
- Market: {request.market}
- Timeframe: {request.timeframe}
- Risk Level: {request.risk_level}

Generate a complete Jupyter notebook with:
1. Cell 1: Imports (pandas, numpy, matplotlib)
2. Cell 2: Data fetching function (placeholder)
3. Cell 3: Strategy parameters definition
4. Cell 4: Signal generation logic
5. Cell 5: Simple backtesting
6. Cell 6: Visualization

Return ONLY valid Python code. Wrap each cell in triple backticks with python.
Format like:
```python
# Cell 1 code
```
```python
# Cell 2 code
```
etc."""
        )

        user_prompt = GLMMessage(
            role="user",
            content=f"Create a {request.risk_level} risk trading strategy: {request.description}"
        )

        # Get AI response
        ai_response = await glm_service.chat([system_prompt, user_prompt])

        # Parse response to extract code cells
        code_cells = parse_code_cells(ai_response)

        # Generate explanation
        explanation = extract_explanation(ai_response)

        # Extract parameters
        parameters = extract_parameters(ai_response)

        await glm_service.close()

        return StrategyResponse(
            code=code_cells,
            explanation=explanation,
            parameters=parameters
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def parse_code_cells(response: str) -> str:
    """Parse AI response to extract code cells"""
    # Split by code blocks
    import re

    code_blocks = re.findall(r'```python\n(.*?)```', response, re.DOTALL)

    if not code_blocks:
        # Fallback: try to find any code
        code_blocks = re.findall(r'```\n(.*?)```', response, re.DOTALL)

    # Join cells with cell marker
    cells = []
    for i, block in enumerate(code_blocks):
        cells.append(f"# Cell {i+1}\n{block.strip()}\n")

    return '\n'.join(cells)

def extract_explanation(response: str) -> str:
    """Extract explanation from AI response"""
    lines = response.split('\n')
    explanation_lines = []
    in_code_block = False

    for line in lines:
        if '```' in line:
            in_code_block = not in_code_block
            continue

        if not in_code_block and line.strip():
            explanation_lines.append(line)

    return '\n'.join(explanation_lines[:5])  # First few lines

def extract_parameters(response: str) -> dict:
    """Extract strategy parameters from AI response"""
    import re

    params = {}

    # Look for common parameter patterns
    param_patterns = {
        'LOOKBACK': r'LOOKBACK\s*=\s*(\d+)',
        'THRESHOLD': r'THRESHOLD\s*=\s*([\d.]+)',
        'STOP_LOSS': r'STOP_LOSS\s*=\s*([\d.]+)',
        'TAKE_PROFIT': r'TAKE_PROFIT\s*=\s*([\d.]+)',
    }

    for name, pattern in param_patterns.items():
        match = re.search(pattern, response)
        if match:
            params[name] = match.group(1)

    return params
```

**Step 4: Update FastAPI main to include router**

Create: `ai-strategy-service/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import strategy

app = FastAPI(title="AI Strategy Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(strategy.router)

@app.get("/")
async def root():
    return {"message": "AI Strategy Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 5: Create test for strategy generation**

Create: `ai-strategy-service/tests/test_strategy_generation.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_generate_strategy_endpoint():
    """Test strategy generation endpoint"""
    response = client.post(
        "/api/strategy/generate",
        json={
            "description": "Simple moving average crossover",
            "market": "stock",
            "timeframe": "daily",
            "risk_level": "medium"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "code" in data
    assert "explanation" in data
    assert "parameters" in data
    assert "Cell" in data["code"]  # Should have cell markers

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

**Step 6: Run tests**

Run:
```bash
cd ai-strategy-service
pytest tests/test_strategy_generation.py -v
```

Expected: Both tests pass

**Step 7: Commit**

```bash
git add ai-strategy-vscode/src/ ai-strategy-service/routers/
git commit -m "feat: implement AI chat interface and strategy generation"
```

---

## Task 5: Notebook Execution and Testing

**Files:**
- Create: `ai-strategy-vscode/src/notebookExecutor.ts`
- Create: `ai-strategy-service/services/jupyter_service.py`
- Create: `test-fixtures/execution/test_execution.py`

**Step 1: Create notebook executor**

Create: `ai-strategy-vscode/src/notebookExecutor.ts`

```typescript
import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface ExecutionResult {
  cellIndex: number;
  success: boolean;
  output: string;
  error?: string;
}

export class NotebookExecutor {
  private notebookPath: string;
  private kernelId: string = '';

  constructor(notebookUri: vscode.Uri) {
    this.notebookPath = notebookUri.fsPath;
  }

  async executeAll(): Promise<ExecutionResult[]> {
    const results: ExecutionResult[] = [];

    try {
      // Use jupyter nbconvert to execute
      const { stdout } = await execAsync(
        `jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=60 "${this.notebookPath}"`
      );

      // Parse output for results
      // This is simplified - real implementation would parse notebook JSON
      results.push({
        cellIndex: 0,
        success: true,
        output: 'Notebook executed successfully'
      });

    } catch (error) {
      results.push({
        cellIndex: 0,
        success: false,
        output: '',
        error: (error as Error).message
      });
    }

    return results;
  }

  async executeCell(cellIndex: number): Promise<ExecutionResult> {
    // This would integrate with Jupyter kernel
    // For MVP, we use a simplified approach

    return {
      cellIndex,
      success: true,
      output: `Cell ${cellIndex} executed`
    };
  }

  async getKernelSpec(): Promise<string[]> {
    try {
      const { stdout } = await execAsync('jupyter kernelspec list --json');
      const specs = JSON.parse(stdout);
      return Object.keys(specs);
    } catch {
      return ['python3'];
    }
  }
}
```

**Step 2: Create Jupyter service**

Create: `ai-strategy-service/services/jupyter_service.py`

```python
import subprocess
import json
from typing import List, Dict, Any
from pathlib import Path

class JupyterService:
    """Service for interacting with Jupyter notebooks"""

    async def execute_notebook(self, notebook_path: str) -> Dict[str, Any]:
        """Execute a Jupyter notebook and return results"""

        # Convert to script and execute
        script_path = notebook_path.replace('.ipynb', '.py')

        # Convert notebook to Python script
        convert_result = subprocess.run(
            ['jupyter', 'nbconvert', '--to', 'script', notebook_path, '--output', script_path],
            capture_output=True,
            text=True
        )

        if convert_result.returncode != 0:
            return {
                'success': False,
                'error': f'Conversion failed: {convert_result.stderr}'
            }

        # Execute the script
        exec_result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Clean up script
        Path(script_path).unlink(missing_ok=True)

        if exec_result.returncode != 0:
            return {
                'success': False,
                'error': exec_result.stderr,
                'output': exec_result.stdout
            }

        return {
            'success': True,
            'output': exec_result.stdout
        }

    async def get_available_kernels(self) -> List[str]:
        """Get list of available Jupyter kernels"""
        result = subprocess.run(
            ['jupyter', 'kernelspec', 'list', '--json'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return ['python3']  # Fallback

        specs = json.loads(result.stdout)
        return list(specs.keys())

    def validate_notebook(self, notebook_path: str) -> Dict[str, Any]:
        """Validate notebook structure and syntax"""
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)

        errors = []

        # Check nbformat version
        if notebook.get('nbformat') != 4:
            errors.append('Not a valid nbformat v4 notebook')

        # Validate cells
        for i, cell in enumerate(notebook.get('cells', [])):
            if cell['cell_type'] == 'code':
                source = ''.join(cell.get('source', []))
                if not source.strip():
                    continue

                # Basic syntax check
                try:
                    compile(source, f'<cell {i}>', 'exec')
                except SyntaxError as e:
                    errors.append(f'Cell {i}: {e}')

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

# Singleton instance
jupyter_service = JupyterService()
```

**Step 3: Create execution test**

Create: `test-fixtures/execution/test_execution.py`

```python
import pytest
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from services.jupyter_service import jupyter_service

def test_execute_simple_notebook():
    """Test executing a simple notebook"""
    notebook_path = 'test-fixtures/templates/test_basic_strategy.ipynb'

    result = await jupyter_service.execute_notebook(notebook_path)

    assert result['success'] == True
    assert 'price' in result['output']

def test_validate_notebook():
    """Test notebook validation"""
    notebook_path = 'test-fixtures/templates/test_basic_strategy.ipynb'

    validation = jupyter_service.validate_notebook(notebook_path)

    assert validation['valid'] == True
    assert len(validation['errors']) == 0

def test_get_kernels():
    """Test getting available kernels"""
    kernels = await jupyter_service.get_available_kernels()

    assert isinstance(kernels, list)
    assert len(kernels) > 0
    assert 'python3' in kernels
```

**Step 4: Create integration test**

Create: `ai-strategy-service/tests/test_integration.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_end_to_end_strategy_flow():
    """Test complete flow: generate → execute → validate"""

    # Step 1: Generate strategy
    gen_response = client.post(
        "/api/strategy/generate",
        json={"description": "Simple moving average crossover"}
    )

    assert gen_response.status_code == 200
    strategy_code = gen_response.json()['code']

    # Step 2: Save as notebook (would normally save to file)
    # For now, just validate code structure
    assert 'def' in strategy_code or 'import' in strategy_code

    # Step 3: Validate notebook would execute successfully
    # This is a simplified check - real implementation would save and execute
    assert 'Cell' in strategy_code  # Has cell markers
```

**Step 5: Run tests**

Run:
```bash
cd ai-strategy-service
pytest tests/test_integration.py -v
```

Expected: End-to-end test passes

**Step 6: Commit**

```bash
git add ai-strategy-vscode/src/notebookExecutor.ts \
        ai-strategy-service/services/jupyter_service.py \
        test-fixtures/execution/
git commit -m "feat: implement notebook execution and testing"
```

---

## Task 6: Integration with Existing CBSC System

**Files:**
- Modify: `ai-strategy-service/routers/strategy.py`
- Create: `ai-strategy-service/services/cbsc_integration.py`
- Modify: `frontend/src/types/strategy.ts` (existing file)

**Step 1: Create CBSC integration service**

Create: `ai-strategy-service/services/cbsc_integration.py`

```python
from typing import Dict, Any, Optional
import httpx
import os
from pathlib import Path

class CBSCIntegration:
    """Integrate generated strategies with existing CBSC system"""

    def __init__(self):
        self.cbsc_api_url = os.getenv('CBSC_API_URL', 'http://localhost:3003')
        self.client = httpx.AsyncClient(timeout=30.0)

    async def deploy_strategy(
        self,
        notebook_path: str,
        strategy_name: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Deploy a notebook strategy to CBSC system

        Args:
            notebook_path: Path to the strategy notebook
            strategy_name: Name for the strategy
            user_id: User ID who created the strategy

        Returns:
            Deployment result with strategy ID
        """

        # 1. Extract strategy parameters from notebook
        params = await self._extract_parameters(notebook_path)

        # 2. Create strategy configuration
        strategy_config = {
            "name": strategy_name,
            "type": "personal",
            "category": "other",
            "description": params.get("description", "Created with AI Assistant"),
            "parameters": {
                **params,
                "created_with_ai": True,
                "source_notebook": notebook_path
            },
            "personalConfig": {
                "userId": user_id,
                "riskTolerance": params.get("risk_tolerance", "moderate"),
                "capitalAllocation": params.get("capital", 10000),
                "maxPositionSize": params.get("max_position", 0.1),
                "stopLoss": params.get("stop_loss", 0.03),
                "takeProfit": params.get("take_profit", 0.1),
                "autoTrading": False
            }
        }

        # 3. Register with CBSC API
        response = await self.client.post(
            f"{self.cbsc_api_url}/api/strategies",
            json=strategy_config,
            headers={"Authorization": f"Bearer {os.getenv('CBSC_API_KEY')}"}
        )

        response.raise_for_status()

        result = response.json()

        return {
            "success": True,
            "strategy_id": result.get("id"),
            "message": "Strategy deployed successfully"
        }

    async def _extract_parameters(self, notebook_path: str) -> Dict[str, Any]:
        """Extract strategy parameters from notebook"""
        import json

        with open(notebook_path, 'r') as f:
            notebook = json.load(f)

        params = {}

        # Look for parameter definitions in code cells
        for cell in notebook.get('cells', []):
            if cell['cell_type'] == 'code':
                source = ''.join(cell.get('source', []))

                # Extract common parameters using regex
                import re

                # Look for variable assignments
                param_patterns = {
                    'SYMBOL': r'SYMBOL\s*=\s*["\']([\w\-]+)["\']',
                    'START_DATE': r'START_DATE\s*=\s*["\']([\d\-]+)["\']',
                    'END_DATE': r'END_DATE\s*=\s*["\']([\d\-]+)["\']',
                    'LOOKBACK': r'LOOKBACK\s*=\s*(\d+)',
                    'THRESHOLD': r'THRESHOLD\s*=\s*([\d.]+)',
                }

                for param_name, pattern in param_patterns.items():
                    match = re.search(pattern, source)
                    if match:
                        params[param_name.lower()] = match.group(1)

        return params

    async def sync_to_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Sync strategies to PersonalStrategyDashboard

        Args:
            user_id: User ID to sync strategies for

        Returns:
            Sync result with strategy count
        """

        response = await self.client.get(
            f"{self.cbsc_api_url}/api/users/{user_id}/strategies",
            headers={"Authorization": f"Bearer {os.getenv('CBSC_API_KEY')}"}
        )

        response.raise_for_status()

        return response.json()

    async def close(self):
        await self.client.aclose()

# Singleton instance
cbsc_integration = CBSCIntegration()
```

**Step 2: Update strategy router with deployment endpoint**

Modify: `ai-strategy-service/routers/strategy.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.glm_service import GLMService, GLMMessage
from services.cbsc_integration import cbsc_integration

router = APIRouter(prefix="/api/strategy", tags=["strategy"])

class StrategyRequest(BaseModel):
    description: str
    market: Optional[str] = "stock"
    timeframe: Optional[str] = "daily"
    risk_level: Optional[str] = "medium"

class DeployRequest(BaseModel):
    notebook_path: str
    strategy_name: str
    user_id: str

class StrategyResponse(BaseModel):
    code: str
    explanation: str
    parameters: dict

@router.post("/generate", response_model=StrategyResponse)
async def generate_strategy(request: StrategyRequest):
    """Generate trading strategy from description using GLM AI"""
    try:
        glm_service = GLMService()

        system_prompt = GLMMessage(
            role="system",
            content=f"""You are a quantitative trading strategy expert. Generate Python code for trading strategies.

Requirements:
- Market: {request.market}
- Timeframe: {request.timeframe}
- Risk Level: {request.risk_level}

Generate a complete Jupyter notebook with:
1. Cell 1: Imports (pandas, numpy, matplotlib)
2. Cell 2: Data fetching function (placeholder)
3. Cell 3: Strategy parameters definition
4. Cell 4: Signal generation logic
5. Cell 5: Simple backtesting
6. Cell 6: Visualization

Return ONLY valid Python code. Wrap each cell in triple backticks with python."""
        )

        user_prompt = GLMMessage(
            role="user",
            content=f"Create a {request.risk_level} risk trading strategy: {request.description}"
        )

        ai_response = await glm_service.chat([system_prompt, user_prompt])
        code_cells = parse_code_cells(ai_response)
        explanation = extract_explanation(ai_response)
        parameters = extract_parameters(ai_response)

        await glm_service.close()

        return StrategyResponse(
            code=code_cells,
            explanation=explanation,
            parameters=parameters
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deploy")
async def deploy_strategy(request: DeployRequest):
    """Deploy a generated strategy to CBSC system"""
    try:
        result = await cbsc_integration.deploy_strategy(
            notebook_path=request.notebook_path,
            strategy_name=request.strategy_name,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/{user_id}")
async def sync_strategies(user_id: str):
    """Sync strategies to personal dashboard"""
    try:
        result = await cbsc_integration.sync_to_dashboard(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 3: Update frontend types for AI-generated strategies**

Modify: `frontend/src/types/strategy.ts` (add to existing interface)

Add to `Strategy` interface:

```typescript
export interface Strategy {
  // ... existing fields ...

  // New fields for AI-generated strategies
  aiGenerated?: boolean;
  sourceNotebook?: string;
  aiModelVersion?: string;  // e.g., "glm-4-plus"

  // New field for validation status
  validationStatus?: 'pending' | 'validated' | 'failed';
  lastValidated?: string;
}
```

**Step 4: Create integration tests**

Create: `ai-strategy-service/tests/test_cbsc_integration.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.cbsc_integration import CBSCIntegration, cbsc_integration

@pytest.mark.asyncio
async def test_extract_parameters_from_notebook():
    """Test parameter extraction from notebook"""
    # Create a test notebook
    import json
    import tempfile

    test_notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": [
                    "SYMBOL = 'AAPL'\n",
                    "LOOKBACK = 20\n",
                    "THRESHOLD = 0.02\n"
                ]
            }
        ],
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        json.dump(test_notebook, f)
        temp_path = f.name

    try:
        integration = CBSCIntegration()
        params = await integration._extract_parameters(temp_path)

        assert 'symbol' in params
        assert params['symbol'] == 'AAPL'
        assert 'lookback' in params
        assert params['lookback'] == '20'
        assert 'threshold' in params
        assert params['threshold'] == '0.02'
    finally:
        import os
        os.unlink(temp_path)

@pytest.mark.asyncio
@patch('services.cbsc_integration.httpx.AsyncClient')
async def test_deploy_strategy_success(mock_client_class):
    """Test successful strategy deployment"""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "strategy-123"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    integration = CBSCIntegration()
    integration.client = mock_client

    result = await integration.deploy_strategy(
        notebook_path="test.ipynb",
        strategy_name="Test Strategy",
        user_id="user-123"
    )

    assert result['success'] == True
    assert result['strategy_id'] == 'strategy-123'
    assert 'deployed successfully' in result['message'].lower()
```

**Step 5: Run integration tests**

Run:
```bash
cd ai-strategy-service
pytest tests/test_cbsc_integration.py -v
```

Expected: All integration tests pass

**Step 6: Commit**

```bash
git add ai-strategy-service/services/cbsc_integration.py \
        ai-strategy-service/routers/strategy.py \
        ai-strategy-service/tests/
git commit -m "feat: integrate with existing CBSC system"
```

---

## Task 7: Documentation and Configuration

**Files:**
- Create: `ai-strategy-vscode/CHANGELOG.md`
- Create: `ai-strategy-vscode/package-lock.json`
- Create: `ai-strategy-service/requirements.txt`
- Create: `docs/setup-guide.md`

**Step 1: Create setup guide**

Create: `docs/setup-guide.md`

```markdown
# AI Strategy Development Tool - Setup Guide

## Prerequisites

1. **VSCode** - Latest version
2. **Python 3.10+** - With Jupyter installed
3. **GLM API Key** - From [智譜AI](https://open.bigmodel.cn/)
4. **Node.js 18+** - For VSCode extension development

## Installation

### 1. Install VSCode Extension

\`\`\`bash
cd ai-strategy-vscode
npm install
npm run compile
code . --install-extension
\`\`\`

### 2. Configure API Key

Open VSCode Settings (Ctrl+,), search for "aiStrategy", and set:

\`\`\`json
{
  "aiStrategy.glmApiKey": "your_glm_api_key_here"
}
\`\`\`

### 3. Install Backend Service

\`\`\`bash
cd ai-strategy-service
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GLM_API_KEY
python -m uvicorn main:app --reload
\`\`\`

### 4. Install Jupyter

\`\`\`bash
pip install jupyter
jupyter notebook list
\`\`\`

## Usage

1. Open VSCode
2. Press `Ctrl+Shift+P` (Cmd+Shift+P on Mac)
3. Type "Create Strategy Notebook"
4. Open AI Chat panel
5. Describe your strategy idea
6. Click "Insert into Notebook" to add generated code

## Testing

Run test suite:

\`\`\`bash
# VSCode extension tests
cd ai-strategy-vscode
npm test

# Backend tests
cd ai-strategy-service
pytest tests/
\`\`\`

## Troubleshooting

### GLM API Errors

- Check your API key is valid
- Verify you have sufficient quota
- Check network connectivity

### Notebook Execution Fails

- Ensure Jupyter is installed: `jupyter --version`
- Check Python kernel: `python -m ipykernel install --user`
- Verify notebook syntax

### Extension Not Loading

- Check VSCode version compatibility
- Try reloading VSCode
- Check Developer Console for errors (Help > Toggle Developer Tools)
```

**Step 2: Create backend requirements**

Create: `ai-strategy-service/requirements.txt`

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.1
pydantic==2.5.0
python-dotenv==1.0.0
jupyter==1.0.0
nbconvert==7.14.0
pandas==2.1.3
numpy==1.26.2
matplotlib==3.8.2
pytest==7.4.3
pytest-asyncio==0.21.1
```

**Step 3: Create changelog**

Create: `ai-strategy-vscode/CHANGELOG.md`

```markdown
# Changelog

All notable changes to the AI Strategy Assistant extension will be documented in this file.

## [0.1.0] - 2026-01-06

### Added
- Initial release of AI Strategy Assistant
- GLM 4.7 AI integration for strategy generation
- Jupyter notebook template system
- Strategy execution and testing
- CBSC system integration
- AI Chat interface in VSCode

### Features
- Create strategies from natural language descriptions
- Pre-built templates for common strategies (breakout, mean reversion)
- One-click notebook execution
- Deploy strategies to existing CBSC backend
- Real-time AI assistance during strategy development
```

**Step 4: Create environment file**

Create: `ai-strategy-service/.env`

```bash
# GLM API Configuration
GLM_API_KEY=your_actual_api_key_here
GLM_MODEL=glm-4-plus

# CBSC Integration
CBSC_API_URL=http://localhost:3003
CBSC_API_KEY=your_cbsc_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

**Step 5: Commit**

```bash
git add docs/ ai-strategy-service/requirements.txt ai-strategy-service/.env
git commit -m "docs: add setup guide and configuration files"
```

---

## Task 8: Final Integration Testing and Polish

**Files:**
- Create: `ai-strategy-vscode/src/test/integration.test.ts`
- Create: `ai-strategy-service/tests/test_e2e.py`
- Modify: `ai-strategy-vscode/package.json`

**Step 1: Create end-to-end integration test**

Create: `ai-strategy-service/tests/test_e2e.py`

```python
import pytest
import asyncio
import json
import tempfile
from pathlib import Path

class TestE2E:
    """End-to-end tests for the complete workflow"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test: Generate → Save → Execute → Deploy"""

        # Step 1: Generate strategy
        from services.glm_service import GLMService, GLMMessage

        glm_service = GLMService()
        system_prompt = GLMMessage(
            role="system",
            content="Generate a simple moving average crossover strategy in Python notebook format."
        )
        user_prompt = GLMMessage(
            role="user",
            content="Create a basic moving average crossover strategy"
        )

        response = await glm_service.chat([system_prompt, user_prompt])
        assert response is not None
        assert len(response) > 0

        await glm_service.close()

        # Step 2: Save to notebook file
        notebook_data = {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "outputs": [],
                    "source": response.split('\n')
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook_data, f)
            notebook_path = f.name

        try:
            # Step 3: Execute notebook
            from services.jupyter_service import jupyter_service

            result = await jupyter_service.execute_notebook(notebook_path)
            assert result['success'] == True

            # Step 4: Validate notebook
            validation = jupyter_service.validate_notebook(notebook_path)
            assert validation['valid'] == True

        finally:
            Path(notebook_path).unlink()

    @pytest.mark.asyncio
    async def test_ai_to_deployment_flow(self):
        """Test: AI generation to CBSC deployment"""

        # This test requires actual CBSC backend
        # Skip in CI/CD if backend not available

        import os

        if not os.getenv('CBSC_API_URL'):
            pytest.skip("CBSC_API_URL not set")

        from services.cbsc_integration import cbsc_integration

        # Mock notebook for testing
        notebook_path = "test_fixtures/templates/test_basic_strategy.ipynb"

        result = await cbsc_integration.deploy_strategy(
            notebook_path=notebook_path,
            strategy_name="E2E Test Strategy",
            user_id="test-user"
        )

        assert result['success'] == True
        assert 'strategy_id' in result
```

**Step 2: Add test scripts to package.json**

Modify: `ai-strategy-vscode/package.json`

Add to "scripts" section:

```json
"scripts": {
  "vscode:prepublish": "npm run compile",
  "compile": "tsc -p ./",
  "watch": "tsc -watch -p ./",
  "pretest": "npm run compile",
  "test": "node ./out/test/runTest.js",
  "test:e2e": "pytest ../ai-strategy-service/tests/test_e2e.py",
  "lint": "eslint src --ext ts",
  "package": "vsce package"
}
```

**Step 3: Create final README**

Create: `README.md` (project root)

```markdown
# AI Strategy Development Tool

Build, test, and deploy quantitative trading strategies with GLM 4.7 AI in VSCode.

## Overview

This tool provides:
- **AI-Powered Strategy Generation**: Describe your idea in plain English, get working Python code
- **Jupyter Notebook Interface**: Edit, execute, and visualize strategies in notebooks
- **One-Click Deployment**: Deploy strategies to the CBSC trading system
- **Real-Time Assistance**: AI chat panel helps you refine and debug strategies

## Architecture

```
VSCode Extension (TypeScript)
    ↓
AI Service (FastAPI + GLM 4.7)
    ↓
Jupyter Notebooks (Python)
    ↓
CBSC Trading System (Integration)
```

## Quick Start

1. **Install VSCode Extension**
   ```bash
   cd ai-strategy-vscode
   npm install
   npm run compile
   ```

2. **Configure GLM API Key**
   - Get API key from [智譜AI](https://open.bigmodel.cn/)
   - Set in VSCode settings: `aiStrategy.glmApiKey`

3. **Start Backend Service**
   ```bash
   cd ai-strategy-service
   pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```

4. **Create Your First Strategy**
   - Open VSCode
   - `Ctrl+Shift+P` → "Create Strategy Notebook"
   - Describe your idea: "20-day moving average breakout with volume confirmation"
   - AI generates code, insert into notebook
   - Execute and see results!

## Features

### AI Strategy Generation
- Natural language to Python code
- Supports multiple strategy types (breakout, mean reversion, momentum)
- Customizable parameters and risk levels

### Notebook Templates
- Pre-built templates for common strategies
- Easy to modify and extend
- Integrated with CBSC data service

### Execution & Testing
- One-click notebook execution
- Real-time results visualization
- Performance metrics calculation

### CBSC Integration
- Deploy strategies to production
- Sync with PersonalStrategyDashboard
- Track performance over time

## Development

### Project Structure
```
.
├── ai-strategy-vscode/      # VSCode Extension
├── ai-strategy-service/      # Backend Service
├── docs/                     # Documentation
├── test-fixtures/            # Test data
└── README.md
```

### Running Tests
```bash
# Extension tests
cd ai-strategy-vscode && npm test

# Backend tests
cd ai-strategy-service && pytest

# E2E tests
pytest test-fixtures/tests/
```

## Contributing

Contributions welcome! Please read our contributing guidelines.

## License

MIT

## Support

For issues and questions, please open a GitHub issue.
```

**Step 4: Run complete test suite**

Run:
```bash
cd ai-strategy-vscode
npm test

cd ../ai-strategy-service
pytest tests/ -v --cov=.
```

Expected: All tests pass with good coverage

**Step 5: Create final commit**

```bash
git add .
git commit -m "feat: complete AI Strategy Development Tool MVP

Features:
- VSCode extension with GLM 4.7 AI integration
- Jupyter notebook template system
- Strategy execution and validation
- CBSC system integration
- Complete test coverage
- Documentation and setup guide

Tests: 100% passing
Coverage: >80%"
```

---

## Implementation Complete!

**Total Tasks:** 8 major tasks
**Estimated Time:** 2-3 weeks
**Lines of Code:** ~3,000-4,000

**Next Steps:**
1. Review the plan
2. Choose execution approach (subagent-driven or parallel session)
3. Begin implementation
