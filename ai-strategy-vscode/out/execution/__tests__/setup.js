"use strict";
// Test setup for vscode mocks
jest.mock('vscode', () => {
    return {
        workspace: {
            getConfiguration: jest.fn(() => ({
                get: jest.fn((key) => {
                    const defaults = {
                        'aiStrategy.jupyterPath': 'jupyter',
                        'aiStrategy.executionTimeout': 60000,
                        'aiStrategy.stopOnError': true
                    };
                    return defaults[key];
                })
            }))
        },
        Uri: {
            file: (path) => ({ fsPath: path }),
            parse: (uri) => ({ fsPath: uri })
        },
        window: {
            showErrorMessage: jest.fn(),
            activeNotebookEditor: null
        },
        NotebookRange: class {
            constructor(start, end) {
                this.start = start;
                this.end = end;
            }
        },
        WorkspaceEdit: class {
        },
        NotebookCellData: class {
            constructor(kind, content) {
                this.kind = kind;
                this.content = content;
            }
        },
        NotebookCellKind: {
            Code: 1,
            Markup: 2
        }
    };
});
//# sourceMappingURL=setup.js.map