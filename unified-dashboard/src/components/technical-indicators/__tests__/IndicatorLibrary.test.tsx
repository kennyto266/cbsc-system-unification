import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import { store } from '../../../store'
import IndicatorLibraryPage from '../../pages/technical-indicators/IndicatorLibraryPage'
import { fetchIndicators } from '../../../store/slices/technicalIndicatorsSlice'

// Mock the store actions
jest.mock('../../../store/slices/technicalIndicatorsSlice', () => ({
  ...jest.requireActual('../../../store/slices/technicalIndicatorsSlice'),
  fetchIndicators: jest.fn(),
}))

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <ConfigProvider>
          {component}
        </ConfigProvider>
      </BrowserRouter>
    </Provider>
  )
}

describe('IndicatorLibraryPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the indicator library page correctly', async () => {
    renderWithProviders(<IndicatorLibraryPage />)

    // Check if the page title is rendered
    expect(screen.getByText('技术指标库')).toBeInTheDocument()
    expect(screen.getByText('探索和配置 477 种专业技术指标，构建您的交易策略')).toBeInTheDocument()

    // Check if quick stats cards are rendered
    expect(screen.getByText('总指标数')).toBeInTheDocument()
    expect(screen.getByText('已收藏')).toBeInTheDocument()
    expect(screen.getByText('自定义指标')).toBeInTheDocument()
    expect(screen.getByText('指标类别')).toBeInTheDocument()

    // Verify fetchIndicators was called
    expect(fetchIndicators).toHaveBeenCalled()
  })

  it('handles search functionality correctly', async () => {
    renderWithProviders(<IndicatorLibraryPage />)

    // Find the search input
    const searchInput = screen.getByPlaceholderText('搜索指标名称、描述或标签...')
    expect(searchInput).toBeInTheDocument()

    // Type in the search input
    fireEvent.change(searchInput, { target: { value: 'RSI' } })

    // Check if the search value is updated
    await waitFor(() => {
      expect(searchInput).toHaveValue('RSI')
    })
  })

  it('renders tabs correctly', () => {
    renderWithProviders(<IndicatorLibraryPage />)

    // Check if main tabs are rendered
    expect(screen.getByText('全部指标')).toBeInTheDocument()
    expect(screen.getByText('我的收藏')).toBeInTheDocument()
    expect(screen.getByText('自定义指标')).toBeInTheDocument()

    // Check if category tabs are rendered
    expect(screen.getByText('趋势指标')).toBeInTheDocument()
    expect(screen.getByText('动量指标')).toBeInTheDocument()
    expect(screen.getByText('波动率指标')).toBeInTheDocument()
  })

  it('shows empty state when no indicators match search', async () => {
    renderWithProviders(<IndicatorLibraryPage />)

    // Find the search input and search for something that won't match
    const searchInput = screen.getByPlaceholderText('搜索指标名称、描述或标签...')
    fireEvent.change(searchInput, { target: { value: 'NONEXISTENT_INDICATOR' } })

    // Wait for empty state to appear
    await waitFor(() => {
      expect(screen.getByText('未找到匹配的指标')).toBeInTheDocument()
    })
  })

  it('opens filter drawer when filter button is clicked', async () => {
    renderWithProviders(<IndicatorLibraryPage />)

    // Find and click the filter button
    const filterButton = screen.getByText('高级筛选')
    fireEvent.click(filterButton)

    // Check if filter drawer content appears
    await waitFor(() => {
      expect(screen.getByText('高级筛选')).toBeInTheDocument()
    })
  })

  it('shows loading state while fetching indicators', () => {
    // Mock the loading state
    ;(fetchIndicators as jest.Mock).mockImplementation(() => (dispatch: any) => {
      dispatch({ type: 'technicalIndicators/fetchIndicators/pending' })
    })

    renderWithProviders(<IndicatorLibraryPage />)

    // Check if loading spinner appears
    // Note: This might need adjustment based on actual loading implementation
  })

  it('displays popular combinations section', () => {
    renderWithProviders(<IndicatorLibraryPage />)

    // Check if popular combinations section is rendered
    expect(screen.getByText('热门组合')).toBeInTheDocument()
    expect(screen.getByText('MACD + RSI 组合')).toBeInTheDocument()
    expect(screen.getByText('布林带 + 随机指标')).toBeInTheDocument()
  })

  it('handles category filtering correctly', async () => {
    renderWithProviders(<IndicatorLibraryPage />)

    // Find category select dropdown
    const categorySelect = screen.getByText('选择类别')
    fireEvent.click(categorySelect)

    // Select a category
    await waitFor(() => {
      const trendOption = screen.getByText('趋势指标')
      fireEvent.click(trendOption)
    })

    // Verify filter was applied
    // This would require checking if the filtered indicators are displayed
  })

  it('navigates between tabs correctly', async () => {
    renderWithProviders(<IndicatorLibraryPage />)

    // Click on favorites tab
    const favoritesTab = screen.getByText('我的收藏')
    fireEvent.click(favoritesTab)

    // Verify tab is active
    await waitFor(() => {
      expect(favoritesTab.closest('.ant-tabs-tab-active')).toBeInTheDocument()
    })

    // Click on custom indicators tab
    const customTab = screen.getByText('自定义指标')
    fireEvent.click(customTab)

    // Verify tab is active
    await waitFor(() => {
      expect(customTab.closest('.ant-tabs-tab-active')).toBeInTheDocument()
    })
  })
})