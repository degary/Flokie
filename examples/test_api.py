#!/usr/bin/env python3
"""
Flask API Template - API 测试脚本

这个脚本提供了完整的 API 测试功能，可以用于：
1. 验证 API 功能是否正常
2. 性能测试
3. 压力测试
4. 集成测试

使用方法:
    python examples/test_api.py --help
"""

import argparse
import asyncio
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class TestResult:
    """测试结果数据类"""

    test_name: str
    success: bool
    response_time: float
    status_code: int
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None


@dataclass
class TestSuite:
    """测试套件数据类"""

    name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_time: float
    avg_response_time: float
    results: List[TestResult]


class APITester:
    """API 测试器"""

    def __init__(
        self,
        base_url: str = "http://localhost:5001",
        timeout: int = 30,
        retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.access_token = None

        # 配置重试策略
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        use_auth: bool = True,
    ) -> TestResult:
        """发送 HTTP 请求并返回测试结果"""
        url = f"{self.base_url}/api{endpoint}"
        headers = {"Content-Type": "application/json"}

        if use_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        start_time = time.time()

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )

            response_time = time.time() - start_time

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"message": response.text}

            return TestResult(
                test_name=f"{method} {endpoint}",
                success=response.ok,
                response_time=response_time,
                status_code=response.status_code,
                response_data=response_data if response.ok else None,
                error_message=str(response_data) if not response.ok else None,
            )

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            return TestResult(
                test_name=f"{method} {endpoint}",
                success=False,
                response_time=response_time,
                status_code=0,
                error_message=str(e),
            )

    def login_admin(self) -> TestResult:
        """管理员登录"""
        result = self._make_request(
            "POST",
            "/auth/login",
            data={"username": "admin", "password": "admin123"},
            use_auth=False,
        )

        if result.success and result.response_data:
            self.access_token = result.response_data["data"]["access_token"]

        return result

    def test_health_endpoints(self) -> List[TestResult]:
        """测试健康检查端点"""
        results = []

        endpoints = [
            "/health",
            "/health/detailed",
            "/health/database",
            "/health/system",
            "/health/readiness",
            "/health/liveness",
        ]

        for endpoint in endpoints:
            result = self._make_request("GET", endpoint, use_auth=False)
            results.append(result)

        return results

    def test_auth_endpoints(self) -> List[TestResult]:
        """测试认证端点"""
        results = []

        # 测试注册（可能失败，因为用户可能已存在）
        timestamp = int(time.time())
        register_result = self._make_request(
            "POST",
            "/auth/register",
            data={
                "username": f"test_user_{timestamp}",
                "email": f"test_{timestamp}@example.com",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User",
            },
            use_auth=False,
        )
        results.append(register_result)

        # 测试登录
        login_result = self.login_admin()
        results.append(login_result)

        if login_result.success:
            # 测试获取当前用户信息
            me_result = self._make_request("GET", "/auth/me")
            results.append(me_result)

            # 测试刷新令牌
            refresh_result = self._make_request("POST", "/auth/refresh")
            results.append(refresh_result)

            # 测试登出
            logout_result = self._make_request("POST", "/auth/logout")
            results.append(logout_result)

        return results

    def test_user_endpoints(self) -> List[TestResult]:
        """测试用户管理端点"""
        results = []

        # 先登录
        login_result = self.login_admin()
        if not login_result.success:
            results.append(
                TestResult(
                    test_name="User endpoints (login required)",
                    success=False,
                    response_time=0,
                    status_code=401,
                    error_message="Admin login failed",
                )
            )
            return results

        # 测试获取用户列表
        users_result = self._make_request("GET", "/users")
        results.append(users_result)

        # 测试创建用户
        timestamp = int(time.time())
        create_result = self._make_request(
            "POST",
            "/users",
            data={
                "username": f"api_test_user_{timestamp}",
                "email": f"api_test_{timestamp}@example.com",
                "password": "TestPassword123!",
                "first_name": "API",
                "last_name": "Test",
            },
        )
        results.append(create_result)

        # 如果创建成功，测试其他用户操作
        if create_result.success and create_result.response_data:
            user_id = create_result.response_data["data"]["user"]["id"]

            # 测试获取用户详情
            get_result = self._make_request("GET", f"/users/{user_id}")
            results.append(get_result)

            # 测试更新用户
            update_result = self._make_request(
                "PUT", f"/users/{user_id}", data={"first_name": "Updated"}
            )
            results.append(update_result)

            # 测试停用用户
            deactivate_result = self._make_request(
                "POST", f"/users/{user_id}/deactivate"
            )
            results.append(deactivate_result)

            # 测试激活用户
            activate_result = self._make_request("POST", f"/users/{user_id}/activate")
            results.append(activate_result)

            # 测试删除用户
            delete_result = self._make_request("DELETE", f"/users/{user_id}")
            results.append(delete_result)

        # 测试搜索用户
        search_result = self._make_request(
            "GET", "/users/search", params={"q": "admin"}
        )
        results.append(search_result)

        # 测试用户统计
        stats_result = self._make_request("GET", "/users/statistics")
        results.append(stats_result)

        return results

    def test_error_handling(self) -> List[TestResult]:
        """测试错误处理"""
        results = []

        # 测试未认证访问
        unauth_result = self._make_request("GET", "/auth/me", use_auth=False)
        results.append(
            TestResult(
                test_name="Unauthorized access",
                success=unauth_result.status_code == 401,
                response_time=unauth_result.response_time,
                status_code=unauth_result.status_code,
                error_message=unauth_result.error_message
                if unauth_result.status_code != 401
                else None,
            )
        )

        # 测试无效登录
        invalid_login = self._make_request(
            "POST",
            "/auth/login",
            data={"username": "invalid", "password": "invalid"},
            use_auth=False,
        )
        results.append(
            TestResult(
                test_name="Invalid login",
                success=invalid_login.status_code == 401,
                response_time=invalid_login.response_time,
                status_code=invalid_login.status_code,
                error_message=invalid_login.error_message
                if invalid_login.status_code != 401
                else None,
            )
        )

        # 测试访问不存在的资源
        not_found = self._make_request("GET", "/users/99999")
        results.append(
            TestResult(
                test_name="Resource not found",
                success=not_found.status_code == 404,
                response_time=not_found.response_time,
                status_code=not_found.status_code,
                error_message=not_found.error_message
                if not_found.status_code != 404
                else None,
            )
        )

        # 测试数据验证错误
        validation_error = self._make_request(
            "POST",
            "/auth/register",
            data={
                "username": "",  # 空用户名
                "email": "invalid-email",  # 无效邮箱
                "password": "123",  # 密码太短
                "first_name": "",
                "last_name": "",
            },
            use_auth=False,
        )
        results.append(
            TestResult(
                test_name="Validation error",
                success=validation_error.status_code == 400,
                response_time=validation_error.response_time,
                status_code=validation_error.status_code,
                error_message=validation_error.error_message
                if validation_error.status_code != 400
                else None,
            )
        )

        return results

    def run_performance_test(
        self,
        endpoint: str = "/health",
        concurrent_requests: int = 10,
        total_requests: int = 100,
    ) -> Dict[str, Any]:
        """运行性能测试"""
        print(f"🚀 运行性能测试: {endpoint}")
        print(f"   并发数: {concurrent_requests}")
        print(f"   总请求数: {total_requests}")

        results = []
        start_time = time.time()

        def make_single_request():
            return self._make_request("GET", endpoint, use_auth=False)

        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(make_single_request) for _ in range(total_requests)
            ]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        end_time = time.time()
        total_time = end_time - start_time

        # 计算统计信息
        successful_requests = [r for r in results if r.success]
        failed_requests = [r for r in results if not r.success]
        response_times = [r.response_time for r in successful_requests]

        stats = {
            "endpoint": endpoint,
            "total_requests": total_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": len(successful_requests) / total_requests * 100,
            "total_time": total_time,
            "requests_per_second": total_requests / total_time,
            "avg_response_time": statistics.mean(response_times)
            if response_times
            else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "median_response_time": statistics.median(response_times)
            if response_times
            else 0,
            "p95_response_time": statistics.quantiles(response_times, n=20)[18]
            if len(response_times) > 20
            else 0,
            "p99_response_time": statistics.quantiles(response_times, n=100)[98]
            if len(response_times) > 100
            else 0,
        }

        return stats

    def run_all_tests(self) -> TestSuite:
        """运行所有测试"""
        print("🧪 开始运行 API 测试套件")
        print("=" * 50)

        all_results = []
        start_time = time.time()

        # 运行各种测试
        test_groups = [
            ("健康检查", self.test_health_endpoints),
            ("认证功能", self.test_auth_endpoints),
            ("用户管理", self.test_user_endpoints),
            ("错误处理", self.test_error_handling),
        ]

        for group_name, test_func in test_groups:
            print(f"\n📋 测试组: {group_name}")
            print("-" * 30)

            group_results = test_func()
            all_results.extend(group_results)

            # 显示组测试结果
            passed = sum(1 for r in group_results if r.success)
            total = len(group_results)
            print(f"   ✅ 通过: {passed}/{total}")

            if passed < total:
                failed_tests = [r for r in group_results if not r.success]
                for test in failed_tests:
                    print(f"   ❌ 失败: {test.test_name} - {test.error_message}")

        end_time = time.time()
        total_time = end_time - start_time

        # 计算总体统计
        passed_tests = sum(1 for r in all_results if r.success)
        failed_tests = len(all_results) - passed_tests
        avg_response_time = statistics.mean([r.response_time for r in all_results])

        return TestSuite(
            name="API 完整测试套件",
            total_tests=len(all_results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_time=total_time,
            avg_response_time=avg_response_time,
            results=all_results,
        )


def print_test_summary(suite: TestSuite):
    """打印测试摘要"""
    print("\n" + "=" * 60)
    print("📊 测试摘要")
    print("=" * 60)

    print(f"测试套件: {suite.name}")
    print(f"总测试数: {suite.total_tests}")
    print(f"通过测试: {suite.passed_tests} ✅")
    print(f"失败测试: {suite.failed_tests} ❌")
    print(f"成功率: {suite.passed_tests/suite.total_tests*100:.1f}%")
    print(f"总耗时: {suite.total_time:.2f} 秒")
    print(f"平均响应时间: {suite.avg_response_time:.3f} 秒")

    if suite.failed_tests > 0:
        print(f"\n❌ 失败的测试:")
        failed_tests = [r for r in suite.results if not r.success]
        for test in failed_tests:
            print(f"   • {test.test_name}")
            print(f"     状态码: {test.status_code}")
            print(f"     错误: {test.error_message}")


def print_performance_stats(stats: Dict[str, Any]):
    """打印性能测试统计"""
    print("\n" + "=" * 60)
    print("⚡ 性能测试结果")
    print("=" * 60)

    print(f"测试端点: {stats['endpoint']}")
    print(f"总请求数: {stats['total_requests']}")
    print(f"成功请求: {stats['successful_requests']}")
    print(f"失败请求: {stats['failed_requests']}")
    print(f"成功率: {stats['success_rate']:.1f}%")
    print(f"总耗时: {stats['total_time']:.2f} 秒")
    print(f"QPS: {stats['requests_per_second']:.2f}")

    print(f"\n📈 响应时间统计:")
    print(f"   平均: {stats['avg_response_time']:.3f} 秒")
    print(f"   最小: {stats['min_response_time']:.3f} 秒")
    print(f"   最大: {stats['max_response_time']:.3f} 秒")
    print(f"   中位数: {stats['median_response_time']:.3f} 秒")

    if stats["p95_response_time"] > 0:
        print(f"   P95: {stats['p95_response_time']:.3f} 秒")
    if stats["p99_response_time"] > 0:
        print(f"   P99: {stats['p99_response_time']:.3f} 秒")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Flask API Template 测试脚本")
    parser.add_argument(
        "--url",
        default="http://localhost:5001",
        help="API 基础 URL (默认: http://localhost:5001)",
    )
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间 (默认: 30 秒)")
    parser.add_argument("--performance", action="store_true", help="运行性能测试")
    parser.add_argument("--endpoint", default="/health", help="性能测试端点 (默认: /health)")
    parser.add_argument("--concurrent", type=int, default=10, help="并发请求数 (默认: 10)")
    parser.add_argument("--requests", type=int, default=100, help="总请求数 (默认: 100)")
    parser.add_argument("--output", help="输出结果到 JSON 文件")

    args = parser.parse_args()

    # 创建测试器
    tester = APITester(base_url=args.url, timeout=args.timeout)

    try:
        if args.performance:
            # 运行性能测试
            stats = tester.run_performance_test(
                endpoint=args.endpoint,
                concurrent_requests=args.concurrent,
                total_requests=args.requests,
            )
            print_performance_stats(stats)

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False)
                print(f"\n💾 结果已保存到: {args.output}")

        else:
            # 运行功能测试
            suite = tester.run_all_tests()
            print_test_summary(suite)

            if args.output:
                suite_dict = asdict(suite)
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(suite_dict, f, indent=2, ensure_ascii=False)
                print(f"\n💾 结果已保存到: {args.output}")

        print(f"\n🎉 测试完成！")

    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
