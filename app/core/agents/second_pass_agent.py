from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import SecondPassToThirdPass, FirstPassToSecondPass
from app.utils.log_util import logger
import json
import re

SECOND_PASS_PROMPT = """
你是一位资深的学术导师，正在用「三遍阅读法」指导学生阅读学术文献。

## 第二遍：拆作战地图（约30分钟）

作为导师，你要像拆解一台精密仪器一样，帮学生理解这篇论文的每一个部件是如何运作的。

### 你的教学任务

请像导师一样，详细讲解以下内容：

#### 1. 研究问题的提出（Introduction分析）
- 作者在Introduction最后一段是如何提出研究问题的？
- 请【原文摘录】这段话
- 分析这段话的写作技巧：作者是如何从背景过渡到问题的？
- 这种提出问题的方式有什么值得学习的地方？

#### 2. 文献综述的结构（Literature Review分析）
- 作者回顾了哪些方面的文献？
- 文献综述是如何组织的？（按时间/按主题/按方法）
- 作者在Literature Review结尾是如何总结前人研究不足的？
- 请【原文摘录】总结前人不足的段落
- 分析：作者是如何"找缺口"的？用了什么表达方式？

#### 3. 研究设计与方法（Method分析）
- 研究设计是什么？（实验/调查/案例/文本分析等）
- 变量是如何定义和测量的？
- 样本是如何选取的？
- 数据分析用了什么方法？
- 方法部分的写作有什么特点？用了什么句式？

#### 4. 核心发现（Results/Discussion分析）
- 主要发现了什么？
- 请【原文摘录】Discussion第一段的核心发现总结
- 作者如何解释这些发现？
- 发现与假设是否一致？

#### 5. 局限与展望（Conclusion分析）
- 作者承认了哪些局限性？
- 提出了哪些未来研究方向？
- 请【原文摘录】关于局限性和展望的段落
- 分析：作者是如何"谦虚地"承认不足的？

#### 6. 论文写作技巧总结
- 这篇论文的段落结构有什么特点？
- 作者如何在不同部分之间过渡？
- 摘抄5个值得学习的学术表达
- 这些表达可以用在论文的哪些部分？

请以JSON格式返回：
{
  "research_question": {
    "original_text": "Introduction最后一段原文摘录",
    "writing_technique": "写作技巧分析",
    "learning_points": "值得学习的地方"
  },
  "literature_review": {
    "coverage": "文献回顾范围",
    "organization": "组织方式",
    "gap_identification": "原文摘录-前人不足总结",
    "gap_technique": "找缺口的表达方式分析"
  },
  "methodology": {
    "research_design": "研究设计",
    "variables": "变量定义与测量",
    "sampling": "样本选取",
    "data_analysis": "数据分析方法",
    "writing_features": "方法部分写作特点"
  },
  "findings": {
    "main_results": "主要发现",
    "original_text": "Discussion第一段原文摘录",
    "interpretation": "发现解释",
    "hypothesis_test": "假设检验结果"
  },
  "limitations": {
    "acknowledged_limitations": "承认的局限性",
    "future_directions": "未来研究方向",
    "original_text": "原文摘录-局限与展望",
    "humble_expression": "谦虚承认不足的表达方式"
  },
  "writing_techniques": {
    "paragraph_structure": "段落结构特点",
    "transition_methods": "过渡方式",
    "useful_expressions": ["表达1", "表达2", "表达3", "表达4", "表达5"],
    "expression_usage": "这些表达可以用在哪些部分"
  }
}
"""

class SecondPassAgent(Agent):
    def __init__(
        self,
        task_id: str,
        model: LLM,
        max_chat_turns: int = 30,
    ) -> None:
        super().__init__(task_id, model, max_chat_turns)
        self.system_prompt = SECOND_PASS_PROMPT

    async def run(self, first_pass_output: FirstPassToSecondPass) -> SecondPassToThirdPass:
        """
        第二遍阅读 - 拆地图
        """
        await self.append_chat_history(
            {"role": "system", "content": self.system_prompt}
        )
        # 使用更多文本，约4万字符
        text_input = first_pass_output.full_text[:40000]
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
                return SecondPassToThirdPass(
                    research_question=result.get("research_question", {}),
                    literature_review=result.get("literature_review", {}),
                    methodology=result.get("methodology", {}),
                    findings=result.get("findings", {}),
                    limitations=result.get("limitations", {}),
                    writing_techniques=result.get("writing_techniques", {}),
                    full_text=first_pass_output.full_text
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return SecondPassToThirdPass(
                    research_question={},
                    literature_review={},
                    methodology={},
                    findings={},
                    limitations={},
                    writing_techniques={},
                    full_text=first_pass_output.full_text
                )
        else:
            logger.error("未找到JSON内容")
            return SecondPassToThirdPass(
                research_question={},
                literature_review={},
                methodology={},
                findings={},
                limitations={},
                writing_techniques={},
                full_text=first_pass_output.full_text
            )
