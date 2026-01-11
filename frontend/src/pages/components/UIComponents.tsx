/**
 * UI Components Showcase - UI組件展示頁面
 * 版本: 1.0.0
 * 描述: 展示所有UI組件的使用方法和效果
 */

import React, { useState } from 'react';
import { Button, Input, Select } from '../../components/ui';
import type { SelectOption } from '../../components/ui';

export const UIComponents: React.FC = () => {
  // Input狀態
  const [inputValue, setInputValue] = useState('');
  const [inputValue2, setInputValue2] = useState('');
  const [inputValue3, setInputValue3] = useState('');

  // Select狀態
  const [selectValue, setSelectValue] = useState('');
  const [multiSelectValue, setMultiSelectValue] = useState<string[]>([]);

  // Select選項
  const selectOptions: SelectOption[] = [
    { value: 'option1', label: '選項 1' },
    { value: 'option2', label: '選項 2' },
    { value: 'option3', label: '選項 3', disabled: true },
    { value: 'option4', label: '選項 4' },
  ];

  const selectGroupOptions = [
    {
      label: '分組 A',
      options: [
        { value: 'a1', label: '選項 A1', description: '這是選項A1的描述' },
        { value: 'a2', label: '選項 A2', description: '這是選項A2的描述' },
      ]
    },
    {
      label: '分組 B',
      options: [
        { value: 'b1', label: '選項 B1' },
        { value: 'b2', label: '選項 B2' },
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 頁面標題 */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-gray-900">UI 組件展示</h1>
          <p className="mt-2 text-gray-600">
            展示 CBSC 設計系統中的所有 UI 組件及其使用方法
          </p>
        </div>

        {/* Button 組件展示 */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Button 按鈕組件</h2>
          <div className="bg-white rounded-lg shadow p-6">
            {/* 變體展示 */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-gray-800 mb-4">變體 (Variants)</h3>
              <div className="flex flex-wrap gap-4">
                <Button variant="primary">Primary</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="link">Link</Button>
                <Button variant="success">Success</Button>
                <Button variant="warning">Warning</Button>
                <Button variant="error">Error</Button>
              </div>
            </div>

            {/* 尺寸展示 */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-gray-800 mb-4">尺寸 (Sizes)</h3>
              <div className="flex flex-wrap gap-4 items-center">
                <Button size="xs">Extra Small</Button>
                <Button size="sm">Small</Button>
                <Button size="md">Medium</Button>
                <Button size="lg">Large</Button>
                <Button size="xl">Extra Large</Button>
              </div>
            </div>

            {/* 狀態展示 */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-gray-800 mb-4">狀態 (States)</h3>
              <div className="flex flex-wrap gap-4">
                <Button>Normal</Button>
                <Button disabled>Disabled</Button>
                <Button loading>Loading</Button>
              </div>
            </div>

            {/* 圖標展示 */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-gray-800 mb-4">圖標 (Icons)</h3>
              <div className="flex flex-wrap gap-4">
                <Button
                  icon={
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  }
                >
                  Add
                </Button>
                <Button
                  iconPosition="right"
                  icon={
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  }
                >
                  Next
                </Button>
              </div>
            </div>

            {/* 全寬和圓角 */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-800 mb-4">其他樣式</h3>
              <Button fullWidth>Full Width</Button>
              <Button rounded>Rounded</Button>
            </div>
          </div>
        </section>

        {/* Input 組件展示 */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Input 輸入框組件</h2>
          <div className="bg-white rounded-lg shadow p-6 space-y-6">
            {/* 基礎輸入框 */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">基礎輸入框</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="用戶名"
                  placeholder="請輸入用戶名"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                />
                <Input
                  label="密碼"
                  type="password"
                  placeholder="請輸入密碼"
                  helperText="密碼至少8位字符"
                />
              </div>
            </div>

            {/* 變體展示 */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">變體樣式</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  variant="default"
                  label="Default"
                  placeholder="默認樣式"
                />
                <Input
                  variant="filled"
                  label="Filled"
                  placeholder="填充樣式"
                />
                <Input
                  variant="outlined"
                  label="Outlined"
                  placeholder="輪廓樣式"
                />
                <Input
                  variant="underlined"
                  label="Underlined"
                  placeholder="下劃線樣式"
                />
              </div>
            </div>

            {/* 尺寸展示 */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">不同尺寸</h3>
              <div className="space-y-4">
                <Input size="xs" label="Extra Small" placeholder="超小尺寸" />
                <Input size="sm" label="Small" placeholder="小尺寸" />
                <Input size="md" label="Medium" placeholder="中等尺寸" />
                <Input size="lg" label="Large" placeholder="大尺寸" />
                <Input size="xl" label="Extra Large" placeholder="超大尺寸" />
              </div>
            </div>

            {/* 狀態展示 */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">狀態</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  state="success"
                  label="成功狀態"
                  value="驗證通過"
                  helperText="輸入有效"
                />
                <Input
                  state="warning"
                  label="警告狀態"
                  value="需要注意"
                  helperText="請檢查輸入"
                />
                <Input
                  state="error"
                  label="錯誤狀態"
                  value="輸入錯誤"
                  errorText="此格式不正確"
                />
                <Input
                  loading
                  label="載入中"
                  placeholder="正在驗證..."
                />
              </div>
            </div>

            {/* 圖標和元素 */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">圖標和元素</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  leftIcon={
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  }
                  label="搜索"
                  placeholder="搜索內容..."
                />
                <Input
                  rightIcon={
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  }
                  label="密碼"
                  type="password"
                  placeholder="請輸入密碼"
                />
                <Input
                  clearable
                  label="可清除"
                  placeholder="輸入後可清除"
                  value={inputValue2}
                  onChange={(e) => setInputValue2(e.target.value)}
                />
                <Input
                  leftElement={
                    <span className="text-sm text-gray-500">+</span>
                  }
                  label="電話號碼"
                  placeholder="86"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Select 組件展示 */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Select 選擇器組件</h2>
          <div className="bg-white rounded-lg shadow p-6 space-y-6">
            {/* 基礎選擇器 */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">基礎選擇器</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="選擇選項"
                  options={selectOptions}
                  placeholder="請選擇..."
                  value={selectValue}
                  onChange={setSelectValue}
                />
                <Select
                  label="禁用選擇器"
                  options={selectOptions}
                  placeholder="已禁用"
                  disabled
                />
              </div>
            </div>

            {/* 變體展示 */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">變體樣式</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Select
                  variant="default"
                  label="Default"
                  options={selectOptions}
                  placeholder="默認樣式"
                />
                <Select
                  variant="filled"
                  label="Filled"
                  options={selectOptions}
                  placeholder="填充樣式"
                />
                <Select
                  variant="outlined"
                  label="Outlined"
                  options={selectOptions}
                  placeholder="輪廓樣式"
                />
              </div>
            </div>

            {/* 可清除和搜索 */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">可清除和搜索</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="可清除"
                  options={selectOptions}
                  placeholder="選擇後可清除"
                  clearable
                  value={selectValue}
                  onChange={setSelectValue}
                />
                <Select
                  label="可搜索"
                  options={selectOptions}
                  placeholder="搜索選項..."
                  searchable
                />
              </div>
            </div>

            {/* 多選和分組 */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">多選和分組</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="多選"
                  options={selectOptions}
                  placeholder="選擇多個選項"
                  multiple
                  value={multiSelectValue}
                  onChange={setMultiSelectValue}
                />
                <Select
                  label="分組選項"
                  options={selectGroupOptions}
                  placeholder="選擇分組選項"
                  searchable
                />
              </div>
            </div>
          </div>
        </section>

        {/* 組件組合展示 */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">組件組合示例</h2>
          <div className="bg-white rounded-lg shadow p-6">
            <form className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Input
                  label="姓名"
                  placeholder="請輸入姓名"
                  required
                />
                <Input
                  label="郵箱"
                  type="email"
                  placeholder="請輸入郵箱"
                  state="error"
                  errorText="請輸入有效的郵箱地址"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Select
                  label="國家"
                  options={[
                    { value: 'cn', label: '中國' },
                    { value: 'us', label: '美國' },
                    { value: 'jp', label: '日本' },
                  ]}
                  placeholder="請選擇國家"
                />
                <Input
                  label="手機號碼"
                  placeholder="請輸入手機號碼"
                  leftIcon={
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                  }
                />
              </div>
              <div className="flex justify-end space-x-4">
                <Button variant="outline">取消</Button>
                <Button loading>提交</Button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
};

export default UIComponents;