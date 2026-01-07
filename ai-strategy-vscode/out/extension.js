"use strict";
/**
 * AI Strategy Assistant - VSCode Extension
 * Main entry point for the extension
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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const chatProvider_1 = require("./chatProvider");
const chatPanel_1 = require("./webview/chatPanel");
let chatProvider;
function activate(context) {
    console.log('AI Strategy Assistant is now active!');
    // Initialize chat provider
    try {
        chatProvider = new chatProvider_1.ChatProvider(context);
    }
    catch (error) {
        const errorMsg = `Failed to initialize AI Strategy Assistant: ${error}`;
        vscode.window.showErrorMessage(errorMsg);
        console.error(errorMsg, error);
        return;
    }
    // Register command to create strategy notebook
    const createNotebookCmd = vscode.commands.registerCommand('aiStrategy.createNotebook', async () => {
        try {
            // Create new notebook with empty content
            const notebookData = new vscode.NotebookData([]);
            const notebook = await vscode.workspace.openNotebookDocument('jupyter-notebook', notebookData);
            await vscode.window.showNotebookDocument(notebook);
            vscode.window.showInformationMessage('Notebook created! Open AI Chat to generate strategies.');
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to create notebook: ${error}`);
        }
    });
    // Register command to open AI chat
    const openChatCmd = vscode.commands.registerCommand('aiStrategy.openChat', () => {
        if (!chatProvider) {
            vscode.window.showErrorMessage('Chat provider not initialized');
            return;
        }
        chatPanel_1.ChatPanel.createOrShow(context.extensionUri, chatProvider);
    });
    // Register command to insert strategy into notebook
    const insertStrategyCmd = vscode.commands.registerCommand('aiStrategy.insertIntoNotebook', async () => {
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
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Generating strategy...',
                    cancellable: false
                }, async () => {
                    const strategyCode = await chatProvider.sendMessage(input);
                    await chatProvider.insertStrategyIntoNotebook(strategyCode);
                });
                vscode.window.showInformationMessage('Strategy inserted into notebook!');
            }
            catch (error) {
                vscode.window.showErrorMessage(`Failed to insert strategy: ${error}`);
            }
        }
    });
    // Register command to show API key configuration
    const configApiKeyCmd = vscode.commands.registerCommand('aiStrategy.configureApiKey', async () => {
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
    });
    // Add all disposables to context
    context.subscriptions.push(createNotebookCmd, openChatCmd, insertStrategyCmd, configApiKeyCmd);
}
function deactivate() {
    // Cleanup chat provider
    if (chatProvider) {
        chatProvider.dispose();
        chatProvider = undefined;
    }
}
//# sourceMappingURL=extension.js.map