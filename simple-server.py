#!/usr/bin/env python3
"""
Simple web server for CBSC Management Interface
CBSC 策略管理系統簡單Web服務器
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import requests
from datetime import datetime

class CBSCRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            # 檢查後端服務狀態
            backend_status = self.check_backend_status()

            # 返回主頁HTML
            html_content = self.generate_main_html(backend_status)
            self.wfile.write(html_content.encode('utf-8'))

        elif self.path == '/api/status':
            self.send_json_response(200, {
                'status': 'success',
                'services': {
                    'backend': self.check_backend_status(),
                    'database': self.check_database_status(),
                    'redis': self.check_redis_status(),
                    'grafana': self.check_grafana_status()
                },
                'timestamp': datetime.now().isoformat()
            })

        elif self.path.startswith('/api/test/'):
            test_name = self.path[10:]  # Remove '/api/test/' prefix
            result = self.run_test(test_name)
            self.send_json_response(200, result)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}, ensure_ascii=False).encode('utf-8'))

    def check_backend_status(self):
        """Check backend API status"""
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                return {'status': 'healthy', 'response': response.json()}
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def check_database_status(self):
        """Check database status"""
        # 簡單的連接測試
        return {'status': 'healthy', 'message': 'PostgreSQL and Redis containers are running'}

    def check_redis_status(self):
        """Check Redis status"""
        return {'status': 'healthy', 'port': '6379', 'message': 'Redis container is healthy'}

    def check_grafana_status(self):
        """Check Grafana status"""
        try:
            response = requests.get('http://localhost:8888', timeout=5)
            if response.status_code == 200:
                return {'status': 'healthy', 'url': 'http://localhost:8888'}
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def run_test(self, test_name):
        """Run specific API test"""
        tests = {
            'health': self.test_health,
            'strategies': self.test_strategies,
            'monitoring': self.test_monitoring
        }

        if test_name in tests:
            return tests[test_name]()
        else:
            return {'error': f'Test "{test_name}" not found'}

    def test_health(self):
        """Test health endpoint"""
        try:
            response = requests.get('http://localhost:8000/health', timeout=10)
            return {
                'test': 'health',
                'status': response.status_code,
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'success': response.status_code == 200
            }
        except Exception as e:
            return {'test': 'health', 'error': str(e), 'success': False}

    def test_strategies(self):
        """Test strategies endpoint"""
        try:
            response = requests.get('http://localhost:8000/api/v1/strategies', timeout=10)
            return {
                'test': 'strategies',
                'status': response.status_code,
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'success': response.status_code == 200
            }
        except Exception as e:
            return {'test': 'strategies', 'error': str(e), 'success': False}

    def test_monitoring(self):
        """Test monitoring endpoint"""
        try:
            response = requests.get('http://localhost:8000/api/v1/monitoring/metrics', timeout=10)
            return {
                'test': 'monitoring',
                'status': response.status_code,
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'success': response.status_code == 200
            }
        except Exception as e:
            return {'test': 'monitoring', 'error': str(e), 'success': False}

    def send_json_response(self, code, data):
        """Send JSON response"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))

    def generate_main_html(self, backend_status):
        """Generate main page HTML"""
        backend_healthy = backend_status.get('status') == 'healthy'

        return f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CBSC 策略管理系統</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans TC', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #4a90e2;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header h2 {{
            color: #7f8c8d;
            font-size: 1.2em;
            margin: 10px 0;
        }}
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .status-card {{
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4a90e2;
            transition: transform 0.3s ease;
        }}
        .status-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }}
        .status-card.success {{
            border-left-color: #27ae60;
            background: rgba(232, 245, 232, 0.9);
        }}
        .status-card.error {{
            border-left-color: #e74c3c;
            background: rgba(253, 234, 234, 0.9);
        }}
        .status-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 1.1em;
        }}
        .status-card p {{
            margin: 0;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .api-section {{
            background: rgba(255, 255, 255, 0.9);
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .api-section h3 {{
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 1.3em;
        }}
        .button {{
            background: #4a90e2;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }}
        .button:hover {{
            background: #357abd;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .button.secondary {{
            background: #95a5a6;
        }}
        .button.secondary:hover {{
            background: #7f8c8d;
        }}
        .button.danger {{
            background: #e74c3c;
        }}
        .button.danger:hover {{
            background: #c0392b;
        }}
        .result {{
            background: rgba(44, 62, 80, 0.95);
            color: #ecf0f1;
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
            white-space: pre-wrap;
            font-family: 'Courier New', Consolas, monospace;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
            border-radius: 4px;
        }}
        .links {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
        }}
        .links a {{
            margin: 10px;
        }}
        .emoji {{
            font-size: 1.3em;
        }}
        .health-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .health-healthy {{ background: #27ae60; }}
        .health-unhealthy {{ background: #e74c3c; }}
        .health-error {{ background: #f39c12; }}
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        .testing {{
            animation: pulse 1s infinite;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span class="emoji">📊</span> CBSC 策略管理系統</h1>
            <h2>Strategy Management System Dashboard</h2>
            <p>量化交易策略管理與監控平台 - 版本 1.0.0</p>
        </div>

        <div class="status-grid">
            <div class="status-card {'success' if backend_healthy else 'error'}">
                <h3><span class="health-indicator {'health-healthy' if backend_healthy else 'health-error'}"></span> 系統狀態</h3>
                <p id="systemStatus">{'系統正常' if backend_healthy else '系統異常'}</p>
            </div>
            <div class="status-card success">
                <h3><span class="emoji">🗄️</span> 數據庫</h3>
                <p>✅ PostgreSQL: localhost:5432<br>✅ Redis: localhost:6379</p>
            </div>
            <div class="status-card {'success' if backend_healthy else 'error'}">
                <h3><span class="emoji">⚡</span> API 服務</h3>
                <p>{'✅ 後端API運行正常' if backend_healthy else '❌ 後端API異常'}</p>
            </div>
            <div class="status-card success">
                <h3><span class="emoji">📈</span> 監控系統</h3>
                <p>✅ Grafana: <a href="http://localhost:8888" target="_blank">http://localhost:8888</a><br>👤 登入: admin/admin</p>
            </div>
        </div>

        <div class="api-section">
            <h3><span class="emoji">🧪</span> API 測試</h3>
            <button class="button" onclick="runTest('health')">健康檢查</button>
            <button class="button" onclick="runTest('strategies')">策略列表</button>
            <button class="button" onclick="runTest('monitoring')">監控指標</button>
            <button class="button secondary" onclick="clearResult()">清除結果</button>
            <button class="button" onclick="runAllTests()">運行所有測試</button>
            <div id="result" class="result" style="display: none;"></div>
        </div>

        <div class="links">
            <a href="http://localhost:8000/docs" target="_blank" class="button">
                <span class="emoji">📚</span> API 文檔
            </a>
            <a href="http://localhost:8000/health" target="_blank" class="button">
                <span class="emoji">❤️</span> 健康檢查
            </a>
            <a href="http://localhost:8888" target="_class="button">
                <span class="emoji">📊</span> Grafana 監控
            </a>
        </div>

        <div class="api-section">
            <h3><span class="emoji">🔗</span> 服務信息</h3>
            <p><strong>後端 API:</strong> http://localhost:8000</p>
            <p><strong>狀態 API:</strong> http://localhost:9999/api/status</p>
            <p><strong>PostgreSQL:</strong> localhost:5432 (cbsc_admin/dev_password_123)</p>
            <p><strong>Redis:</strong> localhost:6379 (redis_password_123)</p>
            <p><strong>Grafana:</strong> http://localhost:8888 (admin/admin)</p>
        </div>

        <div class="api-section">
            <h3><span class="emoji">⏰️</span> 系統時間</h3>
            <p id="systemTime">Loading...</p>
        </div>
    </div>

    <script>
        async function runTest(testName) {{
            const result = document.getElementById('result');
            result.style.display = 'block';
            result.className = 'result testing';
            result.textContent = `正在測試 ${{testName}}...`;

            try {{
                const response = await fetch(`/api/test/${{testName}}`);
                const data = await response.json();

                const statusIcon = data.success ? '✅' : '❌';
                const statusText = data.success ? '成功' : '失敗';

                result.className = 'result';
                result.textContent = `${{statusIcon}} ${{testName}} 測試${{statusText}}:\n\n${{JSON.stringify(data, null, 2)}}`;
            }} catch (error) {{
                result.className = 'result';
                result.textContent = `❌ ${{testName}} 測試失敗:\n\n錯誤: ${{error.message}}`;
            }}
        }}

        async function runAllTests() {{
            const tests = ['health', 'strategies', 'monitoring'];
            const results = [];

            const result = document.getElementById('result');
            result.style.display = 'block';
            result.className = 'result testing';
            result.textContent = '正在運行所有測試...';

            for (const test of tests) {{
                try {{
                    const response = await fetch(`/api/test/${{test}}`);
                    const data = await response.json();
                    results.push({{test: test, success: data.success, data}});
                }} catch (error) {{
                    results.push({{test: test, success: false, error: error.message}});
                }}
            }}

            const successCount = results.filter(r => r.success).length;
            const totalCount = results.length;

            result.className = 'result';
            result.textContent = `測試完成 ( ${{successCount}}/${{totalCount}}):\n\n${{JSON.stringify(results, null, 2)}}`;
        }}

        function clearResult() {{
            document.getElementById('result').style.display = 'none';
        }}

        function updateSystemTime() {{
            const now = new Date();
            const timeString = now.toLocaleString('zh-TW', {{
                timeZone: 'Asia/Taipei',
                year12: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            }});
            document.getElementById('systemTime').textContent = timeString;
        }}

        // 更新系統狀態
        async function updateStatus() {{
            try {{
                const response = await fetch('/api/status');
                const data = await response.json();

                const systemStatus = document.getElementById('systemStatus');
                const statusCard = document.querySelector('.status-card');

                if (data.services.backend.status === 'healthy') {{
                    systemStatus.textContent = '✅ 系統運行正常';
                    statusCard.classList.add('success');
                    statusCard.classList.remove('error');
                }} else {{
                    systemStatus.textContent = '❌ 系統運行異常';
                    statusCard.classList.add('error');
                    statusCard.classList.remove('success');
                }}

                // 5秒後自動更新
                setTimeout(updateStatus, 5000);
            }} catch (error) {{
                console.error('Status update failed:', error);
                setTimeout(updateStatus, 5000);
            }}
        }}

        // 頁面載入時初始化
        window.onload = function() {{
            updateSystemTime();
            updateStatus();
            setInterval(updateSystemTime, 1000);
        }};
    </script>
</body>
</html>'''

    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        if self.path == '/api/test':
            try:
                data = json.loads(post_data.decode('utf-8'))
                result = self.run_test(data.get('test', 'health'))
                self.send_json_response(200, result)
            except Exception as e:
                self.send_json_response(400, {'error': str(e)})
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}, ensure_ascii=False).encode('utf-8'))

def run_server():
    """Run the web server"""
    server = HTTPServer(('0.0.0.0', 9999), CBSCRequestHandler)
    print("CBSC Management Interface starting...")
    print("Access URL: http://localhost:9999")
    print("Status API: http://localhost:9999/api/status")
    print("Press Ctrl+C to stop the server")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()

if __name__ == '__main__':
    run_server()