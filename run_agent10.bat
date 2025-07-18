@echo off
echo 正在启动抖音素材ID分析系统...
echo.
echo 此程序将根据data目录下的素材ID.json文件中的素材ID，
echo 在json\素材数据分析\merged_material_data.json中查找对应的素材名称，
echo 然后根据这些素材名称分析对应的视频。
echo.

REM 设置Python路径，如果Python已在环境变量中，可以直接使用python命令
set PYTHON_CMD=python

REM 检查Python是否可用
%PYTHON_CMD% --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python未找到，请确保已安装Python并添加到环境变量中。
    pause
    exit /b 1
)

REM 运行agent10分析程序
echo 正在根据素材ID分析视频...
%PYTHON_CMD% agents/run_agent10.py

echo.
if %ERRORLEVEL% neq 0 (
    echo 程序运行出错，请检查日志。
    pause
) else (
    echo 分析完成！
    pause
) 