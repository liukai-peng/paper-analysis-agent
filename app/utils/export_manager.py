import json
import os
from datetime import datetime
from typing import Dict, Any
from app.utils.log_util import logger


class ExportManager:
    """导出管理器，负责将分析结果导出为不同格式"""

    def __init__(self, export_dir: str = None):
        """
        初始化导出管理器

        Args:
            export_dir: 导出目录（可选，默认为项目目录下的 exports）
        """
        if export_dir is None:
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            export_dir = os.path.join(project_root, 'exports')

        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        logger.info(f"导出目录: {self.export_dir}")

    def export_to_json(self, result: Dict[str, Any], filename: str = None) -> str:
        """
        导出为JSON格式

        Args:
            result: 分析结果
            filename: 文件名（可选）

        Returns:
            导出文件路径
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                title = result.get('basic_info', {}).get('title', 'analysis')
                # 清理文件名中的非法字符
                title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"{title}_{timestamp}.json"

            filepath = os.path.join(self.export_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"成功导出JSON文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"导出JSON文件失败: {e}")
            raise

    def export_to_markdown(self, result: Dict[str, Any], filename: str = None) -> str:
        """
        导出为Markdown格式

        Args:
            result: 分析结果
            filename: 文件名（可选）

        Returns:
            导出文件路径
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                title = result.get('basic_info', {}).get('title', 'analysis')
                title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"{title}_{timestamp}.md"

            filepath = os.path.join(self.export_dir, filename)

            markdown_content = self._generate_markdown(result)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            logger.info(f"成功导出Markdown文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"导出Markdown文件失败: {e}")
            raise

    def _generate_markdown(self, result: Dict[str, Any]) -> str:
        """生成Markdown内容"""
        content = []

        basic_info = result.get('basic_info', {})

        # 标题
        content.append(f"# 文献分析报告\n")
        content.append(f"**标题**: {basic_info.get('title', '未知')}\n")
        content.append(f"**作者**: {basic_info.get('authors', '未知')}\n")
        content.append(f"**期刊**: {basic_info.get('journal', '未知')} ({basic_info.get('year', '未知')})\n")
        content.append(f"**文献类型**: {basic_info.get('document_type', '未知')}\n")
        content.append(f"**研究领域**: {basic_info.get('research_field', '未知')}\n")
        content.append(f"**一句话概括**: {basic_info.get('one_sentence_summary', '未知')}\n")
        content.append(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        content.append("---\n")

        # 第一遍：找战场
        content.append("## 第一遍：找战场\n")
        first_pass = result.get('first_pass', {})

        phenomenon = first_pass.get('phenomenon', {})
        content.append(f"### 研究现象\n")
        content.append(f"- **描述**: {phenomenon.get('description', '未提供')}\n")
        content.append(f"- **重要性**: {phenomenon.get('importance', '未提供')}\n")
        content.append(f"- **背景**: {phenomenon.get('background', '未提供')}\n\n")

        tools = first_pass.get('tools', {})
        content.append(f"### 理论工具\n")
        content.append(f"- **理论框架**: {tools.get('theoretical_framework', '未提供')}\n")
        content.append(f"- **研究方法**: {tools.get('research_method', '未提供')}\n")
        content.append(f"- **数据来源**: {tools.get('data_source', '未提供')}\n\n")

        contribution = first_pass.get('contribution', {})
        content.append(f"### 核心贡献\n")
        content.append(f"- **主要发现**: {contribution.get('main_finding', '未提供')}\n")
        content.append(f"- **理论贡献**: {contribution.get('theoretical_contribution', '未提供')}\n")
        content.append(f"- **实践意义**: {contribution.get('practical_significance', '未提供')}\n")
        content.append("---\n")

        # 第二遍：拆地图
        content.append("## 第二遍：拆作战地图\n")
        second_pass = result.get('second_pass', {})

        rq = second_pass.get('research_question', {})
        content.append(f"### 研究问题\n")
        content.append(f"- **问题提出**: {rq.get('question_statement', '未提供')}\n")
        if rq.get('original_text'):
            content.append(f"- **原文摘录**: _{rq.get('original_text')}_\n")
        content.append(f"- **写作技巧**: {rq.get('writing_technique', '未提供')}\n\n")

        lr = second_pass.get('literature_review', {})
        content.append(f"### 文献综述\n")
        content.append(f"- **组织方式**: {lr.get('organization', '未提供')}\n")
        content.append(f"- **核心文献**: {lr.get('core_literature', '未提供')}\n")
        if lr.get('gap_statement'):
            content.append(f"- **研究空白**: _{lr.get('gap_statement')}_\n")
        content.append("\n")

        method = second_pass.get('methodology', {})
        content.append(f"### 研究方法\n")
        content.append(f"- **研究设计**: {method.get('design', '未提供')}\n")
        content.append(f"- **变量测量**: {method.get('variables', '未提供')}\n")
        content.append(f"- **样本**: {method.get('sample', '未提供')}\n")
        content.append(f"- **分析方法**: {method.get('analysis', '未提供')}\n")
        content.append("---\n")

        # 第三遍：画连接
        content.append("## 第三遍：画火力连接图\n")
        third_pass = result.get('third_pass', {})

        td = third_pass.get('theoretical_dialogue', {})
        content.append(f"### 理论对话\n")
        content.append(f"- **对话理论**: {td.get('theory', '未提供')}\n")
        content.append(f"- **理论位置**: {td.get('position', '未提供')}\n\n")

        me = third_pass.get('method_evaluation', {})
        content.append(f"### 方法评价\n")
        content.append(f"- **优点**: {me.get('strengths', '未提供')}\n")
        content.append(f"- **局限**: {me.get('limitations', '未提供')}\n")
        content.append(f"- **改进建议**: {me.get('improvements', '未提供')}\n\n")

        ri = third_pass.get('research_inspiration', {})
        content.append(f"### 研究启发\n")
        content.append(f"- **方法借鉴**: {ri.get('method_inspiration', '未提供')}\n")
        content.append(f"- **理论启发**: {ri.get('theory_inspiration', '未提供')}\n")
        content.append(f"- **可研究方向**: {ri.get('future_directions', '未提供')}\n")
        content.append("---\n")

        # 笔记
        content.append("## 详细笔记\n")
        notes = result.get('notes', {})

        three_notes = notes.get('three_sentence_notes', {})
        content.append(f"### 三句话笔记\n")
        content.append(f"- **这篇在说什么？** {three_notes.get('what', '未提供')}\n")
        content.append(f"- **跟我有什么关系？** {three_notes.get('relation', '未提供')}\n")
        content.append(f"- **让我想反驳什么？** {three_notes.get('challenge', '未提供')}\n\n")

        content.append(f"### 详细摘要\n")
        content.append(f"{notes.get('detailed_summary', '未提供')}\n\n")

        # 写作素材
        content.append(f"### 可借鉴的写作素材\n")
        materials = notes.get('writing_materials', {})
        expressions = materials.get('academic_expressions', [])
        if expressions:
            content.append("**学术表达句式库**:\n")
            for i, expr in enumerate(expressions, 1):
                content.append(f"{i}. **原句**: _{expr.get('original', '')}_\n")
                content.append(f"   - **用法**: {expr.get('usage', '')}\n")
                content.append(f"   - **仿写**: {expr.get('imitation', '')}\n\n")

        # 导师教学模块
        if result.get('enable_teaching') and 'teaching' in result:
            content.append("---\n")
            content.append("## 导师教学模块\n")
            teaching = result.get('teaching', {})

            # 批判性思维
            ct = teaching.get('critical_thinking', {})
            content.append("### 批判性思维训练\n")
            questions = ct.get('critical_questions', [])
            if questions:
                content.append("**批判性思考题**:\n")
                for i, q in enumerate(questions, 1):
                    content.append(f"{i}. {q.get('question', '')}\n")
                    content.append(f"   - 思考提示: {q.get('hint', '')}\n\n")

            # 研究空白
            rg = teaching.get('research_gap', {})
            content.append("### 研究空白发现\n")
            rqs = rg.get('research_questions', [])
            if rqs:
                content.append("**可研究问题推荐**:\n")
                for i, rq in enumerate(rqs, 1):
                    content.append(f"{i}. **{rq.get('question', '')}**\n")
                    content.append(f"   - 研究价值: {rq.get('value', '')} ({rq.get('value_reason', '')})\n")
                    content.append(f"   - 可行性: {rq.get('feasibility', '')} ({rq.get('feasibility_reason', '')})\n\n")

            # 写作框架
            wf = teaching.get('writing_framework', {})
            content.append("### 写作框架教学\n")
            quick_ref = wf.get('quick_reference', {})
            if quick_ref:
                content.append("**快速检查清单**:\n")
                for section, items in quick_ref.items():
                    content.append(f"- **{section}**:\n")
                    for item in items:
                        content.append(f"  - [ ] {item}\n")

        return "\n".join(content)

    def export_to_txt(self, result: Dict[str, Any], filename: str = None) -> str:
        """
        导出为纯文本格式

        Args:
            result: 分析结果
            filename: 文件名（可选）

        Returns:
            导出文件路径
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                title = result.get('basic_info', {}).get('title', 'analysis')
                title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"{title}_{timestamp}.txt"

            filepath = os.path.join(self.export_dir, filename)

            markdown_content = self._generate_markdown(result)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            logger.info(f"成功导出TXT文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"导出TXT文件失败: {e}")
            raise

    def export_all_formats(self, result: Dict[str, Any], base_filename: str = None) -> Dict[str, str]:
        """
        导出所有格式

        Args:
            result: 分析结果
            base_filename: 基础文件名（可选）

        Returns:
            各格式文件路径的字典
        """
        try:
            if base_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                title = result.get('basic_info', {}).get('title', 'analysis')
                title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                base_filename = f"{title}_{timestamp}"

            files = {}
            files['json'] = self.export_to_json(result, f"{base_filename}.json")
            files['markdown'] = self.export_to_markdown(result, f"{base_filename}.md")
            files['txt'] = self.export_to_txt(result, f"{base_filename}.txt")

            logger.info(f"成功导出所有格式: {files}")
            return files
        except Exception as e:
            logger.error(f"导出所有格式失败: {e}")
            raise


# 全局导出管理器实例
export_manager = ExportManager()
