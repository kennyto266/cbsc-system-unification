/**
 * GLM-4.6 Integration Patch for agent-foreman
 * 添加GLM-4.6 CLI支持到agent-foreman
 */

const fs = require('fs');
const path = require('path');

// GLM-4.6 代理配置
const GLM46_AGENT = {
    name: "glm46",
    command: ["glm", "--output-format", "text", "--non-interactive"],
    promptViaStdin: true,
};

// 读取原始agents.js文件
const agentsJsPath = "/c/Users/Penguin8n/AppData/Roaming/npm/node_modules/agent-foreman/dist/agents.js";

function patchAgentsFile() {
    try {
        let content = fs.readFileSync(agentsJsPath, 'utf8');

        // 查找DEFAULT_AGENTS数组定义
        const defaultAgentsStart = content.indexOf('export const DEFAULT_AGENTS = [');
        const defaultAgentsEnd = content.indexOf('];', defaultAgentsStart) + 2;

        if (defaultAgentsStart === -1 || defaultAgentsEnd === -1) {
            console.error('无法找到DEFAULT_AGENTS数组定义');
            return false;
        }

        // 解析现有的DEFAULT_AGENTS
        const agentsArrayStr = content.substring(defaultAgentsStart, defaultAgentsEnd);

        // 创建新的DEFAULT_AGENTS，添加GLM-4.6
        const newAgentsArray = agentsArrayStr.replace(
            'export const DEFAULT_AGENTS = [',
            'export const DEFAULT_AGENTS = [\n    // GLM-4.6: Chinese AI model with full permissions\n    {\n        name: "glm46",\n        command: ["glm", "--output-format", "text", "--non-interactive"],\n        promptViaStdin: true,\n    },'
        );

        // 替换原始内容
        const newContent = content.replace(agentsArrayStr, newAgentsArray);

        // 备份原文件
        const backupPath = agentsJsPath + '.backup';
        fs.writeFileSync(backupPath, content);

        // 写入修改后的内容
        fs.writeFileSync(agentsJsPath, newContent);

        console.log('✅ GLM-4.6 support added to agent-foreman successfully!');
        console.log(`📁 Original file backed up to: ${backupPath}`);
        return true;

    } catch (error) {
        console.error('❌ Failed to patch agents.js:', error.message);
        return false;
    }
}

// 检查GLM CLI是否可用
function checkGLMCLI() {
    const { spawnSync } = require('child_process');
    const result = spawnSync('where', ['glm'], { stdio: 'pipe', shell: true });
    return result.status === 0;
}

// 主函数
function main() {
    console.log('🔧 Adding GLM-4.6 support to agent-foreman...');

    if (!checkGLMCLI()) {
        console.error('❌ GLM CLI not found. Please install GLM CLI first.');
        console.log('💡 Installation: npm install -g @glm/cli');
        process.exit(1);
    }

    if (patchAgentsFile()) {
        console.log('🎉 Patch completed! GLM-4.6 is now available in agent-foreman.');
        console.log('📋 Available agents: claude, gemini, codex, glm46');
        console.log('🚀 You can now run: agent-foreman analyze');
    } else {
        console.error('❌ Failed to apply patch. Please check permissions.');
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { patchAgentsFile, checkGLMCLI };