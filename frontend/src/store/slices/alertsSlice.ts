/**
 * Redux slice for Alert Management
 * Handles alert rules, notifications, and history state
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  alertService,
  AlertRule,
  Alert,
  AlertAggregation,
  AlertHistory,
  AlertHistoryFilters,
  AlertStatistics
} from '../../services/alertService';

// Async thunks
export const createAlertRule = createAsyncThunk(
  'alerts/createRule',
  async (rule: Omit<AlertRule, 'id' | 'createdAt' | 'updatedAt'>) => {
    const response = await alertService.createRule(rule);
    return response;
  }
);

export const updateAlertRule = createAsyncThunk(
  'alerts/updateRule',
  async ({ id, updates }: { id: string; updates: Partial<AlertRule> }) => {
    const response = await alertService.updateRule(id, updates);
    return response;
  }
);

export const deleteAlertRule = createAsyncThunk(
  'alerts/deleteRule',
  async (id: string) => {
    await alertService.deleteRule(id);
    return id;
  }
);

export const acknowledgeAlert = createAsyncThunk(
  'alerts/acknowledgeAlert',
  async ({ alertId, userId }: { alertId: string; userId: string }) => {
    const success = await alertService.acknowledgeAlert(alertId, userId);
    return { alertId, success };
  }
);

export const resolveAlert = createAsyncThunk(
  'alerts/resolveAlert',
  async (alertId: string) => {
    const success = await alertService.resolveAlert(alertId);
    return { alertId, success };
  }
);

export const suppressAlert = createAsyncThunk(
  'alerts/suppressAlert',
  async (alertId: string) => {
    const success = await alertService.suppressAlert(alertId);
    return { alertId, success };
  }
);

export const loadAlertHistory = createAsyncThunk(
  'alerts/loadHistory',
  async (filters: AlertHistoryFilters) => {
    const history = alertService.getAlertHistory(filters);
    return history;
  }
);

// State interface
interface AlertsState {
  // Rules
  rules: AlertRule[];
  activeRules: AlertRule[];
  selectedRule: AlertRule | null;
  isRulesLoading: boolean;
  rulesError: string | null;

  // Active Alerts
  alerts: Alert[];
  aggregations: AlertAggregation[];
  unreadAlertsCount: number;
  isAlertsLoading: boolean;
  alertsError: string | null;

  // History
  history: AlertHistory | null;
  isHistoryLoading: boolean;
  historyError: string | null;

  // Filters
  activeFilters: AlertHistoryFilters;

  // UI State
  selectedAlert: Alert | null;
  isCreateRuleModalOpen: boolean;
  isAlertDetailsModalOpen: boolean;
  showAggregatedView: boolean;
}

// Initial state
const initialState: AlertsState = {
  // Rules
  rules: [],
  activeRules: [],
  selectedRule: null,
  isRulesLoading: false,
  rulesError: null,

  // Active Alerts
  alerts: [],
  aggregations: [],
  unreadAlertsCount: 0,
  isAlertsLoading: false,
  alertsError: null,

  // History
  history: null,
  isHistoryLoading: false,
  historyError: null,

  // Filters
  activeFilters: {
    dateRange: {
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date().toISOString()
    },
    priorities: ['critical', 'high', 'medium', 'low'],
    types: ['threshold', 'change_rate', 'pattern', 'anomaly'],
    sources: ['economic', 'strategy', 'portfolio'],
    status: ['active', 'acknowledged', 'resolved', 'suppressed']
  },

  // UI State
  selectedAlert: null,
  isCreateRuleModalOpen: false,
  isAlertDetailsModalOpen: false,
  showAggregatedView: false
};

// Slice
const alertsSlice = createSlice({
  name: 'alerts',
  initialState,
  reducers: {
    // Alert event handlers
    alertTriggered: (state, action: PayloadAction<Alert>) => {
      state.alerts.unshift(action.payload);
      state.unreadAlertsCount += 1;

      // Update statistics if history is loaded
      if (state.history) {
        state.history.statistics.total += 1;
        state.history.statistics.active += 1;
      }
    },

    // Rule selection
    selectRule: (state, action: PayloadAction<AlertRule | null>) => {
      state.selectedRule = action.payload;
    },

    // Alert selection
    selectAlert: (state, action: PayloadAction<Alert | null>) => {
      state.selectedAlert = action.payload;
    },

    // Modal controls
    openCreateRuleModal: (state) => {
      state.isCreateRuleModalOpen = true;
    },

    closeCreateRuleModal: (state) => {
      state.isCreateRuleModalOpen = false;
      state.selectedRule = null;
    },

    openAlertDetailsModal: (state, action: PayloadAction<Alert>) => {
      state.selectedAlert = action.payload;
      state.isAlertDetailsModalOpen = true;
    },

    closeAlertDetailsModal: (state) => {
      state.isAlertDetailsModalOpen = false;
      state.selectedAlert = null;
    },

    // View toggle
    toggleAggregatedView: (state) => {
      state.showAggregatedView = !state.showAggregatedView;
    },

    // Filters
    updateFilters: (state, action: PayloadAction<Partial<AlertHistoryFilters>>) => {
      state.activeFilters = { ...state.activeFilters, ...action.payload };
    },

    resetFilters: (state) => {
      state.activeFilters = {
        dateRange: {
          start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          end: new Date().toISOString()
        },
        priorities: ['critical', 'high', 'medium', 'low'],
        types: ['threshold', 'change_rate', 'pattern', 'anomaly'],
        sources: ['economic', 'strategy', 'portfolio'],
        status: ['active', 'acknowledged', 'resolved', 'suppressed']
      };
    },

    // Mark all alerts as read
    markAllAlertsAsRead: (state) => {
      state.unreadAlertsCount = 0;
    },

    // Clear resolved alerts
    clearResolvedAlerts: (state) => {
      state.alerts = state.alerts.filter(alert => alert.status !== 'resolved');
      state.aggregations = state.aggregations.filter(agg =>
        agg.alerts.some(alert => alert.status !== 'resolved')
      );
    },

    // Bulk actions
    bulkAcknowledgeAlerts: (state, action: PayloadAction<string[]>) => {
      action.payload.forEach(alertId => {
        const alert = state.alerts.find(a => a.id === alertId);
        if (alert && alert.status === 'active') {
          alert.status = 'acknowledged';
          alert.acknowledgedAt = new Date().toISOString();
        }
      });
    },

    bulkResolveAlerts: (state, action: PayloadAction<string[]>) => {
      action.payload.forEach(alertId => {
        const alert = state.alerts.find(a => a.id === alertId);
        if (alert) {
          alert.status = 'resolved';
          alert.resolvedAt = new Date().toISOString();
        }
      });
    },

    // Refresh data
    refreshRules: (state) => {
      state.rules = alertService.getRules();
      state.activeRules = alertService.getActiveRules();
    },

    refreshAlerts: (state) => {
      state.alerts = Array.from(alertService['alerts'].values());
      state.aggregations = Array.from(alertService['aggregations'].values());
    }
  },

  extraReducers: (builder) => {
    // Create rule
    builder
      .addCase(createAlertRule.pending, (state) => {
        state.isRulesLoading = true;
        state.rulesError = null;
      })
      .addCase(createAlertRule.fulfilled, (state, action) => {
        state.isRulesLoading = false;
        state.rules.push(action.payload);
        if (action.payload.isActive) {
          state.activeRules.push(action.payload);
        }
      })
      .addCase(createAlertRule.rejected, (state, action) => {
        state.isRulesLoading = false;
        state.rulesError = action.error.message || 'Failed to create alert rule';
      });

    // Update rule
    builder
      .addCase(updateAlertRule.pending, (state) => {
        state.isRulesLoading = true;
        state.rulesError = null;
      })
      .addCase(updateAlertRule.fulfilled, (state, action) => {
        state.isRulesLoading = false;
        if (action.payload) {
          const index = state.rules.findIndex(rule => rule.id === action.payload!.id);
          if (index !== -1) {
            state.rules[index] = action.payload;
          }

          // Update active rules
          state.activeRules = state.rules.filter(rule => rule.isActive);
        }
      })
      .addCase(updateAlertRule.rejected, (state, action) => {
        state.isRulesLoading = false;
        state.rulesError = action.error.message || 'Failed to update alert rule';
      });

    // Delete rule
    builder
      .addCase(deleteAlertRule.pending, (state) => {
        state.isRulesLoading = true;
        state.rulesError = null;
      })
      .addCase(deleteAlertRule.fulfilled, (state, action) => {
        state.isRulesLoading = false;
        state.rules = state.rules.filter(rule => rule.id !== action.payload);
        state.activeRules = state.activeRules.filter(rule => rule.id !== action.payload);
      })
      .addCase(deleteAlertRule.rejected, (state, action) => {
        state.isRulesLoading = false;
        state.rulesError = action.error.message || 'Failed to delete alert rule';
      });

    // Acknowledge alert
    builder
      .addCase(acknowledgeAlert.fulfilled, (state, action) => {
        if (action.payload.success) {
          const alert = state.alerts.find(a => a.id === action.payload.alertId);
          if (alert) {
            alert.status = 'acknowledged';
            alert.acknowledgedAt = new Date().toISOString();
          }
        }
      });

    // Resolve alert
    builder
      .addCase(resolveAlert.fulfilled, (state, action) => {
        if (action.payload.success) {
          const alert = state.alerts.find(a => a.id === action.payload.alertId);
          if (alert) {
            alert.status = 'resolved';
            alert.resolvedAt = new Date().toISOString();
          }
        }
      });

    // Suppress alert
    builder
      .addCase(suppressAlert.fulfilled, (state, action) => {
        if (action.payload.success) {
          const alert = state.alerts.find(a => a.id === action.payload.alertId);
          if (alert) {
            alert.status = 'suppressed';
          }
        }
      });

    // Load history
    builder
      .addCase(loadAlertHistory.pending, (state) => {
        state.isHistoryLoading = true;
        state.historyError = null;
      })
      .addCase(loadAlertHistory.fulfilled, (state, action) => {
        state.isHistoryLoading = false;
        state.history = action.payload;
      })
      .addCase(loadAlertHistory.rejected, (state, action) => {
        state.isHistoryLoading = false;
        state.historyError = action.error.message || 'Failed to load alert history';
      });
  }
});

// Export actions
export const {
  alertTriggered,
  selectRule,
  selectAlert,
  openCreateRuleModal,
  closeCreateRuleModal,
  openAlertDetailsModal,
  closeAlertDetailsModal,
  toggleAggregatedView,
  updateFilters,
  resetFilters,
  markAllAlertsAsRead,
  clearResolvedAlerts,
  bulkAcknowledgeAlerts,
  bulkResolveAlerts,
  refreshRules,
  refreshAlerts
} = alertsSlice.actions;

// Selectors
export const selectAlertRules = (state: { alerts: AlertsState }) => state.alerts.rules;
export const selectActiveAlertRules = (state: { alerts: AlertsState }) => state.alerts.activeRules;
export const selectSelectedRule = (state: { alerts: AlertsState }) => state.alerts.selectedRule;

export const selectAlerts = (state: { alerts: AlertsState }) => state.alerts.alerts;
export const selectAggregations = (state: { alerts: AlertsState }) => state.alerts.aggregations;
export const selectUnreadAlertsCount = (state: { alerts: AlertsState }) => state.alerts.unreadAlertsCount;
export const selectSelectedAlert = (state: { alerts: AlertsState }) => state.alerts.selectedAlert;

export const selectAlertHistory = (state: { alerts: AlertsState }) => state.alerts.history;
export const selectAlertFilters = (state: { alerts: AlertsState }) => state.alerts.activeFilters;

export const selectAlertStatistics = (state: { alerts: AlertsState }) =>
  state.alerts.history?.statistics || null;

export const selectRulesLoading = (state: { alerts: AlertsState }) => state.alerts.isRulesLoading;
export const selectAlertsLoading = (state: { alerts: AlertsState }) => state.alerts.isAlertsLoading;
export const selectHistoryLoading = (state: { alerts: AlertsState }) => state.alerts.isHistoryLoading;

export const selectRulesError = (state: { alerts: AlertsState }) => state.alerts.rulesError;
export const selectAlertsError = (state: { alerts: AlertsState }) => state.alerts.alertsError;
export const selectHistoryError = (state: { alerts: AlertsState }) => state.alerts.historyError;

export const selectCreateRuleModalOpen = (state: { alerts: AlertsState }) =>
  state.alerts.isCreateRuleModalOpen;
export const selectAlertDetailsModalOpen = (state: { alerts: AlertsState }) =>
  state.alerts.isAlertDetailsModalOpen;
export const selectShowAggregatedView = (state: { alerts: AlertsState }) =>
  state.alerts.showAggregatedView;

// Derived selectors
export const selectActiveAlerts = (state: { alerts: AlertsState }) =>
  state.alerts.alerts.filter(alert => alert.status === 'active');

export const selectCriticalAlerts = (state: { alerts: AlertsState }) =>
  state.alerts.alerts.filter(alert => alert.priority === 'critical' && alert.status === 'active');

export const selectHighPriorityAlerts = (state: { alerts: AlertsState }) =>
  state.alerts.alerts.filter(alert =>
    ['critical', 'high'].includes(alert.priority) && alert.status === 'active'
  );

export const selectFilteredAlerts = (state: { alerts: AlertsState }) => {
  const { alerts } = state.alerts;
  const filters = state.alerts.activeFilters;

  return alerts.filter(alert => {
    // Date range filter
    if (filters.dateRange) {
      const alertTime = new Date(alert.triggeredAt).getTime();
      const start = new Date(filters.dateRange.start).getTime();
      const end = new Date(filters.dateRange.end).getTime();
      if (alertTime < start || alertTime > end) return false;
    }

    // Priority filter
    if (filters.priorities.length > 0 && !filters.priorities.includes(alert.priority)) {
      return false;
    }

    // Type filter
    if (filters.types.length > 0 && !filters.types.includes(alert.type)) {
      return false;
    }

    // Source filter
    if (filters.sources.length > 0 && !filters.sources.includes(alert.source)) {
      return false;
    }

    // Status filter
    if (filters.status.length > 0 && !filters.status.includes(alert.status)) {
      return false;
    }

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        alert.title.toLowerCase().includes(searchLower) ||
        alert.message.toLowerCase().includes(searchLower) ||
        alert.ruleName.toLowerCase().includes(searchLower)
      );
    }

    return true;
  });
};

// Export reducer
export default alertsSlice.reducer;