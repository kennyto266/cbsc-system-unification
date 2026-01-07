"use strict";
/**
 * Webview Chat Panel for AI Strategy Assistant
 * Provides user-friendly chat interface in VSCode sidebar
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
exports.ChatPanel = void 0;
const vscode = __importStar(require("vscode"));
class ChatPanel {
    /**
     * Create or show the chat panel
     * @param extensionUri - Extension URI
     * @param chatProvider - Chat provider instance
     */
    static createOrShow(extensionUri, chatProvider) {
        const column = vscode.window.activeTextEditor
            ? vscode.ViewColumn.Beside
            : vscode.ViewColumn.One;
        // If panel already exists, reveal it
        if (ChatPanel.currentPanel) {
            ChatPanel.currentPanel._panel.reveal(column);
            return ChatPanel.currentPanel;
        }
        // Create new panel
        const panel = vscode.window.createWebviewPanel('aiStrategyChat', 'AI Strategy Chat', column, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [extensionUri]
        });
        ChatPanel.currentPanel = new ChatPanel(panel, extensionUri, chatProvider);
        return ChatPanel.currentPanel;
    }
    /**
     * Private constructor
     */
    constructor(panel, extensionUri, chatProvider) {
        this.extensionUri = extensionUri;
        this.chatProvider = chatProvider;
        this._disposables = [];
        this._panel = panel;
        this._panel.webview.html = this._getHtmlForWebview();
        // Handle messages from webview
        this._panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'chat':
                    await this.handleChatMessage(message.text);
                    break;
                case 'clear':
                    this.handleClearHistory();
                    break;
                case 'insert':
                    await this.handleInsertToNotebook(message.code);
                    break;
            }
        }, null, this._disposables);
        // Handle panel disposal
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
    }
    /**
     * Handle chat message from user
     */
    async handleChatMessage(text) {
        try {
            // Show user message in chat
            this.postMessage({ command: 'addMessage', role: 'user', text });
            // Get AI response
            const response = await this.chatProvider.sendMessage(text);
            // Show AI response
            this.postMessage({ command: 'addMessage', role: 'assistant', text: response });
            // If response contains code, offer insert button
            if (this.containsCode(response)) {
                this.postMessage({ command: 'showInsertButton', code: response });
            }
        }
        catch (error) {
            const errorMsg = `Error: ${error instanceof Error ? error.message : String(error)}`;
            this.postMessage({ command: 'addError', text: errorMsg });
        }
    }
    /**
     * Handle clear history command
     */
    handleClearHistory() {
        this.chatProvider.clearHistory();
        this.postMessage({ command: 'clearMessages' });
    }
    /**
     * Handle insert to notebook command
     */
    async handleInsertToNotebook(code) {
        try {
            await this.chatProvider.insertStrategyIntoNotebook(code);
            this.postMessage({ command: 'showSuccess', text: 'Code inserted into notebook!' });
        }
        catch (error) {
            const errorMsg = `Failed to insert: ${error instanceof Error ? error.message : String(error)}`;
            this.postMessage({ command: 'addError', text: errorMsg });
        }
    }
    /**
     * Check if text contains code blocks
     */
    containsCode(text) {
        return text.includes('```') || text.includes('import ') || text.includes('def ');
    }
    /**
     * Post message to webview
     */
    postMessage(message) {
        this._panel.webview.postMessage(message);
    }
    /**
     * Get HTML content for webview
     */
    _getHtmlForWebview() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Strategy Chat</title>
  <style>
    :root {
      --bg-primary: var(--vscode-editor-background);
      --bg-secondary: var(--vscode-editor-inactiveSelectionBackground);
      --text-primary: var(--vscode-foreground);
      --text-secondary: var(--vscode-descriptionForeground);
      --border-color: var(--vscode-widget-border);
      --input-bg: var(--vscode-input-background);
      --button-bg: var(--vscode-button-background);
      --button-hover: var(--vscode-button-hoverBackground);
      --code-bg: var(--vscode-textCodeBlock-background);
      --user-msg-bg: var(--vscode-input-background);
      --assistant-msg-bg: var(--vscode-editor-inactiveSelectionBackground);
      --accent-color: var(--vscode-textLink-foreground);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
      font-size: var(--vscode-font-size, 13px);
      color: var(--text-primary);
      background: var(--bg-primary);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    #chat-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      max-width: 100%;
    }

    #header {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-secondary);
    }

    #header h2 {
      font-size: 14px;
      font-weight: 600;
      margin: 0;
    }

    #clear-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      padding: 4px 12px;
      border-radius: 3px;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.2s;
    }

    #clear-btn:hover {
      background: var(--button-bg);
      color: var(--text-primary);
    }

    #messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .message {
      padding: 12px;
      border-radius: 8px;
      max-width: 85%;
      line-height: 1.5;
      word-wrap: break-word;
    }

    .user-message {
      align-self: flex-end;
      background: var(--user-msg-bg);
      border: 1px solid var(--border-color);
    }

    .assistant-message {
      align-self: flex-start;
      background: var(--assistant-msg-bg);
      border-left: 3px solid var(--accent-color);
    }

    .error-message {
      align-self: center;
      background: rgba(255, 0, 0, 0.1);
      border: 1px solid rgba(255, 0, 0, 0.3);
      color: #ff6b6b;
      max-width: 100%;
    }

    .message pre {
      background: var(--code-bg);
      padding: 12px;
      border-radius: 4px;
      overflow-x: auto;
      margin: 8px 0;
      border: 1px solid var(--border-color);
    }

    .message code {
      font-family: var(--vscode-editor-font-family, 'Consolas', 'Monaco', monospace);
      font-size: 12px;
    }

    .message p {
      margin: 8px 0;
    }

    .message p:first-child {
      margin-top: 0;
    }

    .message p:last-child {
      margin-bottom: 0;
    }

    #insert-btn-container {
      margin-top: 12px;
    }

    #insert-btn {
      background: var(--button-bg);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 8px 16px;
      border-radius: 3px;
      cursor: pointer;
      font-size: 13px;
      transition: background 0.2s;
    }

    #insert-btn:hover {
      background: var(--button-hover);
    }

    #input-area {
      padding: 12px;
      border-top: 1px solid var(--border-color);
      display: flex;
      gap: 8px;
      background: var(--bg-secondary);
    }

    #user-input {
      flex: 1;
      padding: 8px 12px;
      background: var(--input-bg);
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      border-radius: 3px;
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s;
    }

    #user-input:focus {
      border-color: var(--accent-color);
    }

    #send-btn {
      background: var(--button-bg);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 8px 16px;
      border-radius: 3px;
      cursor: pointer;
      font-size: 13px;
      transition: background 0.2s;
      white-space: nowrap;
    }

    #send-btn:hover {
      background: var(--button-hover);
    }

    #send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .loading {
      opacity: 0.7;
      pointer-events: none;
    }

    /* Scrollbar styling */
    #messages::-webkit-scrollbar {
      width: 8px;
    }

    #messages::-webkit-scrollbar-track {
      background: transparent;
    }

    #messages::-webkit-scrollbar-thumb {
      background: var(--border-color);
      border-radius: 4px;
    }

    #messages::-webkit-scrollbar-thumb:hover {
      background: var(--text-secondary);
    }
  </style>
</head>
<body>
  <div id="chat-container">
    <div id="header">
      <h2>AI Strategy Assistant</h2>
      <button id="clear-btn">Clear Chat</button>
    </div>
    <div id="messages"></div>
    <div id="input-area">
      <input
        type="text"
        id="user-input"
        placeholder="Describe your trading strategy..."
        autocomplete="off"
      />
      <button id="send-btn">Send</button>
    </div>
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    const messagesDiv = document.getElementById('messages');
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const clearBtn = document.getElementById('clear-btn');

    // Add message to chat
    function addMessage(role, text, isError = false) {
      const msgDiv = document.createElement('div');
      msgDiv.className = 'message ' + (isError ? 'error-message' : role + '-message');

      // Format message content
      const formattedContent = formatMessage(text);
      msgDiv.innerHTML = formattedContent;

      messagesDiv.appendChild(msgDiv);
      scrollToBottom();

      return msgDiv;
    }

    // Format message with code blocks and line breaks
    function formatMessage(text) {
      if (!text) return '';

      // Escape HTML
      let formatted = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Format code blocks
      formatted = formatted.replace(/\`\`\`(\w*)\n([\s\S]*?)\`\`\`/g, (match, lang, code) => {
        return '<pre><code class="language-' + lang + '">' + code.trim() + '</code></pre>';
      });

      // Format inline code
      formatted = formatted.replace(/\`([^\`]+)\`/g, '<code>$1</code>');

      // Format line breaks
      formatted = formatted.replace(/\n/g, '<br>');

      return formatted;
    }

    // Scroll to bottom of messages
    function scrollToBottom() {
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    // Send message
    function sendMessage() {
      const text = input.value.trim();
      if (!text) return;

      // Disable input while processing
      input.disabled = true;
      sendBtn.disabled = true;
      sendBtn.textContent = '...';

      // Send message to extension
      vscode.postMessage({ command: 'chat', text: text });

      // Clear input
      input.value = '';
    }

    // Insert code into notebook
    function insertCode(code) {
      vscode.postMessage({ command: 'insert', code: code });
    }

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);

    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    clearBtn.addEventListener('click', () => {
      vscode.postMessage({ command: 'clear' });
    });

    // Handle messages from extension
    window.addEventListener('message', (event) => {
      const message = event.data;

      switch (message.command) {
        case 'addMessage':
          addMessage(message.role, message.text);
          break;

        case 'addError':
          addMessage('assistant', message.text, true);
          break;

        case 'clearMessages':
          messagesDiv.innerHTML = '';
          break;

        case 'showInsertButton':
          const msgDiv = messagesDiv.lastElementChild;
          if (msgDiv && !msgDiv.querySelector('#insert-btn')) {
            const container = document.createElement('div');
            container.id = 'insert-btn-container';
            container.innerHTML = '<button id="insert-btn">Insert to Notebook</button>';
            msgDiv.appendChild(container);

            container.querySelector('#insert-btn').addEventListener('click', () => {
              insertCode(message.code);
              container.remove();
            });
          }
          break;

        case 'showSuccess':
          addMessage('assistant', '✓ ' + message.text);
          break;
      }

      // Re-enable input
      input.disabled = false;
      sendBtn.disabled = false;
      sendBtn.textContent = 'Send';
      input.focus();
    });

    // Focus input on load
    input.focus();
  </script>
</body>
</html>`;
    }
    /**
     * Dispose panel resources
     */
    dispose() {
        ChatPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}
exports.ChatPanel = ChatPanel;
//# sourceMappingURL=chatPanel.js.map