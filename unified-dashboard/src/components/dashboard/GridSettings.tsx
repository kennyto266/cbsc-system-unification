import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Card,
  Button,
  Space,
  Select,
  Switch,
  Slider,
  Input,
  Divider,
  Tooltip,
  Dropdown,
  MenuProps
} from 'antd'
import {
  SettingOutlined,
  LockOutlined,
  UnlockOutlined,
  EditOutlined,
  SaveOutlined,
  ReloadOutlined,
  ClearOutlined,
  CopyOutlined,
  ImportOutlined,
  ExportOutlined,
  LayoutOutlined,
  AppstoreOutlined,
  FullscreenOutlined,
  CompressOutlined,
  UndoOutlined,
  RedoOutlined,
  MoreOutlined
} from '@ant-design/icons'
import { useGridLayout } from '../../hooks/dashboard/useGridLayout'

const { Option } = Select
const { TextArea } = Input

const GridSettings: React.FC = () => {
  const {
    layout,
    isEditMode,
    selectedWidgets,
    canUndo,
    canRedo,
    hasSelection,
    stats,
    toggleEditMode,
    resetLayout,
    clearLayout,
    lockLayout,
    unlockLayout,
    undo,
    redo,
    selectAllWidgets,
    clearSelection,
    deleteSelected,
    exportCurrentLayout,
    importLayoutData,
  } = useGridLayout()

  const [importModalVisible, setImportModalVisible] = useState(false)
  const [importData, setImportData] = useState('')
  const [exportModalVisible, setExportModalVisible] = useState(false)
  const [exportData, setExportData] = useState('')

  // Handle layout export
  const handleExport = useCallback(() => {
    const data = exportCurrentLayout()
    setExportData(data)
    setExportModalVisible(true)
  }, [exportCurrentLayout])

  // Handle layout import
  const handleImport = useCallback(() => {
    if (importData.trim()) {
      importLayoutData(importData)
      setImportModalVisible(false)
      setImportData('')
    }
  }, [importData, importLayoutData])

  // Quick actions menu
  const quickActionsMenu: MenuProps['items'] = [
    {
      key: 'compact',
      label: 'Compact Layout',
      icon: <CompressOutlined />,
      onClick: () => console.log('Compact layout'),
    },
    {
      key: 'expand',
      label: 'Expand Layout',
      icon: <FullscreenOutlined />,
      onClick: () => console.log('Expand layout'),
    },
    {
      type: 'divider',
    },
    {
      key: 'duplicate',
      label: 'Duplicate Layout',
      icon: <CopyOutlined />,
      onClick: () => console.log('Duplicate layout'),
    },
    {
      key: 'saveAs',
      label: 'Save As...',
      icon: <SaveOutlined />,
      onClick: () => console.log('Save as layout'),
    },
  ]

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: -10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: -10 }}
        transition={{ duration: 0.2 }}
      >
        <Card
          title="Grid Settings"
          size="small"
          className="w-80 shadow-lg"
          extra={
            <Button
              type="text"
              size="small"
              icon={<MoreOutlined />}
              onClick={() => console.log('More options')}
            />
          }
        >
          {/* Edit Mode Toggle */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Edit Mode</span>
              <Switch
                checked={isEditMode}
                onChange={toggleEditMode}
                checkedChildren={<EditOutlined />}
                unCheckedChildren={<LayoutOutlined />}
              />
            </div>
            {isEditMode && (
              <p className="text-xs text-gray-500">
                Drag and resize widgets to customize your dashboard
              </p>
            )}
          </div>

          <Divider className="my-3" />

          {/* Layout Controls */}
          <div className="space-y-3">
            {/* Lock/Unlock */}
            <div className="flex items-center justify-between">
              <span className="text-sm">Lock Layout</span>
              <Button
                type={layout.isLocked ? 'primary' : 'default'}
                size="small"
                icon={layout.isLocked ? <LockOutlined /> : <UnlockOutlined />}
                onClick={layout.isLocked ? unlockLayout : lockLayout}
              >
                {layout.isLocked ? 'Locked' : 'Unlocked'}
              </Button>
            </div>

            {/* Undo/Redo */}
            <div className="flex gap-2">
              <Tooltip title="Undo (Ctrl+Z)">
                <Button
                  size="small"
                  icon={<UndoOutlined />}
                  disabled={!canUndo}
                  onClick={undo}
                />
              </Tooltip>
              <Tooltip title="Redo (Ctrl+Y)">
                <Button
                  size="small"
                  icon={<RedoOutlined />}
                  disabled={!canRedo}
                  onClick={redo}
                />
              </Tooltip>
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={resetLayout}
              >
                Reset
              </Button>
              <Button
                size="small"
                icon={<ClearOutlined />}
                onClick={clearLayout}
                danger
              >
                Clear
              </Button>
            </div>

            {/* Selection Controls */}
            {isEditMode && (
              <div className="flex gap-2">
                <Button
                  size="small"
                  icon={<AppstoreOutlined />}
                  onClick={selectAllWidgets}
                >
                  Select All
                </Button>
                <Button
                  size="small"
                  onClick={clearSelection}
                  disabled={!hasSelection}
                >
                  Clear
                </Button>
                <Button
                  size="small"
                  danger
                  disabled={!hasSelection}
                  onClick={deleteSelected}
                >
                  Delete
                </Button>
              </div>
            )}
          </div>

          <Divider className="my-3" />

          {/* Layout Statistics */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Layout Info</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-500">Widgets:</span>
                <span className="ml-1 font-medium">{stats.totalWidgets}</span>
              </div>
              <div>
                <span className="text-gray-500">Visible:</span>
                <span className="ml-1 font-medium">{stats.visibleWidgets}</span>
              </div>
              <div>
                <span className="text-gray-500">Minimized:</span>
                <span className="ml-1 font-medium">{stats.minimizedWidgets}</span>
              </div>
              <div>
                <span className="text-gray-500">Selected:</span>
                <span className="ml-1 font-medium">{selectedWidgets.length}</span>
              </div>
              <div className="col-span-2">
                <span className="text-gray-500">Utilization:</span>
                <span className="ml-1 font-medium">{stats.utilizationRate.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          <Divider className="my-3" />

          {/* Import/Export */}
          <div className="space-y-2">
            <div className="flex gap-2">
              <Button
                size="small"
                icon={<ExportOutlined />}
                onClick={handleExport}
                className="flex-1"
              >
                Export
              </Button>
              <Button
                size="small"
                icon={<ImportOutlined />}
                onClick={() => setImportModalVisible(true)}
                className="flex-1"
              >
                Import
              </Button>
            </div>

            {/* Quick Actions Dropdown */}
            <Dropdown
              menu={{ items: quickActionsMenu }}
              trigger={['click']}
              placement="bottomLeft"
            >
              <Button size="small" icon={<MoreOutlined />} className="w-full">
                More Actions
              </Button>
            </Dropdown>
          </div>
        </Card>
      </motion.div>

      {/* Export Modal */}
      <AnimatePresence>
        {exportModalVisible && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setExportModalVisible(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold mb-4">Export Layout</h3>
              <TextArea
                value={exportData}
                readOnly
                rows={10}
                className="mb-4"
              />
              <div className="flex justify-end gap-2">
                <Button onClick={() => setExportModalVisible(false)}>
                  Close
                </Button>
                <Button
                  type="primary"
                  onClick={() => {
                    navigator.clipboard.writeText(exportData)
                    console.log('Copied to clipboard')
                  }}
                >
                  Copy to Clipboard
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Import Modal */}
      <AnimatePresence>
        {importModalVisible && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setImportModalVisible(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold mb-4">Import Layout</h3>
              <TextArea
                value={importData}
                onChange={(e) => setImportData(e.target.value)}
                placeholder="Paste your layout JSON here..."
                rows={10}
                className="mb-4"
              />
              <div className="flex justify-end gap-2">
                <Button onClick={() => setImportModalVisible(false)}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  onClick={handleImport}
                  disabled={!importData.trim()}
                >
                  Import
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </AnimatePresence>
  )
}

export default GridSettings