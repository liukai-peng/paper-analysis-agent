from app.core.agents.agent import Agent
from app.core.llm.llm import LLM
from app.schemas.A2A import FirstPassToSecondPass, CoordinatorToFirstPass
from app.utils.log_util import logger
from app.utils.json_parser import extract_json_from_response
import json
import re

FIRST_PASS_PROMPT = """
你是一位资深的学术导师，正在用「三遍阅读法」指导学生阅读学术文献。你的讲解风格是：深入浅出、举例丰富、善于类比。

## 第一遍：找战场（约5-10分钟）

作为导师，你要帮助学生在脑海中建立这篇论文的「作战地图」。**你的讲解要像给本科生上课一样详细，不要点到即止，要深入解释每个概念。**

### 你的教学任务

请像导师一样，详细讲解以下内容：

#### 1. 研究现象（这个战场在哪？）
- 这篇文献在研究什么现象？**请用通俗的语言解释这个现象，就像你在给一个外行讲解一样**
- 这个现象为什么重要？有什么现实意义？**请举1-2个生活中的例子来说明**
- 这个现象在什么背景下发生？**请介绍相关的社会、历史或学术背景**
- 这个现象涉及哪些核心概念？**请逐一解释每个概念的含义**

#### 2. 理论工具（用什么武器打仗？）
- 作者使用了什么理论框架？**请详细解释这个理论的核心观点，不要只说名字**
  - 这个理论的创始人是谁？
  - 这个理论的核心命题是什么？
  - 这个理论解释了什么现象？
  - 这个理论有什么局限性？
- 借鉴了哪些前人的理论？**请简要介绍每个理论的核心思想**
- 使用了什么研究方法？（定量/定性/混合）**请解释为什么这个方法适合研究这个问题**
- 数据来源是什么？**数据的代表性如何？**

#### 3. 关键概念详解（这是新手最需要的！）
请提取论文中3-5个最核心的概念，对每个概念进行详细解释：
- 概念名称
- 概念的定义（学术定义 + 通俗解释）
- 这个概念在本研究中的具体含义
- 这个概念与相关概念的区别
- 一个生活中的类比或例子
- 这个概念在论文中是如何被测量/操作的

#### 4. 核心贡献（打赢了什么？）
- 这篇文献最重要的发现是什么？**请用"作者发现..."的句式详细说明**
- 这个发现有什么理论贡献？**这个发现如何推进了现有理论？**
- 这个发现有什么实践意义？**对实践工作者有什么具体指导？**

#### 5. 写作框架学习（学习论文怎么写）
- 标题是如何设计的？有什么特点？**好在哪里？可以如何模仿？**
- 摘要的结构是怎样的？**按照什么逻辑组织？**
- 关键词是如何选择的？**为什么选这几个？**
- 引言部分是如何开篇的？**用了什么"钩子"吸引读者？**

#### 6. 值得学习的表达
- 摘抄5-8个精彩的学术表达句式（比之前更多）
- 摘抄3-5个好的过渡句
- 标注这些句式可以用在什么场景
- **请解释每个句式好在哪里，为什么值得学习**

请以JSON格式返回，确保：
1. 所有字符串使用双引号包围
2. 字符串内部的引号必须使用反斜杠转义（如：\"）
3. 不要包含任何注释
4. 确保JSON格式严格有效
5. 只返回JSON内容，不要添加任何其他文本
{
  "phenomenon": {
    "description": "研究现象描述（详细版）",
    "plain_explanation": "用通俗语言解释这个现象",
    "real_life_examples": ["生活例子1", "生活例子2"],
    "importance": "现象的重要性",
    "background": "研究背景（包括社会、历史、学术背景）",
    "core_concepts_brief": ["概念1", "概念2", "概念3"]
  },
  "tools": {
    "theoretical_framework": {
      "name": "理论框架名称",
      "founder": "创始人",
      "core_propositions": "核心命题详细解释",
      "what_it_explains": "这个理论解释什么现象",
      "limitations": "理论局限性",
      "why_suitable": "为什么适合本研究"
    },
    "previous_theories": [
      {"name": "理论名", "core_idea": "核心思想"},
      {"name": "理论名", "core_idea": "核心思想"}
    ],
    "research_method": {
      "type": "研究方法类型",
      "why_suitable": "为什么适合研究这个问题",
      "advantages": "这种方法的优势"
    },
    "data_source": {
      "description": "数据来源描述",
      "representativeness": "数据代表性分析"
    }
  },
  "key_concepts": [
    {
      "name": "概念名称",
      "academic_definition": "学术定义",
      "plain_explanation": "通俗解释",
      "study_specific_meaning": "在本研究中的具体含义",
      "distinction_from_related": "与相关概念的区别",
      "analogy_or_example": "生活类比或例子",
      "how_measured": "在论文中如何被测量/操作化"
    }
  ],
  "contribution": {
    "main_finding": "主要发现（详细描述）",
    "theoretical_contribution": "理论贡献（如何推进现有理论）",
    "practical_implication": "实践意义（对实践工作者的具体指导）"
  },
  "writing_framework": {
    "title_analysis": "标题设计特点分析",
    "title_why_good": "好在哪里，如何模仿",
    "abstract_structure": "摘要结构分析",
    "abstract_logic": "摘要的组织逻辑",
    "keywords_analysis": "关键词选择分析",
    "keywords_why": "为什么选这几个",
    "introduction_opening": "引言开篇方式",
    "introduction_hook": "用了什么钩子吸引读者"
  },
  "useful_expressions": {
    "academic_sentences": [
      {"sentence": "句式1", "why_good": "好在哪里", "usage_scenario": "适用场景"},
      {"sentence": "句式2", "why_good": "好在哪里", "usage_scenario": "适用场景"}
    ],
    "transition_sentences": [
      {"sentence": "过渡句1", "why_good": "好在哪里"},
      {"sentence": "过渡句2", "why_good": "好在哪里"}
    ]
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

    def _extract_key_sections(self, text: str) -> str:
        """
        提取关键部分（摘要、引言、结论等）
        
        Args:
            text: 原始文本
            
        Returns:
            str: 关键部分文本
        """
        # 提取摘要
        abstract_patterns = [
            r'\n\s*Abstract\s*\n[\s\S]*?\n\s*',
            r'\n\s*ABSTRACT\s*\n[\s\S]*?\n\s*',
            r'\n\s*摘要\s*\n[\s\S]*?\n\s*',
        ]
        
        key_sections = []
        
        # 提取摘要
        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                key_sections.append("摘要:\n" + match.group(0))
                break
        
        # 提取结论
        conclusion_patterns = [
            r'\n\s*Conclusion\s*\n[\s\S]*?\n\s*',
            r'\n\s*CONCLUSION\s*\n[\s\S]*?\n\s*',
            r'\n\s*结论\s*\n[\s\S]*?\n\s*',
        ]
        
        for pattern in conclusion_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                key_sections.append("结论:\n" + match.group(0))
                break
        
        # 提取引言
        introduction_patterns = [
            r'\n\s*Introduction\s*\n[\s\S]*?\n\s*',
            r'\n\s*INTRODUCTION\s*\n[\s\S]*?\n\s*',
            r'\n\s*引言\s*\n[\s\S]*?\n\s*',
        ]
        
        for pattern in introduction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                key_sections.append("引言:\n" + match.group(0))
                break
        
        # 如果没有找到摘要，取前5000字符作为简介
        if not key_sections:
            key_sections.append("简介:\n" + text[:5000])
        
        return "\n\n".join(key_sections)

    async def run(self, coordinator_output: CoordinatorToFirstPass) -> FirstPassToSecondPass:
        """
        第一遍阅读 - 找战场
        """
        # ========== 第一层：文档摘要 ==========
        logger.info("FirstPassAgent: 第一层 - 提取关键部分")
        key_sections = self._extract_key_sections(coordinator_output.full_text)
        logger.info(f"关键部分长度: {len(key_sections)} 字符")

        await self.append_chat_history(
            {"role": "system", "content": self.system_prompt}
        )
        
        # 发送关键部分进行分析
        await self.append_chat_history({"role": "user", "content": key_sections})

        response = await self.model.chat(
            history=self.chat_history,
            agent_name=self.__class__.__name__,
        )
        response_text = response.choices[0].message.content

        # 保存原始响应
        if hasattr(self, 'data_recorder') and self.data_recorder:
            self.data_recorder.save_agent_response(
                self.__class__.__name__,
                "Task",
                response_text
            )

        # 尝试解析JSON，使用多种策略
        result = self._parse_response(response_text)
        
        if result:
            logger.info("JSON解析成功")
            return FirstPassToSecondPass(
                phenomenon=result.get("phenomenon", {}),
                tools=result.get("tools", {}),
                key_concepts=result.get("key_concepts", []),
                contribution=result.get("contribution", {}),
                writing_framework=result.get("writing_framework", {}),
                useful_expressions=result.get("useful_expressions", {}),
                full_text=coordinator_output.full_text
            )
        else:
            logger.error(f"JSON解析失败，响应内容: {response_text[:500]}...")
            # 作为最后的手段，返回一个基本的结构
            return FirstPassToSecondPass(
                phenomenon={"description": "解析失败，请检查原始响应"},
                tools={},
                key_concepts=[],
                contribution={},
                writing_framework={},
                useful_expressions={},
                full_text=coordinator_output.full_text
            )
    
    def _parse_response(self, response_text: str) -> dict:
        """
        解析响应文本，使用多种策略
        
        Args:
            response_text: 响应文本
            
        Returns:
            dict: 解析结果
        """
        # 策略1: 直接使用extract_json_from_response
        result = extract_json_from_response(response_text)
        if result:
            return result
        
        # 策略2: 尝试使用更宽松的解析方法
        try:
            # 清理文本
            cleaned = response_text.replace('“', '"').replace('”', '"')
            # 尝试使用eval（仅作为最后的手段）
            result = eval(cleaned)
            if isinstance(result, dict):
                logger.info("使用eval解析成功")
                return result
        except Exception as e:
            logger.debug(f"eval解析失败: {e}")
        
        # 策略3: 尝试手动构建一个基本结构
        try:
            # 提取phenomenon部分
            import re
            phenom_match = re.search(r'"phenomenon":\s*\{(.*?)\}', response_text, re.DOTALL)
            if phenom_match:
                phenom_text = phenom_match.group(1)
                # 简单处理，提取description
                desc_match = re.search(r'"description":\s*"(.*?)"', phenom_text)
                if desc_match:
                    description = desc_match.group(1)
                    return {
                        "phenomenon": {"description": description},
                        "tools": {},
                        "key_concepts": [],
                        "contribution": {},
                        "writing_framework": {},
                        "useful_expressions": {}
                    }
        except Exception as e:
            logger.debug(f"手动解析失败: {e}")
        
        return {}
