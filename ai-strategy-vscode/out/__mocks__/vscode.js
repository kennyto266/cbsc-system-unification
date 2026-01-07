"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NotebookCellKind = exports.NotebookCellData = exports.WorkspaceEdit = exports.NotebookRange = exports.window = exports.Uri = exports.workspace = void 0;
// Mock for vscode module
exports.workspace = {
    getConfiguration: (_) => ({
        get: (key) => {
            const defaults = {
                'aiStrategy.jupyterPath': 'jupyter',
                'aiStrategy.executionTimeout': 60000,
                'aiStrategy.stopOnError': true
            };
            return defaults[key];
        }
    })
};
exports.Uri = {
    file: (path) => ({ fsPath: path }),
    parse: (uri) => ({ fsPath: uri })
};
exports.window = {
    showErrorMessage: jest.fn(),
    activeNotebookEditor: null
};
const NotebookRange = class {
    constructor(start, end) {
        this.start = start;
        this.end = end;
    }
};
exports.NotebookRange = NotebookRange;
const WorkspaceEdit = class {
};
exports.WorkspaceEdit = WorkspaceEdit;
const NotebookCellData = class {
    constructor(kind, content) {
        this.kind = kind;
        this.content = content;
    }
};
exports.NotebookCellData = NotebookCellData;
exports.NotebookCellKind = {
    Code: 1,
    Markup: 2
};
//# sourceMappingURL=vscode.js.map