#!/bin/bash

# PRD Parse Script
# Converts a PRD into an Epic

set -e

# Configuration
PRD_DIR=".claude/prds"
EPIC_DIR=".claude/epics"

# Get PRD file from argument
PRD_FILE="$1"
if [ -z "$PRD_FILE" ]; then
    echo "❌ Error: PRD file required"
    echo "Usage: $0 <prd-file>"
    exit 1
fi

# Ensure .md extension
if [[ ! "$PRD_FILE" == *.md ]]; then
    PRD_FILE="$PRD_FILE.md"
fi

# Full path to PRD
PRD_PATH="$PRD_DIR/$PRD_FILE"

# Check if PRD exists
if [ ! -f "$PRD_PATH" ]; then
    echo "❌ Error: PRD not found: $PRD_PATH"
    exit 1
fi

# Extract PRD name from file
PRD_NAME=$(grep "^name: " "$PRD_PATH" | sed 's/name: //')
if [ -z "$PRD_NAME" ]; then
    echo "❌ Error: PRD must have a name field"
    exit 1
fi

# Convert to kebab-case for epic directory
EPIC_DIR_NAME=$(echo "$PRD_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')

# Check if epic already exists
if [ -d "$EPIC_DIR/$EPIC_DIR_NAME" ]; then
    echo "❌ Error: Epic already exists: $EPIC_DIR/$EPIC_DIR_NAME"
    exit 1
fi

# Create epic directory
mkdir -p "$EPIC_DIR/$EPIC_DIR_NAME"

# Get current datetime
CREATED=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Extract PRD content
DESCRIPTION=$(grep -A 5 "^## 概述" "$PRD_PATH" | grep -v "^## 概述" | grep -v "^--" | sed '/^$/d' | head -n 3)

# Create epic file
cat > "$EPIC_DIR/$EPIC_DIR_NAME/epic.md" << EOF
---
name: $PRD_NAME Implementation
description: $DESCRIPTION
status: backlog
created: $CREATED
updated: $CREATED
github:
---

# $PRD_NAME Implementation

## 概述

基於PRD文檔 [$PRD_FILE]($PRD_PATH)，實施完整的解決方案。

## 背景

## 目標

## 交付物

## 技術要求

## 風險控制

## 資源需求

## 驗收標準

## 相關文檔
- [PRD]($PRD_PATH)

## GitHub集成

EOF

echo "✅ Epic created: $EPIC_DIR/$EPIC_DIR_NAME/epic.md"
echo "Next: Run: /pm:epic-decompose $EPIC_DIR_NAME"