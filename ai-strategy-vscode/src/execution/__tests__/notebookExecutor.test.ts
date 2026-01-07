import './setup';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import * as vscode from 'vscode';
import { NotebookExecutor, ExecutionResult, ValidationResult } from '../notebookExecutor';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

describe('NotebookExecutor', () => {
  let executor: NotebookExecutor;
  let tempNotebookPath: string;
  let tempDir: string;

  beforeEach(() => {
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

    executor = new NotebookExecutor(vscode.Uri.file(tempNotebookPath));
  });

  afterEach(() => {
    // Clean up temp directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('constructor', () => {
    it('should initialize with notebook URI', () => {
      expect(executor).toBeDefined();
    });

    it('should store notebook path', () => {
      const notebookPath = executor.getNotebookPath();
      expect(notebookPath).toBe(tempNotebookPath);
    });
  });

  describe('validateNotebook', () => {
    it('should validate a valid notebook', async () => {
      const validation: ValidationResult = await executor.validateNotebook();

      expect(validation).toBeDefined();
      expect(validation).toHaveProperty('valid');
      expect(validation).toHaveProperty('errors');
      expect(typeof validation.valid).toBe('boolean');
      expect(Array.isArray(validation.errors)).toBe(true);
    });

    it('should detect invalid notebook format', async () => {
      // Create invalid notebook
      const invalidPath = path.join(tempDir, 'invalid.ipynb');
      fs.writeFileSync(invalidPath, 'not a valid notebook');

      const invalidExecutor = new NotebookExecutor(vscode.Uri.file(invalidPath));
      const validation = await invalidExecutor.validateNotebook();

      expect(validation.valid).toBe(false);
      expect(validation.errors.length).toBeGreaterThan(0);
    });

    it('should detect wrong nbformat', async () => {
      const wrongFormatNotebook = {
        cells: [],
        metadata: {},
        nbformat: 3,  // Wrong format
        nbformat_minor: 0
      };

      const wrongFormatPath = path.join(tempDir, 'wrong_format.ipynb');
      fs.writeFileSync(wrongFormatPath, JSON.stringify(wrongFormatNotebook));

      const wrongFormatExecutor = new NotebookExecutor(vscode.Uri.file(wrongFormatPath));
      const validation = await wrongFormatExecutor.validateNotebook();

      expect(validation.valid).toBe(false);
      expect(validation.errors.some(e => e.includes('nbformat'))).toBe(true);
    });

    it('should validate syntax errors in code cells', async () => {
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

      const syntaxErrorExecutor = new NotebookExecutor(vscode.Uri.file(syntaxErrorPath));
      const validation = await syntaxErrorExecutor.validateNotebook();

      // Should detect syntax error (unbalanced parentheses)
      expect(validation.valid).toBe(false);
    });
  });

  describe('getExecutionStatus', () => {
    it('should return initial status as idle', () => {
      const status = executor.getExecutionStatus();
      expect(status).toBeDefined();
      expect(['idle', 'running', 'error', 'cancelled']).toContain(status);
    });
  });

  describe('getKernelSpec', () => {
    it('should return list of available kernels', async () => {
      const kernels = await executor.getKernelSpec();

      expect(Array.isArray(kernels)).toBe(true);
      expect(kernels.length).toBeGreaterThan(0);
    });

    it('should include python3 kernel or fallback', async () => {
      const kernels = await executor.getKernelSpec();
      expect(kernels.length).toBeGreaterThan(0);
    });
  });

  describe('cancelExecution', () => {
    it('should cancel ongoing execution', () => {
      executor.cancelExecution();
      const status = executor.getExecutionStatus();
      expect(status).toBe('cancelled');
    });
  });

  describe('updateNotebookPath', () => {
    it('should update notebook path', () => {
      const newPath = path.join(tempDir, 'new.ipynb');
      const newUri = vscode.Uri.file(newPath);

      executor.updateNotebookPath(newUri);

      expect(executor.getNotebookPath()).toBe(newPath);
    });

    it('should reset execution status after path update', () => {
      executor.cancelExecution();  // Set to cancelled
      const newPath = path.join(tempDir, 'new.ipynb');
      executor.updateNotebookPath(vscode.Uri.file(newPath));

      expect(executor.getExecutionStatus()).toBe('idle');
    });
  });

  describe('executeCell - basic functionality', () => {
    it('should execute a simple cell', async () => {
      const result: ExecutionResult = await executor.executeCell(0);

      expect(result).toBeDefined();
      expect(result).toHaveProperty('cellIndex');
      expect(result).toHaveProperty('success');
      expect(result).toHaveProperty('output');
      expect(result.cellIndex).toBe(0);
      expect(typeof result.success).toBe('boolean');
      expect(typeof result.output).toBe('string');
    });

    it('should include execution time', async () => {
      const result = await executor.executeCell(0);

      expect(result).toHaveProperty('executionTime');
      expect(typeof result.executionTime).toBe('number');
      expect(result.executionTime!).toBeGreaterThanOrEqual(0);
    });
  });

  describe('executeAll - basic functionality', () => {
    it('should execute all cells', async () => {
      const results: ExecutionResult[] = await executor.executeAll();

      expect(Array.isArray(results)).toBe(true);
      expect(results.length).toBeGreaterThan(0);

      results.forEach(result => {
        expect(result).toHaveProperty('cellIndex');
        expect(result).toHaveProperty('success');
        expect(result).toHaveProperty('output');
      });
    });
  });
});
