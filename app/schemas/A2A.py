from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class PaperSection(BaseModel):
    """论文章节模型"""
    name: str
    start_marker: str = ""
    content: str = ""
    key_points: List[str] = []
    importance: str = "中"
    char_count: int = 0


class PaperSplitOutput(BaseModel):
    """论文切分输出"""
    title: str = ""
    authors: List[str] = []
    abstract: str = ""
    sections: List[PaperSection] = []
    total_chars: int = 0
    full_text: str = ""


class SectionAnalysisOutput(BaseModel):
    """章节深度分析输出"""
    section_name: str = ""
    main_content: Dict[str, str] = {}
    key_arguments: List[Dict[str, str]] = []
    methodology_details: Dict[str, str] = {}
    data_analysis: Dict[str, str] = {}
    writing_techniques: Dict[str, Any] = {}
    useful_expressions: List[str] = []
    critical_points: List[str] = []
    questions_to_explore: List[str] = []


class CoordinatorToFirstPass(BaseModel):
    document_type: str
    full_text: str
    title: str
    authors: List[str] = []
    year: str = ""
    journal: str = ""
    research_field: str = ""
    type_reason: str = ""
    one_sentence_summary: str = ""

class FirstPassToSecondPass(BaseModel):
    phenomenon: Dict[str, Any] = {}
    tools: Dict[str, Any] = {}
    key_concepts: List[Dict[str, str]] = []
    contribution: Dict[str, str] = {}
    writing_framework: Dict[str, Any] = {}
    useful_expressions: Dict[str, Any] = {}
    full_text: str

class SecondPassToThirdPass(BaseModel):
    research_question: Dict[str, Any] = {}
    literature_review: Dict[str, Any] = {}
    methodology: Dict[str, Any] = {}
    findings: Dict[str, Any] = {}
    limitations: Dict[str, Any] = {}
    writing_techniques: Dict[str, Any] = {}
    full_text: str

class ThirdPassToNoteGenerator(BaseModel):
    theoretical_dialogue: Dict[str, Any] = {}
    method_evaluation: Dict[str, Any] = {}
    finding_significance: Dict[str, Any] = {}
    theory_connection: Dict[str, Any] = {}
    research_connections: Dict[str, Any] = {}
    research_inspiration: Dict[str, Any] = {}
    full_text: str

class NoteGeneratorResponse(BaseModel):
    reading_guide: Dict[str, Any] = {}
    three_sentence_notes: Dict[str, str] = {}
    detailed_summary: str = ""
    writing_materials: Dict[str, Any] = {}
    research_inspiration: Dict[str, str] = {}
    citation_info: Dict[str, Any] = {}
    practice_tasks: List[Dict[str, str]] = []
    analysis_result: Dict[str, Any] = {}

class CriticalThinkingOutput(BaseModel):
    argument_critique: Dict[str, str] = {}
    method_critique: Dict[str, str] = {}
    data_critique: Dict[str, str] = {}
    logic_critique: Dict[str, str] = {}
    critical_questions: List[Dict[str, str]] = []
    counterexample_thinking: Dict[str, str] = {}

class SocraticQuestioningOutput(BaseModel):
    clarifying_questions: List[Dict[str, str]] = []
    assumption_questions: List[Dict[str, str]] = []
    evidence_questions: List[Dict[str, str]] = []
    perspective_questions: List[Dict[str, str]] = []
    implication_questions: List[Dict[str, str]] = []
    metacognitive_questions: List[Dict[str, str]] = []
    thinking_pathway: Dict[str, Any] = {}

class ResearchGapOutput(BaseModel):
    theory_gaps: List[Dict[str, str]] = []
    method_gaps: List[Dict[str, str]] = []
    empirical_gaps: List[Dict[str, str]] = []
    practical_gaps: List[Dict[str, str]] = []
    interdisciplinary_gaps: List[Dict[str, str]] = []
    temporal_gaps: List[Dict[str, str]] = []
    research_questions: List[Dict[str, str]] = []
    priority_recommendation: Dict[str, str] = {}

class StorylineAnalysisOutput(BaseModel):
    opening_analysis: Dict[str, str] = {}
    background_analysis: Dict[str, str] = {}
    mainline_analysis: Dict[str, str] = {}
    climax_analysis: Dict[str, str] = {}
    ending_analysis: Dict[str, str] = {}
    argument_chain: Dict[str, Any] = {}
    emotional_resonance: Dict[str, Any] = {}
    writing_templates: Dict[str, Any] = {}
    storyline_summary: Dict[str, Any] = {}

class WritingFrameworkOutput(BaseModel):
    structure_analysis: Dict[str, Any] = {}
    paragraph_organization: Dict[str, str] = {}
    title_framework: Dict[str, Any] = {}
    abstract_framework: Dict[str, Any] = {}
    introduction_framework: Dict[str, Any] = {}
    literature_review_framework: Dict[str, Any] = {}
    method_framework: Dict[str, Any] = {}
    results_framework: Dict[str, Any] = {}
    discussion_framework: Dict[str, Any] = {}
    conclusion_framework: Dict[str, Any] = {}
    academic_norms: Dict[str, str] = {}
    common_mistakes: Dict[str, Any] = {}
    quick_reference: Dict[str, List[str]] = {}
