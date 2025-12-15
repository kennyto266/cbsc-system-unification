# CBSC 量化交易策略管理系统 - 集成测试文档

## 概述

本文档描述了CBSC量化交易策略管理系统的集成测试框架和执行方法。集成测试确保系统的各个组件能够正确协作，包括前端、后端、数据库和外部服务。

## 测试架构

### 1. 测试层级

- **单元测试**: 测试单个函数和组件
- **集成测试**: 测试组件之间的交互
- **端到端测试**: 测试完整的用户工作流

### 2. 测试覆盖范围

#### 前端集成测试 (`frontend/src/integration/`)
- API集成测试
- Redux Store集成测试
- WebSocket集成测试
- 组件交互测试
- 用户流程测试

#### 后端集成测试 (`tests/integration/`)
- 数据库集成测试
- API端点测试
- Redis缓存测试
- WebSocket连接测试
- 外部服务集成测试

#### 端到端测试 (`tests/e2e/`)
- 完整用户工作流测试
- 跨浏览器兼容性测试
- 性能测试
- 错误处理测试

## 环境配置

### 1. 测试环境要求

- Docker & Docker Compose
- Node.js 18+
- Python 3.9+
- PostgreSQL 15+
- Redis 7+

### 2. 测试数据

测试使用独立的环境和数据：
- 测试数据库: `cbsc_test`
- 测试Redis实例: 端口6380
- 模拟外部服务

## 运行测试

### 1. 快速开始

```bash
# 运行所有集成测试
./run-integration-tests.sh

# 运行特定类型的测试
./run-integration-tests.sh backend   # 仅后端测试
./run-integration-tests.sh frontend  # 仅前端测试
./run-integration-tests.sh e2e       # 仅E2E测试
```

### 2. Docker Compose环境

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行测试容器中的测试
docker-compose -f docker-compose.test.yml exec test-runner pytest

# 停止环境
docker-compose -f docker-compose.test.yml down -v
```

### 3. 本地运行

#### 后端测试

```bash
# 安装依赖
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov

# 运行测试
pytest tests/integration/ -v --cov=src
```

#### 前端测试

```bash
# 安装依赖
cd frontend
npm install

# 运行集成测试
npm run test:integration

# 生成覆盖率报告
npm run test:coverage
```

#### E2E测试

```bash
# 安装Playwright
npm install -g @playwright/test
npx playwright install

# 运行E2E测试
npx playwright test tests/e2e/
```

## 测试数据生成

### 1. 使用测试数据生成器

```python
# 后端
from tests.integration.fixtures.test_data_generator import TestDataGenerator

generator = TestDataGenerator(seed=42)
market_data = generator.generate_market_data(
    symbol="00700.HK",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)
```

```typescript
// 前端
import { testUtils } from '@/integration/fixtures/frontendTestData';

const strategy = testUtils.strategy();
const portfolio = testUtils.portfolio();
```

### 2. 自定义测试数据

- 创建测试夹具文件
- 使用`@pytest.fixture`装饰器
- 实现`setup()`和`teardown()`方法

## 测试最佳实践

### 1. 编写测试

- **独立性**: 每个测试应该独立运行
- **可重复性**: 测试结果应该一致
- **快速执行**: 优化测试执行时间
- **清晰的断言**: 使用有意义的断言消息

### 2. 测试组织

```
tests/
├── unit/                  # 单元测试
├── integration/          # 集成测试
│   ├── api/             # API集成测试
│   ├── database/        # 数据库集成测试
│   └── websocket/       # WebSocket集成测试
├── e2e/                  # 端到端测试
├── fixtures/             # 测试数据
└── conftest.py          # pytest配置
```

### 3. Mock使用

```python
# Mock外部API
@pytest.fixture
def mock_external_api():
    with patch('src.external.api_client') as mock:
        mock.return_value = {"data": "test"}
        yield mock
```

```typescript
// Mock API调用
import { server } from './mocks/server';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## 持续集成

### 1. GitHub Actions配置

```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Docker
        run: docker-compose -f docker-compose.test.yml build
      - name: Run Tests
        run: ./run-integration-tests.sh all 4 true
```

### 2. 报告生成

测试报告自动生成并保存在：
- HTML报告: `test-reports/`
- JUnit XML: `test-reports/*.xml`
- 覆盖率报告: `coverage/`
- Playwright报告: `test-reports/playwright/`

## 故障排除

### 1. 常见问题

#### 测试数据库连接失败
```bash
# 检查PostgreSQL容器状态
docker-compose -f docker-compose.test.yml ps postgres-test

# 查看日志
docker-compose -f docker-compose.test.yml logs postgres-test
```

#### 前端测试超时
```bash
# 增加超时时间
npm run test:integration -- --testTimeout=60000
```

#### E2E测试失败
```bash
# 使用调试模式
npx playwright test --debug
```

### 2. 性能优化

- 使用测试并行化 (`-n`参数)
- 实施测试缓存
- 优化数据库查询
- 使用内存数据库进行简单测试

## 测试覆盖率

### 目标覆盖率

- 单元测试: 80%+
- 集成测试: 70%+
- E2E测试: 覆盖关键用户流程

### 查看覆盖率

```bash
# 后端
open coverage/html/index.html

# 前端
open frontend/coverage/lcov-report/index.html
```

## 维护和更新

### 1. 添加新测试

1. 确定测试类型和位置
2. 编写测试用例
3. 添加必要的夹具
4. 更新文档

### 2. 更新测试环境

1. 更新Docker镜像
2. 修改测试配置
3. 验证兼容性
4. 运行完整测试套件

### 3. 测试数据管理

- 定期清理过期的测试数据
- 更新测试数据生成器
- 保持测试数据的真实性

## 联系支持

如有问题或需要帮助，请联系：
- 测试团队: test-team@cbsc.com
- DevOps团队: devops@cbsc.com
- 项目负责人: project-lead@cbsc.com

---

*最后更新: 2024-12-14*
*版本: 1.0*