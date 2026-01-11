#!/bin/bash

# Epic Sync Script
# Syncs an Epic to GitHub

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

# Get GitHub repo information
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
    echo "❌ Error: No git remote origin found"
    exit 1
fi

# Check if it's the template repository (SECURITY CHECK)
if [[ "$REMOTE_URL" == *"automazeio/ccpm"* ]] || [[ "$REMOTE_URL" == *"automazeio/ccpm.git"* ]]; then
    echo "❌ ERROR: You're trying to sync with the CCPM template repository!"
    echo ""
    echo "This repository (automazeio/ccpm) is a template for others to use."
    echo "You should NOT create issues or PRs here."
    echo ""
    echo "To fix this:"
    echo "1. Fork this repository to your own GitHub account"
    echo "2. Update your remote origin:"
    echo "   git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    exit 1
fi

REPO=$(echo "$REMOTE_URL" | sed 's|.*github.com[:/]||' | sed 's|\.git$||')
if [ -z "$REPO" ]; then
    REPO="user/repo"
fi

# Extract epic information
EPIC_TITLE=$(grep "^name: " "$EPIC_DIR/$EPIC_NAME/epic.md" | sed 's/name: //')
EPIC_DESC=$(grep "^description: " "$EPIC_DIR/$EPIC_NAME/epic.md" | sed 's/description: //')
if [ -z "$EPIC_DESC" ]; then
    EPIC_DESC="Implementation of $EPIC_TITLE"
fi

echo "Syncing epic to GitHub repository: $REPO"
echo "Epic: $EPIC_TITLE"

# Strip frontmatter from epic.md for GitHub issue body
TEMP_BODY=$(mktemp)
sed '1,/^---$/d; 1,/^---$/d' "$EPIC_DIR/$EPIC_NAME/epic.md" > "$TEMP_BODY"

# Add epic information header
cat > "$TEMP_BODY.header" << EOF
# 📋 Epic: $EPIC_TITLE

**Location**: \`.claude/epics/$EPIC_NAME/\`

---

EOF

# Combine header and body
cat "$TEMP_BODY.header" "$TEMP_BODY" > "$TEMP_BODY.combined"

# Create GitHub issue for the epic
echo "Creating epic issue..."
gh issue create \
    --repo "$REPO" \
    --title "📋 Epic: $EPIC_TITLE" \
    --body-file "$TEMP_BODY.combined" \
    --label "epic"

echo "Epic issue created. Please provide the issue number:"
read -p "Issue URL: " EPIC_ISSUE_URL
EPIC_ISSUE_NUM=$(echo "$EPIC_ISSUE_URL" | grep -o '[0-9]\+$')

echo "✅ Epic issue created: #$EPIC_ISSUE_NUM"

# Create issues for each task
for TASK_FILE in "$EPIC_DIR/$EPIC_NAME"/*.md; do
    # Skip epic.md
    if [ "$(basename "$TASK_FILE")" == "epic.md" ]; then
        continue
    fi

    # Extract task information
    TASK_NAME=$(grep "^name: " "$TASK_FILE" | sed 's/name: //')
    TASK_DESC=$(grep "^## Description" "$TASK_FILE" -A 2 | grep -v "^## Description" | sed '/^$/d')

    # Strip frontmatter from task file
    TEMP_TASK_BODY=$(mktemp)
    sed '1,/^---$/d; 1,/^---$/d' "$TASK_FILE" > "$TEMP_TASK_BODY"

    # Add task information header
    cat > "$TEMP_TASK_BODY.header" << EOF
# 📝 Task: $TASK_NAME

**Epic**: $EPIC_TITLE (#$EPIC_ISSUE_NUM)
**Location**: \`.claude/epics/$EPIC_NAME/$(basename "$TASK_FILE")\`

---

EOF

    # Combine header and body
    cat "$TEMP_TASK_BODY.header" "$TEMP_TASK_BODY" > "$TEMP_TASK_BODY.combined"

    # Create GitHub issue for the task
    echo "Creating task issue: $TASK_NAME"
    gh issue create \
        --repo "$REPO" \
        --title "📝 $TASK_NAME" \
        --body-file "$TEMP_TASK_BODY.combined" \
        --label "task" \
        --label "epic-$EPIC_ISSUE_NUM"

    # Clean up temp files
    rm -f "$TEMP_TASK_BODY" "$TEMP_TASK_BODY.header" "$TEMP_TASK_BODY.combined"
done

# Update epic.md with GitHub issue reference
sed -i.bak "s/^github:$/github: https:\/\/github.com\/$REPO\/issues\/$EPIC_ISSUE_NUM/" "$EPIC_DIR/$EPIC_NAME/epic.md"
rm -f "$EPIC_DIR/$EPIC_NAME/epic.md.bak"

# Clean up temp files
rm -f "$TEMP_BODY" "$TEMP_BODY.header" "$TEMP_BODY.combined"

echo ""
echo "✅ Epic synchronized to GitHub"
echo "Epic issue: #$EPIC_ISSUE_NUM"
echo "Tasks created: $(ls -1 "$EPIC_DIR/$EPIC_NAME"/*.md | grep -v epic.md | wc -l)"
echo ""
echo "Next: Run: /pm:epic-start $EPIC_NAME"