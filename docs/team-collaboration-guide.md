# 🤝 PyCharm 团队协作指南

## 📋 目录
- [快速开始](#快速开始)
- [GitHub 仓库设置](#github-仓库设置)
- [PyCharm 配置](#pycharm-配置)
- [分支策略](#分支策略)
- [日常协作流程](#日常协作流程)
- [Pull Request 流程](#pull-request-流程)
- [代码审查](#代码审查)
- [最佳实践](#最佳实践)

## 🚀 快速开始

### 1. 项目拥有者：创建和配置 GitHub 仓库

```bash
# 1. 在 GitHub 创建仓库
# 访问: https://github.com/new
# 仓库名: cbsc-system-unification
# 设置为 Public 或 Private

# 2. 邀请团队成员
# Settings → Manage access → Invite collaborators
# 添加团队成员的 GitHub 用户名
```

### 2. 团队成员：Clone 项目到 PyCharm

```bash
# 1. 获取仓库 URL
# HTTPS: https://github.com/kennyto266/cbsc-system-unification.git
# SSH: git@github.com:kennyto266/cbsc-system-unification.git

# 2. 在 PyCharm 中操作
# File → New → Project from Version Control
# 输入仓库 URL → Clone
```

## 🛠️ GitHub 仓库设置

### 分支保护规则

```bash
# 使用 GitHub CLI 或网页界面设置

gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci/travis-ci"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

### 团队权限配置

| 角色 | 权限 | 说明 |
|------|------|------|
| Admin | Admin | 项目维护者，拥有所有权限 |
| Maintainer | Write | 核心开发者，可推送和审查 |
| Developer | Write | 普通开发者，可推送特性分支 |
| Viewer | Read | 只读权限，仅可查看 |

## 💻 PyCharm 配置

### 1. Git 配置

```bash
# 设置 Git 用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 在 PyCharm 中：
# File → Settings → Version Control → Git
# 确认 Path to Git executable 正确
```

### 2. 代码风格统一

```xml
<!-- .idea/codeStyles/Project.xml -->
<component name="ProjectCodeStyleConfiguration">
  <code_scheme name="Project" version="173">
    <Python>
      <option name="USE_CONTINUATION_INDENT_FOR_ARGUMENTS" value="true" />
      <option name="CONTINUATION_INDENT_SIZE" value="4" />
    </Python>
  </code_scheme>
</component>
```

### 3. 团队设置同步

```bash
# 团队成员需要：
# 1. 克隆项目后，导入 .idea/team-collaboration.xml
# 2. 在 PyCharm 中：File → Settings → Plugins → Browse Repositories
# 3. 安装 ".ignore" 和 "Git" 相关插件
```

## 🌿 分支策略

### 分支命名规范

```bash
# 格式: <type>/<description>
feature/user-authentication    # 新功能
fix/login-bug                 # 错误修复
hotfix/security-patch         # 紧急修复
docs/api-documentation        # 文档更新
refactor/database-queries     # 代码重构
test/user-registration-tests # 测试相关
```

### 分支类型说明

| 分支类型 | 用途 | 生命周期 |
|----------|------|----------|
| `main/master` | 生产环境代码 | 长期存在，受保护 |
| `epic/*` | 大型功能开发 | 长期存在，多人协作 |
| `feature/*` | 新功能开发 | 临时，合并后删除 |
| `fix/*` | 错误修复 | 临时，合并后删除 |
| `hotfix/*` | 紧急修复 | 临时，合并后删除 |

### 分支操作命令

```bash
# 创建新分支
git checkout -b feature/user-authentication

# 切换分支
git checkout main

# 查看所有分支
git branch -a

# 删除已合并的本地分支
git branch -d feature/user-authentication

# 删除已合并的远程分支
git push origin --delete feature/user-authentication
```

## 🔄 日常协作流程

### 每日工作流程

```bash
# 1. 更新主分支代码
git checkout main
git pull origin main

# 2. 创建功能分支
git checkout -b feature/new-feature

# 3. 开发过程中定期提交
git add .
git commit -m "feat: Add user login functionality"

# 4. 推送分支到远程
git push -u origin feature/new-feature

# 5. 定期同步主分支更新
git checkout main
git pull origin main
git checkout feature/new-feature
git rebase main
```

### 在 PyCharm 中的操作

1. **查看分支**: 右下角状态栏显示当前分支
2. **创建分支**: Git → New Branch
3. **切换分支**: 右下角 → 选择分支
4. **提交代码**: Git → Commit
5. **推送代码**: Git → Push
6. **拉取更新**: Git → Pull

## 📋 Pull Request 流程

### 创建 Pull Request

```bash
# 1. 推送功能分支
git push -u origin feature/user-authentication

# 2. 在 GitHub 上创建 PR
# 或使用 GitHub CLI：
gh pr create --title "Add user authentication" --body "Implemented user login and registration"

# 3. 填写 PR 模板内容
# 4. 指定审查者
# 5. 等待代码审查
```

### PR 模板内容

```markdown
## 🎯 变更类型
- [x] 新功能 (feature)

## 📝 变更描述
添加用户认证功能，包括登录、注册和密码重置

## 🔗 相关 Issue
关联的 Issue 编号: #123

## ✅ 检查清单
- [x] 代码遵循项目规范
- [x] 添加了单元测试
- [x] 测试通过
- [x] 更新了文档

## 📚 审查者
@team-lead @senior-dev
```

### 合并 Pull Request

```bash
# 1. 确保所有检查通过
# 2. 获得必要数量的批准（至少1个）
# 3. 解决所有冲突
# 4. 使用 squash merge 或 merge commit
# 5. 删除功能分支
```

## 🔍 代码审查

### 审查者职责

1. **代码质量**: 检查代码规范和最佳实践
2. **功能正确性**: 验证代码实现了预期功能
3. **测试覆盖**: 确保有足够的测试
4. **性能考虑**: 评估性能影响
5. **安全性**: 检查潜在安全问题

### 审查流程

```bash
# 1. 收到 PR 通知
# 2. 查看代码变更
# 3. 留下评论和建议
# 4. 批准或请求修改
# 5. 跟踪修改后的代码
# 6. 最终批准合并
```

### 审查技巧

- **建设性反馈**: 提供具体的改进建议
- **解释原因**: 说明为什么需要修改
- **承认优点**: 指出做得好的地方
- **及时响应**: 尽快完成审查

## 💡 最佳实践

### Commit 消息规范

```bash
# 格式: <type>(<scope>): <description>

feat: Add user authentication
fix: Resolve login validation error
docs: Update API documentation
style: Format code according to PEP 8
refactor: Optimize database queries
test: Add unit tests for user service
chore: Update dependencies

# 详细描述
feat(auth): Add OAuth integration

- Implement OAuth2.0 flow
- Add support for Google and GitHub providers
- Update user model with OAuth fields

Fixes #123
```

### 代码提交原则

```bash
# ✅ 好的实践
git commit -m "feat(auth): Add password reset functionality"

# ❌ 避免的实践
git commit -m "fix bug"
git commit -m "update"
git commit -m "work in progress"
```

### 分支管理原则

```bash
# 1. 不要直接在 main 分支开发
# 2. 功能分支要小而专注
# 3. 定期同步 main 分支
# 4. 及时删除已合并的分支
# 5. 使用描述性的分支名
```

### 冲突解决

```bash
# 1. 更新主分支
git checkout main
git pull origin main

# 2. 切换到功能分支并变基
git checkout feature/new-feature
git rebase main

# 3. 解决冲突
# PyCharm 会显示冲突文件，手动解决

# 4. 继续变基
git rebase --continue

# 5. 强制推送（如果已推送过）
git push --force-with-lease origin feature/new-feature
```

## 🛠️ 常用命令速查

### 日常操作

```bash
# 查看状态
git status

# 查看历史
git log --oneline --graph --decorate

# 暂存更改
git stash
git stash pop

# 撤销操作
git checkout -- file.py    # 撤销文件修改
git reset HEAD file.py    # 取消暂存
git reset --soft HEAD~1   # 撤销最后一次提交
```

### 团队协作

```bash
# 查看远程仓库
git remote -v

# 查看团队成员的提交
git shortlog -sn

# 查看特定作者的提交
git log --author="username"

# 标签管理
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## 📞 获取帮助

### 团队沟通
- **技术讨论**: GitHub Issues
- **紧急问题**: 团队群聊
- **代码审查**: GitHub PR 评论

### 学习资源
- [GitHub 文档](https://docs.github.com/)
- [PyCharm Git 教程](https://www.jetbrains.com/pycharm/guide/tutorials/working-with-git/)
- [Pro Git 书籍](https://git-scm.com/book)

### 常见问题解答
1. **Q: 如何解决合并冲突？**
   A: 使用 `git rebase` 或 `git merge`，手动解决冲突文件

2. **Q: 为什么不能推送 main 分支？**
   A: main 分支受保护，需要通过 PR 合并

3. **Q: 如何撤销错误的提交？**
   A: 使用 `git reset` 或 `git revert`

4. **Q: 如何查看谁修改了某行代码？**
   A: 使用 `git blame filename`

---

## 📚 相关文档
- [项目开发规范](./development-guidelines.md)
- [API 文档](./api-documentation.md)
- [测试指南](./testing-guide.md)

**记住**: 良好的协作习惯是团队成功的关键！🚀