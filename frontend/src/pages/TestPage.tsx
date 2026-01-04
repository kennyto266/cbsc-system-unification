import React from 'react';

const TestPage: React.FC = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ color: '#1890ff' }}>測試頁面</h1>
      <p>如果你能看到這個頁面，表示 React 正常運作！</p>
      <p style={{ color: '#52c41a' }}>✅ Vite 服務器正常</p>
      <p style={{ color: '#52c41a' }}>✅ React 組件載入成功</p>
      <p>當前時間: {new Date().toLocaleString()}</p>
    </div>
  );
};

export default TestPage;
