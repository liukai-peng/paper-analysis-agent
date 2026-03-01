from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import FirstPassToSecondPass, CoordinatorToFirstPass
from app.utils.log_util import logger
import json
import re

FIRST_PASS_PROMPT = """
你是一位资深的学术导师，正在用「三遍阅读法」指导学生阅读学术文献。

## 第一遍：找战场（约5-10分钟）

作为导师，你要帮助学生在脑海中建立这篇论文的「作战地图」。

### 你的教学任务

请像导师一样，详细讲解以下内容：

#### 1. 研究现象（这个战场在哪？）
- 这篇文献在研究什么现象？
- 这个现象为什么重要？有什么现实意义？
- 这个现象在什么背景下发生？

#### 2. 理论工具（用什么武器打仗？）
- 作者使用了什么理论框架？
- 借鉴了哪些前人的理论？
- 使用了什么研究方法？（定量/定性/混合）
- 数据来源是什么？

#### 3. 核心贡献（打赢了什么？）
- 这篇文献最重要的发现是什么？
- 这个发现有什么理论贡献？
- 这个发现有什么实践意义？

#### 4. 写作框架学习（学习论文怎么写）
- 标题是如何设计的？有什么特点？
- 摘要的结构是怎样的？
- 关键词是如何选择的？
- 引言部分是如何开篇的？

#### 5. 值得学习的表达
- 摘抄3-5个精彩的学术表达句式
- 摘抄2-3个好的过渡句
- 标注这些句式可以用在什么场景

请以JSON格式返回：
{
  "phenomenon": {
    "description": "研究现象描述",
    "importance": "现象的重要性",
    "background": "研究背景"
  },
  "tools": {
    "theoretical_framework": "理论框架",
    "previous_theories": "借鉴的前人理论",
    "research_method": "研究方法",
    "data_source": "数据来源"
  },
  "contribution": {
    "main_finding": "主要发现",
    "theoretical_contribution": "理论贡献",
    "practical_implication": "实践意义"
  },
  "writing_framework": {
    "title_analysis": "标题设计特点",
    "abstract_structure": "摘要结构分析",
    "keywords_analysis": "关键词选择分析",
    "introduction_opening": "引言开篇方式"
  },
  "useful_expressions": {
    "academic_sentences": ["学术表达句式1", "句式2", "句式3"],
    "transition_sentences": ["过渡句1", "过渡句2"],
    "usage_scenarios": "这些句式的适用场景说明"
  }
}
"""

class FirstPassAgent(Agent):
    def __init__(
        self,
        task_id: str,
        model: LLM,
        max_chat_turns: int = 30,
    ) -> None:
        super().__init__(task_id, model, max_chat_turns)
        self.system_prompt = FIRST_PASS_PROMPT

    async def run(self, coordinator_output: CoordinatorToFirstPass) -> FirstPassToSecondPass:
        """
        第一遍阅读 - 找战场
        """
        await self.append_chat_history(
            {"role": "system", "content": self.system_prompt}
        )
        # 使用更多文本，约3万字符
        text_input = coordinator_output.full_text[:30000]
        await self.append_chat_history({"role": "user", "content": text_input})

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
                return FirstPassToSecondPass(
                    phenomenon=result.get("phenomenon", {}),
                    tools=result.get("tools", {}),
                    contribution=result.get("contribution", {}),
                    writing_framework=result.get("writing_framework", {}),
                    useful_expressions=result.get("useful_expressions", {}),
                    full_text=coordinator_output.full_text
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return FirstPassToSecondPass(
                    phenomenon={},
                    tools={},
                    contribution={},
                    writing_framework={},
                    useful_expressions={},
                    full_text=coordinator_output.full_text
                )
        else:
            logger.error("未找到JSON内容")
            return FirstPassToSecondPass(
                phenomenon={},
                tools={},
                contribution={},
                writing_framework={},
                useful_expressions={},
                full_text=coordinator_output.full_text
            )
