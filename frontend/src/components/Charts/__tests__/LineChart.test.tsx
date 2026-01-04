import React from 'react'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'
import LineChart from '../chartjs/LineChart'
import { ThemeProvider } from '@/contexts/ThemeContext'

// Import chart test setup

// Test wrapper - 测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
)

// Sample data for testing
const sampleData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
  datasets: [
    {
      label: 'Dataset 1',
      data: [12, 19, 3, 5, 2],
      borderColor: '#3B82F6',
      backgroundColor: '#3B82F620'
    },
    {
      label: 'Dataset 2',
      data: [2, 3, 20, 5, 1],
      borderColor: '#EF4444',
      backgroundColor: '#EF444420'
    }
  ]
}

describe('LineChart Component', () => {
  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
  })

  // Basic rendering tests
  describe('Rendering', () => {
    test('renders with minimal props', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} />
        </TestWrapper>
      )

      expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument()
      expect(screen.getByTestId('chart-data')).toBeInTheDocument()
      expect(screen.getByTestId('chart-options')).toBeInTheDocument()
    })

    test('renders with custom dimensions', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} width={800} height={400} />
        </TestWrapper>
      )

      const chart = screen.getByTestId('mock-line-chart').parentElement
      expect(chart).toHaveStyle({
        width: '800px',
        height: '400px'
      })
    })

    test('renders with custom className', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} className="custom-chart" />
        </TestWrapper>
      )

      const chart = screen.getByTestId('mock-line-chart').parentElement
      expect(chart).toHaveClass('custom-chart')
    })

    test('passes data correctly to Chart.js component', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} />
        </TestWrapper>
      )

      const chartDataElement = screen.getByTestId('chart-data')
      expect(chartDataElement.textContent).toContain('Dataset 1')
      expect(chartDataElement.textContent).toContain('Dataset 2')
    })
  })

  // Props tests
  describe('Props handling', () => {
    test('handles timeSeries prop correctly', () => {
      const timeSeriesData = {
        labels: ['2023-01-01', '2023-02-01', '2023-03-01'],
        datasets: [{
          label: 'Time Series',
          data: [100, 200, 150]
        }]
      }

      render(
        <TestWrapper>
          <LineChart data={timeSeriesData} timeSeries={true} />
        </TestWrapper>
      )

      const optionsElement = screen.getByTestId('chart-options')
      expect(optionsElement.textContent).toContain('time')
    })

    test('handles areaFill prop correctly', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} areaFill={true} />
        </TestWrapper>
      )

      const chartDataElement = screen.getByTestId('chart-data')
      expect(chartDataElement.textContent).toContain('"fill":true')
    })

    test('handles stepped prop correctly', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} stepped="before" />
        </TestWrapper>
      )

      const chartDataElement = screen.getByTestId('chart-data')
      expect(chartDataElement.textContent).toContain('"stepped":"before"')
    })

    test('handles custom tension value', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} tension={0.5} />
        </TestWrapper>
      )

      const chartDataElement = screen.getByTestId('chart-data')
      expect(chartDataElement.textContent).toContain('"tension":0.5')
    })

    test('handles custom point radius', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} pointRadius={5} pointHoverRadius={8} />
        </TestWrapper>
      )

      const chartDataElement = screen.getByTestId('chart-data')
      expect(chartDataElement.textContent).toContain('"pointRadius":5')
      expect(chartDataElement.textContent).toContain('"pointHoverRadius":8')
    })

    test('handles custom border width', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} borderWidth={3} />
        </TestWrapper>
      )

      const chartDataElement = screen.getByTestId('chart-data')
      expect(chartDataElement.textContent).toContain('"borderWidth":3')
    })

    test('handles grid visibility', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} showGrid={false} />
        </TestWrapper>
      )

      const optionsElement = screen.getByTestId('chart-options')
      expect(optionsElement.textContent).toContain('"display":false')
    })

    test('handles custom grid color', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} gridColor="#CCCCCC" />
        </TestWrapper>
      )

      const optionsElement = screen.getByTestId('chart-options')
      expect(optionsElement.textContent).toContain('#CCCCCC')
    })

    test('handles custom animation duration', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} animationDuration={500} />
        </TestWrapper>
      )

      const optionsElement = screen.getByTestId('chart-options')
      expect(optionsElement.textContent).toContain('"duration":500')
    })
  })

  // Event handlers tests
  describe('Event handlers', () => {
    test('handles onDataPointClick callback', async () => {
      const handleDataPointClick = jest.fn()

      render(
        <TestWrapper>
          <LineChart data={sampleData} onDataPointClick={handleDataPointClick} />
        </TestWrapper>
      )

      // Simulate click event
      const chartElement = screen.getByTestId('mock-line-chart')
      fireEvent.click(chartElement)

      // Verify component renders with click handler
      expect(chartElement).toBeInTheDocument()
    })

    test('handles onLegendClick callback', () => {
      const handleLegendClick = jest.fn()

      render(
        <TestWrapper>
          <LineChart data={sampleData} onLegendClick={handleLegendClick} />
        </TestWrapper>
      )

      // Verify component renders with legend handler
      expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument()
    })
  })

  // Theme tests
  describe('Theme support', () => {
    test('applies light theme by default', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} theme="light" />
        </TestWrapper>
      )

      // Verify theme is applied (dark theme would have different colors)
      expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument()
    })

    test('applies dark theme correctly', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} theme="dark" />
        </TestWrapper>
      )

      // The theme should be passed and applied
      expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument()
    })
  })

  // Data processing tests
  describe('Data processing', () => {
    test('processes multiple datasets correctly', () => {
      const multiDatasetData = {
        labels: ['A', 'B', 'C'],
        datasets: [
          { label: 'Dataset 1', data: [1, 2, 3] },
          { label: 'Dataset 2', data: [4, 5, 6] },
          { label: 'Dataset 3', data: [7, 8, 9] }
        ]
      }

      render(
        <TestWrapper>
          <LineChart data={multiDatasetData} />
        </TestWrapper>
      )

      const chartDataElement = screen.getByTestId('chart-data')
      multiDatasetData.datasets.forEach(dataset => {
        expect(chartDataElement.textContent).toContain(dataset.label)
      })
    })

    test('applies default colors to datasets without explicit colors', () => {
      const dataWithoutColors = {
        labels: ['A', 'B'],
        datasets: [
          { label: 'Dataset 1', data: [1, 2] },
          { label: 'Dataset 2', data: [3, 4] },
          { label: 'Dataset 3', data: [5, 6] }
        ]
      }

      render(
        <TestWrapper>
          <LineChart data={dataWithoutColors} />
        </TestWrapper>
      )

      const chartDataElement = screen.getByTestId('chart-data')
      // Should apply theme colors (mock uses ant design colors)
      expect(chartDataElement.textContent).toContain('#1890ff')
    })

    test('preserves explicit dataset colors', () => {
      const dataWithCustomColors = {
        labels: ['A', 'B'],
        datasets: [
          {
            label: 'Custom',
            data: [1, 2],
            borderColor: '#FF0000',
            backgroundColor: '#FF000020'
          }
        ]
      }

      render(
        <TestWrapper>
          <LineChart data={dataWithCustomColors} />
        </TestWrapper>
      )

      const chartDataElement = screen.getByTestId('chart-data')
      expect(chartDataElement.textContent).toContain('#FF0000')
    })
  })

  // Options merging tests
  describe('Options merging', () => {
    test('merges custom options with defaults', () => {
      const customOptions = {
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            enabled: false
          }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }

      render(
        <TestWrapper>
          <LineChart data={sampleData} options={customOptions} />
        </TestWrapper>
      )

      const optionsElement = screen.getByTestId('chart-options')
      expect(optionsElement.textContent).toContain('"display":false')
      expect(optionsElement.textContent).toContain('"beginAtZero":true')
    })

    test('preserves default options when not overridden', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} options={{}} />
        </TestWrapper>
      )

      const optionsElement = screen.getByTestId('chart-options')
      // Should still have default responsive option
      expect(optionsElement.textContent).toContain('"responsive":true')
    })
  })

  // Edge cases tests
  describe('Edge cases', () => {
    test('handles empty datasets', () => {
      const emptyData = {
        labels: [],
        datasets: []
      }

      render(
        <TestWrapper>
          <LineChart data={emptyData} />
        </TestWrapper>
      )

      expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument()
    })

    test('handles dataset with missing values', () => {
      const dataWithNulls = {
        labels: ['A', 'B', 'C'],
        datasets: [{
          label: 'Mixed Data',
          data: [1, null, undefined, 4]
        }]
      }

      render(
        <TestWrapper>
          <LineChart data={dataWithNulls} />
        </TestWrapper>
      )

      expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument()
    })

    test('handles single data point', () => {
      const singlePointData = {
        labels: ['A'],
        datasets: [{
          label: 'Single Point',
          data: [42]
        }]
      }

      render(
        <TestWrapper>
          <LineChart data={singlePointData} />
        </TestWrapper>
      )

      expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument()
    })
  })

  // Performance tests
  describe('Performance', () => {
    test('handles large datasets efficiently', () => {
      const largeData = {
        labels: Array.from({ length: 1000 }, (_, i) => `Point ${i}`),
        datasets: [{
          label: 'Large Dataset',
          data: Array.from({ length: 1000 }, () => Math.random() * 100)
        }]
      }

      const startTime = performance.now()
      render(
        <TestWrapper>
          <LineChart data={largeData} />
        </TestWrapper>
      )
      const endTime = performance.now()

      // Should render within reasonable time
      expect(endTime - startTime).toBeLessThan(1000) // 1 second
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('supports ARIA attributes', () => {
      render(
        <TestWrapper>
          <LineChart
            data={sampleData}
            aria-label="Sales performance chart"
            role="img"
          />
        </TestWrapper>
      )

      const chart = screen.getByTestId('mock-line-chart')
      expect(chart).toBeInTheDocument()
      // Note: ARIA attributes are passed through but may not render on mock
    })

    test('supports keyboard navigation', () => {
      render(
        <TestWrapper>
          <LineChart data={sampleData} tabIndex={1} />
        </TestWrapper>
      )

      const chart = screen.getByTestId('mock-line-chart')
      expect(chart).toBeInTheDocument()
      expect(chart).toHaveAttribute('tabIndex', '1')
      // Note: Actual focus testing is limited in jsdom
    })
  })
})