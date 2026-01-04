#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search All User IDs - 全面搜索所有可能的用戶ID
"""

import os
import sys
import re
import json

def search_user_ids():
    print("=== Search All User IDs ===")
    print("=" * 60)
    
    found_ids = []
    
    # 1. Search in FutuOpenD config files
    print("\n1. Searching FutuOpenD configuration files...")
    
    config_files = [
        r"C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\vuex.json",
        r"C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\vuex.json.bak",
        r"C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\vuex.json.tmp"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   Checking: {config_file}")
            try:
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Search for user IDs
                uid_matches = re.findall(r'"uid":\s*"(\d+)"', content)
                user_id_matches = re.findall(r'"userID":\s*(\d+)', content)
                login_matches = re.findall(r'"loginAccount":\s*"([^"]+)"', content)
                account_matches = re.findall(r'"acc_id":\s*(\d+)', content)
                
                if uid_matches:
                    print(f"   Found UIDs: {uid_matches}")
                    found_ids.extend(uid_matches)
                if user_id_matches:
                    print(f"   Found User IDs: {user_id_matches}")
                    found_ids.extend(user_id_matches)
                if login_matches:
                    print(f"   Found Login Accounts: {login_matches}")
                if account_matches:
                    print(f"   Found Account IDs: {account_matches}")
                    
            except Exception as e:
                print(f"   Error reading {config_file}: {e}")
    
    # 2. Search in log files
    print("\n2. Searching log files...")
    log_dir = r"C:\Users\Penguin8n\AppData\Roaming\com.futunn.FutuOpenD\Log"
    
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            if filename.endswith('.log') and '2860386' not in filename:
                file_path = os.path.join(log_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Search for different user ID patterns
                    patterns = [
                        r'UserID[:\s*:\s*(\d+)',
                        r'user_id[:\s*:\s*(\d+)', 
                        r'User-ID[:\s*:\s*(\d+)',
                        r'uid[:\s*:\s*(\d+)',
                        r'account[:\s*:\s*(\d+)',
                        r'acc_id[:\s*:\s*(\d+)',
                        r'286\d{4}',  # Search for similar IDs
                        r'\d{7,8}'  # Search for any 7-8 digit numbers
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            print(f"   In {filename}: Found {len(matches)} IDs: {matches[:5]}")
                            found_ids.extend(matches)
                    
                except Exception as e:
                    print(f"   Error reading {filename}: {e}")
    
    # 3. Search in cache directories
    print("\n3. Searching cache directories...")
    cache_dirs = [
        r"C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\Cache",
        r"C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\GPUCache",
        r"C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\blob_storage"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            for filename in os.listdir(cache_dir):
                if filename.endswith('.json') or filename.endswith('.dat'):
                    file_path = os.path.join(cache_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Search for user patterns
                        user_patterns = [
                            r'"uid":\s*"(\d+)"',
                            r'"user":\s*"(\d+)"',
                            r'"account":\s*"(\d+)"',
                            r'\d{7,8}'
                        ]
                        
                        for pattern in user_patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                print(f"   In cache file {filename}: Found IDs: {matches}")
                                found_ids.extend(matches)
                                
                    except Exception as e:
                        continue  # Skip files that can't be read
    
    # 4. Search environment variables
    print("\n4. Checking environment variables...")
    env_vars = [
        'FUTU_USER_ID',
        'FUTU_USER',
        'FUTU_ACCOUNT',
        'USER_ID',
        'ACCOUNT_ID'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value and value.isdigit():
            print(f"   Environment Variable {var}: {value}")
            found_ids.append(value)
    
    # 5. Summary of findings
    print("\n" + "=" * 60)
    print("SEARCH RESULTS SUMMARY:")
    print("=" * 60)
    
    # Remove duplicates and sort
    unique_ids = list(set(found_ids))
    unique_ids = [id for id in unique_ids if id.isdigit() and len(id) >= 6]
    unique_ids.sort()
    
    if unique_ids:
        print(f"Found {len(unique_ids)} unique user IDs:")
        for i, user_id in enumerate(unique_ids, 1):
            print(f"   {i}. User ID: {user_id}")
            
        # Check if any are different from 2860386
        other_ids = [id for id in unique_ids if id != "2860386"]
        if other_ids:
            print(f"\nOther IDs (not 2860386): {other_ids}")
            print("These might be additional accounts or test accounts")
        else:
            print(f"\nOnly found ID 2860386")
    else:
        print("No additional user IDs found")
    
    # Check if any match common patterns
    print(f"\nPattern Analysis:")
    id_patterns = {
        "Starts with 286": [id for id in unique_ids if id.startswith('286')],
        "7 digits": [id for id in unique_ids if len(id) == 7],
        "8 digits": [id for id in unique_ids if len(id) == 8],
        "Starts with 1": [id for id in unique_ids if id.startswith('1')],
        "Starts with 2": [id for id in unique_ids if id.startswith('2')],
    }
    
    for pattern, ids in id_patterns.items():
        if ids:
            print(f"   {pattern}: {ids}")

if __name__ == "__main__":
    search_user_ids()