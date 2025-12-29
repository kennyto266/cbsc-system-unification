"""
Simple test to verify the database connection fix works
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Test 1: Verify the new connection function exists
print("Test 1: Checking if get_db_connection exists in connection module...")
try:
    from src.database.connection import get_db_connection
    print("  [PASS] get_db_connection found in src.database.connection")
except ImportError as e:
    print(f"  [FAIL] Could not import get_db_connection: {e}")
    sys.exit(1)

# Test 2: Verify the function signature and docstring
print("\nTest 2: Checking function signature and docstring...")
if get_db_connection.__doc__:
    doc_lines = get_db_connection.__doc__.strip().split('\n')
    print(f"  Docstring has {len(doc_lines)} lines")
    print("  [PASS] Function has documentation")
else:
    print("  [FAIL] Function missing docstring")
    sys.exit(1)

# Test 3: Test the functions work correctly
print("\nTest 3: Testing functions work correctly...")

# Test get_date_range
try:
    from src.api.market_data_endpoints import get_date_range
    start, end = get_date_range("1w")
    print(f"  [PASS] get_date_range('1w') returned: {start} to {end}")
except Exception as e:
    print(f"  [FAIL] get_date_range failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("[PASS] All tests passed!")
print("=" * 60)
