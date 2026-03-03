import streamlit as st
from app.utils.pdf_processor import PDFProcessor
from app.core.workflow import PaperSplitWorkflow, LiteratureWorkFlow
from app.database.db_manager import get_db_manager
from app.utils.user_data_manager import UserDataManager
from app.utils.export_manager import ExportManager
from app.utils.log_util import logger
from app.utils.config_manager import config_manager
import asyncio
import os
import glob
import json
from typing import Dict, Any, List, Optional


def render_paper_split_page(api_key: str):
    """渲染论文切分页面"""

    st.title("📚 智能论文分析")
    st.markdown("*先了解结构，再深入分析*")

    # 检查 query params 来确定是否显示文献库
    logger.info(f"当前 query_params: {dict(st.query_params)}")
    if st.query_params.get("view") == "library":
        logger.info("检测到 view=library，设置 show_library=True")
        st.session_state.show_library = True

    # 初始化session state（只在第一次时初始化）
    if 'split_result' not in st.session_state:
        st.session_state.split_result = None
    if 'full_text' not in st.session_state:
        st.session_state.full_text = None
    if 'selected_sections' not in st.session_state:
        st.session_state.selected_sections = []
    if 'section_analysis' not in st.session_state:
        st.session_state.section_analysis = {}
    if 'analysis_mode' not in st.session_state:
        st.session_state.analysis_mode = None
    if 'full_analysis_result' not in st.session_state:
        st.session_state.full_analysis_result = None
    if 'export_success' not in st.session_state:
        st.session_state.export_success = None
    if 'analysis_in_progress' not in st.session_state:
        st.session_state.analysis_in_progress = False
    if 'section_analysis_in_progress' not in st.session_state:
        st.session_state.section_analysis_in_progress = False
    if 'show_library' not in st.session_state:
        st.session_state.show_library = False

    # 侧边栏设置
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # API密钥输入（如果未传入则显示输入框）
        saved_api_key = config_manager.get_api_key("deepseek")
        if not api_key:
            api_key = st.text_input(
                "API密钥",
                type="password",
                value=saved_api_key or "",
                help="请输入您的API密钥"
            )

        # 保存API密钥
        if api_key and api_key != saved_api_key:
            if st.button("💾 保存API密钥"):
                config_manager.set_api_key(api_key, "deepseek")
                st.success("✅ API密钥已安全保存")

        # 删除API密钥
        if saved_api_key:
            if st.button("🗑️ 删除API密钥"):
                config_manager.remove_api_key("deepseek")
                st.success("✅ API密钥已删除")
                st.rerun()

        if not api_key:
            st.warning("⚠️ 请输入API密钥以使用AI自动分析功能")

        # 导出功能
        if st.session_state.full_analysis_result:
            st.header("📥 导出结果")
            export_format = st.selectbox(
                "选择导出格式",
                ["JSON", "Markdown", "TXT"],
                key="export_format"
            )
            if st.button("导出分析结果", key="export_btn"):
                with st.spinner("正在导出..."):
                    export_result(st.session_state.full_analysis_result, export_format)

            # 显示导出成功信息
            if st.session_state.export_success:
                st.success(f"✅ 导出成功: {st.session_state.export_success}")

        # 保存到文献库
        if st.session_state.full_analysis_result or st.session_state.split_result:
            st.header("💾 保存到文献库")
            if st.button("保存分析结果", key="save_btn"):
                with st.spinner("正在保存..."):
                    save_to_library()

    # 步骤指示器
    if st.session_state.show_library:
        st.markdown("### 📋 文献库")
    else:
        steps = ["1️⃣ 上传PDF", "2️⃣ 查看结构", "3️⃣ 选择分析模式", "4️⃣ 查看结果"]
        current_step = get_current_step()
        st.markdown("### " + " → ".join(steps[:current_step]) + " → ".join(steps[current_step:]))

    # 根据当前步骤显示不同内容
    if st.session_state.show_library:
        # 显示文献库
        show_library()
        # 添加返回按钮
        if st.button("⬅️ 返回分析页面", key="back_to_analysis"):
            st.session_state.show_library = False
            if "view" in st.query_params:
                del st.query_params["view"]
            st.rerun()
    elif current_step == 1:
        render_upload_step(api_key)
    elif current_step == 2:
        render_structure_step(api_key)
    elif current_step == 3:
        render_analysis_mode_step(api_key)
    elif current_step == 4:
        render_result_step(api_key)


def get_current_step() -> int:
    """获取当前步骤"""
    logger.info(f"get_current_step: show_library={st.session_state.get('show_library', False)}, full_analysis_result={st.session_state.get('full_analysis_result') is not None}, analysis_mode={st.session_state.get('analysis_mode') is not None}, split_result={st.session_state.get('split_result') is not None}, full_text={bool(st.session_state.get('full_text', ''))}")
    
    if st.session_state.show_library:
        return 0  # 文献库模式
    if st.session_state.full_analysis_result is not None:
        return 4
    if st.session_state.analysis_mode:
        return 4
    if st.session_state.split_result is not None:
        return 3
    if st.session_state.full_text:
        return 2
    return 1


def render_upload_step(api_key: str):
    """步骤1：上传PDF"""

    st.header("1️⃣ 上传PDF文献")

    # 添加快速访问文献库的按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📋 查看我的文献库", key="library_main_btn", use_container_width=True):
            st.query_params["view"] = "library"
            st.rerun()

    st.divider()

    uploaded_file = st.file_uploader(
        "选择PDF文件",
        type="pdf",
        help="支持上传学术PDF文献"
    )

    if uploaded_file is None:
        st.info("📤 请上传PDF文件开始分析")
    else:
        st.success(f"✅ 已上传: {uploaded_file.name}")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"文件大小: {uploaded_file.size / 1024:.1f} KB")
        with col2:
            st.info(f"文件类型: {uploaded_file.type}")

        if st.button("📄 解析PDF结构", type="primary"):
            if not api_key:
                st.error("请先在侧边栏输入API密钥")
            else:
                parse_pdf_and_split(uploaded_file, api_key)


def parse_pdf_and_split(uploaded_file, api_key: str):
    """解析PDF并切分结构"""

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 解析PDF
        status_text.text("📄 正在解析PDF...")
        progress_bar.progress(20)

        if hasattr(uploaded_file, 'read'):
            pdf_bytes = uploaded_file.read()
        else:
            pdf_bytes = uploaded_file

        pdf_processor = PDFProcessor()
        full_text = pdf_processor.extract_text(pdf_bytes)

        if not full_text or len(full_text.strip()) < 100:
            st.error("PDF解析失败或内容过少，请检查文件")
            return

        st.info(f"✅ PDF解析成功，共提取 {len(full_text)} 字符")
        progress_bar.progress(50)

        # 切分论文结构
        status_text.text("🔍 AI正在识别论文结构...")
        progress_bar.progress(60)

        workflow = PaperSplitWorkflow()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        split_result = loop.run_until_complete(
            workflow.split_paper(full_text, api_key)
        )

        progress_bar.progress(100)
        status_text.text("✅ 结构识别完成！")

        # 保存到session state
        st.session_state.full_text = full_text
        st.session_state.split_result = split_result

        st.success("🎉 论文结构识别完成！请查看下一步")
        st.rerun()

    except Exception as e:
        st.error(f"处理失败: {str(e)}")
        logger.error(f"PDF处理失败: {e}", exc_info=True)


def render_structure_step(api_key: str):
    """步骤2：查看论文结构"""

    st.header("2️⃣ 论文结构地图")

    split_result = st.session_state.split_result
    if not split_result:
        st.error("请先上传PDF")
        return

    # 显示基本信息
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 📖 {split_result.title}")
        authors_str = ", ".join(split_result.authors) if split_result.authors else "未知"
        st.markdown(f"**作者**: {authors_str}")
    with col2:
        st.metric("总字符数", f"{split_result.total_chars:,}")
        st.metric("章节数量", len(split_result.sections))

    # 显示摘要
    if split_result.abstract:
        with st.expander("📝 摘要", expanded=True):
            st.markdown(split_result.abstract)

    # 显示章节结构
    st.markdown("### 📋 章节结构")

    for i, section in enumerate(split_result.sections):
        importance_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(section.importance, "⚪")

        with st.expander(f"{importance_icon} {section.name} ({section.importance}重要性)"):
            st.markdown(f"**内容摘要**: {section.content}")

            if section.key_points:
                st.markdown("**关键点**:")
                for point in section.key_points:
                    st.markdown(f"- {point}")

    # 继续按钮
    st.markdown("---")
    if st.button("➡️ 下一步：选择分析模式", type="primary"):
        st.rerun()


def render_analysis_mode_step(api_key: str):
    """步骤3：选择分析模式"""

    st.header("3️⃣ 选择分析模式")

    st.markdown("请选择您想要的分析方式：")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 🚀 快速分析
        **适合**: 快速了解论文全貌

        - 对全文进行三遍阅读法分析
        - 提取核心观点和贡献
        - 生成详细笔记
        - 约2-3分钟完成

        *推荐首次阅读使用*
        """)

        if st.button("选择快速分析", key="quick_analysis", type="primary"):
            run_quick_analysis(api_key)

    with col2:
        st.markdown("""
        ### 🔬 深度分析
        **适合**: 深入学习特定章节

        - 选择感兴趣的章节
        - 对每个章节进行详细分析
        - 学习写作技巧和句式
        - 可反复分析不同章节

        *推荐精读论文使用*
        """)

        if st.button("选择深度分析", key="deep_analysis"):
            st.session_state.analysis_mode = "deep"
            st.rerun()


def run_quick_analysis(api_key: str):
    """运行快速分析"""

    # 检查是否已经在分析中
    if st.session_state.get('analysis_in_progress', False):
        st.warning("⏳ 分析正在进行中，请稍候...")
        return

    # 检查是否已经有结果
    if st.session_state.full_analysis_result:
        st.info("✅ 分析已完成，请查看结果")
        return

    st.session_state.analysis_mode = "quick"
    st.session_state.analysis_in_progress = True

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.text("🤖 AI导师正在分析文献...")
        progress_bar.progress(10)

        workflow = LiteratureWorkFlow()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            workflow.execute(
                st.session_state.full_text,
                api_key,
                enable_teaching=True
            )
        )

        progress_bar.progress(100)
        status_text.text("✅ 分析完成！")

        st.session_state.full_analysis_result = result
        st.session_state.analysis_in_progress = False
        st.success("🎉 分析完成！")
        st.rerun()

    except Exception as e:
        st.session_state.analysis_in_progress = False
        st.error(f"分析失败: {str(e)}")
        logger.error(f"快速分析失败: {e}", exc_info=True)


def render_result_step(api_key: str):
    """步骤4：显示结果"""

    if st.session_state.analysis_mode == "quick":
        render_quick_result()
    else:
        render_deep_analysis(api_key)


def render_quick_result():
    """显示快速分析结果"""

    st.header("4️⃣ 分析结果")

    result = st.session_state.full_analysis_result
    if not result:
        st.error("分析结果不存在")
        return

    # 学习模式选择
    st.markdown("---")
    learning_mode = st.radio(
        "📖 选择学习模式",
        ["📚 分步学习模式（推荐新手）", "📋 完整查看模式"],
        help="分步学习模式会引导你逐步学习，完整查看模式可以一次性查看所有内容"
    )

    if learning_mode == "📚 分步学习模式（推荐新手）":
        render_step_by_step_learning(result)
    else:
        render_full_view(result)

    # 返回主页面按钮
    st.markdown("---")
    if st.button("🏠 返回主页面", key="back_to_main_quick", type="primary"):
        # 重置所有状态
        st.session_state.full_analysis_result = None
        st.session_state.split_result = None
        st.session_state.full_text = ''
        st.session_state.analysis_mode = None
        st.session_state.learning_step = 1
        st.rerun()


def render_step_by_step_learning(result: Dict[str, Any]):
    """分步学习模式"""

    # 初始化学习进度
    if 'learning_step' not in st.session_state:
        st.session_state.learning_step = 1

    # 学习步骤定义
    learning_steps = [
        {
            "step": 1,
            "title": "📖 阅读前准备",
            "icon": "📚",
            "description": "了解论文类型，明确阅读目标"
        },
        {
            "step": 2,
            "title": "🎯 第一遍：找战场",
            "icon": "🎯",
            "description": "快速了解论文的核心内容"
        },
        {
            "step": 3,
            "title": "🗺️ 第二遍：拆地图",
            "icon": "🗺️",
            "description": "深入理解论文的各个部分"
        },
        {
            "step": 4,
            "title": "🔗 第三遍：画连接",
            "icon": "🔗",
            "description": "将论文放入学术脉络中"
        },
        {
            "step": 5,
            "title": "✍️ 学习笔记",
            "icon": "✍️",
            "description": "生成详细的学习笔记"
        },
        {
            "step": 6,
            "title": "🎓 导师教学",
            "icon": "🎓",
            "description": "批判性思维和苏格拉底式提问"
        },
        {
            "step": 7,
            "title": "📝 实践任务",
            "icon": "📝",
            "description": "完成实践任务巩固学习"
        }
    ]

    # 显示学习进度
    st.markdown("### 📊 学习进度")
    progress = (st.session_state.learning_step - 1) / (len(learning_steps) - 1)
    st.progress(progress)
    st.markdown(f"当前进度: {st.session_state.learning_step} / {len(learning_steps)}")

    # 显示步骤导航
    st.markdown("---")
    cols = st.columns(len(learning_steps))
    for i, step_info in enumerate(learning_steps):
        with cols[i]:
            if st.session_state.learning_step > step_info["step"]:
                st.success(f"{step_info['icon']} 步骤{step_info['step']}")
            elif st.session_state.learning_step == step_info["step"]:
                st.info(f"{step_info['icon']} 步骤{step_info['step']}")
            else:
                st.markdown(f"{step_info['icon']} 步骤{step_info['step']}")
            st.markdown(f"<small>{step_info['title']}</small>", unsafe_allow_html=True)

    st.markdown("---")

    # 根据当前步骤显示内容
    if st.session_state.learning_step == 1:
        render_learning_step_1(result)
    elif st.session_state.learning_step == 2:
        render_learning_step_2(result)
    elif st.session_state.learning_step == 3:
        render_learning_step_3(result)
    elif st.session_state.learning_step == 4:
        render_learning_step_4(result)
    elif st.session_state.learning_step == 5:
        render_learning_step_5(result)
    elif st.session_state.learning_step == 6:
        render_learning_step_6(result)
    elif st.session_state.learning_step == 7:
        render_learning_step_7(result)


def render_learning_step_1(result: Dict[str, Any]):
    """步骤1：阅读前准备"""

    st.header("📖 步骤1：阅读前准备")
    st.markdown("*在开始深入阅读之前，先了解这篇论文的基本信息*")

    # 基本信息
    basic_info = result.get("basic_info", {})

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**标题**: {basic_info.get('title', '未知')}")
        authors = basic_info.get('authors', [])
        if isinstance(authors, list):
            authors_str = ", ".join(authors) if authors else "未知"
        else:
            authors_str = authors if authors else "未知"
        st.markdown(f"**作者**: {authors_str}")
        st.markdown(f"**期刊**: {basic_info.get('journal', '未知')} ({basic_info.get('year', '未知')})")
    with col2:
        st.markdown(f"**文献类型**: `{basic_info.get('document_type', '未知')}`")
        st.markdown(f"**研究领域**: {basic_info.get('research_field', '未知')}")

    st.info(f"💡 **一句话概括**: {basic_info.get('one_sentence_summary', '')}")

    # 阅读指南
    st.markdown("---")
    st.subheader("📚 阅读指南")

    notes = result.get("notes", {})
    reading_guide = notes.get("reading_guide", {})

    if reading_guide:
        st.markdown(f"**论文类型**: {reading_guide.get('paper_type', '未知')}")
        st.markdown(f"**阅读目标**: {reading_guide.get('reading_goal', '')}")

        st.markdown("#### 重点关注")
        focus_areas = reading_guide.get('focus_areas', [])
        for area in focus_areas:
            st.markdown(f"- {area}")

        st.markdown("#### 分步阅读策略")
        strategy = reading_guide.get('step_by_step_strategy', {})
        if strategy:
            st.markdown("**快速浏览**")
            st.markdown(strategy.get('quick_scan', ''))
            st.markdown("**精读引言**")
            st.markdown(strategy.get('intensive_reading_intro', ''))
            st.markdown("**方法部分**")
            st.markdown(strategy.get('method_section', ''))
            st.markdown("**结果和讨论**")
            st.markdown(strategy.get('results_discussion', ''))
            st.markdown("**批判性思考**")
            st.markdown(strategy.get('critical_thinking', ''))

        # 关键术语
        key_terms = reading_guide.get('key_terms', [])
        if key_terms:
            st.markdown("#### 📖 关键术语")
            for term_info in key_terms:
                with st.expander(f"🔍 {term_info.get('term', '')}"):
                    st.markdown(f"**定义**: {term_info.get('definition', '')}")
                    st.markdown(f"**例子**: {term_info.get('example', '')}")

    # 导航按钮
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步", disabled=True):
            pass
    with col2:
        if st.button("下一步 ➡️", type="primary"):
            st.session_state.learning_step = 2
            st.rerun()


def render_learning_step_2(result: Dict[str, Any]):
    """步骤2：第一遍阅读"""

    st.header("🎯 步骤2：第一遍 - 找战场")
    st.markdown("*快速了解这篇论文在研究什么、用什么方法、有什么贡献*")

    first_pass = result.get("first_pass", {})

    with st.expander("📍 研究现象", expanded=True):
        phenomenon = first_pass.get("phenomenon", {})
        st.markdown(f"**描述**: {phenomenon.get('description', '')}")
        
        plain_exp = phenomenon.get('plain_explanation', '')
        if plain_exp:
            st.info(f"💡 **通俗解释**: {plain_exp}")
        
        real_life = phenomenon.get('real_life_examples', [])
        if real_life:
            st.markdown("**生活实例**:")
            for ex in real_life:
                st.markdown(f"- {ex}")
        
        st.markdown(f"**重要性**: {phenomenon.get('importance', '')}")
        st.markdown(f"**背景**: {phenomenon.get('background', '')}")

    with st.expander("🔧 理论工具", expanded=True):
        tools = first_pass.get("tools", {})
        tf = tools.get("theoretical_framework", {})
        
        if isinstance(tf, dict):
            st.markdown(f"### 📚 理论框架: {tf.get('name', '')}")
            st.markdown(f"**创始人**: {tf.get('founder', '')}")
            st.markdown(f"**核心命题**: {tf.get('core_propositions', '')}")
            st.markdown(f"**解释的现象**: {tf.get('what_it_explains', '')}")
            st.markdown(f"**局限性**: {tf.get('limitations', '')}")
            st.markdown(f"**为什么适合本研究**: {tf.get('why_suitable', '')}")
        else:
            st.markdown(f"**理论框架**: {tf}")
        
        prev_theories = tools.get("previous_theories", [])
        if prev_theories and isinstance(prev_theories, list):
            st.markdown("### 📖 借鉴的前人理论")
            for theory in prev_theories:
                if isinstance(theory, dict):
                    st.markdown(f"- **{theory.get('name', '')}**: {theory.get('core_idea', '')}")
                else:
                    st.markdown(f"- {theory}")
        
        rm = tools.get("research_method", {})
        if isinstance(rm, dict):
            st.markdown("### 🔬 研究方法")
            st.markdown(f"**类型**: {rm.get('type', '')}")
            st.markdown(f"**为什么适合**: {rm.get('why_suitable', '')}")
            st.markdown(f"**优势**: {rm.get('advantages', '')}")
        else:
            st.markdown(f"**研究方法**: {rm}")
        
        ds = tools.get("data_source", {})
        if isinstance(ds, dict):
            st.markdown("### 📊 数据来源")
            st.markdown(f"**描述**: {ds.get('description', '')}")
            st.markdown(f"**代表性**: {ds.get('representativeness', '')}")
        else:
            st.markdown(f"**数据来源**: {ds}")

    key_concepts = first_pass.get("key_concepts", [])
    if key_concepts:
        with st.expander("🔑 关键概念详解", expanded=True):
            st.markdown("*这是新手最需要理解的部分！每个概念都有详细解释*")
            for i, concept in enumerate(key_concepts, 1):
                st.markdown(f"### 概念 {i}: {concept.get('name', '')}")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**学术定义**: {concept.get('academic_definition', '')}")
                    st.markdown(f"**本研究中的含义**: {concept.get('study_specific_meaning', '')}")
                with col2:
                    st.info(f"💡 **通俗解释**: {concept.get('plain_explanation', '')}")
                    st.success(f"🎯 **类比/例子**: {concept.get('analogy_or_example', '')}")
                st.markdown(f"**与相关概念的区别**: {concept.get('distinction_from_related', '')}")
                st.markdown(f"**如何测量**: {concept.get('how_measured', '')}")
                st.markdown("---")

    with st.expander("🏆 核心贡献"):
        contribution = first_pass.get("contribution", {})
        st.markdown(f"**主要发现**: {contribution.get('main_finding', '')}")
        st.markdown(f"**理论贡献**: {contribution.get('theoretical_contribution', '')}")
        st.markdown(f"**实践意义**: {contribution.get('practical_implication', '')}")

    wf = first_pass.get("writing_framework", {})
    if wf:
        with st.expander("✍️ 写作框架学习"):
            st.markdown(f"**标题设计**: {wf.get('title_analysis', '')}")
            if wf.get('title_why_good'):
                st.info(f"💡 **好在哪里**: {wf.get('title_why_good', '')}")
            st.markdown(f"**摘要结构**: {wf.get('abstract_structure', '')}")
            if wf.get('abstract_logic'):
                st.markdown(f"**组织逻辑**: {wf.get('abstract_logic', '')}")
            st.markdown(f"**关键词选择**: {wf.get('keywords_analysis', '')}")
            if wf.get('keywords_why'):
                st.markdown(f"**为什么选这几个**: {wf.get('keywords_why', '')}")
            st.markdown(f"**引言开篇**: {wf.get('introduction_opening', '')}")
            if wf.get('introduction_hook'):
                st.success(f"🎣 **钩子**: {wf.get('introduction_hook', '')}")

    ue = first_pass.get("useful_expressions", {})
    if ue:
        with st.expander("💬 值得学习的表达"):
            academic = ue.get("academic_sentences", [])
            if academic:
                st.markdown("### 学术表达句式")
                for item in academic:
                    if isinstance(item, dict):
                        st.markdown(f"- {item.get('sentence', '')}")
                        if item.get('why_good'):
                            st.markdown(f"  - 💡 **好在哪里**: {item.get('why_good', '')}")
                        if item.get('usage_scenario'):
                            st.markdown(f"  - 📝 **适用场景**: {item.get('usage_scenario', '')}")
                    else:
                        st.markdown(f"- {item}")
            
            transitions = ue.get("transition_sentences", [])
            if transitions:
                st.markdown("### 过渡句")
                for item in transitions:
                    if isinstance(item, dict):
                        st.markdown(f"- {item.get('sentence', '')}")
                        if item.get('why_good'):
                            st.markdown(f"  - 💡 **好在哪里**: {item.get('why_good', '')}")
                    else:
                        st.markdown(f"- {item}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步"):
            st.session_state.learning_step = 1
            st.rerun()
    with col2:
        if st.button("下一步 ➡️", type="primary"):
            st.session_state.learning_step = 3
            st.rerun()


def render_learning_step_3(result: Dict[str, Any]):
    """步骤3：第二遍阅读"""

    st.header("🗺️ 步骤3：第二遍 - 拆地图")
    st.markdown("*深入理解论文的各个部分，学习写作技巧*")

    second_pass = result.get("second_pass", {})

    rq = second_pass.get("research_question", {})
    with st.expander("❓ 研究问题", expanded=True):
        st.markdown(f"**原文摘录**: {rq.get('original_text', '')}")
        st.markdown(f"**写作技巧**: {rq.get('writing_technique', '')}")
        st.markdown(f"**学习要点**: {rq.get('learning_points', '')}")
        
        core_q = rq.get('core_question', '')
        if core_q:
            st.markdown("---")
            st.markdown("### 📋 研究问题层次分析")
            st.success(f"🎯 **核心研究问题**: {core_q}")
            
            sub_qs = rq.get('sub_questions', [])
            if sub_qs:
                st.markdown("**子问题**:")
                for sq in sub_qs:
                    st.markdown(f"- {sq}")
            
            logic = rq.get('question_logic', '')
            if logic:
                st.markdown(f"**问题逻辑关系**: {logic}")

    lr = second_pass.get("literature_review", {})
    with st.expander("📚 文献综述", expanded=True):
        st.markdown(f"**覆盖范围**: {lr.get('coverage', '')}")
        st.markdown(f"**组织结构**: {lr.get('organization', '')}")
        st.markdown(f"**缺口识别**: {lr.get('gap_identification', '')}")
        st.markdown(f"**缺口技巧**: {lr.get('gap_technique', '')}")
        
        topic_intro = lr.get('topic_introduction', '')
        if topic_intro:
            st.markdown("---")
            st.markdown("### ✍️ 文献综述写作技巧")
            st.markdown(f"**如何引出主题**: {topic_intro}")
            st.markdown(f"**如何评价前人**: {lr.get('evaluation_style', '')}")
            st.markdown(f"**过渡到自己研究**: {lr.get('transition_technique', '')}")

    method = second_pass.get("methodology", {})
    with st.expander("🔬 研究方法", expanded=True):
        st.markdown("*这是新手最需要详细学习的部分！*")
        
        rd = method.get("research_design", {})
        if isinstance(rd, dict):
            st.markdown("### 📐 研究设计")
            st.markdown(f"**类型**: {rd.get('type', '')}")
            st.markdown(f"**为什么选择**: {rd.get('why_chosen', '')}")
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ **优势**: {rd.get('strengths', '')}")
            with col2:
                st.warning(f"⚠️ **劣势**: {rd.get('weaknesses', '')}")
        else:
            st.markdown(f"**研究设计**: {rd}")
        
        variables = method.get("variables", {})
        if variables:
            st.markdown("### 📊 变量分析")
            
            iv = variables.get("independent", {})
            if isinstance(iv, dict):
                st.markdown(f"#### 自变量: {iv.get('name', '')}")
                st.markdown(f"- **操作化**: {iv.get('operationalization', '')}")
                st.markdown(f"- **测量方式**: {iv.get('measurement', '')}")
                if iv.get('explanation'):
                    st.info(f"💡 {iv.get('explanation', '')}")
            
            dv = variables.get("dependent", {})
            if isinstance(dv, dict):
                st.markdown(f"#### 因变量: {dv.get('name', '')}")
                st.markdown(f"- **测量方式**: {dv.get('measurement', '')}")
                if dv.get('explanation'):
                    st.info(f"💡 {dv.get('explanation', '')}")
            
            controls = variables.get("control", [])
            if controls:
                st.markdown("#### 控制变量")
                for cv in controls:
                    if isinstance(cv, dict):
                        st.markdown(f"- **{cv.get('name', '')}**: {cv.get('why_control', '')}")
                    else:
                        st.markdown(f"- {cv}")
        
        sampling = method.get("sampling", {})
        if isinstance(sampling, dict):
            st.markdown("### 👥 样本信息")
            st.markdown(f"**样本量**: {sampling.get('sample_size', '')}")
            st.markdown(f"**抽样方法**: {sampling.get('sampling_method', '')}")
            st.markdown(f"**代表性分析**: {sampling.get('representativeness', '')}")
        else:
            st.markdown(f"**抽样**: {sampling}")
        
        da = method.get("data_analysis", {})
        if isinstance(da, dict):
            st.markdown("### 📈 数据分析")
            st.markdown(f"**描述性统计**: {da.get('descriptive', '')}")
            st.markdown(f"**推断性统计**: {da.get('inferential', '')}")
            st.markdown(f"**统计软件**: {da.get('software', '')}")
        else:
            st.markdown(f"**数据分析**: {da}")
        
        wf = method.get("writing_features", {})
        if isinstance(wf, dict):
            st.markdown("### ✍️ 方法部分写作特点")
            patterns = wf.get('sentence_patterns', [])
            if patterns:
                st.markdown("**常用句式**:")
                for p in patterns:
                    st.markdown(f"- {p}")
            st.markdown(f"**过程描述**: {wf.get('process_description', '')}")

    findings = second_pass.get("findings", {})
    with st.expander("🔍 核心发现"):
        main_results = findings.get("main_results", [])
        if main_results and isinstance(main_results, list):
            st.markdown("### 主要发现")
            for i, r in enumerate(main_results, 1):
                if isinstance(r, dict):
                    st.markdown(f"#### 发现 {i}: {r.get('finding', '')}")
                    st.markdown(f"**详细描述**: {r.get('detail', '')}")
                    st.markdown(f"**作者解释**: {r.get('interpretation', '')}")
                else:
                    st.markdown(f"- {r}")
        else:
            st.markdown(f"**主要发现**: {findings.get('main_results', '')}")
        
        st.markdown(f"**原文摘录**: {findings.get('original_text', '')}")
        st.markdown(f"**假设检验结果**: {findings.get('hypothesis_test', '')}")
        
        inconsistency = findings.get('inconsistency_explanation', '')
        if inconsistency:
            st.warning(f"⚠️ **不一致解释**: {inconsistency}")
        
        ps = findings.get('presentation_style', {})
        if ps:
            st.markdown("---")
            st.markdown("### 📊 结果呈现方式")
            st.markdown(f"**图表**: {ps.get('figures_tables', '')}")
            st.markdown(f"**设计学习点**: {ps.get('design_learning', '')}")

    limitations = second_pass.get("limitations", {})
    with st.expander("⚠️ 局限与展望"):
        acknowledged = limitations.get("acknowledged_limitations", [])
        if isinstance(acknowledged, list):
            st.markdown("### 承认的局限性")
            for lim in acknowledged:
                st.markdown(f"- {lim}")
        else:
            st.markdown(f"**承认的局限性**: {acknowledged}")
        
        future = limitations.get("future_directions", [])
        if isinstance(future, list):
            st.markdown("### 未来研究方向")
            for fd in future:
                st.markdown(f"- {fd}")
        else:
            st.markdown(f"**未来方向**: {future}")
        
        st.markdown(f"**原文摘录**: {limitations.get('original_text', '')}")
        st.markdown(f"**谦虚表达方式**: {limitations.get('humble_expression', '')}")
        
        wt = limitations.get('writing_technique', '')
        if wt:
            st.info(f"💡 **写作技巧**: {wt}")

    wt = second_pass.get("writing_techniques", {})
    if wt:
        with st.expander("✍️ 写作技巧总结"):
            st.markdown(f"**段落结构**: {wt.get('paragraph_structure', '')}")
            
            transitions = wt.get("transition_methods", [])
            if transitions:
                st.markdown("**过渡方式**:")
                for t in transitions:
                    st.markdown(f"- {t}")
            
            expressions = wt.get("useful_expressions", [])
            if expressions:
                st.markdown("### 值得学习的表达")
                for item in expressions:
                    if isinstance(item, dict):
                        st.markdown(f"- {item.get('expression', '')}")
                        if item.get('why_good'):
                            st.markdown(f"  - 💡 **好在哪里**: {item.get('why_good', '')}")
                        if item.get('usage'):
                            st.markdown(f"  - 📝 **用法**: {item.get('usage', '')}")
                    else:
                        st.markdown(f"- {item}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步"):
            st.session_state.learning_step = 2
            st.rerun()
    with col2:
        if st.button("下一步 ➡️", type="primary"):
            st.session_state.learning_step = 4
            st.rerun()


def render_learning_step_4(result: Dict[str, Any]):
    """步骤4：第三遍阅读"""

    st.header("🔗 步骤4：第三遍 - 画连接")
    st.markdown("*将论文放入学术脉络中，理解其位置*")

    third_pass = result.get("third_pass", {})

    td = third_pass.get("theoretical_dialogue", {})
    with st.expander("🌐 理论对话", expanded=True):
        st.markdown(f"### 主要理论: {td.get('main_theory', '')}")
        
        theory_details = td.get("theory_details", {})
        if theory_details:
            st.markdown("#### 📚 理论详解")
            st.markdown(f"**创始人及背景**: {theory_details.get('founder', '')}")
            st.markdown(f"**核心观点**: {theory_details.get('core_propositions', '')}")
            st.markdown(f"**发展脉络**: {theory_details.get('development_stages', '')}")
            st.markdown(f"**重要变体**: {theory_details.get('important_variants', '')}")
            st.markdown(f"**局限性与批评**: {theory_details.get('limitations_criticisms', '')}")
        
        st.markdown(f"**论文在理论脉络中的位置**: {td.get('paper_position', '')}")
        
        pc = td.get("paper_contribution", {})
        if pc:
            st.markdown("---")
            st.markdown("#### 🎯 论文对理论的贡献")
            st.success(f"**贡献类型**: {pc.get('type', '')}")
            st.markdown(f"**具体说明**: {pc.get('details', '')}")

    me = third_pass.get("method_evaluation", {})
    with st.expander("� 研究方法评价"):
        strengths = me.get("strengths", [])
        if isinstance(strengths, list):
            st.markdown("### ✅ 方法优点")
            for s in strengths:
                st.markdown(f"- {s}")
        else:
            st.markdown(f"**优点**: {strengths}")
        
        limitations = me.get("limitations", [])
        if isinstance(limitations, list):
            st.markdown("### ⚠️ 方法局限性")
            for lim in limitations:
                st.markdown(f"- {lim}")
        else:
            st.markdown(f"**局限性**: {limitations}")
        
        improvements = me.get("improvement_suggestions", [])
        if improvements:
            st.markdown("### 💡 改进建议")
            for imp in improvements:
                if isinstance(imp, dict):
                    st.markdown(f"- **{imp.get('suggestion', '')}**: {imp.get('rationale', '')}")
                else:
                    st.markdown(f"- {imp}")
        
        transferable = me.get("transferable_applications", [])
        if transferable:
            st.markdown("### 🔄 可借鉴的应用领域")
            for ta in transferable:
                if isinstance(ta, dict):
                    st.markdown(f"- **{ta.get('field', '')}**: {ta.get('how', '')}")
                else:
                    st.markdown(f"- {ta}")

    fs = third_pass.get("finding_significance", {})
    with st.expander("🎯 核心发现的意义"):
        st.markdown(f"**理论意义**: {fs.get('theoretical_meaning', '')}")
        st.markdown(f"**实践价值**: {fs.get('practical_value', '')}")
        
        inspiration = fs.get("research_inspiration", [])
        if inspiration:
            st.markdown("### 💡 对后续研究的启发")
            for ins in inspiration:
                st.markdown(f"- {ins}")
        
        gen = fs.get("generalization", {})
        if gen:
            st.markdown("---")
            st.markdown("### 🌍 可推广性")
            st.markdown(f"**适用情境**: {gen.get('applicable_contexts', '')}")
            st.markdown(f"**边界条件**: {gen.get('boundary_conditions', '')}")

    tc = third_pass.get("theory_connection", {})
    with st.expander("🔗 理论连接", expanded=True):
        connection_type = tc.get("connection_type", "")
        if "支持" in connection_type:
            st.success(f"**连接类型**: {connection_type}")
        elif "修正" in connection_type:
            st.warning(f"**连接类型**: {connection_type}")
        elif "拓展" in connection_type:
            st.info(f"**连接类型**: {connection_type}")
        elif "挑战" in connection_type:
            st.error(f"**连接类型**: {connection_type}")
        else:
            st.markdown(f"**连接类型**: {connection_type}")
        
        st.markdown(f"**具体说明**: {tc.get('connection_details', '')}")
        st.markdown(f"**支持证据**: {tc.get('evidence_support', '')}")
        
        implications = tc.get('implications', '')
        if implications:
            st.markdown(f"**对理论发展的意义**: {implications}")

    rc = third_pass.get("research_connections", {})
    with st.expander("📚 研究脉络"):
        classic = rc.get("classic_studies", [])
        if classic:
            st.markdown("### 📖 对话的经典研究")
            for cs in classic:
                if isinstance(cs, dict):
                    st.markdown(f"- **{cs.get('study', '')}**: {cs.get('connection', '')}")
                else:
                    st.markdown(f"- {cs}")
        
        recent = rc.get("recent_studies", [])
        if recent:
            st.markdown("### 📰 呼应或对比的近期研究")
            for rs in recent:
                if isinstance(rs, dict):
                    st.markdown(f"- **{rs.get('study', '')}**: {rs.get('connection', '')}")
                else:
                    st.markdown(f"- {rs}")
        
        st.markdown(f"**在领域中的位置**: {rc.get('field_position', '')}")
        
        roadmap = rc.get("research_roadmap", {})
        if roadmap:
            st.markdown("---")
            st.markdown("### 🗺️ 研究脉络图")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**前人研究**\n\n{roadmap.get('previous', '')}")
            with col2:
                st.success(f"**本研究**\n\n{roadmap.get('current', '')}")
            with col3:
                st.warning(f"**后续方向**\n\n{roadmap.get('future', '')}")

    ri = third_pass.get("research_inspiration", {})
    with st.expander("💡 对你研究的启发"):
        qi = ri.get("question_inspiration", {})
        if isinstance(qi, dict):
            st.markdown("### ❓ 研究问题的启发")
            st.markdown(f"**启发**: {qi.get('insight', '')}")
            st.markdown(f"**如何借鉴**: {qi.get('how_to_borrow', '')}")
        else:
            st.markdown(f"**研究问题启发**: {qi}")
        
        mb = ri.get("method_borrowing", {})
        if isinstance(mb, dict):
            st.markdown("### 🔬 方法借鉴")
            st.markdown(f"**可以借鉴的方法**: {mb.get('what', '')}")
            st.markdown(f"**具体如何借鉴**: {mb.get('how', '')}")
        else:
            st.markdown(f"**方法借鉴**: {mb}")
        
        ta = ri.get("theory_application", {})
        if isinstance(ta, dict):
            st.markdown("### 📚 理论框架应用")
            st.markdown(f"**可以应用的理论**: {ta.get('what', '')}")
            st.markdown(f"**具体如何应用**: {ta.get('how', '')}")
        else:
            st.markdown(f"**理论框架应用**: {ta}")
        
        extensions = ri.get("extension_directions", [])
        if extensions:
            st.markdown("### 🚀 可延伸的研究方向")
            for i, ext in enumerate(extensions, 1):
                if isinstance(ext, dict):
                    st.markdown(f"#### 方向 {i}: {ext.get('direction', '')}")
                    st.markdown(f"- **为什么值得研究**: {ext.get('rationale', '')}")
                    st.markdown(f"- **可以怎么研究**: {ext.get('approach', '')}")
                else:
                    st.markdown(f"- {ext}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步"):
            st.session_state.learning_step = 3
            st.rerun()
    with col2:
        if st.button("下一步 ➡️", type="primary"):
            st.session_state.learning_step = 5
            st.rerun()


def render_learning_step_5(result: Dict[str, Any]):
    """步骤5：学习笔记"""

    st.header("✍️ 步骤5：学习笔记")
    st.markdown("*生成详细的学习笔记，记录关键收获*")

    notes = result.get("notes", {})

    # 阅读指南
    with st.expander("📖 阅读指南", expanded=True):
        guide = notes.get("reading_guide", {})
        st.markdown(f"**论文类型**: {guide.get('paper_type', '')}")
        st.markdown(f"**阅读目标**: {guide.get('reading_goal', '')}")

        st.markdown("**重点关注**:")
        for area in guide.get('focus_areas', []):
            st.markdown(f"- {area}")

    # 关键术语
    st.markdown("---")
    st.subheader("📚 关键术语")
    terms = guide.get('key_terms', [])
    for term_info in terms:
        with st.expander(f"🔍 {term_info.get('term', '')}"):
            st.markdown(f"**定义**: {term_info.get('definition', '')}")
            st.markdown(f"**例子**: {term_info.get('example', '')}")

    # 有用表达
    with st.expander("💬 有用表达"):
        expressions = notes.get("useful_expressions", {})
        st.markdown("**学术句式**:")
        for sent in expressions.get('academic_sentences', []):
            st.markdown(f"- {sent}")
        st.markdown(f"**使用场景**: {expressions.get('usage_scenarios', '')}")

    # 导航按钮
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步"):
            st.session_state.learning_step = 4
            st.rerun()
    with col2:
        if st.button("下一步 ➡️", type="primary"):
            st.session_state.learning_step = 6
            st.rerun()


def render_learning_step_6(result: Dict[str, Any]):
    """步骤6：导师教学"""

    st.header("🎓 步骤6：导师教学")
    st.markdown("*批判性思维和苏格拉底式提问*")

    teaching = result.get("teaching", {})

    # 批判性思维
    st.markdown("---")
    st.subheader("🧠 批判性思维训练")
    ct = teaching.get("critical_thinking", {})

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("🎯 观点质疑"):
            ac = ct.get("argument_critique", {})
            st.markdown(f"**核心观点**: {ac.get('core_claim', '')}")
            st.markdown(f"**证据充分性**: {ac.get('evidence_sufficiency', '')}")

    with col2:
        with st.expander("🔬 方法质疑"):
            mc = ct.get("method_critique", {})
            st.markdown(f"**设计合理性**: {mc.get('design_rationale', '')}")
            st.markdown(f"**样本代表性**: {mc.get('sample_representativeness', '')}")

    # 苏格拉底式提问
    with st.expander("🗣️ 苏格拉底式提问"):
        sq = teaching.get("socratic_questioning", {})
        questions = sq.get("questions", [])
        for i, q in enumerate(questions[:5], 1):
            st.markdown(f"**问题 {i}**: {q}")

    # 研究空白
    with st.expander("🔍 研究空白发现"):
        gaps = teaching.get("research_gap", {})
        st.markdown(f"**理论空白**: {gaps.get('theoretical_gap', '')}")
        st.markdown(f"**方法空白**: {gaps.get('methodological_gap', '')}")
        st.markdown(f"**实证空白**: {gaps.get('empirical_gap', '')}")

    # 导航按钮
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步"):
            st.session_state.learning_step = 5
            st.rerun()
    with col2:
        if st.button("下一步 ➡️", type="primary"):
            st.session_state.learning_step = 7
            st.rerun()


def render_learning_step_7(result: Dict[str, Any]):
    """步骤7：实践任务"""

    st.header("📝 步骤7：实践任务")
    st.markdown("*完成实践任务，巩固学习成果*")

    teaching = result.get("teaching", {})
    practice = teaching.get("practice_tasks", {})

    # 即时练习
    with st.expander("✏️ 即时练习", expanded=True):
        immediate = practice.get("immediate_practice", [])
        for i, task in enumerate(immediate, 1):
            st.markdown(f"**任务 {i}**: {task}")

    # 深度探索
    with st.expander("🔍 深度探索"):
        deep = practice.get("deep_exploration", [])
        for i, task in enumerate(deep, 1):
            st.markdown(f"**探索 {i}**: {task}")

    # 写作练习
    with st.expander("📝 写作练习"):
        writing = practice.get("writing_exercises", [])
        for i, task in enumerate(writing, 1):
            st.markdown(f"**练习 {i}**: {task}")

    # 完成学习
    st.markdown("---")
    st.success("🎉 恭喜！你已完成这篇论文的完整学习流程！")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步"):
            st.session_state.learning_step = 6
            st.rerun()
    with col2:
        if st.button("🏠 返回主页面", key="back_to_main_step7", type="primary"):
            # 重置所有状态
            st.session_state.full_analysis_result = None
            st.session_state.split_result = None
            st.session_state.full_text = ''
            st.session_state.analysis_mode = None
            st.session_state.learning_step = 1
            st.rerun()


def display_teaching_module(teaching: dict):
    """显示导师教学模块"""

    st.divider()
    st.header("🎓 导师教学模块")
    st.markdown("*以下内容由AI导师精心准备，帮助你深入学习和思考*")

    # 1. 批判性思维训练
    st.subheader("🧠 批判性思维训练")
    st.markdown("*学会质疑是做研究的第一步*")

    ct = teaching.get("critical_thinking", {})

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("🎯 观点质疑"):
            ac = ct.get("argument_critique", {})
            st.markdown(f"**核心观点**: {ac.get('core_claim', '')}")
            st.markdown(f"**证据充分性**: {ac.get('evidence_sufficiency', '')}")
            st.markdown(f"**其他解释**: {ac.get('alternative_explanations', '')}")

        with st.expander("📊 数据质疑"):
            dc = ct.get("data_critique", {})
            st.markdown(f"**数据可靠性**: {dc.get('data_reliability', '')}")
            st.markdown(f"**样本量评估**: {dc.get('sample_size', '')}")
            st.markdown(f"**选择性报告风险**: {dc.get('selective_reporting', '')}")

    with col2:
        with st.expander("🔬 方法质疑"):
            mc = ct.get("method_critique", {})
            st.markdown(f"**设计合理性**: {mc.get('design_rationale', '')}")
            st.markdown(f"**样本代表性**: {mc.get('sample_representativeness', '')}")
            st.markdown(f"**替代方法**: {mc.get('alternative_methods', '')}")

        with st.expander("🔗 逻辑质疑"):
            lc = ct.get("logic_critique", {})
            st.markdown(f"**前提假设**: {lc.get('assumptions', '')}")
            st.markdown(f"**推理跳跃**: {lc.get('reasoning_gaps', '')}")
            st.markdown(f"**过度推广风险**: {lc.get('overgeneralization', '')}")

    with st.expander("❓ 批判性思考题", expanded=True):
        questions = ct.get("critical_questions", [])
        for i, q in enumerate(questions, 1):
            st.markdown(f"**问题 {i}**: {q.get('question', '')}")
            st.markdown(f"💡 *思考提示: {q.get('hint', '')}*")
            st.markdown("")

    with st.expander("🔄 反例思考"):
        ce = ct.get("counterexample_thinking", {})
        st.markdown(f"**结论可能不成立的条件**: {ce.get('invalid_conditions', '')}")
        st.markdown(f"**可能的反例**: {ce.get('counterexamples', '')}")
        st.markdown(f"**边界条件**: {ce.get('boundary_conditions', '')}")

    # 2. 苏格拉底式提问
    st.divider()
    st.subheader("🗣️ 苏格拉底式提问")
    st.markdown("*通过问题引导你深入思考*")

    sq = teaching.get("socratic_questioning", {})

    question_tabs = st.tabs(["澄清性问题", "假设性问题", "证据性问题", "视角性问题", "推论性问题", "元认知问题"])

    question_types = [
        ("clarifying_questions", "澄清性问题", "帮助澄清概念和观点"),
        ("assumption_questions", "假设性问题", "帮助审视隐含假设"),
        ("evidence_questions", "证据性问题", "帮助评估证据"),
        ("perspective_questions", "视角性问题", "帮助拓展视野"),
        ("implication_questions", "推论性问题", "帮助思考意义"),
        ("metacognitive_questions", "元认知问题", "帮助反思思维过程")
    ]

    for i, (key, title, desc) in enumerate(question_types):
        with question_tabs[i]:
            st.markdown(f"*{desc}*")
            questions = sq.get(key, [])
            for q in questions:
                st.markdown(f"**{q.get('question', '')}**")
                st.markdown(f"- 目的: {q.get('purpose', '')}")
                st.markdown(f"- 预期启发: {q.get('expected_insight', '')}")
                st.markdown("")

    with st.expander("🛤️ 思考路径"):
        pathway = sq.get("thinking_pathway", {})
        st.markdown(f"**切入点**: {pathway.get('entry_point', '')}")
        st.markdown(f"**核心概念**: {', '.join(pathway.get('key_concepts', []))}")
        st.markdown(f"**思考步骤**: {' → '.join(pathway.get('thinking_steps', []))}")
        st.markdown(f"**最终问题**: {pathway.get('ultimate_question', '')}")

    # 3. 研究空白发现
    st.divider()
    st.subheader("🔍 研究空白发现")
    st.markdown("*从现有文献中发现可研究的问题*")

    rg = teaching.get("research_gap", {})

    gap_tabs = st.tabs(["理论空白", "方法空白", "实证空白", "实践空白", "跨学科空白", "趋势空白"])

    gap_types = [
        ("theory_gaps", "理论层面"),
        ("method_gaps", "方法层面"),
        ("empirical_gaps", "实证层面"),
        ("practical_gaps", "实践层面"),
        ("interdisciplinary_gaps", "跨学科层面"),
        ("trend_gaps", "趋势层面")
    ]

    for i, (key, title) in enumerate(gap_types):
        with gap_tabs[i]:
            gaps = rg.get(key, [])
            for gap in gaps:
                st.markdown(f"**{gap.get('gap', '')}**")
                st.markdown(f"- 详细描述: {gap.get('description', '')}")
                st.markdown(f"- 潜在研究问题: {gap.get('potential_research_questions', '')}")
                st.markdown("")


def render_full_view(result: Dict[str, Any]):
    """完整查看模式"""

    st.header("4️⃣ 完整查看模式")
    st.markdown("*一次性查看所有分析内容*")

    # 基本信息
    st.divider()
    st.header("📋 文献基本信息")
    basic_info = result.get("basic_info", {})

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**标题**: {basic_info.get('title', '未知')}")
        authors = basic_info.get('authors', [])
        if isinstance(authors, list):
            authors_str = ", ".join(authors) if authors else "未知"
        else:
            authors_str = authors if authors else "未知"
        st.markdown(f"**作者**: {authors_str}")
        st.markdown(f"**期刊**: {basic_info.get('journal', '未知')} ({basic_info.get('year', '未知')})")
    with col2:
        st.markdown(f"**文献类型**: `{basic_info.get('document_type', '未知')}`")
        st.markdown(f"**研究领域**: {basic_info.get('research_field', '未知')}")

    st.info(f"💡 **一句话概括**: {basic_info.get('one_sentence_summary', '')}")

    # 第一遍：找战场
    st.divider()
    st.header("🎯 第一遍：找战场")
    st.markdown("*快速了解这篇论文在研究什么、用什么方法、有什么贡献*")

    first_pass = result.get("first_pass", {})

    with st.expander("📍 研究现象", expanded=True):
        phenomenon = first_pass.get("phenomenon", {})
        st.markdown(f"**描述**: {phenomenon.get('description', '')}")
        st.markdown(f"**重要性**: {phenomenon.get('importance', '')}")
        st.markdown(f"**背景**: {phenomenon.get('background', '')}")

    with st.expander("🔧 理论工具"):
        tools = first_pass.get("tools", {})
        tf = tools.get("theoretical_framework", {})
        if isinstance(tf, dict):
            st.markdown(f"**理论框架**: {tf.get('name', '')}")
        else:
            st.markdown(f"**理论框架**: {tf}")
        
        rm = tools.get("research_method", {})
        if isinstance(rm, dict):
            st.markdown(f"**研究方法**: {rm.get('type', '')}")
        else:
            st.markdown(f"**研究方法**: {rm}")
        
        ds = tools.get("data_source", {})
        if isinstance(ds, dict):
            st.markdown(f"**数据来源**: {ds.get('description', '')}")
        else:
            st.markdown(f"**数据来源**: {ds}")

    with st.expander("🏆 核心贡献"):
        contribution = first_pass.get("contribution", {})
        st.markdown(f"**主要发现**: {contribution.get('main_finding', '')}")
        st.markdown(f"**理论贡献**: {contribution.get('theoretical_contribution', '')}")
        st.markdown(f"**实践意义**: {contribution.get('practical_significance', '')}")

    # 第二遍：拆地图
    st.divider()
    st.header("🗺️ 第二遍：拆作战地图")
    st.markdown("*深入理解论文的每个部分是如何运作的*")

    second_pass = result.get("second_pass", {})

    with st.expander("❓ 研究问题"):
        rq = second_pass.get("research_question", {})
        st.markdown(f"**问题提出**: {rq.get('question_statement', '')}")
        if rq.get('original_text'):
            st.markdown(f"**原文摘录**: _{rq.get('original_text')}_")
        st.markdown(f"**写作技巧**: {rq.get('writing_technique', '')}")

    with st.expander("📚 文献综述"):
        lr = second_pass.get("literature_review", {})
        st.markdown(f"**组织方式**: {lr.get('organization', '')}")
        st.markdown(f"**核心文献**: {lr.get('core_literature', '')}")
        if lr.get('gap_statement'):
            st.markdown(f"**研究空白**: _{lr.get('gap_statement')}_")

    with st.expander("🔬 研究方法"):
        method = second_pass.get("methodology", {})
        st.markdown(f"**研究设计**: {method.get('design', '')}")
        st.markdown(f"**变量测量**: {method.get('variables', '')}")
        st.markdown(f"**样本**: {method.get('sample', '')}")
        st.markdown(f"**分析方法**: {method.get('analysis', '')}")

    with st.expander("📊 核心发现"):
        findings = second_pass.get("findings", {})
        st.markdown(f"**主要结果**: {findings.get('main_results', '')}")
        if findings.get('original_text'):
            st.markdown(f"**原文摘录**: _{findings.get('original_text')}_")

    # 第三遍：画连接
    st.divider()
    st.header("🔗 第三遍：画火力连接图")
    st.markdown("*把论文放入更大的学术脉络中*")

    third_pass = result.get("third_pass", {})

    with st.expander("💬 理论对话"):
        td = third_pass.get("theoretical_dialogue", {})
        st.markdown(f"**对话理论**: {td.get('theory', '')}")
        st.markdown(f"**理论位置**: {td.get('position', '')}")

    with st.expander("⚖️ 方法评价"):
        me = third_pass.get("method_evaluation", {})
        st.markdown(f"**优点**: {me.get('strengths', '')}")
        st.markdown(f"**局限**: {me.get('limitations', '')}")
        st.markdown(f"**改进建议**: {me.get('improvements', '')}")

    with st.expander("💡 研究启发"):
        ri = third_pass.get("research_inspiration", {})
        st.markdown(f"**方法借鉴**: {ri.get('method_inspiration', '')}")
        st.markdown(f"**理论启发**: {ri.get('theory_inspiration', '')}")
        st.markdown(f"**可研究方向**: {ri.get('future_directions', '')}")

    # 笔记
    st.divider()
    st.header("📝 详细笔记")

    notes = result.get("notes", {})

    st.subheader("📌 三句话笔记")
    three_notes = notes.get("three_sentence_notes", {})
    st.markdown(f"**这篇在说什么？** {three_notes.get('summary', '')}")
    st.markdown(f"**跟我有什么关系？** {three_notes.get('relation', '')}")
    st.markdown(f"**让我想反驳什么？** {three_notes.get('critique', '')}")

    with st.expander("📖 详细摘要"):
        st.markdown(notes.get("detailed_summary", ""))

    # 写作素材
    st.subheader("✍️ 可借鉴的写作素材")
    materials = notes.get("writing_materials", {})

    with st.expander("📖 学术表达句式库", expanded=True):
        expressions = materials.get("academic_expressions", [])
        if expressions:
            for i, expr in enumerate(expressions, 1):
                st.markdown(f"**句式 {i}**")
                st.markdown(f"- 原句: _{expr.get('original', '')}_")
                st.markdown(f"- 用法: {expr.get('usage', '')}")
                st.markdown(f"- 仿写: {expr.get('imitation', '')}")
                st.markdown("---")
        else:
            st.markdown("暂无数据")

    # ========== 导师教学模块 ==========
    if result.get("enable_teaching") and "teaching" in result:
        display_teaching_module(result.get("teaching", {}))


def render_deep_analysis(api_key: str):
    """深度分析界面"""

    st.header("4️⃣ 深度分析")

    split_result = st.session_state.split_result
    if not split_result:
        st.error("请先上传PDF")
        return

    # 章节选择
    st.markdown("### 选择要深度分析的章节")

    section_names = [s.name for s in split_result.sections]
    selected_sections = st.multiselect(
        "选择章节（可多选）",
        section_names,
        default=st.session_state.selected_sections
    )

    if selected_sections != st.session_state.selected_sections:
        st.session_state.selected_sections = selected_sections

    # 显示已选章节
    if selected_sections:
        st.markdown(f"已选择 **{len(selected_sections)}** 个章节")

        # 分析按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 分析选中章节", type="primary"):
                analyze_selected_sections(api_key, selected_sections)
        with col2:
            if st.button("🗑️ 清除分析结果"):
                st.session_state.section_analysis = {}
                st.rerun()

    # 显示分析结果
    display_section_analysis_results()


def analyze_selected_sections(api_key: str, selected_sections: List[str]):
    """分析选中的章节"""

    # 检查是否已经在分析中
    if st.session_state.get('section_analysis_in_progress', False):
        st.warning("⏳ 分析正在进行中，请稍候...")
        return

    st.session_state.section_analysis_in_progress = True

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        workflow = PaperSplitWorkflow()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        total = len(selected_sections)

        for i, section_name in enumerate(selected_sections):
            status_text.text(f"🔍 正在分析: {section_name} ({i+1}/{total})...")
            progress_bar.progress(int((i / total) * 100))

            result = loop.run_until_complete(
                workflow.analyze_section(
                    st.session_state.full_text,
                    section_name,
                    api_key,
                    analysis_depth="deep"
                )
            )

            st.session_state.section_analysis[section_name] = result

        progress_bar.progress(100)
        status_text.text("✅ 分析完成！")
        st.session_state.section_analysis_in_progress = False
        st.success(f"🎉 已完成 {total} 个章节的分析")
        st.rerun()

    except Exception as e:
        st.session_state.section_analysis_in_progress = False
        st.error(f"分析失败: {str(e)}")
        logger.error(f"章节分析失败: {e}", exc_info=True)


def display_section_analysis_results():
    """显示章节分析结果"""

    section_analysis = st.session_state.section_analysis
    if not section_analysis:
        st.info("请选择章节并点击分析按钮")
        return

    st.markdown("### 📊 分析结果")

    for section_name, result in section_analysis.items():
        with st.expander(f"📄 {section_name}", expanded=True):
            # 根据章节类型显示不同内容
            if "background_analysis" in result:
                display_introduction_analysis(result)
            elif "organization" in result:
                display_literature_review_analysis(result)
            elif "design" in result:
                display_methodology_analysis(result)
            elif "main_results" in result:
                display_results_analysis(result)
            else:
                display_generic_section_analysis(result)


def display_introduction_analysis(result: dict):
    """显示引言分析"""

    st.markdown("#### 研究背景分析")
    bg = result.get("background_analysis", {})
    st.markdown(f"**领域现状**: {bg.get('current_status', '')}")
    st.markdown(f"**核心问题**: {bg.get('core_issues', '')}")
    st.markdown(f"**问题引出方式**: {bg.get('question_introduction', '')}")

    st.markdown("#### 研究问题分析")
    rq = result.get("research_question_analysis", {})
    st.markdown(f"**核心问题**: {rq.get('core_question', '')}")
    st.markdown(f"**研究假设**: {rq.get('hypothesis', '')}")
    st.markdown(f"**研究目的**: {rq.get('purpose', '')}")

    st.markdown("#### 可借鉴句式")
    expressions = result.get("useful_expressions", [])
    for expr in expressions:
        st.markdown(f"- {expr}")


def display_literature_review_analysis(result: dict):
    """显示文献综述分析"""

    st.markdown("#### 文献组织")
    st.markdown(f"**组织方式**: {result.get('organization', '')}")
    st.markdown(f"**分类标准**: {result.get('classification_criteria', '')}")

    st.markdown("#### 研究空白")
    st.markdown(f"**识别的空白**: {result.get('research_gaps', '')}")
    st.markdown(f"**论证方式**: {result.get('gap_argumentation', '')}")


def display_methodology_analysis(result: dict):
    """显示方法分析"""

    st.markdown("#### 研究设计")
    st.markdown(f"**设计类型**: {result.get('design', '')}")
    st.markdown(f"**选择理由**: {result.get('design_rationale', '')}")

    st.markdown("#### 数据收集")
    st.markdown(f"**数据来源**: {result.get('data_source', '')}")
    st.markdown(f"**样本**: {result.get('sample', '')}")

    st.markdown("#### 分析方法")
    st.markdown(f"**分析方法**: {result.get('analysis_method', '')}")


def display_results_analysis(result: dict):
    """显示结果分析"""

    st.markdown("#### 主要发现")
    st.markdown(f"**核心结果**: {result.get('main_results', '')}")

    st.markdown("#### 结果呈现")
    st.markdown(f"**呈现方式**: {result.get('presentation_method', '')}")
    st.markdown(f"**图表使用**: {result.get('figure_usage', '')}")


def display_generic_section_analysis(result: dict):
    """显示通用章节分析"""

    st.markdown("#### 主要内容")
    main_content = result.get("main_content", {})
    for key, value in main_content.items():
        st.markdown(f"**{key}**: {value}")

    st.markdown("#### 关键点")
    key_points = result.get("key_points", [])
    for point in key_points:
        st.markdown(f"- {point}")

    st.markdown("#### 可借鉴表达")
    expressions = result.get("useful_expressions", [])
    for expr in expressions:
        st.markdown(f"- {expr}")


def export_result(result: dict, format: str):
    """导出结果"""
    try:
        export_manager = ExportManager()

        if format == "JSON":
            file_path = export_manager.export_to_json(result)
        elif format == "Markdown":
            file_path = export_manager.export_to_markdown(result)
        else:
            file_path = export_manager.export_to_txt(result)

        # 保存成功信息到session state
        st.session_state.export_success = os.path.basename(file_path)
        logger.info(f"导出成功: {file_path}")

        # 提供下载按钮
        with open(file_path, "rb") as f:
            st.download_button(
                label=f"📥 下载 {format} 文件",
                data=f,
                file_name=os.path.basename(file_path),
                mime="application/octet-stream",
                key=f"download_{format}"
            )

    except Exception as e:
        st.error(f"导出失败: {e}")
        logger.error(f"导出失败: {e}", exc_info=True)


def save_to_library():
    """保存到文献库"""
    try:
        # 创建文献库目录
        library_dir = "project/library"
        os.makedirs(library_dir, exist_ok=True)

        if st.session_state.full_analysis_result:
            # 保存快速分析结果
            result = st.session_state.full_analysis_result
            title = result.get("basic_info", {}).get("title", "未命名")
            # 生成文件名
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}_{result.get('analysis_time', '')}.json"
            filepath = os.path.join(library_dir, filename)
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            st.success(f"✅ 已保存到文献库")
            logger.info(f"保存到文献库成功: {filepath}")
        else:
            # 保存论文结构
            split_result = st.session_state.split_result
            title = split_result.title or "未命名"
            # 生成文件名
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}_structure.json"
            filepath = os.path.join(library_dir, filename)
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "type": "paper_structure",
                    "title": split_result.title,
                    "authors": ", ".join(split_result.authors) if split_result.authors else "",
                    "abstract": split_result.abstract,
                    "sections": [s.model_dump() for s in split_result.sections],
                    "total_chars": split_result.total_chars
                }, f, ensure_ascii=False, indent=2)
            
            st.success(f"✅ 已保存到文献库")
            logger.info(f"保存到文献库成功: {filepath}")

    except Exception as e:
        st.error(f"保存失败: {e}")
        logger.error(f"保存到文献库失败: {e}", exc_info=True)


def load_analysis_from_files() -> List[Dict[str, Any]]:
    """从文件系统加载分析结果"""
    analysis_files = []
    
    # 从 work_dir 加载
    work_dir = "project/work_dir"
    pattern = os.path.join(work_dir, "lit_*/analysis_result.json")
    logger.info(f"查找分析文件，模式: {pattern}")
    
    for json_file in glob.glob(pattern):
        try:
            logger.info(f"加载文件: {json_file}")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 添加文件路径信息
                data['_source_file'] = json_file
                data['_source_type'] = 'file'
                analysis_files.append(data)
                logger.info(f"成功加载: {data.get('basic_info', {}).get('title', '未命名')}")
        except Exception as e:
            logger.error(f"加载分析文件失败 {json_file}: {e}")
    
    # 从 library_dir 加载
    library_dir = "project/library"
    if os.path.exists(library_dir):
        pattern = os.path.join(library_dir, "*.json")
        logger.info(f"查找文献库文件，模式: {pattern}")
        
        for json_file in glob.glob(pattern):
            try:
                logger.info(f"加载文件: {json_file}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 添加文件路径信息
                    data['_source_file'] = json_file
                    data['_source_type'] = 'library'
                    analysis_files.append(data)
                    logger.info(f"成功加载: {data.get('basic_info', {}).get('title', '未命名')}")
            except Exception as e:
                logger.error(f"加载文献库文件失败 {json_file}: {e}")
    
    # 按分析时间排序（最新的在前）
    analysis_files.sort(key=lambda x: x.get('analysis_time', ''), reverse=True)
    logger.info(f"共加载 {len(analysis_files)} 个分析文件")
    return analysis_files


def show_library():
    """显示文献库"""
    st.subheader("📋 我的文献库")

    try:
        # 从文件系统获取
        library_items = load_analysis_from_files()
        logger.info(f"从文件系统加载 {len(library_items)} 条记录")
        
        # 合并数据
        all_items = []
        
        # 添加文件系统中的项目
        for i, data in enumerate(library_items):
            basic_info = data.get('basic_info', {})
            all_items.append({
                'id': f"file_{i}",
                'title': basic_info.get('title', '未命名'),
                'created_at': data.get('analysis_time', ''),
                'content': data,
                'source': 'file'
            })

        logger.info(f"总共 {len(all_items)} 条文献记录")

        # 检查是否有选中的文献（通过 query_params）
        selected_idx = st.query_params.get("selected")
        if selected_idx is not None:
            try:
                idx = int(selected_idx)
                if 0 <= idx < len(all_items):
                    item = all_items[idx]
                    content = item.get('content', {})
                    content_type = content.get('type', 'unknown')
                    
                    logger.info(f"处理选中的文献: idx={idx}, type={content_type}")
                    
                    if content_type == 'paper_structure':
                        st.session_state.split_result = content
                        st.session_state.full_text = content.get('full_text', '')
                        st.session_state.full_analysis_result = None
                        st.session_state.analysis_mode = None
                    else:
                        st.session_state.full_analysis_result = content
                        st.session_state.split_result = None
                        st.session_state.full_text = ''
                        st.session_state.analysis_mode = "quick"
                    
                    st.session_state.show_library = False
                    # 清除 query_params
                    if "view" in st.query_params:
                        del st.query_params["view"]
                    if "selected" in st.query_params:
                        del st.query_params["selected"]
                    st.rerun()
            except (ValueError, IndexError) as e:
                logger.error(f"处理选中文献失败: {e}")

        if all_items:
            st.markdown(f"共 **{len(all_items)}** 篇文献")
            logger.info("开始渲染文献列表")
            
            for idx, item in enumerate(all_items):
                content = item.get('content', {})
                content_type = content.get('type', 'unknown')
                source = item.get('source', 'unknown')
                
                logger.info(f"渲染文献: idx={idx}, type={content_type}, source={source}")
                
                # 根据类型显示不同的信息
                if content_type == 'paper_structure':
                    title = content.get('title', '未命名')
                    authors = content.get('authors', '未知')
                    if isinstance(authors, list):
                        authors = ", ".join(authors) if authors else "未知"
                    subtitle = f"{authors} | {len(content.get('sections', []))} 个章节"
                    icon = "📄"
                else:
                    # 对于没有 type 字段的分析结果，从 basic_info 获取信息
                    basic_info = content.get('basic_info', {})
                    title = basic_info.get('title', '未命名')
                    authors = basic_info.get('authors', '未知')
                    if isinstance(authors, list):
                        authors = ", ".join(authors) if authors else "未知"
                    subtitle = f"{authors} | 完整分析"
                    icon = "📚"
                
                # 显示来源标签
                source_tag = "💾 数据库" if source == 'database' else "📁 文件"

                logger.info(f"显示文献: {title}")
                
                # 使用容器来显示文献信息
                st.markdown(f"### {icon} **{title}** ({source_tag})")
                st.markdown(f"*{subtitle}*")
                st.markdown(f"📅 保存时间: {item.get('created_at', '')}")
                
                # 按钮放在 expander 外部
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    if st.button("📖 查看详情", key=f"view_{idx}"):
                        logger.info(f"点击查看详情: idx={idx}, title={title}")
                        # 使用 query_params 来传递选中的索引
                        st.query_params["selected"] = str(idx)
                        st.rerun()
                
                with col2:
                    if st.button("📥 导出", key=f"export_{idx}"):
                        export_format = st.selectbox(
                            "选择导出格式",
                            ["JSON", "Markdown", "TXT"],
                            key=f"export_format_{idx}"
                        )
                        if st.button("确认导出", key=f"confirm_export_{idx}"):
                            with st.spinner("正在导出..."):
                                export_result(content, export_format)
                
                with col3:
                    if st.button("🗑️ 删除", key=f"delete_{idx}"):
                        # 从文件系统删除
                        source_file = content.get('_source_file', '')
                        if source_file and os.path.exists(source_file):
                            os.remove(source_file)
                            st.success("✅ 已删除")
                            st.rerun()
                
                st.markdown("---")
        else:
            st.info("📭 文献库为空")
            st.markdown("""
            **开始分析文献吧！**
            
            1. 上传PDF文件
            2. 选择分析模式
            3. 查看分析结果
            4. 保存到文献库
            """)
    except Exception as e:
        st.warning(f"⚠️ 获取文献库失败: {e}")
        logger.error(f"获取文献库失败: {e}", exc_info=True)
