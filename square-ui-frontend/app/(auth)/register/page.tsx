'use client';

import { useState } from 'react';
import { SquareCard, SquareInput, SquareButton } from '@/components/ui';
import { AlertCircle } from 'lucide-react';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.firstName) newErrors.firstName = '名字為必填項';
    if (!formData.lastName) newErrors.lastName = '姓氏為必填項';
    if (!formData.email) newErrors.email = '電子郵件為必填項';
    if (!formData.password) newErrors.password = '密碼為必填項';
    if (formData.password.length < 8) newErrors.password = '密碼至少需要8個字符';
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '密碼不匹配';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);

    try {
      // TODO: Implement actual registration logic
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('註冊失敗');
      }

      // Redirect to login page on success
      window.location.href = '/login?message=註冊成功，請登錄';
    } catch (err) {
      setErrors({ submit: '註冊失敗，請稍後再試' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <SquareCard>
      <form className="space-y-6" onSubmit={handleSubmit}>
        <h3 className="text-2xl font-semibold text-gray-900 text-center">
          創建新帳戶
        </h3>

        {errors.submit && (
          <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-md">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-sm text-red-700">{errors.submit}</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <SquareInput
            label="名字"
            type="text"
            name="firstName"
            value={formData.firstName}
            onChange={handleChange}
            error={errors.firstName}
            required
          />
          <SquareInput
            label="姓氏"
            type="text"
            name="lastName"
            value={formData.lastName}
            onChange={handleChange}
            error={errors.lastName}
            required
          />
        </div>

        <SquareInput
          label="電子郵件"
          type="email"
          name="email"
          placeholder="example@cbsc.com"
          value={formData.email}
          onChange={handleChange}
          error={errors.email}
          required
        />

        <SquareInput
          label="密碼"
          type="password"
          name="password"
          placeholder="至少8個字符"
          value={formData.password}
          onChange={handleChange}
          error={errors.password}
          required
        />

        <SquareInput
          label="確認密碼"
          type="password"
          name="confirmPassword"
          placeholder="再次輸入密碼"
          value={formData.confirmPassword}
          onChange={handleChange}
          error={errors.confirmPassword}
          required
        />

        <div className="flex items-center">
          <input
            id="agree-terms"
            name="agree-terms"
            type="checkbox"
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            required
          />
          <label htmlFor="agree-terms" className="ml-2 block text-sm text-gray-900">
            我同意{' '}
            <a href="#" className="text-blue-600 hover:text-blue-500">
              服務條款
            </a>
            {' '}和{' '}
            <a href="#" className="text-blue-600 hover:text-blue-500">
              隱私政策
            </a>
          </label>
        </div>

        <SquareButton
          type="submit"
          variant="primary"
          size="lg"
          loading={loading}
          className="w-full"
        >
          註冊帳戶
        </SquareButton>

        <p className="text-center text-sm text-gray-600">
          已有帳戶？{' '}
          <a href="/login" className="font-medium text-blue-600 hover:text-blue-500">
            立即登錄
          </a>
        </p>
      </form>
    </SquareCard>
  );
}