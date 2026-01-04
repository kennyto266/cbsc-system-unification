#!/usr/bin/env python3
"""
Unified Strategy Routes Verification
統一策略路由驗證腳本

Verify that the unified strategy routers are correctly configured
"""

import ast
import sys
from pathlib import Path


def extract_router_info(file_path):
    """Extract router information from a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)

    routes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'router':
                    # Find APIRouter() call
                    if isinstance(node.value, ast.Call):
                        for keyword in node.value.keywords:
                            if keyword.arg == 'prefix':
                                if isinstance(keyword.value, ast.Constant):
                                    prefix = keyword.value.value
                                    routes.append(prefix)

    # Also find @router decorators
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                # Check for @router.get, @router.post, etc.
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute):
                        if hasattr(decorator.func.value, 'id') and decorator.func.value.id == 'router':
                            method = decorator.func.attr
                            # Extract path from first argument
                            if decorator.args:
                                arg = decorator.args[0]
                                if isinstance(arg, ast.Constant):
                                    path = arg.value
                                    routes.append(f"{method.upper()} {path}")

    return routes


def verify_imports_in_main():
    """Verify that unified routers are imported in main.py"""
    main_py = Path("src/main.py")

    if not main_py.exists():
        print("ERROR: src/main.py not found")
        return False

    content = main_py.read_text(encoding='utf-8')

    checks = {
        'unified_crud_router_import': 'unified_crud_router' in content and 'from api.strategies.v2 import' in content,
        'unified_operation_router_import': 'unified_operation_router' in content and 'from api.strategies.v2 import' in content,
        'unified_crud_router_registered': 'unified_crud_router' in content and 'include_router' in content,
        'unified_operation_router_registered': 'unified_operation_router' in content and 'include_router' in content,
    }

    print("Main.py Verification:")
    print("=" * 50)
    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check}")
    print()

    return all(checks.values())


def verify_router_files():
    """Verify that router files exist and are valid Python"""
    files = {
        ('src/api/strategies/v2', 'unified_crud_endpoints.py'): 'Unified CRUD Endpoints',
        ('src/api/strategies/v2', 'unified_operation_endpoints.py'): 'Unified Operation Endpoints',
        ('src/services', 'unified_strategy_service.py'): 'Unified Strategy Service',
        ('src/api/strategies/v2', '__init__.py'): 'v2 Package Init',
    }

    print("Router Files Verification:")
    print("=" * 50)

    all_exist = True
    for (dir_path, file_name), description in files.items():
        file_path = Path(dir_path) / file_name
        exists = file_path.exists()

        if exists:
            # Verify syntax
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
                print(f"  [PASS] {description} ({file_name})")
            except SyntaxError as e:
                print(f"  [FAIL] {description} ({file_name}) - Syntax Error: {e}")
                all_exist = False
        else:
            print(f"  [FAIL] {description} ({file_name}) - Not Found")
            all_exist = False

    print()
    return all_exist


def verify_endpoint_definitions():
    """Verify endpoint definitions in router files"""
    print("Endpoint Definitions:")
    print("=" * 50)

    # Check unified_crud_endpoints.py
    crud_file = Path("src/api/strategies/v2/unified_crud_endpoints.py")
    crud_content = crud_file.read_text(encoding='utf-8')

    crud_endpoints = [
        ("list_strategies", "GET /strategies"),
        ("create_strategy", "POST /strategies"),
        ("get_strategy", "GET /strategies/{strategy_id}"),
        ("update_strategy", "PUT /strategies/{strategy_id}"),
        ("delete_strategy", "DELETE /strategies/{strategy_id}"),
    ]

    print("  Unified CRUD Endpoints:")
    for func_name, expected_path in crud_endpoints:
        found = func_name in crud_content
        status = "PASS" if found else "FAIL"
        print(f"    [{status}] {expected_path} ({func_name})")

    print()

    # Check unified_operation_endpoints.py
    operation_file = Path("src/api/strategies/v2/unified_operation_endpoints.py")
    operation_content = operation_file.read_text(encoding='utf-8')

    operation_endpoints = [
        ("execute_strategy", "POST /strategies/{strategy_id}/execute"),
        ("stop_strategy", "POST /strategies/{strategy_id}/stop"),
        ("get_strategy_status", "GET /strategies/{strategy_id}/status"),
        ("activate_strategy", "POST /strategies/{strategy_id}/activate"),
        ("pause_strategy", "POST /strategies/{strategy_id}/pause"),
        ("duplicate_strategy", "POST /strategies/{strategy_id}/duplicate"),
        ("batch_operation", "POST /strategies/batch"),
    ]

    print("  Unified Operation Endpoints:")
    for func_name, expected_path in operation_endpoints:
        found = func_name in operation_content
        status = "PASS" if found else "FAIL"
        print(f"    [{status}] {expected_path} ({func_name})")

    print()


def main():
    """Main verification function"""
    print("Unified Strategy Routes Verification")
    print("=" * 60)
    print()

    results = []

    # Verify files exist
    results.append(("Router Files", verify_router_files()))

    # Verify endpoint definitions
    verify_endpoint_definitions()

    # Verify main.py imports
    results.append(("Main.py Imports", verify_imports_in_main()))

    # Summary
    print("=" * 60)
    print("SUMMARY:")
    print("=" * 60)

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")

    all_passed = all(r[1] for r in results)

    print()
    if all_passed:
        print("SUCCESS: All verification checks passed!")
        print()
        print("Next Steps:")
        print("  1. Start Docker (for database)")
        print("  2. Run: docker-compose up -d postgres redis")
        print("  3. Start API: python -m uvicorn src.main:app --reload --port 8000")
        print("  4. Visit docs: http://localhost:8000/docs")
        return 0
    else:
        print("FAILED: Some verification checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
