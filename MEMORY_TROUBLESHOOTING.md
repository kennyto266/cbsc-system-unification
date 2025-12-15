# 内存问题故障排除指南

## 问题描述

当运行前端开发服务器时遇到以下错误：
```
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
```

## 快速解决方案

### 1. 使用高内存模式启动
```bash
cd frontend
npm run dev:high-mem
```

### 2. 手动设置Node.js内存限制
```bash
# Linux/Mac
export NODE_OPTIONS="--max-old-space-size=16384"
npm run dev

# Windows
set NODE_OPTIONS=--max-old-space-size=16384
npm run dev
```

### 3. 使用修复脚本
```bash
# Linux/Mac
./scripts/fix-memory.sh

# Windows
scripts\fix-memory.bat
```

## 内存优化配置

### 已实施的优化

1. **Vite配置优化** (`frontend/vite.config.ts`)
   - 启用Terser压缩
   - 优化代码分割
   - 禁用开发环境sourcemap
   - 限制并行文件操作数

2. **启动脚本优化** (`frontend/package.json`)
   - `dev`: 8GB内存限制
   - `dev:high-mem`: 16GB内存限制
   - `build:high-mem`: 8GB内存限制

3. **环境变量配置** (`.env.memory`)
   - 设置默认内存限制
   - 优化构建选项

## 监控内存使用

### 使用监控脚本
```bash
# Linux/Mac
./scripts/memory-monitor.sh

# Windows
scripts\memory-monitor.bat
```

### 手动监控
```bash
# 查看Node.js进程内存使用
ps aux | grep node

# Windows
tasklist | findstr node.exe
```

## 预防措施

1. **定期重启开发服务器** - 长时间运行可能导致内存泄漏
2. **关闭不必要的浏览器标签** - 浏览器也会占用大量内存
3. **使用轻量级IDE** - VS Code相对较轻，避免同时打开多个重型应用
4. **定期清理缓存** - 使用修复脚本清理缓存

## 不同场景的建议

### 开发环境
- 使用 `npm run dev` 进行正常开发
- 如果内存不足，使用 `npm run dev:high-mem`

### 生产构建
- 使用 `npm run build` 进行标准构建
- 大型项目使用 `npm run build:high-mem`

### CI/CD环境
- 设置 `NODE_OPTIONS=--max-old-space-size=4096`
- 使用 `npm run build:ci`（如果配置了）

## 长期解决方案

1. **代码分割优化**
   - 实施更细粒度的代码分割
   - 使用动态导入减少初始包大小

2. **依赖优化**
   - 移除未使用的依赖
   - 使用更轻量的替代库

3. **架构优化**
   - 考虑微前端架构
   - 实施服务端渲染(SSR)

## 紧急恢复步骤

如果系统因内存问题无响应：

1. **强制终止进程**
   ```bash
   # Linux/Mac
   pkill -f node
   killall node

   # Windows
   taskkill /f /im node.exe
   ```

2. **清理系统内存**
   ```bash
   # Linux/Mac
   sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

   # Windows - 重启系统
   ```

3. **重新启动开发环境**
   ```bash
   ./scripts/fix-memory.sh
   cd frontend
   npm run dev:high-mem
   ```

## 联系支持

如果问题持续存在，请提供以下信息：
- 错误截图
- 系统内存大小
- Node.js版本
- 使用的启动命令
- 项目大小（node_modules大小）