@echo off
chcp 65001 >nul
setlocal

echo ===================================
echo   数据处理自动化工具 - 全流程执行
echo ===================================
echo.

:: 设置默认路径
set DATA_DIR=json\素材数据分析
set MATERIAL_JSON=%DATA_DIR%\素材数据.json
set PEAKS_JSON=%DATA_DIR%\BYDHG_peaks_analysis.json
set OUTPUT_JSON=%DATA_DIR%\merged_material_data.json

:: 确保目录存在
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

echo [1/5] 开始提取素材ID...
echo.
cmd /c Tool\extract_material_id.bat
if %ERRORLEVEL% NEQ 0 (
    echo 提取素材ID失败！中止流程。
    pause
    exit /b 1
)
echo.
echo 提取素材ID完成！
echo.

echo [2/5] 开始使用Playwright截取图表...
echo.
python Tool\capture_click_chart.py
if %ERRORLEVEL% NEQ 0 (
    echo 使用Playwright截取图表失败！中止流程。
    pause
    exit /b 1
)
echo.
echo Playwright截图完成！
echo.

echo [3/5] 开始执行Excel数据转换...
echo.
cmd /c Tool\extract_excel_to_json.bat
if %ERRORLEVEL% NEQ 0 (
    echo Excel数据转换失败！中止流程。
    pause
    exit /b 1
)
echo.
echo Excel数据转换完成！
echo.

echo [4/5] 开始执行图片峰值分析...
echo.
cmd /c Tool\gemini_image_peak_analysis.bat
if %ERRORLEVEL% NEQ 0 (
    echo 图片峰值分析失败！中止流程。
    pause
    exit /b 1
)
echo.
echo 图片峰值分析完成！
echo.

echo [5/5] 开始合并素材数据和峰值分析结果...
echo.
echo 素材数据: %MATERIAL_JSON%
echo 峰值分析: %PEAKS_JSON%
echo 输出路径: %OUTPUT_JSON%
echo.

:: 调用Python脚本执行合并
cmd /c python Tool\extract_excel_to_json.py merge "%CD%\%MATERIAL_JSON%" "%CD%\%PEAKS_JSON%" "%CD%\%OUTPUT_JSON%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 合并失败，请检查错误信息。
    pause
    exit /b 1
)

echo.
echo 全流程处理完成！
echo 合并后的数据已保存到: %OUTPUT_JSON%
echo.

pause 