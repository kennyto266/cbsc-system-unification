#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORS and Middleware Configuration Fix
Resolves middleware stack issues causing 500 errors
"""

import os
import re

def fix_cors_in_file(file_path):
    """Fix CORS configuration in a specific file"""

    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Fix CORS configuration
    cors_pattern = r'app\.add_middleware\(\s*CORSMiddleware,\s*allow_origins=\["\*"\],'
    if re.search(cors_pattern, content, re.MULTILINE | re.DOTALL):
        replacement = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "http://localhost:8001", "http://127.0.0.1:3000", "http://127.0.0.1:8000"],'''
        content = re.sub(cors_pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

    # Add error handling middleware if missing
    error_middleware_code = '''# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": "server_error"}
        )

'''
    if 'error_handling_middleware' not in content and '@app.middleware("http")' not in content:
        # Insert before the first route
        first_route_pattern = r'(@app\.(get|post|put|delete|websocket))'
        if re.search(first_route_pattern, content):
            content = re.sub(first_route_pattern, error_middleware_code + r'\n\1', content)

    # Add proper imports if missing
    if 'from fastapi.responses import JSONResponse' not in content and 'JSONResponse' in content:
        imports_pattern = r'(from fastapi import [^\n]+)'
        if re.search(imports_pattern, content):
            content = re.sub(
                imports_pattern,
                r'\1\nfrom fastapi.responses import JSONResponse',
                content
            )

    changes_made = content != original_content

    if changes_made:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return changes_made, "CORS and middleware configuration updated"

def main():
    """Fix CORS issues in all FastAPI files"""

    print("🔧 Fixing CORS and middleware configuration issues...")

    files_to_fix = [
        "production_demo_working.py",
        "simple_fastapi_demo.py",
        "final_working_demo.py",
        "production_demo_final.py",
        "simple_production_working.py"
    ]

    fixes_applied = []

    for file_name in files_to_fix:
        if os.path.exists(file_name):
            fixed, message = fix_cors_in_file(file_name)
            if fixed:
                fixes_applied.append(f"{file_name}: {message}")
                print(f"✅ Fixed {file_name}")
            else:
                print(f"⚠️  No fixes needed for {file_name}")
        else:
            print(f"⚠️  File not found: {file_name}")

    print(f"\n📊 Applied {len(fixes_applied)} fixes:")
    for i, fix in enumerate(fixes_applied, 1):
        print(f"   {i}. {fix}")

    return len(fixes_applied) > 0

if __name__ == "__main__":
    print("🚨 CBSC CORS/Middleware Fix")
    print("=" * 50)

    success = main()

    print("\n" + "=" * 50)
    if success:
        print("✅ CORS and middleware fixes applied successfully!")
        print("\n📋 NEXT STEPS:")
        print("1. Install missing dependencies: pip install bleach redis psutil")
        print("2. Run: python check_dependencies.py")
        print("3. Restart your FastAPI servers")
        print("4. Test endpoints in order: /api/health → / → /api/parameters/current")
    else:
        print("⚠️  No CORS issues found, checking other potential causes...")
    print("=" * 50)