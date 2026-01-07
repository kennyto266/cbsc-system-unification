"use strict";
/**
 * Tests for ChatProvider class
 * Following TDD approach: write failing tests first
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
const globals_1 = require("@jest/globals");
const vscode = __importStar(require("vscode"));
const chatProvider_1 = require("../chatProvider");
// Mock vscode module
globals_1.jest.mock('vscode', () => ({
    window: {
        showErrorMessage: globals_1.jest.fn(),
        activeNotebookEditor: null,
        showNotebookDocument: globals_1.jest.fn(),
    },
    workspace: {
        getConfiguration: globals_1.jest.fn(),
        openNotebookDocument: globals_1.jest.fn(),
        applyEdit: globals_1.jest.fn(),
    },
    WorkspaceEdit: globals_1.jest.fn(),
    Uri: {},
    NotebookRange: globals_1.jest.fn(),
    NotebookCellData: globals_1.jest.fn(),
    NotebookCellKind: {
        Code: 1,
        Markup: 2,
    },
    ViewColumn: {
        One: 1,
        Beside: 2,
    },
    ExtensionContext: {},
}));
(0, globals_1.describe)('ChatProvider', () => {
    let mockContext;
    let mockGLMClient;
    (0, globals_1.beforeEach)(() => {
        // Reset mocks before each test
        globals_1.jest.clearAllMocks();
        mockContext = {
            subscriptions: [],
            globalState: {
                get: globals_1.jest.fn(),
                update: globals_1.jest.fn(),
            },
            workspaceState: {
                get: globals_1.jest.fn(),
                update: globals_1.jest.fn(),
            },
        };
        // Mock GLM client
        mockGLMClient = {
            chat: globals_1.jest.fn(),
            generateStrategy: globals_1.jest.fn(),
        };
    });
    (0, globals_1.describe)('Initialization', () => {
        (0, globals_1.it)('should throw error when API key is not configured', () => {
            // Mock configuration without API key
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue(''),
            });
            (0, globals_1.expect)(() => {
                new chatProvider_1.ChatProvider(mockContext);
            }).toThrow('GLM API Key not configured');
        });
        (0, globals_1.it)('should initialize with valid API key', () => {
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue('test-api-key-12345'),
            });
            const provider = new chatProvider_1.ChatProvider(mockContext);
            (0, globals_1.expect)(provider).toBeDefined();
        });
    });
    (0, globals_1.describe)('Message Handling', () => {
        (0, globals_1.it)('should detect strategy request keywords', () => {
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue('test-api-key'),
            });
            const provider = new chatProvider_1.ChatProvider(mockContext);
            // Test various strategy keywords
            const strategyRequests = [
                'Create a trading strategy',
                'Implement moving average algorithm',
                'Backtest this signal',
                'Buy when RSI < 30',
                'Sell at breakout',
                'Use indicator for confirmation',
                'momentum trading',
            ];
            strategyRequests.forEach(request => {
                (0, globals_1.expect)(provider['isStrategyRequest'](request)).toBe(true);
            });
        });
        (0, globals_1.it)('should handle non-strategy chat messages', async () => {
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue('test-api-key'),
            });
            const provider = new chatProvider_1.ChatProvider(mockContext);
            // Mock regular chat response
            mockGLMClient.chat.mockResolvedValue('I can help with that!');
            const response = await provider.sendMessage('Hello, how are you?');
            (0, globals_1.expect)(response).toBe('I can help with that!');
            (0, globals_1.expect)(mockGLMClient.chat).toHaveBeenCalled();
        });
        (0, globals_1.it)('should handle strategy generation requests', async () => {
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue('test-api-key'),
            });
            const provider = new chatProvider_1.ChatProvider(mockContext);
            // Mock strategy generation
            const mockCode = '# Strategy code\nimport pandas as pd\n...';
            mockGLMClient.generateStrategy.mockResolvedValue(mockCode);
            const response = await provider.sendMessage('Create a breakout strategy');
            (0, globals_1.expect)(response).toBe(mockCode);
            (0, globals_1.expect)(mockGLMClient.generateStrategy).toHaveBeenCalledWith('Create a breakout strategy');
        });
    });
    (0, globals_1.describe)('Chat History', () => {
        (0, globals_1.it)('should maintain chat history', async () => {
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue('test-api-key'),
            });
            const provider = new chatProvider_1.ChatProvider(mockContext);
            mockGLMClient.chat.mockResolvedValue('Response 1');
            await provider.sendMessage('Message 1');
            mockGLMClient.chat.mockResolvedValue('Response 2');
            await provider.sendMessage('Message 2');
            // Verify history contains both messages
            const history = provider['chatHistory'];
            (0, globals_1.expect)(history).toHaveLength(4); // 2 user + 2 assistant messages
            (0, globals_1.expect)(history[0]).toEqual({ role: 'user', content: 'Message 1' });
            (0, globals_1.expect)(history[1]).toEqual({ role: 'assistant', content: 'Response 1' });
        });
        (0, globals_1.it)('should clear chat history', () => {
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue('test-api-key'),
            });
            const provider = new chatProvider_1.ChatProvider(mockContext);
            // Add some history
            provider['chatHistory'] = [
                { role: 'user', content: 'test' },
                { role: 'assistant', content: 'response' },
            ];
            provider.clearHistory();
            (0, globals_1.expect)(provider['chatHistory']).toHaveLength(0);
        });
    });
    (0, globals_1.describe)('Notebook Integration', () => {
        (0, globals_1.it)('should parse code into cells correctly', () => {
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue('test-api-key'),
            });
            const provider = new chatProvider_1.ChatProvider(mockContext);
            const code = `
# Introduction
This is a markdown cell

import pandas as pd
import numpy as np

# Analysis
More content
`;
            const cells = provider['parseCodeToCells'](code);
            (0, globals_1.expect)(cells).toHaveLength(3);
            (0, globals_1.expect)(cells[0].kind).toBe('markdown');
            (0, globals_1.expect)(cells[0].content).toContain('# Introduction');
            (0, globals_1.expect)(cells[1].kind).toBe('code');
            (0, globals_1.expect)(cells[1].content).toContain('import pandas');
        });
        (0, globals_1.it)('should insert strategy into notebook', async () => {
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue('test-api-key'),
            });
            const provider = new chatProvider_1.ChatProvider(mockContext);
            const mockNotebook = {
                uri: vscode.Uri.parse('file:///test.ipynb'),
                cellCount: 0,
            };
            const mockEditor = {
                notebook: mockNotebook,
            };
            vscode.window.activeNotebookEditor = mockEditor;
            const mockApplyEdit = vscode.workspace.applyEdit;
            mockApplyEdit.mockResolvedValue(true);
            const code = '# Strategy\nimport pandas as pd';
            await provider.insertStrategyIntoNotebook(code);
            (0, globals_1.expect)(vscode.workspace.applyEdit).toHaveBeenCalled();
        });
        (0, globals_1.it)('should throw error when no active notebook', async () => {
            vscode.workspace.getConfiguration.mockReturnValue({
                get: globals_1.jest.fn().mockReturnValue('test-api-key'),
            });
            const provider = new chatProvider_1.ChatProvider(mockContext);
            vscode.window.activeNotebookEditor = null;
            await (0, globals_1.expect)(provider.insertStrategyIntoNotebook('code')).rejects.toThrow('No active notebook editor');
        });
    });
});
//# sourceMappingURL=chatProvider.test.js.map