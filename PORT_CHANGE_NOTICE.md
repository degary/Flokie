# 端口变更通知

## 📢 重要变更

**Flask API Template 的默认端口已从 5000 更改为 5001**

## 🔍 变更原因

在 macOS Big Sur 及更新版本中，端口 5000 被系统的 AirPlay 接收器服务占用，导致 Flask 应用无法正常启动。

### 问题表现
```bash
$ curl -I localhost:5000/api/health
HTTP/1.1 403 Forbidden
Server: AirTunes/860.7.1
```

这表明请求被 macOS 的 AirPlay 服务拦截，而不是 Flask 应用。

## ✅ 解决方案

我们将默认端口更改为 5001，以避免与系统服务冲突。

### 更新的配置

1. **环境变量** (`.env.example`):
   ```bash
   FLASK_PORT=5001
   ```

2. **Docker 配置**:
   - `Dockerfile`: `EXPOSE 5001`
   - `docker-compose.*.yml`: `"5001:5001"`
   - 健康检查: `http://localhost:5001/api/health`

3. **文档更新**:
   - 所有示例 URL 更新为 `localhost:5001`
   - API 文档地址: `http://localhost:5001/api/doc/`

## 🚀 新的访问地址

| 服务 | 旧地址 | 新地址 |
|------|--------|--------|
| API 基础地址 | http://localhost:5000/api | http://localhost:5001/api |
| API 文档 | http://localhost:5000/api/doc | http://localhost:5001/api/doc/ |
| 健康检查 | http://localhost:5000/api/health | http://localhost:5001/api/health |

## 🔧 如何使用

### Docker 启动 (推荐)
```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d --build

# 访问应用
curl http://localhost:5001/api/health
```

### 本地启动
```bash
# 设置环境变量
export FLASK_PORT=5001

# 启动应用
python run.py

# 或使用 make 命令
make run-dev
```

## 🛠 自定义端口

如果需要使用其他端口，可以通过以下方式配置：

### 1. 环境变量方式
```bash
# 在 .env 文件中设置
FLASK_PORT=8080

# 或临时设置
export FLASK_PORT=8080
```

### 2. Docker 方式
编辑 `docker-compose.dev.yml`:
```yaml
services:
  app:
    ports:
      - "8080:8080"  # 主机端口:容器端口
    environment:
      - FLASK_PORT=8080
```

## 🔍 端口冲突检查

如果遇到端口冲突，可以使用以下命令检查：

```bash
# 检查端口占用
lsof -i :5001

# 查看所有监听端口
netstat -an | grep LISTEN

# 或使用项目提供的网络诊断工具
make network-test
```

## 📚 相关文档

- [Docker 快速启动指南](DOCKER_QUICK_START.md)
- [网络优化指南](docs/network-optimization.md)
- [故障排除指南](docs/faq-troubleshooting.md)

## 🆘 遇到问题？

如果在端口变更后遇到任何问题：

1. **清理浏览器缓存**: 确保访问新的端口地址
2. **检查防火墙设置**: 确保端口 5001 未被阻止
3. **运行诊断工具**: `make network-test`
4. **查看详细日志**: `docker-compose logs app`

---

感谢您的理解！这个变更将确保 Flask API Template 在所有 macOS 系统上都能正常运行。
