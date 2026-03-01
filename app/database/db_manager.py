"""
统一数据库管理器
整合MySQL、MongoDB、Redis和SQLite，提供统一的数据库访问接口
自动检测数据库连接，失败时切换到SQLite
"""
import os
from typing import Dict, Any, List, Optional
from app.config.database_config import USE_DATABASE, DatabaseConfig
from app.utils.log_util import logger

# 初始化标志
mysql_available = False
mongodb_available = False
redis_available = False

# 尝试连接MySQL
try:
    from app.database.mysql_manager import mysql_manager
    # 测试连接
    mysql_manager.get_connection()
    mysql_available = True
    logger.info("✅ MySQL连接成功")
except Exception as e:
    logger.warning(f"⚠️ MySQL连接失败: {e}，将使用SQLite作为备选")
    mysql_manager = None

# 如果MySQL不可用，使用SQLite
if not mysql_available:
    try:
        from app.database.sqlite_manager import sqlite_manager as mysql_manager
        logger.info("✅ SQLite初始化成功（作为MySQL备选）")
    except Exception as e:
        logger.error(f"❌ SQLite初始化失败: {e}")
        mysql_manager = None

# 尝试连接MongoDB
try:
    from app.database.mongodb_manager import mongodb_manager
    # 测试连接
    mongodb_manager.client.server_info()
    mongodb_available = True
    logger.info("✅ MongoDB连接成功")
except Exception as e:
    logger.warning(f"⚠️ MongoDB连接失败: {e}")
    mongodb_manager = None

# 尝试连接Redis
try:
    from app.database.redis_manager import redis_manager
    # 测试连接
    redis_manager.client.ping()
    redis_available = True
    logger.info("✅ Redis连接成功")
except Exception as e:
    logger.warning(f"⚠️ Redis连接失败: {e}")
    redis_manager = None

class UnifiedDatabaseManager:
    """统一数据库管理器"""
    
    def __init__(self):
        self.mysql = mysql_manager
        self.mongodb = mongodb_manager
        self.redis = redis_manager
        
        # 记录数据库状态
        self.status = {
            "mysql": mysql_available,
            "mongodb": mongodb_available,
            "redis": redis_available,
            "sqlite_fallback": not mysql_available and mysql_manager is not None
        }
        
        logger.info(f"统一数据库管理器初始化完成: {self.status}")
    
    def get_status(self) -> Dict[str, bool]:
        """获取数据库连接状态"""
        return self.status

    # ==================== 通用数据库操作 ====================

    def execute(self, query: str, params: tuple = None) -> Any:
        """执行SQL查询"""
        if self.mysql:
            return self.mysql.execute(query, params)
        raise AttributeError("数据库未配置")

    def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """获取所有查询结果"""
        if self.mysql:
            return self.mysql.fetch_all(query, params)
        raise AttributeError("数据库未配置")
    
    # ==================== 用户认证相关 ====================
    
    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """创建用户"""
        if self.mysql:
            return self.mysql.create_user(username, email, password)
        return {"success": False, "message": "数据库未配置"}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """验证用户登录"""
        if self.mysql:
            return self.mysql.authenticate_user(username, password)
        return {"success": False, "message": "数据库未配置"}
    
    # ==================== 会话管理相关 ====================
    
    def create_session(self, user_id: int, expires_hours: int = None) -> str:
        """创建会话"""
        if self.redis:
            return self.redis.create_session(user_id, expires_hours)
        # 如果没有Redis，使用内存存储（仅用于开发）
        import secrets
        from datetime import datetime, timedelta
        session_token = secrets.token_urlsafe(32)
        # 这里应该使用内存存储或文件存储
        logger.warning("Redis不可用，会话可能无法持久化")
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """验证会话"""
        if self.redis:
            return self.redis.validate_session(session_token)
        # 如果没有Redis，返回None（需要重新登录）
        return None
    
    def delete_session(self, session_token: str) -> bool:
        """删除会话"""
        if self.redis:
            return self.redis.delete_session(session_token)
        return True
    
    # ==================== 文献笔记相关 ====================
    
    def save_literature_note(self, user_id: int, note_data: Dict[str, Any]) -> int:
        """保存文献笔记"""
        if self.mysql:
            return self.mysql.save_literature_note(user_id, note_data)
        return -1
    
    def get_literature_notes(self, user_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """获取文献笔记列表"""
        if self.mysql:
            return self.mysql.get_literature_notes(user_id, limit)
        return []
    
    def delete_literature_note(self, user_id: int, note_id: int) -> bool:
        """删除文献笔记"""
        if self.mysql:
            return self.mysql.delete_literature_note(user_id, note_id)
        return False
    
    # ==================== 学术语料库相关 ====================
    
    def save_academic_template(self, user_id: int, category: str, content: str) -> int:
        """保存学术模板"""
        if self.mysql:
            return self.mysql.save_academic_template(user_id, category, content)
        return -1
    
    def get_academic_corpus(self, user_id: int) -> Dict[str, List[str]]:
        """获取学术语料库"""
        if self.mysql:
            return self.mysql.get_academic_corpus(user_id)
        return {
            "引言": [],
            "文献综述": [],
            "研究方法": [],
            "数据分析": [],
            "讨论": [],
            "结论": []
        }
    
    # ==================== PDF存储相关 ====================
    
    def save_pdf(self, user_id: int, filename: str, content: bytes, metadata: Dict[str, Any] = None) -> str:
        """保存PDF文件"""
        if self.mongodb:
            return self.mongodb.save_pdf(user_id, filename, content, metadata)
        # 如果没有MongoDB，保存到本地文件系统
        try:
            import hashlib
            from datetime import datetime
            
            # 生成唯一ID
            file_hash = hashlib.md5(content).hexdigest()
            file_id = f"{user_id}_{file_hash}"
            
            # 保存到本地目录
            pdf_dir = os.path.join("data", "pdfs", str(user_id))
            os.makedirs(pdf_dir, exist_ok=True)
            
            file_path = os.path.join(pdf_dir, f"{file_id}.pdf")
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # 保存元数据
            metadata_path = os.path.join(pdf_dir, f"{file_id}.json")
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "user_id": user_id,
                    "filename": filename,
                    "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "metadata": metadata or {}
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"PDF保存到本地: {file_path}")
            return file_id
            
        except Exception as e:
            logger.error(f"保存PDF失败: {e}")
            return None
    
    def get_pdf(self, file_id: str) -> bytes:
        """获取PDF文件"""
        if self.mongodb:
            return self.mongodb.get_pdf(file_id)
        # 从本地文件系统读取
        try:
            # 解析user_id
            user_id = file_id.split('_')[0]
            pdf_dir = os.path.join("data", "pdfs", user_id)
            file_path = os.path.join(pdf_dir, f"{file_id}.pdf")
            
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
            return None
            
        except Exception as e:
            logger.error(f"读取PDF失败: {e}")
            return None
    
    def delete_pdf(self, file_id: str) -> bool:
        """删除PDF文件"""
        if self.mongodb:
            return self.mongodb.delete_pdf(file_id)
        # 从本地文件系统删除
        try:
            user_id = file_id.split('_')[0]
            pdf_dir = os.path.join("data", "pdfs", user_id)
            file_path = os.path.join(pdf_dir, f"{file_id}.pdf")
            metadata_path = os.path.join(pdf_dir, f"{file_id}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            logger.info(f"PDF已删除: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除PDF失败: {e}")
            return False
    
    def list_user_pdfs(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的PDF列表"""
        if self.mongodb:
            return self.mongodb.list_user_pdfs(user_id)
        # 从本地文件系统读取
        try:
            import json
            pdf_dir = os.path.join("data", "pdfs", str(user_id))
            
            if not os.path.exists(pdf_dir):
                return []
            
            pdfs = []
            for filename in os.listdir(pdf_dir):
                if filename.endswith('.json'):
                    metadata_path = os.path.join(pdf_dir, filename)
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        file_id = filename.replace('.json', '')
                        pdfs.append({
                            "file_id": file_id,
                            "filename": metadata.get("filename", "未知"),
                            "upload_date": metadata.get("upload_date", ""),
                            "metadata": metadata.get("metadata", {})
                        })
            
            return sorted(pdfs, key=lambda x: x["upload_date"], reverse=True)
            
        except Exception as e:
            logger.error(f"获取PDF列表失败: {e}")
            return []
    
    # ==================== 分析结果相关 ====================
    
    def save_analysis_result(self, user_id: int, file_id: str, result: Dict[str, Any]) -> str:
        """保存分析结果"""
        if self.mongodb:
            return self.mongodb.save_analysis_result(user_id, file_id, result)
        # 保存到本地文件系统
        try:
            import json
            from datetime import datetime
            
            analysis_dir = os.path.join("data", "analysis", str(user_id))
            os.makedirs(analysis_dir, exist_ok=True)
            
            result_id = f"{file_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            result_path = os.path.join(analysis_dir, f"{result_id}.json")
            
            result["user_id"] = user_id
            result["file_id"] = file_id
            result["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析结果保存到本地: {result_path}")
            return result_id
            
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            return None
    
    def get_analysis_result(self, result_id: str) -> Dict[str, Any]:
        """获取分析结果"""
        if self.mongodb:
            return self.mongodb.get_analysis_result(result_id)
        # 从本地文件系统读取
        try:
            import json
            # 解析user_id
            parts = result_id.split('_')
            user_id = parts[0]
            
            analysis_dir = os.path.join("data", "analysis", user_id)
            result_path = os.path.join(analysis_dir, f"{result_id}.json")
            
            if os.path.exists(result_path):
                with open(result_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            logger.error(f"读取分析结果失败: {e}")
            return None

# 全局统一数据库管理器实例
db_manager = UnifiedDatabaseManager()


def get_db_manager() -> UnifiedDatabaseManager:
    """获取数据库管理器实例"""
    return db_manager