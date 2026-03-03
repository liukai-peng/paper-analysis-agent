from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import CoordinatorToFirstPass
from app.utils.log_util import logger
import re
import json

COORDINATOR_PROMPT = """
你是一位资深的学术导师，正在指导学生阅读学术文献。

## 你的任务
请仔细阅读这篇文献，识别其类型并提取基本信息。

## 文献类型分类
- 实证研究论文：通过数据收集和分析验证假设
- 综述论文：系统梳理某一领域的研究现状
- 理论论文：提出或发展新的理论框架
- 方法论文：介绍新的研究方法或工具
- 案例研究：深入分析特定案例

## 请回答以下问题

### 1. 文献基本信息
- 标题是什么？
- 作者有哪些？
- 发表年份和期刊？

### 2. 文献类型判断
这篇文献属于哪种类型？请说明判断依据。

### 3. 研究领域
这篇文献属于哪个学科领域？具体研究方向是什么？

### 4. 一句话概括
用一句话概括这篇文献的核心内容。

请以JSON格式返回：
{
  "document_type": "文献类型",
  "title": "文献标题",
  "authors": ["作者1", "作者2", "作者3"],
  "year": "发表年份",
  "journal": "期刊名称",
  "research_field": "研究领域",
  "type_reason": "类型判断依据",
  "one_sentence_summary": "一句话概括"
}
"""

class CoordinatorAgent(Agent):
    def __init__(
        self,
        task_id: str,
        model: LLM,
        max_chat_turns: int = 30,
    ) -> None:
        super().__init__(task_id, model, max_chat_turns)
        self.system_prompt = COORDINATOR_PROMPT

    async def run(self, full_text: str) -> CoordinatorToFirstPass:
        """
        识别文献类型和提取基本信息
        """
        await self.append_chat_history(
            {"role": "system", "content": self.system_prompt}
        )
        # 使用更多文本，约2万字符
        await self.append_chat_history({"role": "user", "content": full_text[:20000]})

        response = await self.model.chat(
            history=self.chat_history,
            agent_name=self.__class__.__name__,
        )
        response_text = response.choices[0].message.content

        json_match = re.search(r'\{[\s\S]*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                result = json.loads(json_str)
                # 处理 authors 字段，确保它是列表
                authors = result.get("authors", [])
                if isinstance(authors, str):
                    # 如果是字符串，按逗号分割
                    authors = [a.strip() for a in authors.split(",") if a.strip()]
                elif not isinstance(authors, list):
                    authors = []
                
                return CoordinatorToFirstPass(
                    document_type=result.get("document_type", "未知"),
                    full_text=full_text,
                    title=result.get("title", "未知"),
                    authors=authors,
                    year=result.get("year", ""),
                    journal=result.get("journal", ""),
                    research_field=result.get("research_field", ""),
                    type_reason=result.get("type_reason", ""),
                    one_sentence_summary=result.get("one_sentence_summary", "")
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return CoordinatorToFirstPass(
                    document_type="未知",
                    full_text=full_text,
                    title="未知"
                )
        else:
            logger.error("未找到JSON内容")
            return CoordinatorToFirstPass(
                document_type="未知",
                full_text=full_text,
                title="未知"
            )
