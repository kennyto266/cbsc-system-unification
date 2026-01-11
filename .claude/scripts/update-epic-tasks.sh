#!/bin/bash

# Update epic task statuses to completed
echo "Updating epic task statuses..."

# Get current date
CURRENT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# List of completed tasks with their full paths
declare -A epic_tasks=(
    [".claude/epics/square-ui-integration/001-initialization.md"]="completed"
    [".claude/epics/square-ui-integration/002-square-ui-integration.md"]="completed"
    [".claude/epics/square-ui-integration/003-shadcn-integration.md"]="completed"
    [".claude/epics/square-ui-integration/004-nextjs-architecture.md"]="completed"
    [".claude/epics/square-ui-integration/005-state-management.md"]="completed"
    [".claude/epics/square-ui-integration/006-api-integration.md"]="completed"
    [".claude/epics/square-ui-integration/007-strategy-ui.md"]="completed"
    [".claude/epics/square-ui-integration/008-data-visualization.md"]="completed"
    [".claude/epics/dashboard-system/63.md"]="completed"
    [".claude/epics/dashboard-system/64.md"]="completed"
    [".claude/epics/dashboard-system/65.md"]="completed"
)

# Function to update task status
update_task_status() {
    local file_path=$1
    local status=$2

    if [ -f "$file_path" ]; then
        # Create backup
        cp "$file_path" "$file_path.bak"

        # Update status
        sed -i "s/^status: .*/status: $status/" "$file_path"

        # Update timestamp if updated field exists
        if grep -q "^updated:" "$file_path"; then
            sed -i "s/^updated: .*/updated: $CURRENT_DATE/" "$file_path"
        fi

        # Add completion note if not present
        if ! grep -q "## Completion" "$file_path"; then
            echo "" >> "$file_path"
            echo "---" >> "$file_path"
            echo "## Completion" >> "$file_path"
            echo "This task has been completed on $CURRENT_DATE" >> "$file_path"
        fi

        # Remove backup
        rm -f "$file_path.bak"

        echo "✅ Updated: $(basename $file_path)"
    else
        echo "❌ File not found: $file_path"
    fi
}

# Update each task
for task_file in "${!epic_tasks[@]}"; do
    status=${epic_tasks[$task_file]}
    update_task_status "$task_file" "$status"
done

echo ""
echo "✅ Epic task status update completed!"
echo ""
echo "Updated ${#epic_tasks[@]} tasks to 'completed' status"
echo ""
echo "Run '/pm:next' again to see the updated task list."