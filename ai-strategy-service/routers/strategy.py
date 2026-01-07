"""
FastAPI Router for Strategy Generation
Handles AI-powered trading strategy generation using GLM API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import sys
import os
import re

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.glm_service import GLMService, GLMMessage

router = APIRouter(prefix="/api/strategy", tags=["strategy"])


class StrategyRequest(BaseModel):
    """Request model for strategy generation"""
    description: str = Field(..., description="Natural language description of the strategy")
    market: Optional[str] = Field(default="stock", description="Market type (stock, crypto, forex)")
    timeframe: Optional[str] = Field(default="daily", description="Timeframe (minute, hourly, daily)")
    risk_level: Optional[str] = Field(default="medium", description="Risk level (low, medium, high)")


class StrategyResponse(BaseModel):
    """Response model for generated strategy"""
    code: str = Field(..., description="Generated Python code")
    explanation: str = Field(..., description="Strategy explanation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters")
    model: str = Field(default="glm-4-plus", description="AI model used")


class ChatRequest(BaseModel):
    """Request model for general chat"""
    message: str = Field(..., description="User message")
    history: Optional[list] = Field(default_factory=list, description="Chat history")


class ChatResponse(BaseModel):
    """Response model for chat"""
    response: str = Field(..., description="AI response")
    is_strategy: bool = Field(default=False, description="Whether response is a strategy")


@router.post("/generate", response_model=StrategyResponse)
async def generate_strategy(request: StrategyRequest):
    """
    Generate trading strategy from description using GLM AI

    Args:
        request: Strategy generation request with description and parameters

    Returns:
        StrategyResponse with generated code, explanation, and parameters
    """
    try:
        glm_service = GLMService()

        # Construct system prompt with context
        system_prompt_content = f"""You are a quantitative trading strategy expert. Generate Python code for trading strategies.

Requirements:
- Market: {request.market}
- Timeframe: {request.timeframe}
- Risk Level: {request.risk_level}

Generate a complete Jupyter notebook with the following structure:
1. Cell 1: Imports and setup (pandas, numpy, matplotlib)
2. Cell 2: Data fetching function (placeholder for CBSC data integration)
3. Cell 3: Strategy parameters definition
4. Cell 4: Signal generation logic
5. Cell 5: Simple backtesting
6. Cell 6: Visualization and performance metrics

Return ONLY valid Python code. Wrap each cell in triple backticks with python marker.
Format example:
```python
# Cell 1: Imports
import pandas as pd
import numpy as np
```
```python
# Cell 2: Data fetching
def fetch_data(symbol, start, end):
    ...
```
etc.

Ensure the code is production-ready and follows best practices."""

        system_prompt = GLMMessage(
            role="system",
            content=system_prompt_content
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
            parameters=parameters,
            model="glm-4-plus"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy generation failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    General chat endpoint for strategy-related questions

    Args:
        request: Chat request with message and optional history

    Returns:
        ChatResponse with AI response
    """
    try:
        glm_service = GLMService()

        # Build message list
        messages = []

        # Add history if provided
        if request.history:
            for msg in request.history:
                messages.append(GLMMessage(**msg))

        # Add current message
        messages.append(GLMMessage(role="user", content=request.message))

        # Get AI response
        response = await glm_service.chat(messages)

        await glm_service.close()

        # Check if response contains strategy code
        is_strategy = contains_strategy_code(response)

        return ChatResponse(
            response=response,
            is_strategy=is_strategy
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


def parse_code_cells(response: str) -> str:
    """
    Parse AI response to extract code cells

    Args:
        response: AI response text

    Returns:
        Concatenated code cells with markers
    """
    # Split by python code blocks
    code_blocks = re.findall(r'```python\n(.*?)```', response, re.DOTALL)

    if not code_blocks:
        # Fallback: try to find any code blocks
        code_blocks = re.findall(r'```\n(.*?)```', response, re.DOTALL)

    # If still no blocks, try extracting all Python code
    if not code_blocks:
        # Look for common Python patterns
        lines = response.split('\n')
        in_code = False
        current_block = []

        for line in lines:
            if line.strip().startswith('```'):
                in_code = not in_code
                if not in_code and current_block:
                    code_blocks.append('\n'.join(current_block))
                    current_block = []
            elif in_code:
                current_block.append(line)
            elif line.strip().startswith('import ') or line.strip().startswith('from '):
                # Start of code without explicit block
                if current_block:
                    code_blocks.append('\n'.join(current_block))
                current_block = [line]

        if current_block:
            code_blocks.append('\n'.join(current_block))

    # Join cells with cell markers
    cells = []
    for i, block in enumerate(code_blocks):
        cells.append(f"# Cell {i+1}\n{block.strip()}\n")

    return '\n'.join(cells) if cells else response


def extract_explanation(response: str) -> str:
    """
    Extract explanation from AI response

    Args:
        response: AI response text

    Returns:
        Explanation text
    """
    lines = response.split('\n')
    explanation_lines = []
    in_code_block = False

    for line in lines:
        if '```' in line:
            in_code_block = not in_code_block
            continue

        if not in_code_block and line.strip() and not line.strip().startswith('#'):
            # Skip markdown headers
            if not line.strip().startswith('#'):
                explanation_lines.append(line.strip())

    # Return first few non-code lines as explanation
    return '\n'.join(explanation_lines[:5]) if explanation_lines else "Trading strategy generated successfully."


def extract_parameters(response: str) -> Dict[str, Any]:
    """
    Extract strategy parameters from AI response

    Args:
        response: AI response text

    Returns:
        Dictionary of extracted parameters
    """
    params = {}

    # Look for common parameter patterns
    param_patterns = {
        'LOOKBACK': r'LOOKBACK\s*=\s*(\d+)',
        'THRESHOLD': r'THRESHOLD\s*=\s*([\d.]+)',
        'STOP_LOSS': r'STOP_LOSS\s*=\s*([\d.]+)',
        'TAKE_PROFIT': r'TAKE_PROFIT\s*=\s*([\d.]+)',
        'SYMBOL': r'SYMBOL\s*=\s*["\']([\w\-]+)["\']',
        'SHORT_MA': r'SHORT_MA\s*=\s*(\d+)',
        'LONG_MA': r'LONG_MA\s*=\s*(\d+)',
        'RISK_LEVEL': r'risk_level\s*=\s*["\']([\w]+)["\']',
    }

    for name, pattern in param_patterns.items():
        match = re.search(pattern, response)
        if match:
            params[name.lower()] = match.group(1)

    return params


def contains_strategy_code(text: str) -> bool:
    """
    Check if text contains strategy code

    Args:
        text: Text to check

    Returns:
        True if text contains strategy code
    """
    strategy_keywords = [
        'import pandas', 'import numpy', 'def ', '= pd.',
        'strategy', 'backtest', 'signal', 'indicator'
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in strategy_keywords)


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "strategy-generation"}
