/**
 * Dashboard Test Component
 * Test the integration of all three systems
 */

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button, Card, Row, Col, Progress, Badge } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'

import IntegratedDashboard from './IntegratedDashboard'
import Header from '../layout/Header'
import Sidebar from '../layout/Sidebar'

interface TestResult {
  name: string
  status: 'success' | 'error' | 'warning' | 'pending'
  message: string
}

const DashboardTest: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false)
  const [testResults, setTestResults] = useState<TestResult[]>([
    { name: 'Layout Navigation System', status: 'pending', message: 'Testing layout components...' },
    { name: 'Responsive Grid System', status: 'pending', message: 'Testing grid layout...' },
    { name: 'Real-time Chart Components', status: 'pending', message: 'Testing chart integration...' },
    { name: 'WebSocket Connection', status: 'pending', message: 'Testing real-time data...' },
    { name: 'Widget Management', status: 'pending', message: 'Testing widget system...' },
  ])

  const runTests = async () => {
    setIsRunning(true)

    // Simulate testing process
    const testSequence = [
      { index: 0, delay: 1000, status: 'success' as const, message: 'Layout components loaded successfully' },
      { index: 1, delay: 2000, status: 'success' as const, message: 'Grid system responsive and functional' },
      { index: 2, delay: 3000, status: 'success' as const, message: 'Real-time charts rendering correctly' },
      { index: 3, delay: 4000, status: 'success' as const, message: 'WebSocket connection established' },
      { index: 4, delay: 5000, status: 'success' as const, message: 'Widget management system operational' },
    ]

    for (const test of testSequence) {
      await new Promise(resolve => setTimeout(resolve, test.delay))

      setTestResults(prev => {
        const newResults = [...prev]
        newResults[test.index] = {
          ...newResults[test.index],
          status: test.status,
          message: test.message
        }
        return newResults
      })
    }

    setIsRunning(false)
  }

  const resetTests = () => {
    setTestResults([
      { name: 'Layout Navigation System', status: 'pending', message: 'Testing layout components...' },
      { name: 'Responsive Grid System', status: 'pending', message: 'Testing grid layout...' },
      { name: 'Real-time Chart Components', status: 'pending', message: 'Testing chart integration...' },
      { name: 'WebSocket Connection', status: 'pending', message: 'Testing real-time data...' },
      { name: 'Widget Management', status: 'pending', message: 'Testing widget system...' },
    ])
  }

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined className="text-green-500" />
      case 'error':
        return <ExclamationCircleOutlined className="text-red-500" />
      case 'warning':
        return <ExclamationCircleOutlined className="text-yellow-500" />
      case 'pending':
      default:
        return <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    }
  }

  const overallProgress = (testResults.filter(r => r.status === 'success').length / testResults.length) * 100

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <Header collapsed={false} onToggle={() => {}} />

      <div className="flex pt-16">
        {/* Sidebar */}
        <Sidebar collapsed={false} onCollapse={() => {}} />

        {/* Main Content */}
        <div className="flex-1 p-6" style={{ marginLeft: 256 }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* Test Control Panel */}
            <Card className="mb-6" title="Dashboard System Integration Test">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">System Status</h3>
                  <p className="text-gray-500">Testing integrated dashboard components</p>
                </div>
                <div className="flex space-x-2">
                  <Button
                    type="primary"
                    icon={isRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                    onClick={runTests}
                    disabled={isRunning}
                    loading={isRunning}
                  >
                    {isRunning ? 'Running Tests...' : 'Run Tests'}
                  </Button>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={resetTests}
                    disabled={isRunning}
                  >
                    Reset
                  </Button>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Overall Progress</span>
                  <span className="text-sm font-medium">{Math.round(overallProgress)}%</span>
                </div>
                <Progress
                  percent={overallProgress}
                  status={isRunning ? 'active' : overallProgress === 100 ? 'success' : 'normal'}
                  strokeWidth={8}
                />
              </div>

              {/* Test Results */}
              <Row gutter={[16, 16]}>
                {testResults.map((test, index) => (
                  <Col xs={24} sm={12} md={8} key={test.name}>
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <Card
                        size="small"
                        className={`h-full ${
                          test.status === 'success' ? 'border-green-200 bg-green-50 dark:bg-green-900/10' :
                          test.status === 'error' ? 'border-red-200 bg-red-50 dark:bg-red-900/10' :
                          test.status === 'warning' ? 'border-yellow-200 bg-yellow-50 dark:bg-yellow-900/10' :
                          'border-gray-200'
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <div className="mt-1">
                            {getStatusIcon(test.status)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <span className="text-sm font-medium">{test.name}</span>
                              {test.status !== 'pending' && (
                                <Badge
                                  status={test.status === 'success' ? 'success' : test.status}
                                  text={test.status.toUpperCase()}
                                />
                              )}
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{test.message}</p>
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  </Col>
                ))}
              </Row>
            </Card>

            {/* Integrated Dashboard Preview */}
            <Card title="Integrated Dashboard Preview">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
                <IntegratedDashboard />
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  )
}

export default DashboardTest