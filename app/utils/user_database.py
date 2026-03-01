import sqlite3
import os
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, Any
from app.utils.log_util import logger

class UserDatabase:
    """用户数据库管理器"""
    
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """初始化数据库"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # 创建用户会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("用户数据库初始化完成")
    
    def hash_password(self, password: str, salt: str = None) -> tuple:
        """
        哈希密码
        
        Args:
            password: 原始密码
            salt: 盐值（可选）
        
        Returns:
            (密码哈希, 盐值)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        return password_hash, salt
    
    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
        
        Returns:
            创建结果
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return {"success": False, "message": "用户名已存在"}
            
            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return {"success": False, "message": "邮箱已被注册"}
            
            # 哈希密码
            password_hash, salt = self.hash_password(password)
            
            # 插入用户
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"创建用户成功: {username}")
            return {"success": True, "message": "注册成功", "user_id": user_id}
            
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return {"success": False, "message": f"注册失败: {e}"}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        验证用户登录
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            验证结果
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 查找用户
            cursor.execute('''
                SELECT id, username, email, password_hash, salt, is_active
                FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            
            if not user:
                return {"success": False, "message": "用户名或密码错误"}
            
            if not user['is_active']:
                return {"success": False, "message": "账户已被禁用"}
            
            # 验证密码
            password_hash, _ = self.hash_password(password, user['salt'])
            
            if password_hash != user['password_hash']:
                return {"success": False, "message": "用户名或密码错误"}
            
            # 更新最后登录时间
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user['id']))
            
            conn.commit()
            conn.close()
            
            logger.info(f"用户登录成功: {username}")
            return {
                "success": True,
                "message": "登录成功",
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email']
                }
            }
            
        except Exception as e:
            logger.error(f"用户登录失败: {e}")
            return {"success": False, "message": f"登录失败: {e}"}
    
    def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """
        创建会话
        
        Args:
            user_id: 用户ID
            expires_hours: 过期时间（小时）
        
        Returns:
            会话令牌
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 生成会话令牌
            session_token = secrets.token_urlsafe(32)
            
            # 计算过期时间
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(hours=expires_hours)).strftime("%Y-%m-%d %H:%M:%S")
            
            # 插入会话
            cursor.execute('''
                INSERT INTO sessions (user_id, session_token, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, session_token, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), expires_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"创建会话成功: user_id={user_id}")
            return session_token
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        验证会话
        
        Args:
            session_token: 会话令牌
        
        Returns:
            用户信息（如果会话有效）
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 查找会话
            cursor.execute('''
                SELECT s.user_id, s.expires_at, u.username, u.email
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
            ''', (session_token,))
            
            session = cursor.fetchone()
            
            if not session:
                return None
            
            # 检查是否过期
            expires_at = datetime.strptime(session['expires_at'], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expires_at:
                # 删除过期会话
                cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
                conn.commit()
                conn.close()
                return None
            
            conn.close()
            
            return {
                "user_id": session['user_id'],
                "username": session['username'],
                "email": session['email']
            }
            
        except Exception as e:
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
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
            conn.commit()
            conn.close()
            
            logger.info("会话删除成功")
            return True
            
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取用户信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户信息
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, created_at, last_login
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return dict(user)
            return None
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

# 全局用户数据库实例
user_db = UserDatabase()