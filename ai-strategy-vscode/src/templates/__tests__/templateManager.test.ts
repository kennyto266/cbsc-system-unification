import { describe, it, expect } from '@jest/globals';
import { TemplateManager } from '../templateManager';

describe('TemplateManager', () => {
  it('should initialize with built-in templates', () => {
    const manager = new TemplateManager();

    const templates = manager.listTemplates();

    expect(templates.length).toBeGreaterThanOrEqual(2);
    expect(templates.some(t => t.name === 'breakout')).toBe(true);
    expect(templates.some(t => t.name === 'mean_reversion')).toBe(true);
  });

  it('should retrieve breakout template', () => {
    const manager = new TemplateManager();
    const template = manager.getTemplate('breakout');

    expect(template).toBeDefined();
    expect(template?.name).toBe('breakout');
    expect(template?.description).toContain('breakout');
  });

  it('should retrieve mean reversion template', () => {
    const manager = new TemplateManager();
    const template = manager.getTemplate('mean_reversion');

    expect(template).toBeDefined();
    expect(template?.name).toBe('mean_reversion');
    expect(template?.description.toLowerCase()).toContain('mean reversion');
  });

  it('should return undefined for non-existent template', () => {
    const manager = new TemplateManager();
    const template = manager.getTemplate('non-existent');

    expect(template).toBeUndefined();
  });

  it('breakout template should have required cells', () => {
    const manager = new TemplateManager();
    const template = manager.getTemplate('breakout');

    expect(template).toBeDefined();
    expect(template!.cells.length).toBeGreaterThanOrEqual(6);

    const cellSources = template!.cells.map(cell =>
      Array.isArray(cell.source) ? cell.source.join(' ') : cell.source
    );

    // Check for key components
    expect(cellSources.some(s => s.includes('fetch_data') || s.includes('fetch'))).toBe(true);
    expect(cellSources.some(s => s.includes('portfolio') || s.includes('backtest'))).toBe(true);
    expect(cellSources.some(s => s.includes('matplotlib') || s.includes('plot'))).toBe(true);
  });

  it('mean reversion template should have required cells', () => {
    const manager = new TemplateManager();
    const template = manager.getTemplate('mean_reversion');

    expect(template).toBeDefined();
    expect(template!.cells.length).toBeGreaterThanOrEqual(4);

    const cellSources = template!.cells.map(cell =>
      Array.isArray(cell.source) ? cell.source.join(' ') : cell.source
    );

    // Check for key components
    expect(cellSources.some(s => s.includes('Bollinger') || s.includes('bollinger'))).toBe(true);
    expect(cellSources.some(s => s.includes('z_score') || s.includes('z-score'))).toBe(true);
    expect(cellSources.some(s => s.includes('signal'))).toBe(true);
  });

  it('should generate valid notebook from breakout template', () => {
    const manager = new TemplateManager();
    const template = manager.getTemplate('breakout');

    expect(template).toBeDefined();

    const notebook = template!.toNotebook();

    expect(notebook.nbformat).toBe(4);
    expect(notebook.cells.length).toBeGreaterThan(0);
    expect(notebook.metadata.kernelspec).toBeDefined();

    // Verify it's valid JSON
    expect(() => JSON.stringify(notebook)).not.toThrow();
  });

  it('should generate valid notebook from mean reversion template', () => {
    const manager = new TemplateManager();
    const template = manager.getTemplate('mean_reversion');

    expect(template).toBeDefined();

    const notebook = template!.toNotebook();

    expect(notebook.nbformat).toBe(4);
    expect(notebook.cells.length).toBeGreaterThan(0);
    expect(notebook.metadata.kernelspec).toBeDefined();

    // Verify it's valid JSON
    expect(() => JSON.stringify(notebook)).not.toThrow();
  });

  it('template metadata should include required fields', () => {
    const manager = new TemplateManager();
    const templates = manager.listTemplates();

    templates.forEach(template => {
      expect(template.name).toBeDefined();
      expect(template.name.length).toBeGreaterThan(0);
      expect(template.description).toBeDefined();
      expect(template.description.length).toBeGreaterThan(0);
    });
  });
});
