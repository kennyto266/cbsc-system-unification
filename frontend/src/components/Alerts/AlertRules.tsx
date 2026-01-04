/**
 * AlertRules Component
 * Configure and manage alert rules for economic indicators and strategies
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../../store';
import {
  AlertRule,
  AlertCondition,
  AlertRuleType,
  AlertRuleSource,
  AlertPriority
} from '../../services/alertService';
import {
  selectAlertRules,
  selectSelectedRule,
  selectRulesLoading,
  selectRulesError,
  selectActiveAlertRules,
  selectCreateRuleModalOpen,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
  openCreateRuleModal,
  closeCreateRuleModal,
  selectRule
} from '../../store/slices/alertsSlice';

interface AlertRulesProps {
  className?: string;
  showInactive?: boolean;
  allowCreate?: boolean;
  allowEdit?: boolean;
  allowDelete?: boolean;
}

const AlertRules: React.FC<AlertRulesProps> = ({
  className = '',
  showInactive = true,
  allowCreate = true,
  allowEdit = true,
  allowDelete = true
}) => {
  const dispatch = useDispatch<AppDispatch>();

  // Selectors
  const rules = useSelector(selectAlertRules);
  const selectedRule = useSelector(selectSelectedRule);
  const isLoading = useSelector(selectRulesLoading);
  const error = useSelector(selectRulesError);
  const activeRules = useSelector(selectActiveAlertRules);
  const isModalOpen = useSelector(selectCreateRuleModalOpen);

  // Local state
  const [filterSource, setFilterSource] = useState<AlertRuleSource | 'all'>('all');
  const [filterType, setFilterType] = useState<AlertRuleType | 'all'>('all');
  const [filterPriority, setFilterPriority] = useState<AlertPriority | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Form state
  const [formData, setFormData] = useState<Partial<AlertRule>>({
    name: '',
    description: '',
    type: 'threshold',
    source: 'economic',
    priority: 'medium',
    conditions: [],
    isActive: true
  });

  // Current condition being edited
  const [currentCondition, setCurrentCondition] = useState<AlertCondition>({
    field: '',
    operator: '>',
    value: 0
  });

  // Available fields for different sources
  const availableFields: Record<AlertRuleSource, string[]> = {
    economic: [
      'inflation_rate',
      'unemployment_rate',
      'gdp_growth',
      'interest_rate',
      'cpi_index',
      'pmi_index',
      'retail_sales',
      'consumer_confidence',
      'trade_balance',
      'housing_starts'
    ],
    strategy: [
      'performance',
      'sharpe_ratio',
      'max_drawdown',
      'win_rate',
      'profit_factor',
      'calmar_ratio',
      'sortino_ratio',
      'volatility',
      'beta',
      'alpha'
    ],
    portfolio: [
      'total_value',
      'daily_return',
      'position_count',
      'sector_exposure',
      'cash_ratio',
      'leverage_ratio',
      'var',
      'correlation',
      'concentration'
    ]
  };

  // Filter rules
  const filteredRules = rules.filter(rule => {
    if (filterSource !== 'all' && rule.source !== filterSource) return false;
    if (filterType !== 'all' && rule.type !== filterType) return false;
    if (filterPriority !== 'all' && rule.priority !== filterPriority) return false;
    if (searchTerm && !rule.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    if (!showInactive && !rule.isActive) return false;
    return true;
  });

  // Event handlers
  const handleCreateRule = useCallback(() => {
    dispatch(openCreateRuleModal());
    setFormData({
      name: '',
      description: '',
      type: 'threshold',
      source: 'economic',
      priority: 'medium',
      conditions: [],
      isActive: true
    });
  }, [dispatch]);

  const handleEditRule = useCallback((rule: AlertRule) => {
    dispatch(selectRule(rule));
    setFormData({
      ...rule,
      conditions: [...rule.conditions]
    });
  }, [dispatch]);

  const handleDeleteRule = useCallback(async (ruleId: string) => {
    if (window.confirm('Are you sure you want to delete this alert rule?')) {
      await dispatch(deleteRule(ruleId));
    }
  }, [dispatch]);

  const handleToggleRule = useCallback(async (rule: AlertRule) => {
    await dispatch(updateAlertRule({
      id: rule.id,
      updates: { isActive: !rule.isActive }
    }));
  }, [dispatch]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name || formData.conditions?.length === 0) {
      alert('Please provide a name and at least one condition');
      return;
    }

    try {
      if (selectedRule) {
        await dispatch(updateAlertRule({
          id: selectedRule.id,
          updates: formData
        }));
      } else {
        await dispatch(createAlertRule(formData as Omit<AlertRule, 'id' | 'createdAt' | 'updatedAt' | 'userId'>));
      }
      dispatch(closeCreateRuleModal());
    } catch (error) {
      console.error('Failed to save alert rule:', error);
    }
  }, [formData, selectedRule, dispatch]);

  const handleAddCondition = useCallback(() => {
    if (!currentCondition.field || currentCondition.operator === undefined) {
      alert('Please fill in all condition fields');
      return;
    }

    setFormData(prev => ({
      ...prev,
      conditions: [...(prev.conditions || []), { ...currentCondition }]
    }));

    // Reset condition form
    setCurrentCondition({
      field: '',
      operator: '>',
      value: 0
    });
  }, [currentCondition]);

  const handleRemoveCondition = useCallback((index: number) => {
    setFormData(prev => ({
      ...prev,
      conditions: prev.conditions?.filter((_, i) => i !== index) || []
    }));
  }, []);

  // Render helpers
  const getSourceIcon = (source: AlertRuleSource): string => {
    switch (source) {
      case 'economic':
        return '📊';
      case 'strategy':
        return '🎯';
      case 'portfolio':
        return '💼';
      default:
        return '📈';
    }
  };

  const getTypeLabel = (type: AlertRuleType): string => {
    switch (type) {
      case 'threshold':
        return 'Threshold';
      case 'change_rate':
        return 'Change Rate';
      case 'pattern':
        return 'Pattern';
      case 'anomaly':
        return 'Anomaly';
      default:
        return type;
    }
  };

  const getOperatorLabel = (operator: string): string => {
    switch (operator) {
      case '>':
        return 'Greater than';
      case '<':
        return 'Less than';
      case '=':
        return 'Equals';
      case '>=':
        return 'Greater or equal';
      case '<=':
        return 'Less or equal';
      case '!=':
        return 'Not equal';
      case 'change_pct':
        return 'Change %';
      case 'deviation':
        return 'Deviation';
      default:
        return operator;
    }
  };

  // Render rule form modal
  const renderRuleForm = () => {
    if (!isModalOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-bold mb-4">
            {selectedRule ? 'Edit Alert Rule' : 'Create Alert Rule'}
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rule Name *
                </label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <select
                  value={formData.priority || 'medium'}
                  onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value as AlertPriority }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Source
                </label>
                <select
                  value={formData.source || 'economic'}
                  onChange={(e) => setFormData(prev => ({ ...prev, source: e.target.value as AlertRuleSource }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="economic">Economic</option>
                  <option value="strategy">Strategy</option>
                  <option value="portfolio">Portfolio</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type
                </label>
                <select
                  value={formData.type || 'threshold'}
                  onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value as AlertRuleType }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="threshold">Threshold</option>
                  <option value="change_rate">Change Rate</option>
                  <option value="pattern">Pattern</option>
                  <option value="anomaly">Anomaly</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="isActive"
                  checked={formData.isActive !== false}
                  onChange={(e) => setFormData(prev => ({ ...prev, isActive: e.target.checked }))}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="isActive" className="ml-2 text-sm text-gray-700">
                  Active
                </label>
              </div>
            </div>

            {/* Conditions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Conditions
              </label>

              <div className="space-y-2 mb-3">
                {formData.conditions?.map((condition, index) => (
                  <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                    <span className="flex-1 text-sm">
                      {condition.field} {getOperatorLabel(condition.operator)} {condition.value}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveCondition(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>

              {/* Add new condition */}
              <div className="grid grid-cols-4 gap-2">
                <select
                  value={currentCondition.field}
                  onChange={(e) => setCurrentCondition(prev => ({ ...prev, field: e.target.value }))}
                  className="px-2 py-1 border border-gray-300 rounded text-sm"
                >
                  <option value="">Select field...</option>
                  {availableFields[formData.source as AlertRuleSource || 'economic']?.map(field => (
                    <option key={field} value={field}>{field}</option>
                  ))}
                </select>

                <select
                  value={currentCondition.operator}
                  onChange={(e) => setCurrentCondition(prev => ({ ...prev, operator: e.target.value as any }))}
                  className="px-2 py-1 border border-gray-300 rounded text-sm"
                >
                  <option value=">">{getOperatorLabel('>')}</option>
                  <option value="<">{getOperatorLabel('<')}</option>
                  <option value=">=">{getOperatorLabel('>=')}</option>
                  <option value="<=">{getOperatorLabel('<=')}</option>
                  <option value="=">{getOperatorLabel('=')}</option>
                  <option value="!=">{getOperatorLabel('!=')}</option>
                  <option value="change_pct">{getOperatorLabel('change_pct')}</option>
                  <option value="deviation">{getOperatorLabel('deviation')}</option>
                </select>

                <input
                  type="number"
                  value={currentCondition.value}
                  onChange={(e) => setCurrentCondition(prev => ({ ...prev, value: Number(e.target.value) }))}
                  className="px-2 py-1 border border-gray-300 rounded text-sm"
                  placeholder="Value"
                />

                <button
                  type="button"
                  onClick={handleAddCondition}
                  className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                >
                  Add
                </button>
              </div>
            </div>

            {/* Form actions */}
            <div className="flex justify-end gap-2 pt-4">
              <button
                type="button"
                onClick={() => dispatch(closeCreateRuleModal())}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {selectedRule ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Render rule item
  const renderRule = (rule: AlertRule) => {
    const statusColor = rule.isActive ? 'text-green-600' : 'text-gray-500';
    const priorityColor = {
      critical: 'text-red-600',
      high: 'text-orange-600',
      medium: 'text-yellow-600',
      low: 'text-blue-600'
    }[rule.priority];

    return (
      <div key={rule.id} className="bg-white rounded-lg shadow p-4 mb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{getSourceIcon(rule.source)}</span>
              <h4 className="font-semibold">{rule.name}</h4>
              <span className={`text-sm ${priorityColor} font-medium`}>
                {rule.priority.toUpperCase()}
              </span>
              <span className={`text-sm ${statusColor}`}>
                {rule.isActive ? '● Active' : '○ Inactive'}
              </span>
            </div>

            {rule.description && (
              <p className="text-sm text-gray-600 mb-2">{rule.description}</p>
            )}

            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Type: {getTypeLabel(rule.type)}</span>
              <span>Source: {rule.source}</span>
              <span>Conditions: {rule.conditions.length}</span>
              <span>Created: {new Date(rule.createdAt).toLocaleDateString()}</span>
            </div>

            {/* Conditions preview */}
            {rule.conditions.length > 0 && (
              <div className="mt-3 p-2 bg-gray-50 rounded text-sm">
                {rule.conditions.map((condition, index) => (
                  <div key={index}>
                    {condition.field} {getOperatorLabel(condition.operator)} {condition.value}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-2 ml-4">
            {allowEdit && (
              <button
                onClick={() => handleEditRule(rule)}
                className="text-blue-600 hover:text-blue-800"
              >
                Edit
              </button>
            )}
            {allowDelete && (
              <button
                onClick={() => handleDeleteRule(rule.id)}
                className="text-red-600 hover:text-red-800"
              >
                Delete
              </button>
            )}
            <button
              onClick={() => handleToggleRule(rule)}
              className={`px-3 py-1 text-sm rounded ${
                rule.isActive
                  ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                  : 'bg-green-100 text-green-800 hover:bg-green-200'
              }`}
            >
              {rule.isActive ? 'Deactivate' : 'Activate'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`alert-rules ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-bold">Alert Rules</h2>
          {allowCreate && (
            <button
              onClick={handleCreateRule}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Create Rule
            </button>
          )}
        </div>

        <div className="flex gap-4 text-sm">
          <span className="text-green-600 font-medium">
            {activeRules.length} Active
          </span>
          <span className="text-gray-600">
            {rules.length} Total
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Search rules..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <select
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value as AlertRuleSource | 'all')}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Sources</option>
            <option value="economic">Economic</option>
            <option value="strategy">Strategy</option>
            <option value="portfolio">Portfolio</option>
          </select>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as AlertRuleType | 'all')}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="threshold">Threshold</option>
            <option value="change_rate">Change Rate</option>
            <option value="pattern">Pattern</option>
            <option value="anomaly">Anomaly</option>
          </select>

          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value as AlertPriority | 'all')}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      {/* Rules list */}
      <div className="space-y-2">
        {filteredRules.length > 0 ? (
          filteredRules.map(renderRule)
        ) : (
          <div className="text-center py-8 text-gray-500">
            No alert rules found
          </div>
        )}
      </div>

      {/* Create/Edit modal */}
      {renderRuleForm()}

      {/* Loading overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center z-40">
          <div className="bg-white rounded-lg p-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertRules;