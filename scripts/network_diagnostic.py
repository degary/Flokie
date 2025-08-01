#!/usr/bin/env python3
"""
网络诊断脚本

这个脚本帮助诊断网络连接问题，特别是与 Python 包管理相关的网络问题。
"""

import json
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def test_dns_resolution(hostname):
    """测试 DNS 解析"""
    try:
        start_time = time.time()
        ip = socket.gethostbyname(hostname)
        end_time = time.time()

        resolution_time = (end_time - start_time) * 1000
        print_success(f"{hostname} -> {ip} ({resolution_time:.2f}ms)")
        return True, ip, resolution_time
    except socket.gaierror as e:
        print_error(f"{hostname} DNS 解析失败: {e}")
        return False, None, None


def test_tcp_connection(hostname, port, timeout=5):
    """测试 TCP 连接"""
    try:
        start_time = time.time()
        sock = socket.create_connection((hostname, port), timeout)
        end_time = time.time()
        sock.close()

        connection_time = (end_time - start_time) * 1000
        print_success(f"{hostname}:{port} 连接成功 ({connection_time:.2f}ms)")
        return True, connection_time
    except (socket.timeout, socket.error) as e:
        print_error(f"{hostname}:{port} 连接失败: {e}")
        return False, None


def test_http_request(url, timeout=10):
    """测试 HTTP 请求"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        end_time = time.time()

        request_time = (end_time - start_time) * 1000

        if response.status_code == 200:
            print_success(
                f"{url} HTTP 请求成功 ({request_time:.2f}ms, {response.status_code})"
            )
            return True, request_time, response.status_code
        else:
            print_warning(
                f"{url} HTTP 请求返回 {response.status_code} ({request_time:.2f}ms)"
            )
            return False, request_time, response.status_code

    except requests.exceptions.Timeout:
        print_error(f"{url} HTTP 请求超时 (>{timeout}s)")
        return False, None, None
    except requests.exceptions.RequestException as e:
        print_error(f"{url} HTTP 请求失败: {e}")
        return False, None, None


def test_pip_repositories():
    """测试 pip 仓库连接"""
    repositories = {
        "PyPI 官方": "https://pypi.org/simple/",
        "阿里云": "https://mirrors.aliyun.com/pypi/simple/",
        "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple/",
        "豆瓣": "https://pypi.doubanio.com/simple/",
        "清华大学": "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "中科大": "https://pypi.mirrors.ustc.edu.cn/simple/",
    }

    print("\n🐍 测试 Python 包仓库连接:")
    print("-" * 50)

    results = {}

    def test_single_repo(name, url):
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

        print(f"\n测试 {name} ({url}):")

        # DNS 解析
        dns_ok, ip, dns_time = test_dns_resolution(hostname)
        if not dns_ok:
            return name, {"status": "dns_failed"}

        # TCP 连接
        tcp_ok, tcp_time = test_tcp_connection(hostname, port)
        if not tcp_ok:
            return name, {"status": "tcp_failed", "ip": ip, "dns_time": dns_time}

        # HTTP 请求
        http_ok, http_time, status_code = test_http_request(url)

        return name, {
            "status": "success" if http_ok else "http_failed",
            "ip": ip,
            "dns_time": dns_time,
            "tcp_time": tcp_time,
            "http_time": http_time,
            "status_code": status_code,
        }

    # 并发测试所有仓库
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(test_single_repo, name, url)
            for name, url in repositories.items()
        ]

        for future in as_completed(futures):
            name, result = future.result()
            results[name] = result

    return results


def test_docker_registries():
    """测试 Docker 镜像仓库连接"""
    registries = {
        "Docker Hub": "https://registry-1.docker.io",
        "阿里云": "https://registry.cn-hangzhou.aliyuncs.com",
        "腾讯云": "https://ccr.ccs.tencentyun.com",
        "网易云": "https://hub-mirror.c.163.com",
    }

    print("\n🐳 测试 Docker 镜像仓库连接:")
    print("-" * 50)

    results = {}

    for name, url in registries.items():
        print(f"\n测试 {name} ({url}):")
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

        # DNS 解析
        dns_ok, ip, dns_time = test_dns_resolution(hostname)
        if not dns_ok:
            results[name] = {"status": "dns_failed"}
            continue

        # TCP 连接
        tcp_ok, tcp_time = test_tcp_connection(hostname, port)
        if not tcp_ok:
            results[name] = {"status": "tcp_failed", "ip": ip, "dns_time": dns_time}
            continue

        results[name] = {
            "status": "success",
            "ip": ip,
            "dns_time": dns_time,
            "tcp_time": tcp_time,
        }

    return results


def test_system_network():
    """测试系统网络配置"""
    print("\n🌐 测试系统网络配置:")
    print("-" * 50)

    # 测试基本连通性
    test_hosts = [
        ("Google DNS", "8.8.8.8"),
        ("Cloudflare DNS", "1.1.1.1"),
        ("阿里云 DNS", "223.5.5.5"),
        ("腾讯云 DNS", "119.29.29.29"),
    ]

    print("\n📡 测试 DNS 服务器连通性:")
    for name, host in test_hosts:
        print(f"测试 {name} ({host}):")
        test_tcp_connection(host, 53, timeout=3)

    # 测试 HTTP/HTTPS 连通性
    test_urls = [
        ("Google", "https://www.google.com"),
        ("百度", "https://www.baidu.com"),
        ("GitHub", "https://github.com"),
        ("阿里云", "https://www.aliyun.com"),
    ]

    print("\n🌍 测试网站连通性:")
    for name, url in test_urls:
        print(f"测试 {name} ({url}):")
        test_http_request(url, timeout=5)


def get_network_info():
    """获取网络信息"""
    print("\n📊 系统网络信息:")
    print("-" * 50)

    try:
        # 获取本机 IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"主机名: {hostname}")
        print(f"本机 IP: {local_ip}")

        # 获取网关信息（仅 Linux/Mac）
        try:
            if sys.platform != "win32":
                result = subprocess.run(
                    ["route", "-n", "get", "default"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "gateway:" in line:
                            gateway = line.split(":")[1].strip()
                            print(f"默认网关: {gateway}")
                            break
        except:
            pass

        # 获取 DNS 配置
        try:
            if sys.platform == "darwin":  # macOS
                result = subprocess.run(
                    ["scutil", "--dns"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    print("DNS 配置:")
                    lines = result.stdout.split("\n")
                    for i, line in enumerate(lines):
                        if "nameserver[0]" in line:
                            print(f"  主 DNS: {line.split(':')[1].strip()}")
                        elif "nameserver[1]" in line:
                            print(f"  备 DNS: {line.split(':')[1].strip()}")
            elif sys.platform.startswith("linux"):  # Linux
                try:
                    with open("/etc/resolv.conf", "r") as f:
                        print("DNS 配置:")
                        for line in f:
                            if line.startswith("nameserver"):
                                dns_server = line.split()[1]
                                print(f"  DNS 服务器: {dns_server}")
                except:
                    pass
        except:
            pass

    except Exception as e:
        print_error(f"获取网络信息失败: {e}")


def generate_report(pip_results, docker_results):
    """生成诊断报告"""
    print("\n📋 诊断报告:")
    print("=" * 60)

    # pip 仓库报告
    print("\n🐍 Python 包仓库状态:")
    successful_repos = []
    failed_repos = []

    for name, result in pip_results.items():
        if result.get("status") == "success":
            successful_repos.append((name, result.get("http_time", 0)))
        else:
            failed_repos.append((name, result.get("status", "unknown")))

    if successful_repos:
        # 按速度排序
        successful_repos.sort(key=lambda x: x[1])
        print("  ✅ 可用仓库 (按速度排序):")
        for name, time_ms in successful_repos:
            print(f"     {name}: {time_ms:.0f}ms")

    if failed_repos:
        print("  ❌ 不可用仓库:")
        for name, status in failed_repos:
            print(f"     {name}: {status}")

    # Docker 仓库报告
    print("\n🐳 Docker 镜像仓库状态:")
    docker_success = []
    docker_failed = []

    for name, result in docker_results.items():
        if result.get("status") == "success":
            docker_success.append(name)
        else:
            docker_failed.append((name, result.get("status", "unknown")))

    if docker_success:
        print("  ✅ 可用仓库:")
        for name in docker_success:
            print(f"     {name}")

    if docker_failed:
        print("  ❌ 不可用仓库:")
        for name, status in docker_failed:
            print(f"     {name}: {status}")

    # 建议
    print("\n💡 建议:")

    if successful_repos:
        fastest_repo = successful_repos[0][0]
        print(f"  - 推荐使用最快的 pip 仓库: {fastest_repo}")

        # 提供配置命令
        mirror_map = {
            "阿里云": "aliyun",
            "腾讯云": "tencent",
            "豆瓣": "douban",
            "清华大学": "tsinghua",
            "中科大": "ustc",
        }

        if fastest_repo in mirror_map:
            mirror_key = mirror_map[fastest_repo]
            print(f"    配置命令: ./scripts/configure_pip_mirror.sh -m {mirror_key}")

    if not successful_repos:
        print("  - 所有 pip 仓库都不可用，请检查网络连接")
        print("  - 尝试使用代理或 VPN")

    if len(successful_repos) < 3:
        print("  - 网络连接不稳定，建议:")
        print("    1. 检查防火墙设置")
        print("    2. 尝试更换 DNS 服务器")
        print("    3. 联系网络管理员")


def main():
    """主函数"""
    print("🔍 Flask API Template - 网络诊断工具")
    print("=" * 60)

    try:
        # 获取系统网络信息
        get_network_info()

        # 测试系统网络
        test_system_network()

        # 测试 pip 仓库
        pip_results = test_pip_repositories()

        # 测试 Docker 仓库
        docker_results = test_docker_registries()

        # 生成报告
        generate_report(pip_results, docker_results)

        print("\n🎉 网络诊断完成!")
        print("\n💡 如果遇到问题，请:")
        print("   1. 检查防火墙和代理设置")
        print("   2. 尝试更换 DNS 服务器")
        print("   3. 使用 VPN 或代理")
        print("   4. 联系网络管理员")

    except KeyboardInterrupt:
        print("\n\n⏹️ 诊断被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"诊断过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
