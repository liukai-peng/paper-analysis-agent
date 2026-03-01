import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.utils.log_util import logger


class UserDataManager:
    """用户数据管理器，为每个用户提供独立的数据存储"""

    def __init__(self, db_manager=None, base_data_dir: str = "user_data"):
        """
        初始化用户数据管理器

        Args:
            db_manager: 数据库管理器（可选，用于统一数据库）
            base_data_dir: 基础数据目录（用于独立数据库）
        """
        self.db_manager = db_manager
        self.base_data_dir = base_data_dir
        os.makedirs(base_data_dir, exist_ok=True)

    def get_user_dir(self, user_id: int) -> str:
        """
        获取用户数据目录

        Args:
            user_id: 用户ID

        Returns:
            用户数据目录路径
        """
        user_dir = os.path.join(self.base_data_dir, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def get_user_db_path(self, user_id: int) -> str:
        """
        获取用户数据库路径

        Args:
            user_id: 用户ID

        Returns:
            数据库文件路径
        """
        return os.path.join(self.get_user_dir(user_id), "data.db")

    def init_user_database(self, user_id: int):
        """
        初始化用户数据库

        Args:
            user_id: 用户ID
        """
        db_path = self.get_user_db_path(user_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 文献笔记表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS literature_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                document_type TEXT,
                analysis_date TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        ''')

        # 学术语料库表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS academic_corpus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        # 分析历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                title TEXT,
                document_type TEXT,
                analysis_date TEXT NOT NULL,
                result_file TEXT,
                status TEXT DEFAULT 'completed'
            )
        ''')

        conn.commit()
        conn.close()
        logger.info(f"用户数据库初始化完成: user_id={user_id}")

    def save_literature_note(self, user_id: int, title: str, content: Dict[str, Any], literature_type: str = "") -> int:
        """
        保存文献笔记

        Args:
            user_id: 用户ID
            title: 文献标题
            content: 分析结果内容
            literature_type: 文献类型

        Returns:
            笔记ID
        """
        try:
            # 优先保存到本地数据库（更可靠）
            return self._save_to_local_db(user_id, title, content, literature_type)

        except Exception as e:
            logger.error(f"保存到本地数据库失败: {e}")
            # 如果本地保存失败，尝试使用统一数据库
            if self.db_manager:
                return self._save_to_db_manager(user_id, title, content, literature_type)
            raise

    def _save_to_db_manager(self, user_id: int, title: str, content: Dict[str, Any], literature_type: str) -> int:
        """保存到统一数据库管理器"""
        try:
            # 使用MySQL的%s占位符
            query = """
                INSERT INTO literature_notes (user_id, title, document_type, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (
                user_id,
                title,
                literature_type,
                json.dumps(content, ensure_ascii=False),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            if hasattr(self.db_manager, 'execute'):
                result = self.db_manager.execute(query, params)
                logger.info(f"保存文献笔记成功: user_id={user_id}, title={title}")
                return result
            else:
                raise AttributeError("db_manager 没有 execute 方法")

        except Exception as e:
            logger.error(f"保存到统一数据库失败: {e}")
            # 回退到本地数据库
            return self._save_to_local_db(user_id, title, content, literature_type)

    def _save_to_local_db(self, user_id: int, title: str, content: Dict[str, Any], literature_type: str) -> int:
        """保存到本地独立数据库"""
        db_path = self.get_user_db_path(user_id)
        if not os.path.exists(db_path):
            self.init_user_database(user_id)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO literature_notes
            (title, document_type, analysis_date, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            title,
            literature_type,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            json.dumps(content, ensure_ascii=False),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        note_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"保存文献笔记成功: user_id={user_id}, note_id={note_id}")
        return note_id

    def get_user_literature_notes(self, user_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取用户文献笔记列表

        Args:
            user_id: 用户ID
            limit: 限制数量

        Returns:
            笔记列表
        """
        try:
            # 首先尝试从本地数据库获取（因为数据可能保存在这里）
            local_notes = self._get_from_local_db(user_id, limit)
            if local_notes:
                return local_notes

            # 如果本地没有，尝试使用统一数据库
            if self.db_manager:
                return self._get_from_db_manager(user_id, limit)

            return []

        except Exception as e:
            logger.error(f"获取文献笔记失败: {e}")
            # 最后尝试本地数据库
            return self._get_from_local_db(user_id, limit)

    def _get_from_db_manager(self, user_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """从统一数据库获取"""
        try:
            # 使用MySQL的%s占位符
            query = "SELECT * FROM literature_notes WHERE user_id = %s ORDER BY created_at DESC"
            params = [user_id]

            if limit:
                query += " LIMIT %s"
                params.append(limit)

            if hasattr(self.db_manager, 'fetch_all'):
                rows = self.db_manager.fetch_all(query, tuple(params))
                notes = []
                for row in rows:
                    note = dict(row)
                    # 解析content字段
                    if note.get('content'):
                        try:
                            note['content'] = json.loads(note['content'])
                        except:
                            pass
                    notes.append(note)
                return notes
            else:
                raise AttributeError("db_manager 没有 fetch_all 方法")

        except Exception as e:
            logger.error(f"从统一数据库获取失败: {e}")
            return self._get_from_local_db(user_id, limit)

    def _get_from_local_db(self, user_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """从本地数据库获取"""
        db_path = self.get_user_db_path(user_id)
        if not os.path.exists(db_path):
            return []

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if limit:
            cursor.execute('''
                SELECT * FROM literature_notes ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
        else:
            cursor.execute('''
                SELECT * FROM literature_notes ORDER BY created_at DESC
            ''')

        notes = []
        for row in cursor.fetchall():
            note = dict(row)
            # 解析content字段
            if note.get('content'):
                try:
                    note['content'] = json.loads(note['content'])
                except:
                    pass
            notes.append(note)

        conn.close()
        return notes

    def delete_literature_note(self, user_id: int, note_id: int) -> bool:
        """
        删除文献笔记

        Args:
            user_id: 用户ID
            note_id: 笔记ID

        Returns:
            是否成功
        """
        try:
            if self.db_manager:
                return self._delete_from_db_manager(user_id, note_id)
            else:
                return self._delete_from_local_db(user_id, note_id)

        except Exception as e:
            logger.error(f"删除文献笔记失败: {e}")
            return False

    def _delete_from_db_manager(self, user_id: int, note_id: int) -> bool:
        """从统一数据库删除"""
        try:
            query = "DELETE FROM literature_notes WHERE id = ? AND user_id = ?"
            params = (note_id, user_id)

            if hasattr(self.db_manager, 'execute'):
                self.db_manager.execute(query, params)
                logger.info(f"删除文献笔记成功: user_id={user_id}, note_id={note_id}")
                return True
            else:
                raise AttributeError("db_manager 没有 execute 方法")

        except Exception as e:
            logger.error(f"从统一数据库删除失败: {e}")
            return self._delete_from_local_db(user_id, note_id)

    def _delete_from_local_db(self, user_id: int, note_id: int) -> bool:
        """从本地数据库删除"""
        db_path = self.get_user_db_path(user_id)
        if not os.path.exists(db_path):
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM literature_notes WHERE id = ?", (note_id,))
        conn.commit()
        conn.close()

        logger.info(f"删除文献笔记成功: user_id={user_id}, note_id={note_id}")
        return True

    def save_academic_corpus(self, user_id: int, category: str, content: str) -> int:
        """
        保存学术语料

        Args:
            user_id: 用户ID
            category: 语料类别
            content: 语料内容

        Returns:
            语料ID
        """
        db_path = self.get_user_db_path(user_id)
        if not os.path.exists(db_path):
            self.init_user_database(user_id)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO academic_corpus (category, content, created_at)
            VALUES (?, ?, ?)
        ''', (category, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        corpus_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"保存学术语料成功: user_id={user_id}, corpus_id={corpus_id}")
        return corpus_id

    def get_academic_corpus(self, user_id: int, category: str = None):
        """
        获取学术语料

        Args:
            user_id: 用户ID
            category: 语料类别（可选）

        Returns:
            如果指定category，返回该类别的语料列表
            如果不指定category，返回按类别分组的字典
        """
        db_path = self.get_user_db_path(user_id)
        if not os.path.exists(db_path):
            if category:
                return []
            return {
                "引言": [],
                "文献综述": [],
                "研究方法": [],
                "数据分析": [],
                "讨论": [],
                "结论": []
            }

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if category:
            cursor.execute('''
                SELECT * FROM academic_corpus WHERE category = ? ORDER BY created_at DESC
            ''', (category,))
            corpus = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return corpus
        else:
            cursor.execute('''
                SELECT * FROM academic_corpus ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            # 按类别分组
            default_categories = ["引言", "文献综述", "研究方法", "数据分析", "讨论", "结论"]
            corpus = {cat: [] for cat in default_categories}
            
            for row in rows:
                row_dict = dict(row)
                cat = row_dict.get('category', '其他')
                if cat not in corpus:
                    corpus[cat] = []
                corpus[cat].append(row_dict.get('content', ''))
            
            return corpus

    def get_literature_notes(self, user_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """获取文献笔记（别名方法）"""
        return self.get_user_literature_notes(user_id, limit)

    def save_academic_template(self, user_id: int, category: str, content: str) -> int:
        """保存学术模板（别名方法）"""
        return self.save_academic_corpus(user_id, category, content)

    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        导出用户数据

        Args:
            user_id: 用户ID

        Returns:
            包含所有用户数据的字典
        """
        return {
            "literature_notes": self.get_user_literature_notes(user_id),
            "academic_corpus": self.get_academic_corpus(user_id)
        }

    def import_user_data(self, user_id: int, data: Dict[str, Any], merge: bool = True) -> Dict[str, int]:
        """
        导入用户数据

        Args:
            user_id: 用户ID
            data: 要导入的数据
            merge: 是否合并（True）或覆盖（False）

        Returns:
            导入统计信息
        """
        stats = {"literature_notes": 0, "academic_templates": 0}

        # 如果不合并，先清空现有数据
        if not merge:
            db_path = self.get_user_db_path(user_id)
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM literature_notes")
                cursor.execute("DELETE FROM academic_corpus")
                conn.commit()
                conn.close()

        # 导入文献笔记
        if "literature_notes" in data:
            for note in data["literature_notes"]:
                try:
                    self.save_literature_note(
                        user_id,
                        note.get("title", "Untitled"),
                        note.get("content", {}),
                        note.get("document_type", "")
                    )
                    stats["literature_notes"] += 1
                except Exception as e:
                    logger.error(f"导入文献笔记失败: {e}")

        # 导入学术语料
        if "academic_corpus" in data:
            for item in data["academic_corpus"]:
                try:
                    self.save_academic_corpus(
                        user_id,
                        item.get("category", "general"),
                        item.get("content", "")
                    )
                    stats["academic_templates"] += 1
                except Exception as e:
                    logger.error(f"导入学术语料失败: {e}")

        return stats


user_data_manager = UserDataManager()
