@echo off
setlocal enabledelayedexpansion

echo ================================================
echo 素材ID提取工具
echo ================================================
echo.

:: 检查Python是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请安装Python后再试。
    goto :end
)

:: 检查所需的Python库是否安装
echo 检查所需的Python库...
python -c "import pandas" 2>nul
if %errorlevel% neq 0 (
    echo 正在安装pandas库...
    pip install pandas
)

python -c "import openpyxl" 2>nul
if %errorlevel% neq 0 (
    echo 正在安装openpyxl库...
    pip install openpyxl
)

echo.
echo 开始提取素材ID...
echo 将自动查找以"素材数据"开头的Excel文件...
python "%~dp0\extract_material_id.py"

:end
echo.
echo 按任意键退出...
pause > nul 