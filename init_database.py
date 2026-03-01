"""
数据库初始化脚本
用于初始化MySQL、MongoDB和Redis数据库
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.database_config import DatabaseConfig
from app.utils.log_util import logger

def init_mysql():
    """初始化MySQL数据库"""
    print("=" * 50)
    print("正在初始化MySQL数据库...")
    print("=" * 50)
    
    try:
        from app.database.mysql_manager import mysql_manager
        print("✅ MySQL数据库初始化成功")
        return True
    except Exception as e:
        print(f"❌ MySQL数据库初始化失败: {e}")
        return False

def init_mongodb():
    """初始化MongoDB数据库"""
    print("\n" + "=" * 50)
    print("正在初始化MongoDB数据库...")
    print("=" * 50)
    
    try:
        from app.database.mongodb_manager import mongodb_manager
        print("✅ MongoDB数据库初始化成功")
        return True
    except Exception as e:
        print(f"❌ MongoDB数据库初始化失败: {e}")
        return False

def init_redis():
    """初始化Redis连接"""
    print("\n" + "=" * 50)
    print("正在初始化Redis连接...")
    print("=" * 50)
    
    try:
        from app.database.redis_manager import redis_manager
        print("✅ Redis连接初始化成功")
        return True
    except Exception as e:
        print(f"❌ Redis连接初始化失败: {e}")
        return False

def test_connections():
    """测试所有数据库连接"""
    print("\n" + "=" * 50)
    print("测试数据库连接...")
    print("=" * 50)
    
    results = DatabaseConfig.validate_config()
    
    print("\n连接状态:")
    print(f"  MySQL:   {'✅ 已连接' if results['mysql'] else '❌ 未连接'}")
    print(f"  MongoDB: {'✅ 已连接' if results['mongodb'] else '❌ 未连接'}")
    print(f"  Redis:   {'✅ 已连接' if results['redis'] else '❌ 未连接'}")
    
    return results

def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("🎓 文献解读Agent - 数据库初始化")
    print("=" * 50)
    
    # 显示配置信息
    print("\n数据库配置:")
    print(f"  MySQL:   {DatabaseConfig.MYSQL_CONFIG['host']}:{DatabaseConfig.MYSQL_CONFIG['port']}")
    print(f"  MongoDB: {DatabaseConfig.MONGODB_CONFIG['host']}:{DatabaseConfig.MONGODB_CONFIG['port']}")
    print(f"  Redis:   {DatabaseConfig.REDIS_CONFIG['host']}:{DatabaseConfig.REDIS_CONFIG['port']}")
    
    # 测试连接
    test_results = test_connections()
    
    # 初始化数据库
    if test_results['mysql']:
        init_mysql()
    
    if test_results['mongodb']:
        init_mongodb()
    
    if test_results['redis']:
        init_redis()
    
    print("\n" + "=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)
    
    # 显示使用说明
    print("\n使用说明:")
    print("1. 确保MySQL、MongoDB和Redis服务已启动")
    print("2. 配置环境变量（可选）：")
    print("   - MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
    print("   - MONGODB_HOST, MONGODB_PORT, MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_DATABASE")
    print("   - REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB")
    print("3. 或直接修改 app/config/database_config.py 中的配置")
    print("4. 运行 streamlit run app/main.py 启动系统")

if __name__ == "__main__":
    main()