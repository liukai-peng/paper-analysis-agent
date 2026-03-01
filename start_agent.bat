@echo off
echo ========================================
echo 文献解读Agent系统
echo 基于多Agent协作的智能文献分析
echo ========================================
echo.

echo 正在安装依赖...
pip install -r requirements.txt --quiet

echo.
echo 启动文献解读Agent系统...
streamlit run app/main.py

pause