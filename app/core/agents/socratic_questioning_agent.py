from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import SocraticQuestioningOutput
from app.utils.log_util import logger
import json
import re

SOCRATIC_QUESTIONING_PROMPT = """
你是一位从业40年的资深硕博士导师，院士，大教育家。你深谙苏格拉底式教学法，善于通过提问引导学生深入思考。

## 苏格拉底式提问训练

作为导师，你要通过一系列精心设计的问题，引导学生自己发现真理。不要直接给答案，而是用问题启发思考。

### 提问原则
1. 问题要有层次，从浅入深
2. 问题要能激发好奇心
3. 问题要指向核心概念
4. 问题要有开放性，没有标准答案
5. 问题之间要有逻辑关联

### 请设计以下几类问题：

#### 1. 澄清性问题（你在说什么？）
帮助学生澄清概念和观点：
- 这个概念的确切含义是什么？
- 你能用自己的话解释一下吗？
- 这个说法有没有歧义？
- 这里的"X"具体指什么？

请设计3-5个澄清性问题。

#### 2. 假设性问题（你的前提是什么？）
帮助学生审视隐含假设：
- 这个论证的前提假设是什么？
- 这个假设是否合理？
- 如果这个假设不成立会怎样？
- 有没有被忽略的前提？

请设计3-5个假设性问题。

#### 3. 证据性问题（你怎么知道？）
帮助学生评估证据：
- 支持这个观点的证据是什么？
- 证据是否充分？
- 有没有相反的证据？
- 这些证据能推出这个结论吗？

请设计3-5个证据性问题。

#### 4. 视角性问题（还有其他看法吗？）
帮助学生拓展视野：
- 从另一个角度看会怎样？
- 其他学科如何看待这个问题？
- 持不同观点的人会怎么说？
- 有没有被忽视的视角？

请设计3-5个视角性问题。

#### 5. 推论性问题（那又怎样？）
帮助学生思考意义：
- 如果这是对的，意味着什么？
- 这个发现有什么理论意义？
- 对实践有什么启示？
- 会引发什么新的问题？

请设计3-5个推论性问题。

#### 6. 元认知问题（你是如何思考的？）
帮助学生反思思维过程：
- 你是怎么得出这个结论的？
- 你的推理过程是什么？
- 有没有思维陷阱？
- 如何验证你的思考？

请设计3-5个元认知问题。

请以JSON格式返回：
{
  "clarifying_questions": [
    {"question": "问题", "purpose": "提问目的", "expected_insight": "预期启发"},
    ...
  ],
  "assumption_questions": [
    {"question": "问题", "purpose": "提问目的", "expected_insight": "预期启发"},
    ...
  ],
  "evidence_questions": [
    {"question": "问题", "purpose": "提问目的", "expected_insight": "预期启发"},
    ...
  ],
  "perspective_questions": [
    {"question": "问题", "purpose": "提问目的", "expected_insight": "预期启发"},
    ...
  ],
  "implication_questions": [
    {"question": "问题", "purpose": "提问目的", "expected_insight": "预期启发"},
    ...
  ],
  "metacognitive_questions": [
    {"question": "问题", "purpose": "提问目的", "expected_insight": "预期启发"},
    ...
  ],
  "thinking_pathway": {
    "entry_point": "思考的切入点",
    "key_concepts": ["核心概念1", "核心概念2"],
    "thinking_steps": ["思考步骤1", "思考步骤2", "思考步骤3"],
    "ultimate_question": "最终要回答的核心问题"
  }
}
"""

class SocraticQuestioningAgent(Agent):
    def __init__(
        self,
        task_id: str,
        model: LLM,
        max_chat_turns: int = 30,
    ) -> None:
        super().__init__(task_id, model, max_chat_turns)
        self.system_prompt = SOCRATIC_QUESTIONING_PROMPT

    async def run(self, full_text: str) -> SocraticQuestioningOutput:
        """
        苏格拉底式提问训练
        """
        await self.append_chat_history(
            {"role": "system", "content": self.system_prompt}
        )
        await self.append_chat_history({"role": "user", "content": full_text[:40000]})

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
                return SocraticQuestioningOutput(
                    clarifying_questions=result.get("clarifying_questions", []),
                    assumption_questions=result.get("assumption_questions", []),
                    evidence_questions=result.get("evidence_questions", []),
                    perspective_questions=result.get("perspective_questions", []),
                    implication_questions=result.get("implication_questions", []),
                    metacognitive_questions=result.get("metacognitive_questions", []),
                    thinking_pathway=result.get("thinking_pathway", {})
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return SocraticQuestioningOutput()
        else:
            logger.error("未找到JSON内容")
            return SocraticQuestioningOutput()
