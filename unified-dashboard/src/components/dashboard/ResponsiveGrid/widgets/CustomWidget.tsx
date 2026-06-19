import React, { useState, useEffect, useMemo } from 'react'
import { Card, Input, Button, Space, Select, Alert, Spin } from 'antd'
import { CodeOutlined, PlayCircleOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons'

const { TextArea } = Input
const { Option } = Select

// Custom widget component types
const WIDGET_TYPES = [
  { value: 'html', label: 'HTML内容' },
  { value: 'markdown', label: 'Markdown内容' },
  { value: 'iframe', label: '嵌入页面' },
  { value: 'json-viewer', label: 'JSON查看器' },
  { value: 'code-editor', label: '代码编辑器' },
  { value: 'custom-chart', label: '自定义图表' }
]

// Template examples
const WIDGET_TEMPLATES = {
  html: {
    name: 'HTML内容',
    template: `<div style="padding: 20px; text-align: center;">
  <h2>自定义HTML组件</h2>
  <p>这里可以放置任何HTML内容</p>
  <button onclick="alert('Hello from custom widget!')">点击我</button>
</div>`
  },
  markdown: {
    name: 'Markdown内容',
    template: `# 自定义Markdown组件

这是一个使用**Markdown**格式的内容示例。

## 功能特性
- 支持标准Markdown语法
- 可以嵌入代码块
- 支持表格和列表

### 代码示例
\`\`\`javascript
const message = "Hello, Custom Widget!";
console.log(message);
\`\`\`

> 这是一个引用块

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| 1   | 2   | 3   |`
  },
  iframe: {
    name: '嵌入页面',
    template: 'https://www.example.com'
  }
}

interface CustomWidgetProps {
  widgetId: string
  config?: {
    type?: string
    content?: string
    url?: string
    editable?: boolean
    autoRefresh?: boolean
    refreshInterval?: number
  }
  data?: any
}

const CustomWidget: React.FC<CustomWidgetProps> = ({
  widgetId,
  config = {},
  data
}) => {
  const [widgetConfig, setWidgetConfig] = useState({
    type: config.type || 'html',
    content: config.content || '',
    url: config.url || '',
    editable: config.editable !== false,
    autoRefresh: config.autoRefresh || false,
    refreshInterval: config.refreshInterval || 30000
  })

  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState(widgetConfig.content)
  const [loading, setLoading] = useState(false)

  // Update widget config when props change
  useEffect(() => {
    setWidgetConfig({
      type: config.type || 'html',
      content: config.content || '',
      url: config.url || '',
      editable: config.editable !== false,
      autoRefresh: config.autoRefresh || false,
      refreshInterval: config.refreshInterval || 30000
    })
    setEditContent(config.content || '')
  }, [config])

  // Auto refresh functionality
  useEffect(() => {
    if (!widgetConfig.autoRefresh) return

    const interval = setInterval(() => {
      if (widgetConfig.type === 'iframe' && widgetConfig.url) {
        // Refresh iframe by forcing reload
        const iframe = document.getElementById(`iframe-${widgetId}`) as HTMLIFrameElement
        if (iframe) {
          iframe.src = iframe.src
        }
      }
    }, widgetConfig.refreshInterval)

    return () => clearInterval(interval)
  }, [widgetConfig.autoRefresh, widgetConfig.refreshInterval, widgetConfig.type, widgetConfig.url, widgetId])

  // Handle widget type change
  const handleTypeChange = (type: string) => {
    const template = WIDGET_TEMPLATES[type as keyof typeof WIDGET_TEMPLATES]
    const newConfig = {
      ...widgetConfig,
      type,
      content: template?.template || '',
      url: type === 'iframe' ? 'https://www.example.com' : widgetConfig.url
    }
    setWidgetConfig(newConfig)
    setEditContent(newConfig.content)
  }

  // Handle save edit
  const handleSaveEdit = () => {
    setWidgetConfig({
      ...widgetConfig,
      content: editContent
    })
    setIsEditing(false)

    // Save to localStorage or send to backend
    try {
      localStorage.setItem(`custom-widget-${widgetId}`, JSON.stringify({
        ...widgetConfig,
        content: editContent,
        lastUpdated: new Date().toISOString()
      }))
    } catch (error) {
      console.error('Failed to save widget config:', error)
    }
  }

  // Handle template selection
  const handleTemplateSelect = (templateName: string) => {
    const template = WIDGET_TEMPLATES[templateName as keyof typeof WIDGET_TEMPLATES]
    if (template) {
      setEditContent(template.template)
    }
  }

  // Render widget content based on type
  const renderContent = () => {
    switch (widgetConfig.type) {
      case 'html':
        return (
          <div
            dangerouslySetInnerHTML={{ __html: widgetConfig.content }}
            className="custom-html-content"
          />
        )

      case 'markdown':
        // In a real implementation, you would use a markdown renderer like react-markdown
        return (
          <div className="custom-markdown-content prose dark:prose-invert max-w-none">
            <pre className="whitespace-pre-wrap">{widgetConfig.content}</pre>
          </div>
        )

      case 'iframe':
        return (
          <iframe
            id={`iframe-${widgetId}`}
            src={widgetConfig.url}
            className="w-full h-full border-0"
            sandbox="allow-scripts allow-same-origin allow-forms"
            title="Custom Content"
          />
        )

      case 'json-viewer':
        try {
          const jsonData = data ? JSON.stringify(data, null, 2) : widgetConfig.content
          return (
            <pre className="json-viewer bg-gray-100 dark:bg-gray-800 p-4 rounded overflow-auto">
              <code>{jsonData}</code>
            </pre>
          )
        } catch (error) {
          return (
            <Alert
              message="JSON格式错误"
              description="无法解析JSON内容"
              type="error"
              showIcon
            />
          )
        }

      case 'code-editor':
        return (
          <div className="code-editor">
            <pre className="bg-gray-900 text-gray-100 p-4 rounded overflow-auto">
              <code>{widgetConfig.content || '// 在此处编写代码'}</code>
            </pre>
          </div>
        )

      case 'custom-chart':
        // In a real implementation, you would render a chart based on the data
        return (
          <div className="custom-chart">
            <Alert
              message="自定义图表"
              description="图表内容将在此处显示"
              type="info"
              showIcon
            />
          </div>
        )

      default:
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <CodeOutlined className="text-4xl mb-2" />
              <div>未知组件类型</div>
            </div>
          </div>
        )
    }
  }

  // Render editor mode
  const renderEditor = () => {
    return (
      <div className="custom-widget-editor h-full flex flex-col">
        <div className="editor-toolbar p-2 border-b dark:border-gray-700">
          <Space>
            <Select
              value={widgetConfig.type}
              onChange={handleTypeChange}
              style={{ width: 150 }}
              size="small"
            >
              {WIDGET_TYPES.map(type => (
                <Option key={type.value} value={type.value}>
                  {type.label}
                </Option>
              ))}
            </Select>

            {widgetConfig.type !== 'iframe' && (
              <Select
                placeholder="选择模板"
                style={{ width: 150 }}
                size="small"
                onChange={handleTemplateSelect}
              >
                {Object.entries(WIDGET_TEMPLATES).map(([key, template]) => (
                  <Option key={key} value={key}>{template.name}</Option>
                ))}
              </Select>
            )}

            <Button
              type="primary"
              size="small"
              icon={<SaveOutlined />}
              onClick={handleSaveEdit}
            >
              保存
            </Button>

            <Button
              size="small"
              onClick={() => {
                setIsEditing(false)
                setEditContent(widgetConfig.content)
              }}
            >
              取消
            </Button>
          </Space>
        </div>

        <div className="editor-content flex-1">
          {widgetConfig.type === 'iframe' ? (
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">URL地址:</label>
                <Input
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  placeholder="输入要嵌入的URL"
                />
              </div>
            </div>
          ) : (
            <TextArea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              placeholder="输入内容..."
              className="h-full border-0 resize-none focus:shadow-none"
              style={{ fontFamily: 'monospace' }}
            />
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="custom-widget h-full flex flex-col">
      {/* Widget toolbar */}
      {widgetConfig.editable && (
        <div className="widget-toolbar p-2 border-b dark:border-gray-700 flex items-center justify-between">
          <div className="text-sm font-medium">
            {WIDGET_TYPES.find(t => t.value === widgetConfig.type)?.label}
          </div>

          <Space size="small">
            {!isEditing && (
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={() => setIsEditing(true)}
              >
                编辑
              </Button>
            )}
          </Space>
        </div>
      )}

      {/* Widget content */}
      <div className="widget-content flex-1 min-h-0">
        {isEditing ? (
          renderEditor()
        ) : (
          <div className="h-full">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <Spin tip="加载中..." />
              </div>
            ) : (
              renderContent()
            )}
          </div>
        )}
      </div>

      {/* Widget footer */}
      <div className="widget-footer p-2 border-t dark:border-gray-700 text-xs text-gray-500 flex items-center justify-between">
        <span>自定义组件</span>
        <Space size="small">
          {widgetConfig.autoRefresh && <span className="text-green-500">自动刷新</span>}
          <span>ID: {widgetId}</span>
        </Space>
      </div>

      <style jsx>{`
        .custom-html-content {
          padding: 16px;
          overflow: auto;
        }

        .custom-markdown-content {
          padding: 16px;
          overflow: auto;
        }

        .json-viewer {
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-size: 12px;
          line-height: 1.5;
        }

        .code-editor {
          height: 100%;
        }

        .code-editor pre {
          height: 100%;
          margin: 0;
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-size: 13px;
          line-height: 1.5;
        }
      `}</style>
    </div>
  )
}

export default CustomWidget