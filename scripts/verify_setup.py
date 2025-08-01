#!/usr/bin/env python3
"""
设置验证脚本

这个脚本用于验证 Flask API Template 的设置是否正确。
"""

import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def print_info(message):
    """打印信息"""
    print(f"ℹ️  {message}")


def print_success(message):
    """打印成功信息"""
    print(f"✅ {message}")


def print_error(message):
    """打印错误信息"""
    print(f"❌ {message}")


def print_warning(message):
    """打印警告信息"""
    print(f"⚠️  {message}")


def print_header(message):
    """打印标题"""
    print(f"\n🔍 {message}")
    print("-" * 50)


class SetupVerifier:
    """设置验证器"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0

    def check(self, description, check_func):
        """执行检查"""
        self.total_checks += 1
        print_info(f"检查: {description}")

        try:
            result = check_func()
            if result:
                print_success(f"{description} - 通过")
                self.success_count += 1
                return True
            else:
                print_error(f"{description} - 失败")
                self.errors.append(description)
                return False
        except Exception as e:
            print_error(f"{description} - 错误: {e}")
            self.errors.append(f"{description}: {e}")
            return False

    def warn(self, description, check_func):
        """执行警告检查"""
        print_info(f"检查: {description}")

        try:
            result = check_func()
            if result:
                print_success(f"{description} - 通过")
                return True
            else:
                print_warning(f"{description} - 建议修复")
                self.warnings.append(description)
                return False
        except Exception as e:
            print_warning(f"{description} - 警告: {e}")
            self.warnings.append(f"{description}: {e}")
            return False

    def verify_python_version(self):
        """验证 Python 版本"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            print_info(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            print_error(
                f"Python 版本过低: {version.major}.{version.minor}.{version.micro} (需要 3.11+)"
            )
            return False

    def verify_project_structure(self):
        """验证项目结构"""
        required_files = [
            "README.md",
            "run.py",
            "wsgi.py",
            ".env.example",
            "requirements.txt",
            "Makefile",
            "pyproject.toml",
        ]

        required_dirs = ["app", "tests", "scripts", "docs", "requirements"]

        missing_files = []
        missing_dirs = []

        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)

        for dir in required_dirs:
            if not Path(dir).exists():
                missing_dirs.append(dir)

        if missing_files or missing_dirs:
            if missing_files:
                print_error(f"缺少文件: {', '.join(missing_files)}")
            if missing_dirs:
                print_error(f"缺少目录: {', '.join(missing_dirs)}")
            return False

        return True

    def verify_environment_file(self):
        """验证环境文件"""
        if not Path(".env").exists():
            print_warning("未找到 .env 文件，将使用默认配置")
            return False

        # 检查关键配置
        with open(".env", "r") as f:
            content = f.read()

        required_vars = ["SECRET_KEY", "JWT_SECRET_KEY"]
        missing_vars = []

        for var in required_vars:
            if f"{var}=your-" in content or f"{var}=" not in content:
                missing_vars.append(var)

        if missing_vars:
            print_warning(f"环境变量需要配置: {', '.join(missing_vars)}")
            return False

        return True

    def verify_dependencies(self):
        """验证依赖包"""
        required_packages = [
            "flask",
            "flask-sqlalchemy",
            "flask-migrate",
            "flask-jwt-extended",
            "flask-cors",
            "flask-restx",
            "marshmallow",
            "gunicorn",
        ]

        missing_packages = []

        for package in required_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            print_error(f"缺少依赖包: {', '.join(missing_packages)}")
            print_info("运行: pip install -r requirements/development.txt")
            return False

        return True

    def verify_pip_config(self):
        """验证 pip 配置"""
        try:
            result = subprocess.run(
                ["pip", "config", "list"], capture_output=True, text=True, check=True
            )

            config = result.stdout
            if "index-url" in config and "mirrors" in config:
                print_info("pip 镜像源已配置")
                return True
            else:
                print_info("使用默认 pip 源")
                return True

        except subprocess.CalledProcessError:
            print_warning("无法获取 pip 配置")
            return False

    def verify_app_import(self):
        """验证应用导入"""
        try:
            # 添加当前目录到 Python 路径
            sys.path.insert(0, os.getcwd())

            from app import create_app

            app = create_app("testing")

            if app:
                print_info("Flask 应用创建成功")
                return True
            else:
                return False

        except Exception as e:
            print_error(f"应用导入失败: {e}")
            return False

    def verify_database_config(self):
        """验证数据库配置"""
        try:
            sys.path.insert(0, os.getcwd())

            from app import create_app, db

            app = create_app("testing")

            with app.app_context():
                # 尝试连接数据库
                db.engine.execute("SELECT 1")
                print_info("数据库连接正常")
                return True

        except Exception as e:
            print_warning(f"数据库连接问题: {e}")
            return False

    def verify_api_endpoints(self):
        """验证 API 端点"""
        try:
            sys.path.insert(0, os.getcwd())

            from app import create_app

            app = create_app("testing")

            with app.test_client() as client:
                # 测试健康检查端点
                response = client.get("/api/health")
                if response.status_code == 200:
                    print_info("API 端点正常")
                    return True
                else:
                    print_error(f"健康检查失败: {response.status_code}")
                    return False

        except Exception as e:
            print_error(f"API 测试失败: {e}")
            return False

    def verify_docker_config(self):
        """验证 Docker 配置"""
        docker_files = ["Dockerfile", "Dockerfile.dev", "docker-compose.yml"]

        existing_files = [f for f in docker_files if Path(f).exists()]

        if existing_files:
            print_info(f"Docker 配置文件: {', '.join(existing_files)}")

            # 检查 pip 配置文件
            if Path("docker/pip.conf").exists():
                print_info("Docker pip 配置已优化")
                return True
            else:
                print_warning("Docker pip 配置未优化")
                return False
        else:
            print_warning("未找到 Docker 配置文件")
            return False

    def verify_development_tools(self):
        """验证开发工具"""
        tools = {"black": "代码格式化", "flake8": "代码检查", "isort": "导入排序", "pytest": "测试框架"}

        available_tools = []
        missing_tools = []

        for tool, description in tools.items():
            try:
                subprocess.run([tool, "--version"], capture_output=True, check=True)
                available_tools.append(f"{tool} ({description})")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(f"{tool} ({description})")

        if available_tools:
            print_info(f"可用工具: {', '.join(available_tools)}")

        if missing_tools:
            print_warning(f"缺少工具: {', '.join(missing_tools)}")
            return len(available_tools) > len(missing_tools)

        return True

    def run_verification(self):
        """运行完整验证"""
        print("🔍 Flask API Template - 设置验证")
        print("=" * 60)

        # 必需检查
        print_header("必需检查")
        self.check("Python 版本", self.verify_python_version)
        self.check("项目结构", self.verify_project_structure)
        self.check("Python 依赖", self.verify_dependencies)
        self.check("应用导入", self.verify_app_import)
        self.check("API 端点", self.verify_api_endpoints)

        # 推荐检查
        print_header("推荐检查")
        self.warn("环境文件", self.verify_environment_file)
        self.warn("pip 配置", self.verify_pip_config)
        self.warn("数据库配置", self.verify_database_config)
        self.warn("Docker 配置", self.verify_docker_config)
        self.warn("开发工具", self.verify_development_tools)

        # 显示结果
        self.show_results()

    def show_results(self):
        """显示验证结果"""
        print_header("验证结果")

        print(f"总检查项: {self.total_checks}")
        print(f"通过检查: {self.success_count}")
        print(f"失败检查: {len(self.errors)}")
        print(f"警告项目: {len(self.warnings)}")

        success_rate = (self.success_count / self.total_checks) * 100
        print(f"成功率: {success_rate:.1f}%")

        if self.errors:
            print_header("需要修复的问题")
            for error in self.errors:
                print_error(error)

        if self.warnings:
            print_header("建议改进的项目")
            for warning in self.warnings:
                print_warning(warning)

        print_header("建议")

        if not self.errors:
            print_success("🎉 所有必需检查都通过了！")
            print_info("你可以开始使用 Flask API Template 了")
            print_info("运行: make run-dev 启动开发服务器")
        else:
            print_error("❌ 存在必需修复的问题")
            print_info("请根据上面的错误信息进行修复")

            if "Python 依赖" in str(self.errors):
                print_info("建议运行: make install-dev 或 make setup-china")

        if self.warnings:
            print_info("💡 建议修复警告项目以获得更好的开发体验")

        print_info("\n📚 更多帮助:")
        print_info("  - 开发指南: docs/development.md")
        print_info("  - 故障排除: docs/faq-troubleshooting.md")
        print_info("  - API 文档: http://localhost:5001/api/doc")


def main():
    """主函数"""
    verifier = SetupVerifier()

    try:
        verifier.run_verification()
    except KeyboardInterrupt:
        print("\n\n⏹️ 验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"验证过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
