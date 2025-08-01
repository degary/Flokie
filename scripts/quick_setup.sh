#!/bin/bash
#
# 快速设置脚本 - 简化版本
#
# 为中国大陆用户提供快速的 pip 镜像源配置
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 配置 pip 镜像源
configure_pip_simple() {
    print_info "配置 pip 阿里云镜像源..."

    # 配置 pip
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set global.trusted-host mirrors.aliyun.com

    print_success "pip 镜像源配置完成"

    # 创建 Docker pip 配置
    print_info "创建 Docker pip 配置..."
    mkdir -p docker
    cat > docker/pip.conf << 'EOF'
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host = mirrors.aliyun.com
timeout = 120
retries = 5

[install]
trusted-host = mirrors.aliyun.com
EOF

    print_success "Docker pip 配置创建完成"
}

# 测试 pip 配置
test_pip_config() {
    print_info "测试 pip 配置..."

    if pip install --dry-run --quiet pip >/dev/null 2>&1; then
        print_success "pip 配置测试通过"
        return 0
    else
        print_warning "pip 配置测试失败"
        return 1
    fi
}

# 主函数
main() {
    echo "🚀 Flask API Template - 快速设置"
    echo "=================================="
    echo ""

    # 检查是否在项目根目录
    if [ ! -f "README.md" ] || [ ! -f "run.py" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi

    # 配置 pip
    configure_pip_simple

    # 测试配置
    test_pip_config

    echo ""
    print_success "快速设置完成！"
    print_info "现在可以运行以下命令："
    print_info "  make install-dev  # 安装开发依赖"
    print_info "  make run-dev      # 启动开发服务器"
    print_info "  make test-pip     # 测试 pip 速度"
}

# 运行主函数
main "$@"
