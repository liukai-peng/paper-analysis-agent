"""
测试导入是否正常工作
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 测试Python导入...")
print(f"Python路径: {sys.path[0]}")
print()

# 测试基本导入
try:
    print("1. 测试 app.utils.log_util...")
    from app.utils.log_util import logger
    print("   ✅ 成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("2. 测试 app.utils.config_manager...")
    from app.utils.config_manager import config_manager
    print("   ✅ 成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("3. 测试 app.utils.user_database...")
    from app.utils.user_database import user_db
    print("   ✅ 成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("4. 测试 app.pages.auth_page...")
    from app.ui_modules.auth_page import render_auth_page
    print("   ✅ 成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("5. 测试 app.config.database_config...")
    from app.config.database_config import DatabaseConfig
    print("   ✅ 成功")
except Exception as e:
    print(f"   ❌ 失败: {e}")

print()
print("✅ 导入测试完成！")
input("按回车键退出...")
