"""
文献解读Agent系统启动入口
解决Python模块路径问题
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并运行主程序
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys
    
    # 设置Streamlit参数
    sys.argv = [
        "streamlit",
        "run",
        "app/main.py",
        "--server.port=8502",
        "--server.address=localhost"
    ]
    
    # 启动Streamlit
    stcli.main()