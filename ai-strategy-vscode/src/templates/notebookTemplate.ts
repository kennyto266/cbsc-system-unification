/**
 * NotebookTemplate - Base class for creating Jupyter notebook templates
 *
 * Provides methods to build notebook cells and export to Jupyter format
 */

export interface NotebookCell {
  cell_type: 'code' | 'markdown';
  metadata: Record<string, unknown>;
  outputs: unknown[];
  source: string[];
}

export interface NotebookMetadata {
  kernelspec: {
    display_name: string;
    language: string;
    name: string;
  };
  language_info: {
    name: string;
    version: string;
  };
}

export interface JupyterNotebook {
  cells: NotebookCell[];
  metadata: NotebookMetadata;
  nbformat: 4;
  nbformat_minor: 4;
}

export class NotebookTemplate {
  public readonly name: string;
  public readonly description: string;
  public cells: NotebookCell[] = [];

  constructor(name: string, description: string) {
    this.name = name;
    this.description = description;
  }

  /**
   * Add a cell to the template
   * @param cellType - Type of cell ('code' or 'markdown')
   * @param content - Cell content (can be multiline)
   */
  public addCell(cellType: 'code' | 'markdown', content: string): void {
    this.cells.push({
      cell_type: cellType,
      metadata: {},
      outputs: [],
      source: content.split('\n')
    });
  }

  /**
   * Convert template to Jupyter notebook format
   * @returns Complete Jupyter notebook object
   */
  public toNotebook(): JupyterNotebook {
    return {
      cells: this.cells,
      metadata: {
        kernelspec: {
          display_name: 'Python 3',
          language: 'python',
          name: 'python3'
        },
        language_info: {
          name: 'python',
          version: '3.10.0'
        }
      },
      nbformat: 4,
      nbformat_minor: 4
    };
  }

  /**
   * Export notebook as JSON string
   * @returns JSON string representation of the notebook
   */
  public toJSON(): string {
    return JSON.stringify(this.toNotebook(), null, 2);
  }

  /**
   * Get all cells in the template
   * @returns Array of notebook cells
   */
  public getCells(): NotebookCell[] {
    return [...this.cells];
  }

  /**
   * Get cell count
   * @returns Number of cells in the template
   */
  public getCellCount(): number {
    return this.cells.length;
  }
}
