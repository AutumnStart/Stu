@echo off
chcp 65001 > nul
title JSON分析器

:: 设置颜色
color 0B

cls
echo ==========================================
echo        JSON 数据分析工具
echo ==========================================
echo.

echo 检查Python环境...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python环境，请安装Python后重试！
    echo.
    pause
    exit /b
)

:: 使用 %~dp0 来定位到脚本自身所在的目录
set SCRIPT_DIR=%~dp0

if not exist "%SCRIPT_DIR%json_analyzer.py" (
    echo [错误] 未找到 json_analyzer.py 脚本文件！
    echo.
    pause
    exit /b
)

echo.
echo 准备执行JSON分析脚本...
echo.

python "%SCRIPT_DIR%json_analyzer.py"

echo.
echo ==========================================
echo           脚本执行完毕！
echo ==========================================
echo.
exit /b 