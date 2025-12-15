import React, { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
  type PaginationState,
} from '@tanstack/react-table';
import { cn } from '@/lib/utils';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ShadcnButton as Button } from '@/components/ui/shadcn-button';
import { ShadcnInput as Input } from '@/components/ui/shadcn-input';
import { ShadcnSelect as Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/shadcn-select';
import { Badge } from '@/components/ui/shadcn-badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  ChevronDown,
  ChevronUp,
  ChevronsUpDown,
  MoreHorizontal,
  Search,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';

// DataTable Props 接口
export interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  searchable?: boolean;
  searchPlaceholder?: string;
  filterable?: boolean;
  filterColumns?: Array<{
    id: string;
    title: string;
    options: Array<{ value: string; label: string }>;
  }>;
  selectable?: boolean;
  onSelectionChange?: (selectedRows: TData[]) => void;
  pagination?: boolean;
  pageSize?: number;
  loading?: boolean;
  emptyState?: React.ReactNode;
  className?: string;
  rowActions?: (row: TData) => React.ReactNode;
  onRefresh?: () => void;
  onExport?: () => void;
}

// DataTable 组件
export function DataTable<TData, TValue>({
  columns,
  data,
  searchable = true,
  searchPlaceholder = 'Search...',
  filterable = true,
  filterColumns = [],
  selectable = false,
  onSelectionChange,
  pagination = true,
  pageSize = 10,
  loading = false,
  emptyState,
  className,
  rowActions,
  onRefresh,
  onExport,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [rowSelection, setRowSelection] = useState({});
  const [paginationState, setPaginationState] = useState<PaginationState>({
    pageIndex: 0,
    pageSize,
  });

  // 计算选中的行
  const selectedRows = useMemo(() => {
    if (!selectable || !onSelectionChange) return [];
    return data.filter((_, index) => rowSelection[index]);
  }, [rowSelection, data, selectable, onSelectionChange]);

  // 通知选择变化
  React.useEffect(() => {
    if (selectable && onSelectionChange) {
      onSelectionChange(selectedRows);
    }
  }, [selectedRows, selectable, onSelectionChange]);

  // 准备表格列
  const tableColumns = useMemo(() => {
    const cols = [...columns];

    // 添加选择列
    if (selectable) {
      cols.unshift({
        id: 'select',
        header: ({ table }) => (
          <Checkbox
            checked={
              table.getIsAllPageRowsSelected() ||
              (table.getIsSomePageRowsSelected() && 'indeterminate')
            }
            onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
            aria-label="Select all"
          />
        ),
        cell: ({ row }) => (
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={(value) => row.toggleSelected(!!value)}
            aria-label="Select row"
          />
        ),
        enableSorting: false,
        enableHiding: false,
      } as ColumnDef<TData, TValue>);
    }

    // 添加操作列
    if (rowActions) {
      cols.push({
        id: 'actions',
        cell: ({ row }) => {
          return (
            <div className="flex items-center justify-end space-x-2">
              {rowActions(row.original)}
            </div>
          );
        },
        enableSorting: false,
        enableHiding: false,
      } as ColumnDef<TData, TValue>);
    }

    return cols;
  }, [columns, selectable, rowActions]);

  // 创建表格实例
  const table = useReactTable({
    data,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: pagination ? getPaginationRowModel() : undefined,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    onRowSelectionChange: setRowSelection,
    onPaginationChange: setPaginationState,
    state: {
      sorting,
      columnFilters,
      globalFilter,
      rowSelection,
      pagination: paginationState,
    },
    manualPagination: !pagination,
    pageCount: pagination ? undefined : 1,
  });

  // 渲染排序图标
  const renderSortIcon = (column: any) => {
    if (!column.getCanSort()) return null;

    const sortDirection = column.getIsSorted();
    return (
      <Button
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0"
        onClick={() => column.toggleSorting()}
      >
        <ChevronsUpDown className="h-4 w-4" />
      </Button>
    );
  };

  // 渲染空状态
  if (data.length === 0 && !loading) {
    return (
      <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
        {emptyState || (
          <>
            <p className="text-muted-foreground">No data available</p>
            {searchable && globalFilter && (
              <p className="text-sm text-muted-foreground mt-1">
                Try adjusting your search criteria
              </p>
            )}
          </>
        )}
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {/* 搜索框 */}
          {searchable && (
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={searchPlaceholder}
                value={globalFilter ?? ''}
                onChange={(e) => setGlobalFilter(e.target.value)}
                className="pl-8 w-[250px]"
              />
            </div>
          )}

          {/* 过滤器 */}
          {filterable && filterColumns.map((filter) => (
            <Select
              key={filter.id}
              value={(table.getColumn(filter.id)?.getFilterValue() as string) ?? ''}
              onValueChange={(value) =>
                table.getColumn(filter.id)?.setFilterValue(value === 'all' ? undefined : value)
              }
            >
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder={filter.title} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All {filter.title}</SelectItem>
                {filter.options.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ))}
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center space-x-2">
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={loading}
            >
              <RefreshCw className={cn('h-4 w-4 mr-2', loading && 'animate-spin')} />
              Refresh
            </Button>
          )}
          {onExport && (
            <Button variant="outline" size="sm" onClick={onExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          )}
          {selectable && selectedRows.length > 0 && (
            <Badge variant="secondary">
              {selectedRows.length} selected
            </Badge>
          )}
        </div>
      </div>

      {/* 表格 */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    <div className="flex items-center space-x-2">
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                      {renderSortIcon(header.column)}
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && 'selected'}
                  className={cn(
                    'hover:bg-muted/50',
                    row.getIsSelected() && 'bg-muted'
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* 分页 */}
      {pagination && (
        <div className="flex items-center justify-between px-2">
          <div className="flex-1 text-sm text-muted-foreground">
            {table.getFilteredSelectedRowModel().rows.length} of{' '}
            {table.getFilteredRowModel().rows.length} row(s) selected.
          </div>
          <div className="flex items-center space-x-6 lg:space-x-8">
            <div className="flex items-center space-x-2">
              <p className="text-sm font-medium">Rows per page</p>
              <Select
                value={`${paginationState.pageSize}`}
                onValueChange={(value) => {
                  setPaginationState((prev) => ({
                    ...prev,
                    pageSize: Number(value),
                  }));
                }}
              >
                <SelectTrigger className="h-8 w-[70px]">
                  <SelectValue placeholder={paginationState.pageSize} />
                </SelectTrigger>
                <SelectContent side="top">
                  {[10, 20, 30, 40, 50].map((pageSize) => (
                    <SelectItem key={pageSize} value={`${pageSize}`}>
                      {pageSize}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex w-[100px] items-center justify-center text-sm font-medium">
              Page {paginationState.pageIndex + 1} of {table.getPageCount()}
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                className="hidden h-8 w-8 p-0 lg:flex"
                onClick={() => setPaginationState((prev) => ({ ...prev, pageIndex: 0 }))}
                disabled={!table.getCanPreviousPage()}
              >
                <span className="sr-only">Go to first page</span>
                <ChevronDown className="h-4 w-4 rotate-270" />
              </Button>
              <Button
                variant="outline"
                className="h-8 w-8 p-0"
                onClick={() => setPaginationState((prev) => ({ ...prev, pageIndex: prev.pageIndex - 1 }))}
                disabled={!table.getCanPreviousPage()}
              >
                <span className="sr-only">Go to previous page</span>
                <ChevronDown className="h-4 w-4 rotate-90" />
              </Button>
              <Button
                variant="outline"
                className="h-8 w-8 p-0"
                onClick={() => setPaginationState((prev) => ({ ...prev, pageIndex: prev.pageIndex + 1 }))}
                disabled={!table.getCanNextPage()}
              >
                <span className="sr-only">Go to next page</span>
                <ChevronUp className="h-4 w-4 rotate-90" />
              </Button>
              <Button
                variant="outline"
                className="hidden h-8 w-8 p-0 lg:flex"
                onClick={() => setPaginationState((prev) => ({ ...prev, pageIndex: table.getPageCount() - 1 }))}
                disabled={!table.getCanNextPage()}
              >
                <span className="sr-only">Go to last page</span>
                <ChevronUp className="h-4 w-4 rotate-270" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 扩展的列类型，支持渲染函数
export type ExtendedColumnDef<TData, TValue> = ColumnDef<TData, TValue> & {
  render?: (value: TValue, row: TData) => React.ReactNode;
};