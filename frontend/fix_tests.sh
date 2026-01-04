#!/bin/bash

echo "Fixing test setup issues..."

# 1. Check setupTests has MockWebSocketService class
if ! grep -q "class MockWebSocketService" src/setupTests.ts; then
  echo "❌ Missing MockWebSocketService class"
  exit 1
fi

# 2. Check Plotly mock has correct testids
if ! grep -q "mock-plotly-chart" src/setupTests.ts; then
  echo "⚠️  Plotly mock missing 'mock-plotly-chart' testid"
fi

# 3. Find files with lib/utils import issues
echo "Checking for lib/utils import issues..."
grep -r "from ['\"]lib/utils" src --include="*.ts" --include="*.tsx" | wc -l

echo "Test setup check complete"
