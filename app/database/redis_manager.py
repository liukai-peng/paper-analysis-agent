"""
Redis会话管理器
用于会话管理、缓存、API限流等高性能场景
"""
import redis
from redis.exceptions import RedisError
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import secrets
import json
from app.config.database_config import DatabaseConfig, USE_DATABASE
from app.utils.log_util import logger

class RedisManager:
    """Redis会话管理器"""
    
    def __init__(self):
        self.config = DatabaseConfig.REDIS_CONFIG
        self.session_config = DatabaseConfig.SESSION_CONFIG
        self.client = None
        self.init_connection()
    
    def init_connection(self):
        """初始化Redis连接"""
        try:
            self.client = redis.Redis(**self.config)
            
            # 测试连接
            self.client.ping()
            
            logger.info("Redis连接初始化完成")
            
        except RedisError as e:
            logger.error(f"Redis连接初始化失败: {e}")
            raise
    
    def create_session(self, user_id: int, expires_hours: int = None) -> str:
        """
        创建会话
        
        Args:
            user_id: 用户ID
            expires_hours: 过期时间（小时）
        
        Returns:
            会话令牌
        """
        try:
            # 生成会话令牌
            session_token = secrets.token_urlsafe(32)
            
            # 设置过期时间
            if expires_hours is None:
                expires_hours = self.session_config['expires_hours']
            
            expires_seconds = expires_hours * 3600
            
            # 会话键
            session_key = f"{self.session_config['prefix']}{session_token}"
            
            # 会话数据
            session_data = {
                "user_id": user_id,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "expires_at": (datetime.now() + timedelta(hours=expires_hours)).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 存储会话
            self.client.setex(
                session_key,
                expires_seconds,
                json.dumps(session_data, ensure_ascii=False)
            )
            
            logger.info(f"创建会话成功: user_id={user_id}")
            return session_token
            
        except RedisError as e:
            logger.error(f"创建会话失败: {e}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        验证会话
        
        Args:
            session_token: 会话令牌
        
        Returns:
            会话数据（如果有效）
        """
        try:
            session_key = f"{self.session_config['prefix']}{session_token}"
            
            # 获取会话数据
            session_data = self.client.get(session_key)
            
            if not session_data:
                return None
            
            # 解析会话数据
            data = json.loads(session_data)
            
            return data
            
        except RedisError as e:
            logger.error(f"验证会话失败: {e}")
            return None
    
    def delete_session(self, session_token: str) -> bool:
        """
        删除会话（登出）
        
        Args:
            session_token: 会话令牌
        
        Returns:
            是否成功
        """
        try:
            session_key = f"{self.session_config['prefix']}{session_token}"
            self.client.delete(session_key)
            
            logger.info("会话删除成功")
            return True
            
        except RedisError as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    def refresh_session(self, session_token: str, expires_hours: int = None) -> bool:
        """
        刷新会话过期时间
        
        Args:
            session_token: 会话令牌
            expires_hours: 过期时间（小时）
        
        Returns:
            是否成功
        """
        try:
            if expires_hours is None:
                expires_hours = self.session_config['expires_hours']
            
            expires_seconds = expires_hours * 3600
            session_key = f"{self.session_config['prefix']}{session_token}"
            
            # 刷新过期时间
            self.client.expire(session_key, expires_seconds)
            
            logger.info("会话刷新成功")
            return True
            
        except RedisError as e:
            logger.error(f"刷新会话失败: {e}")
            return False
    
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
            cache_key = f"cache:{key}"
            
            # 序列化值
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            self.client.setex(cache_key, expires_seconds, value)
            
            return True
            
        except RedisError as e:
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
            cache_key = f"cache:{key}"
            value = self.client.get(cache_key)
            
            if value:
                # 尝试解析JSON
                try:
                    return json.loads(value)
                except:
                    return value.decode('utf-8')
            
            return None
            
        except RedisError as e:
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
            cache_key = f"cache:{key}"
            self.client.delete(cache_key)
            
            return True
            
        except RedisError as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    def rate_limit(self, key: str, limit: int, period: int) -> Dict[str, Any]:
        """
        API限流
        
        Args:
            key: 限流键（如用户ID或IP）
            limit: 限制次数
            period: 时间窗口（秒）
        
        Returns:
            限流结果
        """
        try:
            rate_key = f"rate_limit:{key}"
            
            # 获取当前计数
            current = self.client.get(rate_key)
            
            if current is None:
                # 第一次访问
                self.client.setex(rate_key, period, 1)
                return {
                    "allowed": True,
                    "current": 1,
                    "limit": limit,
                    "remaining": limit - 1,
                    "reset_after": period
                }
            
            current = int(current)
            
            if current >= limit:
                # 超过限制
                ttl = self.client.ttl(rate_key)
                return {
                    "allowed": False,
                    "current": current,
                    "limit": limit,
                    "remaining": 0,
                    "reset_after": ttl
                }
            
            # 增加计数
            self.client.incr(rate_key)
            
            ttl = self.client.ttl(rate_key)
            return {
                "allowed": True,
                "current": current + 1,
                "limit": limit,
                "remaining": limit - current - 1,
                "reset_after": ttl
            }
            
        except RedisError as e:
            logger.error(f"API限流失败: {e}")
            # 出错时允许访问
            return {
                "allowed": True,
                "current": 0,
                "limit": limit,
                "remaining": limit,
                "reset_after": 0
            }
    
    def close(self):
        """关闭Redis连接"""
        if self.client:
            self.client.close()
            logger.info("Redis连接已关闭")

# 全局Redis管理器实例
redis_manager = RedisManager() if USE_DATABASE["session"] == "redis" else None