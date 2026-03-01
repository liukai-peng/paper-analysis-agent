"""
测试MySQL连接
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.database_config import DatabaseConfig

print("=" * 60)
print("🔍 MySQL连接测试")
print("=" * 60)
print()

# 显示当前配置
print("📋 当前MySQL配置:")
print(f"  主机: {DatabaseConfig.MYSQL_CONFIG['host']}")
print(f"  端口: {DatabaseConfig.MYSQL_CONFIG['port']}")
print(f"  用户: {DatabaseConfig.MYSQL_CONFIG['user']}")
print(f"  密码: {'*' * len(DatabaseConfig.MYSQL_CONFIG['password']) if DatabaseConfig.MYSQL_CONFIG['password'] else '未设置'}")
print(f"  数据库: {DatabaseConfig.MYSQL_CONFIG['database']}")
print()

# 测试连接
print("🔄 测试连接...")
results = DatabaseConfig.validate_config()

print()
print("📊 连接结果:")
print(f"  MySQL:   {'✅ 已连接' if results['mysql'] else '❌ 未连接'}")
print(f"  MongoDB: {'✅ 已连接' if results['mongodb'] else '❌ 未连接'}")
print(f"  Redis:   {'✅ 已连接' if results['redis'] else '❌ 未连接'}")

if not results['mysql']:
    print()
    print("❌ MySQL连接失败，请检查:")
    print("  1. MySQL服务是否已启动")
    print("  2. 用户名和密码是否正确")
    print("  3. 数据库是否存在")
    print("  4. 端口是否正确")
    print()
    print("💡 解决方法:")
    print("  1. 启动MySQL服务: net start MySQL80")
    print("  2. 检查.env文件中的配置")
    print("  3. 创建数据库: CREATE DATABASE literature_agent;")

print()
input("按回车键退出...")
