@echo off
chcp 65001 >nul
title 数据库服务管理器
color 0B

:menu
cls
echo ==========================================
echo    🗄️ 数据库服务管理器 - Windows
echo ==========================================
echo.
echo 请选择操作：
echo.
echo  [1] 启动所有服务
echo  [2] 停止所有服务
echo  [3] 重启所有服务
echo  [4] 查看服务状态
echo  [5] 启动MySQL
echo  [6] 停止MySQL
echo  [7] 启动MongoDB
echo  [8] 停止MongoDB
echo  [9] 启动Redis
echo  [10] 停止Redis
echo.
echo  [0] 退出
echo.
echo ==========================================
set /p choice="请输入选项 (0-10): "

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto stop_all
if "%choice%"=="3" goto restart_all
if "%choice%"=="4" goto check_status
if "%choice%"=="5" goto start_mysql
if "%choice%"=="6" goto stop_mysql
if "%choice%"=="7" goto start_mongodb
if "%choice%"=="8" goto stop_mongodb
if "%choice%"=="9" goto start_redis
if "%choice%"=="10" goto stop_redis
if "%choice%"=="0" goto exit

echo ❌ 无效选项，请重新选择
pause
goto menu

:start_all
echo.
echo 🚀 正在启动所有服务...
echo.
call :start_mysql
call :start_mongodb
call :start_redis
echo.
echo ✅ 所有服务启动命令已执行
echo 💡 请使用选项4查看服务状态
pause
goto menu

:stop_all
echo.
echo 🛑 正在停止所有服务...
echo.
call :stop_redis
call :stop_mongodb
call :stop_mysql
echo.
echo ✅ 所有服务停止命令已执行
pause
goto menu

:restart_all
echo.
echo 🔄 正在重启所有服务...
echo.
call :stop_all
timeout /t 3 /nobreak >nul
call :start_all
echo.
echo ✅ 所有服务重启完成
pause
goto menu

:check_status
echo.
echo 🔍 检查服务状态...
echo.
echo -----------------------------------------
echo MySQL状态：
sc query MySQL80 2>nul | findstr "STATE"
if errorlevel 1 (
    sc query MySQL 2>nul | findstr "STATE"
    if errorlevel 1 echo    ❌ 服务未安装
)
echo.
echo MongoDB状态：
sc query MongoDB 2>nul | findstr "STATE"
if errorlevel 1 echo    ❌ 服务未安装
echo.
echo Redis状态：
sc query Redis 2>nul | findstr "STATE"
if errorlevel 1 echo    ❌ 服务未安装
echo -----------------------------------------
pause
goto menu

:start_mysql
echo 🚀 启动MySQL服务...
net start MySQL80 >nul 2>&1
if errorlevel 1 (
    net start MySQL >nul 2>&1
    if errorlevel 1 (
        echo    ❌ MySQL启动失败
    ) else (
        echo    ✅ MySQL启动成功
    )
) else (
    echo    ✅ MySQL启动成功
)
goto :eof

:stop_mysql
echo 🛑 停止MySQL服务...
net stop MySQL80 >nul 2>&1
if errorlevel 1 (
    net stop MySQL >nul 2>&1
    if errorlevel 1 (
        echo    ❌ MySQL停止失败或已停止
    ) else (
        echo    ✅ MySQL已停止
    )
) else (
    echo    ✅ MySQL已停止
)
goto :eof

:start_mongodb
echo 🚀 启动MongoDB服务...
net start MongoDB >nul 2>&1
if errorlevel 1 (
    echo    ❌ MongoDB启动失败
) else (
    echo    ✅ MongoDB启动成功
)
goto :eof

:stop_mongodb
echo 🛑 停止MongoDB服务...
net stop MongoDB >nul 2>&1
if errorlevel 1 (
    echo    ❌ MongoDB停止失败或已停止
) else (
    echo    ✅ MongoDB已停止
)
goto :eof

:start_redis
echo 🚀 启动Redis服务...
net start Redis >nul 2>&1
if errorlevel 1 (
    echo    ❌ Redis启动失败
) else (
    echo    ✅ Redis启动成功
)
goto :eof

:stop_redis
echo 🛑 停止Redis服务...
net stop Redis >nul 2>&1
if errorlevel 1 (
    echo    ❌ Redis停止失败或已停止
) else (
    echo    ✅ Redis已停止
)
goto :eof

:exit
echo.
echo 👋 感谢使用！
timeout /t 2 /nobreak >nul
exit