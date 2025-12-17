import React, { useState } from 'react';
import { ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import FeedbackWidget from './FeedbackWidget';

interface FeedbackData {
  type: 'bug' | 'feature' | 'improvement' | 'other';
  category: string;
  rating: number;
  title: string;
  description: string;
  email?: string;
  screenshots: File[];
  userAgent: string;
  url: string;
  timestamp: string;
}

export default function FeedbackButton() {
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const handleFeedbackSubmit = async (feedback: FeedbackData) => {
    // 準備要發送的數據
    const formData = new FormData();
    formData.append('type', feedback.type);
    formData.append('category', feedback.category);
    formData.append('rating', feedback.rating.toString());
    formData.append('title', feedback.title);
    formData.append('description', feedback.description);
    formData.append('userAgent', feedback.userAgent);
    formData.append('url', feedback.url);
    formData.append('timestamp', feedback.timestamp);

    if (feedback.email) {
      formData.append('email', feedback.email);
    }

    // 添加截圖文件
    feedback.screenshots.forEach((file, index) => {
      formData.append(`screenshot_${index}`, file);
    });

    try {
      // 發送到後端API
      const response = await fetch('/api/feedback', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('提交失敗');
      }

      // 顯示成功消息
      alert('感謝您的反饋！我們會認真處理您的意見。');
    } catch (error) {
      console.error('提交反饋失敗:', error);
      throw error;
    }
  };

  return (
    <>
      {/* 反饋按鈕 */}
      <div className="fixed bottom-6 right-6 z-40">
        <div className="relative">
          {/* 提示文字 */}
          {showTooltip && (
            <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap">
              點擊提交反饋
              <div className="absolute top-full right-4 w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-gray-900"></div>
            </div>
          )}

          {/* 按鈕 */}
          <button
            onClick={() => setIsWidgetOpen(true)}
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            className="group relative flex items-center justify-center w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-110"
            aria-label="反饋"
          >
            <ChatBubbleLeftRightIcon className="h-7 w-7" />
            {/* 動畫效果 */}
            <span className="absolute inset-0 rounded-full bg-blue-400 animate-ping opacity-20"></span>
          </button>
        </div>
      </div>

      {/* 反饋小部件 */}
      <FeedbackWidget
        isOpen={isWidgetOpen}
        onClose={() => setIsWidgetOpen(false)}
        onSubmit={handleFeedbackSubmit}
      />
    </>
  );
}