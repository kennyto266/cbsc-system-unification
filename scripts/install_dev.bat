@echo off
REM CBSC Strategy Workflow Development Environment Setup Script
REM Supports: Windows
REM Python: 3.10+

setlocal enabledelayedexpansion

REM Configuration
set PYTHON_MIN_VERSION=3.10
set VENV_DIR=.venv
set PROJECT_NAME=CBSC Strategy Workflow

REM Colors (not supported in standard cmd, but structure kept for clarity)
set "INFO=[INFO]"
set "SUCCESS=[OK]"
set "WARNING=[WARN]"
set "ERROR=[ERROR]"

REM Functions
:print_header
echo.
echo ========================================
echo %~1
echo ========================================
echo.
exit /b 0

:check_python_version
echo %INFO% Checking Python version...

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo %ERROR% Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Parse version (simplified check)
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
if %ERRORLEVEL% neq 0 (
    echo %ERROR% Python %PYTHON_MIN_VERSION% or higher is required
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

echo %SUCCESS% Python version check passed
exit /b 0

:create_virtual_environment
echo %INFO% Creating virtual environment...

if exist "%VENV_DIR%" (
    echo %WARNING% Virtual environment already exists at %VENV_DIR%
    set /p RECREATE="Remove and recreate? (y/N): "
    if /i "!RECREATE!"=="y" (
        rmdir /s /q "%VENV_DIR%"
        echo %SUCCESS% Removed existing virtual environment
    ) else (
        echo %SUCCESS% Using existing virtual environment
        exit /b 0
    )
)

python -m venv "%VENV_DIR%"
if %ERRORLEVEL% neq 0 (
    echo %ERROR% Failed to create virtual environment
    pause
    exit /b 1
)

echo %SUCCESS% Virtual environment created at %VENV_DIR%
exit /b 0

:activate_environment
echo %INFO% Activating virtual environment...

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo %ERROR% Virtual environment activation script not found
    pause
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
echo %SUCCESS% Virtual environment activated
exit /b 0

:upgrade_pip
echo %INFO% Upgrading pip and build tools...

python -m pip install --upgrade pip setuptools wheel
if %ERRORLEVEL% neq 0 (
    echo %ERROR% Failed to upgrade pip
    pause
    exit /b 1
)

echo %SUCCESS% pip, setuptools, and wheel upgraded
exit /b 0

:install_package
echo %INFO% Installing %PROJECT_NAME%...

REM Install package in editable mode with dev dependencies
pip install -e ".[dev]"
if %ERRORLEVEL% neq 0 (
    echo %ERROR% Failed to install package
    pause
    exit /b 1
)

echo %SUCCESS% %PROJECT_NAME% installed successfully
exit /b 0

:install_ta_lib
echo %INFO% Installing TA-Lib ^(Optional^)...

set /p INSTALL_TA="Install TA-Lib? ^(requires manual setup^) ^(y/N^): "
if /i "%INSTALL_TA%"=="y" (
    echo %WARNING% TA-Lib on Windows requires manual installation:
    echo 1. Download ta-lib binary from https://github.com/cgohlke/talib-builds/releases
    echo 2. Install ta-lib Python wrapper: pip install TA-Lib
    echo.
    pip install ta-lib
    if %ERRORLEVEL% neq 0 (
        echo %WARNING% TA-Lib installation failed, continuing without it
    ) else (
        echo %SUCCESS% TA-Lib installed
    )
) else (
    echo %INFO% Skipping TA-Lib installation
)
exit /b 0

:create_config_files
echo %INFO% Creating configuration files...

if not exist ".env" (
    if exist ".env.template" (
        copy ".env.template" ".env" >nul
        echo %SUCCESS% Created .env from template
    ) else (
        echo %WARNING% .env.template not found
    )
) else (
    echo %WARNING% .env already exists, skipping
)

if not exist "config" mkdir config

if exist "config\config.template.yaml" (
    if not exist "config\config.yaml" (
        copy "config\config.template.yaml" "config\config.yaml" >nul
        echo %SUCCESS% Created config\config.yaml from template
    )
)
exit /b 0

:setup_pre_commit
echo %INFO% Setting up pre-commit hooks...

if exist ".pre-commit-config.yaml" (
    pip install pre-commit
    pre-commit install
    echo %SUCCESS% Pre-commit hooks installed
) else (
    echo %WARNING% No .pre-commit-config.yaml found, skipping pre-commit setup
)
exit /b 0

:create_directories
echo %INFO% Creating project directories...

if not exist "data\cache" mkdir "data\cache"
if not exist "data\raw" mkdir "data\raw"
if not exist "data\processed" mkdir "data\processed"
if not exist "logs" mkdir logs
if not exist "notebooks\research" mkdir "notebooks\research"
if not exist "notebooks\strategies" mkdir "notebooks\strategies"
if not exist "notebooks\backtests" mkdir "notebooks\backtests"
if not exist "results\backtests" mkdir "results\backtests"
if not exist "results\optimizations" mkdir "results\optimizations"
if not exist "results\analysis" mkdir "results\analysis"
if not exist "tests\unit" mkdir "tests\unit"
if not exist "tests\integration" mkdir "tests\integration"

echo %SUCCESS% Project directories created
exit /b 0

:run_tests
echo %INFO% Running tests...

set /p RUN_TESTS="Run tests to verify installation? ^(Y/n^): "
if /i not "%RUN_TESTS%"=="n" (
    pytest tests/ -v --tb=short
    if %ERRORLEVEL% neq 0 (
        echo %WARNING% Some tests failed, but installation completed
    ) else (
        echo %SUCCESS% All tests passed
    )
) else (
    echo %INFO% Skipping tests
)
exit /b 0

:print_summary
echo.
echo ========================================
echo Installation Complete
echo ========================================
echo.
echo The %PROJECT_NAME% development environment is ready!
echo.
echo Quick Start:
echo   1. Activate the environment:
echo      %VENV_DIR%\Scripts\activate.bat
echo.
echo   2. Start Jupyter Lab:
echo      jupyter lab
echo.
echo   3. Run verification:
echo      python scripts\verify_install.py
echo.
echo For more information, see INSTALL.md
echo.
pause
exit /b 0

:main
call :print_header "%PROJECT_NAME% Installation"

call :check_python_version
if %ERRORLEVEL% neq 0 exit /b 1

call :create_virtual_environment
if %ERRORLEVEL% neq 0 exit /b 1

call :activate_environment
if %ERRORLEVEL% neq 0 exit /b 1

call :upgrade_pip
if %ERRORLEVEL% neq 0 exit /b 1

call :install_package
if %ERRORLEVEL% neq 0 exit /b 1

call :install_ta_lib

call :create_config_files

call :setup_pre_commit

call :create_directories

call :run_tests

call :print_summary
