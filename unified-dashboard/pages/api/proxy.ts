/**
 * Next.js API Route - Proxy Handler
 * API代理處理，轉發請求到後端服務
 */

import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // 只處理指定的HTTP方法
  if (['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].includes(req.method || '')) {
    try {
      const { query } = req
      const path = Array.isArray(query.path) ? query.path.join('/') : query.path || ''

      const backendUrl = `${process.env.API_BASE_URL || 'http://localhost:3003'}/${path}`

      // 構建代理請求選項
      const proxyOptions: RequestInit = {
        method: req.method,
        headers: {
          'Content-Type': 'application/json',
          // 轉發客戶端標頭
          ...(req.headers.authorization && {
            Authorization: req.headers.authorization
          }),
          ...(req.headers['x-api-key'] && {
            'X-API-Key': req.headers['x-api-key']
          }),
          // 添加代理標頭
          'X-Forwarded-For': req.socket.remoteAddress,
          'X-Forwarded-Proto': req.socket.encrypted ? 'https' : 'http',
          'X-Forwarded-Host': req.headers.host,
        },
      }

      // 如果有請求體，添加到代理請求中
      if (['POST', 'PUT', 'PATCH'].includes(req.method || '') && req.body) {
        proxyOptions.body = JSON.stringify(req.body)
      }

      // 發送代理請求
      const response = await fetch(backendUrl, proxyOptions)

      // 獲取響應數據
      let responseData
      const contentType = response.headers.get('content-type')

      if (contentType?.includes('application/json')) {
        responseData = await response.json()
      } else {
        responseData = await response.text()
      }

      // 設置響應狀態和標頭
      res.status(response.status)

      // 轉發重要的響應標頭
      const forwardHeaders = [
        'content-type',
        'cache-control',
        'etag',
        'last-modified',
        'x-rate-limit-remaining',
        'x-rate-limit-reset',
      ]

      forwardHeaders.forEach(header => {
        const value = response.headers.get(header)
        if (value) {
          res.setHeader(header, value)
        }
      })

      // 添加代理標頭
      res.setHeader('X-Proxied-By', 'Next.js')
      res.setHeader('X-Backend-URL', backendUrl)

      // 發送響應
      res.send(responseData)
    } catch (error) {
      console.error('Proxy request failed:', error)
      res.status(502).json({
        error: 'Bad Gateway',
        message: 'Proxy request failed',
        timestamp: new Date().toISOString(),
      })
    }
  } else {
    // 不支持的方法
    res.setHeader('Allow', ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    res.status(405).json({
      error: 'Method Not Allowed',
      message: `Method ${req.method} is not allowed`,
    })
  }
}