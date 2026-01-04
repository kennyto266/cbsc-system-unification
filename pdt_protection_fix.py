#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdt_protection Fix Guide and Execution Tool
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def find_futu_executable():
    """Find FutuOpenD.exe in common locations"""
    search_paths = [
        r"C:\Program Files\FutuOpenD",
        r"C:\Program Files (x86)\FutuOpenD",
        r"C:\Users\Penguin8n\AppData\Local\FutuOpenD",
        r"C:\Users\Penguin8n\AppData\Roaming\FutuOpenD",
        r"C:\Users\Penguin8n\FutuOpenD",
        r"D:\FutuOpenD",
        r"D:\Program Files\FutuOpenD"
    ]

    executable_paths = []

    for base_path in search_paths:
        exe_path = os.path.join(base_path, "FutuOpenD.exe")
        if os.path.exists(exe_path):
            executable_paths.append(exe_path)

    return executable_paths

def check_current_processes():
    """Check current Futu processes"""
    try:
        result = subprocess.run(
            ['wmic', 'process', 'where', 'name like "%futu%"', 'get', 'Name,ExecutablePath', '/format:list'],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
        )
        return result.stdout
    except:
        return "Unable to check processes"

def main():
    """Main execution"""
    print("=== pdt_protection Fix Tool ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Step 1: Find FutuOpenD installations
    print("\n1. Scanning for FutuOpenD installations...")
    executables = find_futu_executable()

    if executables:
        print(f"   Found {len(executables)} installation(s):")
        for i, path in enumerate(executables, 1):
            print(f"   {i}. {path}")
    else:
        print("   No FutuOpenD.exe found in standard locations")
        print("   Please check your installation directory")

    # Step 2: Check current processes
    print("\n2. Checking current Futu processes...")
    processes = check_current_processes()
    if processes.strip():
        print("   Current Futu processes:")
        # Clean up and display process info
        lines = processes.split('\n')
        for line in lines:
            if line.strip() and '=' in line:
                print(f"   {line.strip()}")

    # Step 3: Provide fix instructions
    print("\n3. pdt_protection Fix Instructions:")
    print("   METHOD A - Command Line (Recommended):")
    if executables:
        for i, path in enumerate(executables, 1):
            print(f"   Option {i}:")
            print(f"   1. Close all FutuOpenD instances")
            print(f"   2. Run: \"{path}\" --pdt_protection=0")
            print(f"   3. Login to your account")
            print("")

    print("   METHOD B - Configuration File:")
    print("   1. Find FutuOpenDConfig.xml in installation directory")
    print("   2. Add or modify: <Setting name=\"pdt_protection\" value=\"0\" />")
    print("   3. Restart FutuOpenD")

    print("\n4. Verification Steps:")
    print("   After applying the fix:")
    print("   1. Wait 30 seconds for client to initialize")
    print("   2. Run: python final_account_check.py")
    print("   3. Look for '[SUCCESS] Simulation Account Available!' message")

    # Step 4: Create batch file for easy execution
    if executables:
        print("\n5. Creating batch file for easy execution...")
        batch_content = "@echo off\n"
        batch_content += "echo Starting FutuOpenD with pdt_protection=0...\n"
        batch_content += f"\"{executables[0]}\" --pdt_protection=0\n"
        batch_content += "echo FutuOpenD started. Please login to your account.\n"
        batch_content += "pause\n"

        with open("start_futu_opend.bat", "w", encoding="utf-8") as f:
            f.write(batch_content)

        print(f"   Created: start_futu_opend.bat")
        print(f"   You can double-click this file to start FutuOpenD with the fix")

    # Save configuration info
    config_info = {
        'timestamp': datetime.now().isoformat(),
        'found_executables': executables,
        'pdt_protection_setting': 'Needs to be set to 0',
        'recommended_command': f"\"{executables[0] if executables else 'FutuOpenD.exe'}\" --pdt_protection=0",
        'verification_script': 'python final_account_check.py'
    }

    with open('pdt_protection_config.json', 'w', encoding='utf-8') as f:
        json.dump(config_info, f, indent=2, ensure_ascii=False)

    print(f"\n6. Configuration saved to: pdt_protection_config.json")

    print("\n=== IMPORTANT REMINDERS ===")
    print("• CLOSE all FutuOpenD instances before applying the fix")
    print("• The fix only affects development API access")
    print("• Keep normal security practices in production")
    print("• Test immediately after applying the fix")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Tool execution failed: {e}")
        import traceback
        traceback.print_exc()