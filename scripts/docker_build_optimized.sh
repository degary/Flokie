#!/bin/bash
#
# Docker 构建优化脚本
#
# 这个脚本提供了多种 Docker 构建优化策略，特别针对网络问题进行优化。
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
    echo "Docker 构建优化脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -t, --tag TAG         指定镜像标签 (默认: flask-api-template)"
    echo "  -f, --file FILE       指定 Dockerfile (默认: Dockerfile)"
    echo "  -e, --env ENV         指定环境 (dev|prod) (默认: prod)"
    echo "  -m, --mirror MIRROR   指定 pip 镜像源 (aliyun|tencent|douban|tsinghua|ustc)"
    echo "  -p, --proxy PROXY     使用 HTTP 代理"
    echo "  -c, --clean           构建前清理缓存"
    echo "  -n, --no-cache        不使用构建缓存"
    echo "  -q, --quiet           静默模式"
    echo "  -h, --help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                    # 默认构建"
    echo "  $0 -e dev             # 构建开发环境镜像"
    echo "  $0 -m aliyun -c       # 使用阿里云镜像源并清理缓存"
    echo "  $0 -p http://proxy:8080  # 使用代理构建"
    echo "  $0 -t myapp:v1.0      # 指定镜像标签"
}

# 检查 Docker 是否可用
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装或不在 PATH 中"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行或无权限访问"
        exit 1
    fi
}

# 清理 Docker 缓存
clean_docker_cache() {
    print_info "清理 Docker 缓存..."

    # 清理构建缓存
    docker builder prune -f

    # 清理未使用的镜像
    docker image prune -f

    # 清理未使用的容器
    docker container prune -f

    print_success "Docker 缓存清理完成"
}

# 配置 pip 镜像源
configure_pip_mirror() {
    local mirror=$1

    if [ -n "$mirror" ]; then
        print_info "配置 pip 镜像源: $mirror"
        ./scripts/configure_pip_mirror.sh -m "$mirror"
    fi
}

# 构建 Docker 镜像
build_docker_image() {
    local tag=$1
    local dockerfile=$2
    local proxy=$3
    local no_cache=$4
    local quiet=$5

    print_info "开始构建 Docker 镜像..."
    print_info "镜像标签: $tag"
    print_info "Dockerfile: $dockerfile"

    # 构建命令
    local build_cmd="docker build"

    # 添加标签
    build_cmd="$build_cmd -t $tag"

    # 添加 Dockerfile
    build_cmd="$build_cmd -f $dockerfile"

    # 添加代理配置
    if [ -n "$proxy" ]; then
        print_info "使用代理: $proxy"
        build_cmd="$build_cmd --build-arg HTTP_PROXY=$proxy"
        build_cmd="$build_cmd --build-arg HTTPS_PROXY=$proxy"
        build_cmd="$build_cmd --build-arg http_proxy=$proxy"
        build_cmd="$build_cmd --build-arg https_proxy=$proxy"
    fi

    # 添加无缓存选项
    if [ "$no_cache" = true ]; then
        print_info "使用 --no-cache 选项"
        build_cmd="$build_cmd --no-cache"
    fi

    # 添加静默选项
    if [ "$quiet" = true ]; then
        build_cmd="$build_cmd --quiet"
    fi

    # 添加构建上下文
    build_cmd="$build_cmd ."

    print_info "执行命令: $build_cmd"

    # 记录开始时间
    local start_time=$(date +%s)

    # 执行构建
    if eval "$build_cmd"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "镜像构建成功! 耗时: ${duration}s"

        # 显示镜像信息
        print_info "镜像信息:"
        docker images "$tag" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

        return 0
    else
        print_error "镜像构建失败!"
        return 1
    fi
}

# 测试镜像
test_image() {
    local tag=$1

    print_info "测试镜像: $tag"

    # 运行健康检查
    local container_id=$(docker run -d --name test-container "$tag")

    if [ $? -eq 0 ]; then
        print_info "等待容器启动..."
        sleep 10

        # 检查容器状态
        local status=$(docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "unknown")

        if [ "$status" = "healthy" ]; then
            print_success "容器健康检查通过"
        else
            print_warning "容器健康检查状态: $status"
        fi

        # 清理测试容器
        docker stop "$container_id" >/dev/null 2>&1
        docker rm "$container_id" >/dev/null 2>&1

        print_success "镜像测试完成"
        return 0
    else
        print_error "镜像测试失败"
        return 1
    fi
}

# 显示构建统计信息
show_build_stats() {
    local tag=$1

    print_info "构建统计信息:"

    # 镜像大小
    local size=$(docker images "$tag" --format "{{.Size}}")
    echo "  镜像大小: $size"

    # 层数统计
    local layers=$(docker history "$tag" --quiet | wc -l)
    echo "  镜像层数: $layers"

    # 构建历史
    echo "  构建历史:"
    docker history "$tag" --format "table {{.CreatedBy}}\t{{.Size}}" | head -5
}

# 主函数
main() {
    local tag="flask-api-template"
    local dockerfile="Dockerfile"
    local env="prod"
    local mirror=""
    local proxy=""
    local clean=false
    local no_cache=false
    local quiet=false
    local test=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--tag)
                tag="$2"
                shift 2
                ;;
            -f|--file)
                dockerfile="$2"
                shift 2
                ;;
            -e|--env)
                env="$2"
                if [ "$env" = "dev" ]; then
                    dockerfile="Dockerfile.dev"
                    tag="$tag:dev"
                fi
                shift 2
                ;;
            -m|--mirror)
                mirror="$2"
                shift 2
                ;;
            -p|--proxy)
                proxy="$2"
                shift 2
                ;;
            -c|--clean)
                clean=true
                shift
                ;;
            -n|--no-cache)
                no_cache=true
                shift
                ;;
            -q|--quiet)
                quiet=true
                shift
                ;;
            --test)
                test=true
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

    print_info "Flask API Template - Docker 构建优化脚本"
    echo ""

    # 检查 Docker
    check_docker

    # 清理缓存
    if [ "$clean" = true ]; then
        clean_docker_cache
    fi

    # 配置 pip 镜像源
    configure_pip_mirror "$mirror"

    # 构建镜像
    if build_docker_image "$tag" "$dockerfile" "$proxy" "$no_cache" "$quiet"; then
        # 显示统计信息
        if [ "$quiet" != true ]; then
            echo ""
            show_build_stats "$tag"
        fi

        # 测试镜像
        if [ "$test" = true ]; then
            echo ""
            test_image "$tag"
        fi

        echo ""
        print_success "构建完成! 镜像标签: $tag"
        print_info "运行镜像: docker run -p 5000:5000 $tag"

    else
        echo ""
        print_error "构建失败!"

        print_info "故障排除建议:"
        echo "  1. 检查网络连接"
        echo "  2. 尝试使用镜像源: $0 -m aliyun"
        echo "  3. 尝试使用代理: $0 -p http://proxy:port"
        echo "  4. 清理缓存重试: $0 -c"
        echo "  5. 查看详细日志: docker build --progress=plain ..."

        exit 1
    fi
}

# 运行主函数
main "$@"
