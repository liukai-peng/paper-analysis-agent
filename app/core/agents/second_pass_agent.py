from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import SecondPassToThirdPass, FirstPassToSecondPass
from app.utils.log_util import logger
from app.utils.json_parser import extract_json_from_response
import json
import re

SECOND_PASS_PROMPT = """
你是一位资深的学术导师，正在用「三遍阅读法」指导学生阅读学术文献。你的讲解风格是：深入浅出、举例丰富、善于类比。

## 第二遍：拆作战地图（约30分钟）

作为导师，你要像拆解一台精密仪器一样，帮学生理解这篇论文的每一个部件是如何运作的。**你的讲解要像给本科生上课一样详细，不要点到即止，要深入解释每个概念和方法。**

### 你的教学任务

请像导师一样，详细讲解以下内容：

#### 1. 研究问题的提出（Introduction分析）
- 作者在Introduction最后一段是如何提出研究问题的？
- 请【原文摘录】这段话
- 分析这段话的写作技巧：作者是如何从背景过渡到问题的？
- 这种提出问题的方式有什么值得学习的地方？
- **研究问题的层次分析**：
  - 核心研究问题是什么？
  - 这个问题下面有哪些子问题？
  - 这些问题之间的逻辑关系是什么？

#### 2. 文献综述的结构（Literature Review分析）
- 作者回顾了哪些方面的文献？
- 文献综述是如何组织的？（按时间/按主题/按方法）
- 作者在Literature Review结尾是如何总结前人研究不足的？
- 请【原文摘录】总结前人不足的段落
- 分析：作者是如何"找缺口"的？用了什么表达方式？
- **文献综述写作技巧**：
  - 作者如何引出每个文献主题？
  - 作者如何评价前人研究？（正面评价 vs 批评性评价）
  - 作者如何从文献综述过渡到自己的研究？

#### 3. 研究设计与方法（Method分析）**这是新手最需要详细讲解的部分！**
- **研究设计是什么？**（实验/调查/案例/文本分析等）
  - 为什么选择这种设计？
  - 这种设计的优势和劣势是什么？
  
- **变量是如何定义和测量的？**
  - 自变量是什么？如何操作化？
  - 因变量是什么？如何测量？
  - 控制变量有哪些？为什么要控制？
  - **请详细解释每个变量的测量方式，不要只说名字**
  
- **样本是如何选取的？**
  - 样本量是多少？
  - 抽样方法是什么？
  - 样本的代表性如何？
  
- **数据分析用了什么方法？**
  - 描述性统计用了什么？
  - 推断性统计用了什么？
  - **请解释这些统计方法的原理，不要只说名字**
  
- **方法部分的写作有什么特点？**
  - 用了什么句式？
  - 如何描述研究过程？

#### 4. 核心发现（Results/Discussion分析）
- 主要发现了什么？**请详细描述每个发现**
- 请【原文摘录】Discussion第一段的核心发现总结
- 作者如何解释这些发现？**解释的逻辑是什么？**
- 发现与假设是否一致？**如果不一致，作者如何解释？**
- **结果呈现方式分析**：
  - 作者用了什么图表？
  - 图表的设计有什么值得学习的地方？

#### 5. 局限与展望（Conclusion分析）
- 作者承认了哪些局限性？
- 提出了哪些未来研究方向？
- 请【原文摘录】关于局限性和展望的段落
- 分析：作者是如何"谦虚地"承认不足的？
- **局限性写作技巧**：
  - 作者如何承认不足但不贬低自己研究的价值？
  - 用了什么表达方式？

#### 6. 论文写作技巧总结
- 这篇论文的段落结构有什么特点？
- 作者如何在不同部分之间过渡？
- 摘抄8-10个值得学习的学术表达（比之前更多）
- 这些表达可以用在论文的哪些部分？
- **请解释每个表达好在哪里**

请以JSON格式返回：
{
  "research_question": {
    "original_text": "Introduction最后一段原文摘录",
    "writing_technique": "写作技巧分析",
    "learning_points": "值得学习的地方",
    "core_question": "核心研究问题",
    "sub_questions": ["子问题1", "子问题2"],
    "question_logic": "问题之间的逻辑关系"
  },
  "literature_review": {
    "coverage": "文献回顾范围",
    "organization": "组织方式",
    "gap_identification": "原文摘录-前人不足总结",
    "gap_technique": "找缺口的表达方式分析",
    "topic_introduction": "如何引出每个文献主题",
    "evaluation_style": "如何评价前人研究",
    "transition_technique": "从文献综述过渡到自己研究的方式"
  },
  "methodology": {
    "research_design": {
      "type": "研究设计类型",
      "why_chosen": "为什么选择这种设计",
      "strengths": "这种设计的优势",
      "weaknesses": "这种设计的劣势"
    },
    "variables": {
      "independent": {
        "name": "自变量名称",
        "operationalization": "如何操作化",
        "measurement": "如何测量",
        "explanation": "详细解释"
      },
      "dependent": {
        "name": "因变量名称",
        "measurement": "如何测量",
        "explanation": "详细解释"
      },
      "control": [
        {"name": "控制变量名", "why_control": "为什么要控制"}
      ]
    },
    "sampling": {
      "sample_size": "样本量",
      "sampling_method": "抽样方法",
      "representativeness": "样本代表性分析"
    },
    "data_analysis": {
      "descriptive": "描述性统计方法及原理",
      "inferential": "推断性统计方法及原理解释",
      "software": "使用的统计软件"
    },
    "writing_features": {
      "sentence_patterns": ["句式1", "句式2"],
      "process_description": "如何描述研究过程"
    }
  },
  "findings": {
    "main_results": [
      {"finding": "发现1", "detail": "详细描述", "interpretation": "作者解释"}
    ],
    "original_text": "Discussion第一段原文摘录",
    "hypothesis_test": "假设检验结果",
    "inconsistency_explanation": "如果不一致，作者如何解释",
    "presentation_style": {
      "figures_tables": "用了什么图表",
      "design_learning": "图表设计值得学习的地方"
    }
  },
  "limitations": {
    "acknowledged_limitations": ["局限性1", "局限性2"],
    "future_directions": ["未来方向1", "未来方向2"],
    "original_text": "原文摘录-局限与展望",
    "humble_expression": "谦虚承认不足的表达方式",
    "writing_technique": "如何承认不足但不贬低价值"
  },
  "writing_techniques": {
    "paragraph_structure": "段落结构特点",
    "transition_methods": ["过渡方式1", "过渡方式2"],
    "useful_expressions": [
      {"expression": "表达1", "why_good": "好在哪里", "usage": "用在什么场景"},
      {"expression": "表达2", "why_good": "好在哪里", "usage": "用在什么场景"}
    ]
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

        # 使用改进的JSON解析器
        result = extract_json_from_response(response_text)
        
        if result:
            logger.info("JSON解析成功")
            return SecondPassToThirdPass(
                research_question=result.get("research_question", {}),
                literature_review=result.get("literature_review", {}),
                methodology=result.get("methodology", {}),
                findings=result.get("findings", {}),
                limitations=result.get("limitations", {}),
                writing_techniques=result.get("writing_techniques", {}),
                full_text=first_pass_output.full_text
            )
        else:
            logger.error(f"JSON解析失败，响应内容: {response_text[:500]}...")
            return SecondPassToThirdPass(
                research_question={},
                literature_review={},
                methodology={},
                findings={},
                limitations={},
                writing_techniques={},
                full_text=first_pass_output.full_text
            )
