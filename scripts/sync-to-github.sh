#!/bin/bash

# GitHub Epic Sync Script for System Unification
# 使用说明: ./scripts/sync-to-github.sh <your-username> <your-repo-name>

set -e

# 参数检查
if [ $# -lt 2 ]; then
    echo "用法: $0 <github-username> <repository-name>"
    echo "示例: $0 myusername cbsc-system-unification"
    exit 1
fi

GITHUB_USER="$1"
REPO_NAME="$2"
FULL_REPO="${GITHUB_USER}/${REPO_NAME}"

echo "🚀 开始同步到GitHub仓库: ${FULL_REPO}"
echo ""

# 检查gh CLI是否安装
if ! command -v gh &> /dev/null; then
    echo "❌ 错误: GitHub CLI (gh) 未安装"
    echo "请安装GitHub CLI: https://cli.github.com/manual/installation"
    exit 1
fi

# 检查是否已登录GitHub
if ! gh auth status &> /dev/null; then
    echo "❌ 错误: 未登录GitHub CLI"
    echo "请先运行: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI已就绪"
echo ""

# 步骤1: 创建GitHub仓库
echo "📝 步骤1: 创建GitHub仓库..."
if gh repo view "${FULL_REPO}" &> /dev/null; then
    echo "   仓库 ${FULL_REPO} 已存在"
    REMOTE_URL=$(gh repo view "${FULL_REPO}" --json url -q .url)
    git remote add origin "${REMOTE_URL}" 2>/dev/null || true
else
    echo "   创建新仓库 ${FULL_REPO}..."
    gh repo create "${FULL_REPO}" --public --description="CBSC量化交易系统统一项目 - 基于CCPM的专业项目管理系统" || {
        echo "   创建私有仓库..."
        gh repo create "${FULL_REPO}" --private --description="CBSC量化交易系统统一项目 - 基于CCPM的专业项目管理系统"
    }
    REMOTE_URL="https://github.com/${FULL_REPO}.git"
    git remote add origin "${REMOTE_URL}"
fi
echo "   ✅ 仓库就绪: ${REMOTE_URL}"
echo ""

# 步骤2: 提取Epic内容
echo "📊 步骤2: 准备Epic内容..."
EPIC_FILE=".claude/epics/system-unification/epic.md"

if [ ! -f "$EPIC_FILE" ]; then
    echo "❌ 错误: Epic文件不存在: ${EPIC_FILE}"
    exit 1
fi

# 移除frontmatter并准备GitHub issue body
sed '1,/^---$/d; 1,/^---$/d' "$EPIC_FILE" > /tmp/epic-body.md

# 确定epic类型
if grep -qi "bug\|fix\|issue\|problem\|error" /tmp/epic-body.md; then
    EPIC_TYPE="bug"
else
    EPIC_TYPE="feature"
fi

echo "   ✅ Epic内容已准备"
echo ""

# 步骤3: 创建Epic Issue
echo "🎯 步骤3: 创建Epic Issue..."
EPIC_NUMBER=$(gh issue create \
    --repo "${FULL_REPO}" \
    --title "Epic: System Unification" \
    --body-file /tmp/epic-body.md \
    --label "epic,epic:system-unification,${EPIC_TYPE}" \
    --json number -q .number)

if [ -z "$EPIC_NUMBER" ]; then
    echo "❌ 错误: 无法创建Epic Issue"
    exit 1
fi

echo "   ✅ Epic Issue创建成功: #${EPIC_NUMBER}"
echo ""

# 步骤4: 创建任务Issues
echo "📋 步骤4: 创建任务Issues..."

# 检查是否有gh-sub-issue扩展
USE_SUBISSUES=false
if gh extension list | grep -q "yahsan2/gh-sub-issue"; then
    echo "   发现gh-sub-issue扩展，将创建子issues..."
    USE_SUBISSUES=true
else
    echo "   ⚠️  gh-sub-issue扩展未安装，将创建独立issues"
fi

# 创建任务映射文件
> /tmp/task-mapping.txt

# 为每个任务创建Issue
for task_file in .claude/epics/system-unification/[0-9][0-9][0-9].md; do
    [ -f "$task_file" ] || continue

    # 提取任务名称
    task_name=$(grep '^name:' "$task_file" | sed 's/^name: *//')

    # 移除frontmatter
    sed '1,/^---$/d; 1,/^---$/d' "$task_file" > /tmp/task-body.md

    # 创建Issue
    if [ "$USE_SUBISSUES" = true ]; then
        task_number=$(gh sub-issue create \
            --parent "$EPIC_NUMBER" \
            --title "$task_name" \
            --body-file /tmp/task-body.md \
            --label "task,epic:system-unification" \
            --json number -q .number)
    else
        task_number=$(gh issue create \
            --repo "${FULL_REPO}" \
            --title "$task_name" \
            --body-file /tmp/task-body.md \
            --label "task,epic:system-unification" \
            --json number -q .number)
    fi

    if [ -n "$task_number" ]; then
        echo "   ✅ 任务创建成功: #${task_number} - ${task_name}"
        echo "${task_file}:${task_number}" >> /tmp/task-mapping.txt
    else
        echo "   ❌ 任务创建失败: ${task_name}"
    fi
done

echo ""
echo "📊 任务创建完成统计:"
TASK_COUNT=$(wc -l < /tmp/task-mapping.txt)
echo "   总任务数: ${TASK_COUNT}"

# 步骤5: 重命名任务文件并更新引用
echo ""
echo "🔄 步骤5: 更新本地文件..."

# 创建ID映射文件
> /tmp/id-mapping.txt
while IFS=: read -r task_file task_number; do
    old_num=$(basename "$task_file" .md)
    echo "${old_num}:${task_number}" >> /tmp/id-mapping.txt
done < /tmp/task-mapping.txt

# 更新每个任务文件
while IFS=: read -r task_file task_number; do
    new_name="$(dirname "$task_file")/${task_number}.md"

    # 读取文件内容
    content=$(cat "$task_file")

    # 更新引用
    while IFS=: read -r old_num new_num; do
        content=$(echo "$content" | sed "s/\b${old_num}\b/${new_num}/g")
    done < /tmp/id-mapping.txt

    # 更新frontmatter
    current_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    github_url="https://github.com/${FULL_REPO}/issues/${task_number}"

    # 使用sed更新frontmatter字段
    content=$(echo "$content" | sed "s|^github:.*|github: ${github_url}|")
    content=$(echo "$content" | sed "s|^updated:.*|updated: ${current_date}|")

    # 写入新文件
    echo "$content" > "$new_name"

    # 删除旧文件
    if [ "$task_file" != "$new_name" ]; then
        rm "$task_file"
    fi

    echo "   📝 ${task_file} → ${new_name}"
done < /tmp/task-mapping.txt

# 步骤6: 更新Epic文件
echo ""
echo "📝 步骤6: 更新Epic文件..."
current_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
epic_url="https://github.com/${FULL_REPO}/issues/${EPIC_NUMBER}"

# 更新Epic frontmatter
epic_content=$(cat "$EPIC_FILE")
epic_content=$(echo "$epic_content" | sed "s|^github:.*|github: ${epic_url}|")
epic_content=$(echo "$epic_content" | sed "s|^updated:.*|updated: ${current_date}|")
echo "$epic_content" > "$EPIC_FILE"

# 创建更新后的Tasks Created部分
cat > /tmp/tasks-section.md << 'EOF'
## Tasks Created
EOF

# 添加每个任务
for task_file in .claude/epics/system-unification/[0-9]*.md; do
    [ -f "$task_file" ] || continue

    issue_num=$(basename "$task_file" .md)
    task_name=$(grep '^name:' "$task_file" | sed 's/^name: *//')
    parallel=$(grep '^parallel:' "$task_file" | sed 's/^parallel: *//')

    echo "- [ ] #${issue_num} - ${task_name} (parallel: ${parallel})" >> /tmp/tasks-section.md
done

# 添加统计信息
total_count=$(ls .claude/epics/system-unification/[0-9]*.md 2>/dev/null | wc -l)
parallel_count=$(grep -l '^parallel: true' .claude/epics/system-unification/[0-9]*.md 2>/dev/null | wc -l)
sequential_count=$((total_count - parallel_count))

cat >> /tmp/tasks-section.md << EOF

Total tasks: ${total_count}
Parallel tasks: ${parallel_count}
Sequential tasks: ${sequential_count}
EOF

# 替换Epic文件中的Tasks Created部分
cp "$EPIC_FILE" "$EPIC_FILE.backup"
awk '
  /^## Tasks Created/ {
    skip=1
    while ((getline line < "/tmp/tasks-section.md") > 0) print line
    close("/tmp/tasks-section.md")
  }
  /^## / && !/^## Tasks Created/ { skip=0 }
  !skip && !/^## Tasks Created/ { print }
' "$EPIC_FILE.backup" > "$EPIC_FILE"
rm "$EPIC_FILE.backup"

echo "   ✅ Epic文件已更新"

# 步骤7: 创建GitHub映射文件
echo ""
echo "📋 步骤7: 创建GitHub映射文件..."
mkdir -p .claude/epics/system-unification

cat > .claude/epics/system-unification/github-mapping.md << EOF
# GitHub Issue Mapping

Epic: #${EPIC_NUMBER} - ${epic_url}

Tasks:
EOF

# 添加任务映射
for task_file in .claude/epics/system-unification/[0-9]*.md; do
    [ -f "$task_file" ] || continue

    issue_num=$(basename "$task_file" .md)
    task_name=$(grep '^name:' "$task_file" | sed 's/^name: *//')
    task_url="https://github.com/${FULL_REPO}/issues/${issue_num}"

    echo "- #${issue_num}: ${task_name} - ${task_url}" >> .claude/epics/system-unification/github-mapping.md
done

echo "" >> .claude/epics/system-unification/github-mapping.md
echo "Synced: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> .claude/epics/system-unification/github-mapping.md

echo "   ✅ 映射文件已创建: .claude/epics/system-unification/github-mapping.md"

# 步骤8: 提交本地更改
echo ""
echo "💾 步骤8: 提交本地更改..."
git add .claude/epics/system-unification/
git add scripts/
git commit -m "Sync epic and tasks to GitHub

- Epic: #${EPIC_NUMBER} - System Unification
- Tasks: ${TASK_COUNT} sub-issues created
- Files renamed with GitHub issue numbers
- GitHub mapping created

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 步骤9: 推送到GitHub
echo ""
echo "🚀 步骤9: 推送到GitHub..."
git push -u origin main

# 步骤10: 创建工作树
echo ""
echo "🌳 步骤10: 创建开发工作树..."
if [ -d "../epic-system-unification" ]; then
    echo "   工作树已存在，跳过创建"
else
    git worktree add ../epic-system-unification -b epic/system-unification
    echo "   ✅ 工作树已创建: ../epic-system-unification"
fi

# 清理临时文件
rm -f /tmp/epic-body.md /tmp/task-body.md /tmp/task-mapping.txt /tmp/id-mapping.txt /tmp/tasks-section.md

# 最终报告
echo ""
echo "🎉 GitHub同步完成！"
echo ""
echo "📊 同步摘要:"
echo "   📁 仓库: https://github.com/${FULL_REPO}"
echo "   🎯 Epic: #${EPIC_NUMBER} - https://github.com/${FULL_REPO}/issues/${EPIC_NUMBER}"
echo "   📋 任务数: ${TASK_COUNT}"
echo "   🌳 工作树: ../epic-system-unification"
echo ""
echo "🚀 下一步操作:"
echo "   1. 查看Epic: https://github.com/${FULL_REPO}/issues/${EPIC_NUMBER}"
echo "   2. 开始并行执行: /pm:epic-start system-unification"
echo "   3. 或处理单个任务: /pm:issue-start <task-number>"
echo "   4. 查看项目状态: /pm:status"
echo ""
echo "✨ 项目管理现在已在GitHub上完全同步！"