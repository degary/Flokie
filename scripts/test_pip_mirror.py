#!/usr/bin/env python3
"""
测试 pip 镜像源配置脚本

这个脚本用于测试 pip 镜像源是否配置正确，并测试下载速度。
"""

import json
import subprocess
import sys
import time
from urllib.parse import urlparse

import requests


def print_info(message):
    """打印信息"""
    print(f"ℹ️  {message}")


def print_success(message):
    """打印成功信息"""
    print(f"✅ {message}")


def print_error(message):
    """打印错误信息"""
    print(f"❌ {message}")


def print_warning(message):
    """打印警告信息"""
    print(f"⚠️  {message}")


def get_pip_config():
    """获取当前 pip 配置"""
    try:
        result = subprocess.run(
            ["pip", "config", "list"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def test_mirror_speed(mirror_url, package_name="requests", timeout=10):
    """测试镜像源速度"""
    try:
        # 构建包的 JSON API URL
        parsed_url = urlparse(mirror_url)
        if "simple" in mirror_url:
            # 对于 simple API，我们测试主页
            test_url = mirror_url
        else:
            # 对于其他 API，构建包的 JSON URL
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            test_url = f"{base_url}/pypi/{package_name}/json"

        print_info(f"测试镜像源: {mirror_url}")
        print_info(f"测试 URL: {test_url}")

        start_time = time.time()
        response = requests.get(test_url, timeout=timeout)
        end_time = time.time()

        response_time = end_time - start_time

        if response.status_code == 200:
            print_success(f"响应时间: {response_time:.2f} 秒")
            return response_time
        else:
            print_error(f"HTTP 状态码: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print_error(f"请求超时 (>{timeout}s)")
        return None
    except requests.exceptions.RequestException as e:
        print_error(f"请求失败: {e}")
        return None


def test_pip_install_speed(package_name="requests", use_cache=False):
    """测试 pip 安装速度"""
    try:
        print_info(f"测试 pip 安装速度: {package_name}")

        cmd = ["pip", "install", "--dry-run", package_name]
        if not use_cache:
            cmd.append("--no-cache-dir")

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        end_time = time.time()

        response_time = end_time - start_time
        print_success(f"pip 解析时间: {response_time:.2f} 秒")
        return response_time

    except subprocess.CalledProcessError as e:
        print_error(f"pip 命令失败: {e}")
        return None


def get_current_mirror():
    """获取当前使用的镜像源"""
    config = get_pip_config()
    if not config:
        return None

    for line in config.split("\n"):
        if "global.index-url" in line:
            return line.split("=", 1)[1].strip()

    return None


def main():
    """主函数"""
    print("🔍 pip 镜像源配置测试")
    print("=" * 50)

    # 1. 显示当前配置
    print("\n📋 当前 pip 配置:")
    config = get_pip_config()
    if config:
        print(config)
    else:
        print_warning("无法获取 pip 配置，可能是 pip 版本过低")

    # 2. 获取当前镜像源
    current_mirror = get_current_mirror()
    if current_mirror:
        print_info(f"当前镜像源: {current_mirror}")
    else:
        print_info("使用默认官方源: https://pypi.org/simple/")
        current_mirror = "https://pypi.org/simple/"

    # 3. 测试镜像源连接速度
    print("\n🚀 测试镜像源连接速度:")
    mirror_speed = test_mirror_speed(current_mirror)

    # 4. 测试 pip 安装速度
    print("\n📦 测试 pip 解析速度:")
    pip_speed = test_pip_install_speed()

    # 5. 测试常见镜像源速度对比
    print("\n🏁 镜像源速度对比:")
    mirrors = {
        "阿里云": "https://mirrors.aliyun.com/pypi/simple/",
        "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple/",
        "豆瓣": "https://pypi.doubanio.com/simple/",
        "清华大学": "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "中科大": "https://pypi.mirrors.ustc.edu.cn/simple/",
        "官方源": "https://pypi.org/simple/",
    }

    speeds = {}
    for name, url in mirrors.items():
        print(f"\n测试 {name}:")
        speed = test_mirror_speed(url, timeout=5)
        if speed:
            speeds[name] = speed

    # 6. 显示速度排名
    if speeds:
        print("\n🏆 速度排名 (从快到慢):")
        sorted_speeds = sorted(speeds.items(), key=lambda x: x[1])
        for i, (name, speed) in enumerate(sorted_speeds, 1):
            print(f"  {i}. {name}: {speed:.2f}s")

    # 7. 给出建议
    print("\n💡 建议:")
    if current_mirror == "https://pypi.org/simple/":
        print("  - 当前使用官方源，如果在中国大陆建议配置国内镜像源")
        print("  - 运行: make configure-pip")
    elif mirror_speed and mirror_speed < 2.0:
        print("  - 当前镜像源速度良好")
    elif mirror_speed and mirror_speed > 5.0:
        print("  - 当前镜像源速度较慢，建议更换")
        print("  - 运行: ./scripts/configure_pip_mirror.sh -l 查看可用镜像源")

    print("\n🎉 测试完成!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"测试过程中发生错误: {e}")
        sys.exit(1)
