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

:: 设置脚本路径
set SCRIPT_PATH=%~dp0extract_excel_to_json.py

:: 创建输出目录
if not exist "%~dp0..\json\素材数据分析" mkdir "%~dp0..\json\素材数据分析"

echo 正在将Excel数据转换为JSON格式...
echo 将自动查找以"素材数据"开头的Excel文件...

:: 直接运行Python脚本，让脚本自动查找素材数据文件
python "%SCRIPT_PATH%"

if %ERRORLEVEL% NEQ 0 (
    echo 处理过程中出现错误！
    pause
    exit /b 1
)

echo 处理完成！
pause
exit /b 0 