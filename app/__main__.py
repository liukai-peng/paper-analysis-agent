"""
直接运行app模块的入口
使用方法: python -m app
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入主程序
from app.main import *

# Streamlit会自动运行main.py中的代码
