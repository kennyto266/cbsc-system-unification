"""
Test fixtures for notebook execution testing

Provides sample notebooks and test data for execution tests.
"""

import json
import os
from pathlib import Path


def create_simple_notebook(output_path: str) -> None:
    """
    Create a simple test notebook with basic operations

    Args:
        output_path: Where to save the notebook
    """
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Simple Test Notebook\n", "\n", "This notebook tests basic execution."]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "\n",
                    "print('Libraries imported successfully')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Create test data\n",
                    "data = pd.DataFrame({\n",
                    "    'price': [100, 102, 101, 103, 105, 104, 106],\n",
                    "    'volume': [1000, 1200, 900, 1100, 1300, 950, 1150]\n",
                    "})\n",
                    "\n",
                    "print('Test data created:')\n",
                    "print(data)"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Calculate simple statistics\n",
                    "avg_price = data['price'].mean()\n",
                    "total_volume = data['volume'].sum()\n",
                    "\n",
                    "print(f'Average price: {avg_price:.2f}')\n",
                    "print(f'Total volume: {total_volume}')"
                ]
            }
        ],
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

    with open(output_path, 'w') as f:
        json.dump(notebook, f, indent=2)


def create_error_notebook(output_path: str) -> None:
    """
    Create a notebook with intentional syntax errors

    Args:
        output_path: Where to save the notebook
    """
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    "x = 10"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# This cell has syntax errors\n",
                    "invalid syntax here !!!\n",
                    "more bad syntax"
                ]
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with open(output_path, 'w') as f:
        json.dump(notebook, f, indent=2)


def create_strategy_notebook(output_path: str) -> None:
    """
    Create a simple trading strategy notebook

    Args:
        output_path: Where to save the notebook
    """
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Simple Moving Average Strategy\n"]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "\n",
                    "# Configuration\n",
                    "SYMBOL = 'AAPL'\n",
                    "SHORT_MA = 5\n",
                    "LONG_MA = 10\n",
                    "\n",
                    "print(f'Testing {SYMBOL} with MA({SHORT_MA}) and MA({LONG_MA)})')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Generate sample price data\n",
                    "np.random.seed(42)\n",
                    "prices = np.random.randn(20).cumsum() + 100\n",
                    "dates = pd.date_range('2024-01-01', periods=20)\n",
                    "\n",
                    "data = pd.DataFrame({\n",
                    "    'date': dates,\n",
                    "    'close': prices\n",
                    "}).set_index('date')\n",
                    "\n",
                    "print(data.head())"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Calculate moving averages\n",
                    "data['ma_short'] = data['close'].rolling(SHORT_MA).mean()\n",
                    "data['ma_long'] = data['close'].rolling(LONG_MA).mean()\n",
                    "\n",
                    "# Generate signals\n",
                    "data['signal'] = 0\n",
                    "data.loc[data['ma_short'] > data['ma_long'], 'signal'] = 1\n",
                    "\n",
                    "print('Signals generated:')\n",
                    "print(data[['close', 'ma_short', 'ma_long', 'signal']].tail())"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Calculate returns\n",
                    "data['returns'] = data['close'].pct_change()\n",
                    "\n",
                    "# Strategy return (next day return if signal is 1)\n",
                    "data['strategy_return'] = data['returns'].shift(-1) * data['signal']\n",
                    "\n",
                    "total_return = data['strategy_return'].sum()\n",
                    "print(f'Total Strategy Return: {total_return:.2%}')"
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

    with open(output_path, 'w') as f:
        json.dump(notebook, f, indent=2)


def create_empty_notebook(output_path: str) -> None:
    """
    Create an empty notebook with just metadata

    Args:
        output_path: Where to save the notebook
    """
    notebook = {
        "cells": [],
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

    with open(output_path, 'w') as f:
        json.dump(notebook, f, indent=2)


if __name__ == '__main__':
    """
    Main entry point for creating test fixtures
    Run this script to generate all test notebooks
    """
    import sys

    # Set UTF-8 encoding for output
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    fixtures_dir = Path(__file__).parent

    print(f'Creating test fixtures in {fixtures_dir}...')

    # Create test notebooks
    create_simple_notebook(fixtures_dir / 'simple_test.ipynb')
    print('OK Created simple_test.ipynb')

    create_error_notebook(fixtures_dir / 'error_test.ipynb')
    print('OK Created error_test.ipynb')

    create_strategy_notebook(fixtures_dir / 'strategy_test.ipynb')
    print('OK Created strategy_test.ipynb')

    create_empty_notebook(fixtures_dir / 'empty_test.ipynb')
    print('OK Created empty_test.ipynb')

    print('\nAll test fixtures created successfully!')
    print(f'Location: {fixtures_dir}')
