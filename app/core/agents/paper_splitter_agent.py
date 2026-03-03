from app.core.agents.agent import Agent
from app.schemas.A2A import PaperSplitOutput
from app.utils.log_util import logger
from typing import List
import json
import re

# 论文切分Agent的系统提示词
PAPER_SPLITTER_PROMPT = """
你是一名专业的学术论文结构分析师，擅长识别和切分各类学术论文的结构。

你的任务是：
1. 分析输入的论文文本，识别其整体结构
2. 提取论文的基本信息（标题、作者、摘要）
3. 识别并切分各个章节，包括但不限于：
   - 引言/Introduction
   - 文献综述/Literature Review
   - 研究方法/Methodology
   - 实验/Results
   - 讨论/Discussion
   - 结论/Conclusion
   - 参考文献/References
4. 为每个章节提取关键点和重要性评估
5. 不要压缩内容，保持原文的完整性

请以JSON格式输出结果，包含以下字段：
{
  "title": "论文标题",
  "authors": "作者列表",
  "abstract": "摘要内容",
  "sections": [
    {
      "name": "章节名称",
      "content": "章节内容摘要",
      "key_points": ["关键点1", "关键点2"],
      "importance": "高/中/低"
    }
  ]
}

请确保：
- 准确识别论文结构
- 保留原文的核心内容
- 评估每个章节的重要性
- 输出格式严格为JSON
"""


class PaperSplitterAgent(Agent):
    """论文切分Agent - 负责识别论文结构并切分章节"""

    def __init__(
        self,
        task_id: str,
        model,
        max_chat_turns: int = 30,
    ) -> None:
        super().__init__(task_id, model, max_chat_turns)
        self.system_prompt = PAPER_SPLITTER_PROMPT

    def _remove_references(self, text: str) -> str:
        """
        去除参考文献及其后面的内容
        
        Args:
            text: 原始论文文本
            
        Returns:
            str: 去除参考文献后的文本
        """
        # 常见的参考文献标题模式（不区分大小写）
        reference_patterns = [
            r'\n\s*References\s*\n',
            r'\n\s*REFERENCES\s*\n',
            r'\n\s*参考文献\s*\n',
            r'\n\s*Bibliography\s*\n',
            r'\n\s*BIBLIOGRAPHY\s*\n',
            r'\n\s*Citations\s*\n',
            r'\n\s*CITATIONS\s*\n',
            r'\n\s*Reference\s*\n',
            r'\n\s*REFERENCE\s*\n',
        ]
        
        # 查找第一个匹配的参考文献位置
        for pattern in reference_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 找到参考文献的位置，返回前面的内容
                result = text[:match.start()]
                logger.info(f"检测到参考文献，已去除。原始长度: {len(text)}，处理后长度: {len(result)}")
                return result
        
        # 如果没有找到参考文献，返回原文
        return text

    def _extract_key_sections(self, text: str) -> str:
        """
        提取关键部分（摘要、引言、结论等）
        
        Args:
            text: 原始文本
            
        Returns:
            str: 关键部分文本
        """
        # 提取摘要
        abstract_patterns = [
            r'\n\s*Abstract\s*\n[\s\S]*?\n\s*',
            r'\n\s*ABSTRACT\s*\n[\s\S]*?\n\s*',
            r'\n\s*摘要\s*\n[\s\S]*?\n\s*',
        ]
        
        key_sections = []
        
        # 提取摘要
        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                key_sections.append("摘要:\n" + match.group(0))
                break
        
        # 提取结论
        conclusion_patterns = [
            r'\n\s*Conclusion\s*\n[\s\S]*?\n\s*',
            r'\n\s*CONCLUSION\s*\n[\s\S]*?\n\s*',
            r'\n\s*结论\s*\n[\s\S]*?\n\s*',
        ]
        
        for pattern in conclusion_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                key_sections.append("结论:\n" + match.group(0))
                break
        
        # 如果没有找到摘要，取前5000字符作为简介
        if not key_sections:
            key_sections.append("简介:\n" + text[:5000])
        
        return "\n\n".join(key_sections)

    def _split_into_chunks(self, text: str, chunk_size: int = 8000) -> List[str]:
        """
        将文本分块
        
        Args:
            text: 原始文本
            chunk_size: 每块大小
            
        Returns:
            List[str]: 分块后的文本列表
        """
        chunks = []
        current_chunk = ""
        
        # 按段落分块
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
                current_chunk += paragraph + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    async def run(self, full_text: str) -> PaperSplitOutput:
        """
        切分论文结构

        Args:
            full_text: 论文全文

        Returns:
            PaperSplitOutput: 切分结果
        """
        logger.info(f"PaperSplitterAgent: 开始切分论文，文本长度: {len(full_text)}")

        # 去除参考文献及其后面的内容
        full_text = self._remove_references(full_text)

        # ========== 第一层：文档摘要 ==========
        logger.info("PaperSplitterAgent: 第一层 - 提取关键部分")
        key_sections = self._extract_key_sections(full_text)
        logger.info(f"关键部分长度: {len(key_sections)} 字符")

        await self.append_chat_history(
            {"role": "system", "content": self.system_prompt}
        )

        # 发送关键部分进行分析
        await self.append_chat_history(
            {"role": "user", "content": f"请分析以下论文关键部分并切分结构：\n\n{key_sections}"}
        )

        response = await self.model.chat(
            history=self.chat_history,
            agent_name=self.__class__.__name__,
        )
        response_text = response.choices[0].message.content

        # 解析JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                result = json.loads(json_str)

                # 构建章节列表
                sections = []
                for sec in result.get("sections", []):
                    section = PaperSection(
                        name=sec.get("name", "未知章节"),
                        content=sec.get("content", ""),
                        key_points=sec.get("key_points", []),
                        importance=sec.get("importance", "中")
                    )
                    sections.append(section)

                output = PaperSplitOutput(
                    title=result.get("title", "未知标题"),
                    authors=result.get("authors", []),
                    abstract=result.get("abstract", ""),
                    sections=sections,
                    total_chars=len(full_text),
                    full_text=full_text
                )

                logger.info(f"PaperSplitterAgent: 切分完成，共 {len(sections)} 个章节")
                return output

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                # 返回默认结构
                return self._create_default_output(full_text)
        else:
            logger.error("未找到JSON内容")
            return self._create_default_output(full_text)

    def _create_default_output(self, full_text: str) -> PaperSplitOutput:
        """创建默认输出结构"""
        return PaperSplitOutput(
            title="未知标题",
            authors="",
            abstract="",
            sections=[
                PaperSection(
                    name="全文",
                    content="论文内容",
                    key_points=[],
                    importance="高"
                )
            ],
            total_chars=len(full_text),
            full_text=full_text
        )


# 导入需要的模型
from app.schemas.A2A import PaperSection
