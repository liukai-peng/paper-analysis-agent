"""
检查环境变量配置
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🔍 环境变量检查")
print("=" * 60)
print()

# 检查.env文件是否存在
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
print(f"📁 .env文件路径: {env_path}")
print(f"   文件存在: {'✅ 是' if os.path.exists(env_path) else '❌ 否'}")
print()

if os.path.exists(env_path):
    print("📄 .env文件内容:")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if 'password' in key.lower():
                        print(f"   {key}={'*' * len(value)}")
                    else:
                        print(f"   {key}={value}")
    print()

# 尝试加载dotenv
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv已安装")
    
    # 加载.env文件
    load_dotenv(env_path)
    print("✅ .env文件已加载")
except ImportError:
    print("❌ python-dotenv未安装")
    print("   安装命令: pip install python-dotenv")

print()
print("🌍 系统环境变量:")
env_vars = [
    'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE',
    'MONGODB_HOST', 'MONGODB_PORT', 'MONGODB_DATABASE',
    'REDIS_HOST', 'REDIS_PORT'
]

for var in env_vars:
    value = os.getenv(var, '未设置')
    if 'password' in var.lower() and value != '未设置':
        value = '*' * len(value)
    print(f"   {var}: {value}")

print()
input("按回车键退出...")
