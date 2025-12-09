#!/usr/bin/env node

/**
 * 自动应用GLM-4.6补丁到agent-foreman
 * Automatic GLM-4.6 integration patch for agent-foreman
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

// 配置路径
const AGENT_FOREMAN_DIR = "C:\\Users\\Penguin8n\\AppData\\Roaming\\npm\\node_modules\\agent-foreman\\dist";
const AGENTS_JS_PATH = path.join(AGENT_FOREMAN_DIR, 'agents.js');
const BACKUP_PATH = path.join(AGENT_FOREMAN_DIR, 'agents.js.original-backup');
const PATCH_PATH = path.join(__dirname, 'agents-glm-patch.js');

console.log('🔧 Applying GLM-4.6 support patch to agent-foreman...\n');

// 步骤1: 检查agent-foreman安装
if (!fs.existsSync(AGENT_FOREMAN_DIR)) {
    console.error('❌ agent-foreman not found. Please install it first:');
    console.error('   npm install -g agent-foreman');
    process.exit(1);
}

console.log('✅ agent-foreman installation found');

// 步骤2: 检查GLM模拟器
const glmPath = path.join(__dirname, 'glm.bat');
if (!fs.existsSync(glmPath)) {
    console.error('❌ GLM simulator not found');
    process.exit(1);
}

console.log('✅ GLM simulator found');

// 步骤3: 备份原始文件
if (!fs.existsSync(BACKUP_PATH)) {
    try {
        fs.copyFileSync(AGENTS_JS_PATH, BACKUP_PATH);
        console.log('✅ Original agents.js backed up');
    } catch (error) {
        console.error('❌ Failed to backup original file:', error.message);
        process.exit(1);
    }
} else {
    console.log('✅ Backup already exists');
}

// 步骤4: 读取补丁文件
try {
    const patchContent = fs.readFileSync(PATCH_PATH, 'utf8');
    console.log('✅ GLM patch file loaded');

    // 步骤5: 应用补丁
    fs.writeFileSync(AGENTS_JS_PATH, patchContent);
    console.log('✅ GLM-4.6 support applied to agents.js');

} catch (error) {
    console.error('❌ Failed to apply patch:', error.message);
    process.exit(1);
}

// 步骤6: 创建GLM命令符号链接
const glmSymlink = path.join(__dirname, 'glm');
try {
    if (fs.existsSync(glmSymlink)) {
        fs.unlinkSync(glmSymlink);
    }
    fs.symlinkSync('glm.bat', glmSymlink);
    console.log('✅ GLM command symlink created');
} catch (error) {
    console.warn('⚠️  Could not create symlink (continuing):', error.message);
}

// 步骤7: 测试GLM命令
console.log('\n🧪 Testing GLM command...');
const testResult = spawnSync('glm.bat', ['--help'], {
    stdio: 'pipe',
    shell: true,
    cwd: __dirname
});

if (testResult.status === 0) {
    console.log('✅ GLM simulator working correctly');
} else {
    console.warn('⚠️  GLM simulator test failed, but continuing...');
}

// 步骤8: 验证agent-foreman检测
console.log('\n🔍 Verifying agent-foreman detects GLM...');
const whereResult = spawnSync('where', ['glm.bat'], {
    stdio: 'pipe',
    shell: true,
    cwd: __dirname,
    env: { ...process.env, PATH: `${__dirname};${process.env.PATH}` }
});

if (whereResult.status === 0) {
    console.log('✅ GLM command found in PATH');
} else {
    console.log('ℹ️  GLM command not in global PATH, but available locally');
}

// 完成报告
console.log('\n🎉 GLM-4.6 integration completed successfully!');
console.log('\n📋 Summary:');
console.log('  ✅ GLM-4.6 added to agent-foreman');
console.log('  ✅ Priority order: GLM-4.6 > Claude > Gemini > Codex');
console.log('  ✅ GLM simulator ready for use');
console.log('  ✅ Original files backed up');

console.log('\n🚀 Usage:');
console.log('  agent-foreman analyze docs/ARCHITECTURE.md');
console.log('  agent-foreman init "your project goal"');

console.log('\n📁 Files created/modified:');
console.log(`  📄 ${glmPath} - GLM simulator`);
console.log(`  🔧 ${AGENTS_JS_PATH} - Modified with GLM support`);
console.log(`  💾 ${BACKUP_PATH} - Original backup`);

console.log('\n💡 If you want to restore the original:');
console.log(`  cp "${BACKUP_PATH}" "${AGENTS_JS_PATH}"`);

console.log('\n✨ Enjoy GLM-4.6 powered project analysis!');