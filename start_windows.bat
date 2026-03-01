@echo off
chcp 65001 >nul
title 文献解读Agent系统
color 0A

echo ==========================================
echo    🎓 文献解读Agent系统 - Windows版
echo ==========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

echo 📂 当前目录: %cd%
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.9+
    echo 📥 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安装
python --version
echo.

REM 检查依赖是否安装
echo 🔍 检查项目依赖...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 📦 正在安装依赖...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo ❌ 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖已安装
)

echo.

REM 检查配置文件
if not exist ".env" (
    echo ⚠️ 配置文件不存在，正在创建...
    copy .env.example .env
    echo ✅ 配置文件已创建，请编辑.env文件设置数据库密码
    echo 📝 配置文件路径：%~dp0.env
    notepad .env
    echo.
    echo ⚠️ 请设置好数据库密码后重新运行此脚本
    pause
    exit /b 1
)

echo ✅ 配置文件存在
echo.

echo ==========================================
echo    🚀 正在启动文献解读Agent系统...
echo ==========================================
echo.
echo 🌐 系统将在浏览器中打开
echo 📍 访问地址：http://localhost:8501
echo.
echo 💡 提示：
echo    - 首次使用需要注册账户
echo    - 请配置Deepseek API密钥
echo    - 按Ctrl+C可以停止服务
echo    - 如果MySQL连接失败，系统将自动使用SQLite
echo.

REM 使用新的启动入口
python run.py

REM 如果启动失败
if errorlevel 1 (
    echo.
    echo ❌ 系统启动失败
    echo 🔧 请检查：
    echo    1. 端口8501是否被占用
    echo    2. 配置文件是否正确
    echo    3. 数据库服务是否正常运行
    pause
)

echo.
echo 👋 感谢使用文献解读Agent系统！
pause