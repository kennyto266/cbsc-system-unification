#!/bin/bash

# 测试覆盖率检查脚本
# 用于在提交前验证测试覆盖率是否达标

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
MIN_TOTAL_COVERAGE=80
MIN_FRONTEND_COVERAGE=80
MIN_BACKEND_COVERAGE=80

echo -e "${GREEN}🔍 检查测试覆盖率...${NC}"
echo "----------------------------------------"

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 创建临时目录
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# 函数：检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ 错误: $1 命令未找到${NC}"
        exit 1
    fi
}

# 函数：检查覆盖率并返回数值
get_coverage() {
    local file=$1
    if [ -f "$file" ]; then
        # 使用 Python 解析 JSON 并提取覆盖率
        python3 -c "
import json
try:
    with open('$file', 'r') as f:
        data = json.load(f())
    # 处理前端覆盖率格式
    if 'total' in data:
        print(data.get('total', {}).get('lines', {}).get('pct', 0))
    # 处理后端覆盖率格式
    elif 'totals' in data:
        print(data.get('totals', {}).get('percent_covered', 0))
    else:
        print(0)
except:
    print(0)
" 2>/dev/null || echo 0
}

# 检查必要的命令
check_command "node"
check_command "npm"
check_command "python3"
check_command "pytest"

# 生成前端覆盖率
echo -e "\n${YELLOW}📦 生成前端覆盖率...${NC}"
cd frontend
if npm run test:coverage -- --silent --json --outputFile=coverage.json 2>/dev/null; then
    FRONTEND_COVERAGE=$(get_coverage coverage.json)
    echo -e "前端覆盖率: ${FRONTEND_COVERAGE}%"

    # 复制到临时目录
    cp coverage.json "$TEMP_DIR/frontend-coverage.json"

    if (( $(echo "$FRONTEND_COVERAGE < $MIN_FRONTEND_COVERAGE" | bc -l) )); then
        echo -e "${RED}❌ 前端覆盖率 (${FRONTEND_COVERAGE}%) 低于阈值 (${MIN_FRONTEND_COVERAGE}%)${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ 前端覆盖率检查通过${NC}"
    fi
else
    echo -e "${RED}❌ 前端测试失败${NC}"
    exit 1
fi

# 生成后端覆盖率
echo -e "\n${YELLOW}🐍 生成后端覆盖率...${NC}"
cd ..
if pytest --cov=src --cov-report=json --cov-fail-under=0 -q 2>/dev/null; then
    BACKEND_COVERAGE=$(get_coverage coverage.json)
    echo -e "后端覆盖率: ${BACKEND_COVERAGE}%"

    # 复制到临时目录
    cp coverage.json "$TEMP_DIR/backend-coverage.json"

    if (( $(echo "$BACKEND_COVERAGE < $MIN_BACKEND_COVERAGE" | bc -l) )); then
        echo -e "${RED}❌ 后端覆盖率 (${BACKEND_COVERAGE}%) 低于阈值 (${MIN_BACKEND_COVERAGE}%)${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ 后端覆盖率检查通过${NC}"
    fi
else
    echo -e "${RED}❌ 后端测试失败${NC}"
    exit 1
fi

# 计算总覆盖率
echo -e "\n${YELLOW}📊 计算总覆盖率...${NC}"
TOTAL_LINES=$(cat "$TEMP_DIR"/*-coverage.json | python3 -c "
import json, sys
total_lines = 0
covered_lines = 0

for line in sys.stdin:
    try:
        data = json.loads(line)
        if 'total' in data:  # Frontend
            total_lines += data['total']['lines']['total']
            covered_lines += data['total']['lines']['covered']
        elif 'totals' in data:  # Backend
            total_lines += data['totals']['num_statements']
            covered_lines += data['totals']['covered_statements']
    except:
        pass

if total_lines > 0:
    print(round(covered_lines / total_lines * 100, 2))
else:
    print(0)
")

echo -e "总覆盖率: ${TOTAL_LINES}%"

if (( $(echo "$TOTAL_LINES < $MIN_TOTAL_COVERAGE" | bc -l) )); then
    echo -e "${RED}❌ 总覆盖率 (${TOTAL_LINES}%) 低于阈值 (${MIN_TOTAL_COVERAGE}%)${NC}"
    exit 1
else
    echo -e "${GREEN}✅ 总覆盖率检查通过${NC}"
fi

# 显示详细的覆盖率报告
echo -e "\n${YELLOW}📋 覆盖率详情:${NC}"
echo "----------------------------------------"
printf "%-15s %10s %10s\n" "模块" "覆盖率" "状态"
printf "%-15s %10s %10s\n" "前端" "${FRONTEND_COVERAGE}%" "$(echo $FRONTEND_COVERAGE | awk -v t=$MIN_FRONTEND_COVERAGE '{if ($1 >= t) print "✅"; else print "❌"}')"
printf "%-15s %10s %10s\n" "后端" "${BACKEND_COVERAGE}%" "$(echo $BACKEND_COVERAGE | awk -v t=$MIN_BACKEND_COVERAGE '{if ($1 >= t) print "✅"; else print "❌"}')"
printf "%-15s %10s %10s\n" "总计" "${TOTAL_LINES}%" "$(echo $TOTAL_LINES | awk -v t=$MIN_TOTAL_COVERAGE '{if ($1 >= t) print "✅"; else print "❌"}')"

# 生成覆盖率徽章数据
echo -e "\n${YELLOW}🏷️ 生成覆盖率徽章...${NC}"
cat > "$TEMP_DIR/coverage-badges.json" << EOF
{
  "schemaVersion": 1,
  "label": "coverage",
  "message": "${TOTAL_LINES}%",
  "color": "$(echo $TOTAL_LINES | awk '{if ($1 >= 80) print "green"; else if ($1 >= 60) print "yellow"; else print "red"}')"
}
EOF

# 保存覆盖率数据
mkdir -p coverage
cp "$TEMP_DIR"/*-coverage.json coverage/ 2>/dev/null || true
cp "$TEMP_DIR"/coverage-badges.json coverage/ 2>/dev/null || true

# 成功信息
echo -e "\n${GREEN}✅ 所有覆盖率检查通过！${NC}"
echo "----------------------------------------"
echo "📁 覆盖率数据保存在: coverage/"
echo "🏷️ 徽章数据: coverage/coverage-badges.json"
echo ""
echo "💡 提示:"
echo "   - 运行 'python scripts/generate-coverage-report.py' 生成详细报告"
echo "   - 查看 coverage/coverage-report.html 获取可视化报告"