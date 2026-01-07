import { describe, it, expect } from '@jest/globals';
import { NotebookTemplate } from '../notebookTemplate';

describe('NotebookTemplate', () => {
  it('should create a template with name and description', () => {
    const template = new NotebookTemplate('test-template', 'Test description');

    expect(template.name).toBe('test-template');
    expect(template.description).toBe('Test description');
    expect(template.cells).toEqual([]);
  });

  it('should add markdown cells correctly', () => {
    const template = new NotebookTemplate('test', 'Test');
    template.addCell('markdown', '# Test Header\n\nSome content');

    expect(template.cells).toHaveLength(1);
    expect(template.cells[0].cell_type).toBe('markdown');
    expect(template.cells[0].source).toEqual(['# Test Header', '', 'Some content']);
  });

  it('should add code cells correctly', () => {
    const template = new NotebookTemplate('test', 'Test');
    template.addCell('code', 'print("hello")\nprint("world")');

    expect(template.cells).toHaveLength(1);
    expect(template.cells[0].cell_type).toBe('code');
    expect(template.cells[0].source).toEqual(['print("hello")', 'print("world")']);
  });

  it('should generate valid Jupyter notebook format', () => {
    const template = new NotebookTemplate('test', 'Test');
    template.addCell('markdown', '# Test');
    template.addCell('code', 'x = 1');

    const notebook = template.toNotebook();

    expect(notebook.nbformat).toBe(4);
    expect(notebook.nbformat_minor).toBe(4);
    expect(notebook.cells).toHaveLength(2);
    expect(notebook.metadata.kernelspec).toBeDefined();
    expect(notebook.metadata.kernelspec.language).toBe('python');
    expect(notebook.metadata.language_info).toBeDefined();
  });

  it('should handle empty lines in cell content', () => {
    const template = new NotebookTemplate('test', 'Test');
    template.addCell('markdown', '# Header\n\nContent\n\nMore content');

    const cell = template.cells[0];
    expect(cell.source).toContain('');
    expect(cell.source).toHaveLength(5);
  });

  it('should export notebook as JSON string', () => {
    const template = new NotebookTemplate('test', 'Test');
    template.addCell('code', 'x = 1');

    const notebook = template.toNotebook();
    const jsonString = JSON.stringify(notebook);

    expect(() => JSON.parse(jsonString)).not.toThrow();
    const parsed = JSON.parse(jsonString);
    expect(parsed.cells).toHaveLength(1);
  });
});
