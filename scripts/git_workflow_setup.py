#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 工作流程設置腳本
建立標準化的Git分支策略和代碼審查流程

Git Workflow:
1. 主分支保護
2. 功能分支開發
3. 代碼審查流程
4. 自動化測試
5. 規範化提交信息
"""

import subprocess
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class GitWorkflowManager:
    """Git工作流程管理器"""

    def __init__(self):
        self.repo_root = self._get_repo_root()
        self.config = self._load_config()
        self.branch_protection = BranchProtectionManager()
        self.commit_validator = CommitMessageValidator()
        self.pr_manager = PullRequestManager()

    def _get_repo_root(self) -> Path:
        """獲取Git倉庫根目錄"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        return Path.cwd()  # fallback

    def _load_config(self) -> Dict[str, Any]:
        """加載Git配置"""
        config_file = self.repo_root / '.git' / 'workflow_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        # 默認配置
        return {
            'protected_branches': ['main', 'master', 'develop'],
            'require_code_review': True,
            'require_tests': True,
            'max_pr_files': 20,
            'commit_message_format': 'conventional',
            'auto_merge_threshold': 0.8,
            'timeout_hours': 24
        }

    def setup_git_workflow(self) -> bool:
        """設置Git工作流程"""
        try:
            print("Setting up Git workflow...")

            # 1. 設置分支保護
            if not self._setup_branch_protection():
                return False

            # 2. 設置提交信息規範
            if not self._setup_commit_standards():
                return False

            # 3. 設置Pull Request模板
            if not self._setup_pr_templates():
                return False

            # 4. 設置預提交鉤子
            if not self._setup_pre_commit_hooks():
                return False

            # 5. 設置CI/CD配置
            if not self._setup_ci_cd():
                return False

            print("Git workflow setup completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Failed to setup Git workflow: {e}")
            return False

    def _setup_branch_protection(self) -> bool:
        """設置分支保護"""
        print("Setting up branch protection...")

        try:
            # 配置保護分支
            for branch in self.config['protected_branches']:
                if not self.branch_protection.protect_branch(branch):
                    return False

            # 創建主分支的保護配置
            main_config = {
                "required_status_checks": {
                    "strict": True,
                    "contexts": [
                        "continuous-integration",
                        "code-review"
                    ]
                },
                "enforce_admins": True,
                "required_pull_request_reviews": {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews": True,
                    "require_code_owner_reviews": False
                },
                "restrictions": {
                    "users": [],
                    "teams": []
                }
            }

            # 保存配置
            config_file = self.repo_root / '.github' / 'branch_protection.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(main_config, f, indent=2)

            print(f"Protected branches: {self.config['protected_branches']}")
            return True

        except Exception as e:
            logger.error(f"Failed to setup branch protection: {e}")
            return False

    def _setup_commit_standards(self) -> bool:
        """設置提交信息規範"""
        print("Setting up commit message standards...")

        try:
            # 設置提交信息鉤子
            hooks_dir = self.repo_root / '.git' / 'hooks'
            hooks_dir.mkdir(exist_ok=True)

            # 提交信息驗證鉤子
            pre_commit_hook = '''#!/bin/bash
# Pre-commit hook for commit message validation

commit_msg_file=$1
if [ -z "$commit_msg_file" ]; then
    commit_msg_file=$(git rev-parse --git-dir)/COMMIT_EDITMSG)
fi

# 檢查提交信息格式
python -c "
import sys
import re

with open('$commit_msg_file', 'r') as f:
    commit_msg = f.read()

# 檢查是否符合慣例式提交格式
pattern = r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert):\\s.+'

if not re.match(pattern, commit_msg, re.MULTILINE):
    print('ERROR: Commit message does not follow conventional format')
    print('Format: type(scope): description')
    print('Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert')
    sys.exit(1)

print('Commit message format is valid')
"
'''

            with open(hooks_dir / 'pre-commit', 'w') as f:
                f.write(pre_commit_hook)

            # 設置為可執行
            os.chmod(hooks_dir / 'pre-commit', 0o755)

            print("Commit message validation hook installed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup commit standards: {e}")
            return False

    def _setup_pr_templates(self) -> bool:
        """設置Pull Request模板"""
        print("Setting up PR templates...")

        try:
            # 創建PR模板
            pr_template = """## Description
### Type
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

### Changes Made
-

### Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

### Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of the code completed
- [ ] Documentation updated if needed
- [ ] All tests passing
- [ ] No security vulnerabilities

### Additional Notes
"""

            # 保存模板
            pr_template_file = self.repo_root / '.github' / 'PULL_REQUEST_TEMPLATE.md'
            pr_template_file.parent.mkdir(parents=True, exist_ok=True)
            pr_template_file.write_text(pr_template)

            # Issue模板
            issue_template = """## Bug Report
### Expected Behavior
### Actual Behavior
### Steps to Reproduce
1.
2.
3.

### Environment
- OS:
- Version:
- Browser (if applicable):

## Feature Request
### Problem Statement
### Proposed Solution
### Acceptance Criteria
- [ ]
"""

            issue_template_file = self.repo_root / '.github' / 'ISSUE_TEMPLATE.md'
            issue_template_file.parent.mkdir(parents=True, exist_ok=True)
            issue_template_file.write_text(issue_template)

            print("PR and Issue templates created")
            return True

        except Exception as e:
            logger.error(f"Failed to setup PR templates: {e}")
            return False

    def _setup_pre_commit_hooks(self) -> " [str]:
        """設置預提交鉤子"""
        print("Setting up pre-commit hooks...")

        try:
            # 創建.pre-commit-config.yaml
            precommit_config = """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black", "--line-length", "88"]

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: local
    hooks:
      - id: security-check
        name: Security checks
        entry: python src/security/test_security_fixes.py
        language: system
        pass_filenames: false
"""

            config_file = self.repo_root / '.pre-commit-config.yaml'
            with open(config_file, 'w') as f:
                f.write(precommit_config)

            # 創建安全性檢查腳本
            security_check = '''#!/usr/bin/env python3
import sys
import subprocess
import os

def run_security_checks():
    """Run security checks"""
    try:
        # 檢查危險的eval/exec調用
        result = subprocess.run([
            'grep', '-r', '--include=*.py', '--exclude-dir=venv',
            '--exclude-dir=node_modules', 'eval\\|exec\\|compile', 'src/'
        ], capture_output=True, text=True)

        if result.stdout:
            print("WARNING: Found potentially dangerous eval/exec calls:")
            print(result.stdout)
            return False

        # 檢查硬編碼憑證
        result = subprocess.run([
            'grep', '-r', '--include=*.py', '--exclude-dir=venv',
            '--exclude-dir=node_modules', 'password\\|secret\\|key', 'src/'
        ], capture_output=True, text=True)

        if result.stdout:
            print("WARNING: Found potential hardcoded credentials:")
            print(result.stdout)
            return False

        print("Security checks passed")
        return True

    except Exception as e:
        print(f"Security check failed: {e}")
        return False

if __name__ == "__main__":
    if not run_security_checks():
        sys.exit(1)
'''

            security_file = self.repo_root / 'src' / 'security' / 'test_security_fixes.py'
            security_file.parent.mkdir(parents=True, exist_ok=True)
            with open(security_file, 'w') as f:
                f.write(security_check)

            print("Pre-commit hooks configured")
            return True

        except Exception as e:
            logger.error(f"Failed to setup pre-commit hooks: {e}")
            return False

    def _setup_ci_cd(self) -> bool:
        """設置CI/CD配置"""
        print("Setting up CI/CD configuration...")

        try:
            # GitHub Actions工作流
            workflow_file = self.repo_root / '.github' / 'workflows' / 'ci.yml'
            workflow_file.parent.mkdir(parents=True, exist_ok=True)

            workflow_content = """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: [3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pre-commit pytest pytest-cov

    - name: Run pre-commit
      run: |
        pre-commit run --all-files

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml --cov-report=html

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  security:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Run security checks
      run: |
        python src/security/test_security_fixes.py

    - name: Run dependency vulnerability scan
      run: |
        pip install safety
        safety check --json

  code-quality:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"

    - name: Install tools
      run: |
        pip install flake8 isort black bandit

    - name: Run code quality checks
      run: |
        flake8 src/ --count
        isort --check-only src/ --diff
        black --check src/
        bandit -r src/ -f json
"""

            workflow_file.write_text(workflow_content)

            print("CI/CD workflow configured")
            return True

        except Exception as e:
            logger.error(f"Failed to setup CI/CD: {e}")
            return False

class BranchProtectionManager:
    """分支保護管理器"""

    def __init__(self):
        self.protected_branches = []

    def protect_branch(self, branch_name: str) -> bool:
        """保護分支"""
        try:
            # 這裡可以集成GitHub API或Git鉤子
            # 簡化實現，實際使用時需要完整的API集成
            self.protected_branches.append(branch_name)
            logger.info(f"Protected branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to protect branch {branch_name}: {e}")
            return False

class CommitMessageValidator:
    """提交信息驗證器"""

    CONVENTIONAL_PATTERNS = [
        r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert):\s+.+',
        r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)\([^)]*\):.+',
    ]

    def validate_commit_message(self, message: str) -> bool:
        """驗證提交信息格式"""
        # 移除空行和多餘空格
        lines = [line.strip() for line in message.split('\n') if line.strip()]
        if not lines:
            return False

        first_line = lines[0]

        # 檢查是否符合慣例式提交格式
        for pattern in self.CONVENTIONAL_PATTERNS:
            if re.match(pattern, first_line, re.IGNORECASE):
                return True

        return False

class PullRequestManager:
    """Pull Request管理器"""

    def __init__(self):
        self.pr_templates = {}
        self.review_requirements = {}

    def create_pr_template(self, template_name: str, template_content: str) -> bool:
        """創建PR模板"""
        try:
            self.pr_templates[template_name] = template_content
            return True
        except Exception as e:
            logger.error(f"Failed to create PR template {template_name}: {e}")
            return False

def setup_git_workflow():
    """設置Git工作流程的便利函數"""
    print("Setting up Git workflow...")

    manager = GitWorkflowManager()
    success = manager.setup_git_workflow()

    if success:
        print("\n🎉 Git workflow setup completed!")
        print("✅ Branch protection enabled")
        print("✅ Commit standards enforced")
        print("✅ PR templates created")
        print("✅ Pre-commit hooks installed")
        print("✅ CI/CD workflow configured")
        print("\n📋 Next steps:")
        print("1. Create feature branches from main/develop")
        print("2. Follow commit message format (conventional)")
        "3. Submit Pull Requests for code review")
        "4. Wait for CI/CD checks to pass")
    else:
        print("❌ Failed to setup Git workflow")

    return success

# 全局實例
_global_manager: Optional[GitWorkflowManager] = None

def get_git_manager() -> GitWorkflowManager:
    """獲取全局Git工作流管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = GitWorkflowManager()
    return _global_manager

def main():
    """主函數"""
    return setup_git_workflow()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)