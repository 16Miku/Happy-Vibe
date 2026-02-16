@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   Happy Vibe - 一键启动所有服务
echo ========================================
echo.

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "GAME_DIR=%SCRIPT_DIR%..\game"

:: 解析参数
set "START_GAME=0"
set "NO_MONITOR=0"

:parse_args
if "%~1"=="" goto check_env
if /i "%~1"=="--with-game" (
    set "START_GAME=1"
    shift
    goto parse_args
)
if /i "%~1"=="--no-monitor" (
    set "NO_MONITOR=1"
    shift
    goto parse_args
)
if /i "%~1"=="--help" (
    goto show_help
)
shift
goto parse_args

:show_help
echo 用法: run_all.bat [选项]
echo.
echo 选项:
echo   --with-game    同时启动 Godot 游戏客户端
echo   --no-monitor   不启动监控器
echo   --help         显示此帮助信息
echo.
exit /b 0

:check_env
echo [信息] 检查环境...

:: 检查 vibehub 虚拟环境
if not exist "%SCRIPT_DIR%..\vibehub\.venv" (
    echo [警告] 虚拟环境不存在，将在启动时自动创建
)

echo [信息] 环境检查完成
echo.

:: 启动后端服务 (新窗口)
echo [信息] 启动 VibeHub 后端服务...
start "VibeHub Backend" cmd /k ""%SCRIPT_DIR%start_backend.bat""

:: 等待后端启动
echo [信息] 等待后端服务启动...
timeout /t 3 /nobreak >nul

:: 检查后端是否启动成功
powershell -Command "(Invoke-WebRequest -Uri 'http://127.0.0.1:8765/health' -UseBasicParsing -TimeoutSec 5).StatusCode" >nul 2>&1
if errorlevel 1 (
    echo [警告] 后端服务可能尚未完全启动，继续等待...
    timeout /t 5 /nobreak >nul
)

:: 启动监控器 (新窗口)
if "%NO_MONITOR%"=="0" (
    echo [信息] 启动 Monitor 监控器...
    start "Happy Vibe Monitor" cmd /k ""%SCRIPT_DIR%start_monitor.bat""
) else (
    echo [信息] 跳过监控器启动 (--no-monitor)
)

:: 启动游戏客户端 (可选)
if "%START_GAME%"=="1" (
    echo [信息] 启动 Godot 游戏客户端...
    if exist "%GAME_DIR%\project.godot" (
        start "" godot --path "%GAME_DIR%"
    ) else (
        echo [警告] 找不到游戏项目: %GAME_DIR%\project.godot
    )
)

echo.
echo ========================================
echo   所有服务已启动
echo ========================================
echo.
echo 服务地址:
echo   - VibeHub API: http://127.0.0.1:8765
echo   - API 文档:    http://127.0.0.1:8765/docs
echo.
echo 提示:
echo   - 使用 stop_all.bat 停止所有服务
echo   - 或在各窗口按 Ctrl+C 单独停止
echo.

endlocal
