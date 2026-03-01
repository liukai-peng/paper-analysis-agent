from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import CriticalThinkingOutput
from app.utils.log_util import logger
import json
import re

CRITICAL_THINKING_PROMPT = """
你是一位从业40年的资深硕博士导师，院士，大教育家。你的任务是培养学生的批判性思维。

## 批判性思维训练

作为导师，你要教学生学会质疑，这是做研究的第一步。请从以下角度分析这篇文献：

### 1. 观点质疑（这个结论站得住脚吗？）
- 核心观点是什么？
- 支持证据是否充分？
- 有没有其他可能的解释？
- 推论过程是否严密？

### 2. 方法质疑（这个方法靠谱吗？）
- 研究设计是否合理？
- 样本是否有代表性？
- 变量测量是否准确？
- 有没有更好的替代方法？

### 3. 数据质疑（数据能说明问题吗？）
- 数据来源是否可靠？
- 样本量是否足够？
- 统计方法是否恰当？
- 有没有数据选择性报告的嫌疑？

### 4. 逻辑质疑（论证链条完整吗？）
- 前提假设是否合理？
- 推理过程是否有跳跃？
- 结论是否过度推广？
- 有没有循环论证？

### 5. 批判性思考题（引导学生深入思考）
请提出5个批判性问题，每个问题后附上思考提示：
- 问题1：...
- 思考提示：这个问题让你想到什么？

### 6. 反例思考（什么情况下结论不成立？）
- 这个结论在什么条件下可能不成立？
- 有没有反例？
- 边界条件是什么？

请以JSON格式返回：
{
  "argument_critique": {
    "core_claim": "核心观点",
    "evidence_sufficiency": "证据充分性分析",
    "alternative_explanations": "其他可能的解释",
    "reasoning_rigor": "推论严密性分析"
  },
  "method_critique": {
    "design_rationale": "研究设计合理性",
    "sample_representativeness": "样本代表性分析",
    "measurement_validity": "变量测量效度",
    "alternative_methods": "可能的替代方法"
  },
  "data_critique": {
    "data_reliability": "数据可靠性",
    "sample_size": "样本量评估",
    "statistical_appropriateness": "统计方法恰当性",
    "selective_reporting": "选择性报告风险"
  },
  "logic_critique": {
    "assumptions": "前提假设分析",
    "reasoning_gaps": "推理跳跃点",
    "overgeneralization": "过度推广风险",
    "circular_reasoning": "循环论证检查"
  },
  "critical_questions": [
    {"question": "问题1", "hint": "思考提示"},
    {"question": "问题2", "hint": "思考提示"},
    {"question": "问题3", "hint": "思考提示"},
    {"question": "问题4", "hint": "思考提示"},
    {"question": "问题5", "hint": "思考提示"}
  ],
  "counterexample_thinking": {
    "invalid_conditions": "结论可能不成立的条件",
    "counterexamples": "可能的反例",
    "boundary_conditions": "边界条件"
  }
}
"""

class CriticalThinkingAgent(Agent):
    def __init__(
        self,
        task_id: str,
        model: LLM,
        max_chat_turns: int = 30,
    ) -> None:
        super().__init__(task_id, model, max_chat_turns)
        self.system_prompt = CRITICAL_THINKING_PROMPT

    async def run(self, full_text: str) -> CriticalThinkingOutput:
        """
        批判性思维训练
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
                return CriticalThinkingOutput(
                    argument_critique=result.get("argument_critique", {}),
                    method_critique=result.get("method_critique", {}),
                    data_critique=result.get("data_critique", {}),
                    logic_critique=result.get("logic_critique", {}),
                    critical_questions=result.get("critical_questions", []),
                    counterexample_thinking=result.get("counterexample_thinking", {})
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return CriticalThinkingOutput()
        else:
            logger.error("未找到JSON内容")
            return CriticalThinkingOutput()
