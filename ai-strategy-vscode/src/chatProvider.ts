/**
 * ChatProvider - Manages AI chat interactions and strategy generation
 * Integrates with GLM API and VSCode notebook API
 */

import * as vscode from 'vscode';
import { GLMClient } from './api/glmClient';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export class ChatProvider {
  private glmClient: GLMClient;
  private chatHistory: ChatMessage[] = [];

  constructor(private context: vscode.ExtensionContext) {
    // Get API key from VSCode settings
    const config = vscode.workspace.getConfiguration('aiStrategy');
    const apiKey = config.get<string>('glmApiKey', '');

    if (!apiKey) {
      const errorMsg = 'GLM API Key not configured. Please set aiStrategy.glmApiKey in settings.';
      vscode.window.showErrorMessage(errorMsg);
      throw new Error(errorMsg);
    }

    this.glmClient = new GLMClient(apiKey);
  }

  /**
   * Send a message to the AI and get response
   * @param message - User's message
   * @returns AI's response
   */
  async sendMessage(message: string): Promise<string> {
    // Add user message to history
    this.chatHistory.push({ role: 'user', content: message });

    let response: string;

    // Check if user wants to generate strategy
    if (this.isStrategyRequest(message)) {
      // Use strategy generation for trading-related requests
      response = await this.glmClient.generateStrategy(message);
    } else {
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
  private isStrategyRequest(message: string): boolean {
    const strategyKeywords = [
      'strategy', 'trading', 'algorithm', 'backtest',
      'buy', 'sell', 'signal', 'indicator', 'moving average',
      'breakout', 'momentum', 'mean reversion', 'bollinger',
      'rsi', 'macd', 'portfolio', 'position'
    ];

    const lowerMessage = message.toLowerCase();
    return strategyKeywords.some(keyword => lowerMessage.includes(keyword));
  }

  /**
   * Convert chat history to GLM message format
   * @param history - Chat history
   * @returns GLM message array
   */
  private convertToGLMMessages(history: ChatMessage[]): any[] {
    return history.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'assistant',
      content: msg.content
    }));
  }

  /**
   * Clear chat history
   */
  clearHistory(): void {
    this.chatHistory = [];
  }

  /**
   * Insert generated strategy code into active notebook
   * @param code - Generated strategy code
   */
  async insertStrategyIntoNotebook(code: string): Promise<void> {
    // Parse the generated code into cells
    const cells = this.parseCodeToCells(code);

    // Get current notebook editor
    const editor = vscode.window.activeNotebookEditor;
    if (!editor) {
      throw new Error('No active notebook editor. Please open a notebook first.');
    }

    const notebook = editor.notebook;

    // Create cell data objects
    const notebookCells = cells.map(cell =>
      new vscode.NotebookCellData(
        cell.kind === 'code'
          ? vscode.NotebookCellKind.Code
          : vscode.NotebookCellKind.Markup,
        cell.content,
        cell.kind === 'code' ? 'python' : 'markdown'
      )
    );

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
  private parseCodeToCells(code: string): Array<{kind: string, content: string}> {
    const cells: Array<{kind: string, content: string}> = [];

    // Split by markdown headers (#) or code blocks
    const lines = code.split('\n');
    let currentCell: string[] = [];
    let currentType: 'markdown' | 'code' = 'markdown';
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
        } else {
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
  getHistory(): ChatMessage[] {
    return [...this.chatHistory];
  }

  /**
   * Cleanup resources
   */
  async dispose(): Promise<void> {
    await this.glmClient.close();
    this.clearHistory();
  }
}
