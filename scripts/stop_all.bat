@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   Happy Vibe - 停止所有服务
echo ========================================
echo.

:: 解析参数
set "FORCE=0"
set "CLEAN=0"

:parse_args
if "%~1"=="" goto stop_services
if /i "%~1"=="--force" (
    set "FORCE=1"
    shift
    goto parse_args
)
if /i "%~1"=="--clean" (
    set "CLEAN=1"
    shift
    goto parse_args
)
if /i "%~1"=="--help" (
    goto show_help
)
shift
goto parse_args

:show_help
echo 用法: stop_all.bat [选项]
echo.
echo 选项:
echo   --force    强制终止所有 Python 进程
echo   --clean    清理临时文件和缓存
echo   --help     显示此帮助信息
echo.
exit /b 0

:stop_services
echo [信息] 正在停止 Happy Vibe 服务...
echo.

:: 查找并终止 uvicorn 进程 (VibeHub 后端)
echo [信息] 停止 VibeHub 后端...
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo list ^| findstr "PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /i "uvicorn" >nul
    if not errorlevel 1 (
        echo [信息] 终止进程 PID: %%a
        taskkill /pid %%a /f >nul 2>&1
    )
)

:: 查找并终止 monitor 进程
echo [信息] 停止 Monitor 监控器...
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo list ^| findstr "PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /i "monitor" >nul
    if not errorlevel 1 (
        echo [信息] 终止进程 PID: %%a
        taskkill /pid %%a /f >nul 2>&1
    )
)

:: 强制模式：终止所有 Python 进程
if "%FORCE%"=="1" (
    echo.
    echo [警告] 强制模式：终止所有 Python 进程...
    taskkill /im python.exe /f >nul 2>&1
    if not errorlevel 1 (
        echo [信息] 所有 Python 进程已终止
    )
)

:: 清理临时文件
if "%CLEAN%"=="1" (
    echo.
    echo [信息] 清理临时文件...

    set "SCRIPT_DIR=%~dp0"

    :: 清理 __pycache__
    for /d /r "%SCRIPT_DIR%.." %%d in (__pycache__) do (
        if exist "%%d" (
            echo [信息] 删除: %%d
            rd /s /q "%%d" 2>nul
        )
    )

    :: 清理 .pytest_cache
    for /d /r "%SCRIPT_DIR%.." %%d in (.pytest_cache) do (
        if exist "%%d" (
            echo [信息] 删除: %%d
            rd /s /q "%%d" 2>nul
        )
    )

    :: 清理 .mypy_cache
    for /d /r "%SCRIPT_DIR%.." %%d in (.mypy_cache) do (
        if exist "%%d" (
            echo [信息] 删除: %%d
            rd /s /q "%%d" 2>nul
        )
    )

    :: 清理 .ruff_cache
    for /d /r "%SCRIPT_DIR%.." %%d in (.ruff_cache) do (
        if exist "%%d" (
            echo [信息] 删除: %%d
            rd /s /q "%%d" 2>nul
        )
    )

    :: 清理 *.pyc 文件
    del /s /q "%SCRIPT_DIR%..\*.pyc" 2>nul

    echo [信息] 临时文件清理完成
)

echo.
echo ========================================
echo   所有服务已停止
echo ========================================
echo.

endlocal
