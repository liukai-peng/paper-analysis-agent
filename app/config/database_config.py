"""
数据库配置文件
支持MySQL、MongoDB和Redis
"""
import os
from typing import Dict, Any

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    # 加载.env文件
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ 已加载配置文件: {env_path}")
    else:
        print(f"⚠️ 配置文件不存在: {env_path}")
except ImportError:
    print("⚠️ 未安装python-dotenv，使用系统环境变量")

class DatabaseConfig:
    """数据库配置类"""
    
    # MySQL配置
    MYSQL_CONFIG = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "lkp123456"),
        "database": os.getenv("MYSQL_DATABASE", "literature_agent"),
        "charset": "utf8mb4"
    }
    
    # MongoDB配置
    MONGODB_CONFIG = {
        "host": os.getenv("MONGODB_HOST", "localhost"),
        "port": int(os.getenv("MONGODB_PORT", "27017")),
        "username": os.getenv("MONGODB_USERNAME", None),
        "password": os.getenv("MONGODB_PASSWORD", None),
        "database": os.getenv("MONGODB_DATABASE", "literature_agent")
    }
    
    # Redis配置
    REDIS_CONFIG = {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD", None),
        "db": int(os.getenv("REDIS_DB", "0")),
        "decode_responses": True
    }
    
    # 会话配置
    SESSION_CONFIG = {
        "expires_hours": int(os.getenv("SESSION_EXPIRES_HOURS", "24")),
        "prefix": "session:"
    }
    
    @classmethod
    def get_mysql_url(cls) -> str:
        """获取MySQL连接URL"""
        return f"mysql+pymysql://{cls.MYSQL_CONFIG['user']}:{cls.MYSQL_CONFIG['password']}@{cls.MYSQL_CONFIG['host']}:{cls.MYSQL_CONFIG['port']}/{cls.MYSQL_CONFIG['database']}?charset={cls.MYSQL_CONFIG['charset']}"
    
    @classmethod
    def get_mongodb_url(cls) -> str:
        """获取MongoDB连接URL"""
        if cls.MONGODB_CONFIG['username'] and cls.MONGODB_CONFIG['password']:
            return f"mongodb://{cls.MONGODB_CONFIG['username']}:{cls.MONGODB_CONFIG['password']}@{cls.MONGODB_CONFIG['host']}:{cls.MONGODB_CONFIG['port']}/{cls.MONGODB_CONFIG['database']}"
        return f"mongodb://{cls.MONGODB_CONFIG['host']}:{cls.MONGODB_CONFIG['port']}/{cls.MONGODB_CONFIG['database']}"
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """验证数据库配置"""
        results = {
            "mysql": False,
            "mongodb": False,
            "redis": False
        }
        
        # 测试MySQL连接
        try:
            import pymysql
            conn = pymysql.connect(**cls.MYSQL_CONFIG)
            conn.close()
            results["mysql"] = True
        except Exception as e:
            print(f"MySQL连接失败: {e}")
        
        # 测试MongoDB连接
        try:
            from pymongo import MongoClient
            client = MongoClient(cls.get_mongodb_url(), serverSelectionTimeoutMS=5000)
            client.server_info()
            results["mongodb"] = True
            client.close()
        except Exception as e:
            print(f"MongoDB连接失败: {e}")
        
        # 测试Redis连接
        try:
            import redis
            r = redis.Redis(**cls.REDIS_CONFIG)
            r.ping()
            results["redis"] = True
            r.close()
        except Exception as e:
            print(f"Redis连接失败: {e}")
        
        return results

# 数据库选择配置
USE_DATABASE = {
    "user_auth": "mysql",          # 用户认证使用MySQL
    "literature_notes": "mysql",   # 文献笔记使用MySQL
    "pdf_storage": "mongodb",      # PDF原文存储使用MongoDB
    "analysis_results": "mongodb", # 分析结果存储使用MongoDB
    "session": "redis",            # 会话管理使用Redis
    "cache": "redis"               # 缓存使用Redis
}