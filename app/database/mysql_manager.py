"""
MySQL数据库管理器
用于存储用户信息、文献笔记、学术语料库等关系型数据
"""
import pymysql
from pymysql.cursors import DictCursor
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import secrets
from app.config.database_config import DatabaseConfig, USE_DATABASE
from app.utils.log_util import logger

class MySQLManager:
    """MySQL数据库管理器"""
    
    def __init__(self):
        self.config = DatabaseConfig.MYSQL_CONFIG
        self.init_database()
    
    def get_connection(self) -> pymysql.Connection:
        """获取数据库连接"""
        return pymysql.connect(**self.config, cursorclass=DictCursor)
    
    def init_database(self):
        """初始化数据库"""
        try:
            # 先连接到MySQL服务器（不指定数据库）
            temp_config = self.config.copy()
            temp_config.pop('database')
            conn = pymysql.connect(**temp_config, cursorclass=DictCursor)
            cursor = conn.cursor()
            
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
            conn.close()
            
            # 连接到目标数据库
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(64) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_username (username),
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # 创建文献笔记表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS literature_notes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    document_type VARCHAR(100),
                    analysis_date DATETIME NOT NULL,
                    first_pass JSON,
                    second_pass JSON,
                    third_pass JSON,
                    my_notes JSON,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at),
                    FULLTEXT INDEX ft_title (title)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # 创建学术语料库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS academic_corpus (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_category (user_id, category),
                    FULLTEXT INDEX ft_content (content)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # 创建分析历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    task_id VARCHAR(100) NOT NULL,
                    title VARCHAR(500),
                    document_type VARCHAR(100),
                    analysis_date DATETIME NOT NULL,
                    result_file VARCHAR(500),
                    status VARCHAR(20) DEFAULT 'completed',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_task_id (task_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("MySQL数据库初始化完成")
            
        except Exception as e:
            logger.error(f"MySQL数据库初始化失败: {e}")
            raise
    
    def hash_password(self, password: str, salt: str = None) -> tuple:
        """哈希密码"""
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
        """创建新用户"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "message": "用户名已存在"}
            
            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "message": "邮箱已被注册"}
            
            # 哈希密码
            password_hash, salt = self.hash_password(password)
            
            # 插入用户
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', (username, email, password_hash, salt, datetime.now()))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"创建用户成功: {username}")
            return {"success": True, "message": "注册成功", "user_id": user_id}
            
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return {"success": False, "message": f"注册失败: {e}"}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """验证用户登录"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 查找用户
            cursor.execute('''
                SELECT id, username, email, password_hash, salt, is_active
                FROM users WHERE username = %s
            ''', (username,))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return {"success": False, "message": "用户名或密码错误"}
            
            if not user['is_active']:
                conn.close()
                return {"success": False, "message": "账户已被禁用"}
            
            # 验证密码
            password_hash, _ = self.hash_password(password, user['salt'])
            
            if password_hash != user['password_hash']:
                conn.close()
                return {"success": False, "message": "用户名或密码错误"}
            
            # 更新最后登录时间
            cursor.execute('''
                UPDATE users SET last_login = %s WHERE id = %s
            ''', (datetime.now(), user['id']))
            
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
    
    def save_literature_note(self, user_id: int, note_data: Dict[str, Any]) -> int:
        """保存文献笔记"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            import json
            cursor.execute('''
                INSERT INTO literature_notes 
                (user_id, title, document_type, analysis_date, first_pass, second_pass, third_pass, my_notes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                note_data.get('title', '未知标题'),
                note_data.get('document_type', '未知类型'),
                note_data.get('analysis_date', datetime.now()),
                json.dumps(note_data.get('first_pass', {}), ensure_ascii=False),
                json.dumps(note_data.get('second_pass', {}), ensure_ascii=False),
                json.dumps(note_data.get('third_pass', {}), ensure_ascii=False),
                json.dumps(note_data.get('my_notes', {}), ensure_ascii=False),
                datetime.now()
            ))
            
            note_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"保存文献笔记成功: user_id={user_id}, note_id={note_id}")
            return note_id
            
        except Exception as e:
            logger.error(f"保存文献笔记失败: {e}")
            raise
    
    def get_literature_notes(self, user_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """获取文献笔记列表"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            import json
            if limit:
                cursor.execute('''
                    SELECT * FROM literature_notes 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM literature_notes 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                ''', (user_id,))
            
            notes = []
            for row in cursor.fetchall():
                note = dict(row)
                note['first_pass'] = json.loads(note['first_pass']) if note['first_pass'] else {}
                note['second_pass'] = json.loads(note['second_pass']) if note['second_pass'] else {}
                note['third_pass'] = json.loads(note['third_pass']) if note['third_pass'] else {}
                note['my_notes'] = json.loads(note['my_notes']) if note['my_notes'] else {}
                notes.append(note)
            
            conn.close()
            return notes
            
        except Exception as e:
            logger.error(f"获取文献笔记失败: {e}")
            return []
    
    def delete_literature_note(self, user_id: int, note_id: int) -> bool:
        """删除文献笔记"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM literature_notes WHERE id = %s AND user_id = %s", (note_id, user_id))
            conn.commit()
            conn.close()
            
            logger.info(f"删除文献笔记成功: user_id={user_id}, note_id={note_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文献笔记失败: {e}")
            return False
    
    def save_academic_template(self, user_id: int, category: str, content: str) -> int:
        """保存学术模板"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO academic_corpus (user_id, category, content, created_at)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, category, content, datetime.now()))
            
            template_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"保存学术模板成功: user_id={user_id}, template_id={template_id}")
            return template_id
            
        except Exception as e:
            logger.error(f"保存学术模板失败: {e}")
            raise
    
    def get_academic_corpus(self, user_id: int) -> Dict[str, List[str]]:
        """获取学术语料库"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category, content FROM academic_corpus 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            ''', (user_id,))
            
            corpus = {
                "引言": [],
                "文献综述": [],
                "研究方法": [],
                "数据分析": [],
                "讨论": [],
                "结论": []
            }
            
            for row in cursor.fetchall():
                category = row['category']
                if category in corpus:
                    corpus[category].append(row['content'])
            
            conn.close()
            return corpus
            
        except Exception as e:
            logger.error(f"获取学术语料库失败: {e}")
            return {
                "引言": [],
                "文献综述": [],
                "研究方法": [],
                "数据分析": [],
                "讨论": [],
                "结论": []
            }

    # ==================== 通用数据库操作 ====================

    def execute(self, query: str, params: tuple = None) -> Any:
        """执行SQL查询"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
            conn.commit()
            conn.close()
            
            return result
            
        except Exception as e:
            logger.error(f"执行SQL查询失败: {e}")
            raise

    def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """获取所有查询结果"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = cursor.fetchall()
            conn.close()
            
            return rows
            
        except Exception as e:
            logger.error(f"获取查询结果失败: {e}")
            raise

# 全局MySQL管理器实例
mysql_manager = MySQLManager() if USE_DATABASE["user_auth"] == "mysql" else None