#!/bin/bash

# PRD Creation Script
# Creates a new Product Requirements Document

set -e

# Configuration
PRD_DIR=".claude/prds"
EPIC_DIR=".claude/epics"

# Ensure directories exist
mkdir -p "$PRD_DIR"

# Function to get current datetime
get_datetime() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Get PRD name from argument
PRD_NAME="$1"
if [ -z "$PRD_NAME" ]; then
    echo "❌ Error: PRD name required"
    echo "Usage: $0 <prd-name>"
    exit 1
fi

# Convert to kebab-case for filename
PRD_FILE=$(echo "$PRD_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')

# Check if PRD already exists
if [ -f "$PRD_DIR/$PRD_FILE.md" ]; then
    echo "❌ Error: PRD already exists: $PRD_DIR/$PRD_FILE.md"
    exit 1
fi

# Get current datetime
CREATED=$(get_datetime)

# Create PRD file
cat > "$PRD_DIR/$PRD_FILE.md" << EOF
---
name: $PRD_NAME
description:
status: backlog
created: $CREATED
updated: $CREATED
github:
---

# $PRD_NAME

## 概述

## 目標用戶

## 問題陳述

## 解決方案

## 功能需求

### 核心功能

### 高級功能

## 非功能需求

### 性能要求

### 安全要求

### 可用性要求

## 技術要求

## 驗收標準

## 風險評估

## 時間規劃

## 相關文檔

EOF

echo "✅ PRD created: $PRD_DIR/$PRD_FILE.md"
echo "Next: Edit the PRD file, then run: /pm:prd-parse $PRD_FILE"