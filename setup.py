"""
Setup configuration for CBSC Strategy Workflow package.

This setup.py is provided as a fallback for older pip versions.
For modern packaging, pyproject.toml is the primary configuration.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else ""

# Read version from __init__.py
version = "0.1.0"
init_file = this_directory / "cbsc_strategy" / "__init__.py"
if init_file.exists():
    with open(init_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip('"').strip("'")
                break

setup(
    name="cbsc-strategy-workflow",
    version=version,
    author="CBSC Team",
    author_email="dev-team@cbsc.com",
    description="CBSC Data Science Strategy Development Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cbsc/cbsc-strategy-workflow",
    packages=find_packages(exclude=["tests*", "docs*", "scripts*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
        "plotly>=5.14.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.3.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.0",
        "requests>=2.31.0",
        "jupyter>=1.0.0",
        "ipython>=8.12.0",
        "ipywidgets>=8.0.0",
        "notebook>=7.0.0",
        "quantstats>=0.0.59",
        "ta-lib>=0.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
            "black>=23.0.0",
            "pre-commit>=3.5.0",
        ],
        "ml": [
            "tensorflow>=2.15.0",
            "torch>=2.0.0",
            "transformers>=4.35.0",
        ],
        "database": [
            "sqlalchemy>=2.0.0",
            "psycopg2-binary>=2.9.0",
            "redis>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cbsc-backtest=cbsc_strategy.cli:main_backtest",
            "cbsc-validate=cbsc_strategy.cli:main_validate",
        ],
    },
    package_data={
        "cbsc_strategy": [
            "config/*.yaml",
            "config/*.json",
            "indicators/*.yaml",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
