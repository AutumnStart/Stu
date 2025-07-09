@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
title 素材高消耗筛选工具

:: 设置颜色
color 0A

cls
echo ==========================================
echo        素材高消耗筛选工具 - 自动运行      
echo ==========================================
echo.
echo 检查Python环境...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python环境，请安装Python后重试！
    echo 程序将在5秒后自动关闭...
    timeout /t 5 >nul
    exit /b
)

:: 检查脚本文件是否存在
if not exist Tool\filter_high_cost_materials.py (
    echo [错误] 未找到Tool\filter_high_cost_materials.py文件！
    echo 请确保脚本文件存在于Tool目录中。
    echo.
    echo 程序将在5秒后自动关闭...
    timeout /t 5 >nul
    exit /b
)

:: 显示form目录中的文件数量
echo 正在扫描数据文件...
set "file_count=0"
if not exist form (
    echo [错误] 未找到form目录！
    echo 请确保form目录存在并包含Excel文件。
    echo.
    pause
    exit /b
)

for %%f in (form\*.xlsx) do set /a file_count+=1

if %file_count% EQU 0 (
    echo [错误] form目录中未找到Excel文件！
    echo.
    pause
    exit /b
)

echo.
echo 在form目录中找到 %file_count% 个Excel文件
echo 系统将自动选择最新的数据文件进行分析
echo.

echo 正在执行高消耗素材筛选...
echo.

:: 执行高消耗素材筛选工具
python Tool\filter_high_cost_materials.py

echo.
if %errorlevel% NEQ 0 (
    echo [错误] 执行过程中出现错误！
    echo.
    pause
    exit /b
)

echo.
echo ==========================================
echo           筛选分析完成！                
echo ==========================================
echo.
echo 按任意键退出程序...
pause >nul
exit /b 