"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const globals_1 = require("@jest/globals");
const notebookTemplate_1 = require("../notebookTemplate");
(0, globals_1.describe)('NotebookTemplate', () => {
    (0, globals_1.it)('should create a template with name and description', () => {
        const template = new notebookTemplate_1.NotebookTemplate('test-template', 'Test description');
        (0, globals_1.expect)(template.name).toBe('test-template');
        (0, globals_1.expect)(template.description).toBe('Test description');
        (0, globals_1.expect)(template.cells).toEqual([]);
    });
    (0, globals_1.it)('should add markdown cells correctly', () => {
        const template = new notebookTemplate_1.NotebookTemplate('test', 'Test');
        template.addCell('markdown', '# Test Header\n\nSome content');
        (0, globals_1.expect)(template.cells).toHaveLength(1);
        (0, globals_1.expect)(template.cells[0].cell_type).toBe('markdown');
        (0, globals_1.expect)(template.cells[0].source).toEqual(['# Test Header', '', 'Some content']);
    });
    (0, globals_1.it)('should add code cells correctly', () => {
        const template = new notebookTemplate_1.NotebookTemplate('test', 'Test');
        template.addCell('code', 'print("hello")\nprint("world")');
        (0, globals_1.expect)(template.cells).toHaveLength(1);
        (0, globals_1.expect)(template.cells[0].cell_type).toBe('code');
        (0, globals_1.expect)(template.cells[0].source).toEqual(['print("hello")', 'print("world")']);
    });
    (0, globals_1.it)('should generate valid Jupyter notebook format', () => {
        const template = new notebookTemplate_1.NotebookTemplate('test', 'Test');
        template.addCell('markdown', '# Test');
        template.addCell('code', 'x = 1');
        const notebook = template.toNotebook();
        (0, globals_1.expect)(notebook.nbformat).toBe(4);
        (0, globals_1.expect)(notebook.nbformat_minor).toBe(4);
        (0, globals_1.expect)(notebook.cells).toHaveLength(2);
        (0, globals_1.expect)(notebook.metadata.kernelspec).toBeDefined();
        (0, globals_1.expect)(notebook.metadata.kernelspec.language).toBe('python');
        (0, globals_1.expect)(notebook.metadata.language_info).toBeDefined();
    });
    (0, globals_1.it)('should handle empty lines in cell content', () => {
        const template = new notebookTemplate_1.NotebookTemplate('test', 'Test');
        template.addCell('markdown', '# Header\n\nContent\n\nMore content');
        const cell = template.cells[0];
        (0, globals_1.expect)(cell.source).toContain('');
        (0, globals_1.expect)(cell.source).toHaveLength(5);
    });
    (0, globals_1.it)('should export notebook as JSON string', () => {
        const template = new notebookTemplate_1.NotebookTemplate('test', 'Test');
        template.addCell('code', 'x = 1');
        const notebook = template.toNotebook();
        const jsonString = JSON.stringify(notebook);
        (0, globals_1.expect)(() => JSON.parse(jsonString)).not.toThrow();
        const parsed = JSON.parse(jsonString);
        (0, globals_1.expect)(parsed.cells).toHaveLength(1);
    });
});
//# sourceMappingURL=notebookTemplate.test.js.map