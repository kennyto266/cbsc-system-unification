# 🤝 CBSC 系统团队协作

> **项目**: CBSC量化交易策略管理系统  
> **仓库**: https://github.com/kennyto266/cbsc-system-unification  
> **团队协作指南**: [docs/team-collaboration-guide.md](./docs/team-collaboration-guide.md)

## 🚀 快速开始

### 团队成员首次设置

1. **Clone 项目到 PyCharm**
   ```
   File → New → Project from Version Control
   URL: https://github.com/kennyto266/cbsc-system-unification.git
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行设置脚本**
   ```bash
   chmod +x scripts/setup-team-collaboration.sh
   ./scripts/setup-team-collaboration.sh
   ```

4. **加载团队别名**
   ```bash
   source team-aliases.sh
   ```

### 分支策略概览

```
main (生产环境) ← epic/* (大型功能)
                      ↓
                  feature/* (新功能)
                  fix/* (修复)
                  hotfix/* (紧急修复)
```

## 📋 团队成员

| 角色 | 成员 | GitHub | 权限 |
|------|------|--------|------|
| 👑 项目负责人 | @kennyto26 | [kennyto266](https://github.com/kennyto266) | Admin |
| 🛠️ 核心开发者 | TBD | TBD | Write |
| 👨‍💻 开发者 | TBD | TBD | Write |
| 👀 观察者 | TBD | TBD | Read |

## 🔄 日常工作流程

### 创建功能分支
```bash
feature/user-dashboard  # 创建功能分支
```

### 提交代码
```bash
gaa                    # 添加所有文件
gcm "feat: Add user dashboard"  # 提交
gph                    # 推送到远程
```

### 创建 Pull Request
```bash
gpr                    # 创建 PR（需要填写标题和描述）
```

## 📚 重要文档

- 📖 [完整团队协作指南](./docs/team-collaboration-guide.md)
- 🔧 [开发环境设置](./docs/development-setup.md)
- 🧪 [测试指南](./docs/testing-guide.md)
- 📝 [API 文档](./docs/api-documentation.md)

## 🛡️ 代码规范

### Commit 消息格式
```
<type>(<scope>): <description>

feat: 新功能
fix: 错误修复
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建过程或辅助工具的变动
```

### 分支命名规范
```
feature/功能描述    # 新功能
fix/问题描述        # 错误修复
hotfix/紧急修复     # 紧急修复
docs/文档更新       # 文档
refactor/重构       # 重构代码
```

## 🔧 有用的命令

### 团队协作别名
```bash
# 基础操作
gco <branch>        # 切换分支
gbr                 # 查看所有分支
gst                 # 查看状态
gaa                 # 添加所有文件
gcm "message"       # 提交
gph                 # 推送
gpl                 # 拉取

# PR 操作
gpr                 # 创建 Pull Request
gmr                 # 合并 Pull Request

# 快捷创建分支
feature/branch-name # 创建功能分支
fix/branch-name     # 创建修复分支
hotfix/branch-name  # 创建热修复分支
```

### 查看 Git 历史
```bash
glg                 # 查看提交历史图
git shortlog -sn    # 查看成员提交统计
git blame file.py   # 查看文件修改历史
```

## 📞 获取帮助

### 技术支持
- 📧 邮箱: dev-team@cbsc.com
- 💬 讨论: GitHub Issues
- 🚨 紧急问题: 团队群聊

### 学习资源
- [GitHub 官方文档](https://docs.github.com/)
- [PyCharm Git 教程](https://www.jetbrains.com/pycharm/guide/tutorials/working-with-git/)
- [Pro Git 中文版](https://git-scm.com/book/zh/v2)

## 🎯 当前项目状态

- **主分支**: `epic/創建個人策略管理Dashboard`
- **最后更新**: 2025-12-18
- **活动分支**: 5个
- **待处理 PR**: 0个
- **团队规模**: 扩展中

---

**记住**: 优秀的代码质量 + 良好的协作习惯 = 成功的项目！🚀

> 💡 **提示**: 遇到问题时，先查看 [团队协作指南](./docs/team-collaboration-guide.md) 或在团队群聊中求助。