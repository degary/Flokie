#!/bin/bash
#
# 更新文档中的端口号脚本
#
# 将所有文档中的 localhost:5000 替换为 localhost:5001
#

set -e

print_info() {
    echo "ℹ️  $1"
}

print_success() {
    echo "✅ $1"
}

# 需要更新的文件列表
files=(
    "docs/api-guide.md"
    "docs/deployment.md"
    "docs/faq-troubleshooting.md"
    "examples/api_examples.py"
    "examples/test_api.py"
    "scripts/test_pip_mirror.py"
    "scripts/network_diagnostic.py"
    "scripts/verify_setup.py"
    "docker-compose.dev.yml"
    "docker-compose.yml"
    "docker-compose.prod.yml"
)

print_info "更新文档中的端口号从 5000 到 5001..."

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        print_info "更新文件: $file"
        # 使用 sed 替换 localhost:5000 为 localhost:5001
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' 's/localhost:5000/localhost:5001/g' "$file"
        else
            # Linux
            sed -i 's/localhost:5000/localhost:5000/g' "$file"
        fi
        print_success "已更新: $file"
    else
        echo "⚠️  文件不存在: $file"
    fi
done

print_success "端口更新完成！"
print_info "现在应用将在端口 5001 上运行"
print_info "访问地址: http://localhost:5001/api/health"
