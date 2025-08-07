#!/usr/bin/env python3
"""
脚本用于修复测试中 User 实例创建时缺少密码的问题
"""

import os
import re


def fix_user_creation_in_file(filepath):
    """修复文件中的 User 创建问题"""
    if not os.path.exists(filepath):
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # 查找 User(...) 创建但没有立即调用 set_password 的模式
    # 这个正则表达式查找 User 创建后没有紧跟 set_password 的情况
    pattern = r"(user\d*\s*=\s*User\([^)]+\))\s*\n(?!\s*user\d*\.set_password)"

    def replacement(match):
        user_creation = match.group(1)
        # 提取变量名
        var_match = re.search(r"(\w+)\s*=\s*User", user_creation)
        if var_match:
            var_name = var_match.group(1)
            return f"{user_creation}\n            {var_name}.set_password('testpassword123')"
        return user_creation

    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.MULTILINE)

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {filepath}")
    else:
        print(f"No changes needed in {filepath}")


# 需要修复的文件列表
files_to_fix = [
    "tests/unit/test_user_model.py",
    "tests/integration/test_database_operations.py",
]

for filepath in files_to_fix:
    fix_user_creation_in_file(filepath)
