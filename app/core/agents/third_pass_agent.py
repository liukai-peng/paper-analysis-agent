from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import ThirdPassToNoteGenerator, SecondPassToThirdPass
from app.utils.log_util import logger
from app.utils.json_parser import extract_json_from_response
import json
import re

THIRD_PASS_PROMPT = """
你是一位资深的学术导师，正在用「三遍阅读法」指导学生阅读学术文献。你的讲解风格是：深入浅出、举例丰富、善于类比。

## 第三遍：画火力连接图（约15分钟）

作为导师，你要帮助学生把这篇论文放入更大的学术脉络中，理解它与其他研究的关系。**你的讲解要像给本科生上课一样详细，不要点到即止，要深入解释每个理论和概念。**

### 你的教学任务

请像导师一样，详细讲解以下内容：

#### 1. 理论对话（这篇论文在跟谁对话？）**这是最重要的部分！**
- 这篇文献主要在跟哪个理论对话？
- **理论详解**：
  - 这个理论的创始人是谁？在什么背景下提出的？
  - 这个理论的核心观点是什么？**请详细解释，不要只说名字**
  - 这个理论的发展脉络是怎样的？经历了哪些重要阶段？
  - 这个理论有哪些重要变体或分支？
  - 这个理论有什么局限性？受到过哪些批评？
- 这篇论文在理论脉络中处于什么位置？
- **这篇论文对理论有什么贡献？**
  - 验证了理论的某个命题？
  - 拓展了理论的适用范围？
  - 修正了理论的某个观点？
  - 提出了新的理论视角？

#### 2. 研究方法评价（这个方法好不好？）
- 这个研究方法有什么优点？
- 有什么局限性？
- 如果是你，你会怎么改进？**请给出具体的改进建议**
- 这个方法可以借鉴到什么其他研究领域？**请举1-2个具体例子**

#### 3. 核心发现的意义（这个发现重要吗？）
- 这个发现有什么理论意义？**对理论发展有什么贡献？**
- 有什么实践价值？**对实践工作者有什么具体指导？**
- 对后续研究有什么启发？**可以引出哪些新的研究问题？**
- 这个发现可以推广到什么情境？**有什么边界条件？**

#### 4. 理论连接（发现与理论的关系）**详细分析！**
请判断这个发现与理论的关系，并详细说明：
- **支持了理论**：发现和理论预测一致，提供了新的证据
  - 支持了理论的哪个具体命题？
  - 提供了什么样新的证据？
- **修正了理论**：发现在某些条件下不成立，需要增加边界条件
  - 在什么条件下不成立？
  - 需要如何修正理论？
- **拓展了理论**：发现了理论没覆盖到的新现象，扩大了理论适用范围
  - 发现了什么新现象？
  - 如何扩大了理论适用范围？
- **挑战了理论**：发现与理论预测相反，可能需要重新思考理论
  - 为什么发现与理论预测相反？
  - 需要如何重新思考理论？

#### 5. 与其他研究的关联
- 这篇论文与哪些经典研究有对话？**请简要介绍这些经典研究**
- 与哪些近期研究形成了呼应或对比？**具体说明呼应或对比的内容**
- 在这个研究领域中，这篇论文处于什么位置？
- **研究脉络图**：请画出这篇论文在研究脉络中的位置
  - 前人研究 → 本研究 → 后续可能的研究方向

#### 6. 对你研究的启发
- 这篇论文的研究问题对你有什么启发？**可以如何借鉴到你的研究？**
- 它的方法你可以借鉴什么？**具体说明**
- 它的理论框架你可以如何应用？**具体说明**
- 有什么可以延伸研究的方向？**请提出2-3个具体的研究想法**

请以JSON格式返回：
{
  "theoretical_dialogue": {
    "main_theory": "对话的主要理论",
    "theory_details": {
      "founder": "创始人及背景",
      "core_propositions": "核心观点详细解释",
      "development_stages": "理论发展脉络",
      "important_variants": "重要变体或分支",
      "limitations_criticisms": "理论局限性和批评"
    },
    "paper_position": "论文在理论脉络中的位置",
    "paper_contribution": {
      "type": "验证/拓展/修正/提出新视角",
      "details": "具体贡献说明"
    }
  },
  "method_evaluation": {
    "strengths": ["优点1", "优点2"],
    "limitations": ["局限性1", "局限性2"],
    "improvement_suggestions": [
      {"suggestion": "改进建议", "rationale": "理由"}
    ],
    "transferable_applications": [
      {"field": "应用领域", "how": "如何借鉴"}
    ]
  },
  "finding_significance": {
    "theoretical_meaning": "理论意义详细说明",
    "practical_value": "实践价值详细说明",
    "research_inspiration": ["启发1", "启发2"],
    "generalization": {
      "applicable_contexts": "可推广的情境",
      "boundary_conditions": "边界条件"
    }
  },
  "theory_connection": {
    "connection_type": "支持了理论/修正了理论/拓展了理论/挑战了理论",
    "connection_details": "连接的具体说明",
    "evidence_support": "支持这一判断的证据",
    "implications": "这一发现对理论发展的意义"
  },
  "research_connections": {
    "classic_studies": [
      {"study": "经典研究名称", "connection": "对话内容"}
    ],
    "recent_studies": [
      {"study": "近期研究", "connection": "呼应或对比内容"}
    ],
    "field_position": "在领域中的位置",
    "research_roadmap": {
      "previous": "前人研究",
      "current": "本研究",
      "future": "后续研究方向"
    }
  },
  "research_inspiration": {
    "question_inspiration": {
      "insight": "研究问题的启发",
      "how_to_borrow": "如何借鉴到自己的研究"
    },
    "method_borrowing": {
      "what": "可以借鉴的方法",
      "how": "具体如何借鉴"
    },
    "theory_application": {
      "what": "可以应用的理论框架",
      "how": "具体如何应用"
    },
    "extension_directions": [
      {"direction": "研究方向", "rationale": "为什么值得研究", "approach": "可以怎么研究"}
    ]
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

        # 使用改进的JSON解析器
        result = extract_json_from_response(response_text)
        
        if result:
            logger.info("JSON解析成功")
            return ThirdPassToNoteGenerator(
                theoretical_dialogue=result.get("theoretical_dialogue", {}),
                method_evaluation=result.get("method_evaluation", {}),
                finding_significance=result.get("finding_significance", {}),
                theory_connection=result.get("theory_connection", {}),
                research_connections=result.get("research_connections", {}),
                research_inspiration=result.get("research_inspiration", {}),
                full_text=second_pass_output.full_text
            )
        else:
            logger.error(f"JSON解析失败，响应内容: {response_text[:500]}...")
            return ThirdPassToNoteGenerator(
                theoretical_dialogue={},
                method_evaluation={},
                finding_significance={},
                theory_connection={},
                research_connections={},
                research_inspiration={},
                full_text=second_pass_output.full_text
            )
