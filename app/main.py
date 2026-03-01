import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from app.utils.config_manager import config_manager
from app.ui_modules.paper_split_page import render_paper_split_page

# 页面配置
st.set_page_config(
    page_title="文献解读Agent系统",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 获取API密钥
api_key = config_manager.get_api_key("deepseek")

# 主内容区 - 使用新的论文切分页面
render_paper_split_page(api_key)