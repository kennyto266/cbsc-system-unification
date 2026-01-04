"""
CODEX-- 后端服务综合测试脚本
Comprehensive Backend Test Script
"""

import subprocess
import time
import requests
import json
import sys
from typing import Dict, List, Tuple

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text:^70}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")

def print_success(text: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def check_python_version() -> bool:
    """检查Python版本"""
    print_header("检查Python版本")
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 8:
        print_success("Python版本符合要求 (>= 3.8)")
        return True
    else:
        print_error("Python版本过低，需要 >= 3.8")
        return False

def check_dependencies() -> bool:
    """检查依赖包"""
    print_header("检查依赖包")

    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'redis',
        'pydantic'
    ]

    all_ok = True
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package}")
        except ImportError:
            print_error(f"{package} - 未安装")
            all_ok = False

    return all_ok

def test_import(module_path: str, description: str) -> bool:
    """测试模块导入"""
    print(f"测试 {description}... ", end="", flush=True)
    try:
        subprocess.run(
            [sys.executable, "-c", f"import sys; sys.path.insert(0, '.'); from {module_path}"],
            capture_output=True,
            timeout=10,
            check=True,
            text=True
        )
        print_success("OK")
        return True
    except subprocess.TimeoutExpired:
        print_error("超时")
        return False
    except subprocess.CalledProcessError as e:
        print_error(f"失败")
        if e.stderr:
            print(f"   错误: {e.stderr.strip()[:100]}")
        return False

def test_api_imports() -> Dict[str, bool]:
    """测试API导入"""
    print_header("测试API模块导入")

    tests = {
        "src.api.main": "主API",
        "backend.main": "Backend API",
        "src.auth_simple": "认证服务",
        "src.api.unified_strategy_service": "统一策略服务",
        "src.api.strategy_execution_engine": "策略执行引擎",
    }

    results = {}
    for module, desc in tests.items():
        results[desc] = test_import(module, desc)

    return results

def start_api_server(port: int = 3003) -> subprocess.Popen:
    """启动API服务器"""
    print_info(f"启动API服务器 (端口 {port})...")

    cmd = [sys.executable, "-m", "uvicorn", "src.api.main:app",
           "--host", "127.0.0.1", "--port", str(port)]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 等待服务器启动
    time.sleep(3)

    if process.poll() is None:
        print_success(f"API服务器已启动 (PID: {process.pid})")
        return process
    else:
        print_error("API服务器启动失败")
        stdout, stderr = process.communicate()
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return None

def test_endpoint(url: str, method: str = "GET", data: dict = None) -> Tuple[bool, dict]:
    """测试API端点"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            return False, {"error": "Unsupported method"}

        try:
            return response.status_code < 400, response.json()
        except:
            return response.status_code < 400, {"status_code": response.status_code}

    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}

def test_api_endpoints() -> Dict[str, bool]:
    """测试API端点"""
    print_header("测试API端点")

    base_url = "http://127.0.0.1:3003"

    tests = {
        "根端点": f"{base_url}/",
        "健康检查": f"{base_url}/health",
        "API文档": f"{base_url}/docs",
        "存活探针": f"{base_url}/live",
        "就绪探针": f"{base_url}/ready",
    }

    results = {}
    for name, url in tests.items():
        success, response = test_endpoint(url)
        results[name] = success
        if success:
            print_success(f"{name} - HTTP 200")
        else:
            print_error(f"{name} - {response.get('error', 'Unknown error')}")

    return results

def test_authenticated_endpoints():
    """测试需要认证的端点"""
    print_header("测试需要认证的端点")

    base_url = "http://127.0.0.1:3003"

    # 首先尝试登录
    print_info("尝试登录...")
    success, response = test_endpoint(
        f"{base_url}/api/auth/login",
        "POST",
        {"username": "test", "password": "test"}
    )

    if success and "access_token" in response:
        print_success("登录成功")
        token = response["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 测试需要认证的端点
        endpoints = [
            ("用户资料", f"{base_url}/api/user/profile"),
            ("策略列表", f"{base_url}/api/personal-strategies/strategies"),
            ("用户统计", f"{base_url}/api/user/statistics"),
        ]

        for name, url in endpoints:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    print_success(f"{name} - OK")
                else:
                    print_warning(f"{name} - HTTP {response.status_code}")
            except Exception as e:
                print_error(f"{name} - {e}")
    else:
        print_warning("登录失败 (需要先创建用户)")
        print_info("提示: 运行 python create_test_user.py 创建测试用户")

def test_database_connections():
    """测试数据库连接"""
    print_header("测试数据库连接")

    # SQLite
    print_info("检查 SQLite 数据库...")
    import os
    if os.path.exists("user_management.db"):
        size = os.path.getsize("user_management.db")
        print_success(f"SQLite 数据库存在 (大小: {size} bytes)")
    else:
        print_warning("SQLite 数据库不存在")

    # PostgreSQL
    print_info("检查 PostgreSQL 连接...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="cbsc",
            user="postgres",
            password="postgres"
        )
        print_success("PostgreSQL 连接成功")
        conn.close()
    except Exception as e:
        print_warning(f"PostgreSQL 连接失败: {e}")

    # Redis
    print_info("检查 Redis 连接...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print_success("Redis 连接成功")
    except Exception as e:
        print_warning(f"Redis 连接失败: {e}")

def generate_report(results: Dict[str, dict]):
    """生成测试报告"""
    print_header("测试报告摘要")

    total = 0
    passed = 0

    for category, tests in results.items():
        print(f"\n{category}:")
        for test_name, result in tests.items():
            total += 1
            if result:
                passed += 1
                print_success(f"  {test_name}")
            else:
                print_error(f"  {test_name}")

    print(f"\n{Colors.BOLD}总计: {passed}/{total} 通过 ({passed*100//total if total > 0 else 0}%){Colors.RESET}")

def main():
    """主函数"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          CODEX-- 后端服务综合测试脚本                           ║")
    print("║          Comprehensive Backend Test Script                      ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")

    results = {}

    # Phase 1: 环境检查
    results["环境检查"] = {
        "Python版本": check_python_version(),
        "依赖包": check_dependencies(),
    }

    # Phase 2: 模块导入测试
    results["模块导入"] = test_api_imports()

    # Phase 3: 启动API服务器
    print_header("启动API服务器")
    api_process = start_api_server(3003)

    if api_process:
        try:
            # Phase 4: API端点测试
            results["API端点"] = test_api_endpoints()

            # Phase 5: 认证端点测试
            test_authenticated_endpoints()

            # Phase 6: 数据库连接测试
            test_database_connections()

        finally:
            # 停止API服务器
            print_info("\n停止API服务器...")
            api_process.terminate()
            time.sleep(1)
            if api_process.poll() is None:
                api_process.kill()
            print_success("API服务器已停止")

    # 生成报告
    generate_report(results)

    print(f"\n{Colors.BOLD}测试完成!{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}测试被中断{Colors.RESET}")
        sys.exit(1)
