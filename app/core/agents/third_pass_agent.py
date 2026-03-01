from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import ThirdPassToNoteGenerator, SecondPassToThirdPass
from app.utils.log_util import logger
import json
import re

THIRD_PASS_PROMPT = """
你是一位资深的学术导师，正在用「三遍阅读法」指导学生阅读学术文献。

## 第三遍：画火力连接图（约15分钟）

作为导师，你要帮助学生把这篇论文放入更大的学术脉络中，理解它与其他研究的关系。

### 你的教学任务

请像导师一样，详细讲解以下内容：

#### 1. 理论对话（这篇论文在跟谁对话？）
- 这篇文献主要在跟哪个理论对话？
- 这个理论的核心观点是什么？
- 这个理论的发展脉络是怎样的？
- 这篇论文在理论脉络中处于什么位置？

#### 2. 研究方法评价（这个方法好不好？）
- 这个研究方法有什么优点？
- 有什么局限性？
- 如果是你，你会怎么改进？
- 这个方法可以借鉴到什么其他研究领域？

#### 3. 核心发现的意义（这个发现重要吗？）
- 这个发现有什么理论意义？
- 有什么实践价值？
- 对后续研究有什么启发？
- 这个发现可以推广到什么情境？

#### 4. 理论连接（发现与理论的关系）
请判断这个发现与理论的关系，并详细说明：
- **支持了理论**：发现和理论预测一致，提供了新的证据
- **修正了理论**：发现在某些条件下不成立，需要增加边界条件
- **拓展了理论**：发现了理论没覆盖到的新现象，扩大了理论适用范围
- **挑战了理论**：发现与理论预测相反，可能需要重新思考理论

#### 5. 与其他研究的关联
- 这篇论文与哪些经典研究有对话？
- 与哪些近期研究形成了呼应或对比？
- 在这个研究领域中，这篇论文处于什么位置？

#### 6. 对你研究的启发
- 这篇论文的研究问题对你有什么启发？
- 它的方法你可以借鉴什么？
- 它的理论框架你可以如何应用？
- 有什么可以延伸研究的方向？

请以JSON格式返回：
{
  "theoretical_dialogue": {
    "main_theory": "对话的主要理论",
    "theory_core": "理论核心观点",
    "theory_development": "理论发展脉络",
    "paper_position": "论文在理论脉络中的位置"
  },
  "method_evaluation": {
    "strengths": "方法优点",
    "limitations": "方法局限性",
    "improvement_suggestions": "改进建议",
    "transferable_applications": "可借鉴的应用领域"
  },
  "finding_significance": {
    "theoretical_meaning": "理论意义",
    "practical_value": "实践价值",
    "research_inspiration": "对后续研究的启发",
    "generalization": "可推广情境"
  },
  "theory_connection": {
    "connection_type": "支持了理论/修正了理论/拓展了理论/挑战了理论",
    "connection_details": "连接的具体说明",
    "evidence_support": "支持这一判断的证据"
  },
  "research_connections": {
    "classic_studies": "对话的经典研究",
    "recent_studies": "呼应或对比的近期研究",
    "field_position": "在领域中的位置"
  },
  "research_inspiration": {
    "question_inspiration": "研究问题的启发",
    "method_borrowing": "方法借鉴",
    "theory_application": "理论框架应用",
    "extension_directions": "可延伸的研究方向"
  }
}
"""

class ThirdPassAgent(Agent):
    def __init__(
        self,
        task_id: str,
        model: LLM,
        max_chat_turns: int = 30,
    ) -> None:
        super().__init__(task_id, model, max_chat_turns)
        self.system_prompt = THIRD_PASS_PROMPT

    async def run(self, second_pass_output: SecondPassToThirdPass) -> ThirdPassToNoteGenerator:
        """
        第三遍阅读 - 画连接
        """
        await self.append_chat_history(
            {"role": "system", "content": self.system_prompt}
        )
        # 使用更多文本，约4万字符
        text_input = second_pass_output.full_text[:40000]
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
                return ThirdPassToNoteGenerator(
                    theoretical_dialogue=result.get("theoretical_dialogue", {}),
                    method_evaluation=result.get("method_evaluation", {}),
                    finding_significance=result.get("finding_significance", {}),
                    theory_connection=result.get("theory_connection", {}),
                    research_connections=result.get("research_connections", {}),
                    research_inspiration=result.get("research_inspiration", {}),
                    full_text=second_pass_output.full_text
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return ThirdPassToNoteGenerator(
                    theoretical_dialogue={},
                    method_evaluation={},
                    finding_significance={},
                    theory_connection={},
                    research_connections={},
                    research_inspiration={},
                    full_text=second_pass_output.full_text
                )
        else:
            logger.error("未找到JSON内容")
            return ThirdPassToNoteGenerator(
                theoretical_dialogue={},
                method_evaluation={},
                finding_significance={},
                theory_connection={},
                research_connections={},
                research_inspiration={},
                full_text=second_pass_output.full_text
            )
