/**
 * Economic Data Table Component
 * 經濟數據表格組件
 */

import React, { useState, useMemo } from 'react'
import { ChevronUp, ChevronDown, Search, Download, Eye, EyeOff, Calendar } from 'lucide-react'
import { format } from 'date-fns'

interface EconomicDataPoint {
  date: string
  value: number
  indicator?: string
}

interface ChartData {
  hibor?: EconomicDataPoint[]
  gdp?: EconomicDataPoint[]
  pmi?: EconomicDataPoint[]
  visitors?: EconomicDataPoint[]
  unemployment?: EconomicDataPoint[]
}

interface EconomicDataTableProps {
  data: ChartData
  indicators: string[]
  loading: boolean
  error: string | null
  className?: string
}

interface SortConfig {
  key: string
  direction: 'asc' | 'desc'
}

interface Column {
  key: string
  label: string
  sortable: boolean
  format?: (value: any) => string
  width?: string
}

export default function EconomicDataTable({
  data,
  indicators,
  loading,
  error,
  className = ''
}: EconomicDataTableProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(50)
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'date', direction: 'desc' })
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(
    new Set(['date', 'indicator', 'value', 'change'])
  )

  // Generate table data from the economic data
  const tableData = useMemo(() => {
    const rows: any[] = []

    indicators.forEach(indicator => {
      const indicatorData = data[indicator as keyof ChartData] || []

      indicatorData.forEach((point: EconomicDataPoint, index: number) => {
        const prevPoint = index > 0 ? indicatorData[index - 1] : null
        const change = prevPoint ? point.value - prevPoint.value : 0
        const changePercent = prevPoint ? ((point.value - prevPoint.value) / prevPoint.value) * 100 : 0

        rows.push({
          id: `${indicator}-${point.date}`,
          date: point.date,
          indicator: indicator.toUpperCase(),
          value: point.value,
          change: change,
          changePercent: changePercent,
          rawValue: point.value,
          rawDate: new Date(point.date).getTime()
        })
      })
    })

    return rows.sort((a, b) => {
      if (sortConfig.key === 'date') {
        return sortConfig.direction === 'asc'
          ? a.rawDate - b.rawDate
          : b.rawDate - a.rawDate
      }

      const aValue = a[sortConfig.key]
      const bValue = b[sortConfig.key]

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortConfig.direction === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue)
      }

      return sortConfig.direction === 'asc'
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number)
    })
  }, [data, indicators, sortConfig])

  // Filter data based on search term
  const filteredData = useMemo(() => {
    if (!searchTerm) return tableData

    return tableData.filter(row => {
      const searchLower = searchTerm.toLowerCase()
      return (
        row.date.toLowerCase().includes(searchLower) ||
        row.indicator.toLowerCase().includes(searchLower) ||
        row.value.toString().includes(searchLower) ||
        row.change.toString().includes(searchLower)
      )
    })
  }, [tableData, searchTerm])

  // Paginate data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return filteredData.slice(startIndex, endIndex)
  }, [filteredData, currentPage, itemsPerPage])

  const totalPages = Math.ceil(filteredData.length / itemsPerPage)

  // Column definitions
  const columns: Column[] = [
    {
      key: 'date',
      label: 'Date',
      sortable: true,
      format: (value: string) => format(new Date(value), 'MMM dd, yyyy'),
      width: '150px'
    },
    {
      key: 'indicator',
      label: 'Indicator',
      sortable: true,
      width: '120px'
    },
    {
      key: 'value',
      label: 'Value',
      sortable: true,
      format: (value: number, row: any) => {
        switch (row.indicator.toLowerCase()) {
          case 'hibor':
            return `${value.toFixed(2)}%`
          case 'gdp':
            return `${value.toFixed(1)}%`
          case 'pmi':
            return value.toFixed(1)
          case 'visitors':
            return `${(value / 1000000).toFixed(2)}M`
          case 'unemployment':
            return `${value.toFixed(1)}%`
          default:
            return value.toFixed(2)
        }
      },
      width: '100px'
    },
    {
      key: 'change',
      label: 'Change',
      sortable: true,
      format: (value: number, row: any) => {
        const formattedValue = Math.abs(value).toFixed(2)
        const indicator = row.indicator.toLowerCase()
        let unit = ''

        if (['hibor', 'gdp', 'unemployment'].includes(indicator)) {
          unit = '%'
        } else if (indicator === 'visitors') {
          unit = 'K'
          return `${value >= 0 ? '+' : ''}${(value / 1000).toFixed(1)}${unit}`
        }

        return `${value >= 0 ? '+' : '-'}${formattedValue}${unit}`
      },
      width: '100px'
    },
    {
      key: 'changePercent',
      label: 'Change %',
      sortable: true,
      format: (value: number) => {
        const colorClass = value > 0 ? 'text-green-600' : value < 0 ? 'text-red-600' : 'text-gray-600'
        return `<span class="${colorClass}">${value >= 0 ? '+' : ''}${value.toFixed(2)}%</span>`
      },
      width: '100px'
    }
  ]

  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
  }

  const toggleColumn = (columnKey: string) => {
    const newVisibleColumns = new Set(visibleColumns)
    if (newVisibleColumns.has(columnKey)) {
      newVisibleColumns.delete(columnKey)
    } else {
      newVisibleColumns.add(columnKey)
    }
    setVisibleColumns(newVisibleColumns)
  }

  const exportData = (format: 'csv' | 'json') => {
    let content = ''
    let filename = `economic-data-${format(new Date(), 'yyyy-MM-dd')}`

    if (format === 'csv') {
      const headers = columns
        .filter(col => visibleColumns.has(col.key))
        .map(col => col.label)
        .join(',')

      const rows = filteredData.map(row => {
        return columns
          .filter(col => visibleColumns.has(col.key))
          .map(col => {
            const value = row[col.key]
            return col.format ? col.format(value, row).replace(/<[^>]*>/g, '') : value
          })
          .join(',')
      })

      content = [headers, ...rows].join('\n')
      filename += '.csv'
    } else {
      content = JSON.stringify(filteredData, null, 2)
      filename += '.json'
    }

    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-8 text-center ${className}`}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading economic data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-8 text-center ${className}`}>
        <div className="text-red-500 text-lg mb-2">⚠️</div>
        <p className="text-gray-600">Error loading data: {error}</p>
      </div>
    )
  }

  if (filteredData.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-8 text-center ${className}`}>
        <p className="text-gray-600">No data available for the selected criteria.</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Economic Data Table
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({filteredData.length.toLocaleString()} records)
            </span>
          </h3>

          <div className="flex items-center space-x-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search data..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Export */}
            <div className="relative group">
              <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                <Download className="h-5 w-5" />
              </button>
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                <button
                  onClick={() => exportData('csv')}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Export as CSV
                </button>
                <button
                  onClick={() => exportData('json')}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Export as JSON
                </button>
              </div>
            </div>

            {/* Column Visibility */}
            <div className="relative group">
              <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                <Eye className="h-5 w-5" />
              </button>
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                {columns.map(column => (
                  <label
                    key={column.key}
                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={visibleColumns.has(column.key)}
                      onChange={() => toggleColumn(column.key)}
                      className="mr-2"
                    />
                    {column.label}
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns
                .filter(col => visibleColumns.has(col.key))
                .map(column => (
                  <th
                    key={column.key}
                    style={{ width: column.width }}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => column.sortable && handleSort(column.key)}
                  >
                    <div className="flex items-center space-x-1">
                      <span>{column.label}</span>
                      {sortConfig.key === column.key && (
                        sortConfig.direction === 'asc' ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )
                      )}
                    </div>
                  </th>
                ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.map((row, index) => (
              <tr
                key={row.id}
                className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
              >
                {columns
                  .filter(col => visibleColumns.has(col.key))
                  .map(column => {
                    const value = row[column.key]
                    const formattedValue = column.format ? column.format(value, row) : value

                    return (
                      <td
                        key={column.key}
                        className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                      >
                        {column.key === 'change' && (
                          <span className={value > 0 ? 'text-green-600' : value < 0 ? 'text-red-600' : 'text-gray-600'}>
                            {formattedValue}
                          </span>
                        )}
                        {column.key === 'changePercent' && (
                          <span className={value > 0 ? 'text-green-600' : value < 0 ? 'text-red-600' : 'text-gray-600'}>
                            {formattedValue}
                          </span>
                        )}
                        {column.key !== 'change' && column.key !== 'changePercent' && formattedValue}
                      </td>
                    )
                  })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="px-6 py-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {((currentPage - 1) * itemsPerPage) + 1} to{' '}
            {Math.min(currentPage * itemsPerPage, filteredData.length)} of{' '}
            {filteredData.length} results
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>

            <div className="flex space-x-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum = i + 1
                if (totalPages > 5) {
                  const startPage = Math.max(1, currentPage - 2)
                  const endPage = Math.min(totalPages, startPage + 4)
                  pageNum = startPage + i
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-1 text-sm border rounded-md ${
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              })}
            </div>

            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}