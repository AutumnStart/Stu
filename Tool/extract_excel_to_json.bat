@echo off
chcp 65001 >nul
setlocal

:: 检查是否存在Python环境
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误：未检测到Python环境，请安装Python后再运行此脚本。
    pause
    exit /b 1
)

:: 设置脚本和Excel路径
set SCRIPT_PATH=%~dp0extract_excel_to_json.py
set DEFAULT_EXCEL_PATH=%~dp0..\data\素材数据.xlsx

:: 创建输出目录
if not exist "%~dp0..\json\素材数据分析" mkdir "%~dp0..\json\素材数据分析"

echo 正在将Excel数据转换为JSON格式...
python "%SCRIPT_PATH%" "%DEFAULT_EXCEL_PATH%"

if %ERRORLEVEL% NEQ 0 (
    echo 处理过程中出现错误！
    pause
    exit /b 1
)

echo 处理完成！
exit /b 0 