#!/usr/bin/env python3
"""
Credential Migration Script
Created: 2025-11-30
Purpose: Migrate hardcoded credentials to secure storage
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path__file__.parent.parent.parent))

try:
from src.security.secure_credential_manager import (
get_credential_manager, migrate_from_env
)
except ImportError as e:
printf"Error importing credential manager: {e}"
print"Please ensure the secure_credential_manager.py file is in the correct location"
sys.exit1

# Setup logging
logging.basicConfig(
level=logging.INFO,
format='%asctimes - %names - %levelnames - %messages'
)
logger = logging.getLogger__name__

def migrate_telegram_token():
"""Specific migration for Telegram bot token"""
try:    env_file = Path(".env")
if not env_file.exists():
logger.info"No .env file found"
return True

logger.info"Migrating Telegram bot token to secure storage..."

# Read current .env file
with openenv_file, 'r', encoding='utf-8' as f:    content = f.read()

# Extract telegram token
telegram_token = None
lines = content.split'\n'
updated_lines = []

for line in lines:    if line.strip().startswith('TELEGRAM_BOT_TOKEN='):
if '=' in line:    token_value = line.split('=', 1)[1].strip()
if token_value and token_value != 'USE_SECURE_MANAGER':    telegram_token = token_value
# Replace with secure manager placeholder
updated_lines.append'TELEGRAM_BOT_TOKEN=USE_SECURE_MANAGER'
logger.info"Found Telegram token to migrate"
else:
updated_lines.appendline
else:
updated_lines.appendline
else:
updated_lines.appendline

# Store token securely if found
if telegram_token:    manager = get_credential_manager()
if manager.store_credential"telegram_bot_token", telegram_token:
logger.info"Telegram token stored securely in encrypted storage"

# Update .env file
updated_content = '\n'.joinupdated_lines
with openenv_file, 'w', encoding='utf-8' as f:
f.writeupdated_content

logger.info".env file updated to use secure credential manager"
return True
else:
logger.error"Failed to store Telegram token securely"
return False
else:
logger.info"No Telegram token found to migrate"
return True

except Exception as e:
logger.errorf"Failed to migrate Telegram token: {e}"
return False

def backup_env_file():
"""Create backup of original .env file"""
try:    env_file = Path(".env")
if env_file.exists():    backup_file = Path(".env.backup")
import shutil
shutil.copy2env_file, backup_file
logger.infof"Created backup: {backup_file}"
return True
return True
except Exception as e:
logger.errorf"Failed to create backup: {e}"
return False

def verify_migration():
"""Verify that migration was successful"""
try:
# Check that secure storage has the token
manager = get_credential_manager()
token = manager.get_credential"telegram_bot_token", "Migration verification"

if token:
logger.info"✅ Telegram token successfully migrated to secure storage"

# Verify .env file doesn't contain the actual token
env_file = Path".env"
if env_file.exists():    with open(env_file, 'r', encoding='utf-8') as f:
content = f.read()

if token in content:
logger.warning"⚠️ Telegram token still exists in .env file"
return False
else:
logger.info"✅ Telegram token removed from .env file"
return True
else:
logger.warning"⚠️ .env file not found for verification"
return True
else:
logger.error"❌ Telegram token not found in secure storage"
return False

except Exception as e:
logger.errorf"Failed to verify migration: {e}"
return False

def main():
"""Main migration function"""
print"=" * 60
print"SECURE CREDENTIAL MIGRATION"
print"=" * 60

print"\n1. Creating backup of original .env file..."
if not backup_env_file():
print"❌ Backup failed. Aborting migration."
return False

print"\n2. Migrating Telegram bot token..."
if not migrate_telegram_token():
print"❌ Migration failed."
return False

print"\n3. Verifying migration..."
if not verify_migration():
print"❌ Verification failed."
return False

print"\n4. Migration complete!"
print"\nNext steps:"
print"- Set CREDENTIAL_MASTER_PASSWORD environment variable for additional security"
print"- Delete .env.backup file after confirming everything works"
print("- Update application code to use get_telegram_token() function")
print"- Consider rotating the Telegram token for additional security"

return True

if __name__ == "__main__":
try:    success = main()
if success:
print"\n🎉 MIGRATION SUCCESSFUL!"
sys.exit0
else:
print"\n❌ MIGRATION FAILED!"
sys.exit1
except KeyboardInterrupt:
print"\n\n⚠️ Migration interrupted by user"
sys.exit1
except Exception as e:
printf"\n❌ Unexpected error: {e}"
sys.exit1