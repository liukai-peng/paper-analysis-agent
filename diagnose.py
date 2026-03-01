"""
系统诊断脚本
检查数据库连接和配置
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🔍 文献解读Agent系统 - 诊断工具")
print("=" * 70)
print()

# 1. 检查Python环境
print("📋 Python环境检查")
print(f"   Python版本: {sys.version}")
print(f"   Python路径: {sys.executable}")
print()

# 2. 检查项目结构
print("📁 项目结构检查")
required_files = [
    'app/main.py',
    'app/config/database_config.py',
    'app/database/db_manager.py',
    'app/utils/log_util.py',
    '.env.example',
    'requirements.txt'
]

for file in required_files:
    exists = os.path.exists(file)
    print(f"   {'✅' if exists else '❌'} {file}")

print()

# 3. 检查.env文件
print("🌍 环境变量检查")
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    print(f"   ✅ .env文件存在: {env_path}")
    
    # 尝试加载
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print("   ✅ python-dotenv已加载")
    except ImportError:
        print("   ⚠️ python-dotenv未安装")
    
    # 显示配置（隐藏密码）
    import os
    print("   配置信息:")
    print(f"     MYSQL_HOST: {os.getenv('MYSQL_HOST', '未设置')}")
    print(f"     MYSQL_PORT: {os.getenv('MYSQL_PORT', '未设置')}")
    print(f"     MYSQL_USER: {os.getenv('MYSQL_USER', '未设置')}")
    password = os.getenv('MYSQL_PASSWORD', '')
    print(f"     MYSQL_PASSWORD: {'*' * len(password) if password else '未设置'}")
    print(f"     MYSQL_DATABASE: {os.getenv('MYSQL_DATABASE', '未设置')}")
else:
    print(f"   ❌ .env文件不存在")
    print(f"      请复制.env.example为.env并配置数据库信息")

print()

# 4. 测试数据库连接
print("🗄️ 数据库连接测试")

try:
    from app.config.database_config import DatabaseConfig
    
    # 测试MySQL
    print("   测试MySQL连接...")
    try:
        import pymysql
        conn = pymysql.connect(**DatabaseConfig.MYSQL_CONFIG)
        conn.close()
        print("   ✅ MySQL连接成功")
    except Exception as e:
        print(f"   ❌ MySQL连接失败: {e}")
        print()
        print("   💡 MySQL故障排除:")
        print("      1. 检查MySQL服务是否运行:")
        print("         net start MySQL80")
        print("      2. 检查用户名和密码是否正确")
        print("      3. 检查数据库是否存在:")
        print("         CREATE DATABASE literature_agent;")
        print("      4. 检查防火墙设置")
    
    # 测试MongoDB
    print("   测试MongoDB连接...")
    try:
        from pymongo import MongoClient
        client = MongoClient(DatabaseConfig.get_mongodb_url(), serverSelectionTimeoutMS=5000)
        client.server_info()
        client.close()
        print("   ✅ MongoDB连接成功")
    except Exception as e:
        print(f"   ❌ MongoDB连接失败: {e}")
    
    # 测试Redis
    print("   测试Redis连接...")
    try:
        import redis
        r = redis.Redis(**DatabaseConfig.REDIS_CONFIG)
        r.ping()
        r.close()
        print("   ✅ Redis连接成功")
    except Exception as e:
        print(f"   ❌ Redis连接失败: {e}")
        
except Exception as e:
    print(f"   ❌ 配置加载失败: {e}")

print()

# 5. 检查依赖
print("📦 依赖检查")
required_packages = [
    'streamlit',
    'pymysql',
    'pymongo',
    'redis',
    'cryptography',
    'python-dotenv'
]

for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package} (未安装)")

print()

# 6. 提供解决方案
print("🔧 解决方案")
print()
print("如果MySQL连接失败，系统会自动使用SQLite作为备选方案。")
print("SQLite不需要安装额外的数据库服务，数据会保存在本地文件中。")
print()
print("如果你想使用MySQL，请:")
print("  1. 确保MySQL服务已启动")
print("  2. 编辑.env文件，设置正确的数据库密码")
print("  3. 创建数据库: CREATE DATABASE literature_agent;")
print()
print("如果你只想快速体验系统，可以直接运行，")
print("系统会自动使用SQLite，无需配置MySQL。")

print()
print("=" * 70)
input("按回车键退出...")
