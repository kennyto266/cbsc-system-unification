// Test setup for vscode mocks
jest.mock('vscode', () => {
  return {
    workspace: {
      getConfiguration: jest.fn(() => ({
        get: jest.fn((key: string) => {
          const defaults: Record<string, any> = {
            'aiStrategy.jupyterPath': 'jupyter',
            'aiStrategy.executionTimeout': 60000,
            'aiStrategy.stopOnError': true
          };
          return defaults[key];
        })
      }))
    },
    Uri: {
      file: (path: string) => ({ fsPath: path }),
      parse: (uri: string) => ({ fsPath: uri })
    },
    window: {
      showErrorMessage: jest.fn(),
      activeNotebookEditor: null
    },
    NotebookRange: class {
      constructor(public start: number, public end: number) {}
    },
    WorkspaceEdit: class {},
    NotebookCellData: class {
      constructor(
        public kind: any,
        public content: string
      ) {}
    },
    NotebookCellKind: {
      Code: 1,
      Markup: 2
    }
  };
});
