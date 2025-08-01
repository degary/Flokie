#!/usr/bin/env python3
"""
Flask API Template - API 使用示例

本文件提供了完整的 API 使用示例，展示如何与 Flask API Template 进行交互。
"""

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class APIResponse:
    """API 响应数据类"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    status_code: int = 200


class FlaskAPIClient:
    """Flask API Template 客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:5001",
        access_token: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.refresh_token = None
        self.session = requests.Session()

        # 设置默认超时
        self.session.timeout = 30

        # 设置重试策略
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Flask-API-Template-Client/1.0",
        }

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        use_auth: bool = True,
    ) -> APIResponse:
        """发送 HTTP 请求"""
        url = f"{self.base_url}/api{endpoint}"
        headers = (
            self._get_headers() if use_auth else {"Content-Type": "application/json"}
        )

        try:
            response = self.session.request(
                method=method, url=url, json=data, params=params, headers=headers
            )

            # 尝试解析 JSON 响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"message": response.text}

            return APIResponse(
                success=response.ok,
                data=response_data if response.ok else None,
                error=response_data if not response.ok else None,
                status_code=response.status_code,
            )

        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False, error={"message": str(e)}, status_code=500
            )

    # 认证相关方法
    def register(
        self, username: str, email: str, password: str, first_name: str, last_name: str
    ) -> APIResponse:
        """用户注册"""
        data = {
            "username": username,
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
        }
        return self._make_request("POST", "/auth/register", data, use_auth=False)

    def login(self, username: str, password: str) -> APIResponse:
        """用户登录"""
        data = {"username": username, "password": password}
        response = self._make_request("POST", "/auth/login", data, use_auth=False)

        if response.success and response.data:
            self.access_token = response.data["data"]["access_token"]
            self.refresh_token = response.data["data"]["refresh_token"]

        return response

    def refresh_access_token(self) -> APIResponse:
        """刷新访问令牌"""
        if not self.refresh_token:
            return APIResponse(
                success=False, error={"message": "No refresh token available"}
            )

        # 临时设置刷新令牌
        old_token = self.access_token
        self.access_token = self.refresh_token

        response = self._make_request("POST", "/auth/refresh")

        if response.success and response.data:
            self.access_token = response.data["data"]["access_token"]
        else:
            self.access_token = old_token

        return response

    def logout(self) -> APIResponse:
        """用户登出"""
        response = self._make_request("POST", "/auth/logout")

        if response.success:
            self.access_token = None
            self.refresh_token = None

        return response

    def get_current_user(self) -> APIResponse:
        """获取当前用户信息"""
        return self._make_request("GET", "/auth/me")

    def change_password(self, current_password: str, new_password: str) -> APIResponse:
        """修改密码"""
        data = {
            "current_password": current_password,
            "new_password": new_password,
            "confirm_password": new_password,
        }
        return self._make_request("POST", "/auth/password/change", data)

    def request_password_reset(self, email: str) -> APIResponse:
        """请求密码重置"""
        data = {"email": email}
        return self._make_request(
            "POST", "/auth/password/reset-request", data, use_auth=False
        )

    def reset_password(self, token: str, new_password: str) -> APIResponse:
        """重置密码"""
        data = {
            "token": token,
            "new_password": new_password,
            "confirm_password": new_password,
        }
        return self._make_request("POST", "/auth/password/reset", data, use_auth=False)

    # 用户管理方法
    def get_users(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        include_inactive: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> APIResponse:
        """获取用户列表"""
        params = {
            "page": page,
            "per_page": per_page,
            "include_inactive": include_inactive,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        if search:
            params["search"] = search

        return self._make_request("GET", "/users", params=params)

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        is_admin: bool = False,
    ) -> APIResponse:
        """创建用户"""
        data = {
            "username": username,
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "is_admin": is_admin,
        }
        return self._make_request("POST", "/users", data)

    def get_user(self, user_id: int) -> APIResponse:
        """获取用户详情"""
        return self._make_request("GET", f"/users/{user_id}")

    def update_user(self, user_id: int, **kwargs) -> APIResponse:
        """更新用户信息"""
        return self._make_request("PUT", f"/users/{user_id}", kwargs)

    def delete_user(self, user_id: int, hard_delete: bool = False) -> APIResponse:
        """删除用户"""
        params = {"hard_delete": hard_delete} if hard_delete else None
        return self._make_request("DELETE", f"/users/{user_id}", params=params)

    def activate_user(self, user_id: int) -> APIResponse:
        """激活用户"""
        return self._make_request("POST", f"/users/{user_id}/activate")

    def deactivate_user(self, user_id: int) -> APIResponse:
        """停用用户"""
        return self._make_request("POST", f"/users/{user_id}/deactivate")

    def unlock_user(self, user_id: int) -> APIResponse:
        """解锁用户"""
        return self._make_request("POST", f"/users/{user_id}/unlock")

    def set_admin_status(self, user_id: int, is_admin: bool) -> APIResponse:
        """设置管理员权限"""
        data = {"is_admin": is_admin}
        return self._make_request("POST", f"/users/{user_id}/admin", data)

    def search_users(
        self, query: str, limit: int = 20, include_inactive: bool = False
    ) -> APIResponse:
        """搜索用户"""
        params = {"q": query, "limit": limit, "include_inactive": include_inactive}
        return self._make_request("GET", "/users/search", params=params)

    def get_user_statistics(self) -> APIResponse:
        """获取用户统计信息"""
        return self._make_request("GET", "/users/statistics")

    # 健康检查方法
    def health_check(self) -> APIResponse:
        """基础健康检查"""
        return self._make_request("GET", "/health", use_auth=False)

    def detailed_health_check(self) -> APIResponse:
        """详细健康检查"""
        return self._make_request("GET", "/health/detailed", use_auth=False)

    def database_health_check(self) -> APIResponse:
        """数据库健康检查"""
        return self._make_request("GET", "/health/database", use_auth=False)


def print_response(response: APIResponse, title: str = ""):
    """打印 API 响应"""
    print(f"\n{'='*50}")
    if title:
        print(f"📋 {title}")
        print(f"{'='*50}")

    print(f"✅ 成功: {response.success}")
    print(f"📊 状态码: {response.status_code}")

    if response.success and response.data:
        print(f"📄 响应数据:")
        print(json.dumps(response.data, indent=2, ensure_ascii=False))
    elif response.error:
        print(f"❌ 错误信息:")
        print(json.dumps(response.error, indent=2, ensure_ascii=False))


def demo_authentication_flow():
    """演示认证流程"""
    print("\n🔐 认证流程演示")
    print("=" * 50)

    client = FlaskAPIClient()

    # 1. 健康检查
    print("\n1️⃣ 健康检查")
    health = client.health_check()
    print_response(health, "健康检查")

    # 2. 用户注册
    print("\n2️⃣ 用户注册")
    register_response = client.register(
        username="demo_user",
        email="demo@example.com",
        password="DemoPassword123!",
        first_name="Demo",
        last_name="User",
    )
    print_response(register_response, "用户注册")

    # 3. 用户登录
    print("\n3️⃣ 用户登录")
    login_response = client.login("demo_user", "DemoPassword123!")
    print_response(login_response, "用户登录")

    if not login_response.success:
        print("❌ 登录失败，可能用户已存在，尝试使用默认管理员账户")
        login_response = client.login("admin", "admin123")
        print_response(login_response, "管理员登录")

    if login_response.success:
        # 4. 获取当前用户信息
        print("\n4️⃣ 获取当前用户信息")
        user_info = client.get_current_user()
        print_response(user_info, "当前用户信息")

        # 5. 刷新令牌
        print("\n5️⃣ 刷新访问令牌")
        refresh_response = client.refresh_access_token()
        print_response(refresh_response, "刷新令牌")

        # 6. 修改密码（演示，不实际执行）
        print("\n6️⃣ 修改密码演示（跳过实际执行）")
        print("💡 可以使用 client.change_password(current_password, new_password)")

        # 7. 登出
        print("\n7️⃣ 用户登出")
        logout_response = client.logout()
        print_response(logout_response, "用户登出")


def demo_user_management():
    """演示用户管理功能"""
    print("\n👥 用户管理演示")
    print("=" * 50)

    client = FlaskAPIClient()

    # 登录管理员账户
    print("\n🔑 管理员登录")
    login_response = client.login("admin", "admin123")

    if not login_response.success:
        print("❌ 管理员登录失败，跳过用户管理演示")
        return

    print_response(login_response, "管理员登录")

    # 1. 获取用户列表
    print("\n1️⃣ 获取用户列表")
    users_response = client.get_users(page=1, per_page=5)
    print_response(users_response, "用户列表")

    # 2. 创建新用户
    print("\n2️⃣ 创建新用户")
    create_response = client.create_user(
        username=f"test_user_{int(time.time())}",
        email=f"test_{int(time.time())}@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="User",
    )
    print_response(create_response, "创建用户")

    if create_response.success:
        user_id = create_response.data["data"]["user"]["id"]

        # 3. 获取用户详情
        print("\n3️⃣ 获取用户详情")
        user_detail = client.get_user(user_id)
        print_response(user_detail, "用户详情")

        # 4. 更新用户信息
        print("\n4️⃣ 更新用户信息")
        update_response = client.update_user(
            user_id, first_name="Updated", last_name="Name"
        )
        print_response(update_response, "更新用户")

        # 5. 停用用户
        print("\n5️⃣ 停用用户")
        deactivate_response = client.deactivate_user(user_id)
        print_response(deactivate_response, "停用用户")

        # 6. 激活用户
        print("\n6️⃣ 激活用户")
        activate_response = client.activate_user(user_id)
        print_response(activate_response, "激活用户")

        # 7. 删除用户（软删除）
        print("\n7️⃣ 删除用户")
        delete_response = client.delete_user(user_id, hard_delete=False)
        print_response(delete_response, "删除用户")

    # 8. 搜索用户
    print("\n8️⃣ 搜索用户")
    search_response = client.search_users("admin", limit=5)
    print_response(search_response, "搜索用户")

    # 9. 获取用户统计
    print("\n9️⃣ 用户统计信息")
    stats_response = client.get_user_statistics()
    print_response(stats_response, "用户统计")


def demo_health_checks():
    """演示健康检查功能"""
    print("\n🏥 健康检查演示")
    print("=" * 50)

    client = FlaskAPIClient()

    # 1. 基础健康检查
    print("\n1️⃣ 基础健康检查")
    basic_health = client.health_check()
    print_response(basic_health, "基础健康检查")

    # 2. 详细健康检查
    print("\n2️⃣ 详细健康检查")
    detailed_health = client.detailed_health_check()
    print_response(detailed_health, "详细健康检查")

    # 3. 数据库健康检查
    print("\n3️⃣ 数据库健康检查")
    db_health = client.database_health_check()
    print_response(db_health, "数据库健康检查")


def demo_error_handling():
    """演示错误处理"""
    print("\n⚠️ 错误处理演示")
    print("=" * 50)

    client = FlaskAPIClient()

    # 1. 未认证访问受保护资源
    print("\n1️⃣ 未认证访问")
    unauthorized = client.get_current_user()
    print_response(unauthorized, "未认证访问")

    # 2. 无效登录凭据
    print("\n2️⃣ 无效登录凭据")
    invalid_login = client.login("invalid_user", "wrong_password")
    print_response(invalid_login, "无效登录")

    # 3. 访问不存在的用户
    print("\n3️⃣ 访问不存在的用户")
    client.login("admin", "admin123")  # 先登录
    not_found = client.get_user(99999)
    print_response(not_found, "用户不存在")

    # 4. 验证错误
    print("\n4️⃣ 数据验证错误")
    validation_error = client.register(
        username="",  # 空用户名
        email="invalid-email",  # 无效邮箱
        password="123",  # 密码太短
        first_name="",
        last_name="",
    )
    print_response(validation_error, "验证错误")


def performance_test():
    """简单的性能测试"""
    print("\n⚡ 性能测试演示")
    print("=" * 50)

    client = FlaskAPIClient()

    # 登录
    login_response = client.login("admin", "admin123")
    if not login_response.success:
        print("❌ 登录失败，跳过性能测试")
        return

    # 测试多次健康检查
    print("\n🔄 执行 10 次健康检查")
    start_time = time.time()

    for i in range(10):
        response = client.health_check()
        if not response.success:
            print(f"❌ 第 {i+1} 次检查失败")
        else:
            print(f"✅ 第 {i+1} 次检查成功")

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / 10

    print(f"\n📊 性能统计:")
    print(f"   总时间: {total_time:.2f} 秒")
    print(f"   平均响应时间: {avg_time:.3f} 秒")
    print(f"   每秒请求数: {10/total_time:.2f} RPS")


def main():
    """主函数 - 运行所有演示"""
    print("🚀 Flask API Template - API 使用示例")
    print("=" * 60)

    try:
        # 运行各种演示
        demo_health_checks()
        demo_authentication_flow()
        demo_user_management()
        demo_error_handling()
        performance_test()

        print("\n🎉 所有演示完成！")
        print("\n💡 提示:")
        print("   - 查看 Swagger 文档: http://localhost:5001/api/doc")
        print("   - 查看详细文档: docs/api-guide.md")
        print("   - 运行测试: make test")

    except KeyboardInterrupt:
        print("\n\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n\n❌ 演示过程中发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
