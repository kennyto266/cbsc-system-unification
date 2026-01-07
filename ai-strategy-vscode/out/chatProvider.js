"use strict";
/**
 * ChatProvider - Manages AI chat interactions and strategy generation
 * Integrates with GLM API and VSCode notebook API
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChatProvider = void 0;
const vscode = __importStar(require("vscode"));
const glmClient_1 = require("./api/glmClient");
/**
 * Keywords that trigger strategy generation mode
 */
const STRATEGY_KEYWORDS = [
    'strategy',
    'trading',
    'backtest',
    'algorithm',
    'quantitative',
    'breakout',
    'mean reversion',
    'momentum',
    'buy',
    'sell',
    'signal',
    'indicator',
    'moving average',
    'bollinger',
    'rsi',
    'macd',
    'portfolio',
    'position'
];
class ChatProvider {
    constructor(context) {
        this.context = context;
        this.chatHistory = [];
        // Get API key from VSCode settings
        const config = vscode.workspace.getConfiguration('aiStrategy');
        const apiKey = config.get('glmApiKey', '');
        if (!apiKey) {
            const errorMsg = 'GLM API Key not configured. Please set aiStrategy.glmApiKey in settings.';
            vscode.window.showErrorMessage(errorMsg);
            throw new Error(errorMsg);
        }
        this.glmClient = new glmClient_1.GLMClient(apiKey);
    }
    /**
     * Send a message to the AI and get response
     * @param message - User's message
     * @returns AI's response
     */
    async sendMessage(message) {
        // Add user message to history
        this.chatHistory.push({ role: 'user', content: message });
        let response;
        // Check if user wants to generate strategy
        if (this.isStrategyRequest(message)) {
            // Use strategy generation for trading-related requests
            response = await this.glmClient.generateStrategy(message);
        }
        else {
            // Regular chat
            const glmMessages = this.convertToGLMMessages(this.chatHistory);
            response = await this.glmClient.chat(glmMessages);
        }
        // Add assistant response to history
        this.chatHistory.push({ role: 'assistant', content: response });
        return response;
    }
    /**
     * Check if message is a strategy generation request
     * @param message - User's message
     * @returns True if message contains strategy-related keywords
     */
    isStrategyRequest(message) {
        const lowerMessage = message.toLowerCase();
        return STRATEGY_KEYWORDS.some(keyword => lowerMessage.includes(keyword));
    }
    /**
     * Convert chat history to GLM message format
     * @param history - Chat history
     * @returns GLM message array
     */
    convertToGLMMessages(history) {
        return history.map(msg => ({
            role: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content
        }));
    }
    /**
     * Clear chat history
     */
    clearHistory() {
        this.chatHistory = [];
    }
    /**
     * Insert generated strategy code into active notebook
     * @param code - Generated strategy code
     */
    async insertStrategyIntoNotebook(code) {
        // Parse the generated code into cells
        const cells = this.parseCodeToCells(code);
        // Get current notebook editor
        const editor = vscode.window.activeNotebookEditor;
        if (!editor) {
            throw new Error('No active notebook editor. Please open a notebook first.');
        }
        const notebook = editor.notebook;
        // Create cell data objects
        const notebookCells = cells.map(cell => new vscode.NotebookCellData(cell.kind === 'code'
            ? vscode.NotebookCellKind.Code
            : vscode.NotebookCellKind.Markup, cell.content, cell.kind === 'code' ? 'python' : 'markdown'));
        // Create notebook edit to replace cells (append to end)
        const range = new vscode.NotebookRange(notebook.cellCount, notebook.cellCount);
        const edit = vscode.NotebookEdit.insertCells(range.start, notebookCells);
        // Create workspace edit and apply
        const workspaceEdit = new vscode.WorkspaceEdit();
        workspaceEdit.set(notebook.uri, [edit]);
        // Apply edit
        const success = await vscode.workspace.applyEdit(workspaceEdit);
        if (!success) {
            throw new Error('Failed to insert code into notebook');
        }
    }
    /**
     * Parse generated code into notebook cells
     * @param code - Generated code string
     * @returns Array of cell objects
     */
    parseCodeToCells(code) {
        const cells = [];
        // Split by markdown headers (#) or code blocks
        const lines = code.split('\n');
        let currentCell = [];
        let currentType = 'markdown';
        let inCodeBlock = false;
        for (const line of lines) {
            // Check for code block markers
            if (line.trim().startsWith('```')) {
                if (inCodeBlock) {
                    // End of code block
                    if (currentCell.length > 0) {
                        cells.push({ kind: 'code', content: currentCell.join('\n') });
                    }
                    currentCell = [];
                    inCodeBlock = false;
                }
                else {
                    // Start of code block
                    if (currentCell.length > 0) {
                        cells.push({ kind: 'markdown', content: currentCell.join('\n') });
                    }
                    currentCell = [];
                    inCodeBlock = true;
                }
                continue;
            }
            // Check for markdown headers
            if (line.trim().startsWith('#') && !inCodeBlock && currentCell.length > 0) {
                cells.push({ kind: currentType, content: currentCell.join('\n') });
                currentCell = [line];
                currentType = 'markdown';
                continue;
            }
            currentCell.push(line);
        }
        // Don't forget the last cell
        if (currentCell.length > 0) {
            cells.push({ kind: inCodeBlock ? 'code' : currentType, content: currentCell.join('\n') });
        }
        // If no cells were created, treat entire content as code
        if (cells.length === 0 && code.trim()) {
            cells.push({ kind: 'code', content: code.trim() });
        }
        return cells;
    }
    /**
     * Get chat history
     * @returns Current chat history
     */
    getHistory() {
        return [...this.chatHistory];
    }
    /**
     * Cleanup resources
     */
    async dispose() {
        await this.glmClient.close();
        this.clearHistory();
    }
}
exports.ChatProvider = ChatProvider;
//# sourceMappingURL=chatProvider.js.map