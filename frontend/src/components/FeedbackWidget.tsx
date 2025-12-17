import React, { useState } from 'react';
import { StarIcon, ExclamationTriangleIcon, CheckCircleIcon, LightBulbIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

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

interface FeedbackWidgetProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (feedback: FeedbackData) => void;
}

export default function FeedbackWidget({ isOpen, onClose, onSubmit }: FeedbackWidgetProps) {
  const [feedbackType, setFeedbackType] = useState<FeedbackData['type']>('bug');
  const [category, setCategory] = useState('');
  const [rating, setRating] = useState(0);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [email, setEmail] = useState('');
  const [screenshots, setScreenshots] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const categories = {
    bug: ['功能異常', '顯示錯誤', '性能問題', '崩閃/卡頓', '數據錯誤'],
    feature: ['新功能需求', '功能增強', '界面優化', '數據展示', '交互改進'],
    improvement: ['性能優化', '用戶體驗', '流程簡化', '易用性提升', '其他改進'],
    other: ['建議', '問題諮詢', '其他']
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title || !description) {
      alert('請填寫標題和描述');
      return;
    }

    setIsSubmitting(true);

    const feedback: FeedbackData = {
      type: feedbackType,
      category,
      rating: feedbackType === 'other' ? 0 : rating,
      title,
      description,
      email,
      screenshots,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString()
    };

    try {
      await onSubmit(feedback);
      // Reset form
      setFeedbackType('bug');
      setCategory('');
      setRating(0);
      setTitle('');
      setDescription('');
      setEmail('');
      setScreenshots([]);
      onClose();
    } catch (error) {
      console.error('提交反饋失敗:', error);
      alert('提交失敗，請稍後重試');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleScreenshotChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setScreenshots(prev => [...prev, ...files]);
  };

  const removeScreenshot = (index: number) => {
    setScreenshots(prev => prev.filter((_, i) => i !== index));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">用戶反饋</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 反饋類型 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              反饋類型
            </label>
            <div className="grid grid-cols-4 gap-3">
              <button
                type="button"
                onClick={() => setFeedbackType('bug')}
                className={`p-3 rounded-lg border-2 transition-all ${
                  feedbackType === 'bug'
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <ExclamationTriangleIcon className="h-6 w-6 mx-auto mb-1 text-red-500" />
                <span className="text-xs">問題報告</span>
              </button>
              <button
                type="button"
                onClick={() => setFeedbackType('feature')}
                className={`p-3 rounded-lg border-2 transition-all ${
                  feedbackType === 'feature'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <LightBulbIcon className="h-6 w-6 mx-auto mb-1 text-blue-500" />
                <span className="text-xs">功能建議</span>
              </button>
              <button
                type="button"
                onClick={() => setFeedbackType('improvement')}
                className={`p-3 rounded-lg border-2 transition-all ${
                  feedbackType === 'improvement'
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <CheckCircleIcon className="h-6 w-6 mx-auto mb-1 text-green-500" />
                <span className="text-xs">改進建議</span>
              </button>
              <button
                type="button"
                onClick={() => setFeedbackType('other')}
                className={`p-3 rounded-lg border-2 transition-all ${
                  feedbackType === 'other'
                    ? 'border-gray-500 bg-gray-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <StarIcon className="h-6 w-6 mx-auto mb-1 text-gray-500" />
                <span className="text-xs">其他</span>
              </button>
            </div>
          </div>

          {/* 分類 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              具體分類
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">請選擇分類</option>
              {categories[feedbackType].map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* 評分 */}
          {feedbackType !== 'other' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                整體評分
              </label>
              <div className="flex space-x-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className="transition-transform hover:scale-110"
                  >
                    {star <= rating ? (
                      <StarIconSolid className="h-8 w-8 text-yellow-400" />
                    ) : (
                      <StarIcon className="h-8 w-8 text-gray-300" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 標題 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              標題
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="簡要描述問題或建議"
              required
            />
          </div>

          {/* 描述 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              詳細描述
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={5}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="請詳細描述您的反饋內容"
              required
            />
          </div>

          {/* 郵箱 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              聯繫郵箱（可選）
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="your@email.com"
            />
          </div>

          {/* 截圖上傳 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              截圖上傳
            </label>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleScreenshotChange}
              className="hidden"
              id="screenshot-upload"
            />
            <label
              htmlFor="screenshot-upload"
              className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <span>選擇截圖</span>
            </label>
            {screenshots.length > 0 && (
              <div className="mt-3 space-y-2">
                {screenshots.map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                    <span className="text-sm text-gray-700">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeScreenshot(index)}
                      className="text-red-500 hover:text-red-700 transition-colors"
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 提交按鈕 */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? '提交中...' : '提交反饋'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}