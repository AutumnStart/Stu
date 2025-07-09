@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
title 抖音素材潜力预测系统 - 自动运行

:: 设置颜色
color 0A

cls
echo ==========================================
echo   抖音素材潜力预测系统 - 自动分析模式     
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

:: 确保data目录存在
if not exist data (
    echo 创建data输出目录...
    mkdir data
)

echo.
echo 正在启动自动分析模式...
echo.

:: 显示form目录中的文件数量
echo 正在扫描数据文件...
set "file_count=0"
for %%f in (form\*.xlsx) do set /a file_count+=1

echo.
echo 在form目录中找到 %file_count% 个Excel文件
echo 系统将自动选择最新的数据文件进行分析
echo.

echo 正在处理数据...
echo.

:: 执行分析，使用自动扫描功能
python Tool\production_deployment_tool.py --output-dir data

echo.
echo 分析完成！结果已保存到data目录。
echo.

:: 检查是否存在run_cost_filter.bat文件
echo 准备执行高消耗素材筛选...
if not exist run_cost_filter.bat (
    echo [错误] 未找到run_cost_filter.bat文件！
    echo 高消耗素材筛选无法执行。
    echo.
    echo 程序将在5秒后自动关闭...
    timeout /t 5 >nul
    exit /b
)

:: 执行高消耗素材筛选工具
echo.
echo ==========================================
echo   开始执行高消耗素材筛选...
echo ==========================================
echo.
call run_cost_filter.bat

echo.
echo 所有任务已完成，程序将在5秒后自动关闭...
timeout /t 5 >nul
exit /b 