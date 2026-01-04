#!/usr/bin/env python3
"""
环境配置验证脚本
验证所有必需的环境变量是否已设置
"""
import os
import sys
from typing import List, Dict, Any


# 定义各环境必需的变量
REQUIRED_VARS = {
    "all": [
        "ENVIRONMENT",
        "DATABASE_URL",
        "REDIS_URL",
        "JWT_SECRET",
        "SECRET_KEY",
    ],
    "production": [
        "JWT_SECRET",
        "SECRET_KEY",
        "REFRESH_SECRET_KEY",
        "SESSION_SECRET",
        "ENCRYPTION_KEY",
        "DATABASE_URL",
        "REDIS_PASSWORD",
    ],
    "development": [],
    "test": [],
}

# 定义可选但推荐的变量
RECOMMENDED_VARS = [
    "API_HOST",
    "API_PORT",
    "CORS_ORIGINS",
    "LOG_LEVEL",
    "FRONTEND_PORT",
    "WEBSOCKET_PORT",
]


def check_variable_length(name: str, value: str, min_length: int = 32) -> bool:
    """检查变量值的长度是否满足要求"""
    if len(value) < min_length:
        print(f"❌ {name}: 长度不足 ({len(value)} < {min_length})")
        return False
    return True


def check_secret_strength(name: str, value: str) -> bool:
    """检查密钥强度"""
    issues = []

    if len(value) < 32:
        issues.append(f"长度不足 ({len(value)} < 32)")

    # 检查是否为默认值或占位符
    placeholder_patterns = [
        "change_this",
        "your_",
        "change",
        "example",
        "localhost",
        "dev_",
        "test_",
        "demo",
    ]

    value_lower = value.lower()
    if any(pattern in value_lower for pattern in placeholder_patterns):
        issues.append("包含占位符或默认值")

    if issues:
        print(f"⚠️  {name}: {', '.join(issues)}")
        return False

    return True


def validate_environment() -> Dict[str, Any]:
    """验证环境配置"""
    environment = os.getenv("ENVIRONMENT", "development")

    results = {
        "environment": environment,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "valid": True,
    }

    # 检查必需的变量
    required = REQUIRED_VARS.get("all", []) + REQUIRED_VARS.get(environment, [])

    for var in required:
        value = os.getenv(var)
        if not value:
            results["missing"].append(var)
            results["valid"] = False
        elif var in ["JWT_SECRET", "SECRET_KEY", "REFRESH_SECRET_KEY", "SESSION_SECRET", "ENCRYPTION_KEY"]:
            # 对密钥进行额外检查
            if environment == "production":
                if not check_secret_strength(var, value):
                    results["warnings"].append(var)

    # 检查推荐的变量
    for var in RECOMMENDED_VARS:
        if not os.getenv(var):
            results["warnings"].append(f"{var} (未设置)")

    # 特定环境的额外检查
    if environment == "production":
        # 生产环境必须检查
        if os.getenv("DEBUG") == "true":
            results["invalid"].append("DEBUG=true 在生产环境中不安全")
            results["valid"] = False

        if os.getenv("CORS_ORIGINS", "").startswith("http://localhost"):
            results["warnings"].append("CORS_ORIGINS 包含 localhost，生产环境应该移除")

    return results


def print_results(results: Dict[str, Any]):
    """打印验证结果"""
    print(f"\n{'='*60}")
    print(f"环境配置验证报告")
    print(f"{'='*60}")
    print(f"当前环境: {results['environment'].upper()}")
    print(f"验证状态: {'✅ 通过' if results['valid'] else '❌ 失败'}")
    print(f"{'='*60}\n")

    if results["missing"]:
        print(f"❌ 缺失的必需变量 ({len(results['missing'])}):")
        for var in results["missing"]:
            print(f"   - {var}")
        print()

    if results["invalid"]:
        print(f"❌ 配置错误 ({len(results['invalid'])}):")
        for issue in results["invalid"]:
            print(f"   - {issue}")
        print()

    if results["warnings"]:
        print(f"⚠️  警告 ({len(results['warnings'])}):")
        for warning in results["warnings"]:
            print(f"   - {warning}")
        print()

    if results["valid"] and not results["warnings"]:
        print("✅ 所有配置项正常")
        print()

    print(f"{'='*60}\n")


def main():
    """主函数"""
    print("CBSC 环境配置验证工具")
    print("正在检查环境配置...\n")

    results = validate_environment()
    print_results(results)

    # 如果验证失败，返回错误代码
    sys.exit(0 if results["valid"] else 1)


if __name__ == "__main__":
    main()
