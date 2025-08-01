# API 使用指南

本指南提供了 Flask API Template 的详细 API 使用说明和示例。

## 目录

- [认证流程](#认证流程)
- [API 端点详解](#api-端点详解)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)
- [SDK 和工具](#sdk-和工具)

## 认证流程

### JWT 认证机制

本 API 使用 JWT (JSON Web Token) 进行身份认证。认证流程如下：

1. **用户注册/登录** → 获取访问令牌和刷新令牌
2. **API 调用** → 在请求头中包含访问令牌
3. **令牌刷新** → 使用刷新令牌获取新的访问令牌

### 令牌类型

- **访问令牌 (Access Token)**: 用于 API 调用，有效期较短（默认 15 分钟）
- **刷新令牌 (Refresh Token)**: 用于获取新的访问令牌，有效期较长（默认 30 天）

## API 端点详解

### 认证 API

#### 用户注册

**端点**: `POST /api/auth/register`

**请求示例**:
```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_active": true,
      "is_verified": false,
      "is_admin": false,
      "created_at": "2024-01-01T10:00:00Z"
    },
    "verification_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

#### 用户登录

**端点**: `POST /api/auth/login`

**请求示例**:
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePassword123!"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_active": true,
      "is_verified": true,
      "is_admin": false
    }
  }
}
```

#### 刷新令牌

**端点**: `POST /api/auth/refresh`

**请求示例**:
```bash
curl -X POST http://localhost:5001/api/auth/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 900
  }
}
```

#### 获取当前用户信息

**端点**: `GET /api/auth/me`

**请求示例**:
```bash
curl -X GET http://localhost:5001/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "message": "User information retrieved successfully",
  "data": {
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_active": true,
      "is_verified": true,
      "is_admin": false,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z",
      "last_login": "2024-01-01T12:00:00Z"
    }
  }
}
```

#### 修改密码

**端点**: `POST /api/auth/password/change`

**请求示例**:
```bash
curl -X POST http://localhost:5001/api/auth/password/change \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPassword123!",
    "new_password": "NewPassword123!",
    "confirm_password": "NewPassword123!"
  }'
```

#### 密码重置请求

**端点**: `POST /api/auth/password/reset-request`

**请求示例**:
```bash
curl -X POST http://localhost:5001/api/auth/password/reset-request \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com"
  }'
```

#### 密码重置

**端点**: `POST /api/auth/password/reset`

**请求示例**:
```bash
curl -X POST http://localhost:5001/api/auth/password/reset \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset_token_from_email",
    "new_password": "NewPassword123!",
    "confirm_password": "NewPassword123!"
  }'
```

### 用户管理 API

#### 获取用户列表

**端点**: `GET /api/users`

**查询参数**:
- `page`: 页码（默认: 1）
- `per_page`: 每页数量（默认: 20，最大: 100）
- `search`: 搜索关键词
- `include_inactive`: 是否包含非活跃用户（默认: false）
- `sort_by`: 排序字段（created_at, updated_at, username, email）
- `sort_order`: 排序方向（asc, desc）

**请求示例**:
```bash
curl -X GET "http://localhost:5001/api/users?page=1&per_page=10&search=john&sort_by=created_at&sort_order=desc" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Users retrieved successfully",
  "data": {
    "users": [
      {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true,
        "is_verified": true,
        "is_admin": false,
        "created_at": "2024-01-01T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 1,
      "pages": 1,
      "has_prev": false,
      "has_next": false,
      "prev_num": null,
      "next_num": null
    }
  }
}
```

#### 创建用户

**端点**: `POST /api/users`

**请求示例**:
```bash
curl -X POST http://localhost:5001/api/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "first_name": "New",
    "last_name": "User",
    "is_admin": false
  }'
```

#### 获取用户详情

**端点**: `GET /api/users/{user_id}`

**请求示例**:
```bash
curl -X GET http://localhost:5001/api/users/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 更新用户信息

**端点**: `PUT /api/users/{user_id}`

**请求示例**:
```bash
curl -X PUT http://localhost:5001/api/users/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Updated",
    "last_name": "Name",
    "email": "updated@example.com"
  }'
```

#### 删除用户

**端点**: `DELETE /api/users/{user_id}`

**查询参数**:
- `hard_delete`: 是否永久删除（默认: false，软删除）

**请求示例**:
```bash
# 软删除（停用用户）
curl -X DELETE http://localhost:5001/api/users/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 硬删除（永久删除）
curl -X DELETE "http://localhost:5001/api/users/1?hard_delete=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 用户状态管理

**激活用户**: `POST /api/users/{user_id}/activate`
```bash
curl -X POST http://localhost:5001/api/users/1/activate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**停用用户**: `POST /api/users/{user_id}/deactivate`
```bash
curl -X POST http://localhost:5001/api/users/1/deactivate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**解锁用户**: `POST /api/users/{user_id}/unlock`
```bash
curl -X POST http://localhost:5001/api/users/1/unlock \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 设置管理员权限

**端点**: `POST /api/users/{user_id}/admin`

**请求示例**:
```bash
curl -X POST http://localhost:5001/api/users/1/admin \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_admin": true
  }'
```

#### 搜索用户

**端点**: `GET /api/users/search`

**查询参数**:
- `q`: 搜索关键词（必需，最少 2 个字符）
- `limit`: 结果数量限制（默认: 20，最大: 50）
- `include_inactive`: 是否包含非活跃用户

**请求示例**:
```bash
curl -X GET "http://localhost:5001/api/users/search?q=john&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 用户统计信息

**端点**: `GET /api/users/statistics`

**请求示例**:
```bash
curl -X GET http://localhost:5001/api/users/statistics \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "total_users": 100,
    "active_users": 85,
    "inactive_users": 15,
    "verified_users": 90,
    "unverified_users": 10,
    "admin_users": 5,
    "locked_users": 2,
    "users_created_today": 3,
    "users_created_this_week": 12,
    "users_created_this_month": 45
  }
}
```

### 健康检查 API

#### 基础健康检查

**端点**: `GET /api/health`

**请求示例**:
```bash
curl -X GET http://localhost:5001/api/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "database": {
    "status": "healthy",
    "response_time": 0.05
  }
}
```

#### 详细健康检查

**端点**: `GET /api/health/detailed`

**请求示例**:
```bash
curl -X GET http://localhost:5001/api/health/detailed
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime": 86400,
  "database": {
    "status": "healthy",
    "response_time": 0.05,
    "connection_pool": {
      "size": 10,
      "checked_out": 2,
      "overflow": 0
    }
  },
  "system": {
    "cpu_usage": 25.5,
    "memory_usage": 512.0,
    "disk_usage": 75.2
  },
  "application": {
    "active_users": 150,
    "requests_per_minute": 1200,
    "error_rate": 0.01
  }
}
```

## 错误处理

### 错误响应格式

所有错误响应都遵循统一的格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional error details"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

### 常见错误代码

| HTTP 状态码 | 错误代码 | 描述 |
|-------------|----------|------|
| 400 | `VALIDATION_ERROR` | 请求数据验证失败 |
| 401 | `AUTHENTICATION_ERROR` | 认证失败或令牌无效 |
| 403 | `AUTHORIZATION_ERROR` | 权限不足 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 409 | `CONFLICT` | 资源冲突（如用户名已存在） |
| 422 | `UNPROCESSABLE_ENTITY` | 请求格式正确但语义错误 |
| 423 | `LOCKED` | 账户被锁定 |
| 429 | `RATE_LIMIT_EXCEEDED` | 请求频率超限 |
| 500 | `INTERNAL_SERVER_ERROR` | 服务器内部错误 |

### 验证错误示例

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "username": ["Username is required"],
      "email": ["Invalid email format"],
      "password": ["Password must be at least 8 characters"]
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

## 最佳实践

### 1. 认证和安全

- **始终使用 HTTPS** 在生产环境中
- **安全存储令牌** 不要在客户端明文存储
- **定期刷新令牌** 使用刷新令牌机制
- **实现令牌撤销** 在用户登出时撤销令牌

### 2. 错误处理

- **检查 HTTP 状态码** 不要仅依赖响应体
- **处理网络错误** 实现重试机制
- **记录错误信息** 便于调试和监控

### 3. 性能优化

- **使用分页** 避免一次性获取大量数据
- **实现缓存** 缓存频繁访问的数据
- **压缩请求** 使用 gzip 压缩
- **并发控制** 合理控制并发请求数量

### 4. API 版本管理

- **使用版本号** 在 URL 或请求头中指定版本
- **向后兼容** 保持 API 的向后兼容性
- **文档更新** 及时更新 API 文档

## SDK 和工具

### Python SDK 示例

```python
import requests
from typing import Optional, Dict, Any

class FlaskAPIClient:
    def __init__(self, base_url: str, access_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        response = self.session.post(
            f'{self.base_url}/api/auth/login',
            json={'username': username, 'password': password},
            headers=self._get_headers()
        )
        response.raise_for_status()
        data = response.json()

        if data['success']:
            self.access_token = data['data']['access_token']

        return data

    def get_current_user(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        response = self.session.get(
            f'{self.base_url}/api/auth/me',
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_users(self, page: int = 1, per_page: int = 20,
                  search: Optional[str] = None) -> Dict[str, Any]:
        """获取用户列表"""
        params = {'page': page, 'per_page': per_page}
        if search:
            params['search'] = search

        response = self.session.get(
            f'{self.base_url}/api/users',
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

# 使用示例
client = FlaskAPIClient('http://localhost:5001')

# 登录
login_result = client.login('admin', 'admin123')
print(f"Login successful: {login_result['success']}")

# 获取当前用户信息
user_info = client.get_current_user()
print(f"Current user: {user_info['data']['user']['username']}")

# 获取用户列表
users = client.get_users(page=1, per_page=10)
print(f"Total users: {users['data']['pagination']['total']}")
```

### JavaScript/Node.js SDK 示例

```javascript
class FlaskAPIClient {
    constructor(baseUrl, accessToken = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.accessToken = accessToken;
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        return headers;
    }

    async request(method, endpoint, data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: this.getHeaders()
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error?.message || 'Request failed');
        }

        return result;
    }

    async login(username, password) {
        const result = await this.request('POST', '/api/auth/login', {
            username,
            password
        });

        if (result.success) {
            this.accessToken = result.data.access_token;
        }

        return result;
    }

    async getCurrentUser() {
        return await this.request('GET', '/api/auth/me');
    }

    async getUsers(options = {}) {
        const params = new URLSearchParams();

        Object.entries(options).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                params.append(key, value);
            }
        });

        const queryString = params.toString();
        const endpoint = `/api/users${queryString ? `?${queryString}` : ''}`;

        return await this.request('GET', endpoint);
    }
}

// 使用示例
const client = new FlaskAPIClient('http://localhost:5001');

async function example() {
    try {
        // 登录
        const loginResult = await client.login('admin', 'admin123');
        console.log('Login successful:', loginResult.success);

        // 获取当前用户信息
        const userInfo = await client.getCurrentUser();
        console.log('Current user:', userInfo.data.user.username);

        // 获取用户列表
        const users = await client.getUsers({ page: 1, per_page: 10 });
        console.log('Total users:', users.data.pagination.total);
    } catch (error) {
        console.error('API Error:', error.message);
    }
}

example();
```

### Postman 集合

你可以导入以下 Postman 集合来快速测试 API：

```json
{
  "info": {
    "name": "Flask API Template",
    "description": "Complete API collection for Flask API Template",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:5001/api"
    },
    {
      "key": "access_token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"admin\",\n  \"password\": \"admin123\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/auth/login",
              "host": ["{{base_url}}"],
              "path": ["auth", "login"]
            }
          }
        }
      ]
    }
  ]
}
```

## 总结

本指南涵盖了 Flask API Template 的主要 API 端点和使用方法。更多详细信息请参考：

- **Swagger 文档**: http://localhost:5001/api/doc
- **开发指南**: [docs/development.md](development.md)
- **部署指南**: [docs/deployment.md](deployment.md)

如有问题，请查看项目的 GitHub Issues 或创建新的问题报告。
