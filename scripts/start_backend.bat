@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   Happy Vibe - VibeHub 后端启动脚本
echo ========================================
echo.

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "VIBEHUB_DIR=%SCRIPT_DIR%..\vibehub"

:: 检查 vibehub 目录
if not exist "%VIBEHUB_DIR%" (
    echo [错误] 找不到 vibehub 目录: %VIBEHUB_DIR%
    echo 请确保脚本位于 Happy-Vibe\scripts\ 目录下
    pause
    exit /b 1
)

cd /d "%VIBEHUB_DIR%"
echo [信息] 工作目录: %CD%

:: 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [警告] 虚拟环境不存在，正在创建...
    echo.
    uv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [信息] 正在安装依赖...
    call .venv\Scripts\activate.bat
    uv pip install -e ".[dev]"
    if errorlevel 1 (
        echo [错误] 安装依赖失败
        pause
        exit /b 1
    )
) else (
    call .venv\Scripts\activate.bat
)

echo [信息] 虚拟环境已激活
echo.

:: 解析参数
set "HOST=127.0.0.1"
set "PORT=8765"
set "RELOAD="

:parse_args
if "%~1"=="" goto start_server
if /i "%~1"=="--host" (
    set "HOST=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--port" (
    set "PORT=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--reload" (
    set "RELOAD=--reload"
    shift
    goto parse_args
)
shift
goto parse_args

:start_server
echo [信息] 启动 VibeHub 后端服务...
echo [信息] 地址: http://%HOST%:%PORT%
echo [信息] API 文档: http://%HOST%:%PORT%/docs
echo.
echo 按 Ctrl+C 停止服务
echo ----------------------------------------

python -m uvicorn src.main:app --host %HOST% --port %PORT% %RELOAD%

if errorlevel 1 (
    echo.
    echo [错误] 服务启动失败
    pause
    exit /b 1
)

endlocal
