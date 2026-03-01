@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 设置Python路径
set PYTHONPATH=%cd%;%PYTHONPATH%

REM 启动Streamlit
echo 🚀 启动文献解读Agent系统...
streamlit run app/main.py --server.port=8501