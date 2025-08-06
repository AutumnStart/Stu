@echo off
chcp 65001 >nul

echo ================================================
echo     素材分析与关键用户行为提取工具
echo     版本: 1.0.0
echo ================================================

REM 获取当前目录
set CURRENT_DIR=%~dp0
set TOOL_DIR=%CURRENT_DIR%\Tool

REM 检查Python是否已安装
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到Python安装，请确保已安装Python并添加到PATH环境变量中。
    goto END
)

REM 检查脚本是否存在
set ANALYZER_SCRIPT=%TOOL_DIR%\IterativeMediaAnalyzer.py
set BEHAVIOR_SCRIPT=%TOOL_DIR%\extract_behavior_analysis.py

if not exist "%ANALYZER_SCRIPT%" (
    echo [错误] 未找到素材分析脚本: %ANALYZER_SCRIPT%
    goto END
)

if not exist "%BEHAVIOR_SCRIPT%" (
    echo [错误] 未找到行为提取脚本: %BEHAVIOR_SCRIPT%
    goto END
)

REM 执行素材分析脚本
echo [2/4] 正在执行素材分析...
echo 运行脚本: %ANALYZER_SCRIPT%
python "%ANALYZER_SCRIPT%"

if %ERRORLEVEL% NEQ 0 (
    echo [错误] 素材分析脚本执行失败，错误代码: %ERRORLEVEL%
    goto END
)

echo [3/4] 素材分析完成!
echo.
echo ================================================
echo.

REM 执行行为提取脚本
echo [4/4] 正在提取关键用户行为节点分析...
echo 运行脚本: %BEHAVIOR_SCRIPT%
python "%BEHAVIOR_SCRIPT%"

if %ERRORLEVEL% NEQ 0 (
    echo [错误] 行为提取脚本执行失败，错误代码: %ERRORLEVEL%
    goto END
)

echo ================================================
echo 全部处理完成！
echo ================================================

:END
echo.
echo 按任意键退出...
pause > nul 