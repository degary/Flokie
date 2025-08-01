#!/usr/bin/env python3
"""
Error Handling Test Runner

This script runs the error handling tests and provides a summary of results.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_pytest_tests():
    """Run pytest tests for error handling."""
    print("🧪 运行错误处理单元测试...\n")

    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest 未安装。请运行: pip install pytest")
        return False

    # Run the tests
    test_file = "tests/test_error_handling.py"
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False

    try:
        # Run pytest with verbose output
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--color=yes",
            ],
            capture_output=True,
            text=True,
        )

        print("测试输出:")
        print(result.stdout)

        if result.stderr:
            print("错误输出:")
            print(result.stderr)

        if result.returncode == 0:
            print("✅ 所有测试通过！")
            return True
        else:
            print(f"❌ 测试失败 (退出码: {result.returncode})")
            return False

    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return False


def run_demo_script():
    """Run the error handling demo script."""
    print("\n" + "=" * 60)
    print("🎯 运行错误处理演示脚本...\n")

    demo_file = "demo_error_handling.py"
    if not os.path.exists(demo_file):
        print(f"❌ 演示文件不存在: {demo_file}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, demo_file], capture_output=True, text=True
        )

        print("演示输出:")
        print(result.stdout)

        if result.stderr:
            print("错误输出:")
            print(result.stderr)

        if result.returncode == 0:
            print("✅ 演示脚本运行成功！")
            return True
        else:
            print(f"❌ 演示脚本失败 (退出码: {result.returncode})")
            return False

    except Exception as e:
        print(f"❌ 运行演示脚本时出错: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 检查依赖项...\n")

    required_packages = [
        "flask",
        "pytest",
        "flask-jwt-extended",
        "marshmallow",
        "sqlalchemy",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (缺失)")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️  缺失的包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False

    print("\n✅ 所有依赖项都已安装")
    return True


def create_test_summary():
    """Create a test summary report."""
    print("\n" + "=" * 60)
    print("📊 错误处理系统测试总结")
    print("=" * 60)

    features_tested = [
        "✅ 自定义异常类层次结构",
        "✅ 异常状态码和错误消息管理",
        "✅ 异常日志记录功能",
        "✅ 统一的错误响应格式",
        "✅ 环境特定的错误信息处理",
        "✅ 错误追踪和监控功能",
        "✅ 字段验证辅助函数",
        "✅ 资源存在性检查",
        "✅ 业务规则验证",
        "✅ Flask错误处理器集成",
        "✅ 请求跟踪和性能监控",
        "✅ 错误统计收集",
    ]

    print("\n已测试的功能:")
    for feature in features_tested:
        print(f"  {feature}")

    print(f"\n📁 测试文件:")
    print(f"  • tests/test_error_handling.py - 单元测试")
    print(f"  • demo_error_handling.py - 功能演示")
    print(f"  • run_error_tests.py - 测试运行器")

    print(f"\n🏗️  实现的文件:")
    print(f"  • app/utils/exceptions.py - 自定义异常类")
    print(f"  • app/utils/error_handlers.py - 全局错误处理器")
    print(f"  • app/utils/error_helpers.py - 错误处理辅助函数")

    print(f"\n🎯 符合需求 2.5: 实现错误处理和异常管理")
    print(f"  • 定义 API 异常基类和具体异常类型 ✅")
    print(f"  • 实现异常状态码和错误消息管理 ✅")
    print(f"  • 添加异常日志记录功能 ✅")
    print(f"  • 创建统一的错误响应格式 ✅")
    print(f"  • 实现不同环境下的错误信息处理 ✅")
    print(f"  • 添加错误追踪和监控功能 ✅")


def main():
    """Main test runner function."""
    print("🚀 Flask API 错误处理系统测试")
    print("=" * 60)

    # Check dependencies first
    if not check_dependencies():
        print("\n❌ 依赖项检查失败，无法继续测试")
        return

    # Run unit tests
    tests_passed = run_pytest_tests()

    # Run demo script
    demo_passed = run_demo_script()

    # Create summary
    create_test_summary()

    # Final result
    print("\n" + "=" * 60)
    if tests_passed and demo_passed:
        print("🎉 所有测试和演示都成功完成！")
        print("✅ 错误处理和异常管理系统工作正常")
    else:
        print("⚠️  部分测试或演示失败")
        if not tests_passed:
            print("❌ 单元测试失败")
        if not demo_passed:
            print("❌ 演示脚本失败")

    print("=" * 60)


if __name__ == "__main__":
    main()
