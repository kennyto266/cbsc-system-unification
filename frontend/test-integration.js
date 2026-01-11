/**
 * Frontend Integration Test Script
 * 前端集成测试脚本
 *
 * 测试内容：
 * 1. 端口配置验证
 * 2. API连接测试
 * 3. 组件渲染测试
 */

const http = require('http');

// 测试端口是否可用
async function testPort(port) {
  return new Promise((resolve) => {
    const req = http.request(
      {
        hostname: 'localhost',
        port: port,
        path: '/',
        method: 'GET',
        timeout: 3000,
      },
      (res) => {
        console.log(`✅ Port ${port} is responsive`);
        resolve(true);
      }
    );

    req.on('error', () => {
      console.log(`❌ Port ${port} is not responsive`);
      resolve(false);
    });

    req.end();
  });
}

// 测试API连接
async function testAPIConnection() {
  const API_URL = 'http://localhost:9000';

  try {
    const response = await fetch(`${API_URL}/api/health`, {
      method: 'GET',
      timeout: 3000,
    });

    if (response.ok) {
      console.log('✅ Backend API is connected');
      return true;
    } else {
      console.log('❌ Backend API returned error:', response.status);
      return false;
    }
  } catch (error) {
    console.log('❌ Cannot connect to Backend API:', error.message);
    return false;
  }
}

// 主测试函数
async function runTests() {
  console.log('🚀 Starting Frontend Integration Tests...\n');

  // 测试端口
  console.log('1. Testing port configuration...');
  const isPort3000Available = await testPort(3000);

  if (!isPort3000Available) {
    console.log('\n⚠️  Port 3000 is not available. Please check if the frontend is running.');
    console.log('   To start the frontend, run: cd frontend && npm start\n');
  }

  // 测试API连接
  console.log('\n2. Testing API connection...');
  const isAPIConnected = await testAPIConnection();

  // 测试总结
  console.log('\n3. Test Summary:');
  console.log(`   - Port 3000: ${isPort3000Available ? '✅ Available' : '❌ Not Available'}`);
  console.log(`   - API Connection: ${isAPIConnected ? '✅ Connected' : '❌ Not Connected'}`);

  console.log('\n📋 Next Steps:');
  if (!isPort3000Available) {
    console.log('   1. Start the frontend: cd frontend && npm start');
  }
  if (!isAPIConnected) {
    console.log('   2. Start the backend API server (port 9000)');
  }
  if (isPort3000Available && isAPIConnected) {
    console.log('   ✅ All systems ready! Open http://localhost:3000 in your browser');
  }
}

// 运行测试
runTests().catch(console.error);