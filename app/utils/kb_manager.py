import json
import os
from datetime import datetime
from typing import Dict, Any, List
from app.utils.log_util import logger

class KnowledgeBaseManager:
    """知识库管理器，负责导入导出知识库数据"""
    
    def __init__(self, literature_notes_file: str = "literature_notes.json", 
                 academic_corpus_file: str = "academic_corpus.json"):
        self.literature_notes_file = literature_notes_file
        self.academic_corpus_file = academic_corpus_file
    
    def export_knowledge_base(self, export_dir: str = "exports", filename: str = None) -> str:
        """
        导出整个知识库
        
        Args:
            export_dir: 导出目录
            filename: 文件名（可选）
        
        Returns:
            导出文件路径
        """
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"knowledge_base_{timestamp}.json"
            
            filepath = os.path.join(export_dir, filename)
            
            # 读取文献笔记
            literature_notes = []
            if os.path.exists(self.literature_notes_file):
                with open(self.literature_notes_file, "r", encoding="utf-8") as f:
                    literature_notes = json.load(f)
            
            # 读取学术语料库
            academic_corpus = {}
            if os.path.exists(self.academic_corpus_file):
                with open(self.academic_corpus_file, "r", encoding="utf-8") as f:
                    academic_corpus = json.load(f)
            
            # 构建导出数据
            export_data = {
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0",
                "literature_notes": literature_notes,
                "academic_corpus": academic_corpus
            }
            
            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功导出知识库: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"导出知识库失败: {e}")
            raise
    
    def import_knowledge_base(self, import_file: str, merge: bool = False) -> Dict[str, int]:
        """
        导入知识库
        
        Args:
            import_file: 导入文件路径
            merge: 是否合并（True）或覆盖（False）
        
        Returns:
            导入统计信息
        """
        try:
            # 读取导入文件
            with open(import_file, "r", encoding="utf-8") as f:
                import_data = json.load(f)
            
            # 验证数据格式
            if "literature_notes" not in import_data or "academic_corpus" not in import_data:
                raise ValueError("导入文件格式不正确")
            
            # 读取现有数据
            existing_notes = []
            if os.path.exists(self.literature_notes_file):
                with open(self.literature_notes_file, "r", encoding="utf-8") as f:
                    existing_notes = json.load(f)
            
            existing_corpus = {}
            if os.path.exists(self.academic_corpus_file):
                with open(self.academic_corpus_file, "r", encoding="utf-8") as f:
                    existing_corpus = json.load(f)
            
            # 处理文献笔记
            import_notes = import_data["literature_notes"]
            if merge:
                # 合并模式：添加新的笔记
                existing_ids = {note.get("id") for note in existing_notes}
                new_notes = [note for note in import_notes if note.get("id") not in existing_ids]
                merged_notes = existing_notes + new_notes
                notes_count = len(new_notes)
            else:
                # 覆盖模式：完全替换
                merged_notes = import_notes
                notes_count = len(import_notes)
            
            # 处理学术语料库
            import_corpus = import_data["academic_corpus"]
            if merge:
                # 合并模式：合并模板
                merged_corpus = {}
                for category in set(list(existing_corpus.keys()) + list(import_corpus.keys())):
                    existing_templates = existing_corpus.get(category, [])
                    import_templates = import_corpus.get(category, [])
                    merged_corpus[category] = existing_templates + import_templates
                corpus_count = sum(len(templates) for templates in import_corpus.values())
            else:
                # 覆盖模式：完全替换
                merged_corpus = import_corpus
                corpus_count = sum(len(templates) for templates in import_corpus.values())
            
            # 保存数据
            with open(self.literature_notes_file, "w", encoding="utf-8") as f:
                json.dump(merged_notes, f, ensure_ascii=False, indent=2)
            
            with open(self.academic_corpus_file, "w", encoding="utf-8") as f:
                json.dump(merged_corpus, f, ensure_ascii=False, indent=2)
            
            # 返回统计信息
            stats = {
                "literature_notes": notes_count,
                "academic_templates": corpus_count,
                "total_items": notes_count + corpus_count
            }
            
            logger.info(f"成功导入知识库: {stats}")
            return stats
        except Exception as e:
            logger.error(f"导入知识库失败: {e}")
            raise
    
    def export_literature_notes(self, export_dir: str = "exports", filename: str = None) -> str:
        """
        仅导出文献笔记
        
        Args:
            export_dir: 导出目录
            filename: 文件名（可选）
        
        Returns:
            导出文件路径
        """
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"literature_notes_{timestamp}.json"
            
            filepath = os.path.join(export_dir, filename)
            
            if os.path.exists(self.literature_notes_file):
                with open(self.literature_notes_file, "r", encoding="utf-8") as f:
                    notes = json.load(f)
                
                export_data = {
                    "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "version": "1.0",
                    "notes": notes
                }
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"成功导出文献笔记: {filepath}")
                return filepath
            else:
                raise FileNotFoundError("文献笔记文件不存在")
        except Exception as e:
            logger.error(f"导出文献笔记失败: {e}")
            raise
    
    def export_academic_corpus(self, export_dir: str = "exports", filename: str = None) -> str:
        """
        仅导出学术语料库
        
        Args:
            export_dir: 导出目录
            filename: 文件名（可选）
        
        Returns:
            导出文件路径
        """
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"academic_corpus_{timestamp}.json"
            
            filepath = os.path.join(export_dir, filename)
            
            if os.path.exists(self.academic_corpus_file):
                with open(self.academic_corpus_file, "r", encoding="utf-8") as f:
                    corpus = json.load(f)
                
                export_data = {
                    "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "version": "1.0",
                    "corpus": corpus
                }
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"成功导出学术语料库: {filepath}")
                return filepath
            else:
                raise FileNotFoundError("学术语料库文件不存在")
        except Exception as e:
            logger.error(f"导出学术语料库失败: {e}")
            raise

# 全局知识库管理器实例
kb_manager = KnowledgeBaseManager()