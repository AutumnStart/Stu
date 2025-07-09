@echo off
echo 开始运行图片峰值分析程序...
echo.

cd /d %~dp0
python gemini_image_peak_analysis.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo 运行成功!
) else (
    echo 运行出错，错误代码: %ERRORLEVEL%
    echo 请检查是否安装了必要的Python库: requests
    echo 可以使用以下命令安装:
    echo pip install requests
)

pause 