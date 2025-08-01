# 常见问题解答和故障排除指南

本指南收集了使用 Flask API Template 时的常见问题和解决方案。

## 📋 目录

- [安装和设置问题](#安装和设置问题)
- [开发环境问题](#开发环境问题)
- [数据库问题](#数据库问题)
- [认证和权限问题](#认证和权限问题)
- [API 调用问题](#api-调用问题)
- [部署问题](#部署问题)
- [性能问题](#性能问题)
- [测试问题](#测试问题)
- [Docker 问题](#docker-问题)
- [日志和调试](#日志和调试)

## 🔧 安装和设置问题

### Q: pip 安装依赖超时或速度慢

**问题**: 在中国大陆地区，pip 安装依赖时经常出现超时或下载速度很慢。

**解决方案**:
```bash
# 方法1: 使用项目提供的配置脚本（推荐）
make configure-pip

# 方法2: 手动配置阿里云镜像源
./scripts/configure_pip_mirror.sh -m aliyun

# 方法3: 临时使用镜像源
pip install -r requirements/development.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 方法4: 查看所有可用镜像源
./scripts/configure_pip_mirror.sh -l

# 方法5: 重置为官方源
./scripts/configure_pip_mirror.sh -r
```

### Q: 安装依赖时出现权限错误

**问题**: 运行 `pip install` 时出现权限错误。

**解决方案**:
```bash
# 使用虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

pip install -r requirements/development.txt

# 或者使用用户安装
pip install --user -r requirements/development.txt
```

### Q: Python 版本不兼容

**问题**: 项目要求 Python 3.11+，但系统版本较低。

**解决方案**:
```bash
# 使用 pyenv 管理 Python 版本
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv local 3.11.0

# 或使用 conda
conda create -n flask-api python=3.11
conda activate flask-api
```

### Q: 环境变量配置错误

**问题**: 应用启动时提示环境变量缺失。

**解决方案**:
```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件，设置必要的变量
# 至少需要设置：
# SECRET_KEY=your-secret-key-here
# JWT_SECRET_KEY=your-jwt-secret-key-here

# 3. 生成安全的密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🛠 开发环境问题

### Q: 开发服务器无法启动

**问题**: 运行 `make run-dev` 时服务器无法启动。

**解决方案**:
```bash
# 1. 检查端口是否被占用
lsof -i :5000  # Mac/Linux
netstat -ano | findstr :5000  # Windows

# 2. 更改端口
export FLASK_PORT=5001
make run-dev

# 3. 检查配置
make debug-config

# 4. 验证环境
make validate-env
```

### Q: 热重载不工作

**问题**: 修改代码后服务器不自动重启。

**解决方案**:
```bash
# 1. 确保启用了重载
export FLASK_USE_RELOADER=true

# 2. 检查文件监控
# 某些系统需要增加文件监控限制
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 3. 使用增强开发服务器
make run-dev
```

### Q: 导入错误

**问题**: 出现模块导入错误。

**解决方案**:
```bash
# 1. 确保在项目根目录
pwd

# 2. 设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 3. 检查虚拟环境
which python
pip list

# 4. 重新安装依赖
pip install -r requirements/development.txt
```

## 🗄️ 数据库问题

### Q: 数据库连接失败

**问题**: 应用无法连接到数据库。

**解决方案**:
```bash
# 1. 检查数据库 URL
echo $DATABASE_URL

# 2. 初始化数据库
make db-init

# 3. 检查数据库文件权限（SQLite）
ls -la instance/
chmod 664 instance/*.db

# 4. 测试数据库连接
python -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    try:
        db.engine.execute('SELECT 1')
        print('✅ 数据库连接成功')
    except Exception as e:
        print(f'❌ 数据库连接失败: {e}')
"
```

### Q: 数据库迁移失败

**问题**: 运行 `flask db migrate` 或 `flask db upgrade` 失败。

**解决方案**:
```bash
# 1. 检查迁移状态
flask db current
flask db history

# 2. 重置迁移（开发环境）
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 3. 手动修复迁移冲突
flask db merge -m "Merge migrations"

# 4. 强制迁移（谨慎使用）
flask db stamp head
```

### Q: 数据库锁定错误

**问题**: SQLite 数据库被锁定。

**解决方案**:
```bash
# 1. 停止所有应用实例
pkill -f "python.*run.py"

# 2. 检查数据库进程
lsof instance/dev_app.db

# 3. 重启数据库连接
rm instance/dev_app.db-journal  # 如果存在

# 4. 使用 WAL 模式（推荐）
# 在配置中设置：
# SQLALCHEMY_ENGINE_OPTIONS = {
#     'pool_pre_ping': True,
#     'connect_args': {'check_same_thread': False}
# }
```

## 🔐 认证和权限问题

### Q: JWT 令牌无效

**问题**: API 调用返回 401 未授权错误。

**解决方案**:
```bash
# 1. 检查令牌格式
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5001/api/auth/me

# 2. 验证令牌是否过期
# 使用 jwt.io 解码令牌检查 exp 字段

# 3. 刷新令牌
curl -X POST -H "Authorization: Bearer YOUR_REFRESH_TOKEN" \
  http://localhost:5001/api/auth/refresh

# 4. 重新登录
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  http://localhost:5001/api/auth/login
```

### Q: 权限不足错误

**问题**: 访问某些 API 时返回 403 权限不足。

**解决方案**:
```bash
# 1. 检查用户权限
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5001/api/auth/me

# 2. 使用管理员账户
# 默认管理员: admin / admin123

# 3. 提升用户权限（管理员操作）
curl -X POST -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_admin": true}' \
  http://localhost:5001/api/users/USER_ID/admin
```

### Q: 密码重置不工作

**问题**: 密码重置功能无法正常工作。

**解决方案**:
```bash
# 1. 检查邮件配置（如果使用邮件）
# 在开发环境中，重置令牌会在日志中显示

# 2. 直接在数据库中重置密码
python -c "
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app('development')
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    user.password_hash = generate_password_hash('new_password')
    db.session.commit()
    print('密码已重置')
"
```

## 🌐 API 调用问题

### Q: CORS 错误

**问题**: 前端调用 API 时出现 CORS 错误。

**解决方案**:
```bash
# 1. 检查 CORS 配置
echo $CORS_ORIGINS

# 2. 更新 CORS 设置
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080"

# 3. 在开发环境中允许所有来源（仅开发）
export CORS_ORIGINS="*"

# 4. 检查预检请求
curl -X OPTIONS -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  http://localhost:5001/api/auth/login
```

### Q: 请求数据验证失败

**问题**: API 返回 400 验证错误。

**解决方案**:
```bash
# 1. 检查请求格式
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Test123!"}' \
  http://localhost:5001/api/auth/register

# 2. 查看详细错误信息
# 在开发环境中，错误响应会包含详细的验证信息

# 3. 检查必需字段
# 参考 API 文档或 Swagger UI: http://localhost:5001/api/doc
```

### Q: 响应数据格式错误

**问题**: API 返回的数据格式不符合预期。

**解决方案**:
```bash
# 1. 检查 Accept 头
curl -H "Accept: application/json" \
  http://localhost:5001/api/health

# 2. 查看 API 文档
# 访问 http://localhost:5001/api/doc

# 3. 检查 API 版本
# 确保使用正确的 API 端点路径
```

## 🚀 部署问题

### Q: Docker 构建时 pip 安装超时

**问题**: Docker 构建过程中 pip 安装依赖时出现网络超时。

**解决方案**:
```bash
# 1. 配置 pip 镜像源（中国大陆用户）
make configure-pip

# 2. 重新构建 Docker 镜像
docker build --no-cache -t flask-api-template .

# 3. 手动配置不同的镜像源
./scripts/configure_pip_mirror.sh -m tencent  # 腾讯云
./scripts/configure_pip_mirror.sh -m douban   # 豆瓣
./scripts/configure_pip_mirror.sh -m tsinghua # 清华大学

# 4. 临时使用代理构建
docker build --build-arg HTTP_PROXY=http://proxy:port \
             --build-arg HTTPS_PROXY=http://proxy:port \
             -t flask-api-template .
```

### Q: Docker 构建失败

**问题**: Docker 镜像构建过程中出现其他错误。

**解决方案**:
```bash
# 1. 清理 Docker 缓存
docker system prune -a

# 2. 使用 --no-cache 重新构建
docker build --no-cache -t flask-api-template .

# 3. 检查 Dockerfile 语法
docker build --dry-run -t flask-api-template .

# 4. 分步构建调试
docker build --target development -t flask-api-template:dev .
```

### Q: 容器启动失败

**问题**: Docker 容器无法正常启动。

**解决方案**:
```bash
# 1. 查看容器日志
docker logs CONTAINER_ID

# 2. 进入容器调试
docker run -it --entrypoint /bin/bash flask-api-template

# 3. 检查环境变量
docker run --env-file .env.prod flask-api-template

# 4. 检查端口映射
docker run -p 5000:5000 flask-api-template
```

### Q: 生产环境性能问题

**问题**: 生产环境中应用响应缓慢。

**解决方案**:
```bash
# 1. 启用生产配置
export FLASK_CONFIG=production

# 2. 使用 Gunicorn
gunicorn -c gunicorn.conf.py wsgi:app

# 3. 配置反向代理
# 使用 Nginx 或其他反向代理

# 4. 启用缓存
# 配置 Redis 或 Memcached

# 5. 数据库优化
# 添加索引，优化查询
```

## ⚡ 性能问题

### Q: 应用响应缓慢

**问题**: API 响应时间过长。

**解决方案**:
```bash
# 1. 启用性能分析
export ENABLE_PROFILING=true
export SLOW_REQUEST_THRESHOLD=0.5

# 2. 检查数据库查询
# 在日志中查看慢查询

# 3. 使用性能测试工具
python examples/test_api.py --performance --requests 100 --concurrent 10

# 4. 优化数据库连接池
# 在配置中调整连接池大小
```

### Q: 内存使用过高

**问题**: 应用内存占用持续增长。

**解决方案**:
```bash
# 1. 监控内存使用
docker stats CONTAINER_ID

# 2. 检查内存泄漏
pip install memory-profiler
python -m memory_profiler your_script.py

# 3. 优化数据库连接
# 确保正确关闭数据库连接

# 4. 调整工作进程数量
# 在 gunicorn.conf.py 中调整 workers 数量
```

## 🧪 测试问题

### Q: 测试失败

**问题**: 运行测试时出现失败。

**解决方案**:
```bash
# 1. 运行单个测试文件
pytest tests/unit/test_auth_service.py -v

# 2. 查看详细错误信息
pytest tests/ -v --tb=long

# 3. 重新创建测试数据库
rm instance/test_app.db
pytest tests/

# 4. 检查测试环境
export FLASK_CONFIG=testing
python -c "from app import create_app; print(create_app('testing').config)"
```

### Q: 测试覆盖率低

**问题**: 代码测试覆盖率不达标。

**解决方案**:
```bash
# 1. 查看覆盖率报告
pytest --cov=app --cov-report=html tests/
open htmlcov/index.html

# 2. 查看未覆盖的代码
pytest --cov=app --cov-report=term-missing tests/

# 3. 添加缺失的测试
# 根据报告添加相应的测试用例
```

## 🐳 Docker 问题

### Q: Docker Compose 服务无法通信

**问题**: 多个服务之间无法正常通信。

**解决方案**:
```bash
# 1. 检查网络配置
docker-compose ps
docker network ls

# 2. 测试服务连接
docker-compose exec app ping db

# 3. 检查端口映射
docker-compose port app 5000

# 4. 查看服务日志
docker-compose logs app
docker-compose logs db
```

### Q: 数据持久化问题

**问题**: 容器重启后数据丢失。

**解决方案**:
```bash
# 1. 检查卷配置
docker-compose config

# 2. 创建命名卷
docker volume create flask_api_data

# 3. 备份数据
docker run --rm -v flask_api_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz -C /data .

# 4. 恢复数据
docker run --rm -v flask_api_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/backup.tar.gz -C /data
```

## 📊 日志和调试

### Q: 日志信息不足

**问题**: 无法获得足够的调试信息。

**解决方案**:
```bash
# 1. 调整日志级别
export LOG_LEVEL=DEBUG

# 2. 启用详细错误信息
export ERROR_INCLUDE_DETAILS=true
export ERROR_INCLUDE_TRACEBACK=true

# 3. 查看应用日志
tail -f logs/app.log

# 4. 使用调试模式
export FLASK_DEBUG=true
make run-dev
```

### Q: 错误追踪困难

**问题**: 难以定位错误来源。

**解决方案**:
```bash
# 1. 启用请求 ID
# 每个请求都会有唯一的 request_id

# 2. 使用结构化日志
# 日志以 JSON 格式输出，便于分析

# 3. 集成错误监控
# 配置 Sentry 或其他错误监控服务

# 4. 添加自定义日志
import logging
logger = logging.getLogger(__name__)
logger.info("Custom log message", extra={"user_id": user.id})
```

## 🆘 获取帮助

如果以上解决方案都无法解决你的问题，可以通过以下方式获取帮助：

### 1. 检查文档
- [开发指南](development.md)
- [部署指南](deployment.md)
- [API 使用指南](api-guide.md)

### 2. 运行诊断工具
```bash
# 环境验证
make validate-env

# 配置调试
make debug-config

# 健康检查
curl http://localhost:5001/api/health/detailed
```

### 3. 收集调试信息
```bash
# 系统信息
python --version
pip list
docker --version
docker-compose --version

# 应用信息
export FLASK_CONFIG=development
python -c "
from app import create_app
app = create_app('development')
print('Flask version:', app.__class__.__module__)
print('Config:', app.config['FLASK_CONFIG'])
print('Debug:', app.config['DEBUG'])
"

# 日志信息
tail -n 100 logs/app.log
```

### 4. 创建最小复现示例
创建一个最小的代码示例来复现问题，这有助于快速定位和解决问题。

### 5. 提交 Issue
在 GitHub 上提交 Issue 时，请包含：
- 问题描述
- 复现步骤
- 期望结果
- 实际结果
- 环境信息
- 相关日志

---

**记住**: 大多数问题都有解决方案，保持耐心，仔细阅读错误信息，逐步排查问题。
