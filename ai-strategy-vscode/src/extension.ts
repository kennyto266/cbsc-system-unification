import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  console.log('AI Strategy Assistant is now active!');

  // Register command to create strategy notebook
  const createNotebookCmd = vscode.commands.registerCommand(
    'aiStrategy.createNotebook',
    async () => {
      const notebook = await vscode.workspace.openNotebookDocument(
        vscode.Uri.parse('untitled:/strategy.ipynb')
      );
      await vscode.window.showNotebookDocument(notebook);
    }
  );

  // Register command to open AI chat
  const openChatCmd = vscode.commands.registerCommand(
    'aiStrategy.openChat',
    () => {
      const panel = vscode.window.createWebviewPanel(
        'aiChat',
        'AI Strategy Chat',
        vscode.ViewColumn.Beside,
        { enableScripts: true }
      );
      panel.webview.html = getChatWebviewContent();
    }
  );

  context.subscriptions.push(createNotebookCmd, openChatCmd);
}

export function deactivate() {}

function getChatWebviewContent(): string {
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
