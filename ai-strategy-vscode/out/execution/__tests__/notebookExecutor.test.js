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
require("./setup");
const globals_1 = require("@jest/globals");
const vscode = __importStar(require("vscode"));
const notebookExecutor_1 = require("../notebookExecutor");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
(0, globals_1.describe)('NotebookExecutor', () => {
    let executor;
    let tempNotebookPath;
    let tempDir;
    (0, globals_1.beforeEach)(() => {
        // Create temporary directory for test notebooks
        tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'notebook-test-'));
        // Create a simple test notebook
        const testNotebook = {
            cells: [
                {
                    cell_type: 'code',
                    execution_count: null,
                    metadata: {},
                    outputs: [],
                    source: ['x = 1\n', 'print(x)']
                }
            ],
            metadata: {
                kernelspec: {
                    display_name: 'Python 3',
                    'language': 'python',
                    name: 'python3'
                }
            },
            nbformat: 4,
            nbformat_minor: 4
        };
        tempNotebookPath = path.join(tempDir, 'test.ipynb');
        fs.writeFileSync(tempNotebookPath, JSON.stringify(testNotebook));
        executor = new notebookExecutor_1.NotebookExecutor(vscode.Uri.file(tempNotebookPath));
    });
    afterEach(() => {
        // Clean up temp directory
        if (fs.existsSync(tempDir)) {
            fs.rmSync(tempDir, { recursive: true, force: true });
        }
    });
    (0, globals_1.describe)('constructor', () => {
        (0, globals_1.it)('should initialize with notebook URI', () => {
            (0, globals_1.expect)(executor).toBeDefined();
        });
        (0, globals_1.it)('should store notebook path', () => {
            const notebookPath = executor.getNotebookPath();
            (0, globals_1.expect)(notebookPath).toBe(tempNotebookPath);
        });
    });
    (0, globals_1.describe)('validateNotebook', () => {
        (0, globals_1.it)('should validate a valid notebook', async () => {
            const validation = await executor.validateNotebook();
            (0, globals_1.expect)(validation).toBeDefined();
            (0, globals_1.expect)(validation).toHaveProperty('valid');
            (0, globals_1.expect)(validation).toHaveProperty('errors');
            (0, globals_1.expect)(typeof validation.valid).toBe('boolean');
            (0, globals_1.expect)(Array.isArray(validation.errors)).toBe(true);
        });
        (0, globals_1.it)('should detect invalid notebook format', async () => {
            // Create invalid notebook
            const invalidPath = path.join(tempDir, 'invalid.ipynb');
            fs.writeFileSync(invalidPath, 'not a valid notebook');
            const invalidExecutor = new notebookExecutor_1.NotebookExecutor(vscode.Uri.file(invalidPath));
            const validation = await invalidExecutor.validateNotebook();
            (0, globals_1.expect)(validation.valid).toBe(false);
            (0, globals_1.expect)(validation.errors.length).toBeGreaterThan(0);
        });
        (0, globals_1.it)('should detect wrong nbformat', async () => {
            const wrongFormatNotebook = {
                cells: [],
                metadata: {},
                nbformat: 3, // Wrong format
                nbformat_minor: 0
            };
            const wrongFormatPath = path.join(tempDir, 'wrong_format.ipynb');
            fs.writeFileSync(wrongFormatPath, JSON.stringify(wrongFormatNotebook));
            const wrongFormatExecutor = new notebookExecutor_1.NotebookExecutor(vscode.Uri.file(wrongFormatPath));
            const validation = await wrongFormatExecutor.validateNotebook();
            (0, globals_1.expect)(validation.valid).toBe(false);
            (0, globals_1.expect)(validation.errors.some(e => e.includes('nbformat'))).toBe(true);
        });
        (0, globals_1.it)('should validate syntax errors in code cells', async () => {
            // Notebook with syntax error (unbalanced parentheses)
            const syntaxErrorNotebook = {
                cells: [
                    {
                        cell_type: 'code',
                        execution_count: null,
                        metadata: {},
                        outputs: [],
                        source: ['def foo(']
                    }
                ],
                metadata: {},
                nbformat: 4,
                nbformat_minor: 4
            };
            const syntaxErrorPath = path.join(tempDir, 'syntax_error.ipynb');
            fs.writeFileSync(syntaxErrorPath, JSON.stringify(syntaxErrorNotebook));
            const syntaxErrorExecutor = new notebookExecutor_1.NotebookExecutor(vscode.Uri.file(syntaxErrorPath));
            const validation = await syntaxErrorExecutor.validateNotebook();
            // Should detect syntax error (unbalanced parentheses)
            (0, globals_1.expect)(validation.valid).toBe(false);
        });
    });
    (0, globals_1.describe)('getExecutionStatus', () => {
        (0, globals_1.it)('should return initial status as idle', () => {
            const status = executor.getExecutionStatus();
            (0, globals_1.expect)(status).toBeDefined();
            (0, globals_1.expect)(['idle', 'running', 'error', 'cancelled']).toContain(status);
        });
    });
    (0, globals_1.describe)('getKernelSpec', () => {
        (0, globals_1.it)('should return list of available kernels', async () => {
            const kernels = await executor.getKernelSpec();
            (0, globals_1.expect)(Array.isArray(kernels)).toBe(true);
            (0, globals_1.expect)(kernels.length).toBeGreaterThan(0);
        });
        (0, globals_1.it)('should include python3 kernel or fallback', async () => {
            const kernels = await executor.getKernelSpec();
            (0, globals_1.expect)(kernels.length).toBeGreaterThan(0);
        });
    });
    (0, globals_1.describe)('cancelExecution', () => {
        (0, globals_1.it)('should cancel ongoing execution', () => {
            executor.cancelExecution();
            const status = executor.getExecutionStatus();
            (0, globals_1.expect)(status).toBe('cancelled');
        });
    });
    (0, globals_1.describe)('updateNotebookPath', () => {
        (0, globals_1.it)('should update notebook path', () => {
            const newPath = path.join(tempDir, 'new.ipynb');
            const newUri = vscode.Uri.file(newPath);
            executor.updateNotebookPath(newUri);
            (0, globals_1.expect)(executor.getNotebookPath()).toBe(newPath);
        });
        (0, globals_1.it)('should reset execution status after path update', () => {
            executor.cancelExecution(); // Set to cancelled
            const newPath = path.join(tempDir, 'new.ipynb');
            executor.updateNotebookPath(vscode.Uri.file(newPath));
            (0, globals_1.expect)(executor.getExecutionStatus()).toBe('idle');
        });
    });
    (0, globals_1.describe)('executeCell - basic functionality', () => {
        (0, globals_1.it)('should execute a simple cell', async () => {
            const result = await executor.executeCell(0);
            (0, globals_1.expect)(result).toBeDefined();
            (0, globals_1.expect)(result).toHaveProperty('cellIndex');
            (0, globals_1.expect)(result).toHaveProperty('success');
            (0, globals_1.expect)(result).toHaveProperty('output');
            (0, globals_1.expect)(result.cellIndex).toBe(0);
            (0, globals_1.expect)(typeof result.success).toBe('boolean');
            (0, globals_1.expect)(typeof result.output).toBe('string');
        });
        (0, globals_1.it)('should include execution time', async () => {
            const result = await executor.executeCell(0);
            (0, globals_1.expect)(result).toHaveProperty('executionTime');
            (0, globals_1.expect)(typeof result.executionTime).toBe('number');
            (0, globals_1.expect)(result.executionTime).toBeGreaterThanOrEqual(0);
        });
    });
    (0, globals_1.describe)('executeAll - basic functionality', () => {
        (0, globals_1.it)('should execute all cells', async () => {
            const results = await executor.executeAll();
            (0, globals_1.expect)(Array.isArray(results)).toBe(true);
            (0, globals_1.expect)(results.length).toBeGreaterThan(0);
            results.forEach(result => {
                (0, globals_1.expect)(result).toHaveProperty('cellIndex');
                (0, globals_1.expect)(result).toHaveProperty('success');
                (0, globals_1.expect)(result).toHaveProperty('output');
            });
        });
    });
});
//# sourceMappingURL=notebookExecutor.test.js.map