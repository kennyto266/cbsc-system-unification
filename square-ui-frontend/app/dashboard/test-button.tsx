'use client';

import React from 'react';

// 一個簡單的測試按鈕組件，用於驗證點擊事件
export default function TestButton() {
  const handleClick = () => {
    console.log('測試按鈕被點擊了！');
    alert('測試按鈕被點擊了！');
  };

  return (
    <button
      onClick={handleClick}
      style={{
        padding: '10px 20px',
        backgroundColor: '#ff0000',
        color: '#ffffff',
        border: 'none',
        borderRadius: '5px',
        cursor: 'pointer',
        margin: '10px'
      }}
    >
      測試按鈕（點我）
    </button>
  );
}