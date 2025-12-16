#!/usr/bin/env node

/**
 * 任務清理腳本
 * 用於批量更新和清理 GitHub Issues
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// GitHub API token
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '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';

// 任務映射配置
const TASK_MAPPINGS = {
  // Square-UI 前端框架集成 (Epic #50)
  'square-ui-integration': {
    epic: '#50',
    prefix: 'UI-',
    issues: {
      59: { title: 'UI-009: 用戶管理界面開發', labels: ['frontend', 'ui', 'P2'] },
      60: { title: 'UI-010: 性能優化和代碼分割', labels: ['frontend', 'optimize', 'P2'] },
      61: { title: 'UI-011: 測試體系建設', labels: ['test', 'P2'] },
      62: { title: 'UI-012: 部署上線和文檔', labels: ['deploy', 'docs', 'P2'] }
    }
  },

  // 個人策略管理Dashboard (Epic #2)
  'personal-dashboard': {
    epic: '#2',
    prefix: 'Dashboard-',
    issues: {
      55: { title: 'Dashboard-005: 狀態管理架構實現', labels: ['frontend', 'react', 'P2'] },
      56: { title: 'Dashboard-006: API 集成層開發', labels: ['backend', 'api', 'P2'] },
      57: { title: 'Dashboard-007: 策略管理界面實現', labels: ['frontend', 'ui', 'P2'] },
      58: { title: 'Dashboard-008: 數據可視化組件開發', labels: ['frontend', 'charts', 'P2'] }
    }
  },

  // CBSC 系統統一整合 (Epic #11)
  'cbsc-integration': {
    epic: '#11',
    prefix: 'Unify-',
    issues: {
      39: { title: 'Unify-001: 系統架構深入分析與規劃', labels: ['backend', 'architecture', 'P1'] },
      40: { title: 'Unify-002: 策略管理系統重構 - 模組化重構與API統一', labels: ['backend', 'refactor', 'P1'] },
      17: { title: 'Unify-003: 後端服務整合 - API網關與服務治理', labels: ['backend', 'api', 'P1'] },
      18: { title: 'Unify-004: 數據架構重構 - PostgreSQL + Redis 統一架構', labels: ['backend', 'database', 'P1'] }
    }
  }
};

// 執行 GitHub CLI 命令
function execGH(command) {
  try {
    const fullCommand = `export GITHUB_TOKEN=${GITHUB_TOKEN} && ${command}`;
    console.log(`執行: ${command}`);
    const result = execSync(fullCommand, { encoding: 'utf8', stdio: 'pipe' });
    return result;
  } catch (error) {
    console.error(`錯誤: ${command}`);
    console.error(error.stderr.toString());
    return null;
  }
}

// 更新單個任務
function updateTask(issueNumber, config) {
  console.log(`\n更新任務 #${issueNumber}...`);

  // 更新標題
  if (config.title) {
    execGH(`gh issue edit ${issueNumber} --title "${config.title}"`);
  }

  // 添加標籤
  if (config.labels && config.labels.length > 0) {
    const labelArgs = config.labels.map(label => `--add-label "${label}"`).join(' ');
    execGH(`gh issue edit ${issueNumber} ${labelArgs}`);
  }

  // 添加狀態標籤
  execGH(`gh issue edit ${issueNumber} --add-label "status:planning"`);

  // 添加 epic 關聯
  if (config.epic) {
    const comment = `此任務屬於 ${config.epic} Epic。參考 [任務命名規範](.claude/docs/task-naming-conventions.md)`;
    execGH(`gh issue comment ${issueNumber} --body "${comment}"`);
  }
}

// 關閉空任務
function closeEmptyTask(issueNumber) {
  console.log(`\n關閉空任務 #${issueNumber}...`);
  execGH(`gh issue close ${issueNumber} --comment "關閉空任務 - 沒有具體內容" --reason "not planned"`);
}

// 生成報告
function generateReport() {
  const report = {
    timestamp: new Date().toISOString(),
    updated: [],
    closed: [],
    errors: []
  };

  // 處理每個分組
  Object.entries(TASK_MAPPINGS).forEach(([group, config]) => {
    console.log(`\n處理分組: ${group}`);

    Object.entries(config.issues).forEach(([issueNum, issueConfig]) => {
      const result = updateTask(parseInt(issueNum), issueConfig);
      if (result !== null) {
        report.updated.push(parseInt(issueNum));
      } else {
        report.errors.push(parseInt(issueNum));
      }
    });
  });

  // 關閉空任務 #51, #52
  [51, 52].forEach(issueNum => {
    closeEmptyTask(issueNum);
    report.closed.push(issueNum);
  });

  // 保存報告
  const reportPath = path.join(__dirname, '../reports', `task-cleanup-${Date.now()}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log('\n任務清理完成！');
  console.log(`更新: ${report.updated.length} 個任務`);
  console.log(`關閉: ${report.closed.length} 個任務`);
  console.log(`錯誤: ${report.errors.length} 個任務`);
  console.log(`報告已保存到: ${reportPath}`);
}

// 主函數
function main() {
  console.log('開始清理任務...');
  console.log('確保已安裝並認證 GitHub CLI');

  // 檢查認證
  const authResult = execGH('gh auth status');
  if (!authResult) {
    console.error('GitHub CLI 認證失敗，請先運行: gh auth login');
    process.exit(1);
  }

  generateReport();
}

// 執行主函數
if (require.main === module) {
  main();
}

module.exports = {
  updateTask,
  closeEmptyTask,
  generateReport
};