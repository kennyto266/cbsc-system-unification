import React, { useState, useEffect } from 'react';
import {
  User,
  Mail,
  Phone,
  Globe,
  Palette,
  Camera,
  Save,
  X,
  Check,
  AlertCircle
} from 'lucide-react';

const ProfileEdit = () => {
  const [profile, setProfile] = useState({
    bio: '',
    phone: '',
    timezone: 'Asia/Shanghai',
    language: 'zh-CN',
    theme: 'light'
  });
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [avatarFile, setAvatarFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch('/api/user/profile', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProfile({
          bio: data.bio || '',
          phone: data.phone || '',
          timezone: data.timezone || 'Asia/Shanghai',
          language: data.language || 'zh-CN',
          theme: data.theme || 'light'
        });
      }
    } catch (err) {
      console.error('加载用户资料失败:', err);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProfile(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        setMessage({ type: 'error', text: '请选择图片文件' });
        return;
      }

      // 验证文件大小 (5MB)
      if (file.size > 5 * 1024 * 1024) {
        setMessage({ type: 'error', text: '图片大小不能超过5MB' });
        return;
      }

      setAvatarFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setMessage({ type: 'error', text: '请先登录' });
        return;
      }

      // 先上传头像（如果有）
      if (avatarFile) {
        const formData = new FormData();
        formData.append('file', avatarFile);

        const avatarResponse = await fetch('/api/user/avatar', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });

        if (!avatarResponse.ok) {
          throw new Error('头像上传失败');
        }
      }

      // 更新资料
      const updateData = {
        bio: profile.bio,
        phone: profile.phone,
        timezone: profile.timezone,
        language: profile.language,
        theme: profile.theme
      };

      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        setMessage({ type: 'success', text: '资料更新成功' });
        // 清除头像预览
        setAvatarPreview(null);
        setAvatarFile(null);
        // 清除消息
        setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '更新失败');
      }

    } catch (err) {
      setMessage({ type: 'error', text: err.message || '更新失败' });
    } finally {
      setLoading(false);
    }
  };

  const clearMessage = () => {
    setMessage({ type: '', text: '' });
  };

  const timezones = [
    { value: 'Asia/Shanghai', label: '北京时间 (GMT+8)' },
    { value: 'America/New_York', label: '纽约时间 (GMT-5)' },
    { value: 'Europe/London', label: '伦敦时间 (GMT+0)' },
    { value: 'Asia/Tokyo', label: '东京时间 (GMT+9)' }
  ];

  const languages = [
    { value: 'zh-CN', label: '简体中文' },
    { value: 'en-US', label: 'English' }
  ];

  const themes = [
    { value: 'light', label: '亮色主题', color: 'bg-white border-gray-300' },
    { value: 'dark', label: '暗色主题', color: 'bg-gray-900 border-gray-700' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6">
        <div className="bg-white rounded-lg shadow-sm">
          {/* 头部 */}
          <div className="border-b px-6 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-gray-900">编辑个人资料</h1>
              <button
                onClick={() => window.history.back()}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* 消息提示 */}
          {message.text && (
            <div className={`mx-6 mt-4 p-3 rounded-lg flex items-center ${
              message.type === 'success'
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}>
              {message.type === 'success' ? (
                <Check className="w-5 h-5 mr-2" />
              ) : (
                <AlertCircle className="w-5 h-5 mr-2" />
              )}
              {message.text}
              <button
                onClick={clearMessage}
                className="ml-auto text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* 表单内容 */}
          <form onSubmit={handleSave} className="px-6 py-6 space-y-6">
            {/* 头像上传 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">头像</label>
              <div className="flex items-center space-x-4">
                <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
                  {avatarPreview ? (
                    <img
                      src={avatarPreview}
                      alt="头像预览"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <User className="w-12 h-12 text-gray-400" />
                  )}
                </div>
                <div className="flex-1">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    className="hidden"
                    id="avatar-upload"
                  />
                  <label
                    htmlFor="avatar-upload"
                    className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 cursor-pointer"
                  >
                    <Camera className="w-4 h-4 mr-2" />
                    选择图片
                  </label>
                  <p className="text-xs text-gray-500 mt-1">
                    支持 JPG、PNG 格式，文件大小不超过5MB
                  </p>
                </div>
              </div>
            </div>

            {/* 个人简介 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">个人简介</label>
              <textarea
                name="bio"
                value={profile.bio}
                onChange={handleInputChange}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="介绍一下自己..."
              />
            </div>

            {/* 联系电话 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">联系电话</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Phone className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="tel"
                  name="phone"
                  value={profile.phone}
                  onChange={handleInputChange}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="请输入电话号码"
                />
              </div>
            </div>

            {/* 时区设置 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">时区</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Globe className="h-5 w-5 text-gray-400" />
                </div>
                <select
                  name="timezone"
                  value={profile.timezone}
                  onChange={handleInputChange}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {timezones.map(tz => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* 语言设置 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">语言</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Globe className="h-5 w-5 text-gray-400" />
                </div>
                <select
                  name="language"
                  value={profile.language}
                  onChange={handleInputChange}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {languages.map(lang => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* 主题设置 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">界面主题</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Palette className="h-5 w-5 text-gray-400" />
                </div>
                <select
                  name="theme"
                  value={profile.theme}
                  onChange={handleInputChange}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {themes.map(theme => (
                    <option key={theme.value} value={theme.value}>
                      {theme.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* 按钮组 */}
            <div className="flex justify-end space-x-3 pt-6 border-t">
              <button
                type="button"
                onClick={() => window.history.back()}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    保存中...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    保存
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ProfileEdit;