import React, { useState } from 'react'
import {
  Button,
  ButtonGroup,
  Fab,
  ThemeToggle,
  ThemeSelector,
  Card,
  Badge,
  Input,
  Select,
  Modal,
  LoadingSpinner,
  StatCard,
  QuickActions,
  RecentActivities,
  useTheme,
} from '@/components/ui'
import { colors, typography, spacing } from '@/styles/tokens'

// Design system showcase page - 设计系统展示页面
export default function DesignSystem() {
  const { theme, setTheme } = useTheme()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [selectValue, setSelectValue] = useState('option1')

  return (
    <div className="min-h-screen bg-background-primary text-text-primary p-6">
      {/* Header - 头部 */}
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gradient mb-2">
              CBSC Design System
            </h1>
            <p className="text-text-secondary">
              企业级UI/UX设计系统展示
            </p>
          </div>
          <ThemeSelector />
        </div>

        {/* Theme Section - 主题部分 */}
        <Card className="mb-8">
          <Card.Header>
            <h2 className="text-2xl font-semibold">主题系统</h2>
          </Card.Header>
          <Card.Body>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <span>当前主题: <strong>{theme}</strong></span>
                <ThemeToggle showLabel />
                <Button
                  variant="outline"
                  onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                >
                  切换主题
                </Button>
              </div>

              {/* Color Palette - 色彩展示 */}
              <div>
                <h3 className="text-lg font-medium mb-3">色彩系统</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm font-medium mb-2">主色调</p>
                    <div className="space-y-1">
                      {Object.entries(colors.primary).slice(3, 9).map(([key, value]) => (
                        <div key={key} className="flex items-center gap-2">
                          <div
                            className="w-8 h-8 rounded border"
                            style={{ backgroundColor: value }}
                          />
                          <span className="text-sm text-text-secondary">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <p className="text-sm font-medium mb-2">语义色</p>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded bg-success" />
                        <span className="text-sm text-text-secondary">Success</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded bg-warning" />
                        <span className="text-sm text-text-secondary">Warning</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded bg-error" />
                        <span className="text-sm text-text-secondary">Error</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded bg-info" />
                        <span className="text-sm text-text-secondary">Info</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm font-medium mb-2">中性色</p>
                    <div className="space-y-1">
                      {Object.entries(colors.neutral).slice(0, 6).map(([key, value]) => (
                        <div key={key} className="flex items-center gap-2">
                          <div
                            className="w-8 h-8 rounded border"
                            style={{ backgroundColor: value }}
                          />
                          <span className="text-sm text-text-secondary">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card.Body>
        </Card>

        {/* Typography Section - 字体部分 */}
        <Card className="mb-8">
          <Card.Header>
            <h2 className="text-2xl font-semibold">字体系统</h2>
          </Card.Header>
          <Card.Body>
            <div className="space-y-4">
              <h3 className="font-serif" style={{ fontFamily: typography.fontFamilies.sans }}>
                Inter - 默认字体族
              </h3>
              <div className="space-y-2">
                <h1 className="text-4xl">H1 Heading - 36px</h1>
                <h2 className="text-3xl">H2 Heading - 30px</h2>
                <h3 className="text-2xl">H3 Heading - 24px</h3>
                <h4 className="text-xl">H4 Heading - 20px</h4>
                <h5 className="text-lg">H5 Heading - 18px</h5>
                <h6 className="text-base">H6 Heading - 16px</h6>
                <p className="text-sm">Body Small - 14px</p>
                <p className="text-xs">Body XSmall - 12px</p>
              </div>
            </div>
          </Card.Body>
        </Card>

        {/* Button Section - 按钮部分 */}
        <Card className="mb-8">
          <Card.Header>
            <h2 className="text-2xl font-semibold">按钮组件</h2>
          </Card.Header>
          <Card.Body>
            <div className="space-y-6">
              {/* Variants - 变体 */}
              <div>
                <h3 className="text-lg font-medium mb-3">按钮变体</h3>
                <div className="flex flex-wrap gap-2">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="outline">Outline</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="danger">Danger</Button>
                  <Button variant="success">Success</Button>
                </div>
              </div>

              {/* Sizes - 尺寸 */}
              <div>
                <h3 className="text-lg font-medium mb-3">按钮尺寸</h3>
                <div className="flex flex-wrap items-center gap-2">
                  <Button size="xs">Extra Small</Button>
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                  <Button size="xl">Extra Large</Button>
                </div>
              </div>

              {/* States - 状态 */}
              <div>
                <h3 className="text-lg font-medium mb-3">按钮状态</h3>
                <div className="flex flex-wrap gap-2">
                  <Button>Default</Button>
                  <Button loading>Loading</Button>
                  <Button disabled>Disabled</Button>
                </div>
              </div>

              {/* With Icons - 带图标 */}
              <div>
                <h3 className="text-lg font-medium mb-3">带图标的按钮</h3>
                <div className="flex flex-wrap gap-2">
                  <Button icon="➕">Add</Button>
                  <Button icon="🗑️" variant="danger" iconPosition="right">
                    Delete
                  </Button>
                  <Button icon="💾" variant="outline">Save</Button>
                </div>
              </div>

              {/* Button Group - 按钮组 */}
              <div>
                <h3 className="text-lg font-medium mb-3">按钮组</h3>
                <ButtonGroup>
                  <Button variant="outline">Cancel</Button>
                  <Button>Submit</Button>
                </ButtonGroup>
              </div>

              {/* Full Width - 全宽 */}
              <div>
                <h3 className="text-lg font-medium mb-3">全宽按钮</h3>
                <Button fullWidth>Full Width Button</Button>
              </div>
            </div>
          </Card.Body>
        </Card>

        {/* Form Components Section - 表单组件部分 */}
        <Card className="mb-8">
          <Card.Header>
            <h2 className="text-2xl font-semibold">表单组件</h2>
          </Card.Header>
          <Card.Body>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Input */}
              <div>
                <h3 className="text-lg font-medium mb-3">输入框</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">基础输入框</label>
                    <Input
                      placeholder="请输入内容"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">带错误</label>
                    <Input
                      placeholder="错误输入框"
                      error="这是一个错误信息"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">禁用状态</label>
                    <Input
                      placeholder="禁用的输入框"
                      disabled
                    />
                  </div>
                </div>
              </div>

              {/* Select */}
              <div>
                <h3 className="text-lg font-medium mb-3">选择框</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">基础选择框</label>
                    <Select value={selectValue} onChange={setSelectValue}>
                      <option value="option1">选项 1</option>
                      <option value="option2">选项 2</option>
                      <option value="option3">选项 3</option>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </Card.Body>
        </Card>

        {/* Badge Section - 徽章部分 */}
        <Card className="mb-8">
          <Card.Header>
            <h2 className="text-2xl font-semibold">徽章组件</h2>
          </Card.Header>
          <Card.Body>
            <div className="flex flex-wrap gap-2">
              <Badge>Default</Badge>
              <Badge variant="primary">Primary</Badge>
              <Badge variant="success">Success</Badge>
              <Badge variant="warning">Warning</Badge>
              <Badge variant="error">Error</Badge>
              <Badge variant="info">Info</Badge>
            </div>
          </Card.Body>
        </Card>

        {/* Card Section - 卡片部分 */}
        <Card className="mb-8">
          <Card.Header>
            <h2 className="text-2xl font-semibold">卡片组件</h2>
          </Card.Header>
          <Card.Body>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <Card.Header>
                  <h3 className="font-semibold">卡片标题</h3>
                </Card.Header>
                <Card.Body>
                  <p className="text-text-secondary">
                    这是卡片的内容区域，可以放置任意内容。
                  </p>
                </Card.Body>
                <Card.Footer>
                  <Button size="sm">操作</Button>
                </Card.Footer>
              </Card>

              <StatCard
                title="总策略数"
                value="128"
                change="+12.5%"
                trend="up"
                icon="📊"
              />

              <Card className="text-center">
                <Card.Body>
                  <LoadingSpinner />
                  <p className="mt-2 text-sm text-text-secondary">加载中...</p>
                </Card.Body>
              </Card>
            </div>
          </Card.Body>
        </Card>

        {/* Modal Section - 模态框部分 */}
        <Card className="mb-8">
          <Card.Header>
            <h2 className="text-2xl font-semibold">模态框组件</h2>
          </Card.Header>
          <Card.Body>
            <Button onClick={() => setIsModalOpen(true)}>
              打开模态框
            </Button>

            <Modal
              isOpen={isModalOpen}
              onClose={() => setIsModalOpen(false)}
              title="示例模态框"
            >
              <p className="mb-4">
                这是一个模态框示例。模态框用于需要用户交互的重要操作。
              </p>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                  取消
                </Button>
                <Button onClick={() => setIsModalOpen(false)}>
                  确认
                </Button>
              </div>
            </Modal>
          </Card.Body>
        </Card>

        {/* Floating Action Button - 浮动操作按钮 */}
        <Fab
          icon="✉️"
          onClick={() => alert('Feedback clicked!')}
          aria-label="Send feedback"
        />

        {/* Dashboard Components - 仪表板组件 */}
        <Card className="mb-8">
          <Card.Header>
            <h2 className="text-2xl font-semibold">仪表板组件</h2>
          </Card.Header>
          <Card.Body>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <QuickActions />
              <RecentActivities />
            </div>
          </Card.Body>
        </Card>
      </div>
    </div>
  )
}