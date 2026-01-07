/**
 * AI Strategy Assistant - VSCode Extension
 * Main entry point for the extension
 */

import * as vscode from 'vscode';
import { ChatProvider } from './chatProvider';
import { ChatPanel } from './webview/chatPanel';

let chatProvider: ChatProvider | undefined;

export function activate(context: vscode.ExtensionContext) {
  console.log('AI Strategy Assistant is now active!');

  // Initialize chat provider
  try {
    chatProvider = new ChatProvider(context);
  } catch (error) {
    const errorMsg = `Failed to initialize AI Strategy Assistant: ${error}`;
    vscode.window.showErrorMessage(errorMsg);
    console.error(errorMsg, error);
    return;
  }

  // Register command to create strategy notebook
  const createNotebookCmd = vscode.commands.registerCommand(
    'aiStrategy.createNotebook',
    async () => {
      try {
        // Create new notebook with empty content
        const notebookData = new vscode.NotebookData([]);
        const notebook = await vscode.workspace.openNotebookDocument(
          'jupyter-notebook',
          notebookData
        );
        await vscode.window.showNotebookDocument(notebook);

        vscode.window.showInformationMessage('Notebook created! Open AI Chat to generate strategies.');
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to create notebook: ${error}`);
      }
    }
  );

  // Register command to open AI chat
  const openChatCmd = vscode.commands.registerCommand(
    'aiStrategy.openChat',
    () => {
      if (!chatProvider) {
        vscode.window.showErrorMessage('Chat provider not initialized');
        return;
      }
      ChatPanel.createOrShow(context.extensionUri, chatProvider);
    }
  );

  // Register command to insert strategy into notebook
  const insertStrategyCmd = vscode.commands.registerCommand(
    'aiStrategy.insertIntoNotebook',
    async () => {
      if (!chatProvider) {
        vscode.window.showErrorMessage('Chat provider not initialized');
        return;
      }

      const input = await vscode.window.showInputBox({
        prompt: 'Describe your strategy idea',
        placeHolder: 'e.g., 20-day moving average breakout strategy',
        ignoreFocusOut: true
      });

      if (input) {
        try {
          await vscode.window.withProgress(
            {
              location: vscode.ProgressLocation.Notification,
              title: 'Generating strategy...',
              cancellable: false
            },
            async () => {
              const strategyCode = await chatProvider!.sendMessage(input);
              await chatProvider!.insertStrategyIntoNotebook(strategyCode);
            }
          );

          vscode.window.showInformationMessage('Strategy inserted into notebook!');
        } catch (error) {
          vscode.window.showErrorMessage(`Failed to insert strategy: ${error}`);
        }
      }
    }
  );

  // Register command to show API key configuration
  const configApiKeyCmd = vscode.commands.registerCommand(
    'aiStrategy.configureApiKey',
    async () => {
      const apiKey = await vscode.window.showInputBox({
        prompt: 'Enter your GLM API Key',
        password: true,
        ignoreFocusOut: true
      });

      if (apiKey) {
        const config = vscode.workspace.getConfiguration('aiStrategy');
        await config.update('glmApiKey', apiKey, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage('API Key saved successfully!');
      }
    }
  );

  // Add all disposables to context
  context.subscriptions.push(
    createNotebookCmd,
    openChatCmd,
    insertStrategyCmd,
    configApiKeyCmd
  );
}

export function deactivate() {
  // Cleanup chat provider
  if (chatProvider) {
    chatProvider.dispose();
    chatProvider = undefined;
  }
}
