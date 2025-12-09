#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Check and Installation Script
Checks for missing dependencies and installs them
"""

import subprocess
import sys
import importlib

def check_and_install_package(package_name, import_name=None):
    """Check if a package is installed and install it if missing"""

    if import_name is None:
        import_name = package_name

    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} is already installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is missing - installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅ {package_name} installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package_name}: {e}")
            return False

def check_fastapi_dependencies():
    """Check FastAPI-specific dependencies"""

    print("🔍 Checking FastAPI dependencies...")

    critical_deps = [
        ("fastapi", "fastapi"),
        ("uvicorn[standard]", "uvicorn"),
        ("pydantic", "pydantic"),
        ("starlette", "starlette"),
        ("python-multipart", "multipart"),
    ]

    security_deps = [
        ("bleach", "bleach"),
        ("python-jose[cryptography]", "jose"),  # For JWT
        ("passlib[bcrypt]", "passlib"),
        ("python-multipart", "multipart"),
    ]

    performance_deps = [
        ("redis", "redis"),
        ("psutil", "psutil"),
        ("aiofiles", "aiofiles"),
    ]

    all_installed = True

    print("\n📦 Critical FastAPI Dependencies:")
    for package, import_name in critical_deps:
        if not check_and_install_package(package, import_name):
            all_installed = False

    print("\n🔒 Security Dependencies:")
    for package, import_name in security_deps:
        if not check_and_install_package(package, import_name):
            print(f"⚠️  Optional security package {package} not installed")

    print("\n⚡ Performance Dependencies:")
    for package, import_name in performance_deps:
        if not check_and_install_package(package, import_name):
            print(f"⚠️  Optional performance package {package} not installed")

    return all_installed

def create_requirements_file():
    """Create a requirements.txt file with all needed dependencies"""

    requirements = """# FastAPI Core Dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
starlette>=0.27.0
python-multipart>=0.0.6

# Security Dependencies
bleach>=6.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# Performance & Monitoring
redis>=5.0.0
psutil>=5.9.0
aiofiles>=23.0.0

# Optional but Recommended
httpx>=0.25.0
websockets>=12.0
"""

    with open("requirements_fixed.txt", "w") as f:
        f.write(requirements)

    print("📄 Created requirements_fixed.txt")

def test_imports():
    """Test that all critical imports work"""

    print("\n🧪 Testing critical imports...")

    test_imports = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "starlette.middleware.cors",
        "fastapi.responses",
        "fastapi.exceptions"
    ]

    success_count = 0

    for module_name in test_imports:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module_name}: {e}")

    print(f"\n📊 Import success rate: {success_count}/{len(test_imports)}")
    return success_count == len(test_imports)

def main():
    """Main dependency check function"""

    print("🚨 CBSC Dependency Check & Fix")
    print("=" * 50)

    # Check dependencies
    deps_ok = check_fastapi_dependencies()

    # Create requirements file
    create_requirements_file()

    # Test imports
    imports_ok = test_imports()

    print("\n" + "=" * 50)

    if deps_ok and imports_ok:
        print("✅ All dependencies are properly installed!")
        print("\n📋 NEXT STEPS:")
        print("1. Run: python fix_security_validator.py")
        print("2. Run: python fix_cors_middleware.py")
        print("3. Start your FastAPI server: python production_demo_working.py")
        print("4. Test: curl http://localhost:8000/api/health")
    else:
        print("⚠️  Some dependencies are missing or broken")
        print("\n🔧 MANUAL FIXES NEEDED:")
        if not deps_ok:
            print("1. Install missing packages manually")
        if not imports_ok:
            print("2. Check Python path and environment")
        print("3. Try: pip install -r requirements_fixed.txt")

    print("=" * 50)

if __name__ == "__main__":
    main()