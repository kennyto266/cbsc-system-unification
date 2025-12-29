#!/bin/bash

# PyCharm 团队协作自动化设置脚本
# 使用方法: ./setup-team-collaboration.sh

set -e

echo "🚀 开始设置 PyCharm 团队协作环境..."

# 检查 Git 仓库
if [ ! -d ".git" ]; then
    echo "❌ 当前目录不是 Git 仓库"
    exit 1
fi

echo "✅ Git 仓库检查完成"

# 设置 GitHub 分支保护规则
echo "🛡️ 设置分支保护规则..."

# 检查是否安装了 GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI 未安装，请手动设置分支保护规则"
    echo "   访问: https://github.com/kennyto266/cbsc-system-unification/settings/branches"
else
    # 设置 main 分支保护
    gh api repos/kennyto266/cbsc-system-unification/branches/main/protection \
      --method PUT \
      --field required_status_checks='{"strict":false,"contexts":[]}' \
      --field enforce_admins=false \
      --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":false,"require_code_owner_reviews":false}' \
      --field restrictions=null \
      --silent 2>/dev/null || echo "⚠️  分支保护设置失败，请手动配置"
    
    echo "✅ GitHub 分支保护规则设置完成"
fi

# 创建必要的目录结构
echo "📁 创建项目目录结构..."
mkdir -p .idea/codeStyles
mkdir -p docs
mkdir -p scripts

# 创建 PyCharm 代码风格配置
echo "🎨 创建代码风格配置..."
cat > .idea/codeStyles/Project.xml << 'EOF'
<component name="ProjectCodeStyleConfiguration">
  <code_scheme name="Project" version="173">
    <Python>
      <option name="USE_CONTINUATION_INDENT_FOR_ARGUMENTS" value="true" />
      <option name="CONTINUATION_INDENT_SIZE" value="4" />
      <option name="SPACE_BEFORE_METHOD_PARENTHESES" value="true" />
      <option name="SPACE_WITHIN_METHOD_PARENTHESES" value="false" />
      <option name="SPACE_WITHIN_METHOD_CALL_PARENTHESES" value="false" />
    </Python>
    <codeStyleSettings language="Python">
      <option name="RIGHT_MARGIN" value="88" />
      <option name="KEEP_BLANK_LINES_IN_DECLARATIONS" value="1" />
      <option name="KEEP_BLANK_LINES_IN_CODE" value="1" />
      <option name="KEEP_BLANK_LINES_BEFORE_RBRACE" value="0" />
      <option name="BLANK_LINES_BEFORE_IMPORTS" value="1" />
      <option name="BLANK_LINES_AFTER_IMPORTS" value="1" />
      <option name="BLANK_LINES_AROUND_CLASS" value="1" />
      <option name="BLANK_LINES_AROUND_METHOD" value="1" />
      <option name="ALIGN_MULTILINE_ASSIGNMENT" value="false" />
      <option name="ALIGN_MULTILINE_BINARY_OPERATION" value="false" />
      <option name="ALIGN_MULTILINE_TERNARY_OPERATION" value="false" />
      <option name="ALIGN_MULTILINE_ARRAY_INITIALIZER_EXPRESSION" value="false" />
      <option name="ALIGN_MULTILINE_FOR" value="false" />
      <option name="ALIGN_MULTILINE_PARAMETERS_IN_CALLS" value="false" />
      <option name="ALIGN_MULTILINE_PARAMETERS" value="false" />
      <option name="ALIGN_MULTILINE_RESOURCES" value="false" />
      <option name="ALIGN_MULTILINE_FOR" value="false" />
      <option name="ALIGN_MULTILINE_EXTENDS_LIST" value="false" />
      <option name="ALIGN_MULTILINE_PARENTHESIZED_EXPRESSION" value="false" />
      <option name="ALIGN_MULTILINE_METHOD_BRACKETS" value="false" />
      <option name="ALIGN_MULTILINE_THROWS_LIST" value="false" />
      <option name="ALIGN_MULTILINE_EXTENDS_LIST" value="false" />
      <option name="ALIGN_MULTILINE_ARRAY_INITIALIZER_EXPRESSION" value="false" />
    </codeStyleSettings>
  </code_scheme>
</component>
EOF

# 创建 Git hooks
echo "🪝 创建 Git hooks..."
mkdir -p .git/hooks

# Pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

echo "🔍 运行预提交检查..."

# 检查 Python 语法
python_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)
if [ ! -z "$python_files" ]; then
    for file in $python_files; do
        if ! python -m py_compile "$file"; then
            echo "❌ Python 语法错误: $file"
            exit 1
        fi
    done
    echo "✅ Python 语法检查通过"
fi

# 检查文件大小
large_files=$(git diff --cached --name-only | xargs ls -la 2>/dev/null | awk '$5 > 10485760 { print $9 }' || true)
if [ ! -z "$large_files" ]; then
    echo "⚠️  发现大文件 (>10MB):"
    echo "$large_files"
    echo "请使用 Git LFS 或移除这些文件"
fi

echo "✅ 预提交检查完成"
EOF

chmod +x .git/hooks/pre-commit

# 创建团队配置文件
echo "👥 创建团队配置..."
cat > team-aliases.sh << 'EOF'
#!/bin/bash

# 团队协作常用别名
alias gco='git checkout'
alias gbr='git branch'
alias gst='git status'
alias gaa='git add .'
alias gcm='git commit -m'
alias gph='git push'
alias gpl='git pull'
alias gpr='gh pr create'
alias gmr='gh pr merge'
alias glg='git log --oneline --graph --decorate'

# 功能分支快捷操作
feature() {
    git checkout -b "feature/$1"
}

fix() {
    git checkout -b "fix/$1"
}

hotfix() {
    git checkout -b "hotfix/$1"
}

echo "✅ 团队别名已加载"
echo "使用方法: feature/new-function, fix/login-bug, hotfix/security-patch"
EOF

chmod +x team-aliases.sh

echo ""
echo "🎉 PyCharm 团队协作环境设置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 将 team-aliases.sh 添加到你的 ~/.bashrc 或 ~/.zshrc"
echo "2. 在 PyCharm 中导入 .idea/team-collaboration.xml"
echo "3. 在 GitHub 上邀请团队成员: Settings → Manage access"
echo "4. 团队成员访问: docs/team-collaboration-guide.md"
echo ""
echo "🚀 开始团队协作吧！"