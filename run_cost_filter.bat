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
if not exist filter_high_cost_materials.py (
    echo [错误] 未找到filter_high_cost_materials.py文件！
    echo 请确保脚本文件与批处理文件在同一目录。
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
python filter_high_cost_materials.py

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
echo Next Step:
echo -----------------------
echo 1. Upload to Feishu
echo 2. Exit 
echo -----------------------
echo.

set /p user_choice=Enter your choice (1 or 2): 

if "%user_choice%"=="2" (
    echo.
    echo Program ended. Thank you!
    timeout /t 3 > nul
    exit /b
) else if "%user_choice%"=="1" (
    echo.
    echo ==========================================
    echo   STARTING FEISHU DATA UPLOAD...
    echo ==========================================
    echo.
    
    :: 检查是否存在feishu_write.py文件
    if not exist feishu_write.py (
        echo [ERROR] feishu_write.py not found!
        echo Cannot proceed with data upload.
        echo.
        pause
        exit /b
    )
    
    :: 检查是否存在feishu_config.json文件
    if not exist feishu_config.json (
        echo [WARNING] feishu_config.json not found!
        echo Please ensure Feishu configuration is properly set.
        echo.
    )
    
    echo Uploading data to Feishu...
    python feishu_write.py
    
    if %errorlevel% NEQ 0 (
        echo.
        echo [ERROR] Error occurred during Feishu upload!
        echo.
        pause
        exit /b
    )
    
    echo.
    echo Feishu upload completed
    echo.
    echo Exiting in 5 seconds...
    timeout /t 5 >nul
    exit /b

) else (
    echo.
    echo Invalid choice. Program will exit.
    timeout /t 3 >nul
    exit /b
)
