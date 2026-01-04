/**
 * Error Page Component
 * Display various error states
 */

import React from 'react'
import { Result, Button } from 'antd'
import { useNavigate } from 'react-router-dom'

interface ErrorPageProps {
  status?: number
  title?: string
  subTitle?: string
}

export const ErrorPage: React.FC<ErrorPageProps> = ({
  status = 404,
  title = '404',
  subTitle = 'Sorry, the page you visited does not exist.',
}) => {
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Result
        status={status as any}
        title={title}
        subTitle={subTitle}
        extra={
          <Button type="primary" onClick={() => navigate('/')}>
            Back Home
          </Button>
        }
      />
    </div>
  )
}

export default ErrorPage
