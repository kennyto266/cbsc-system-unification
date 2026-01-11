import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';
import TouchFeedback from './TouchFeedback';

interface Column<T> {
  key: keyof T;
  title: string;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  sorter?: (a: T, b: T) => number;
}

interface MobileTableProps<T> {
  data: T[];
  columns: Column<T>[];
  className?: string;
  rowKey?: keyof T | ((record: T) => string);
  onRow?: (record: T, index: number) => {
    onClick?: (e: React.MouseEvent) => void;
    className?: string;
  };
  expandedRowRender?: (record: T, index: number) => React.ReactNode;
  defaultExpandAllRows?: boolean;
  loading?: boolean;
  empty?: React.ReactNode;
  cardMode?: boolean;
}

/**
 * MobileTable - Responsive table component for mobile devices
 * Supports both table view and card view based on screen size
 */
function MobileTable<T extends Record<string, any>>({
  data,
  columns,
  className,
  rowKey = 'id',
  onRow,
  expandedRowRender,
  defaultExpandAllRows = false,
  loading = false,
  empty,
  cardMode = false,
}: MobileTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<{
    key: keyof T;
    direction: 'asc' | 'desc';
  } | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string | number>>(
    defaultExpandAllRows ? new Set(data.map((_, i) => i)) : new Set()
  );

  const getRowKey = (record: T, index: number): string | number => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return record[rowKey as keyof T] as string | number || index;
  };

  const handleSort = (column: Column<T>) => {
    if (!column.sortable || !column.sorter) return;

    const direction = sortConfig?.key === column.key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    setSortConfig({ key: column.key, direction });
  };

  const sortedData = React.useMemo(() => {
    if (!sortConfig) return data;

    const column = columns.find(col => col.key === sortConfig.key);
    if (!column?.sorter) return data;

    return [...data].sort((a, b) => {
      const result = column.sorter!(a, b);
      return sortConfig.direction === 'asc' ? result : -result;
    });
  }, [data, columns, sortConfig]);

  const toggleExpanded = (key: string | number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedRows(newExpanded);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        {empty || (
          <>
            <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p>暫無數據</p>
          </>
        )}
      </div>
    );
  }

  // Mobile Card View
  if (cardMode) {
    return (
      <div className={clsx('space-y-3', className)}>
        {sortedData.map((record, index) => {
          const key = getRowKey(record, index);
          const isExpanded = expandedRows.has(key);
          const rowProps = onRow?.(record, index) || {};

          return (
            <TouchFeedback key={key} {...rowProps}>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                {/* Card Header */}
                <div className="p-4 space-y-3">
                  {columns.map((column, colIndex) => {
                    const value = record[column.key as keyof T];
                    const content = column.render ? column.render(value, record, index) : value;

                    if (colIndex === 0) {
                      // First column as title
                      return (
                        <div key={column.key as string} className="flex items-center justify-between">
                          <h3 className="font-medium text-gray-900 flex-1">{content}</h3>
                          {expandedRowRender && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleExpanded(key);
                              }}
                              className="p-1 rounded hover:bg-gray-100 transition-colors"
                            >
                              {isExpanded ? (
                                <ChevronDown className="w-5 h-5" />
                              ) : (
                                <ChevronRight className="w-5 h-5" />
                              )}
                            </button>
                          )}
                        </div>
                      );
                    }

                    return (
                      <div key={column.key as string} className="flex items-start gap-2">
                        <span className="text-sm text-gray-500 whitespace-nowrap min-w-0 flex-shrink-0">
                          {column.title}:
                        </span>
                        <span className={clsx(
                          'text-sm text-gray-900 flex-1',
                          column.align === 'right' && 'text-right',
                          column.align === 'center' && 'text-center'
                        )}>
                          {content}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* Expanded Content */}
                {expandedRowRender && isExpanded && (
                  <div className="px-4 pb-4 border-t border-gray-100">
                    {expandedRowRender(record, index)}
                  </div>
                )}
              </div>
            </TouchFeedback>
          );
        })}
      </div>
    );
  }

  // Desktop Table View
  return (
    <div className={clsx('bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden', className)}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key as string}
                  scope="col"
                  className={clsx(
                    'px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider',
                    column.align === 'center' && 'text-center',
                    column.align === 'right' && 'text-right'
                  )}
                  style={{ width: column.width }}
                >
                  {column.sortable ? (
                    <button
                      onClick={() => handleSort(column)}
                      className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                    >
                      {column.title}
                      {sortConfig?.key === column.key && (
                        <span className="text-primary-600">
                          {sortConfig.direction === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </button>
                  ) : (
                    column.title
                  )}
                </th>
              ))}
              {expandedRowRender && <th className="w-10" />}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedData.map((record, index) => {
              const key = getRowKey(record, index);
              const isExpanded = expandedRows.has(key);
              const rowProps = onRow?.(record, index) || {};

              return (
                <React.Fragment key={key}>
                  <tr
                    {...rowProps}
                    className={clsx(
                      'hover:bg-gray-50 transition-colors',
                      rowProps.className
                    )}
                  >
                    {columns.map((column) => {
                      const value = record[column.key as keyof T];
                      const content = column.render ? column.render(value, record, index) : value;

                      return (
                        <td
                          key={column.key as string}
                          className={clsx(
                            'px-6 py-4 whitespace-nowrap text-sm text-gray-900',
                            column.align === 'center' && 'text-center',
                            column.align === 'right' && 'text-right'
                          )}
                        >
                          {content}
                        </td>
                      );
                    })}
                    {expandedRowRender && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => toggleExpanded(key)}
                          className="p-1 rounded hover:bg-gray-100 transition-colors"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-5 h-5" />
                          ) : (
                            <ChevronRight className="w-5 h-5" />
                          )}
                        </button>
                      </td>
                    )}
                  </tr>
                  {expandedRowRender && isExpanded && (
                    <tr>
                      <td colSpan={columns.length + (expandedRowRender ? 1 : 0)} className="px-6 py-4">
                        {expandedRowRender(record, index)}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default MobileTable;