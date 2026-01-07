// Mock for vscode module
export const workspace = {
  getConfiguration: (_: string) => ({
    get: (key: string) => {
      const defaults: Record<string, any> = {
        'aiStrategy.jupyterPath': 'jupyter',
        'aiStrategy.executionTimeout': 60000,
        'aiStrategy.stopOnError': true
      };
      return defaults[key];
    }
  })
};

export const Uri = {
  file: (path: string) => ({ fsPath: path }),
  parse: (uri: string) => ({ fsPath: uri })
};

export const window = {
  showErrorMessage: jest.fn(),
  activeNotebookEditor: null
};

export const NotebookRange = class {
  constructor(public start: number, public end: number) {}
};

export const WorkspaceEdit = class {};

export const NotebookCellData = class {
  constructor(
    public kind: any,
    public content: string
  ) {}
};

export const NotebookCellKind = {
  Code: 1,
  Markup: 2
};
