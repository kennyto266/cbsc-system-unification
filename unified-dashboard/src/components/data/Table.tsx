import React, { useState } from 'react'
import { cn } from '@/utils/cn'

export interface Column<T = any> {
  key: string
  title: string
  dataIndex?: string
  render?: (value: any, record: T, index: number) => React.ReactNode
  sortable?: boolean
  width?: string | number
  align?: 'left' | 'center' | 'right'
  className?: string
}

export interface TableProps<T = any> {
  columns: Column<T>[]
  data: T[]
  loading?: boolean
  pagination?: {
    current: number
    pageSize: number
    total: number
    onChange: (page: number, pageSize: number) => void
  }
  rowSelection?: {
    selectedRowKeys: string[]
    onChange: (selectedRowKeys: string[], selectedRows: T[]) => void
  }
  onRow?: (record: T, index: number) => React.HTMLAttributes<HTMLTableRowElement>
  className?: string
  size?: 'small' | 'middle' | 'large'
  striped?: boolean
  bordered?: boolean
}

function Table<T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  pagination,
  rowSelection,
  onRow,
  className,
  size = 'middle',
  striped = false,
  bordered = false,
}: TableProps<T>) {
  const [sortConfig, setSortConfig] = useState<{
    key: string
    direction: 'asc' | 'desc'
  } | null>(null)

  const handleSort = (column: Column<T>) => {
    if (!column.sortable) return

    let direction: 'asc' | 'desc' = 'asc'
    if (sortConfig && sortConfig.key === column.key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }

    setSortConfig({ key: column.key, direction })
  }

  const sortedData = React.useMemo(() => {
    if (!sortConfig) return data

    return [...data].sort((a, b) => {
      const aValue = a[sortConfig.key]
      const bValue = b[sortConfig.key]

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1
      }
      return 0
    })
  }, [data, sortConfig])

  const sizeClasses = {
    small: 'text-xs',
    middle: 'text-sm',
    large: 'text-base',
  }

  const paddingClasses = {
    small: 'px-2 py-1',
    middle: 'px-4 py-2',
    large: 'px-6 py-3',
  }

  return (
    <div className={cn('w-full overflow-hidden', className)}>
      <div className="overflow-x-auto">
        <table className={cn(
          'w-full border-collapse',
          sizeClasses[size],
          bordered && 'border border-gray-200'
        )}>
          <thead>
            <tr className={cn(
              'bg-gray-50',
              striped && 'bg-gray-100'
            )}>
              {rowSelection && (
                <th className={cn(
                  'text-left font-medium text-gray-900',
                  paddingClasses[size],
                  bordered && 'border border-gray-200'
                )}>
                  <input
                    type="checkbox"
                    checked={rowSelection.selectedRowKeys.length === data.length}
                    onChange={(e) => {
                      if (e.target.checked) {
                        const allKeys = data.map((_, index) => index.toString())
                        rowSelection.onChange(allKeys, data)
                      } else {
                        rowSelection.onChange([], [])
                      }
                    }}
                  />
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    'text-left font-medium text-gray-900',
                    paddingClasses[size],
                    column.align === 'center' && 'text-center',
                    column.align === 'right' && 'text-right',
                    column.sortable && 'cursor-pointer hover:bg-gray-100',
                    bordered && 'border border-gray-200',
                    column.className
                  )}
                  style={{ width: column.width }}
                  onClick={() => handleSort(column)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.title}</span>
                    {column.sortable && sortConfig?.key === column.key && (
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d={
                            sortConfig.direction === 'asc'
                              ? 'M5 15l7-7 7 7'
                              : 'M19 9l-7 7-7-7'
                          }
                        />
                      </svg>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td
                  colSpan={columns.length + (rowSelection ? 1 : 0)}
                  className={cn(
                    'text-center py-8 text-gray-500',
                    paddingClasses[size]
                  )}
                >
                  <div className="flex items-center justify-center space-x-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    <span>加载中...</span>
                  </div>
                </td>
              </tr>
            ) : sortedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (rowSelection ? 1 : 0)}
                  className={cn(
                    'text-center py-8 text-gray-500',
                    paddingClasses[size]
                  )}
                >
                  暂无数据
                </td>
              </tr>
            ) : (
              sortedData.map((record, index) => {
                const isSelected = rowSelection?.selectedRowKeys.includes(index.toString())
                const rowProps = onRow?.(record, index) || {}

                return (
                  <tr
                    key={index}
                    className={cn(
                      'border-t border-gray-200 hover:bg-gray-50',
                      striped && index % 2 === 1 && 'bg-gray-50',
                      isSelected && 'bg-primary-50',
                      bordered && 'border border-gray-200'
                    )}
                    {...rowProps}
                  >
                    {rowSelection && (
                      <td className={cn(
                        paddingClasses[size],
                        bordered && 'border border-gray-200'
                      )}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => {
                            if (e.target.checked) {
                              const newKeys = [...rowSelection.selectedRowKeys, index.toString()]
                              const newRows = [...rowSelection.selectedRows, record]
                              rowSelection.onChange(newKeys, newRows)
                            } else {
                              const newKeys = rowSelection.selectedRowKeys.filter(k => k !== index.toString())
                              const newRows = rowSelection.selectedRows.filter((_, i) => rowSelection.selectedRowKeys[i] !== index.toString())
                              rowSelection.onChange(newKeys, newRows)
                            }
                          }}
                        />
                      </td>
                    )}
                    {columns.map((column) => {
                      const value = column.dataIndex ? record[column.dataIndex] : record[column.key]
                      return (
                        <td
                          key={column.key}
                          className={cn(
                            paddingClasses[size],
                            column.align === 'center' && 'text-center',
                            column.align === 'right' && 'text-right',
                            bordered && 'border border-gray-200',
                            column.className
                          )}
                        >
                          {column.render ? column.render(value, record, index) : value}
                        </td>
                      )
                    })}
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {pagination && (
        <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200">
          <div className="text-sm text-gray-700">
            显示第 {(pagination.current - 1) * pagination.pageSize + 1} 到{' '}
            {Math.min(pagination.current * pagination.pageSize, pagination.total)} 条，
            共 {pagination.total} 条记录
          </div>
          <div className="flex items-center space-x-2">
            <button
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={pagination.current === 1}
              onClick={() => pagination.onChange(pagination.current - 1, pagination.pageSize)}
            >
              上一页
            </button>
            <span className="text-sm">
              第 {pagination.current} 页，共 {Math.ceil(pagination.total / pagination.pageSize)} 页
            </span>
            <button
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
              onClick={() => pagination.onChange(pagination.current + 1, pagination.pageSize)}
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export { Table }