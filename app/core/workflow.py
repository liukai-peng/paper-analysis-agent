from app.core.agents import (
    CoordinatorAgent, FirstPassAgent, SecondPassAgent, 
    ThirdPassAgent, NoteGeneratorAgent,
    CriticalThinkingAgent, SocraticQuestioningAgent,
    ResearchGapAgent, StorylineAnalysisAgent, WritingFrameworkAgent,
    PaperSplitterAgent
)
from app.core.llm.llm_factory import LLMFactory
from app.utils.log_util import logger
from app.utils.error_handler import retry, handle_errors
from app.utils.data_recorder import DataRecorder
from app.schemas.A2A import PaperSplitOutput, SectionAnalysisOutput
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class WorkFlow:
    def __init__(self):
        pass

    def execute(self) -> str:
        pass

class LiteratureWorkFlow(WorkFlow):
    task_id: str
    work_dir: str

    @retry(max_attempts=3, delay=2.0, backoff=2.0)
    @handle_errors(error_message="文献解读工作流执行失败")
    async def execute(self, full_text: str, api_key: str, enable_teaching: bool = True) -> dict:
        """
        执行文献解读工作流
        
        Args:
            full_text: 文献全文
            api_key: API密钥
            enable_teaching: 是否启用教学模块
        """
        self.task_id = f"lit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.work_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'project', 'work_dir', self.task_id)
        os.makedirs(self.work_dir, exist_ok=True)

        logger.info(f"开始文献解读工作流: {self.task_id}")
        logger.info(f"文献全文长度: {len(full_text)} 字符")
        logger.info(f"教学模块: {'启用' if enable_teaching else '禁用'}")

        try:
            # 初始化LLM
            logger.info(f"初始化LLM，API密钥长度: {len(api_key) if api_key else 0}")
            if not api_key or not api_key.strip():
                raise ValueError("API密钥不能为空，请在侧边栏输入Deepseek API密钥")

            # 初始化数据记录器
            data_recorder = DataRecorder(self.work_dir)

            llm_factory = LLMFactory(self.task_id)
            coordinator_llm, first_pass_llm, second_pass_llm, third_pass_llm = llm_factory.get_all_llms(api_key)
            
            # 设置数据记录器
            coordinator_llm.set_data_recorder(data_recorder)
            first_pass_llm.set_data_recorder(data_recorder)
            second_pass_llm.set_data_recorder(data_recorder)
            third_pass_llm.set_data_recorder(data_recorder)

            # ========== 第一阶段：基础分析 ==========
            
            # 1. CoordinatorAgent - 识别文献类型
            logger.info("=" * 50)
            logger.info("第1步: CoordinatorAgent - 识别文献类型")
            logger.info("=" * 50)
            coordinator_agent = CoordinatorAgent(self.task_id, coordinator_llm)
            coordinator_output = await coordinator_agent.run(full_text)
            logger.info(f"文献类型: {coordinator_output.document_type}")
            logger.info(f"文献标题: {coordinator_output.title}")

            # 2. FirstPassAgent - 找战场
            logger.info("=" * 50)
            logger.info("第2步: FirstPassAgent - 找战场（第一遍阅读）")
            logger.info("=" * 50)
            first_pass_agent = FirstPassAgent(self.task_id, first_pass_llm)
            first_pass_output = await first_pass_agent.run(coordinator_output)
            logger.info("第一遍阅读完成")

            # 3. SecondPassAgent - 拆地图
            logger.info("=" * 50)
            logger.info("第3步: SecondPassAgent - 拆作战地图（第二遍阅读）")
            logger.info("=" * 50)
            second_pass_agent = SecondPassAgent(self.task_id, second_pass_llm)
            second_pass_output = await second_pass_agent.run(first_pass_output)
            logger.info("第二遍阅读完成")

            # 4. ThirdPassAgent - 画连接
            logger.info("=" * 50)
            logger.info("第4步: ThirdPassAgent - 画火力连接图（第三遍阅读）")
            logger.info("=" * 50)
            third_pass_agent = ThirdPassAgent(self.task_id, third_pass_llm)
            third_pass_output = await third_pass_agent.run(second_pass_output)
            logger.info("第三遍阅读完成")

            # 5. NoteGeneratorAgent - 生成详细笔记
            logger.info("=" * 50)
            logger.info("第5步: NoteGeneratorAgent - 生成详细笔记")
            logger.info("=" * 50)
            note_generator_agent = NoteGeneratorAgent(self.task_id, third_pass_llm)
            note_output = await note_generator_agent.run(third_pass_output)
            logger.info("笔记生成完成")

            # 构建基础结果
            result = {
                "task_id": self.task_id,
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "enable_teaching": enable_teaching,
                
                "basic_info": {
                    "document_type": coordinator_output.document_type,
                    "title": coordinator_output.title,
                    "authors": coordinator_output.authors,
                    "year": coordinator_output.year,
                    "journal": coordinator_output.journal,
                    "research_field": coordinator_output.research_field,
                    "one_sentence_summary": coordinator_output.one_sentence_summary
                },
                
                "first_pass": {
                    "phenomenon": first_pass_output.phenomenon,
                    "tools": first_pass_output.tools,
                    "contribution": first_pass_output.contribution,
                    "writing_framework": first_pass_output.writing_framework,
                    "useful_expressions": first_pass_output.useful_expressions
                },
                
                "second_pass": {
                    "research_question": second_pass_output.research_question,
                    "literature_review": second_pass_output.literature_review,
                    "methodology": second_pass_output.methodology,
                    "findings": second_pass_output.findings,
                    "limitations": second_pass_output.limitations,
                    "writing_techniques": second_pass_output.writing_techniques
                },
                
                "third_pass": {
                    "theoretical_dialogue": third_pass_output.theoretical_dialogue,
                    "method_evaluation": third_pass_output.method_evaluation,
                    "finding_significance": third_pass_output.finding_significance,
                    "theory_connection": third_pass_output.theory_connection,
                    "research_connections": third_pass_output.research_connections,
                    "research_inspiration": third_pass_output.research_inspiration
                },
                
                "notes": {
                    "reading_guide": note_output.reading_guide,
                    "three_sentence_notes": note_output.three_sentence_notes,
                    "detailed_summary": note_output.detailed_summary,
                    "writing_materials": note_output.writing_materials,
                    "research_inspiration": note_output.research_inspiration,
                    "citation_info": note_output.citation_info,
                    "practice_tasks": note_output.practice_tasks
                }
            }

            # ========== 第二阶段：导师教学模块 ==========
            
            if enable_teaching:
                logger.info("=" * 50)
                logger.info("第二阶段：导师教学模块")
                logger.info("=" * 50)
                
                # 6. CriticalThinkingAgent - 批判性思维训练
                logger.info("第6步: CriticalThinkingAgent - 批判性思维训练")
                critical_thinking_agent = CriticalThinkingAgent(self.task_id, third_pass_llm)
                critical_thinking_output = await critical_thinking_agent.run(full_text)
                logger.info("批判性思维训练完成")
                
                # 7. SocraticQuestioningAgent - 苏格拉底式提问
                logger.info("第7步: SocraticQuestioningAgent - 苏格拉底式提问")
                socratic_agent = SocraticQuestioningAgent(self.task_id, third_pass_llm)
                socratic_output = await socratic_agent.run(full_text)
                logger.info("苏格拉底式提问完成")
                
                # 8. ResearchGapAgent - 研究空白发现
                logger.info("第8步: ResearchGapAgent - 研究空白发现")
                research_gap_agent = ResearchGapAgent(self.task_id, third_pass_llm)
                research_gap_output = await research_gap_agent.run(full_text)
                logger.info("研究空白发现完成")
                
                # 9. StorylineAnalysisAgent - 学术故事线分析
                logger.info("第9步: StorylineAnalysisAgent - 学术故事线分析")
                storyline_agent = StorylineAnalysisAgent(self.task_id, third_pass_llm)
                storyline_output = await storyline_agent.run(full_text)
                logger.info("学术故事线分析完成")
                
                # 10. WritingFrameworkAgent - 写作框架教学
                logger.info("第10步: WritingFrameworkAgent - 写作框架教学")
                writing_framework_agent = WritingFrameworkAgent(self.task_id, third_pass_llm)
                writing_framework_output = await writing_framework_agent.run(full_text)
                logger.info("写作框架教学完成")
                
                # 添加教学模块结果
                result["teaching"] = {
                    "critical_thinking": {
                        "argument_critique": critical_thinking_output.argument_critique,
                        "method_critique": critical_thinking_output.method_critique,
                        "data_critique": critical_thinking_output.data_critique,
                        "logic_critique": critical_thinking_output.logic_critique,
                        "critical_questions": critical_thinking_output.critical_questions,
                        "counterexample_thinking": critical_thinking_output.counterexample_thinking
                    },
                    "socratic_questioning": {
                        "clarifying_questions": socratic_output.clarifying_questions,
                        "assumption_questions": socratic_output.assumption_questions,
                        "evidence_questions": socratic_output.evidence_questions,
                        "perspective_questions": socratic_output.perspective_questions,
                        "implication_questions": socratic_output.implication_questions,
                        "metacognitive_questions": socratic_output.metacognitive_questions,
                        "thinking_pathway": socratic_output.thinking_pathway
                    },
                    "research_gap": {
                        "theory_gaps": research_gap_output.theory_gaps,
                        "method_gaps": research_gap_output.method_gaps,
                        "empirical_gaps": research_gap_output.empirical_gaps,
                        "practical_gaps": research_gap_output.practical_gaps,
                        "interdisciplinary_gaps": research_gap_output.interdisciplinary_gaps,
                        "temporal_gaps": research_gap_output.temporal_gaps,
                        "research_questions": research_gap_output.research_questions,
                        "priority_recommendation": research_gap_output.priority_recommendation
                    },
                    "storyline_analysis": {
                        "opening_analysis": storyline_output.opening_analysis,
                        "background_analysis": storyline_output.background_analysis,
                        "mainline_analysis": storyline_output.mainline_analysis,
                        "climax_analysis": storyline_output.climax_analysis,
                        "ending_analysis": storyline_output.ending_analysis,
                        "argument_chain": storyline_output.argument_chain,
                        "emotional_resonance": storyline_output.emotional_resonance,
                        "writing_templates": storyline_output.writing_templates,
                        "storyline_summary": storyline_output.storyline_summary
                    },
                    "writing_framework": {
                        "structure_analysis": writing_framework_output.structure_analysis,
                        "paragraph_organization": writing_framework_output.paragraph_organization,
                        "title_framework": writing_framework_output.title_framework,
                        "abstract_framework": writing_framework_output.abstract_framework,
                        "introduction_framework": writing_framework_output.introduction_framework,
                        "literature_review_framework": writing_framework_output.literature_review_framework,
                        "method_framework": writing_framework_output.method_framework,
                        "results_framework": writing_framework_output.results_framework,
                        "discussion_framework": writing_framework_output.discussion_framework,
                        "conclusion_framework": writing_framework_output.conclusion_framework,
                        "academic_norms": writing_framework_output.academic_norms,
                        "common_mistakes": writing_framework_output.common_mistakes,
                        "quick_reference": writing_framework_output.quick_reference
                    }
                }

            # 保存结果
            result_file = os.path.join(self.work_dir, "analysis_result.json")
            
            # 验证结果数据完整性
            if not result:
                logger.error("分析结果为空，无法保存")
                raise ValueError("分析结果为空")
            
            # 使用数据记录器保存分析结果
            data_recorder.save_analysis_result(result)
            
            # 打印统计摘要
            data_recorder.print_summary()

            logger.info(f"工作流完成，结果保存到: {result_file}")
            return result

        except Exception as e:
            logger.error(f"工作流执行过程中发生错误: {e}")
            raise


class PaperSplitWorkflow(WorkFlow):
    """论文切分工作流 - 第一步：切分论文结构"""

    task_id: str
    work_dir: str

    async def split_paper(self, full_text: str, api_key: str) -> PaperSplitOutput:
        """
        切分论文结构

        Args:
            full_text: 论文全文
            api_key: API密钥

        Returns:
            PaperSplitOutput: 切分结果
        """
        self.task_id = f"split_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.work_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'project', 'work_dir', self.task_id)
        os.makedirs(self.work_dir, exist_ok=True)

        logger.info(f"开始论文切分: {self.task_id}")
        logger.info(f"论文全文长度: {len(full_text)} 字符")

        if not api_key or not api_key.strip():
            raise ValueError("API密钥不能为空")

        llm_factory = LLMFactory(self.task_id)
        splitter_llm, _, _, _ = llm_factory.get_all_llms(api_key)

        # 使用 PaperSplitterAgent 切分论文
        splitter_agent = PaperSplitterAgent(self.task_id, splitter_llm)
        split_result = await splitter_agent.run(full_text)

        # 保存切分结果
        split_file = os.path.join(self.work_dir, "split_result.json")
        with open(split_file, "w", encoding="utf-8") as f:
            json.dump(split_result.model_dump(), f, ensure_ascii=False, indent=2)

        logger.info(f"论文切分完成，共 {len(split_result.sections)} 个章节")

        return split_result

    async def analyze_section(
        self,
        full_text: str,
        section_name: str,
        api_key: str,
        analysis_depth: str = "deep"
    ) -> Dict[str, Any]:
        """
        深度分析特定章节

        Args:
            full_text: 论文全文
            section_name: 章节名称
            api_key: API密钥
            analysis_depth: 分析深度 (quick/deep)

        Returns:
            章节分析结果
        """
        self.task_id = f"section_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"开始章节深度分析: {section_name}")

        if not api_key or not api_key.strip():
            raise ValueError("API密钥不能为空")

        llm_factory = LLMFactory(self.task_id)
        _, first_pass_llm, second_pass_llm, third_pass_llm = llm_factory.get_all_llms(api_key)

        # 根据章节名称选择合适的分析策略
        section_prompts = {
            "引言": INTRODUCTION_ANALYSIS_PROMPT,
            "文献综述": LITERATURE_REVIEW_ANALYSIS_PROMPT,
            "研究方法": METHODOLOGY_ANALYSIS_PROMPT,
            "方法": METHODOLOGY_ANALYSIS_PROMPT,
            "结果": RESULTS_ANALYSIS_PROMPT,
            "讨论": DISCUSSION_ANALYSIS_PROMPT,
            "结论": CONCLUSION_ANALYSIS_PROMPT,
        }

        prompt = section_prompts.get(section_name, DEFAULT_SECTION_PROMPT)

        # 使用 third_pass_llm 进行深度分析
        from app.core.llm.llm import LLM
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请深度分析以下论文的【{section_name}】部分：\n\n{full_text[:35000]}"}
        ]

        response = await third_pass_llm.chat(messages, agent_name="SectionAnalyzer")

        from app.utils.json_parser import extract_json_from_response
        response_text = response.choices[0].message.content
        result = extract_json_from_response(response_text)

        if not result:
            result = {"raw_analysis": response_text}

        result["section_name"] = section_name
        result["analysis_depth"] = analysis_depth

        return result


# 章节分析提示词
INTRODUCTION_ANALYSIS_PROMPT = """
你是一位资深学术导师，正在指导学生深入理解论文的【引言】部分。

## 分析任务

请对引言部分进行深度分析，包括：

### 1. 研究背景梳理
- 研究领域的现状如何？
- 存在哪些核心问题或争议？
- 作者如何引出研究问题？

### 2. 研究问题分析
- 核心研究问题是什么？
- 研究假设是什么？
- 研究目的和意义？

### 3. 写作技巧
- 作者如何吸引读者注意？
- 如何从背景过渡到研究问题？
- 使用了哪些修辞手法？

### 4. 可学习的句式
- 列出5-10个可以借鉴的学术表达

请以JSON格式返回：
{
  "section_name": "引言",
  "background_analysis": {...},
  "research_question_analysis": {...},
  "writing_techniques": {...},
  "useful_expressions": [...],
  "key_insights": [...]
}
"""

LITERATURE_REVIEW_ANALYSIS_PROMPT = """
你是一位资深学术导师，正在指导学生深入理解论文的【文献综述】部分。

## 分析任务

### 1. 文献组织结构
- 作者如何组织文献？
- 按时间/主题/方法论分类？

### 2. 研究空白识别
- 作者指出了哪些研究空白？
- 如何论证现有研究的不足？

### 3. 批判性分析
- 作者如何评价前人研究？
- 有哪些批判性思维值得学习？

### 4. 写作框架
- 文献综述的逻辑框架是什么？
- 如何引出自己的研究？

请以JSON格式返回分析结果。
"""

METHODOLOGY_ANALYSIS_PROMPT = """
你是一位资深学术导师，正在指导学生深入理解论文的【研究方法】部分。

## 分析任务

### 1. 研究设计
- 采用了什么研究设计？
- 为什么选择这种设计？

### 2. 数据收集
- 数据来源是什么？
- 样本选择标准？
- 数据收集工具？

### 3. 数据分析
- 使用了哪些分析方法？
- 为什么选择这些方法？

### 4. 方法论启示
- 这种方法可以应用到哪些其他研究？
- 有哪些注意事项？

请以JSON格式返回分析结果。
"""

RESULTS_ANALYSIS_PROMPT = """
你是一位资深学术导师，正在指导学生深入理解论文的【结果】部分。

## 分析任务

### 1. 主要发现
- 核心发现是什么？
- 数据如何支持结论？

### 2. 结果呈现
- 作者如何呈现结果？
- 图表使用是否恰当？

### 3. 数据解读
- 关键数据的意义是什么？
- 有哪些意外发现？

请以JSON格式返回分析结果。
"""

DISCUSSION_ANALYSIS_PROMPT = """
你是一位资深学术导师，正在指导学生深入理解论文的【讨论】部分。

## 分析任务

### 1. 结果解释
- 作者如何解释研究发现？
- 与假设是否一致？

### 2. 理论贡献
- 对理论有什么贡献？
- 如何与前人研究对话？

### 3. 局限性
- 作者承认了哪些局限？
- 还有哪些未提及的局限？

### 4. 实践意义
- 研究有什么实践价值？

请以JSON格式返回分析结果。
"""

CONCLUSION_ANALYSIS_PROMPT = """
你是一位资深学术导师，正在指导学生深入理解论文的【结论】部分。

## 分析任务

### 1. 核心结论
- 研究的主要结论是什么？
- 是否回答了研究问题？

### 2. 未来研究方向
- 作者提出了哪些未来研究方向？
- 还有哪些可以延伸的研究？

### 3. 写作技巧
- 如何简洁有力地总结研究？

请以JSON格式返回分析结果。
"""

DEFAULT_SECTION_PROMPT = """
你是一位资深学术导师，请深度分析论文的这一部分。

请以JSON格式返回：
{
  "section_name": "章节名称",
  "main_content": {...},
  "key_points": [...],
  "writing_techniques": {...},
  "useful_expressions": [...],
  "critical_insights": [...]
}
"""
