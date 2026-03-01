import streamlit as st
import os
import json
from datetime import datetime
from app.core.workflow import LiteratureWorkFlow
from app.utils.log_util import logger
import fitz

# 初始化数据文件
LITERATURE_NOTES_FILE = "literature_notes.json"
ACADEMIC_CORPUS_FILE = "academic_corpus.json"
REVIEWS_FILE = "reviews.xlsx"

# 初始化数据文件
if not os.path.exists(LITERATURE_NOTES_FILE):
    with open(LITERATURE_NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

if not os.path.exists(ACADEMIC_CORPUS_FILE):
    with open(ACADEMIC_CORPUS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "引言": [],
            "文献综述": [],
            "研究方法": [],
            "数据分析": [],
            "讨论": [],
            "结论": []
        }, f, ensure_ascii=False, indent=2)

# 侧边栏导航
with st.sidebar:
    st.title("🎓 文献解读Agent")
    st.markdown("---")
    
    # API密钥输入
    api_key = st.text_input("🔑 Deepseek API密钥", type="password", help="用于大模型自动分析文献")
    
    if not api_key:
        st.warning("⚠️ 请输入API密钥以使用AI自动分析功能")
    
    st.markdown("---")
    
    page = st.radio(
        "选择功能模块",
        ["🏠 首页", "📚 文献分析", "📝 知识库管理"]
    )

# 首页
if page == "🏠 首页":
    st.title("🎓 文献解读Agent系统")
    st.markdown("### 基于多Agent协作的智能文献分析系统")
    
    st.markdown("---")
    st.markdown("## 🚀 系统架构")
    
    st.markdown("""
    ```
    ┌─────────────────────────────────────────────────────────────┐
    │                    LiteratureAgent Workflow                 │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  PDF输入 → CoordinatorAgent → FirstPassAgent → SecondPassAgent
    │                    ↓               ↓                ↓
    │              识别文献类型      找战场(5秒)       拆地图(30秒)
    │                                     ↓                ↓
    │                              FirstPassToSecondPass  SecondPassToThirdPass
    │                                                         ↓
    │                                               ThirdPassAgent
    │                                                       ↓
    │                                              画连接(15秒)
    │                                                       ↓
    │                                              NoteGeneratorAgent
    │                                                       ↓
    │                                              三句话笔记
    │                                                       ↓
    │                                              保存到知识库
    └─────────────────────────────────────────────────────────────┘
    ```
    """)
    
    st.markdown("---")
    st.markdown("## 📋 功能说明")
    st.markdown("1. **文献分析** - 上传PDF，AI自动完成三遍阅读法分析")
    st.markdown("2. **知识库管理** - 管理文献笔记、学术语料和审稿意见")
    st.markdown("3. **AI自动分析** - 大模型完全代替人工分析")

# 文献分析页面
elif page == "📚 文献分析":
    st.title("📚 文献分析")
    st.markdown("### AI自动完成三遍阅读法分析")
    
    # 文件上传
    uploaded_file = st.file_uploader("📁 上传PDF文件", type="pdf")
    
    if uploaded_file:
        st.success(f"✅ 成功上传: {uploaded_file.name}")
        
        # 解析PDF
        with st.spinner("正在解析PDF..."):
            try:
                doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                doc.close()
                
                st.info(f"✅ PDF解析完成！共 {len(full_text)} 字符")
                
                # 显示解析后的文本
                with st.expander("📄 查看解析后的文本"):
                    st.text_area("PDF全文", full_text, height=300, key="pdf_full_text")
                
                # AI分析按钮
                if st.button("🤖 AI自动分析（三遍阅读法）", type="primary"):
                    if not api_key:
                        st.error("请先输入API密钥")
                    else:
                        with st.spinner("AI正在分析文献...这可能需要1-2分钟"):
                            try:
                                workflow = LiteratureWorkFlow()
                                result = await workflow.execute(full_text, api_key)
                                
                                # 显示分析结果
                                st.divider()
                                st.header("🔍 分析结果 - 第一遍：找战场")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown("#### 📝 现象")
                                    st.write(result["first_pass"]["phenomenon"])
                                with col2:
                                    st.markdown("#### 🔧 工具")
                                    st.write(result["first_pass"]["tools"])
                                with col3:
                                    st.markdown("#### 🎯 贡献")
                                    st.write(result["first_pass"]["contribution"])
                                
                                st.divider()
                                st.header("🗺️ 分析结果 - 第二遍：拆作战地图")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("#### 研究问题提出")
                                    st.text_area("", result["second_pass"]["research_question"], height=150, disabled=True, key="research_question")
                                    st.markdown("#### 核心发现总结")
                                    st.text_area("", result["second_pass"]["core_finding"], height=150, disabled=True, key="core_finding")
                                with col2:
                                    st.markdown("#### 前人不足总结")
                                    st.text_area("", result["second_pass"]["literature_gap"], height=150, disabled=True, key="literature_gap")
                                    st.markdown("#### 局限与展望")
                                    st.text_area("", result["second_pass"]["limitations"], height=150, disabled=True, key="limitations")
                                
                                st.divider()
                                st.header("🎯 分析结果 - 第三遍：画火力连接图")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown("#### 📖 前人理论")
                                    st.write(result["third_pass"]["previous_theory"])
                                with col2:
                                    st.markdown("#### 🔬 本文方法")
                                    st.write(result["third_pass"]["methods"])
                                with col3:
                                    st.markdown("#### 🔍 本文发现")
                                    st.write(result["third_pass"]["findings"])
                                
                                st.markdown("#### 🔗 理论连接")
                                st.info(f"**连接类型**: {result['third_pass']['connection_type']}")
                                st.text_area("连接说明", result["third_pass"]["connection_details"], height=100, disabled=True, key="connection_details")
                                
                                st.divider()
                                st.header("📝 文献笔记")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown("#### 这篇在说什么？")
                                    st.write(result["notes"]["summary"])
                                with col2:
                                    st.markdown("#### 这篇跟我有什么关系？")
                                    st.write(result["notes"]["relation"])
                                with col3:
                                    st.markdown("#### 这篇让我想反驳什么？")
                                    st.write(result["notes"]["critique"])
                                
                                # 保存到文献笔记库
                                if st.button("💾 保存到文献笔记库"):
                                    with open(LITERATURE_NOTES_FILE, "r", encoding="utf-8") as f:
                                        notes = json.load(f)
                                    
                                    new_note = {
                                        "id": len(notes) + 1,
                                        "title": result["title"],
                                        "document_type": result["document_type"],
                                        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "first_pass": result["first_pass"],
                                        "second_pass": result["second_pass"],
                                        "third_pass": result["third_pass"],
                                        "my_notes": {
                                            "summary": result["notes"]["summary"],
                                            "relation": result["notes"]["relation"],
                                            "critique": result["notes"]["critique"]
                                        }
                                    }
                                    
                                    notes.append(new_note)
                                    
                                    with open(LITERATURE_NOTES_FILE, "w", encoding="utf-8") as f:
                                        json.dump(notes, f, ensure_ascii=False, indent=2)
                                    
                                    st.success("✅ 保存成功！")
                                    
                            except Exception as e:
                                st.error(f"分析失败: {e}")
                                logger.error(f"分析失败: {e}")
            except Exception as e:
                st.error(f"PDF解析失败: {e}")
                logger.error(f"PDF解析失败: {e}")

# 知识库管理页面
elif page == "📝 知识库管理":
    st.title("📝 知识库管理")
    
    # 文献笔记库
    st.markdown("## 📚 文献笔记库")
    with open(LITERATURE_NOTES_FILE, "r", encoding="utf-8") as f:
        notes = json.load(f)
    
    st.info(f"共 {len(notes)} 篇文献笔记")
    
    for i, note in enumerate(notes):
        with st.expander(f"📄 {note.get('title', '未知标题')} ({note.get('document_type', '未知类型')})"):
            st.markdown(f"**分析日期**: {note.get('analysis_date', '未知')}")
            st.markdown("---")
            
            st.markdown("### 📝 我的笔记")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**这篇在说什么？**")
                st.write(note['my_notes']['summary'])
            with col2:
                st.markdown("**这篇跟我有什么关系？**")
                st.write(note['my_notes']['relation'])
            with col3:
                st.markdown("**这篇让我想反驳什么？**")
                st.write(note['my_notes']['critique'])
            
            if st.button(f"删除笔记 {i+1}"):
                notes.pop(i)
                with open(LITERATURE_NOTES_FILE, "w", encoding="utf-8") as f:
                    json.dump(notes, f, ensure_ascii=False, indent=2)
                st.success("✅ 删除成功！")
                st.experimental_rerun()
    
    st.markdown("---")
    
    # 学术语料库
    st.markdown("## 📖 学术语料库")
    with open(ACADEMIC_CORPUS_FILE, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    
    # 显示现有模板
    for category, templates in corpus.items():
        st.markdown(f"### {category}")
        for j, template in enumerate(templates):
            st.text_area(f"模板 {j+1}", template, height=80, key=f"{category}_{j}")
    
    # 添加新模板
    with st.expander("➕ 添加新模板"):
        category = st.selectbox("选择分类", list(corpus.keys()))
        new_template = st.text_area("新模板内容", height=100, key="new_template")
        if st.button("添加模板"):
            corpus[category].append(new_template)
            with open(ACADEMIC_CORPUS_FILE, "w", encoding="utf-8") as f:
                json.dump(corpus, f, ensure_ascii=False, indent=2)
            st.success("✅ 添加成功！")
            st.experimental_rerun()

st.markdown("---")
st.markdown("💡 **记住**：学术写作不是创作，而是组装。从输入到输出，建立你的学术工作流！")