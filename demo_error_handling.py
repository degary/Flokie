#!/usr/bin/env python3
"""
Error Handling Demo Script

This script demonstrates the error handling and exception management system
by creating various error scenarios and showing how they are handled.
"""

import os
import sys
import json
from flask import Flask

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.utils.exceptions import (
    ValidationError, AuthenticationError, NotFoundError, 
    ConflictError, BusinessLogicError, UserNotFoundError,
    InvalidCredentialsError, DuplicateResourceError
)
from app.utils.error_helpers import (
    validate_required_fields, validate_field_length, 
    check_resource_exists, validate_business_rule
)


def demo_custom_exceptions():
    """Demonstrate custom exception classes."""
    print("=== 演示自定义异常类 ===\n")
    
    # 1. ValidationError with field errors
    print("1. ValidationError 示例:")
    try:
        field_errors = {
            'username': '用户名必须至少3个字符',
            'email': '邮箱格式无效'
        }
        raise ValidationError("表单验证失败", field_errors=field_errors)
    except ValidationError as e:
        print(f"   错误码: {e.error_code}")
        print(f"   状态码: {e.status_code}")
        print(f"   消息: {e.message}")
        print(f"   详情: {e.details}")
        print(f"   JSON格式: {json.dumps(e.to_dict(), indent=2, ensure_ascii=False)}")
    print()
    
    # 2. AuthenticationError
    print("2. AuthenticationError 示例:")
    try:
        raise InvalidCredentialsError()
    except InvalidCredentialsError as e:
        print(f"   错误码: {e.error_code}")
        print(f"   状态码: {e.status_code}")
        print(f"   消息: {e.message}")
    print()
    
    # 3. NotFoundError with resource type
    print("3. NotFoundError 示例:")
    try:
        raise UserNotFoundError(user_id="12345")
    except UserNotFoundError as e:
        print(f"   错误码: {e.error_code}")
        print(f"   状态码: {e.status_code}")
        print(f"   消息: {e.message}")
        print(f"   详情: {e.details}")
    print()
    
    # 4. ConflictError
    print("4. ConflictError 示例:")
    try:
        raise DuplicateResourceError("User", "email")
    except DuplicateResourceError as e:
        print(f"   错误码: {e.error_code}")
        print(f"   状态码: {e.status_code}")
        print(f"   消息: {e.message}")
        print(f"   详情: {e.details}")
    print()
    
    # 5. BusinessLogicError
    print("5. BusinessLogicError 示例:")
    try:
        raise BusinessLogicError(
            "无法删除有活跃订单的用户", 
            details={'active_orders': 3, 'user_id': '123'}
        )
    except BusinessLogicError as e:
        print(f"   错误码: {e.error_code}")
        print(f"   状态码: {e.status_code}")
        print(f"   消息: {e.message}")
        print(f"   详情: {e.details}")
    print()


def demo_error_helpers():
    """Demonstrate error helper functions."""
    print("=== 演示错误处理辅助函数 ===\n")
    
    # 1. Required field validation
    print("1. 必填字段验证:")
    try:
        data = {'username': 'testuser'}  # Missing email and password
        required_fields = ['username', 'email', 'password']
        validate_required_fields(data, required_fields)
    except ValidationError as e:
        print(f"   ✓ 捕获到验证错误: {e.message}")
        print(f"   ✓ 字段错误: {e.details['field_errors']}")
    print()
    
    # 2. Field length validation
    print("2. 字段长度验证:")
    try:
        data = {'username': 'ab', 'password': '123'}  # Too short
        constraints = {
            'username': {'min': 3, 'max': 50},
            'password': {'min': 8, 'max': 128}
        }
        validate_field_length(data, constraints)
    except ValidationError as e:
        print(f"   ✓ 捕获到验证错误: {e.message}")
        print(f"   ✓ 字段错误: {e.details['field_errors']}")
    print()
    
    # 3. Resource existence check
    print("3. 资源存在性检查:")
    try:
        check_resource_exists(None, "User", "12345")
    except NotFoundError as e:
        print(f"   ✓ 捕获到未找到错误: {e.message}")
        print(f"   ✓ 详情: {e.details}")
    print()
    
    # 4. Business rule validation
    print("4. 业务规则验证:")
    try:
        user_balance = 50
        withdrawal_amount = 100
        validate_business_rule(
            user_balance >= withdrawal_amount,
            "余额不足",
            details={'balance': user_balance, 'requested': withdrawal_amount}
        )
    except BusinessLogicError as e:
        print(f"   ✓ 捕获到业务逻辑错误: {e.message}")
        print(f"   ✓ 详情: {e.details}")
    print()


def demo_flask_error_handling():
    """Demonstrate Flask error handling integration."""
    print("=== 演示Flask错误处理集成 ===\n")
    
    # Create test app
    app = create_app('testing')
    
    # Add test routes that raise different errors
    @app.route('/test/validation-error')
    def test_validation_error():
        raise ValidationError(
            "表单验证失败",
            field_errors={'email': '邮箱格式无效', 'password': '密码太短'}
        )
    
    @app.route('/test/auth-error')
    def test_auth_error():
        raise InvalidCredentialsError()
    
    @app.route('/test/not-found')
    def test_not_found():
        raise UserNotFoundError(user_id="12345")
    
    @app.route('/test/conflict')
    def test_conflict():
        raise DuplicateResourceError("User", "email")
    
    @app.route('/test/business-logic')
    def test_business_logic():
        raise BusinessLogicError(
            "无法执行此操作",
            details={'reason': '用户权限不足'}
        )
    
    @app.route('/test/generic-error')
    def test_generic_error():
        raise ValueError("这是一个通用Python异常")
    
    # Test the error handling
    with app.test_client() as client:
        test_cases = [
            ('/test/validation-error', 'ValidationError'),
            ('/test/auth-error', 'AuthenticationError'),
            ('/test/not-found', 'NotFoundError'),
            ('/test/conflict', 'ConflictError'),
            ('/test/business-logic', 'BusinessLogicError'),
            ('/test/generic-error', 'Generic Exception')
        ]
        
        for endpoint, error_type in test_cases:
            print(f"{error_type} 测试:")
            response = client.get(endpoint)
            data = json.loads(response.data)
            
            print(f"   状态码: {response.status_code}")
            print(f"   错误码: {data.get('code', 'N/A')}")
            print(f"   消息: {data.get('error', 'N/A')}")
            if 'details' in data and data['details']:
                print(f"   详情: {data['details']}")
            print(f"   完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print()


def demo_environment_specific_handling():
    """Demonstrate environment-specific error handling."""
    print("=== 演示环境特定的错误处理 ===\n")
    
    # Test development environment
    print("1. 开发环境错误处理:")
    dev_app = create_app('development')
    dev_app.config['ERROR_INCLUDE_DETAILS'] = True
    dev_app.config['ERROR_INCLUDE_TRACEBACK'] = True
    
    @dev_app.route('/test/error')
    def dev_error():
        raise ValueError("开发环境错误 - 显示详细信息")
    
    with dev_app.test_client() as client:
        response = client.get('/test/error')
        data = json.loads(response.data)
        print(f"   状态码: {response.status_code}")
        print(f"   消息: {data.get('message', 'N/A')}")
        print(f"   包含详情: {'details' in data}")
        print(f"   包含堆栈跟踪: {'traceback' in data}")
    print()
    
    # Test production environment
    print("2. 生产环境错误处理:")
    prod_app = create_app('production')
    
    @prod_app.route('/test/error')
    def prod_error():
        raise ValueError("生产环境错误 - 隐藏敏感信息")
    
    with prod_app.test_client() as client:
        response = client.get('/test/error')
        data = json.loads(response.data)
        print(f"   状态码: {response.status_code}")
        print(f"   消息: {data.get('message', 'N/A')}")
        print(f"   包含详情: {'details' in data and bool(data['details'])}")
        print(f"   包含堆栈跟踪: {'traceback' in data}")
    print()


def demo_error_monitoring():
    """Demonstrate error monitoring capabilities."""
    print("=== 演示错误监控功能 ===\n")
    
    app = create_app('testing')
    app.config['DEBUG'] = True  # Enable error stats endpoint
    app.config['SLOW_REQUEST_THRESHOLD'] = 0.001  # Very low threshold for demo
    
    @app.route('/test/slow')
    def slow_endpoint():
        import time
        time.sleep(0.01)  # Simulate slow request
        return {'message': 'slow response'}
    
    @app.route('/test/error')
    def error_endpoint():
        raise ValidationError("测试错误")
    
    with app.test_client() as client:
        # Make some requests
        print("1. 发送正常请求:")
        response = client.get('/test/slow')
        print(f"   状态码: {response.status_code}")
        
        print("\n2. 发送错误请求:")
        response = client.get('/test/error')
        print(f"   状态码: {response.status_code}")
        
        print("\n3. 检查错误统计:")
        response = client.get('/internal/error-stats')
        if response.status_code == 200:
            stats = json.loads(response.data)
            print(f"   总请求数: {stats['error_stats']['total_requests']}")
            print(f"   错误请求数: {stats['error_stats']['error_requests']}")
            print(f"   慢请求数: {stats['error_stats']['slow_requests']}")
            print(f"   错误类型统计: {stats['error_stats']['error_types']}")
        else:
            print(f"   无法获取统计信息 (状态码: {response.status_code})")
    print()


def main():
    """Run all error handling demos."""
    print("🚀 Flask API 错误处理和异常管理系统演示\n")
    print("=" * 60)
    
    try:
        demo_custom_exceptions()
        demo_error_helpers()
        demo_flask_error_handling()
        demo_environment_specific_handling()
        demo_error_monitoring()
        
        print("=" * 60)
        print("✅ 所有演示完成！错误处理系统工作正常。")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()