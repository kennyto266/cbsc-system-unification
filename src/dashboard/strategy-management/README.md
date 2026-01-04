# 个人策略管理Dashboard

一个用于管理和监控量化交易策略的Web Dashboard。

## 功能特性

### 核心功能
- **策略管理**: 创建、编辑、删除、启动和停止交易策略（最多4个）
- **实时监控**: 查看策略运行状态和实时性能指标
- **数据可视化**:
  - 净值曲线图
  - 回撤分析图
  - 月度收益热力图
- **性能指标**:
  - 总收益率
  - Sharpe比率
  - 最大回撤
  - 策略运行统计

### 技术特性
- **响应式设计**: 支持桌面、平板和移动设备
- **主题切换**: 支持浅色/深色主题
- **实时更新**: 自动刷新数据（30秒间隔）
- **本地缓存**: 离线支持策略数据缓存
- **错误处理**: 完善的错误处理和用户反馈

## 快速开始

### 1. 环境要求
- 现代Web浏览器（Chrome, Firefox, Safari, Edge）
- FastAPI后端服务运行在 `http://localhost:3003`

### 2. 直接在浏览器中打开
```bash
# 使用本地服务器（推荐）
# 进入项目目录
cd src/dashboard/strategy-management

# 使用Python的内置服务器
python -m http.server 8080

# 或使用Node.js的http-server
npx http-server -p 8080

# 然后在浏览器中访问
open http://localhost:8080
```

### 3. 集成到现有项目
```html
<!-- 在你的HTML文件中引入 -->
<link rel="stylesheet" href="path/to/dashboard/css/main.css">
<link rel="stylesheet" href="path/to/dashboard/css/components.css">
<link rel="stylesheet" href="path/to/dashboard/css/responsive.css">
<link rel="stylesheet" href="path/to/dashboard/css/dashboard.css">
<link rel="stylesheet" href="path/to/dashboard/css/forms.css">

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<!-- Dashboard脚本 -->
<script type="module" src="path/to/dashboard/js/dashboard.js"></script>
```

## 项目结构

```
src/dashboard/strategy-management/
├── index.html              # 主页面
├── css/                    # 样式文件
│   ├── main.css           # 基础样式和变量
│   ├── components.css     # UI组件样式
│   ├── responsive.css     # 响应式样式
│   ├── dashboard.css      # Dashboard专用样式
│   └── forms.css          # 表单样式
├── js/                     # JavaScript文件
│   ├── constants.js       # 常量定义
│   ├── utils.js           # 工具函数
│   ├── storage.js         # 本地存储管理
│   ├── api.js             # API客户端
│   ├── event-bus.js       # 事件总线
│   ├── error-handler.js   # 错误处理
│   ├── websocket.js       # WebSocket客户端（可选）
│   ├── chart.js           # 图表基础类
│   ├── net-value-chart.js # 净值曲线图
│   ├── drawdown-chart.js  # 回撤图
│   ├── sharpe-chart.js    # Sharpe比率图
│   ├── heatmap.js         # 月度热力图
│   ├── strategy-manager.js # 策略管理器
│   ├── strategy-list.js   # 策略列表组件
│   ├── strategy-form.js   # 策略表单组件
│   └── dashboard.js       # 主Dashboard类
└── assets/                 # 资源文件
    ├── icons/             # 图标
    └── images/            # 图片
```

## 配置选项

### API配置
在 `js/constants.js` 中修改 `API_CONFIG`:
```javascript
export const API_CONFIG = {
    BASE_URL: 'http://localhost:3003',  // 修改为你的API地址
    TIMEOUT: 5000,                      // 请求超时时间
    RETRY_ATTEMPTS: 3,                 // 重试次数
    RETRY_DELAY: 1000                  // 重试延迟
};
```

### 主题配置
在 `js/constants.js` 中添加自定义颜色：
```javascript
export const CHART_CONFIG = {
    COLORS: [
        '#4299e1', // 自定义颜色1
        '#48bb78', // 自定义颜色2
        // ...
    ]
};
```

## API接口要求

Dashboard需要后端提供以下API接口：

### 策略管理
- `GET /api/strategies` - 获取策略列表
- `POST /api/strategies` - 创建新策略
- `GET /api/strategies/{id}` - 获取策略详情
- `PUT /api/strategies/{id}` - 更新策略
- `POST /api/strategies/{id}/start` - 启动策略
- `POST /api/strategies/{id}/stop` - 停止策略
- `POST /api/strategies/{id}/delete` - 删除策略

### 性能数据
- `GET /api/strategies/{id}/performance?period=1m` - 获取策略性能数据

### 响应格式
```json
{
    "success": true,
    "data": {
        // 实际数据
    },
    "message": "操作成功"
}
```

## 自定义扩展

### 添加新的图表类型
1. 在 `js/chart.js` 中扩展基础类
2. 创建新的图表组件文件
3. 在 `js/dashboard.js` 中初始化

### 添加新的策略类型
在 `js/constants.js` 中更新 `STRATEGY_TYPES`:
```javascript
export const STRATEGY_TYPES = {
    // 现有类型...
    CUSTOM_TYPE: {
        value: 'custom',
        label: '自定义策略',
        description: '自定义交易策略',
        icon: 'cog'
    }
};
```

### 修改主题
在 `css/main.css` 中的 `:root` 和 `[data-theme="dark"]` 中更新CSS变量。

## 浏览器兼容性

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 开发说明

### 代码规范
- 使用ES6+模块化开发
- 遵循函数式编程原则
- 使用CSS变量进行主题管理
- 组件化设计，松耦合架构

### 调试技巧
1. 打开浏览器开发者工具
2. 查看Console日志
3. 使用Network面板监控API请求
4. 使用断点调试JavaScript

### 性能优化
- 图表数据缓存
- 防抖和节流
- 延迟加载
- 图片优化

## 故障排除

### 常见问题

**Q: 图表不显示**
A: 检查：
1. Chart.js是否正确加载
2. Canvas元素是否存在
3. 数据格式是否正确

**Q: API请求失败**
A: 检查：
1. 后端服务是否运行
2. API地址是否正确
3. 网络连接是否正常

**Q: 策略数据不更新**
A: 检查：
1. 自动刷新是否启用
2. 浏览器标签页是否活跃
3. 检查Network请求

## 更新日志

### v1.0.0 (2025-12-18)
- 初始版本发布
- 完整的策略管理功能
- 数据可视化图表
- 响应式设计
- 主题切换支持

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。