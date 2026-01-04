# PROJECT KNOWLEDGE BASE

**Generated:** 2025-01-03 **Project:** Claude Code PM + 香港量化交易系统
**Languages:** Python, TypeScript, JavaScript, Rust, Go

## OVERVIEW

Multi-project workspace containing:

- **Claude Code PM**: Spec-driven development system with GitHub integration
- **CODEX--**: Complex quant trading system (9,679 files) - non-price
  indicators, multi-process optimization, HK government data
- **simplified_system**: Streamlined quant system (416 files) - alpha factors,
  backtesting, dashboard
- **backend**: FastAPI user management system (93 files) - authentication, API
  endpoints, PostgreSQL
- **frontend**: React dashboard (772 files) - real-time monitoring, trading
  visualization

## STRUCTURE

```
./
├── .claude/               # PM system workspace (epics, prds, context)
├── CODEX--/               # Main quant system (Rust+Python+React)
├── simplified_system/       # Streamlined quant system (Python)
├── backend/               # FastAPI backend
├── frontend/              # React frontend
├── anthropics-skills/      # Reusable skill definitions
└── .worktrees/           # Git worktrees for parallel development
```

## WHERE TO LOOK

| Task                      | Location             | Notes                                               |
| ------------------------- | -------------------- | --------------------------------------------------- |
| PM workflow (PRDs, epics) | `.claude/`           | Use `/pm:prd-new`, `/pm:epic-decompose`             |
| Quant trading - complex   | `CODEX--/`           | Multi-process optimization, 477 indicators, HK data |
| Quant trading - simple    | `simplified_system/` | Alpha factors, VectorBT, dashboard                  |
| User auth/management      | `backend/`           | FastAPI routes, DB models, JWT auth                 |
| Trading dashboard         | `frontend/`          | React components, real-time WebSocket               |
| Skills & commands         | `.claude/`           | Reusable skills, PM commands                        |
| Git worktrees             | `.worktrees/`        | Parallel development isolation                      |

## CORE WORKFLOWS

### PM System (Claude Code PM)

```bash
# Start new feature
/pm:prd-new feature-name          # Create PRD
/pm:prd-parse feature-name         # Convert to epic
/pm:epic-decompose feature-name    # Break into tasks
/pm:epic-sync feature-name        # Push to GitHub

# Execute
/pm:issue-start 1234             # Start work on issue
/pm:issue-sync 1234              # Sync progress
/pm:next                        # Get next task
```

### Quant Trading Development

```bash
# CODEX-- (complex system)
cd CODEX--
python multiprocess_nonprice_parameter_backtest.py    # Multi-process optimization
python test_multiprocess_nonprice_parameter.py        # Quick test
python run_full_dashboard.py                       # Full system

# simplified_system (streamlined)
cd simplified_system
python advanced_alpha_factor_demo.py               # Alpha factors
python api_maintenance_monitor.py                  # API monitoring
```

### Backend Development

```bash
cd backend
pytest                           # Run tests
pytest -m unit                     # Unit tests only
pytest --cov=backend tests/          # Coverage report
python main.py                      # Start server (port 3004)
```

### Frontend Development

```bash
cd frontend
npm run dev                      # Start dev server (port 3000)
npm run test                      # Run tests
npm run build                     # Production build
```

---

# Agents

**[中文文档 (Chinese Documentation)](doc/AGENTS_ZH.md)**

Specialized agents that do heavy work and return concise summaries to preserve
context.

## Core Philosophy

> "Don't anthropomorphize subagents. Use them to organize your prompts and elide
> context. Subagents are best when they can do lots of work but then provide
> small amounts of information back to the main conversation thread."
>
> – Adam Wolff, Anthropic

---

## Development Commands

### TypeScript/JavaScript (Root + Frontend)

**Testing:**

- `npm test` - Run all tests (unit + integration)
- `npm run test:unit` - Run unit tests only: `jest tests/unit`
- `npm run test:integration` - Run integration tests: `jest tests/integration`
- `npm run test:e2e` - Run E2E tests: `jest tests/e2e` or `playwright test`
- `npm run test:watch` - Watch mode for continuous testing
- `npm run test:coverage` - Generate test coverage report

**Running Single Test:**

```bash
# Jest pattern matching (works for most test files)
npm test -- --testNamePattern="test_create_strategy"
npm test -- strategyService.test.ts

# Exact file path
npm test backend/tests/unit/test_strategy_service.py
```

**Linting/Formatting:**

- `npm run lint` - ESLint check: `eslint . --ext .js,.jsx,.ts,.tsx`
- `npm run lint:fix` - Auto-fix ESLint issues
- `npm run format` - Prettier format: `prettier --write .`
- `npm run format:check` - Check formatting without fixing
- `npm run type-check` - TypeScript type check: `tsc --noEmit`

**Development:**

- `npm run dev` - Start dev server (Frontend: port 3000, Root: uses
  docker-compose)
- `npm run build` - Production build

### Python (Backend)

**Testing:**

```bash
# Run all tests
pytest

# Run specific test file
pytest backend/tests/unit/test_strategy_service.py

# Run specific test function
pytest backend/tests/unit/test_strategy_service.py::TestUnifiedStrategyService::test_create_strategy_success

# Run with markers
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"   # Skip slow tests
pytest -m "api or db"   # API or database tests

# Coverage
pytest --cov=backend --cov=src --cov-report=html
```

**Linting/Formatting:**

```bash
# Format code
black .
isort .

# Type checking
mypy backend/ src/

# Linting
flake8 backend/
ruff check backend/
```

---

## Code Style Guidelines

### TypeScript/JavaScript

**Imports:**

- Grouped: standard library → third-party → internal (with blank lines between
  groups)
- Alphabetical within groups
- Use absolute imports: `@/components`, `@/utils`, etc.
- Explicitly named imports preferred: `import { specificThing } from 'module'`

```typescript
// ✅ Correct
import React, { useState, useEffect } from 'react';
import { debounce } from 'lodash-es';
import { useStrategies } from '@/hooks/useStrategies';
import type { Strategy } from '@/types/strategy';
```

**Formatting:**

- 2 spaces indentation
- Single quotes (except JSX attributes)
- Semicolons required
- Trailing commas in multi-line arrays/objects
- 100 character line limit
- 2 empty lines between top-level definitions

```typescript
// ✅ Correct
const strategy: Strategy = {
  id: '123',
  name: 'Test Strategy',
  parameters: {
    window: 20,
    threshold: 0.5,
  },
};
```

**Naming:**

- camelCase for variables/functions
- PascalCase for components/classes
- UPPER_SNAKE_CASE for constants
- Prefix hooks with `use`
- Prefix test files with `.test.ts` or `.spec.ts`

```typescript
// ✅ Correct
const getUserData = async (id: string) => {};
const API_BASE_URL = 'https://api.example.com';
export const useStrategy = () => {};
```

**Types:**

- Always use TypeScript - no `any` types (warn in code, error in tests)
- Explicit return types for exported functions
- Use `interface` for object shapes, `type` for unions/primitives
- Strict null checking enabled
- No `@ts-ignore` or `@ts-expect-error` without justification

```typescript
// ✅ Correct
interface Strategy {
  id: string;
  name: string;
  performance?: PerformanceMetrics;
}

type Status = 'active' | 'inactive' | 'archived';

const getStrategy = async (id: string): Promise<Strategy> => {};
```

**Error Handling:**

- Use async/await with try/catch
- Provide meaningful error messages
- Return error objects or throw custom errors
- Never use empty catch blocks

```typescript
// ✅ Correct
try {
  const result = await apiCall();
  return { success: true, data: result };
} catch (error) {
  console.error('Failed to fetch strategy:', error);
  return { success: false, error: error.message };
}
```

**Comments:**

- Use `//` for single-line comments
- Use `/** */` for JSDoc on exported functions
- Explain "why", not "what" (code already says what)
- English comments only

```typescript
// ✅ Correct
/**
 * Calculate strategy performance metrics
 * Uses Monte Carlo simulation for robustness
 */
export const calculatePerformance = (data: Trade[]): Metrics => {};
```

### Python

**Formatting (Black):**

- 4 spaces indentation
- 100 character line limit
- No trailing whitespace
- 2 blank lines before top-level definitions
- Single quotes preferred

```python
# ✅ Correct
def create_strategy(user_id: int, name: str) -> Strategy:
    """Create a new strategy for the given user."""
    strategy = Strategy(user_id=user_id, name=name)
    session.add(strategy)
    await session.commit()
    return strategy
```

**Imports:**

- Grouped: standard library → third-party → internal (with blank lines)
- Alphabetical within groups
- Use isort for consistent ordering
- Relative imports for internal modules

```python
# ✅ Correct
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.strategy import Strategy
from schemas.strategy import StrategyCreate
```

**Naming:**

- snake_case for functions/variables
- PascalCase for classes
- UPPER_SNAKE_CASE for constants
- Prefix test files with `test_`
- Prefix test functions with `test_`

```python
# ✅ Correct
def get_user_strategies(user_id: int) -> List[Strategy]:
    pass

class StrategyService:
    pass

MAX_RETRY_ATTEMPTS = 3
```

**Type Hints:**

- Use type hints for all function arguments and returns
- Use Optional for nullable types
- Import from typing module
- Gradual adoption: warnings enabled, strict checking in production

```python
# ✅ Correct
from typing import List, Optional, Dict, Any

def process_strategy(
    strategy_id: int,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    pass
```

**Docstrings:**

- Google style docstrings
- Triple quotes for module/function/class docs
- Describe args, returns, raises

```python
# ✅ Correct
def create_strategy(user_id: int, name: str) -> Strategy:
    """Create a new strategy.

    Args:
        user_id: Owner user ID
        name: Strategy name

    Returns:
        Created strategy object
    """
    pass
```

**Error Handling:**

- Use async/await with try/except
- Log errors with context
- Raise HTTPException for API errors
- Never use bare except

```python
# ✅ Correct
try:
    strategy = await get_strategy(strategy_id)
    return strategy
except ValueError as e:
    logger.error(f"Invalid strategy data: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

---

## Available Agents

### 🔍 `code-analyzer`

- **Purpose**: Hunt bugs across multiple files without polluting main context
- **Pattern**: Search many files → Analyze code → Return bug report
- **Usage**: When you need to trace logic flows, find bugs, or validate changes
- **Returns**: Concise bug report with critical findings only

### 📄 `file-analyzer`

- **Purpose**: Read and summarize verbose files (logs, outputs, configs)
- **Pattern**: Read files → Extract insights → Return summary
- **Usage**: When you need to understand log files or analyze verbose output
- **Returns**: Key findings and actionable insights (80-90% size reduction)

### 🧪 `test-runner`

- **Purpose**: Execute tests without dumping output to main thread
- **Pattern**: Run tests → Capture to log → Analyze results → Return summary
- **Usage**: When you need to run tests and understand failures
- **Returns**: Test results summary with failure analysis

### 🔀 `parallel-worker`

- **Purpose**: Coordinate multiple parallel work streams for an issue
- **Pattern**: Read analysis → Spawn sub-agents → Consolidate results → Return
  summary
- **Usage**: When executing parallel work streams in a worktree
- **Returns**: Consolidated status of all parallel work

## Why Agents?

Agents are **context firewalls** that protect the main conversation from
information overload:

```
Without Agent:
Main thread reads 10 files → Context explodes → Loses coherence

With Agent:
Agent reads 10 files → Main thread gets 1 summary → Context preserved
```

## How Agents Preserve Context

1. **Heavy Lifting** - Agents do the messy work (reading files, running tests,
   implementing features)
2. **Context Isolation** - Implementation details stay in the agent, not the
   main thread
3. **Concise Returns** - Only essential information returns to main conversation
4. **Parallel Execution** - Multiple agents can work simultaneously without
   context collision

## Example Usage

```bash
# Analyzing code for bugs
Task: "Search for memory leaks in the codebase"
Agent: code-analyzer
Returns: "Found 3 potential leaks: [concise list]"
Main thread never sees: The hundreds of files examined

# Running tests
Task: "Run authentication tests"
Agent: test-runner
Returns: "2/10 tests failed: [failure summary]"
Main thread never sees: Verbose test output and logs

# Parallel implementation
Task: "Implement issue #1234 with parallel streams"
Agent: parallel-worker
Returns: "Completed 4/4 streams, 15 files modified"
Main thread never sees: Individual implementation details
```

## Creating New Agents

New agents should follow these principles:

1. **Single Purpose** - Each agent has one clear job
2. **Context Reduction** - Return 10-20% of what you process
3. **No Roleplay** - Agents aren't "experts", they're task executors
4. **Clear Pattern** - Define input → processing → output pattern
5. **Error Handling** - Gracefully handle failures and report clearly

## Anti-Patterns to Avoid

❌ **Creating "specialist" agents** (database-expert, api-expert) Agents don't
have different knowledge - they're all the same model

❌ **Returning verbose output** Defeats the purpose of context preservation

❌ **Making agents communicate with each other** Use a coordinator agent instead
(like parallel-worker)

❌ **Using agents for simple tasks** Only use agents when context reduction is
valuable

## Integration with PM System

Agents integrate seamlessly with the PM command system:

- `/pm:issue-analyze` → Identifies work streams
- `/pm:issue-start` → Spawns parallel-worker agent
- parallel-worker → Spawns multiple sub-agents
- Sub-agents → Work in parallel in the worktree
- Results → Consolidated back to main thread

This creates a hierarchy that maximizes parallelism while preserving context at
every level.
