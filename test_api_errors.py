#!/usr/bin/env python3
"""
API Error Handling Test Script

This script tests the error handling system through actual HTTP requests
to demonstrate how errors are handled in real API scenarios.
"""

import json
import requests
import time
from threading import Thread
from flask import Flask

from app import create_app
from app.utils.exceptions import ValidationError, AuthenticationError, NotFoundError


class APIErrorTester:
    """Test class for API error handling."""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.app = None
        self.server_thread = None
    
    def start_test_server(self):
        """Start a test Flask server."""
        print("🚀 启动测试服务器...")
        
        self.app = create_app('testing')
        self.app.config['DEBUG'] = True
        
        # Add test routes that demonstrate different error scenarios
        self.add_test_routes()
        
        # Start server in a separate thread
        def run_server():
            self.app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        
        self.server_thread = Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        print("✅ 测试服务器已启动 (http://localhost:5000)")
    
    def add_test_routes(self):
        """Add test routes to demonstrate error handling."""
        
        @self.app.route('/api/test/validation-error', methods=['POST'])
        def test_validation_error():
            """Test validation error handling."""
            raise ValidationError(
                "请求数据验证失败",
                field_errors={
                    'username': '用户名必须至少3个字符',
                    'email': '邮箱格式无效',
                    'password': '密码必须至少8个字符'
                }
            )
        
        @self.app.route('/api/test/auth-error')
        def test_auth_error():
            """Test authentication error handling."""
            raise AuthenticationError("认证失败：无效的访问令牌")
        
        @self.app.route('/api/test/not-found/<resource_id>')
        def test_not_found(resource_id):
            """Test not found error handling."""
            raise NotFoundError(
                f"用户 ID {resource_id} 不存在",
                resource_type="User",
                details={'requested_id': resource_id}
            )
        
        @self.app.route('/api/test/server-error')
        def test_server_error():
            """Test generic server error handling."""
            # Simulate an unexpected error
            raise ValueError("这是一个意外的服务器错误")
        
        @self.app.route('/api/test/slow-request')
        def test_slow_request():
            """Test slow request monitoring."""
            time.sleep(1.5)  # Simulate slow processing
            return {'message': '慢请求处理完成', 'processing_time': '1.5秒'}
        
        @self.app.route('/api/test/success')
        def test_success():
            """Test successful request."""
            return {
                'message': '请求成功',
                'data': {'id': 1, 'name': '测试数据'},
                'timestamp': time.time()
            }
        
        @self.app.route('/api/test/rate-limit')
        def test_rate_limit():
            """Test rate limiting (simulated)."""
            from app.utils.exceptions import RateLimitError
            raise RateLimitError(retry_after=60)
        
        @self.app.route('/internal/error-stats')
        def error_stats():
            """Error statistics endpoint."""
            return {
                'message': '错误统计功能正常',
                'note': '实际统计数据由错误监控中间件提供'
            }
    
    def test_validation_error(self):
        """Test validation error response."""
        print("\n1. 测试验证错误处理:")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/test/validation-error",
                json={'invalid': 'data'},
                timeout=5
            )
            
            print(f"   状态码: {response.status_code}")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                print(f"   错误码: {data.get('code')}")
                print(f"   错误消息: {data.get('error')}")
                print(f"   字段错误: {data.get('details', {}).get('field_errors', {})}")
                print(f"   时间戳: {data.get('timestamp')}")
                print(f"   请求路径: {data.get('path')}")
            else:
                print(f"   响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
    
    def test_authentication_error(self):
        """Test authentication error response."""
        print("\n2. 测试认证错误处理:")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/test/auth-error",
                headers={'Authorization': 'Bearer invalid-token'},
                timeout=5
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                print(f"   错误码: {data.get('code')}")
                print(f"   错误消息: {data.get('error')}")
                print(f"   时间戳: {data.get('timestamp')}")
            else:
                print(f"   响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
    
    def test_not_found_error(self):
        """Test not found error response."""
        print("\n3. 测试资源未找到错误处理:")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/test/not-found/99999",
                timeout=5
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                print(f"   错误码: {data.get('code')}")
                print(f"   错误消息: {data.get('error')}")
                print(f"   详情: {data.get('details')}")
            else:
                print(f"   响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
    
    def test_server_error(self):
        """Test server error response."""
        print("\n4. 测试服务器错误处理:")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/test/server-error",
                timeout=5
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                print(f"   错误码: {data.get('code')}")
                print(f"   错误消息: {data.get('message')}")
                print(f"   包含堆栈跟踪: {'traceback' in data}")
            else:
                print(f"   响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
    
    def test_slow_request_monitoring(self):
        """Test slow request monitoring."""
        print("\n5. 测试慢请求监控:")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/api/test/slow-request",
                timeout=10
            )
            end_time = time.time()
            
            print(f"   状态码: {response.status_code}")
            print(f"   实际响应时间: {end_time - start_time:.2f}秒")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                print(f"   响应消息: {data.get('message')}")
                print(f"   处理时间: {data.get('processing_time')}")
            
            print("   注意: 慢请求会被记录在服务器日志中")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
    
    def test_successful_request(self):
        """Test successful request."""
        print("\n6. 测试成功请求:")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/test/success",
                timeout=5
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                print(f"   响应消息: {data.get('message')}")
                print(f"   数据: {data.get('data')}")
            else:
                print(f"   响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
    
    def test_rate_limit_error(self):
        """Test rate limit error response."""
        print("\n7. 测试速率限制错误处理:")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/test/rate-limit",
                timeout=5
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                print(f"   错误码: {data.get('code')}")
                print(f"   错误消息: {data.get('error')}")
                print(f"   重试时间: {data.get('details', {}).get('retry_after')}秒")
            else:
                print(f"   响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
    
    def test_error_statistics(self):
        """Test error statistics endpoint."""
        print("\n8. 测试错误统计端点:")
        
        try:
            response = requests.get(
                f"{self.base_url}/internal/error-stats",
                timeout=5
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"   响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
    
    def run_all_tests(self):
        """Run all API error handling tests."""
        print("🧪 API 错误处理测试")
        print("="*50)
        
        # Start test server
        self.start_test_server()
        
        try:
            # Run all tests
            self.test_successful_request()
            self.test_validation_error()
            self.test_authentication_error()
            self.test_not_found_error()
            self.test_server_error()
            self.test_slow_request_monitoring()
            self.test_rate_limit_error()
            self.test_error_statistics()
            
            print("\n" + "="*50)
            print("✅ 所有API错误处理测试完成")
            print("\n📝 测试总结:")
            print("  • 验证错误 (400) - 字段验证失败")
            print("  • 认证错误 (401) - 无效的访问令牌")
            print("  • 资源未找到 (404) - 请求的资源不存在")
            print("  • 服务器错误 (500) - 意外的服务器错误")
            print("  • 速率限制 (429) - 请求频率过高")
            print("  • 慢请求监控 - 性能监控功能")
            print("  • 错误统计 - 监控数据收集")
            
        except KeyboardInterrupt:
            print("\n⚠️  测试被用户中断")
        except Exception as e:
            print(f"\n❌ 测试过程中出现错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function to run API error tests."""
    print("🚀 Flask API 错误处理 HTTP 测试")
    print("="*60)
    
    # Check if requests library is available
    try:
        import requests
    except ImportError:
        print("❌ requests 库未安装。请运行: pip install requests")
        return
    
    # Create and run tester
    tester = APIErrorTester()
    tester.run_all_tests()


if __name__ == '__main__':
    main()