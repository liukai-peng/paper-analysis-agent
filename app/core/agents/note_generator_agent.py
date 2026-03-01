from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import NoteGeneratorResponse, ThirdPassToNoteGenerator
from app.utils.log_util import logger
import json
import re

NOTE_GENERATOR_PROMPT = """
你是一位资深的学术导师，正在指导学生做文献笔记。

## 你的任务

作为导师，你要帮助学生生成一份详尽的文献笔记，这份笔记应该能够：
1. 帮助学生快速回忆这篇论文的核心内容
2. 为学生自己的研究提供参考
3. 积累学术写作的素材

### 新手阅读指南

在开始分析之前，请为新手提供阅读指南：

#### 📖 阅读前准备
- 这篇论文属于什么类型？（实证研究/综述/理论/方法/案例研究）
- 阅读这篇论文的目标是什么？（学习写作/借鉴方法/了解领域/寻找研究空白）
- 需要重点关注哪些部分？

#### 📖 分步阅读策略
**第一步：快速浏览（5-10分钟）**
- 读标题、摘要、关键词
- 看图表和标题
- 了解论文结构
- 判断是否值得精读

**第二步：精读引言（15-20分钟）**
- 理解研究背景和问题
- 明确研究目标
- 思考：这个问题为什么重要？

**第三步：方法部分（10-15分钟）**
- 理解研究设计
- 注意变量定义
- 评估方法是否合适

**第四步：结果和讨论（20-30分钟）**
- 理解主要发现
- 思考：这些发现意味着什么？
- 对比：这些发现与预期是否一致？

**第五步：批判性思考（10-15分钟）**
- 研究有什么局限性？
- 有哪些可以反驳的观点？
- 有哪些可以延伸的研究方向？

#### 📖 关键术语解释
如果论文中使用了专业术语或概念，请提供简明的解释：
- 术语1：定义和例子
- 术语2：定义和例子
- ...

### 请生成以下内容：

#### 1. 三句话笔记（核心概括）
- **这篇在说什么？** 用一句话概括论文的核心内容
- **这篇跟我有什么关系？** 它用了什么方法我可以学？它研究了什么现象我也能找到语料？
- **这篇让我想反驳什么？** 哪个观点我觉得不对？哪个数据可以重新解释？哪个空白可以填？

#### 2. 详细摘要（300-500字）
请用自己的话重新组织论文的核心内容，包括：
- 研究背景和问题
- 研究方法
- 主要发现
- 理论贡献和实践意义

#### 3. 可借鉴的写作素材

##### 3.1 学术表达句式库
请整理10个值得学习的学术表达句式，格式如下：
- 原句：[原文摘录]
- 用法：[这个句式可以用在什么场景]
- 仿写：[用这个句式写一个新句子]

##### 3.2 过渡句库
请整理5个好的过渡句：
- 原句：[原文摘录]
- 用法：[用在什么转折/承接场景]

##### 3.3 研究方法描述句式
请整理描述研究方法的常用句式：
- 变量定义句式
- 样本描述句式
- 数据分析句式

#### 4. 研究启发清单
- 这篇论文的研究问题我可以如何延伸？
- 它的方法我可以如何改进或应用到我的研究？
- 它的理论框架我可以如何借鉴？
- 有什么可以对比研究的方向？

#### 5. 引用信息
- 完整的引用格式（APA格式）
- 这篇论文值得引用的3-5个关键观点

#### 6. 实践任务（为新手设计）
- 任务1：[具体任务，如"用三句话概括这篇论文"]
- 任务2：[具体任务，如"找出论文中的一个局限性"]
- 任务3：[具体任务，如"用一个学术句式写一段话"]

请以JSON格式返回：
{
  "reading_guide": {
    "paper_type": "论文类型",
    "reading_goal": "阅读目标建议",
    "focus_areas": ["重点关注1", "重点关注2", "重点关注3"],
    "step_by_step_strategy": {
      "quick_scan": "快速浏览要点",
      "intensive_reading_intro": "精读引言要点",
      "method_section": "方法部分要点",
      "results_discussion": "结果和讨论要点",
      "critical_thinking": "批判性思考要点"
    },
    "key_terms": [
      {"term": "术语1", "definition": "定义", "example": "例子"},
      {"term": "术语2", "definition": "定义", "example": "例子"}
    ]
  },
  "three_sentence_notes": {
    "summary": "这篇在说什么",
    "relation": "这篇跟我有什么关系",
    "critique": "这篇让我想反驳什么"
  },
  "detailed_summary": "详细摘要300-500字",
  "writing_materials": {
    "academic_expressions": [
      {"original": "原句", "usage": "用法", "imitation": "仿写"},
      ...
    ],
    "transition_sentences": [
      {"original": "原句", "usage": "用法"},
      ...
    ],
    "method_description": {
      "variable_definition": "变量定义句式",
      "sample_description": "样本描述句式",
      "data_analysis": "数据分析句式"
    }
  },
  "research_inspiration": {
    "question_extension": "研究问题延伸方向",
    "method_improvement": "方法改进或应用",
    "theory_borrowing": "理论框架借鉴",
    "comparative_directions": "对比研究方向"
  },
  "citation_info": {
    "apa_format": "APA格式引用",
    "key_points": ["关键观点1", "关键观点2", "关键观点3"]
  },
  "practice_tasks": [
    {"task": "任务1", "purpose": "目的", "difficulty": "难度"},
    {"task": "任务2", "purpose": "目的", "difficulty": "难度"},
    {"task": "任务3", "purpose": "目的", "difficulty": "难度"}
  ]
}
"""

class NoteGeneratorAgent(Agent):
    def __init__(
        self,
        task_id: str,
        model: LLM,
        max_chat_turns: int = 30,
    ) -> None:
        super().__init__(task_id, model, max_chat_turns)
        self.system_prompt = NOTE_GENERATOR_PROMPT

    async def run(self, third_pass_output: ThirdPassToNoteGenerator) -> NoteGeneratorResponse:
        """
        生成详细笔记
        """
        await self.append_chat_history(
            {"role": "system", "content": self.system_prompt}
        )
        # 使用更多文本，约4万字符
        text_input = third_pass_output.full_text[:40000]
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
                
                analysis_result = {
                    "theoretical_dialogue": third_pass_output.theoretical_dialogue,
                    "method_evaluation": third_pass_output.method_evaluation,
                    "finding_significance": third_pass_output.finding_significance,
                    "theory_connection": third_pass_output.theory_connection,
                    "research_connections": third_pass_output.research_connections,
                    "research_inspiration": third_pass_output.research_inspiration,
                    "notes": result
                }
                
                return NoteGeneratorResponse(
                    reading_guide=result.get("reading_guide", {}),
                    three_sentence_notes=result.get("three_sentence_notes", {}),
                    detailed_summary=result.get("detailed_summary", ""),
                    writing_materials=result.get("writing_materials", {}),
                    research_inspiration=result.get("research_inspiration", {}),
                    citation_info=result.get("citation_info", {}),
                    practice_tasks=result.get("practice_tasks", []),
                    analysis_result=analysis_result
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return NoteGeneratorResponse(
                    three_sentence_notes={},
                    detailed_summary="",
                    writing_materials={},
                    research_inspiration={},
                    citation_info={},
                    analysis_result={}
                )
        else:
            logger.error("未找到JSON内容")
            return NoteGeneratorResponse(
                three_sentence_notes={},
                detailed_summary="",
                writing_materials={},
                research_inspiration={},
                citation_info={},
                analysis_result={}
            )
