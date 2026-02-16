@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   Happy Vibe - Monitor 监控器启动脚本
echo ========================================
echo.

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "MONITOR_DIR=%SCRIPT_DIR%..\monitor"
set "VIBEHUB_DIR=%SCRIPT_DIR%..\vibehub"

:: 检查 monitor 目录
if not exist "%MONITOR_DIR%" (
    echo [错误] 找不到 monitor 目录: %MONITOR_DIR%
    echo 请确保脚本位于 Happy-Vibe\scripts\ 目录下
    pause
    exit /b 1
)

cd /d "%MONITOR_DIR%"
echo [信息] 工作目录: %CD%

:: 检查虚拟环境 (使用 vibehub 的虚拟环境)
if not exist "%VIBEHUB_DIR%\.venv\Scripts\activate.bat" (
    echo [错误] 找不到虚拟环境
    echo 请先运行 start_backend.bat 创建虚拟环境
    pause
    exit /b 1
)

call "%VIBEHUB_DIR%\.venv\Scripts\activate.bat"
echo [信息] 虚拟环境已激活
echo.

:: 检查 monitor 依赖
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装 monitor 依赖...
    uv pip install -e ".[dev]"
    if errorlevel 1 (
        echo [错误] 安装依赖失败
        pause
        exit /b 1
    )
)

echo [信息] 启动 Monitor 监控器...
echo.
echo 按 Ctrl+C 停止监控
echo ----------------------------------------

python src/main.py %*

if errorlevel 1 (
    echo.
    echo [错误] 监控器启动失败
    pause
    exit /b 1
)

endlocal
