#!/bin/bash

# Simple Epic Sync Script
# Creates GitHub issues for an Epic and its tasks

set -e

# Configuration
EPIC_DIR=".claude/epics"

# Get epic name from argument
EPIC_NAME="$1"
if [ -z "$EPIC_NAME" ]; then
    echo "❌ Error: Epic name required"
    echo "Usage: $0 <epic-name>"
    exit 1
fi

# Check if epic exists
if [ ! -d "$EPIC_DIR/$EPIC_NAME" ]; then
    echo "❌ Error: Epic not found: $EPIC_DIR/$EPIC_NAME"
    exit 1
fi

# Extract epic information
EPIC_TITLE=$(grep "^name: " "$EPIC_DIR/$EPIC_NAME/epic.md" | sed 's/name: //')
EPIC_DESC=$(grep "^description: " "$EPIC_DIR/$EPIC_NAME/epic.md" | sed 's/description: //')
if [ -z "$EPIC_DESC" ]; then
    EPIC_DESC="Implementation of $EPIC_TITLE"
fi

echo "📋 Epic: $EPIC_TITLE"
echo ""
echo "Tasks to be created:"
for TASK_FILE in "$EPIC_DIR/$EPIC_NAME"/*.md; do
    if [ "$(basename "$TASK_FILE")" == "epic.md" ]; then
        continue
    fi
    TASK_NAME=$(grep "^name: " "$TASK_FILE" | sed 's/name: //')
    echo "  - $TASK_NAME"
done

echo ""
echo "To sync to GitHub:"
echo "1. Run: cd $EPIC_DIR/$EPIC_NAME"
echo "2. Create epic issue manually with title: '📋 Epic: $EPIC_TITLE'"
echo "3. Create task issues for each file with titles starting with '📝'"
echo "4. Update task dependencies as needed"
echo ""
echo "Next: Run: /pm:epic-start $EPIC_NAME"