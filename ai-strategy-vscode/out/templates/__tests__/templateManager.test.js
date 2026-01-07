"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const globals_1 = require("@jest/globals");
const templateManager_1 = require("../templateManager");
(0, globals_1.describe)('TemplateManager', () => {
    (0, globals_1.it)('should initialize with built-in templates', () => {
        const manager = new templateManager_1.TemplateManager();
        const templates = manager.listTemplates();
        (0, globals_1.expect)(templates.length).toBeGreaterThanOrEqual(2);
        (0, globals_1.expect)(templates.some(t => t.name === 'breakout')).toBe(true);
        (0, globals_1.expect)(templates.some(t => t.name === 'mean_reversion')).toBe(true);
    });
    (0, globals_1.it)('should retrieve breakout template', () => {
        const manager = new templateManager_1.TemplateManager();
        const template = manager.getTemplate('breakout');
        (0, globals_1.expect)(template).toBeDefined();
        (0, globals_1.expect)(template?.name).toBe('breakout');
        (0, globals_1.expect)(template?.description).toContain('breakout');
    });
    (0, globals_1.it)('should retrieve mean reversion template', () => {
        const manager = new templateManager_1.TemplateManager();
        const template = manager.getTemplate('mean_reversion');
        (0, globals_1.expect)(template).toBeDefined();
        (0, globals_1.expect)(template?.name).toBe('mean_reversion');
        (0, globals_1.expect)(template?.description.toLowerCase()).toContain('mean reversion');
    });
    (0, globals_1.it)('should return undefined for non-existent template', () => {
        const manager = new templateManager_1.TemplateManager();
        const template = manager.getTemplate('non-existent');
        (0, globals_1.expect)(template).toBeUndefined();
    });
    (0, globals_1.it)('breakout template should have required cells', () => {
        const manager = new templateManager_1.TemplateManager();
        const template = manager.getTemplate('breakout');
        (0, globals_1.expect)(template).toBeDefined();
        (0, globals_1.expect)(template.cells.length).toBeGreaterThanOrEqual(6);
        const cellSources = template.cells.map(cell => Array.isArray(cell.source) ? cell.source.join(' ') : cell.source);
        // Check for key components
        (0, globals_1.expect)(cellSources.some(s => s.includes('fetch_data') || s.includes('fetch'))).toBe(true);
        (0, globals_1.expect)(cellSources.some(s => s.includes('portfolio') || s.includes('backtest'))).toBe(true);
        (0, globals_1.expect)(cellSources.some(s => s.includes('matplotlib') || s.includes('plot'))).toBe(true);
    });
    (0, globals_1.it)('mean reversion template should have required cells', () => {
        const manager = new templateManager_1.TemplateManager();
        const template = manager.getTemplate('mean_reversion');
        (0, globals_1.expect)(template).toBeDefined();
        (0, globals_1.expect)(template.cells.length).toBeGreaterThanOrEqual(4);
        const cellSources = template.cells.map(cell => Array.isArray(cell.source) ? cell.source.join(' ') : cell.source);
        // Check for key components
        (0, globals_1.expect)(cellSources.some(s => s.includes('Bollinger') || s.includes('bollinger'))).toBe(true);
        (0, globals_1.expect)(cellSources.some(s => s.includes('z_score') || s.includes('z-score'))).toBe(true);
        (0, globals_1.expect)(cellSources.some(s => s.includes('signal'))).toBe(true);
    });
    (0, globals_1.it)('should generate valid notebook from breakout template', () => {
        const manager = new templateManager_1.TemplateManager();
        const template = manager.getTemplate('breakout');
        (0, globals_1.expect)(template).toBeDefined();
        const notebook = template.toNotebook();
        (0, globals_1.expect)(notebook.nbformat).toBe(4);
        (0, globals_1.expect)(notebook.cells.length).toBeGreaterThan(0);
        (0, globals_1.expect)(notebook.metadata.kernelspec).toBeDefined();
        // Verify it's valid JSON
        (0, globals_1.expect)(() => JSON.stringify(notebook)).not.toThrow();
    });
    (0, globals_1.it)('should generate valid notebook from mean reversion template', () => {
        const manager = new templateManager_1.TemplateManager();
        const template = manager.getTemplate('mean_reversion');
        (0, globals_1.expect)(template).toBeDefined();
        const notebook = template.toNotebook();
        (0, globals_1.expect)(notebook.nbformat).toBe(4);
        (0, globals_1.expect)(notebook.cells.length).toBeGreaterThan(0);
        (0, globals_1.expect)(notebook.metadata.kernelspec).toBeDefined();
        // Verify it's valid JSON
        (0, globals_1.expect)(() => JSON.stringify(notebook)).not.toThrow();
    });
    (0, globals_1.it)('template metadata should include required fields', () => {
        const manager = new templateManager_1.TemplateManager();
        const templates = manager.listTemplates();
        templates.forEach(template => {
            (0, globals_1.expect)(template.name).toBeDefined();
            (0, globals_1.expect)(template.name.length).toBeGreaterThan(0);
            (0, globals_1.expect)(template.description).toBeDefined();
            (0, globals_1.expect)(template.description.length).toBeGreaterThan(0);
        });
    });
});
//# sourceMappingURL=templateManager.test.js.map