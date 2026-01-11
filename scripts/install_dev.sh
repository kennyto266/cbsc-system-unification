#!/bin/bash
# CBSC Strategy Workflow Development Environment Setup Script
# Supports: Linux, macOS
# Python: 3.10+

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.10"
VENV_DIR=".venv"
PROJECT_NAME="CBSC Strategy Workflow"

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_python_version() {
    print_header "Checking Python Version"

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.10 or higher from https://www.python.org/"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    echo "Found Python $PYTHON_VERSION"

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
        print_error "Python $PYTHON_MIN_VERSION or higher is required"
        echo "Current version: $PYTHON_VERSION"
        exit 1
    fi

    print_success "Python version check passed ($PYTHON_VERSION >= $PYTHON_MIN_VERSION)"
}

create_virtual_environment() {
    print_header "Creating Virtual Environment"

    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists at $VENV_DIR"
        read -p "Remove and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
            print_success "Removed existing virtual environment"
        else
            print_success "Using existing virtual environment"
            return 0
        fi
    fi

    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created at $VENV_DIR"
}

activate_environment() {
    print_header "Activating Virtual Environment"

    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        print_error "Virtual environment activation script not found"
        exit 1
    fi

    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
}

upgrade_pip() {
    print_header "Upgrading pip and build tools"

    pip install --upgrade pip setuptools wheel
    print_success "pip, setuptools, and wheel upgraded"
}

install_package() {
    print_header "Installing $PROJECT_NAME"

    # Install package in editable mode
    pip install -e ".[dev]"

    print_success "$PROJECT_NAME installed successfully"
}

install_ta_lib() {
    print_header "Installing TA-Lib (Optional)"

    read -p "Install TA-Lib? (requires system build tools) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check if ta-lib is already installed
        if python3 -c "import talib" 2>/dev/null; then
            print_success "TA-Lib is already installed"
        else
            print_warning "TA-Lib installation requires system dependencies"
            echo "For macOS: brew install ta-lib"
            echo "For Ubuntu/Debian: sudo apt-get install build-essential wget"
            echo "  wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz"
            echo "  tar -xzf ta-lib-0.4.0-src.tar.gz"
            echo "  cd ta-lib/"
            echo "  ./configure --prefix=/usr"
            echo "  make"
            echo "  sudo make install"
            echo ""

            # Try to install ta-lib Python wrapper
            pip install ta-lib || print_warning "TA-Lib installation failed, continuing without it"
        fi
    else
        print_warning "Skipping TA-Lib installation"
    fi
}

create_config_files() {
    print_header "Creating Configuration Files"

    # Copy .env template
    if [ ! -f ".env" ]; then
        if [ -f ".env.template" ]; then
            cp .env.template .env
            print_success "Created .env from template"
        else
            print_warning ".env.template not found"
        fi
    else
        print_warning ".env already exists, skipping"
    fi

    # Create config directory if needed
    mkdir -p config

    # Copy config template
    if [ -f "config/config.template.yaml" ] && [ ! -f "config/config.yaml" ]; then
        cp config/config.template.yaml config/config.yaml
        print_success "Created config/config.yaml from template"
    fi
}

setup_pre_commit() {
    print_header "Setting Up Pre-commit Hooks"

    if [ -f ".pre-commit-config.yaml" ]; then
        pip install pre-commit
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_warning "No .pre-commit-config.yaml found, skipping pre-commit setup"
    fi
}

create_directories() {
    print_header "Creating Project Directories"

    mkdir -p data/{cache,raw,processed}
    mkdir -p logs
    mkdir -p notebooks/{research,strategies,backtests}
    mkdir -p results/{backtests,optimizations,analysis}
    mkdir -p tests/{unit,integration}

    print_success "Project directories created"
}

run_tests() {
    print_header "Running Tests"

    read -p "Run tests to verify installation? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        if pytest tests/ -v --tb=short; then
            print_success "All tests passed"
        else
            print_warning "Some tests failed, but installation completed"
        fi
    else
        print_warning "Skipping tests"
    fi
}

print_summary() {
    print_header "Installation Complete"

    echo ""
    echo -e "${GREEN}The $PROJECT_NAME development environment is ready!${NC}"
    echo ""
    echo "Quick Start:"
    echo "  1. Activate the environment:"
    echo -e "     ${BLUE}source $VENV_DIR/bin/activate${NC}"
    echo ""
    echo "  2. Start Jupyter Lab:"
    echo -e "     ${BLUE}jupyter lab${NC}"
    echo ""
    echo "  3. Run verification:"
    echo -e "     ${BLUE}python scripts/verify_install.py${NC}"
    echo ""
    echo "For more information, see INSTALL.md"
    echo ""
}

# Main installation flow
main() {
    print_header "$PROJECT_NAME Installation"

    check_python_version
    create_virtual_environment
    activate_environment
    upgrade_pip
    install_package
    install_ta_lib
    create_config_files
    setup_pre_commit
    create_directories
    run_tests
    print_summary
}

# Run main function
main
