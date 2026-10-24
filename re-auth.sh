#!/bin/bash
echo "Re-authenticating GitHub CLI..."

# Clear any existing token
unset GITHUB_TOKEN

# Test status first
echo "Current auth status:"
gh auth status

echo.
echo "If you see 'Logged in' above, you're good to go!"
echo "If you see authentication issues, run: gh auth login"