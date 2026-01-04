/**
 * NotFound Page - 404 錯誤頁面
 * 
 * 當用戶訪問不存在的路徑時顯示
 */

import { Button, Result } from 'antd';
import { useNavigate } from 'react-router-dom';

/**
 * 404 Not Found 頁面
 */
export const NotFound: React.FC = () => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <Result
        status="404"
        title="404"
        subTitle="抱歉，您訪問的頁面不存在。"
        extra={
          <>
            <Button type="primary" onClick={handleGoHome}>
              返回首頁
            </Button>
            <Button className="ml-2" onClick={handleGoBack}>
              返回上一頁
            </Button>
          </>
        }
      />
    </div>
  );
};

export default NotFound;
