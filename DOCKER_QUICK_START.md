# Docker 快速启动指南

## 🚀 快速启动

### 1. 开发环境启动

```bash
# 构建并启动开发环境
docker-compose -f docker-compose.dev.yml up --build

# 或者后台运行
docker-compose -f docker-compose.dev.yml up -d --build
```

### 2. 访问应用

启动成功后，访问以下地址：

- **API 健康检查**: http://localhost:5001/api/health
- **API 文档**: http://localhost:5001/api/doc/
- **API 规范**: http://localhost:5001/api/swagger.json

### 3. 测试 API

```bash
# 健康检查
curl http://localhost:5001/api/health

# 查看 API 文档
curl http://localhost:5001/api/swagger.json
```

## 🔧 常用命令

### 查看日志
```bash
# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs

# 查看应用日志
docker-compose -f docker-compose.dev.yml logs app

# 实时查看日志
docker-compose -f docker-compose.dev.yml logs -f app
```

### 停止服务
```bash
# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除卷
docker-compose -f docker-compose.dev.yml down -v
```

### 重新构建
```bash
# 重新构建镜像
docker-compose -f docker-compose.dev.yml build --no-cache

# 重新构建并启动
docker-compose -f docker-compose.dev.yml up --build --force-recreate
```

## 🐛 故障排除

### 端口冲突问题

如果遇到端口 5001 被占用的问题：

1. **检查端口占用**:
   ```bash
   lsof -i :5001
   ```

2. **修改端口**:
   编辑 `.env` 文件：
   ```bash
   FLASK_PORT=5002
   ```

   然后更新 `docker-compose.dev.yml`：
   ```yaml
   ports:
     - "5002:5002"
   ```

### 构建失败

如果 Docker 构建失败：

1. **清理 Docker 缓存**:
   ```bash
   docker system prune -a
   ```

2. **使用优化构建脚本**:
   ```bash
   make docker-build-dev
   ```

3. **检查网络连接**:
   ```bash
   make network-test
   ```

### 应用无法启动

1. **检查容器状态**:
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

2. **查看详细日志**:
   ```bash
   docker-compose -f docker-compose.dev.yml logs app
   ```

3. **进入容器调试**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec app bash
   ```

## 📊 健康检查

Docker 容器包含自动健康检查：

```bash
# 检查容器健康状态
docker-compose -f docker-compose.dev.yml ps

# 手动执行健康检查
docker-compose -f docker-compose.dev.yml exec app /app/docker/healthcheck.sh
```

健康检查会测试：
- 应用是否响应
- 数据库连接是否正常
- API 端点是否可访问

## 🌐 网络优化

如果在中国大陆遇到构建缓慢的问题：

```bash
# 配置 pip 镜像源
make quick-setup

# 使用优化构建
make docker-build-dev
```

## 📝 开发工作流

1. **启动开发环境**:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **查看日志**:
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f app
   ```

3. **修改代码** (代码会自动重载)

4. **测试 API**:
   ```bash
   curl http://localhost:5001/api/health
   ```

5. **停止环境**:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

## 🎯 生产环境

如果要启动生产环境：

```bash
# 生产环境启动
docker-compose -f docker-compose.prod.yml up -d --build

# 访问地址
curl http://localhost:5001/api/health
```

---

现在你可以使用 Docker 启动 Flask API Template 了！如果遇到任何问题，请查看故障排除部分或运行 `make network-test` 进行诊断。
