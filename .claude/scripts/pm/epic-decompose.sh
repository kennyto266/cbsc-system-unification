#!/bin/bash

# Epic Decompose Script
# Breaks down an Epic into tasks

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

# Check if epic.md exists
if [ ! -f "$EPIC_DIR/$EPIC_NAME/epic.md" ]; then
    echo "❌ Error: Epic file not found: $EPIC_DIR/$EPIC_NAME/epic.md"
    exit 1
fi

# Extract epic name from file
EPIC_TITLE=$(grep "^name: " "$EPIC_DIR/$EPIC_NAME/epic.md" | sed 's/name: //')
if [ -z "$EPIC_TITLE" ]; then
    echo "❌ Error: Epic must have a name field"
    exit 1
fi

echo "Decomposing epic: $EPIC_TITLE"

# Create a simple task decomposition based on common patterns
# In a real implementation, this would analyze the epic content more carefully

# Get current datetime
CREATED=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Task counter
TASK_NUM=1

# Function to create a task
create_task() {
    local TASK_NAME="$1"
    local TASK_DESC="$2"
    local TASK_FILE=$(printf "%03d" $TASK_NUM).md

    cat > "$EPIC_DIR/$EPIC_NAME/$TASK_FILE" << EOF
---
name: $TASK_NAME
status: backlog
created: $CREATED
updated: $CREATED
github:
depends_on: []
parallel: true
conflicts_with: []
---

# Task: $TASK_NAME

## Description
$TASK_DESC

## Acceptance Criteria
- [ ]

## Technical Details

## Dependencies

## Effort Estimate
- Size:
- Hours:
- Parallel:

## Definition of Done
- [ ]
EOF

    echo "Created task: $TASK_FILE - $TASK_NAME"
    TASK_NUM=$((TASK_NUM + 1))
}

# Read epic content and create tasks
# This is a simplified version - in practice, you'd want more sophisticated parsing

# Look for specific patterns in the epic.md
if grep -q "Phase 1" "$EPIC_DIR/$EPIC_NAME/epic.md"; then
    # Phase-based epic
    create_task "Phase 1: Infrastructure Setup" "Set up basic infrastructure and foundation"
    create_task "Phase 2: Core Implementation" "Implement core functionality"
    create_task "Phase 3: Integration & Testing" "Integrate components and test"
    create_task "Phase 4: Deployment & Documentation" "Deploy and document"
else
    # Generic tasks
    create_task "Analysis & Planning" "Analyze requirements and create detailed plan"
    create_task "Core Implementation" "Implement the main functionality"
    create_task "Testing & QA" "Test the implementation"
    create_task "Documentation & Deployment" "Document and deploy"
fi

echo ""
echo "✅ Epic decomposed into $((TASK_NUM - 1)) tasks"
echo "Directory: $EPIC_DIR/$EPIC_NAME"
echo ""
echo "Next: Run: /pm:epic-sync $EPIC_NAME"