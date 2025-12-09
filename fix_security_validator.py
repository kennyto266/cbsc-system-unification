#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emergency Fix for Security Validator Syntax Errors
Run this script to fix the critical syntax issues in secure_api_validator.py
"""

import os
import re

def fix_security_validator():
    """Fix syntax errors in secure_api_validator.py"""

    file_path = "src/security/secure_api_validator.py"

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    print(f"🔧 Fixing syntax errors in {file_path}...")

    # Read the original file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply fixes
    fixes_applied = []

    # Fix 1: getLogger syntax
    if 'logging.getLogger__name__' in content:
        content = content.replace('logging.getLogger__name__', 'logging.getLogger(__name__)')
        fixes_applied.append("Fixed logging.getLogger syntax")

    # Fix 2: __init__ method syntax
    content = re.sub(r'def __init__self:', 'def __init__(self):', content)
    if 'def __init__(self):' in content and 'def __init__self:' not in content:
        fixes_applied.append("Fixed __init__ method syntax")

    # Fix 3: validate_input method syntax
    content = re.sub(r'def validate_inputself,', 'def validate_input(self,', content)
    if 'def validate_input(self,' in content:
        fixes_applied.append("Fixed validate_input method syntax")

    # Fix 4: Basic validation method syntax
    content = re.sub(r'def _basic_validationself,', 'def _basic_validation(self,', content)

    # Fix 5: Dangerous content method syntax
    content = re.sub(r'def _contains_dangerous_contentself,', 'def _contains_dangerous_content(self,', content)

    # Fix 6: Request data validation methods
    content = re.sub(r'def validate_request_dataself,', 'def validate_request_data(self,', content)
    content = re.sub(r'def validate_path_paramsself,', 'def validate_path_params(self,', content)
    content = re.sub(r'def validate_query_paramsself,', 'def validate_query_params(self,', content)

    # Fix 7: JSON body method syntax
    content = re.sub(r'def sanitize_json_bodyself,', 'def sanitize_json_body(self,', content)

    # Fix 8: JSON depth method syntax
    content = re.sub(r'def _get_json_depthself,', 'def _get_json_depth(self,', content)

    # Fix 9: Class method decorators and colons
    content = re.sub(r'@validator\'\*', pre=True', '@validator("*", pre=True)', content)

    # Fix 10: Method parameter syntax with colons
    content = re.sub(r'return validator.validate_inputv, field.name', 'return validator.validate_input(v, field.name)', content)

    # Fix 11: Try-except blocks and colons
    content = re.sub(r'try:\s*value = expected_type\(value\)\s*except ValueError, TypeError:',
                    'try:\n        value = expected_type(value)\n    except (ValueError, TypeError):', content)

    # Fix 12: isinstance method calls
    content = re.sub(r'isinstancevalue, str:', 'isinstance(value, str):', content)
    content = re.sub(r'lenvalue', 'len(value)', content)
    content = re.sub(r're.matchrules\[\'pattern\'\], value', 're.match(rules[\'pattern\'], value)', content)

    # Fix 13: HTML escaping
    content = re.sub(r'html\.escapevalue', 'html.escape(value)', content)

    # Fix 14: Method calls with proper spacing
    content = re.sub(r'validator\.validate_inputvalue, param_name', 'validator.validate_input(value, param_name)', content)
    content = re.sub(r'validator\.validate_request_datapath_params', 'validator.validate_request_data(path_params)', content)

    # Fix 15: JSON parsing
    content = re.sub(r'json\.loadsbody.decode\'utf-8\'', 'json.loads(body.decode(\'utf-8\'))', content)
    content = re.sub(r'lenbody', 'len(body)', content)

    # Fix 16: JSON depth calculation
    content = re.sub(r'max\(self\._get_json_depthv, current_depth \+ 1 for v in obj\.values\(\)\)',
                    'max(self._get_json_depth(v, current_depth + 1) for v in obj.values())', content)
    content = re.sub(r'max\(self\._get_json_depthitem, current_depth \+ 1 for item in obj\)',
                    'max(self._get_json_depth(item, current_depth + 1) for item in obj)', content)

    # Fix 17: Testing function syntax
    content = re.sub(r'print"Testing', 'print("Testing', content)
    content = re.sub(r'printf', 'print(f', content)
    content = re.sub(r'validator\.validate_inputvalue, param_name', 'validator.validate_input(value, param_name)', content)

    # Write the fixed content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Applied {len(fixes_applied)} syntax fixes:")
    for i, fix in enumerate(fixes_applied, 1):
        print(f"   {i}. {fix}")

    return True

def verify_fixes():
    """Verify that the fixes worked by trying to import the module"""
    print("\n🔍 Verifying fixes...")
    try:
        import sys
        sys.path.insert(0, '.')

        # Try to import the fixed module
        from src.security.secure_api_validator import SecureAPIValidator

        # Try to create an instance
        validator = SecureAPIValidator()

        print("✅ Security validator imports successfully!")
        print("✅ Instance creation works!")

        # Test a simple validation
        result = validator.validate_input("test", "agent_id")
        print(f"✅ Basic validation works: {result}")

        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚨 CBSC Security Validator Emergency Fix")
    print("=" * 50)

    # Apply fixes
    success = fix_security_validator()

    if success:
        # Verify fixes
        verify_fixes()

        print("\n" + "=" * 50)
        print("📋 NEXT STEPS:")
        print("1. Restart your FastAPI server")
        print("2. Test the /api/health endpoint")
        print("3. Monitor server logs for any remaining errors")
        print("4. Run: python fix_cors_middleware.py")
        print("=" * 50)
    else:
        print("\n❌ Fix application failed. Manual intervention required.")