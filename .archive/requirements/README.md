# Archived Requirements Files

## Archive Date
2025-01-04

## Purpose
These files were archived during the Python dependency unification process.
They are kept for historical reference but should NOT be used in production.

## Deprecated Files

### Main Directory
- `requirements-prod.txt` - Old production dependencies (pandas 2.1.4, numpy 1.25.2)
- `requirements-real.txt` - Real backend dependencies (pandas 2.1.4, numpy 1.25.2)
- `requirements_comprehensive.txt` - Comprehensive dependencies (unpinned versions)
- `requirements.auth.txt` - Authentication-specific dependencies
- `requirements-ci.txt` - CI/CD dependencies

### Main Directory Backup (root)
- `requirements.txt` - Original root requirements (pandas 2.2.3, numpy 1.24.3)
- `requirements-prod.txt` - Production version
- `requirements-real.txt` - Real backend version
- `requirements_comprehensive.txt` - Comprehensive version
- `requirements.auth.txt` - Auth version
- `requirements-ci.txt` - CI version

### Src Directory
- `src.requirements.txt` - Original src requirements (pandas 2.1.3, numpy 1.25.2)
- `src.requirements_mfa.txt` - MFA-specific requirements
- `src.requirements-dev.txt` - Development requirements

### Backend Directory
- `backend.requirements.txt` - Original backend requirements (unpinned versions)

## Version Conflicts Resolved

### pandas
- **Old versions**: 2.1.3, 2.1.4, 2.2.3
- **New unified version**: 2.2.3 (latest stable)

### numpy
- **Old versions**: 1.24.3, 1.25.2
- **New unified version**: 1.26.4 (latest compatible with pandas 2.2.3)

## Migration Path

1. **For new installations**: Use root `requirements.txt`
2. **For development**: Add `requirements-dev.txt`
3. **For testing**: Add `requirements-test.txt`

Example:
```bash
# Production
pip install -r requirements.txt

# Development
pip install -r requirements.txt -r requirements-dev.txt

# Testing
pip install -r requirements.txt -r requirements-test.txt
```

## Notes

- All version conflicts have been resolved
- Packages are pinned to exact versions for stability
- The unified requirements.txt is the single source of truth
- Subproject requirements files (src, backend) now reference the root file
