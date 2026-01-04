#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check pdt_protection setting and provide solution
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def find_futu_opend():
    """Find FutuOpenD installation path"""
    possible_paths = [
        r"C:\Users\Penguin8n\AppData\Local\FutuOpenD\FutuOpenD.exe",
        r"C:\Program Files\FutuOpenD\FutuOpenD.exe",
        r"C:\Users\Penguin8n\AppData\Roaming\FutuOpenD\FutuOpenD.exe",
        r"C:\Users\Penguin8n\FutuOpenD\FutuOpenD.exe"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def check_running_processes():
    """Check if FutuOpenD is running"""
    try:
        result = subprocess.run(['tasklist', '/fi', 'imagename eq FutuOpenD.exe'],
                               capture_output=True, text=True, encoding='utf-8')
        return 'FutuOpenD.exe' in result.stdout
    except:
        return False

def main():
    """Main function"""
    print("=== FutuOpenD Configuration Check ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Check if FutuOpenD is running
    is_running = check_running_processes()
    print(f"1. FutuOpenD Status: {'Running' if is_running else 'Not Running'}")

    # Find FutuOpenD path
    opend_path = find_futu_opend()
    if opend_path:
        print(f"2. FutuOpenD Path: {opend_path}")
    else:
        print("2. FutuOpenD Path: Not found in common locations")
        print("   Please check your installation directory")

    print("\n3. pdt_protection Configuration:")
    print("   Based on official documentation:")
    print("   - pdt_protection=0 may be required for API access")
    print("   - This controls data protection settings")

    if is_running and opend_path:
        print("\n4. Recommended Steps:")
        print("   STEP 1: Close FutuOpenD completely")
        print("   STEP 2: Restart with pdt_protection=0 parameter:")
        print(f"           \"{opend_path}\" --pdt_protection=0")
        print("   STEP 3: Relogin to your account")
        print("   STEP 4: Test API connection again")
    elif opend_path:
        print("\n4. Start FutuOpenD with recommended parameters:")
        print(f"   \"{opend_path}\" --pdt_protection=0")

    print("\n5. Alternative Methods:")
    print("   Method A: Modify configuration file")
    print("   - Find FutuOpenDConfig.xml")
    print("   - Set pdt_protection to 0")
    print("   - Restart client")
    print("")
    print("   Method B: Check NiuNiu App settings")
    print("   - Open 富途牛牛 App")
    print("   - Go to Settings > Developer Options")
    print("   - Disable data protection if available")

    print("\n6. Verification Commands:")
    print("   After making changes, test with:")
    print("   python final_account_check.py")
    print("   python test_all_account_types.py")

    # Save configuration info
    config_info = {
        'timestamp': datetime.now().isoformat(),
        'opend_running': is_running,
        'opend_path': opend_path,
        'pdt_protection_setting': 'Unknown (requires manual check)',
        'recommended_action': 'Set pdt_protection=0 if simulation access fails'
    }

    with open('futu_opend_config.json', 'w', encoding='utf-8') as f:
        json.dump(config_info, f, indent=2, ensure_ascii=False)

    print(f"\nConfiguration info saved to: futu_opend_config.json")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Configuration check failed: {e}")
        import traceback
        traceback.print_exc()