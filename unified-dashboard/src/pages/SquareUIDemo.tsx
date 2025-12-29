// Square-UI Demo Page
import React, { useState } from 'react';
import {
  SquareButton,
  SquareCard,
  SquareInput,
  cn
} from '../components/square';
import { squareColors } from '../components/square/utils/square-utils';

export default function SquareUIDemo() {
  const [inputValue, setInputValue] = useState('');
  const [selectedVariant, setSelectedVariant] = useState('primary');

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-square-500 to-purple-600 bg-clip-text text-transparent">
          Square-UI 组件演示
        </h1>
        <p className="text-gray-600 mb-8">现代化的设计系统组件库</p>

        {/* Button Examples */}
        <SquareCard className="mb-8" animated>
          <SquareCard.Header>
            <SquareCardTitle>按钮组件</SquareCardTitle>
            <SquareCardDescription>
              支持多种变体和尺寸的按钮组件
            </SquareCardDescription>
          </SquareCard.Header>
          <SquareCard.Content>
            <div className="space-y-4">
              {/* Variants */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">变体</h3>
                <div className="flex flex-wrap gap-3">
                  <SquareButton variant="primary">Primary</SquareButton>
                  <SquareButton variant="secondary">Secondary</SquareButton>
                  <SquareButton variant="success">Success</SquareButton>
                  <SquareButton variant="warning">Warning</SquareButton>
                  <SquareButton variant="error">Error</SquareButton>
                  <SquareButton variant="outline">Outline</SquareButton>
                  <SquareButton variant="ghost">Ghost</SquareButton>
                </div>
              </div>

              {/* Sizes */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">尺寸</h3>
                <div className="flex items-center gap-3">
                  <SquareButton size="sm">Small</SquareButton>
                  <SquareButton size="md">Medium</SquareButton>
                  <SquareButton size="lg">Large</SquareButton>
                  <SquareButton size="xl">Extra Large</SquareButton>
                </div>
              </div>

              {/* States */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">状态</h3>
                <div className="flex flex-wrap gap-3">
                  <SquareButton>Normal</SquareButton>
                  <SquareButton disabled>Disabled</SquareButton>
                  <SquareButton loading>Loading</SquareButton>
                  <SquareButton fullWidth>Full Width</SquareButton>
                </div>
              </div>

              {/* With Icons */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">带图标</h3>
                <div className="flex flex-wrap gap-3">
                  <SquareButton
                    icon={<span>🚀</span>}
                    iconPosition="left"
                  >
                    左侧图标
                  </SquareButton>
                  <SquareButton
                    icon={<span>⭐</span>}
                    iconPosition="right"
                  >
                    右侧图标
                  </SquareButton>
                </div>
              </div>
            </div>
          </SquareCard.Content>
        </SquareCard>

        {/* Card Examples */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <SquareCard variant="default" hover>
            <SquareCard.Header>
              <SquareCardTitle>默认卡片</SquareCardTitle>
            </SquareCard.Header>
            <SquareCard.Content>
              <p className="text-gray-600">
                这是一个默认样式的卡片组件，具有轻微的阴影效果。
              </p>
            </SquareCard.Content>
            <SquareCard.Footer>
              <SquareButton size="sm">查看详情</SquareButton>
            </SquareCard.Footer>
          </SquareCard>

          <SquareCard variant="glass" hover>
            <SquareCard.Header>
              <SquareCardTitle>玻璃态卡片</SquareCardTitle>
            </SquareCard.Header>
            <SquareCard.Content>
              <p className="text-gray-600">
                这是一个具有玻璃态效果的卡片组件，背景模糊且半透明。
              </p>
            </SquareCard.Content>
            <SquareCard.Footer>
              <SquareButton size="sm" variant="outline">了解更多</SquareButton>
            </SquareCard.Footer>
          </SquareCard>

          <SquareCard variant="elevated" hover>
            <SquareCard.Header>
              <SquareCardTitle>悬浮卡片</SquareCardTitle>
            </SquareCard.Header>
            <SquareCard.Content>
              <p className="text-gray-600">
                这是一个具有明显阴影效果的悬浮卡片，突出显示重要内容。
              </p>
            </SquareCard.Content>
            <SquareCard.Footer>
              <SquareButton size="sm" variant="ghost">忽略</SquareButton>
            </SquareCard.Footer>
          </SquareCard>

          <SquareCard variant="outlined" hover>
            <SquareCard.Header>
              <SquareCardTitle>边框卡片</SquareCardTitle>
            </SquareCard.Header>
            <SquareCard.Content>
              <p className="text-gray-600">
                这是一个仅显示边框的简约卡片样式。
              </p>
            </SquareCard.Content>
            <SquareCard.Footer>
              <SquareButton size="sm" variant="secondary">确认</SquareButton>
            </SquareCard.Footer>
          </SquareCard>
        </div>

        {/* Input Examples */}
        <SquareCard className="mb-8" animated>
          <SquareCard.Header>
            <SquareCardTitle>输入框组件</SquareCardTitle>
            <SquareCardDescription>
              支持多种样式和状态的输入框组件
            </SquareCardDescription>
          </SquareCard.Header>
          <SquareCard.Content>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <SquareInput
                  label="默认输入框"
                  placeholder="请输入内容..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                />
              </div>
              <div>
                <SquareInput
                  label="填充样式"
                  variant="filled"
                  placeholder="填充样式的输入框"
                />
              </div>
              <div>
                <SquareInput
                  label="边框样式"
                  variant="outlined"
                  placeholder="边框样式的输入框"
                />
              </div>
              <div>
                <SquareInput
                  label="带图标"
                  placeholder="搜索..."
                  leftIcon={<span>🔍</span>}
                />
              </div>
              <div>
                <SquareInput
                  label="错误状态"
                  error="这是一个错误提示信息"
                  placeholder="输入有误"
                />
              </div>
              <div>
                <SquareInput
                  label="帮助文本"
                  helperText="这是额外的帮助信息"
                  placeholder="带帮助信息的输入框"
                />
              </div>
            </div>
          </SquareCard.Content>
        </SquareCard>

        {/* Color Palette */}
        <SquareCard animated>
          <SquareCard.Header>
            <SquareCardTitle>Square-UI 色板</SquareCardTitle>
            <SquareCardDescription>
              Square-UI 的品牌色彩系统
            </SquareCardDescription>
          </SquareCard.Header>
          <SquareCard.Content>
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">主色板</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(squareColors.primary).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center space-x-2 bg-gray-100 rounded-square p-2"
                  >
                    <div
                      className="w-12 h-12 rounded-square shadow-sm"
                      style={{ backgroundColor: value }}
                    />
                    <div>
                      <div className="text-sm font-medium">{key}</div>
                      <div className="text-xs text-gray-500">{value}</div>
                    </div>
                  </div>
                ))}
              </div>

              <h3 className="text-sm font-medium text-gray-700 mb-3 mt-6">渐变效果</h3>
              <div className="space-y-2">
                {Object.entries(squareColors.gradient).map(([key, value]) => (
                  <div
                    key={key}
                    className="h-20 rounded-square shadow-sm flex items-center justify-center text-white font-medium"
                    style={{ background: value }}
                  >
                    {key}
                  </div>
                ))}
              </div>
            </div>
          </SquareCard.Content>
        </SquareCard>
      </div>
    </div>
  );
}