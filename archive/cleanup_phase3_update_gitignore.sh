#!/bin/bash
###############################################################################
# QUANT SYSTEM CLEANUP - PHASE 3: UPDATE .GITIGNORE
# This script updates .gitignore to prevent future accumulation
###############################################################################

set -e  # Exit on error

echo "============================================================================="
echo "QUANT SYSTEM CLEANUP - PHASE 3: UPDATE .GITIGNORE"
echo "============================================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backup existing .gitignore
if [ -f ".gitignore" ]; then
    echo "Backing up existing .gitignore to .gitignore.backup"
    cp .gitignore .gitignore.backup
fi

echo "Updating .gitignore..."

# Create comprehensive .gitignore
cat > .gitignore << 'EOF'
# =============================================================================
# QUANTITATIVE TRADING SYSTEM - .GITIGNORE
# Auto-generated on cleanup - prevents future file bloat
# =============================================================================

# ----------------------------
# System Files
# ----------------------------
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
*.log

# ----------------------------
# Python
# ----------------------------
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environments
venv*/
.venv*/
env*/
.env*/
ENV/
.env

# PyCharm
.idea/

# Jupyter Notebook
.ipynb_checkpoints

# ----------------------------
# Node.js & Frontend
# ----------------------------
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn-integrity

# Frontend build outputs
frontend/dist/
frontend/build/
frontend/.next/
frontend/out/

# React / Vue
.react
.vue

# ----------------------------
# Rust
# ----------------------------
target/
Cargo.lock
**/*.rs.bk

# ----------------------------
# Quant System Specific
# ----------------------------
# Log files
*.log
logs/
log/

# Data files (keep structure, not content)
data/raw/*
!data/raw/.gitkeep
data/cache/*
!data/cache/.gitkeep
data/user_data/*
!data/user_data/.gitkeep

# Configuration (keep templates)
config/*.json
!config/*.template.json

# Backtest results
backtest_results/
*.backtest.json
results/
performance_reports/

# User workspace data
workspace_data/users/*

# Temporary files
tmp/
temp/
*.tmp
*.temp

# ----------------------------
# Archive (auto-generated files)
# ----------------------------
archive/large-files/
archive/deprecated/

# ----------------------------
# Database
# ----------------------------
*.db
*.sqlite
*.sqlite3

# ----------------------------
# Cache Directories
# ----------------------------
.cache/
.parcel-cache/
.npm/
.eslintcache
.stylelintcache

# ----------------------------
# Testing
# ----------------------------
.coverage
.pytest_cache/
htmlcov/
.tox/
.nox/

# Coverage reports
coverage.xml
*.cover
.hypothesis/

# ----------------------------
# IDEs
# ----------------------------
.vscode/
.idea/
*.swp
*.swo
*~

# ----------------------------
# OS
# ----------------------------
.directory
Trash-*

# ----------------------------
# Misc
# ----------------------------
*.bak
*.backup
*.orig
EOF

echo -e "${GREEN}✓ Created comprehensive .gitignore${NC}"
echo ""

# Also create/update .git/info/exclude for local-only ignores
if [ -d ".git/info" ]; then
    cat >> .git/info/exclude << 'EOF'

# Local git exclude (not shared)
# -------------------------------
# Any files listed here won't be tracked by git
# but won't be shared with other developers

EOF
    echo "Updated .git/info/exclude for local ignores"
fi

echo ""
echo "============================================================================="
echo -e "${GREEN}CLEANUP PHASE 3 COMPLETE!${NC}"
echo "============================================================================="
echo ""
echo "Actions taken:"
echo "  ✓ Backed up original .gitignore to .gitignore.backup"
echo "  ✓ Created comprehensive .gitignore with:"
echo "      - Python (__pycache__, .pyc, venvs, etc.)"
echo "      - Node.js (node_modules, logs, etc.)"
echo "      - Rust (target/, Cargo.lock)"
echo "      - Quant system (logs, data files, etc.)"
echo "      - IDE and system files"
echo "  ✓ Updated .git/info/exclude for local-only ignores"
echo ""
echo "Next time you run git commands:"
echo "  • node_modules won't be tracked"
echo "  • __pycache__ won't be tracked"
echo "  • target/ won't be tracked"
echo "  • *.log files won't be tracked"
echo ""
echo -e "${GREEN}✓ .gitignore updated successfully!${NC}"
echo ""
echo "============================================================================="
