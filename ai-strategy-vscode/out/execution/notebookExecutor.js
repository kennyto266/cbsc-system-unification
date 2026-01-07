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
exports.NotebookExecutor = void 0;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const util_1 = require("util");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const execAsync = (0, util_1.promisify)(child_process_1.exec);
/**
 * Notebook executor for running Jupyter notebooks
 * Integrates with local Jupyter installation or remote kernels
 */
class NotebookExecutor {
    constructor(notebookUri) {
        this.kernelId = '';
        this.executionStatus = 'idle';
        this.cancellationRequested = false;
        this.notebookPath = notebookUri.fsPath;
    }
    /**
     * Execute a single cell by index
     * @param cellIndex - Index of cell to execute
     * @returns Execution result with output and status
     */
    async executeCell(cellIndex) {
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
        }
        catch (error) {
            this.executionStatus = 'error';
            return {
                cellIndex,
                success: false,
                output: '',
                error: error.message,
                executionTime: Date.now() - startTime
            };
        }
    }
    /**
     * Execute all cells in the notebook
     * @returns Array of execution results for each cell
     */
    async executeAll() {
        const results = [];
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
        }
        catch (error) {
            this.executionStatus = 'error';
            return [{
                    cellIndex: 0,
                    success: false,
                    output: '',
                    error: error.message
                }];
        }
    }
    /**
     * Cancel ongoing execution
     */
    cancelExecution() {
        this.cancellationRequested = true;
        this.executionStatus = 'cancelled';
    }
    /**
     * Get current execution status
     * @returns Current status
     */
    getExecutionStatus() {
        return this.executionStatus;
    }
    /**
     * Get available Jupyter kernels
     * @returns List of kernel specifications
     */
    async getKernelSpec() {
        try {
            const config = vscode.workspace.getConfiguration('aiStrategy');
            const jupyterPath = config.get('jupyterPath', 'jupyter');
            const { stdout } = await execAsync(`${jupyterPath} kernelspec list --json`);
            // Parse JSON output
            const specs = JSON.parse(stdout);
            return Object.keys(specs.kernelspecs || {});
        }
        catch (error) {
            // Fallback to python3 if Jupyter not available
            console.warn('Failed to get kernel specs, using fallback:', error);
            return ['python3'];
        }
    }
    /**
     * Validate notebook structure and syntax
     * @returns Validation result with errors and warnings
     */
    async validateNotebook() {
        const errors = [];
        const warnings = [];
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
        }
        catch (error) {
            return {
                valid: false,
                errors: [`Failed to read notebook: ${error.message}`],
                warnings
            };
        }
    }
    /**
     * Read notebook from file
     * @returns Parsed notebook object
     */
    readNotebook() {
        const content = fs.readFileSync(this.notebookPath, 'utf-8');
        return JSON.parse(content);
    }
    /**
     * Extract source code from cell
     * @param cell - Notebook cell
     * @returns Combined source string
     */
    extractCellSource(cell) {
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
    async executePythonCode(code) {
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
                const timeout = config.get('executionTimeout', 60000);
                // Execute Python with timeout
                const { stdout, stderr } = await execAsync(`python "${tempFile}"`, { timeout });
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
            }
            catch (execError) {
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
        }
        catch (error) {
            return {
                success: false,
                output: '',
                error: error.message
            };
        }
    }
    /**
     * Check Python syntax using basic heuristics
     * @param code - Python code to check
     * @returns List of syntax error messages
     */
    checkPythonSyntax(code) {
        const errors = [];
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
                if (char === '(')
                    parenCount++;
                if (char === ')')
                    parenCount--;
                if (char === '[')
                    bracketCount++;
                if (char === ']')
                    bracketCount--;
                if (char === '{')
                    braceCount++;
                if (char === '}')
                    braceCount--;
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
    stopOnError() {
        const config = vscode.workspace.getConfiguration('aiStrategy');
        return config.get('stopOnError', true);
    }
    /**
     * Get notebook path
     * @returns File system path to notebook
     */
    getNotebookPath() {
        return this.notebookPath;
    }
    /**
     * Update notebook path (for renamed/moved notebooks)
     * @param newUri - New notebook URI
     */
    updateNotebookPath(newUri) {
        this.notebookPath = newUri.fsPath;
        this.executionStatus = 'idle';
        this.cancellationRequested = false;
    }
}
exports.NotebookExecutor = NotebookExecutor;
//# sourceMappingURL=notebookExecutor.js.map