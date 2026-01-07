import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';

const execAsync = promisify(exec);

/**
 * Result of notebook cell execution
 */
export interface ExecutionResult {
  cellIndex: number;
  success: boolean;
  output: string;
  error?: string;
  executionTime?: number;
}

/**
 * Notebook validation result
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Execution status
 */
export type ExecutionStatus = 'idle' | 'running' | 'error' | 'cancelled';

/**
 * Notebook executor for running Jupyter notebooks
 * Integrates with local Jupyter installation or remote kernels
 */
export class NotebookExecutor {
  private notebookPath: string;
  private kernelId: string = '';
  private executionStatus: ExecutionStatus = 'idle';
  private cancellationRequested: boolean = false;

  constructor(notebookUri: vscode.Uri) {
    this.notebookPath = notebookUri.fsPath;
  }

  /**
   * Execute a single cell by index
   * @param cellIndex - Index of cell to execute
   * @returns Execution result with output and status
   */
  async executeCell(cellIndex: number): Promise<ExecutionResult> {
    const startTime = Date.now();

    try {
      this.executionStatus = 'running';

      // Read notebook to get cell content
      const notebook = this.readNotebook();
      if (!notebook.cells || cellIndex >= notebook.cells.length) {
        throw new Error(`Cell index ${cellIndex} out of bounds`);
      }

      const cell = notebook.cells[cellIndex];
      if (cell.cell_type !== 'code') {
        return {
          cellIndex,
          success: true,
          output: '',
          executionTime: Date.now() - startTime
        };
      }

      const code = this.extractCellSource(cell);

      // Execute code using Python
      const result = await this.executePythonCode(code);

      this.executionStatus = 'idle';

      return {
        cellIndex,
        success: result.success,
        output: result.output,
        error: result.error,
        executionTime: Date.now() - startTime
      };

    } catch (error) {
      this.executionStatus = 'error';
      return {
        cellIndex,
        success: false,
        output: '',
        error: (error as Error).message,
        executionTime: Date.now() - startTime
      };
    }
  }

  /**
   * Execute all cells in the notebook
   * @returns Array of execution results for each cell
   */
  async executeAll(): Promise<ExecutionResult[]> {
    const results: ExecutionResult[] = [];

    try {
      this.executionStatus = 'running';
      this.cancellationRequested = false;

      // Read notebook
      const notebook = this.readNotebook();

      // Execute each code cell
      for (let i = 0; i < notebook.cells.length; i++) {
        if (this.cancellationRequested) {
          this.executionStatus = 'cancelled';
          break;
        }

        const cell = notebook.cells[i];
        if (cell.cell_type === 'code') {
          const result = await this.executeCell(i);
          results.push(result);

          // Stop on error if configured
          if (!result.success && this.stopOnError()) {
            break;
          }
        }
      }

      if (!this.cancellationRequested) {
        this.executionStatus = 'idle';
      }

      return results;

    } catch (error) {
      this.executionStatus = 'error';
      return [{
        cellIndex: 0,
        success: false,
        output: '',
        error: (error as Error).message
      }];
    }
  }

  /**
   * Cancel ongoing execution
   */
  cancelExecution(): void {
    this.cancellationRequested = true;
    this.executionStatus = 'cancelled';
  }

  /**
   * Get current execution status
   * @returns Current status
   */
  getExecutionStatus(): ExecutionStatus {
    return this.executionStatus;
  }

  /**
   * Get available Jupyter kernels
   * @returns List of kernel specifications
   */
  async getKernelSpec(): Promise<string[]> {
    try {
      const config = vscode.workspace.getConfiguration('aiStrategy');
      const jupyterPath = config.get<string>('jupyterPath', 'jupyter');

      const { stdout } = await execAsync(`${jupyterPath} kernelspec list --json`);

      // Parse JSON output
      const specs = JSON.parse(stdout);
      return Object.keys(specs.kernelspecs || {});

    } catch (error) {
      // Fallback to python3 if Jupyter not available
      console.warn('Failed to get kernel specs, using fallback:', error);
      return ['python3'];
    }
  }

  /**
   * Validate notebook structure and syntax
   * @returns Validation result with errors and warnings
   */
  async validateNotebook(): Promise<ValidationResult> {
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      const notebook = this.readNotebook();

      // Check nbformat version
      if (notebook.nbformat !== 4) {
        errors.push(`Invalid nbformat: ${notebook.nbformat} (expected 4)`);
      }

      // Check cells structure
      if (!notebook.cells || !Array.isArray(notebook.cells)) {
        errors.push('Invalid notebook structure: missing or invalid cells array');
        return { valid: false, errors, warnings };
      }

      // Validate each code cell
      for (let i = 0; i < notebook.cells.length; i++) {
        const cell = notebook.cells[i];

        if (!cell.cell_type) {
          errors.push(`Cell ${i}: missing cell_type`);
          continue;
        }

        if (cell.cell_type === 'code') {
          const source = this.extractCellSource(cell);

          if (!source.trim()) {
            warnings.push(`Cell ${i}: empty code cell`);
            continue;
          }

          // Basic syntax check using simple heuristics
          // Node.js doesn't have Python's compile(), so we do basic checks
          const syntaxErrors = this.checkPythonSyntax(source);
          if (syntaxErrors.length > 0) {
            errors.push(`Cell ${i}: ${syntaxErrors.join(', ')}`);
          }
        }
      }

      return {
        valid: errors.length === 0,
        errors,
        warnings
      };

    } catch (error) {
      return {
        valid: false,
        errors: [`Failed to read notebook: ${(error as Error).message}`],
        warnings
      };
    }
  }

  /**
   * Read notebook from file
   * @returns Parsed notebook object
   */
  private readNotebook(): any {
    const content = fs.readFileSync(this.notebookPath, 'utf-8');
    return JSON.parse(content);
  }

  /**
   * Extract source code from cell
   * @param cell - Notebook cell
   * @returns Combined source string
   */
  private extractCellSource(cell: any): string {
    if (typeof cell.source === 'string') {
      return cell.source;
    }
    if (Array.isArray(cell.source)) {
      return cell.source.join('');
    }
    return '';
  }

  /**
   * Execute Python code using subprocess
   * @param code - Python code to execute
   * @returns Execution result
   */
  private async executePythonCode(code: string): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    try {
      // Create temp file for code
      const tempDir = path.join(path.dirname(this.notebookPath), '.tmp');
      if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
      }

      const tempFile = path.join(tempDir, `code_${Date.now()}.py`);
      fs.writeFileSync(tempFile, code);

      try {
        const config = vscode.workspace.getConfiguration('aiStrategy');
        const timeout = config.get<number>('executionTimeout', 60000);

        // Execute Python with timeout
        const { stdout, stderr } = await execAsync(
          `python "${tempFile}"`,
          { timeout }
        );

        // Clean up temp file
        fs.unlinkSync(tempFile);

        if (stderr && stderr.trim()) {
          return {
            success: false,
            output: stdout,
            error: stderr
          };
        }

        return {
          success: true,
          output: stdout
        };

      } catch (execError: any) {
        // Clean up temp file on error
        if (fs.existsSync(tempFile)) {
          fs.unlinkSync(tempFile);
        }

        // Check if it's a timeout
        if (execError.killed && execError.signal === 'SIGTERM') {
          return {
            success: false,
            output: '',
            error: 'Execution timeout'
          };
        }

        return {
          success: false,
          output: execError.stdout || '',
          error: execError.stderr || execError.message
        };
      }

    } catch (error) {
      return {
        success: false,
        output: '',
        error: (error as Error).message
      };
    }
  }

  /**
   * Check Python syntax using basic heuristics
   * @param code - Python code to check
   * @returns List of syntax error messages
   */
  private checkPythonSyntax(code: string): string[] {
    const errors: string[] = [];

    // Check for common syntax issues
    const lines = code.split('\n');

    let parenCount = 0;
    let bracketCount = 0;
    let braceCount = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineNum = i + 1;

      // Count brackets
      for (const char of line) {
        if (char === '(') parenCount++;
        if (char === ')') parenCount--;
        if (char === '[') bracketCount++;
        if (char === ']') bracketCount--;
        if (char === '{') braceCount++;
        if (char === '}') braceCount--;
      }

      // Check for common syntax errors
      if (line.trim().startsWith('def ') || line.trim().startsWith('class ')) {
        if (!line.includes(':')) {
          errors.push(`Line ${lineNum}: missing colon`);
        }
      }

      if (line.trim().startsWith('if ') || line.trim().startsWith('for ') ||
          line.trim().startsWith('while ') || line.trim().startsWith('with ')) {
        if (!line.includes(':')) {
          errors.push(`Line ${lineNum}: missing colon`);
        }
      }

      // Check for invalid characters
      if (/[^\x00-\x7F]/.test(line) && !line.includes('#')) {
        // Non-ASCII but not a comment (might be encoding issue)
        // Don't error on this as Python 3 supports UTF-8
      }
    }

    // Check for unbalanced brackets
    if (parenCount !== 0) {
      errors.push('Unbalanced parentheses');
    }
    if (bracketCount !== 0) {
      errors.push('Unbalanced brackets');
    }
    if (braceCount !== 0) {
      errors.push('Unbalanced braces');
    }

    return errors;
  }

  /**
   * Check if should stop on error
   * @returns True if should stop on first error
   */
  private stopOnError(): boolean {
    const config = vscode.workspace.getConfiguration('aiStrategy');
    return config.get<boolean>('stopOnError', true);
  }

  /**
   * Get notebook path
   * @returns File system path to notebook
   */
  getNotebookPath(): string {
    return this.notebookPath;
  }

  /**
   * Update notebook path (for renamed/moved notebooks)
   * @param newUri - New notebook URI
   */
  updateNotebookPath(newUri: vscode.Uri): void {
    this.notebookPath = newUri.fsPath;
    this.executionStatus = 'idle';
    this.cancellationRequested = false;
  }
}
