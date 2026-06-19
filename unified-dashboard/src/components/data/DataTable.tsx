import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
  forwardRef,
  useImperativeHandle
} from 'react'
import {
  useTable,
  useSortBy,
  usePagination,
  useColumnOrder,
  useFlexLayout,
  useRowSelect,
  Column,
  Row,
  HeaderGroup,
  TableInstance,
  ColumnInstance
} from 'react-table'
import { FixedSizeList as List } from 'react-window'
import { BaseChartProps } from '../components/charts/types/chart.types'
import { ChevronUp, ChevronDown, ArrowDownUp, Download, Filter } from 'lucide-react'

// Table types
export interface TableColumn {
  id: string
  Header: string
  accessor: string | ((row: any) => any)
  width?: number
  minWidth?: number
  maxWidth?: number
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  filterable?: boolean
  Cell?: ({ value, row, column }: { value: any; row: Row; column: ColumnInstance }) => React.ReactNode
  className?: string
  headerClassName?: string
  footer?: string | ((column: ColumnInstance) => React.ReactNode)
}

export interface DataTableProps extends Omit<BaseChartProps, 'width' | 'height'> {
  columns: TableColumn[]
  data: any[]
  virtualized?: boolean
  rowHeight?: number
  maxHeight?: number
  pagination?: {
    enabled?: boolean
    pageSize?: number
    pageIndex?: number
    showSizeChanger?: boolean
    showQuickJumper?: boolean
    pageSizeOptions?: number[]
  }
  selection?: {
    enabled?: boolean
    mode?: 'single' | 'multiple'
    onSelect?: (selectedRows: any[]) => void
    getRowId?: (row: any) => string | number
  }
  sorting?: {
    enabled?: boolean
    defaultSortBy?: Array<{ id: string; desc: boolean }>
  }
  filtering?: {
    enabled?: boolean
    filters?: Record<string, any>
    onFilter?: (filters: Record<string, any>) => void
  }
  actions?: {
    enabled?: boolean
    actions?: Array<{
      key: string
      label: string
      icon?: React.ReactNode
      onClick: (selectedRows: any[]) => void
      disabled?: (selectedRows: any[]) => boolean
    }>
  }
  export?: {
    enabled?: boolean
    formats?: ('csv' | 'json' | 'excel')[]
    filename?: string
  }
  onRowClick?: (row: any, index: number) => void
  onRowDoubleClick?: (row: any, index: number) => void
  emptyMessage?: string
  loading?: boolean
  error?: string
}

export interface DataTableRef {
  refresh: () => void
  getSelectedRows: () => any[]
  exportData: (format: 'csv' | 'json' | 'excel') => void
  scrollToRow: (index: number) => void
}

// Virtualized row component
const VirtualizedRow = ({
  index,
  style,
  data
}: {
  index: number
  style: React.CSSProperties
  data: {
    prepareRow: (row: Row) => void
    rows: Row[]
    onRowClick?: (row: any, index: number) => void
    onRowDoubleClick?: (row: any, index: number) => void
  }
}) => {
  const row = data.rows[index]
  data.prepareRow(row)

  const handleClick = useCallback(() => {
    if (data.onRowClick) {
      data.onRowClick(row.original, index)
    }
  }, [row, index, data.onRowClick])

  const handleDoubleClick = useCallback(() => {
    if (data.onRowDoubleClick) {
      data.onRowDoubleClick(row.original, index)
    }
  }, [row, index, data.onRowDoubleClick])

  return (
    <div
      {...row.getRowProps({
        style
      })}
      className="table-row"
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
    >
      {row.cells.map((cell) => (
        <div
          {...cell.getCellProps()}
          className={`table-cell ${cell.column.className || ''}`}
          style={{
            ...cell.getCellProps().style,
            display: 'flex',
            alignItems: 'center',
            padding: '0 8px',
            justifyContent: cell.column.align === 'center' ? 'center' :
                          cell.column.align === 'right' ? 'flex-end' : 'flex-start'
          }}
        >
          {cell.render('Cell')}
        </div>
      ))}
    </div>
  )
}

export const DataTable = forwardRef<DataTableRef, DataTableProps>(({
  columns,
  data,
  virtualized = false,
  rowHeight = 40,
  maxHeight = 400,
  pagination = {},
  selection = {},
  sorting = {},
  filtering = {},
  actions = {},
  export: exportConfig = {},
  onRowClick,
  onRowDoubleClick,
  emptyMessage = 'No data available',
  loading = false,
  error,
  className = '',
  theme = 'light'
}, ref) => {
  const tableRef = useRef<List>(null)
  const [selectedRowIds, setSelectedRowIds] = useState<Record<string, boolean>>({})

  // Memoize columns
  const memoizedColumns = useMemo(() => columns, [columns])

  // Add selection column if enabled
  const tableColumns = useMemo(() => {
    const cols = [...memoizedColumns]

    if (selection.enabled) {
      cols.unshift({
        id: 'selection',
        Header: '',
        width: 40,
        disableResizing: true,
        Cell: ({ row }) => (
          <input
            type={selection.mode === 'single' ? 'radio' : 'checkbox'}
            checked={row.isSelected}
            onChange={() => row.toggleRowSelected()}
            style={{ cursor: 'pointer' }}
          />
        )
      })
    }

    return cols
  }, [memoizedColumns, selection])

  // Table instance
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
    page,
    canPreviousPage,
    canNextPage,
    pageOptions,
    pageCount,
    gotoPage,
    nextPage,
    previousPage,
    setPageSize,
    state: { pageIndex, pageSize, sortBy, filters },
    selectedFlatRows
  } = useTable(
    {
      columns: tableColumns,
      data,
      initialState: {
        pageSize: pagination.pageSize || 10,
        pageIndex: pagination.pageIndex || 0,
        sortBy: sorting.defaultSortBy || [],
        filters: Object.entries(filtering.filters || {}).map(([id, value]) => ({
          id,
          value
        }))
      },
      getRowId: selection.getRowId,
      manualPagination: false,
      manualSortBy: false,
      manualFilters: false
    },
    useFlexLayout,
    useColumnOrder,
    useSortBy,
    usePagination,
    useRowSelect,
    (hooks) => {
      if (selection.enabled) {
        hooks.visibleColumns.push((columns) => [
          {
            id: 'selection',
            Header: ({ getToggleAllRowsSelectedProps }) => (
              <input
                type={selection.mode === 'single' ? 'radio' : 'checkbox'}
                {...getToggleAllRowsSelectedProps()}
                style={{ cursor: 'pointer' }}
              />
            ),
            Cell: ({ row }) => (
              <input
                type={selection.mode === 'single' ? 'radio' : 'checkbox'}
                checked={row.isSelected}
                onChange={() => row.toggleRowSelected()}
                style={{ cursor: 'pointer' }}
              />
            )
          },
          ...columns
        ])
      }
    }
  ) as TableInstance

  // Handle selection change
  useEffect(() => {
    if (selection.onSelect && selection.enabled) {
      const selectedRows = selectedFlatRows.map(row => row.original)
      selection.onSelect(selectedRows)
    }
  }, [selectedFlatRows, selection])

  // Export functions
  const exportData = useCallback((format: 'csv' | 'json' | 'excel') => {
    const dataToExport = selectedFlatRows.length > 0
      ? selectedFlatRows.map(row => row.original)
      : data

    const filename = exportConfig.filename || `table_export_${Date.now()}`

    switch (format) {
      case 'csv':
        exportCSV(dataToExport, filename)
        break
      case 'json':
        exportJSON(dataToExport, filename)
        break
      case 'excel':
        exportExcel(dataToExport, filename)
        break
    }
  }, [selectedFlatRows, data, exportConfig])

  const exportCSV = (data: any[], filename: string) => {
    const headers = columns.map(col => col.Header)
    const csvContent = [
      headers.join(','),
      ...data.map(row =>
        columns.map(col => {
          const value = typeof col.accessor === 'function'
            ? col.accessor(row)
            : row[col.accessor]
          return `"${value}"`
        }).join(',')
      )
    ].join('\n')

    downloadFile(csvContent, `${filename}.csv`, 'text/csv')
  }

  const exportJSON = (data: any[], filename: string) => {
    const jsonContent = JSON.stringify(data, null, 2)
    downloadFile(jsonContent, `${filename}.json`, 'application/json')
  }

  const exportExcel = (data: any[], filename: string) => {
    // Implement Excel export using a library like xlsx
    console.log('Excel export not implemented')
  }

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Imperative API
  useImperativeHandle(ref, () => ({
    refresh: () => {
      // Trigger data refresh
    },
    getSelectedRows: () => selectedFlatRows.map(row => row.original),
    exportData,
    scrollToRow: (index: number) => {
      if (tableRef.current && virtualized) {
        tableRef.current.scrollToItem(index)
      }
    }
  }), [selectedFlatRows, exportData, virtualized])

  // Theme styles
  const themeStyles = useMemo(() => {
    return theme === 'dark'
      ? {
          backgroundColor: '#1f1f1f',
          color: 'rgba(255, 255, 255, 0.9)',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          headerBg: '#2d2d2d',
          hoverBg: 'rgba(255, 255, 255, 0.05)',
          selectedBg: 'rgba(24, 144, 255, 0.2)'
        }
      : {
          backgroundColor: '#ffffff',
          color: 'rgba(0, 0, 0, 0.9)',
          borderColor: 'rgba(0, 0, 0, 0.1)',
          headerBg: '#fafafa',
          hoverBg: 'rgba(0, 0, 0, 0.02)',
          selectedBg: 'rgba(24, 144, 255, 0.1)'
        }
  }, [theme])

  const displayData = pagination.enabled ? page : rows

  if (loading) {
    return (
      <div className="data-table-loading" style={{ padding: '20px', textAlign: 'center' }}>
        Loading...
      </div>
    )
  }

  if (error) {
    return (
      <div className="data-table-error" style={{ padding: '20px', textAlign: 'center', color: '#ff4d4f' }}>
        Error: {error}
      </div>
    )
  }

  return (
    <div className={`data-table ${className}`} style={{ backgroundColor: themeStyles.backgroundColor }}>
      {/* Actions Bar */}
      {actions.enabled && (
        <div className="table-actions" style={{
          padding: '8px 0',
          borderBottom: `1px solid ${themeStyles.borderColor}`,
          display: 'flex',
          gap: '8px'
        }}>
          {actions.actions?.map(action => (
            <button
              key={action.key}
              onClick={() => action.onClick(selectedFlatRows.map(row => row.original))}
              disabled={action.disabled?.(selectedFlatRows.map(row => row.original))}
              style={{
                padding: '4px 12px',
                border: `1px solid ${themeStyles.borderColor}`,
                borderRadius: '4px',
                backgroundColor: themeStyles.headerBg,
                color: themeStyles.color,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              {action.icon}
              {action.label}
            </button>
          ))}
        </div>
      )}

      {/* Table */}
      <div
        {...getTableProps()}
        className="table"
        style={{
          maxHeight: virtualized ? maxHeight : 'auto',
          overflow: virtualized ? 'hidden' : 'auto'
        }}
      >
        {/* Header */}
        <div className="table-head">
          {headerGroups.map(headerGroup => (
            <div
              {...headerGroup.getHeaderGroupProps()}
              className="table-header-group"
              style={{
                display: 'flex',
                backgroundColor: themeStyles.headerBg,
                borderBottom: `2px solid ${themeStyles.borderColor}`
              }}
            >
              {headerGroup.headers.map(column => (
                <div
                  {...column.getHeaderProps({
                    style: {
                      ...column.getHeaderProps().style,
                      width: column.width,
                      minWidth: column.minWidth,
                      maxWidth: column.maxWidth,
                      padding: '8px',
                      fontWeight: '600',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: column.align === 'center' ? 'center' :
                                        column.align === 'right' ? 'flex-end' : 'flex-between'
                    }
                  })}
                  className={`table-header ${column.headerClassName || ''}`}
                >
                  <span>{column.render('Header')}</span>
                  {sorting.enabled && column.sortable && (
                    <span
                      {...column.getSortByToggleProps()}
                      style={{
                        marginLeft: '4px',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center'
                      }}
                    >
                      {column.isSorted
                        ? column.isSortedDesc
                          ? <ChevronDown size={14} />
                          : <ChevronUp size={14} />
                        : <ArrowDownUp size={14} opacity={0.3} />
                      }
                    </span>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Body */}
        <div
          {...getTableBodyProps()}
          className="table-body"
          style={{
            height: virtualized ? `${displayData.length * rowHeight}px` : 'auto'
          }}
        >
          {displayData.length === 0 ? (
            <div
              style={{
                padding: '40px',
                textAlign: 'center',
                color: themeStyles.color,
                opacity: 0.6
              }}
            >
              {emptyMessage}
            </div>
          ) : virtualized ? (
            <List
              ref={tableRef}
              height={maxHeight}
              itemCount={displayData.length}
              itemSize={rowHeight}
              itemData={{
                prepareRow,
                rows: displayData,
                onRowClick,
                onRowDoubleClick
              }}
            >
              {VirtualizedRow}
            </List>
          ) : (
            displayData.map((row, index) => {
              prepareRow(row)
              return (
                <div
                  {...row.getRowProps({
                    style: {
                      display: 'flex',
                      borderBottom: `1px solid ${themeStyles.borderColor}`,
                      backgroundColor: row.isSelected ? themeStyles.selectedBg : 'transparent'
                    }
                  })}
                  className="table-row"
                  onClick={() => onRowClick?.(row.original, index)}
                  onDoubleClick={() => onRowDoubleClick?.(row.original, index)}
                  style={{
                    ...row.getRowProps().style,
                    display: 'flex',
                    backgroundColor: row.isSelected ? themeStyles.selectedBg : 'transparent'
                  }}
                >
                  {row.cells.map(cell => (
                    <div
                      {...cell.getCellProps()}
                      className={`table-cell ${cell.column.className || ''}`}
                      style={{
                        ...cell.getCellProps().style,
                        padding: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: cell.column.align === 'center' ? 'center' :
                                          cell.column.align === 'right' ? 'flex-end' : 'flex-start'
                      }}
                    >
                      {cell.render('Cell')}
                    </div>
                  ))}
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Pagination */}
      {pagination.enabled && (
        <div className="table-pagination" style={{
          padding: '16px',
          borderTop: `1px solid ${themeStyles.borderColor}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              onClick={() => gotoPage(0)}
              disabled={!canPreviousPage}
              style={{
                padding: '4px 8px',
                border: `1px solid ${themeStyles.borderColor}`,
                borderRadius: '4px',
                backgroundColor: themeStyles.headerBg,
                cursor: canPreviousPage ? 'pointer' : 'not-allowed'
              }}
            >
              {'<<'}
            </button>
            <button
              onClick={() => previousPage()}
              disabled={!canPreviousPage}
              style={{
                padding: '4px 8px',
                border: `1px solid ${themeStyles.borderColor}`,
                borderRadius: '4px',
                backgroundColor: themeStyles.headerBg,
                cursor: canPreviousPage ? 'pointer' : 'not-allowed'
              }}
            >
              {'<'}
            </button>
            <span style={{ margin: '0 8px' }}>
              Page{' '}
              <strong>
                {pageIndex + 1} of {pageOptions.length}
              </strong>
            </span>
            <button
              onClick={() => nextPage()}
              disabled={!canNextPage}
              style={{
                padding: '4px 8px',
                border: `1px solid ${themeStyles.borderColor}`,
                borderRadius: '4px',
                backgroundColor: themeStyles.headerBg,
                cursor: canNextPage ? 'pointer' : 'not-allowed'
              }}
            >
              {'>'}
            </button>
            <button
              onClick={() => gotoPage(pageCount - 1)}
              disabled={!canNextPage}
              style={{
                padding: '4px 8px',
                border: `1px solid ${themeStyles.borderColor}`,
                borderRadius: '4px',
                backgroundColor: themeStyles.headerBg,
                cursor: canNextPage ? 'pointer' : 'not-allowed'
              }}
            >
              {'>>'}
            </button>
          </div>

          {pagination.showSizeChanger && (
            <select
              value={pageSize}
              onChange={e => {
                setPageSize(Number(e.target.value))
              }}
              style={{
                padding: '4px 8px',
                border: `1px solid ${themeStyles.borderColor}`,
                borderRadius: '4px',
                backgroundColor: themeStyles.headerBg
              }}
            >
              {(pagination.pageSizeOptions || [10, 20, 30, 40, 50]).map(pageSize => (
                <option key={pageSize} value={pageSize}>
                  Show {pageSize}
                </option>
              ))}
            </select>
          )}
        </div>
      )}
    </div>
  )
})

DataTable.displayName = 'DataTable'

export default DataTable