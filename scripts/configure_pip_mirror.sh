#!/bin/bash
#
# 配置 pip 镜像源脚本
#
# 这个脚本帮助配置 pip 使用国内镜像源，解决网络访问慢的问题。
# 支持多个镜像源选择。
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 显示帮助信息
show_help() {
    echo "配置 pip 镜像源脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -m, --mirror MIRROR    指定镜像源 (aliyun|tencent|douban|tsinghua|ustc)"
    echo "  -g, --global          全局配置 (默认只配置当前用户)"
    echo "  -r, --reset           重置为官方源"
    echo "  -l, --list            列出可用的镜像源"
    echo "  -s, --show            显示当前配置"
    echo "  -h, --help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -m aliyun          # 配置阿里云镜像源"
    echo "  $0 -m tencent -g      # 全局配置腾讯云镜像源"
    echo "  $0 -r                 # 重置为官方源"
    echo "  $0 -s                 # 显示当前配置"
}

# 获取镜像源 URL
get_mirror_url() {
    case $1 in
        aliyun) echo "https://mirrors.aliyun.com/pypi/simple/" ;;
        tencent) echo "https://mirrors.cloud.tencent.com/pypi/simple/" ;;
        douban) echo "https://pypi.doubanio.com/simple/" ;;
        tsinghua) echo "https://pypi.tuna.tsinghua.edu.cn/simple/" ;;
        ustc) echo "https://pypi.mirrors.ustc.edu.cn/simple/" ;;
        official) echo "https://pypi.org/simple/" ;;
        *) echo "" ;;
    esac
}

# 获取可信主机
get_trusted_host() {
    case $1 in
        aliyun) echo "mirrors.aliyun.com" ;;
        tencent) echo "mirrors.cloud.tencent.com" ;;
        douban) echo "pypi.doubanio.com" ;;
        tsinghua) echo "pypi.tuna.tsinghua.edu.cn" ;;
        ustc) echo "pypi.mirrors.ustc.edu.cn" ;;
        official) echo "pypi.org" ;;
        *) echo "" ;;
    esac
}

# 列出可用镜像源
list_mirrors() {
    print_info "可用的镜像源:"
    echo ""
    echo "  aliyun: $(get_mirror_url aliyun)"
    echo "  tencent: $(get_mirror_url tencent)"
    echo "  douban: $(get_mirror_url douban)"
    echo "  tsinghua: $(get_mirror_url tsinghua)"
    echo "  ustc: $(get_mirror_url ustc)"
    echo ""
    echo "  official: $(get_mirror_url official) (官方源)"
}

# 显示当前配置
show_config() {
    print_info "当前 pip 配置:"
    echo ""

    # 检查全局配置
    if [ -f "/etc/pip.conf" ]; then
        echo "全局配置 (/etc/pip.conf):"
        cat /etc/pip.conf
        echo ""
    fi

    # 检查用户配置
    local user_config=""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        user_config="$HOME/Library/Application Support/pip/pip.conf"
    else
        user_config="$HOME/.config/pip/pip.conf"
    fi

    if [ -f "$user_config" ]; then
        echo "用户配置 ($user_config):"
        cat "$user_config"
        echo ""
    fi

    # 显示当前有效配置
    echo "当前有效配置:"
    pip config list 2>/dev/null || echo "  无配置或 pip 版本过低"
}

# 配置镜像源
configure_mirror() {
    local mirror=$1
    local is_global=$2

    local index_url=$(get_mirror_url "$mirror")
    local trusted_host=$(get_trusted_host "$mirror")

    if [ -z "$index_url" ]; then
        print_error "不支持的镜像源: $mirror"
        print_info "使用 -l 选项查看可用的镜像源"
        exit 1
    fi

    print_info "配置 pip 镜像源: $mirror"
    print_info "镜像地址: $index_url"

    # 配置命令
    local config_cmd="pip config set global.index-url $index_url"
    local trust_cmd="pip config set global.trusted-host $trusted_host"

    if [ "$is_global" = true ]; then
        print_info "配置全局镜像源..."
        if [ "$EUID" -ne 0 ]; then
            print_warning "全局配置需要 root 权限，将使用 sudo"
            sudo $config_cmd
            sudo $trust_cmd
        else
            $config_cmd
            $trust_cmd
        fi
    else
        print_info "配置用户镜像源..."
        $config_cmd
        $trust_cmd
    fi

    print_success "镜像源配置完成!"

    # 测试配置
    print_info "测试镜像源连接..."
    if pip install --dry-run --quiet pip >/dev/null 2>&1; then
        print_success "镜像源连接正常"
    else
        print_warning "镜像源连接测试失败，请检查网络连接"
    fi
}

# 重置为官方源
reset_mirror() {
    print_info "重置 pip 为官方源..."

    pip config unset global.index-url 2>/dev/null || true
    pip config unset global.trusted-host 2>/dev/null || true

    print_success "已重置为官方源"
}

# 创建 Docker pip 配置文件
create_docker_config() {
    local mirror=$1

    local index_url=$(get_mirror_url "$mirror")
    local trusted_host=$(get_trusted_host "$mirror")

    if [ -z "$index_url" ]; then
        print_error "不支持的镜像源: $mirror"
        exit 1
    fi

    print_info "创建 Docker pip 配置文件..."

    cat > docker/pip.conf << EOF
[global]
index-url = $index_url
trusted-host = $trusted_host
timeout = 120
retries = 5

[install]
trusted-host = $trusted_host
EOF

    print_success "Docker pip 配置文件已创建: docker/pip.conf"
}

# 主函数
main() {
    local mirror=""
    local is_global=false
    local reset=false
    local list=false
    local show=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--mirror)
                mirror="$2"
                shift 2
                ;;
            -g|--global)
                is_global=true
                shift
                ;;
            -r|--reset)
                reset=true
                shift
                ;;
            -l|--list)
                list=true
                shift
                ;;
            -s|--show)
                show=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 执行相应操作
    if [ "$list" = true ]; then
        list_mirrors
    elif [ "$show" = true ]; then
        show_config
    elif [ "$reset" = true ]; then
        reset_mirror
    elif [ -n "$mirror" ]; then
        configure_mirror "$mirror" "$is_global"
        # 同时创建 Docker 配置文件
        create_docker_config "$mirror"
    else
        print_info "Flask API Template - pip 镜像源配置工具"
        echo ""
        print_info "推荐使用阿里云镜像源（中国大陆用户）:"
        echo "  $0 -m aliyun"
        echo ""
        print_info "查看所有可用选项:"
        echo "  $0 -h"
        echo ""
        print_info "查看可用镜像源:"
        echo "  $0 -l"
    fi
}

# 检查 pip 是否可用
if ! command -v pip &> /dev/null; then
    print_error "pip 未安装或不在 PATH 中"
    exit 1
fi

# 运行主函数
main "$@"
