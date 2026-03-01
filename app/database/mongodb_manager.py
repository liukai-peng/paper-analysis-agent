"""
MongoDB数据库管理器
用于存储PDF原文、分析结果等大文本和非结构化数据
"""
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.config.database_config import DatabaseConfig, USE_DATABASE
from app.utils.log_util import logger

class MongoDBManager:
    """MongoDB数据库管理器"""
    
    def __init__(self):
        self.config = DatabaseConfig.MONGODB_CONFIG
        self.client = None
        self.db = None
        self.init_database()
    
    def init_database(self):
        """初始化数据库连接"""
        try:
            # 连接MongoDB
            self.client = MongoClient(
                DatabaseConfig.get_mongodb_url(),
                serverSelectionTimeoutMS=5000
            )
            
            # 测试连接
            self.client.server_info()
            
            # 获取数据库
            self.db = self.client[self.config['database']]
            
            # 创建索引
            self.create_indexes()
            
            logger.info("MongoDB数据库初始化完成")
            
        except PyMongoError as e:
            logger.error(f"MongoDB数据库初始化失败: {e}")
            raise
    
    def create_indexes(self):
        """创建索引"""
        try:
            # PDF文档集合索引
            self.db.pdf_documents.create_index([("user_id", 1), ("upload_date", -1)])
            self.db.pdf_documents.create_index([("user_id", 1), ("title", "text")])
            
            # 分析结果集合索引
            self.db.analysis_results.create_index([("user_id", 1), ("analysis_date", -1)])
            self.db.analysis_results.create_index([("user_id", 1), ("task_id", 1)])
            
            # 缓存集合索引
            self.db.cache.create_index([("key", 1)], unique=True)
            self.db.cache.create_index([("expires_at", 1)], expireAfterSeconds=0)
            
            logger.info("MongoDB索引创建完成")
            
        except PyMongoError as e:
            logger.error(f"创建索引失败: {e}")
    
    def save_pdf_document(self, user_id: int, title: str, pdf_bytes: bytes, 
                         metadata: Dict[str, Any] = None) -> str:
        """
        保存PDF文档
        
        Args:
            user_id: 用户ID
            title: 文档标题
            pdf_bytes: PDF文件字节
            metadata: 元数据
        
        Returns:
            文档ID
        """
        try:
            import bson
            
            document = {
                "user_id": user_id,
                "title": title,
                "pdf_data": bson.Binary(pdf_bytes),
                "metadata": metadata or {},
                "upload_date": datetime.now(),
                "size": len(pdf_bytes)
            }
            
            result = self.db.pdf_documents.insert_one(document)
            document_id = str(result.inserted_id)
            
            logger.info(f"保存PDF文档成功: user_id={user_id}, document_id={document_id}")
            return document_id
            
        except PyMongoError as e:
            logger.error(f"保存PDF文档失败: {e}")
            raise
    
    def get_pdf_document(self, user_id: int, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取PDF文档
        
        Args:
            user_id: 用户ID
            document_id: 文档ID
        
        Returns:
            文档数据
        """
        try:
            from bson import ObjectId
            
            document = self.db.pdf_documents.find_one({
                "_id": ObjectId(document_id),
                "user_id": user_id
            })
            
            if document:
                document['_id'] = str(document['_id'])
            
            return document
            
        except PyMongoError as e:
            logger.error(f"获取PDF文档失败: {e}")
            return None
    
    def list_pdf_documents(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        列出用户的PDF文档
        
        Args:
            user_id: 用户ID
            limit: 限制数量
        
        Returns:
            文档列表（不包含PDF数据）
        """
        try:
            documents = self.db.pdf_documents.find(
                {"user_id": user_id},
                {"pdf_data": 0}  # 不返回PDF数据
            ).sort("upload_date", -1).limit(limit)
            
            result = []
            for doc in documents:
                doc['_id'] = str(doc['_id'])
                result.append(doc)
            
            return result
            
        except PyMongoError as e:
            logger.error(f"列出PDF文档失败: {e}")
            return []
    
    def delete_pdf_document(self, user_id: int, document_id: str) -> bool:
        """
        删除PDF文档
        
        Args:
            user_id: 用户ID
            document_id: 文档ID
        
        Returns:
            是否成功
        """
        try:
            from bson import ObjectId
            
            result = self.db.pdf_documents.delete_one({
                "_id": ObjectId(document_id),
                "user_id": user_id
            })
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"删除PDF文档成功: user_id={user_id}, document_id={document_id}")
            
            return success
            
        except PyMongoError as e:
            logger.error(f"删除PDF文档失败: {e}")
            return False
    
    def save_analysis_result(self, user_id: int, task_id: str, result: Dict[str, Any]) -> str:
        """
        保存分析结果
        
        Args:
            user_id: 用户ID
            task_id: 任务ID
            result: 分析结果
        
        Returns:
            结果ID
        """
        try:
            document = {
                "user_id": user_id,
                "task_id": task_id,
                "result": result,
                "analysis_date": datetime.now()
            }
            
            result_doc = self.db.analysis_results.insert_one(document)
            result_id = str(result_doc.inserted_id)
            
            logger.info(f"保存分析结果成功: user_id={user_id}, task_id={task_id}")
            return result_id
            
        except PyMongoError as e:
            logger.error(f"保存分析结果失败: {e}")
            raise
    
    def get_analysis_result(self, user_id: int, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取分析结果
        
        Args:
            user_id: 用户ID
            task_id: 任务ID
        
        Returns:
            分析结果
        """
        try:
            result = self.db.analysis_results.find_one({
                "user_id": user_id,
                "task_id": task_id
            })
            
            if result:
                result['_id'] = str(result['_id'])
            
            return result
            
        except PyMongoError as e:
            logger.error(f"获取分析结果失败: {e}")
            return None
    
    def list_analysis_results(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        列出用户的分析结果
        
        Args:
            user_id: 用户ID
            limit: 限制数量
        
        Returns:
            分析结果列表
        """
        try:
            results = self.db.analysis_results.find(
                {"user_id": user_id}
            ).sort("analysis_date", -1).limit(limit)
            
            result_list = []
            for result in results:
                result['_id'] = str(result['_id'])
                result_list.append(result)
            
            return result_list
            
        except PyMongoError as e:
            logger.error(f"列出分析结果失败: {e}")
            return []
    
    def set_cache(self, key: str, value: Any, expires_seconds: int = 3600) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expires_seconds: 过期时间（秒）
        
        Returns:
            是否成功
        """
        try:
            from datetime import timedelta
            
            document = {
                "key": key,
                "value": value,
                "expires_at": datetime.now() + timedelta(seconds=expires_seconds)
            }
            
            self.db.cache.update_one(
                {"key": key},
                {"$set": document},
                upsert=True
            )
            
            return True
            
        except PyMongoError as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值
        """
        try:
            document = self.db.cache.find_one({"key": key})
            
            if document:
                return document.get("value")
            
            return None
            
        except PyMongoError as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
        
        Returns:
            是否成功
        """
        try:
            self.db.cache.delete_one({"key": key})
            return True
            
        except PyMongoError as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB连接已关闭")

# 全局MongoDB管理器实例
mongodb_manager = MongoDBManager() if USE_DATABASE["pdf_storage"] == "mongodb" else None