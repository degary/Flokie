#!/bin/bash
#
# 中国大陆用户一键设置脚本
#
# 这个脚本为中国大陆用户提供一键设置功能，包括：
# - 配置 pip 镜像源
# - 配置 Docker 镜像源
# - 网络优化设置
# - 开发环境初始化
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

print_header() {
    echo -e "${CYAN}$1${NC}"
}

# 显示欢迎信息
show_welcome() {
    clear
    print_header "🇨🇳 Flask API Template - 中国大陆用户一键设置"
    print_header "=" * 60
    echo ""
    print_info "本脚本将为您配置以下内容："
    echo "  📦 pip 镜像源 (阿里云)"
    echo "  🐳 Docker 镜像源 (阿里云)"
    echo "  🌐 网络优化设置"
    echo "  🛠️  开发环境初始化"
    echo "  📚 依赖包安装"
    echo ""

    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "设置已取消"
        exit 0
    fi
}

# 检查系统环境
check_environment() {
    print_step "检查系统环境..."

    # 检查操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
    else
        OS="Unknown"
        print_warning "未知操作系统: $OSTYPE"
    fi

    print_info "操作系统: $OS"

    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 版本: $PYTHON_VERSION"
    else
        print_error "Python3 未安装"
        exit 1
    fi

    # 检查 pip
    if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
        print_success "pip 已安装"
    else
        print_error "pip 未安装"
        exit 1
    fi

    # 检查 Docker (可选)
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version 2>&1 | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker 版本: $DOCKER_VERSION"
        HAS_DOCKER=true
    else
        print_warning "Docker 未安装 (可选)"
        HAS_DOCKER=false
    fi

    # 检查网络连接
    print_info "检查网络连接..."
    if ping -c 1 mirrors.aliyun.com &> /dev/null; then
        print_success "阿里云镜像源连接正常"
    else
        print_warning "阿里云镜像源连接异常"
    fi
}

# 配置 pip 镜像源
configure_pip() {
    print_step "配置 pip 镜像源..."

    if [ -f "scripts/configure_pip_mirror.sh" ]; then
        ./scripts/configure_pip_mirror.sh -m aliyun
        print_success "pip 镜像源配置完成"
    else
        print_warning "pip 配置脚本不存在，手动配置..."

        # 手动配置 pip
        pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
        pip config set global.trusted-host mirrors.aliyun.com

        print_success "pip 镜像源手动配置完成"
    fi

    # 测试 pip 配置
    print_info "测试 pip 配置..."
    if pip install --dry-run --quiet pip >/dev/null 2>&1; then
        print_success "pip 镜像源测试通过"
    else
        print_warning "pip 镜像源测试失败"
    fi
}

# 配置 Docker 镜像源
configure_docker() {
    if [ "$HAS_DOCKER" = false ]; then
        print_info "跳过 Docker 配置 (Docker 未安装)"
        return
    fi

    print_step "配置 Docker 镜像源..."

    # Docker 配置文件路径
    if [[ "$OS" == "macOS" ]]; then
        DOCKER_CONFIG="$HOME/.docker/daemon.json"
    else
        DOCKER_CONFIG="/etc/docker/daemon.json"
    fi

    # 创建 Docker 配置目录
    DOCKER_DIR=$(dirname "$DOCKER_CONFIG")
    if [ ! -d "$DOCKER_DIR" ]; then
        if [[ "$DOCKER_CONFIG" == "/etc/docker/daemon.json" ]]; then
            sudo mkdir -p "$DOCKER_DIR"
        else
            mkdir -p "$DOCKER_DIR"
        fi
    fi

    # 备份现有配置
    if [ -f "$DOCKER_CONFIG" ]; then
        if [[ "$DOCKER_CONFIG" == "/etc/docker/daemon.json" ]]; then
            sudo cp "$DOCKER_CONFIG" "$DOCKER_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        else
            cp "$DOCKER_CONFIG" "$DOCKER_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        print_info "已备份现有 Docker 配置"
    fi

    # 创建新的 Docker 配置
    cat > /tmp/docker_daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://ccr.ccs.tencentyun.com",
    "https://hub-mirror.c.163.com"
  ],
  "dns": ["223.5.5.5", "8.8.8.8"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

    # 安装配置文件
    if [[ "$DOCKER_CONFIG" == "/etc/docker/daemon.json" ]]; then
        sudo mv /tmp/docker_daemon.json "$DOCKER_CONFIG"
        sudo chmod 644 "$DOCKER_CONFIG"
    else
        mv /tmp/docker_daemon.json "$DOCKER_CONFIG"
        chmod 644 "$DOCKER_CONFIG"
    fi

    print_success "Docker 镜像源配置完成"
    print_info "配置文件位置: $DOCKER_CONFIG"

    # 重启 Docker (如果正在运行)
    if docker info &> /dev/null; then
        print_info "重启 Docker 服务以应用配置..."
        if [[ "$OS" == "macOS" ]]; then
            print_warning "请手动重启 Docker Desktop"
        else
            if systemctl is-active --quiet docker; then
                sudo systemctl restart docker
                print_success "Docker 服务已重启"
            fi
        fi
    fi
}

# 设置环境变量
setup_environment() {
    print_step "设置环境变量..."

    # 复制环境变量模板
    if [ -f ".env.example" ] && [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "已创建 .env 文件"
    fi

    # 生成安全密钥
    if [ -f ".env" ]; then
        print_info "生成安全密钥..."

        # 生成 SECRET_KEY
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

        # 更新 .env 文件
        if [[ "$OS" == "macOS" ]]; then
            sed -i '' "s/your-secret-key-here/$SECRET_KEY/" .env
            sed -i '' "s/your-jwt-secret-key-here/$JWT_SECRET_KEY/" .env
        else
            sed -i "s/your-secret-key-here/$SECRET_KEY/" .env
            sed -i "s/your-jwt-secret-key-here/$JWT_SECRET_KEY/" .env
        fi

        print_success "安全密钥已生成"
    fi
}

# 安装依赖
install_dependencies() {
    print_step "安装 Python 依赖..."

    # 检查虚拟环境
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "建议使用虚拟环境"
        read -p "是否创建虚拟环境? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 -m venv venv
            source venv/bin/activate
            print_success "虚拟环境已创建并激活"
        fi
    else
        print_info "检测到虚拟环境: $VIRTUAL_ENV"
    fi

    # 升级 pip
    print_info "升级 pip..."
    pip install --upgrade pip

    # 安装开发依赖
    if [ -f "requirements/development.txt" ]; then
        print_info "安装开发依赖..."
        pip install -r requirements/development.txt
        print_success "开发依赖安装完成"
    elif [ -f "requirements.txt" ]; then
        print_info "安装项目依赖..."
        pip install -r requirements.txt
        print_success "项目依赖安装完成"
    else
        print_warning "未找到依赖文件"
    fi

    # 安装 pre-commit hooks
    if command -v pre-commit &> /dev/null; then
        print_info "安装 pre-commit hooks..."
        pre-commit install
        print_success "pre-commit hooks 安装完成"
    fi
}

# 初始化数据库
initialize_database() {
    print_step "初始化数据库..."

    if [ -f "scripts/init_db.py" ]; then
        python scripts/init_db.py
        print_success "数据库初始化完成"
    elif command -v flask &> /dev/null; then
        export FLASK_APP=run.py
        flask db upgrade 2>/dev/null || flask db init && flask db migrate && flask db upgrade
        print_success "数据库迁移完成"
    else
        print_warning "跳过数据库初始化"
    fi
}

# 运行测试
run_tests() {
    print_step "运行基础测试..."

    # 网络测试
    if [ -f "scripts/test_pip_mirror.py" ]; then
        print_info "测试 pip 镜像源..."
        python scripts/test_pip_mirror.py || true
    fi

    # 健康检查
    if [ -f "run.py" ]; then
        print_info "测试应用启动..."
        timeout 10s python run.py &
        APP_PID=$!
        sleep 3

        if kill -0 $APP_PID 2>/dev/null; then
            print_success "应用启动测试通过"
            kill $APP_PID 2>/dev/null || true
        else
            print_warning "应用启动测试失败"
        fi
    fi
}

# 显示完成信息
show_completion() {
    print_header ""
    print_header "🎉 设置完成!"
    print_header "=" * 60
    echo ""
    print_success "配置摘要:"
    echo "  ✅ pip 镜像源: 阿里云"
    if [ "$HAS_DOCKER" = true ]; then
        echo "  ✅ Docker 镜像源: 阿里云"
    fi
    echo "  ✅ 环境变量: 已配置"
    echo "  ✅ Python 依赖: 已安装"
    echo "  ✅ 数据库: 已初始化"
    echo ""
    print_info "下一步操作:"
    echo "  🚀 启动开发服务器: make run-dev"
    echo "  🧪 运行测试: make test"
    echo "  📚 查看文档: README.md"
    echo "  🌐 API 文档: http://localhost:5000/api/doc"
    echo ""
    print_info "常用命令:"
    echo "  make help          # 查看所有可用命令"
    echo "  make network-test  # 网络诊断"
    echo "  make test-pip      # 测试 pip 速度"
    echo "  make docker-build  # 构建 Docker 镜像"
    echo ""
    print_warning "注意事项:"
    echo "  - 如果使用了虚拟环境，请记得激活: source venv/bin/activate"
    echo "  - 首次运行可能需要一些时间来下载依赖"
    echo "  - 遇到问题请查看 docs/faq-troubleshooting.md"
}

# 主函数
main() {
    # 检查是否在项目根目录
    if [ ! -f "README.md" ] || [ ! -f "run.py" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi

    # 显示欢迎信息
    show_welcome

    # 执行设置步骤
    echo ""
    print_header "开始设置..."
    echo ""

    check_environment
    echo ""

    configure_pip
    echo ""

    configure_docker
    echo ""

    setup_environment
    echo ""

    install_dependencies
    echo ""

    initialize_database
    echo ""

    run_tests
    echo ""

    # 显示完成信息
    show_completion
}

# 错误处理
trap 'print_error "设置过程中发生错误，请检查上面的错误信息"; exit 1' ERR

# 运行主函数
main "$@"
