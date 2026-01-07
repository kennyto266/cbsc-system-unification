"use strict";
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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
function activate(context) {
    console.log('AI Strategy Assistant is now active!');
    // Register command to create strategy notebook
    const createNotebookCmd = vscode.commands.registerCommand('aiStrategy.createNotebook', async () => {
        try {
            // Create new notebook with empty content
            const notebookData = new vscode.NotebookData([]);
            const notebook = await vscode.workspace.openNotebookDocument('jupyter-notebook', notebookData);
            await vscode.window.showNotebookDocument(notebook);
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to create notebook: ${error}`);
        }
    });
    // Register command to open AI chat
    const openChatCmd = vscode.commands.registerCommand('aiStrategy.openChat', () => {
        const panel = vscode.window.createWebviewPanel('aiChat', 'AI Strategy Chat', vscode.ViewColumn.Beside, { enableScripts: true });
        panel.webview.html = getChatWebviewContent();
    });
    context.subscriptions.push(createNotebookCmd, openChatCmd);
}
function deactivate() { }
function getChatWebviewContent() {
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: var(--vscode-font-family); padding: 20px; }
    #chat-container { display: flex; flex-direction: column; height: 100vh; }
    #messages { flex: 1; overflow-y: auto; margin-bottom: 10px; }
    #input-area { display: flex; gap: 10px; }
    input { flex: 1; padding: 8px; }
    button { padding: 8px 16px; }
  </style>
</head>
<body>
  <div id="chat-container">
    <div id="messages"></div>
    <div id="input-area">
      <input type="text" id="user-input" placeholder="Describe your strategy idea...">
      <button id="send-btn">Send</button>
    </div>
  </div>
  <script>
    const vscode = acquireVsCodeApi();
    document.getElementById('send-btn').addEventListener('click', () => {
      const input = document.getElementById('user-input');
      vscode.postMessage({ type: 'chat', message: input.value });
      input.value = '';
    });
  </script>
</body>
</html>`;
}
//# sourceMappingURL=extension.js.map