/**
 * UI Slice - UI狀態管理
 * 版本: 1.0.0
 * 描述: 管理UI相關的全局狀態
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// 主題類型
export type Theme = 'light' | 'dark' | 'auto'

// 語言類型
export type Language = 'zh-CN' | 'zh-TW' | 'en-US'

// 通知類型
export type NotificationType = 'success' | 'error' | 'warning' | 'info'

// 通知接口
export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  duration?: number
  persistent?: boolean
  timestamp: number
  actions?: Array<{
    label: string
    action: () => void
    primary?: boolean
  }>
}

// 側邊欄狀態
export interface SidebarState {
  isOpen: boolean
  isCollapsed: boolean
  activeMenu?: string
  openMenus: string[]
}

// UI State 接口
export interface UIState {
  // 主題和語言
  theme: Theme
  language: Language

  // 側邊欄
  sidebar: SidebarState

  // 通知
  notifications: Notification[]

  // 加載狀態
  globalLoading: boolean
  loading: Record<string, boolean>
  loadingText?: string

  // 模態框
  modals: Record<string, boolean>

  // 抽層
  drawers: Record<string, boolean>

  // 分頁大小
  pageSize: number

  // 頁面標題
  pageTitle: string
  breadcrumb: Array<{
    title: string
    path?: string
  }>

  // 響應式
  isMobile: boolean
  screenSize: {
    width: number
    height: number
  }

  // 捲綁監聽
  keyboardShortcuts: {
    enabled: boolean
    helpVisible: boolean
  }

  // 搜索狀態
  globalSearch: {
    isOpen: boolean
    query: string
    results: any[]
  }

  // 快捷操作
  quickActions: {
    visible: boolean
    actions: Array<{
      id: string
      label: string
      icon: string
      action: () => void
      shortcut?: string
    }>
  }
}

// 初始狀態
const getInitialState = (): UIState => ({
  theme: (localStorage.getItem('cbsc_theme') as Theme) || 'light',
  language: (localStorage.getItem('cbsc_language') as Language) || 'zh-CN',

  sidebar: {
    isOpen: true,
    isCollapsed: false,
    openMenus: [],
  },

  notifications: [],

  globalLoading: false,
  loading: {},
  loadingText: undefined,

  modals: {},
  drawers: {},

  pageSize: 20,

  pageTitle: 'CBSC 策略管理系統',
  breadcrumb: [],

  isMobile: window.innerWidth < 768,
  screenSize: {
    width: window.innerWidth,
    height: window.innerHeight,
  },

  keyboardShortcuts: {
    enabled: true,
    helpVisible: false,
  },

  globalSearch: {
    isOpen: false,
    query: '',
    results: [],
  },

  quickActions: {
    visible: false,
    actions: [],
  },
})

const initialState: UIState = getInitialState()

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // 設置主題
    setTheme: (state, action: PayloadAction<Theme>) => {
      state.theme = action.payload;
      localStorage.setItem('cbsc_theme', action.payload);
    },

    // 設置語言
    setLanguage: (state, action: PayloadAction<Language>) => {
      state.language = action.payload;
      localStorage.setItem('cbsc_language', action.payload);
    },

    // 切換側邊欄
    toggleSidebar: (state) => {
      state.sidebar.isOpen = !state.sidebar.isOpen;
    },

    // 設置側邊欄狀態
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebar.isOpen = action.payload;
    },

    // 切換側邊權折疊
    toggleSidebarCollapse: (state) => {
      state.sidebar.isCollapsed = !state.sidebar.isCollapsed;
    },

    // 設置側邊欄折疊狀態
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebar.isCollapsed = action.payload;
    },

    // 設置活動菜單
    setActiveMenu: (state, action: PayloadAction<string>) => {
      state.sidebar.activeMenu = action.payload;
    },

    // 切換菜單展開狀態
    toggleMenuOpen: (state, action: PayloadAction<string>) => {
      const menuId = action.payload;
      const index = state.sidebar.openMenus.indexOf(menuId);
      if (index > -1) {
        state.sidebar.openMenus.splice(index, 1);
      } else {
        state.sidebar.openMenus.push(menuId);
      }
    },

    // 添加通知
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: Date.now(),
      };
      state.notifications.unshift(notification);

      // 限制通知數量
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50);
      }
    },

    // 移除通知
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },

    // 清除所有通知
    clearNotifications: (state) => {
      state.notifications = [];
    },

    // 標記通知為已讀
    markNotificationRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification) {
        // 可以添加已讀標記邏輯
      }
    },

    // 設置全局加載狀態
    setGlobalLoading: (state, action: PayloadAction<{ loading: boolean; text?: string }>) => {
      state.globalLoading = action.payload.loading;
      state.loadingText = action.payload.text;
    },

    // 設置特定加載狀態
    setLoading: (state, action: PayloadAction<{ key: string; loading: boolean }>) => {
      state.loading[action.payload.key] = action.payload.loading;
    },

    // 打開模態框
    openModal: (state, action: PayloadAction<string>) => {
      state.modals[action.payload] = true;
    },

    // 關閉模態框
    closeModal: (state, action: PayloadAction<string>) => {
      state.modals[action.payload] = false;
    },

    // 設置模態框狀態
    setModalOpen: (state, action: PayloadAction<{ key: string; open: boolean }>) => {
      state.modals[action.payload.key] = action.payload.open;
    },

    // 關閉所有模態框
    closeAllModals: (state) => {
      state.modals = {};
    },

    // 打開抽層
    openDrawer: (state, action: PayloadAction<string>) => {
      state.drawers[action.payload] = true;
    },

    // 關閉抽層
    closeDrawer: (state, action: PayloadAction<string>) => {
      state.drawers[action.payload] = false;
    },

    // 設置抽層狀態
    setDrawerOpen: (state, action: PayloadAction<{ key: string; open: boolean }>) => {
      state.drawers[action.payload.key] = action.payload.open;
    },

    // 關閉所有抽層
    closeAllDrawers: (state) => {
      state.drawers = {};
    },

    // 設置頁面標題
    setPageTitle: (state, action: PayloadAction<string>) => {
      state.pageTitle = action.payload;
      document.title = `${action.payload} - CBSC`;
    },

    // 設置面包屑
    setBreadcrumb: (state, action: PayloadAction<Array<{ title: string; path?: string }>>) => {
      state.breadcrumb = action.payload;
    },

    // 更新屏幕尺寸
    updateScreenSize: (state, action: PayloadAction<{ width: number; height: number }>) => {
      state.screenSize = action.payload;
      state.isMobile = action.payload.width < 768;
    },

    // 切換鍵盤快捷鍵
    toggleKeyboardShortcuts: (state) => {
      state.keyboardShortcuts.enabled = !state.keyboardShortcuts.enabled;
    },

    // 顯示/隱藏快捷鍵幫助
    setKeyboardShortcutsHelp: (state, action: PayloadAction<boolean>) => {
      state.keyboardShortcuts.helpVisible = action.payload;
    },

    // 打開全局搜索
    openGlobalSearch: (state) => {
      state.globalSearch.isOpen = true;
      state.globalSearch.query = '';
      state.globalSearch.results = [];
    },

    // 關閉全局搜索
    closeGlobalSearch: (state) => {
      state.globalSearch.isOpen = false;
    },

    // 設置搜索查詢
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.globalSearch.query = action.payload;
    },

    // 設置搜索結果
    setSearchResults: (state, action: PayloadAction<any[]>) => {
      state.globalSearch.results = action.payload;
    },

    // 切換快捷操作
    toggleQuickActions: (state) => {
      state.quickActions.visible = !state.quickActions.visible;
    },

    // 設置快捷操作
    setQuickActions: (state, action: PayloadAction<UIState['quickActions']['actions']>) => {
      state.quickActions.actions = action.payload;
    },

    // 設置分頁大小
    setPageSize: (state, action: PayloadAction<number>) => {
      state.pageSize = action.payload;
    },

    // 重置UI狀態
    resetUIState: () => getInitialState(),
  },
})

export const {
  setTheme,
  setLanguage,
  toggleSidebar,
  setSidebarOpen,
  toggleSidebarCollapse,
  setSidebarCollapsed,
  setActiveMenu,
  toggleMenuOpen,
  addNotification,
  removeNotification,
  clearNotifications,
  markNotificationRead,
  setGlobalLoading,
  setLoading,
  openModal,
  closeModal,
  setModalOpen,
  closeAllModals,
  openDrawer,
  closeDrawer,
  setDrawerOpen,
  closeAllDrawers,
  setPageTitle,
  setBreadcrumb,
  updateScreenSize,
  toggleKeyboardShortcuts,
  setKeyboardShortcutsHelp,
  openGlobalSearch,
  closeGlobalSearch,
  setSearchQuery,
  setSearchResults,
  toggleQuickActions,
  setQuickActions,
  setPageSize,
  resetUIState,
} = uiSlice.actions

// 選擇器
export const selectUI = (state: { ui: UIState }) => state.ui;
export const selectTheme = (state: { ui: UIState }) => state.ui.theme;
export const selectLanguage = (state: { ui: UIState }) => state.ui.language;
export const selectSidebar = (state: { ui: UIState }) => state.ui.sidebar;
export const selectNotifications = (state: { ui: UIState }) => state.ui.notifications;
export const selectGlobalLoading = (state: { ui: UIState }) => state.ui.globalLoading;
export const selectModals = (state: { ui: UIState }) => state.ui.modals;
export const selectDrawers = (state: { ui: UIState }) => state.ui.drawers;
export const selectPageTitle = (state: { ui: UIState }) => state.ui.pageTitle;
export const selectBreadcrumb = (state: { ui: UIState }) => state.ui.breadcrumb;
export const selectIsMobile = (state: { ui: UIState }) => state.ui.isMobile;
export const selectScreenSize = (state: { ui: UIState }) => state.ui.screenSize;
export const selectGlobalSearch = (state: { ui: UIState }) => state.ui.globalSearch;
export const selectQuickActions = (state: { ui: UIState }) => state.ui.quickActions;

// 複合選擇器
export const selectUnreadNotifications = (state: { ui: UIState }) =>
  state.ui.notifications.filter(n => !n.persistent);

export const selectModalOpen = (modalKey: string) => (state: { ui: UIState }) =>
  state.ui.modals[modalKey] || false;

export const selectDrawerOpen = (drawerKey: string) => (state: { ui: UIState }) =>
  state.ui.drawers[drawerKey] || false;

// 導出 reducer
export default uiSlice.reducer