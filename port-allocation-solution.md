# CBSC系统端口分配解决方案

## 问题概述

当前CBSC系统存在严重的端口冲突问题，特别是3000端口被多个前端系统占用，导致开发环境混乱，影响开发效率。

## 当前端口使用情况

### 冲突端口
```
3000: unified-dashboard (开发服务器)
     frontend (Create React App)
     解决方案: 保留unified-dashboard，迁移frontend
```

### 已占用端口
```
3001: unified-dashboard (预览服务器)
3003: CBSC主系统API (FastAPI)
3004: 用户管理API (FastAPI)
5432: PostgreSQL数据库
6379: Redis缓存
8000: 监控服务 (Grafana)
```

## 端口重新分配方案

### 开发环境端口分配

#### 前端服务
```
3000: unified-dashboard (主前端系统) ✅
3002: frontend (迁移中，避免冲突)
3005: localhost_interface前端
3006: strategy-dashboard重构版
```

#### 后端服务（保持不变）
```
3003: CBSC策略API
3004: 用户管理API
3010: 统一API网关 (新增)
```

#### 开发工具
```
6006: Storybook组件文档
8080: 开发代理服务器
9000: 调试服务
```

#### 数据服务（保持不变）
```
5432: PostgreSQL
6379: Redis
```

### 生产环境端口分配

#### Nginx反向代理配置
```
80/443: 统一入口端口
/api/v1/*: 后端API路由
/dashboard/*: 前端应用路由
/static/*: 静态资源路由
```

#### 内部服务端口
```
3010: API网关内部端口
3011-3020: 微服务端口范围
```

## 实施步骤

### 第一步：解决3000端口冲突（立即执行）

1. **修改frontend的端口配置**
```json
// frontend/package.json
{
  "scripts": {
    "start": "PORT=3002 react-scripts start",
    "dev": "PORT=3002 react-scripts start"
  }
}
```

2. **更新unified-dashboard的配置**
```json
// unified-dashboard/vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    strictPort: true  // 强制使用3000端口
  }
})
```

3. **创建端口占用检查脚本**
```bash
#!/bin/bash
# scripts/check-ports.sh

echo "检查端口占用情况..."
ports=(3000 3001 3002 3003 3004 3005 3006)

for port in "${ports[@]}"; do
  if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ 端口 $port 已被占用"
    lsof -i :$port
  else
    echo "❌ 端口 $port 空闲"
  fi
done
```

### 第二步：建立端口管理制度

1. **创建端口分配文档**
```markdown
# 端口分配登记表

| 端口 | 服务 | 负责人 | 状态 | 最后更新 |
|------|------|--------|------|----------|
| 3000 | unified-dashboard | Frontend Team | 活跃 | 2025-12-12 |
| 3002 | frontend (临时) | Frontend Team | 活跃 | 2025-12-12 |
```

2. **端口预约机制**
- 新服务申请端口需要提交PR
- 自动化CI检查端口冲突
- 定期审计未使用的端口

### 第三步：优化开发启动脚本

1. **统一启动脚本**
```bash
#!/bin/bash
# scripts/start-dev.sh

echo "启动CBSC开发环境..."

# 检查端口占用
./scripts/check-ports.sh

# 启动后端服务
echo "启动后端服务..."
cd src/api && python -m uvicorn main:app --port 3003 &
API_PID=$!

cd ../user-management && python -m uvicorn main:app --port 3004 &
USER_API_PID=$!

# 启动前端服务
echo "启动前端服务..."
cd ../../unified-dashboard && npm run dev &
DASHBOARD_PID=$!

cd ../frontend && PORT=3002 npm run dev &
FRONTEND_PID=$!

# 保存PID到文件
echo $API_PID > .pids/api.pid
echo $USER_API_PID > .pids/user-api.pid
echo $DASHBOARD_PID > .pids/dashboard.pid
echo $FRONTEND_PID > .pids/frontend.pid

echo "开发环境启动完成！"
echo "unified-dashboard: http://localhost:3000"
echo "frontend: http://localhost:3002"
echo "API文档: http://localhost:3003/docs"
```

2. **停止脚本**
```bash
#!/bin/bash
# scripts/stop-dev.sh

echo "停止开发环境..."

# 读取PID并终止进程
if [ -f .pids/api.pid ]; then
  kill $(cat .pids/api.pid)
  rm .pids/api.pid
fi

# 重复其他服务...

echo "所有服务已停止"
```

### 第四步：配置Nginx反向代理（生产环境）

```nginx
# nginx.conf
server {
    listen 80;
    server_name cbsc.example.com;

    # 前端应用
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API路由
    location /api/ {
        proxy_pass http://localhost:3010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket支持
    location /ws/ {
        proxy_pass http://localhost:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 长期解决方案

### 1. Docker Compose端口管理

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  unified-dashboard:
    build: ./unified-dashboard
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development

  frontend:
    build: ./frontend
    ports:
      - "3002:3000"  # 容器内3000映射到主机3002
    environment:
      - NODE_ENV=development

  api-gateway:
    build: ./src/api
    ports:
      - "3010:3010"
    depends_on:
      - postgres
      - redis
```

### 2. 动态端口分配服务

```typescript
// src/utils/port-manager.ts
class PortManager {
  private usedPorts = new Set<number>();

  async allocatePort(preferred?: number): Promise<number> {
    if (preferred && !this.isPortUsed(preferred)) {
      this.usedPorts.add(preferred);
      return preferred;
    }

    // 自动寻找可用端口
    for (let port = 3000; port < 3100; port++) {
      if (!this.isPortUsed(port)) {
        this.usedPorts.add(port);
        return port;
      }
    }

    throw new Error('No available ports');
  }

  releasePort(port: number): void {
    this.usedPorts.delete(port);
  }

  private isPortUsed(port: number): boolean {
    return this.usedPorts.has(port);
  }
}
```

### 3. 端口冲突检测CI

```yaml
# .github/workflows/port-check.yml
name: Port Conflict Check

on: [pull_request]

jobs:
  check-ports:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Check port configurations
        run: |
          # 检查配置文件中的端口冲突
          node scripts/check-port-conflicts.js

      - name: Validate port allocation
        run: |
          # 验证端口分配是否符合规范
          python scripts/validate-port-allocation.py
```

## 监控和告警

### 端口使用监控

```typescript
// src/monitoring/port-monitor.ts
import { exec } from 'child_process';

export class PortMonitor {
  async checkPortStatus(port: number): Promise<{
    port: number;
    status: 'occupied' | 'free';
    process?: string;
    pid?: number;
  }> {
    return new Promise((resolve) => {
      exec(`lsof -i :${port}`, (error, stdout) => {
        if (error) {
          resolve({ port, status: 'free' });
        } else {
          const lines = stdout.split('\n')[1];
          const parts = lines.split(/\s+/);
          resolve({
            port,
            status: 'occupied',
            process: parts[0],
            pid: parseInt(parts[1])
          });
        }
      });
    });
  }
}
```

### 告警规则

```yaml
# alerts/port-conflicts.yml
groups:
  - name: port-conflicts
    rules:
      - alert: PortConflictDetected
        expr: up{job="port-check"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "端口 {{ $labels.port }} 冲突检测"
          description: "端口 {{ $labels.port }} 预期被 {{ $labels.expected_service }} 占用，但实际被 {{ $labels.actual_process }} 占用"
```

## 最佳实践

1. **文档化所有端口使用**
   - 维护端口分配表
   - 记录端口变更历史
   - 定期审计未使用端口

2. **使用环境变量管理端口**
   ```env
   # .env.development
   UNIFIED_DASHBOARD_PORT=3000
   FRONTEND_PORT=3002
   API_GATEWAY_PORT=3010
   ```

3. **自动化检测和修复**
   - CI/CD流水线集成端口检查
   - 开发启动前自动检测
   - 冲突时提供解决方案

## 总结

通过合理的端口重新分配和管理制度，可以彻底解决CBSC系统的端口冲突问题，提高开发效率和系统稳定性。

关键措施：
1. 立即解决3000端口冲突
2. 建立端口管理制度
3. 优化开发启动流程
4. 实施长期监控方案

---

*文档版本: 1.0*
*最后更新: 2025-12-12*
*执行负责人: DevOps Team*