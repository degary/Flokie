# Flask API Template

一个功能完整、生产就绪的 Flask API 项目模板，提供现代化的架构设计和最佳实践配置。

## 🚀 特性

- **现代化架构**: 分层架构设计，清晰的代码组织
- **JWT 认证**: 完整的用户认证和授权系统
- **API 文档**: 自动生成的 Swagger/OpenAPI 文档
- **数据库集成**: SQLAlchemy ORM 和数据库迁移支持
- **多环境支持**: 开发、测试、验收、生产环境配置
- **容器化部署**: Docker 和 Docker Compose 支持
- **CI/CD 就绪**: GitHub Actions 工作流配置
- **代码质量**: Black、isort、flake8 代码质量工具
- **测试框架**: pytest 单元测试和集成测试
- **错误处理**: 统一的异常处理和错误响应
- **日志系统**: 结构化日志记录和监控
- **健康检查**: 应用和系统健康状态监控

## 📋 目录

- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API 文档](#api-文档)
- [开发指南](#开发指南)
- [部署指南](#部署指南)
- [配置说明](#配置说明)
- [测试](#测试)
- [网络优化](#网络优化)
- [贡献指南](#贡献指南)

## 🏃‍♂️ 快速开始

### 前置要求

- Python 3.11+
- Docker 和 Docker Compose (可选，用于容器化部署)
- Git

### 安装和运行

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd flask-api-template
   ```

2. **设置开发环境**

   **中国大陆用户（推荐）**:
   ```bash
   # 快速设置 pip 镜像源（推荐）
   make quick-setup

   # 或完整的一键设置（包含镜像源配置、依赖安装等）
   make setup-china
   ```

   **其他用户**:
   ```bash
   # 安装开发依赖和设置 pre-commit hooks
   make install-dev

   # 或者手动安装
   pip install -r requirements/development.txt
   pre-commit install
   ```

3. **配置环境变量**
   ```bash
   # 复制环境变量模板
   cp .env.example .env

   # 编辑 .env 文件，设置必要的配置
   # 至少需要设置 SECRET_KEY 和 JWT_SECRET_KEY
   ```

4. **初始化数据库**
   ```bash
   make db-init
   ```

5. **启动开发服务器**
   ```bash
   # 使用增强的开发服务器（推荐）
   make run-dev

   # 或使用基本的 Flask 开发服务器
   make run
   ```

6. **访问应用**
   - API 基础地址: http://localhost:5001/api
   - API 文档: http://localhost:5001/api/doc/
   - API 规范: http://localhost:5001/api/swagger.json
   - 健康检查: http://localhost:5001/api/health

### Docker 快速启动

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d --build

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f docker-compose.dev.yml down
```

> 📖 详细的 Docker 使用指南请参考 [DOCKER_QUICK_START.md](DOCKER_QUICK_START.md)

### 网络问题解决

如果在中国大陆遇到网络问题，可以使用以下命令：

```bash
# 网络诊断
make network-test

# 配置 pip 镜像源
make configure-pip

# 测试 pip 速度
make test-pip

# 优化 Docker 构建
make docker-build
```

## 📁 项目结构

```
flask-api-template/
├── app/                          # 应用主目录
│   ├── __init__.py              # Flask 应用工厂
│   ├── config/                  # 配置文件
│   │   ├── base.py             # 基础配置
│   │   ├── development.py      # 开发环境配置
│   │   ├── testing.py          # 测试环境配置
│   │   ├── acceptance.py       # 验收环境配置
│   │   └── production.py       # 生产环境配置
│   ├── models/                  # 数据模型
│   │   ├── base.py             # 基础模型类
│   │   └── user.py             # 用户模型
│   ├── services/                # 业务逻辑层
│   │   ├── auth_service.py     # 认证服务
│   │   └── user_service.py     # 用户服务
│   ├── controllers/             # 控制器层
│   │   ├── auth_controller.py  # 认证控制器
│   │   ├── user_controller.py  # 用户控制器
│   │   └── health_controller.py # 健康检查控制器
│   ├── api/                     # API 文档定义
│   │   ├── auth_namespace.py   # 认证 API 文档
│   │   ├── user_namespace.py   # 用户 API 文档
│   │   ├── health_namespace.py # 健康检查 API 文档
│   │   └── models.py           # API 模型定义
│   ├── middleware/              # 中间件
│   │   ├── auth_middleware.py  # 认证中间件
│   │   └── logging_middleware.py # 日志中间件
│   ├── schemas/                 # 数据验证模式
│   │   ├── auth_schemas.py     # 认证数据模式
│   │   ├── user_schemas.py     # 用户数据模式
│   │   └── common_schemas.py   # 通用数据模式
│   ├── utils/                   # 工具函数
│   │   ├── exceptions.py       # 自定义异常
│   │   ├── error_handlers.py   # 错误处理器
│   │   ├── validation.py       # 数据验证工具
│   │   └── logging_config.py   # 日志配置
│   └── extensions.py            # Flask 扩展初始化
├── tests/                       # 测试目录
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   ├── conftest.py            # pytest 配置
│   └── factories.py           # 测试数据工厂
├── migrations/                  # 数据库迁移文件
├── scripts/                     # 脚本工具
│   ├── setup_dev.sh           # 开发环境设置
│   ├── dev_server.py          # 增强开发服务器
│   ├── shell_context.py       # 交互式 shell
│   ├── init_db.py             # 数据库初始化
│   ├── deploy.sh              # 部署脚本
│   └── manage_secrets.sh      # 密钥管理
├── docker/                      # Docker 配置
│   ├── Dockerfile             # 生产环境镜像
│   ├── Dockerfile.dev         # 开发环境镜像
│   └── healthcheck.sh         # 健康检查脚本
├── .github/                     # GitHub Actions 工作流
│   └── workflows/
│       ├── ci.yml             # 持续集成
│       └── cd.yml             # 持续部署
├── docs/                        # 文档
│   ├── development.md         # 开发指南
│   └── deployment.md          # 部署指南
├── requirements/                # 依赖文件
│   ├── base.txt              # 基础依赖
│   ├── development.txt       # 开发依赖
│   ├── testing.txt           # 测试依赖
│   └── production.txt        # 生产依赖
├── .env.example                # 环境变量模板
├── Makefile                    # 开发命令
├── pyproject.toml             # 项目配置
├── run.py                     # 开发服务器入口
└── wsgi.py                    # WSGI 入口
```

## 📚 API 文档

### 自动生成的文档

启动应用后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:5001/api/doc/
- **OpenAPI JSON**: http://localhost:5001/api/swagger.json

### 主要 API 端点

#### 认证 API (`/api/auth`)

- `POST /auth/login` - 用户登录
- `POST /auth/register` - 用户注册
- `POST /auth/refresh` - 刷新访问令牌
- `POST /auth/logout` - 用户登出
- `GET /auth/me` - 获取当前用户信息
- `POST /auth/password/reset-request` - 请求密码重置
- `POST /auth/password/reset` - 重置密码
- `POST /auth/password/change` - 修改密码
- `POST /auth/email/verify` - 验证邮箱

#### 用户管理 API (`/api/users`)

- `GET /users` - 获取用户列表（分页）
- `POST /users` - 创建新用户
- `GET /users/{id}` - 获取用户详情
- `PUT /users/{id}` - 更新用户信息
- `DELETE /users/{id}` - 删除用户
- `POST /users/{id}/activate` - 激活用户
- `POST /users/{id}/deactivate` - 停用用户
- `POST /users/{id}/unlock` - 解锁用户
- `POST /users/{id}/admin` - 设置管理员权限
- `GET /users/search` - 搜索用户
- `GET /users/statistics` - 用户统计信息

#### 健康检查 API (`/api/health`)

- `GET /health` - 基础健康检查
- `GET /health/detailed` - 详细健康检查
- `GET /health/database` - 数据库健康检查
- `GET /health/system` - 系统资源检查
- `GET /health/readiness` - 就绪状态检查
- `GET /health/liveness` - 存活状态检查

### API 使用示例

#### 用户注册和登录

```bash
# 注册新用户
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# 用户登录
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePassword123!"
  }'

# 响应示例
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com",
      "first_name": "Test",
      "last_name": "User",
      "is_active": true,
      "is_verified": false,
      "is_admin": false
    }
  }
}
```

#### 使用 JWT 令牌访问受保护的端点

```bash
# 获取当前用户信息
curl -X GET http://localhost:5001/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 获取用户列表（需要管理员权限）
curl -X GET http://localhost:5001/api/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🛠 开发指南

### 开发环境设置

详细的开发环境设置指南请参考 [docs/development.md](docs/development.md)。

### 常用开发命令

```bash
# 验证项目设置
make verify

# 代码格式化
make format

# 代码质量检查
make lint

# 运行测试
make test

# 启动交互式 shell
make shell

# 查看当前配置
make debug-config

# 验证开发环境
make validate-env
```

### 添加新的 API 端点

1. **创建数据模型** (如果需要)
   ```python
   # app/models/your_model.py
   from app.models.base import BaseModel

   class YourModel(BaseModel):
       __tablename__ = 'your_table'
       # 定义字段
   ```

2. **创建服务层**
   ```python
   # app/services/your_service.py
   class YourService:
       @staticmethod
       def create_item(data):
           # 业务逻辑
           pass
   ```

3. **创建控制器**
   ```python
   # app/controllers/your_controller.py
   from flask import Blueprint

   your_bp = Blueprint('your', __name__)

   @your_bp.route('/items', methods=['POST'])
   def create_item():
       # 处理请求
       pass
   ```

4. **添加 API 文档**
   ```python
   # app/api/your_namespace.py
   from flask_restx import Namespace, Resource

   your_ns = Namespace('your', description='Your operations')

   @your_ns.route('/items')
   class YourResource(Resource):
       def post(self):
           """Create new item"""
           pass
   ```

5. **注册蓝图和命名空间**
   ```python
   # app/__init__.py
   from app.controllers.your_controller import your_bp
   from app.api.your_namespace import your_ns

   def create_app(config_name):
       # ...
       app.register_blueprint(your_bp, url_prefix='/api')
       api.add_namespace(your_ns)
   ```

### 数据库操作

```bash
# 创建新的迁移
flask db migrate -m "Add new table"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade

# 查看迁移历史
flask db history
```

## 🚀 部署指南

详细的部署指南请参考 [docs/deployment.md](docs/deployment.md)。

### 快速部署

#### 开发环境
```bash
./scripts/deploy.sh dev up
```

#### 生产环境
```bash
# 生成密钥
./scripts/manage_secrets.sh generate prod

# 验证配置
python scripts/validate_config.py prod

# 部署
./scripts/deploy.sh prod up --build
```

### Docker 部署

```bash
# 构建镜像
docker build -t flask-api-template .

# 运行容器
docker run -d \
  --name flask-api \
  -p 5000:5000 \
  --env-file .env.prod \
  flask-api-template
```

### Docker Compose 部署

```bash
# 生产环境
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `FLASK_CONFIG` | 运行环境 | `development` | 否 |
| `SECRET_KEY` | Flask 密钥 | - | 是 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | - | 是 |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///app.db` | 否 |
| `FLASK_HOST` | 服务器主机 | `0.0.0.0` | 否 |
| `FLASK_PORT` | 服务器端口 | `5000` | 否 |
| `LOG_LEVEL` | 日志级别 | `INFO` | 否 |

### 配置环境

- **development**: 开发环境，启用调试模式
- **testing**: 测试环境，使用内存数据库
- **acceptance**: 验收环境，生产级配置
- **production**: 生产环境，最高安全级别

### 数据库配置

支持多种数据库：

```bash
# SQLite (开发环境)
DATABASE_URL=sqlite:///app.db

# PostgreSQL (生产环境推荐)
DATABASE_URL=postgresql://user:password@localhost/dbname

# MySQL
DATABASE_URL=mysql://user:password@localhost/dbname
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
make test

# 运行单元测试
make test-unit

# 运行集成测试
make test-integration

# 运行特定测试文件
pytest tests/unit/test_user_service.py -v

# 运行特定测试方法
pytest tests/unit/test_user_service.py::TestUserService::test_create_user -v
```

### 测试覆盖率

测试覆盖率报告会自动生成：

- **终端输出**: 显示覆盖率摘要
- **HTML 报告**: `htmlcov/index.html`
- **XML 报告**: `coverage.xml`

### 编写测试

```python
# tests/unit/test_your_service.py
import pytest
from app.services.your_service import YourService

class TestYourService:
    def test_create_item(self):
        # 测试逻辑
        result = YourService.create_item({'name': 'test'})
        assert result is not None
```

## 🌐 网络优化

针对中国大陆地区的网络环境，我们提供了完整的网络优化解决方案：

### 快速解决网络问题

```bash
# 中国大陆用户一键设置（推荐）
make setup-china

# 网络诊断
make network-test

# 配置 pip 镜像源
make configure-pip

# 测试 pip 速度
make test-pip

# 优化 Docker 构建
make docker-build
```

### 支持的优化功能

- **pip 镜像源**: 支持阿里云、腾讯云、豆瓣等多个国内镜像源
- **Docker 优化**: 容器构建时自动使用镜像源，避免超时
- **网络诊断**: 全面的网络连接和速度测试
- **一键设置**: 中国大陆用户专用的自动化设置脚本

详细信息请参考 [网络优化指南](docs/network-optimization.md)。

## 🤝 贡献指南

### 开发流程

1. **Fork 项目**
2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **提交更改**
   ```bash
   git commit -m "Add your feature"
   ```
4. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```
5. **创建 Pull Request**

### 代码规范

- 使用 **Black** 进行代码格式化
- 使用 **isort** 进行导入排序
- 使用 **flake8** 进行代码检查
- 编写测试用例，保持测试覆盖率 > 80%
- 添加适当的文档字符串

### 提交信息规范

```
type(scope): description

[optional body]

[optional footer]
```

类型：
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 🆘 获取帮助

- **文档**: 查看 `docs/` 目录下的详细文档
- **Issues**: 在 GitHub 上提交问题
- **讨论**: 使用 GitHub Discussions 进行讨论

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和开源社区。

---

**Flask API Template** - 让 API 开发更简单、更高效！
