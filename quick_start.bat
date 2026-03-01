@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 🚀 启动文献解读Agent系统...

REM 设置Python路径
set PYTHONPATH=%cd%;%PYTHONPATH%

REM 直接启动Streamlit
streamlit run app/main.py --server.port=8501 --server.headless=true
