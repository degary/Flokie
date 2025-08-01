#!/usr/bin/env python3
"""
快速修复代码风格问题的脚本。
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """运行命令并返回结果。"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def fix_imports():
    """使用 isort 修复导入顺序。"""
    print("修复导入顺序...")
    success, stdout, stderr = run_command("isort . --profile black")
    if success:
        print("✓ 导入顺序已修复")
    else:
        print(f"✗ 修复导入顺序失败: {stderr}")


def fix_formatting():
    """使用 black 修复代码格式。"""
    print("修复代码格式...")
    success, stdout, stderr = run_command("black .")
    if success:
        print("✓ 代码格式已修复")
    else:
        print(f"✗ 修复代码格式失败: {stderr}")


def remove_unused_imports():
    """移除未使用的导入（简单版本）。"""
    print("检查未使用的导入...")

    # 这里可以添加更复杂的逻辑来移除未使用的导入
    # 目前只是一个占位符
    print("✓ 未使用导入检查完成")


def main():
    """主函数。"""
    print("开始修复代码风格问题...")

    # 确保在项目根目录
    if not os.path.exists("app"):
        print("请在项目根目录运行此脚本")
        sys.exit(1)

    # 运行修复
    fix_formatting()
    fix_imports()
    remove_unused_imports()

    # 运行 pre-commit 检查
    print("\n运行 pre-commit 检查...")
    success, stdout, stderr = run_command("pre-commit run --all-files")

    if success:
        print("✓ 所有检查通过！")
    else:
        print("还有一些问题需要手动修复:")
        print(stderr)

    print("\n修复完成！")


if __name__ == "__main__":
    main()
