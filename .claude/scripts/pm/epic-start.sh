#!/bin/bash

# Epic Start Script
# Starts parallel execution of an Epic's tasks

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

echo "🚀 Starting Epic: $EPIC_TITLE"
echo ""

# Count tasks
TASK_COUNT=$(ls -1 "$EPIC_DIR/$EPIC_NAME"/*.md 2>/dev/null | grep -v epic.md | wc -l)

if [ "$TASK_COUNT" -eq 0 ]; then
    echo "❌ No tasks found. Run: /pm:epic-decompose $EPIC_NAME"
    exit 1
fi

echo "Found $TASK_COUNT tasks:"
echo ""

# List all tasks
for TASK_FILE in "$EPIC_DIR/$EPIC_NAME"/*.md; do
    # Skip epic.md
    if [ "$(basename "$TASK_FILE")" == "epic.md" ]; then
        continue
    fi

    TASK_NAME=$(basename "$TASK_FILE" .md)
    TASK_STATUS=$(grep "^status: " "$TASK_FILE" | sed 's/status: //')

    printf "  %-15s %s\n" "$TASK_NAME" "($TASK_STATUS)"
done

echo ""
echo "Epic started! Tasks are ready for execution."
echo ""
echo "To work on a specific task:"
echo "  1. Navigate to epic directory: cd $EPIC_DIR/$EPIC_NAME"
echo "  2. Edit the task file to update status"
echo "  3. Commit your changes with clear messages"
echo ""
echo "Example:"
echo "  cd $EPIC_DIR/$EPIC_NAME"
echo "  # Edit 001.md"
echo "  git add 001.md"
echo "  git commit -m \"Issue #123: Implement authentication system\""