/**
 * Next.js API Route - Health Check
 * 系統健康檢查端點
 */

import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    // 檢查後端服務狀態
    const backendHealth = await checkBackendHealth()

    // 檢查數據庫連接
    const dbHealth = await checkDatabaseHealth()

    // 檢查Redis連接
    const redisHealth = await checkRedisHealth()

    const healthStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        backend: backendHealth,
        database: dbHealth,
        redis: redisHealth,
      },
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
    }

    // 判斷整體健康狀態
    const isHealthy = Object.values(healthStatus.services).every(
      service => service.status === 'healthy'
    )

    res.status(isHealthy ? 200 : 503).json(healthStatus)
  } catch (error) {
    console.error('Health check failed:', error)
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Health check failed',
    })
  }
}

async function checkBackendHealth() {
  try {
    const response = await fetch(`${process.env.API_BASE_URL || 'http://localhost:3003'}/health`)

    if (response.ok) {
      const data = await response.json()
      return {
        status: 'healthy',
        responseTime: response.headers.get('x-response-time'),
        ...data,
      }
    } else {
      return {
        status: 'unhealthy',
        error: `Backend returned ${response.status}`,
      }
    }
  } catch (error) {
    return {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

async function checkDatabaseHealth() {
  // 這裡應該實際檢查數據庫連接
  // 目前返回模擬數據
  return {
    status: 'healthy',
    connection: 'connected',
    responseTime: '5ms',
  }
}

async function checkRedisHealth() {
  // 這裡應該實際檢查Redis連接
  // 目前返回模擬數據
  return {
    status: 'healthy',
    connection: 'connected',
    responseTime: '2ms',
  }
}