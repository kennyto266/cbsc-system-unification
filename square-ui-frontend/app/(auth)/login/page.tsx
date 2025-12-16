'use client';

import { useState } from 'react';
import { SquareCard, SquareInput, SquareButton } from '@/components/ui';
import { AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // TODO: Implement actual login logic
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('登錄失敗');
      }

      const data = await response.json();
      // Store token and redirect
      window.location.href = '/dashboard';
    } catch (err) {
      setError('登錄失敗，請檢查您的憑據');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SquareCard>
      <form className="space-y-6" onSubmit={handleSubmit}>
        <h3 className="text-2xl font-semibold text-gray-900 text-center">
          登錄您的帳戶
        </h3>

        {error && (
          <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-md">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-sm text-red-700">{error}</span>
          </div>
        )}

        <SquareInput
          label="電子郵件"
          type="email"
          placeholder="example@cbsc.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <SquareInput
          label="密碼"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
              記住我
            </label>
          </div>

          <div className="text-sm">
            <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
              忘記密碼？
            </a>
          </div>
        </div>

        <SquareButton
          type="submit"
          variant="primary"
          size="lg"
          loading={loading}
          className="w-full"
        >
          登錄
        </SquareButton>

        <p className="text-center text-sm text-gray-600">
          還沒有帳戶？{' '}
          <a href="/register" className="font-medium text-blue-600 hover:text-blue-500">
            立即註冊
          </a>
        </p>
      </form>
    </SquareCard>
  );
}