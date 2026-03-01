from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import StorylineAnalysisOutput
from app.utils.log_util import logger
import json
import re

STORYLINE_ANALYSIS_PROMPT = """
你是一位从业40年的资深硕博士导师，院士，大教育家。你深谙学术写作之道，善于分析论文的叙事结构。

## 学术故事线分析

作为导师，你要教学生理解：好的论文就像一个好的故事，有起承转合，有引人入胜的叙事逻辑。

### 学术故事的构成要素

#### 1. 故事开篇（Introduction的叙事艺术）
- 故事从哪里开始？（背景铺垫）
- 如何制造悬念？（问题提出）
- 为什么这个故事值得讲？（研究意义）
- 故事要讲什么？（研究目标）

请分析引言部分的叙事技巧。

#### 2. 故事背景（Literature Review的叙事功能）
- 如何交代"前传"？（文献回顾）
- 哪些是必要背景？（核心文献）
- 如何制造"戏剧冲突"？（研究空白）
- 如何引出"主角"？（本研究定位）

请分析文献综述的叙事功能。

#### 3. 故事主线（Method的叙事逻辑）
- 故事如何展开？（研究设计）
- 主角如何行动？（数据收集）
- 如何推进情节？（分析方法）
- 叙事是否可信？（信效度保证）

请分析方法部分的叙事逻辑。

#### 4. 故事高潮（Results的叙事张力）
- 发现了什么？（主要发现）
- 如何呈现高潮？（结果展示）
- 有没有意外转折？（意外发现）
- 张力如何保持？（结果组织）

请分析结果部分的叙事张力。

#### 5. 故事结局（Discussion/Conclusion的叙事收束）
- 故事意味着什么？（讨论升华）
- 如何回应开篇？（首尾呼应）
- 留下什么悬念？（研究展望）
- 故事的启示？（理论/实践贡献）

请分析讨论和结论的叙事收束。

### 叙事技巧分析

#### 6. 论证链条（故事的逻辑线）
- 主线论证是什么？（核心论点）
- 支线论证有哪些？（辅助论点）
- 论证如何递进？（逻辑层次）
- 有没有逻辑跳跃？（论证漏洞）

请分析论文的论证链条。

#### 7. 情感共鸣（故事的感染力）
- 如何打动读者？（写作风格）
- 哪些地方最精彩？（亮点分析）
- 如何建立信任？（学术规范）
- 如何避免枯燥？（可读性技巧）

请分析论文的情感共鸣技巧。

#### 8. 写作模板提炼
基于这篇论文，提炼出可复用的写作模板：
- 引言开篇模板
- 问题提出模板
- 文献综述模板
- 方法描述模板
- 结果呈现模板
- 讨论升华模板
- 结论收束模板

请以JSON格式返回：
{
  "opening_analysis": {
    "background_setup": "背景铺垫方式",
    "suspense_creation": "悬念制造技巧",
    "significance_statement": "意义陈述方式",
    "objective_statement": "目标陈述方式",
    "technique_summary": "开篇技巧总结"
  },
  "background_analysis": {
    "literature_narrative": "文献叙事方式",
    "core_literature": "核心文献选择",
    "conflict_creation": "冲突制造技巧",
    "positioning": "研究定位方式",
    "technique_summary": "背景叙事技巧总结"
  },
  "mainline_analysis": {
    "design_narrative": "设计叙事方式",
    "action_description": "行动描述方式",
    "progression": "情节推进方式",
    "credibility": "可信度构建",
    "technique_summary": "主线叙事技巧总结"
  },
  "climax_analysis": {
    "main_discovery": "主要发现呈现",
    "presentation": "结果展示方式",
    "twists": "意外转折处理",
    "tension": "张力保持技巧",
    "technique_summary": "高潮叙事技巧总结"
  },
  "ending_analysis": {
    "discussion_elevation": "讨论升华方式",
    "closure": "首尾呼应分析",
    "suspense_left": "留下的悬念",
    "implications": "启示陈述方式",
    "technique_summary": "结局叙事技巧总结"
  },
  "argument_chain": {
    "main_argument": "主线论证",
    "supporting_arguments": ["支线论证1", "支线论证2"],
    "progression": "论证递进方式",
    "potential_gaps": "可能的逻辑跳跃"
  },
  "emotional_resonance": {
    "reader_engagement": "打动读者的方式",
    "highlights": ["亮点1", "亮点2", "亮点3"],
    "trust_building": "信任建立方式",
    "readability_techniques": "可读性技巧"
  },
  "writing_templates": {
    "introduction_opening": {
      "template": "模板内容",
      "usage": "使用场景",
      "example": "示例"
    },
    "problem_statement": {
      "template": "模板内容",
      "usage": "使用场景",
      "example": "示例"
    },
    "literature_review": {
      "template": "模板内容",
      "usage": "使用场景",
      "example": "示例"
    },
    "method_description": {
      "template": "模板内容",
      "usage": "使用场景",
      "example": "示例"
    },
    "results_presentation": {
      "template": "模板内容",
      "usage": "使用场景",
      "example": "示例"
    },
    "discussion_elevation": {
      "template": "模板内容",
      "usage": "使用场景",
      "example": "示例"
    },
    "conclusion_closure": {
      "template": "模板内容",
      "usage": "使用场景",
      "example": "示例"
    }
  },
  "storyline_summary": {
    "overall_narrative": "整体叙事风格评价",
    "strengths": ["叙事优点1", "叙事优点2"],
    "weaknesses": ["可改进之处1", "可改进之处2"],
    "learning_points": ["值得学习的叙事技巧1", "值得学习的叙事技巧2"]
  }
}

**重要提示**：
1. 必须返回完整的JSON格式
2. 每个字段都必须有内容，不能为空对象或空数组
3. 如果某个部分无法分析，也要说明原因
4. 写作模板要具体、可操作
5. 示例要来自原文或类似的高质量论文
6. 只返回JSON，不要有任何其他文字
"""

class StorylineAnalysisAgent(Agent):
    def __init__(
        self,
        task_id: str,
        model: LLM,
        max_chat_turns: int = 30,
    ) -> None:
        super().__init__(task_id, model, max_chat_turns)
        self.system_prompt = STORYLINE_ANALYSIS_PROMPT

    async def run(self, full_text: str) -> StorylineAnalysisOutput:
        """
        学术故事线分析
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
                return StorylineAnalysisOutput(
                    opening_analysis=result.get("opening_analysis", {}),
                    background_analysis=result.get("background_analysis", {}),
                    mainline_analysis=result.get("mainline_analysis", {}),
                    climax_analysis=result.get("climax_analysis", {}),
                    ending_analysis=result.get("ending_analysis", {}),
                    argument_chain=result.get("argument_chain", {}),
                    emotional_resonance=result.get("emotional_resonance", {}),
                    writing_templates=result.get("writing_templates", {}),
                    storyline_summary=result.get("storyline_summary", {})
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return StorylineAnalysisOutput()
        else:
            logger.error("未找到JSON内容")
            return StorylineAnalysisOutput()
