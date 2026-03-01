from app.core.agents.agent import Agent
from app.core.agents.coordinator_agent import CoordinatorAgent
from app.core.agents.first_pass_agent import FirstPassAgent
from app.core.agents.second_pass_agent import SecondPassAgent
from app.core.agents.third_pass_agent import ThirdPassAgent
from app.core.agents.note_generator_agent import NoteGeneratorAgent
from app.core.agents.critical_thinking_agent import CriticalThinkingAgent
from app.core.agents.socratic_questioning_agent import SocraticQuestioningAgent
from app.core.agents.research_gap_agent import ResearchGapAgent
from app.core.agents.storyline_analysis_agent import StorylineAnalysisAgent
from app.core.agents.writing_framework_agent import WritingFrameworkAgent
from app.core.agents.paper_splitter_agent import PaperSplitterAgent

__all__ = [
    "Agent",
    "CoordinatorAgent",
    "FirstPassAgent",
    "SecondPassAgent",
    "ThirdPassAgent",
    "NoteGeneratorAgent",
    "CriticalThinkingAgent",
    "SocraticQuestioningAgent",
    "ResearchGapAgent",
    "StorylineAnalysisAgent",
    "WritingFrameworkAgent",
    "PaperSplitterAgent"
]
