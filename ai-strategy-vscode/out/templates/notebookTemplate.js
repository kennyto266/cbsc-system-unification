"use strict";
/**
 * NotebookTemplate - Base class for creating Jupyter notebook templates
 *
 * Provides methods to build notebook cells and export to Jupyter format
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.NotebookTemplate = void 0;
class NotebookTemplate {
    constructor(name, description) {
        this.cells = [];
        this.name = name;
        this.description = description;
    }
    /**
     * Add a cell to the template
     * @param cellType - Type of cell ('code' or 'markdown')
     * @param content - Cell content (can be multiline)
     */
    addCell(cellType, content) {
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
    toNotebook() {
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
    toJSON() {
        return JSON.stringify(this.toNotebook(), null, 2);
    }
    /**
     * Get all cells in the template
     * @returns Array of notebook cells
     */
    getCells() {
        return [...this.cells];
    }
    /**
     * Get cell count
     * @returns Number of cells in the template
     */
    getCellCount() {
        return this.cells.length;
    }
}
exports.NotebookTemplate = NotebookTemplate;
//# sourceMappingURL=notebookTemplate.js.map