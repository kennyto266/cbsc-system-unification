# Requirements Quick Reference Guide
# 依赖文件快速参考指南

**Last Updated**: 2025-01-04

---

## 📋 Three Files Overview

### 1️⃣ requirements.txt (Production)
**Use for**: Production deployments, Docker images, cloud environments

```bash
pip install -r requirements.txt
```

**What's inside**:
- Core framework (FastAPI, Uvicorn)
- Data processing (pandas 2.2.3, numpy 1.26.4)
- Database (SQLAlchemy, PostgreSQL, Redis)
- Backtesting (vectorbt, quantstats)
- Monitoring & logging

**Package count**: 86 packages
**Pinned versions**: 51 packages
**Flexible versions**: 35 packages (for compatible updates)

---

### 2️⃣ requirements-dev.txt (Development)
**Use for**: Local development, debugging, documentation

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

**What's inside**:
- Code quality (black, isort, flake8, pylint)
- Testing framework (pytest, coverage)
- Interactive tools (Jupyter, IPython)
- Debugging (ipdb, pudb, py-spy)
- Documentation (Sphinx, MkDocs)

**Package count**: 62 packages
**All packages pinned**: Yes

---

### 3️⃣ requirements-test.txt (Testing)
**Use for**: CI/CD pipelines, automated testing

```bash
pip install -r requirements.txt -r requirements-test.txt
```

**What's inside**:
- Testing framework (pytest, pytest-asyncio, pytest-cov)
- Mocking (pytest-mock, responses, freezegun)
- API testing (httpx, websockets)
- Performance testing (locust, pytest-benchmark)
- Property-based testing (hypothesis)

**Package count**: 71 packages
**All packages pinned**: Yes (except 1)

---

## 🚀 Common Scenarios

### Scenario 1: New Developer Setup
```bash
# Step 1: Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Step 2: Install production dependencies
pip install -r requirements.txt

# Step 3: Install development tools (optional)
pip install -r requirements-dev.txt

# Step 4: Verify installation
python -c "import pandas, numpy; print(f'pandas: {pandas.__version__}, numpy: {numpy.__version__}')"
# Expected: pandas: 2.2.3, numpy: 1.26.4
```

### Scenario 2: Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Scenario 3: CI/CD Pipeline
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest tests/ -v
```

### Scenario 4: Updating Dependencies
```bash
# 1. Check for security vulnerabilities
pip-audit

# 2. Check for outdated packages
pip list --outdated

# 3. Update specific package
pip install --upgrade package-name

# 4. Update requirements.txt with new version
# Edit requirements.txt: package-name==X.Y.Z

# 5. Test thoroughly
pytest tests/ -v

# 6. Commit changes
git add requirements.txt
git commit -m "chore: upgrade package-name to X.Y.Z"
```

---

## 🔍 Version Verification

### Quick Check
```bash
# Check pandas and numpy versions
python -c "import pandas, numpy; print(f'pandas: {pandas.__version__}, numpy: {numpy.__version__}')"
```

### Detailed Check
```bash
# List all installed packages
pip list

# Check for version conflicts
pip-check --disable-notice

# View dependency tree
pipdeptree

# Export current environment
pip freeze > current_environment.txt
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: pandas/numpy version mismatch
**Symptom**: Import errors, numerical inconsistencies
**Solution**:
```bash
pip uninstall pandas numpy -y
pip install pandas==2.2.3 numpy==1.26.4
```

### Issue 2: Dependency conflict
**Symptom**: pip install fails with conflict error
**Solution**:
```bash
# View conflict details
pip install --dry-run -r requirements.txt

# Force reinstall
pip install --force-reinstall -r requirements.txt
```

### Issue 3: TA-Lib installation fails
**Symptom**: "Command errored out with exit status 1"
**Solution**:
```bash
# Use binary version instead
pip install talib-binary

# Or install from system package manager
# Ubuntu/Debian:
sudo apt-get install ta-lib
pip install TA-Lib
```

### Issue 4: Outdated pip version
**Symptom**: Warning about pip version
**Solution**:
```bash
pip install --upgrade pip
```

---

## 📊 Statistics Summary

| File | Packages | Pinned | Flexible | Purpose |
|------|----------|--------|----------|---------|
| requirements.txt | 86 | 51 | 35 | Production |
| requirements-dev.txt | 62 | 62 | 0 | Development |
| requirements-test.txt | 71 | 70 | 1 | Testing |
| **Total** | **219** | **183** | **36** | All |

---

## 🎯 Key Points to Remember

1. **Always use requirements.txt** as the base for all installations
2. **pandas==2.2.3 and numpy==1.26.4** are the critical unified versions
3. **Pin versions** (==) for stability in production
4. **Use flexible versions** (>=) only for compatible libraries
5. **Test thoroughly** after any version change
6. **Document changes** in requirements.txt comments
7. **Archive old files** in `.archive/requirements/`

---

## 📚 Additional Resources

- **Full Report**: `PYTHON_DEPENDENCIES_UNIFICATION_REPORT.md`
- **Summary**: `DEPENDENCY_UNIFICATION_SUMMARY.md`
- **Archive**: `.archive/requirements/README.md`

---

**Quick Commands**:
```bash
# Install everything
pip install -r requirements.txt -r requirements-dev.txt -r requirements-test.txt

# Run tests
pytest tests/ -v

# Check versions
python -c "import pandas, numpy; print(f'pandas: {pandas.__version__}, numpy: {numpy.__version__}')"

# Security audit
pip-audit
```

---

**Last Updated**: 2025-01-04
**Maintained by**: Dependency Management Specialist
