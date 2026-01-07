/**
 * Tests for ChatProvider class
 * Following TDD approach: write failing tests first
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import * as vscode from 'vscode';
import { ChatProvider } from '../chatProvider';

// Mock vscode module
jest.mock('vscode', () => ({
  window: {
    showErrorMessage: jest.fn(),
    activeNotebookEditor: null,
    showNotebookDocument: jest.fn(),
  },
  workspace: {
    getConfiguration: jest.fn(),
    openNotebookDocument: jest.fn(),
    applyEdit: jest.fn(),
  },
  WorkspaceEdit: jest.fn(),
  Uri: {},
  NotebookRange: jest.fn(),
  NotebookCellData: jest.fn(),
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

describe('ChatProvider', () => {
  let mockContext: vscode.ExtensionContext;
  let mockGLMClient: any;

  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();

    mockContext = {
      subscriptions: [],
      globalState: {
        get: jest.fn(),
        update: jest.fn(),
      },
      workspaceState: {
        get: jest.fn(),
        update: jest.fn(),
      },
    } as any;

    // Mock GLM client
    mockGLMClient = {
      chat: jest.fn(),
      generateStrategy: jest.fn(),
    };
  });

  describe('Initialization', () => {
    it('should throw error when API key is not configured', () => {
      // Mock configuration without API key
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue(''),
      });

      expect(() => {
        new ChatProvider(mockContext);
      }).toThrow('GLM API Key not configured');
    });

    it('should initialize with valid API key', () => {
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue('test-api-key-12345'),
      });

      const provider = new ChatProvider(mockContext);
      expect(provider).toBeDefined();
    });
  });

  describe('Message Handling', () => {
    it('should detect strategy request keywords', () => {
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue('test-api-key'),
      });

      const provider = new ChatProvider(mockContext);

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
        expect(provider['isStrategyRequest'](request)).toBe(true);
      });
    });

    it('should handle non-strategy chat messages', async () => {
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue('test-api-key'),
      });

      const provider = new ChatProvider(mockContext);

      // Mock regular chat response
      mockGLMClient.chat.mockResolvedValue('I can help with that!');

      const response = await provider.sendMessage('Hello, how are you?');

      expect(response).toBe('I can help with that!');
      expect(mockGLMClient.chat).toHaveBeenCalled();
    });

    it('should handle strategy generation requests', async () => {
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue('test-api-key'),
      });

      const provider = new ChatProvider(mockContext);

      // Mock strategy generation
      const mockCode = '# Strategy code\nimport pandas as pd\n...';
      mockGLMClient.generateStrategy.mockResolvedValue(mockCode);

      const response = await provider.sendMessage('Create a breakout strategy');

      expect(response).toBe(mockCode);
      expect(mockGLMClient.generateStrategy).toHaveBeenCalledWith('Create a breakout strategy');
    });
  });

  describe('Chat History', () => {
    it('should maintain chat history', async () => {
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue('test-api-key'),
      });

      const provider = new ChatProvider(mockContext);
      mockGLMClient.chat.mockResolvedValue('Response 1');

      await provider.sendMessage('Message 1');
      mockGLMClient.chat.mockResolvedValue('Response 2');
      await provider.sendMessage('Message 2');

      // Verify history contains both messages
      const history = provider['chatHistory'];
      expect(history).toHaveLength(4); // 2 user + 2 assistant messages
      expect(history[0]).toEqual({ role: 'user', content: 'Message 1' });
      expect(history[1]).toEqual({ role: 'assistant', content: 'Response 1' });
    });

    it('should clear chat history', () => {
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue('test-api-key'),
      });

      const provider = new ChatProvider(mockContext);

      // Add some history
      provider['chatHistory'] = [
        { role: 'user', content: 'test' },
        { role: 'assistant', content: 'response' },
      ];

      provider.clearHistory();

      expect(provider['chatHistory']).toHaveLength(0);
    });
  });

  describe('Notebook Integration', () => {
    it('should parse code into cells correctly', () => {
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue('test-api-key'),
      });

      const provider = new ChatProvider(mockContext);

      const code = `
# Introduction
This is a markdown cell

import pandas as pd
import numpy as np

# Analysis
More content
`;

      const cells = provider['parseCodeToCells'](code);

      expect(cells).toHaveLength(3);
      expect(cells[0].kind).toBe('markdown');
      expect(cells[0].content).toContain('# Introduction');
      expect(cells[1].kind).toBe('code');
      expect(cells[1].content).toContain('import pandas');
    });

    it('should insert strategy into notebook', async () => {
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue('test-api-key'),
      });

      const provider = new ChatProvider(mockContext);

      const mockNotebook = {
        uri: vscode.Uri.parse('file:///test.ipynb'),
        cellCount: 0,
      };

      const mockEditor = {
        notebook: mockNotebook,
      };

      (vscode.window.activeNotebookEditor as any) = mockEditor;
      const mockApplyEdit = vscode.workspace.applyEdit as jest.MockedFunction<typeof vscode.workspace.applyEdit>;
      mockApplyEdit.mockResolvedValue(true);

      const code = '# Strategy\nimport pandas as pd';
      await provider.insertStrategyIntoNotebook(code);

      expect(vscode.workspace.applyEdit).toHaveBeenCalled();
    });

    it('should throw error when no active notebook', async () => {
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn().mockReturnValue('test-api-key'),
      });

      const provider = new ChatProvider(mockContext);

      (vscode.window.activeNotebookEditor as any) = null;

      await expect(
        provider.insertStrategyIntoNotebook('code')
      ).rejects.toThrow('No active notebook editor');
    });
  });
});
