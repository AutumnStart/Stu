@echo off
chcp 65001 >nul
setlocal

:: =================================================================
:: 总启动器 - 依次执行所有数据处理和上传任务
:: =================================================================

echo.
echo  ======================================================
echo     数据处理与上传全流程启动器
echo  ======================================================
echo.
echo  此脚本将按顺序执行四个核心程序:
echo  1. 素材潜力预测 (production_deployment_tool.py)
echo  2. 分析报告生成 (json_analyzer.py)
echo  3. 分析报告上传 (feishu_write.py)
echo  4. 高消耗素材筛选与上传 (filter_high_cost_materials.py)
echo.

:START_PROCESS
cls
echo.
echo  ======================================================
echo  [1/4] 正在执行: 素材潜力预测...
echo  ======================================================
echo.
python production_deployment_tool.py
if %errorlevel% neq 0 (
    echo.
    echo  !!!!!!!!!! 错误 !!!!!!!!!!
    echo  步骤1 ^(production_deployment_tool.py^) 执行失败。
    echo  请检查上面的错误信息。
    goto END
)
echo.
echo  步骤1 完成。等待5秒...
timeout /t 5 /nobreak >nul

:NEXT_PROCESS_2
cls
echo.
echo  ======================================================
echo  [2/4] 正在执行: 分析报告生成...
echo  ======================================================
echo.
python json_analyzer.py
if %errorlevel% neq 0 (
    echo.
    echo  !!!!!!!!!! 错误 !!!!!!!!!!
    echo  步骤2 ^(json_analyzer.py^) 执行失败。
    echo  请检查上面的错误信息。
    goto END
)
echo.
echo  步骤2 完成。等待5秒...
timeout /t 5 /nobreak >nul

:NEXT_PROCESS_3
cls
echo.
echo  ======================================================
echo  [3/4] 正在执行: 分析报告上传至飞书...
echo  ======================================================
echo.
python feishu_write.py
if %errorlevel% neq 0 (
    echo.
    echo  !!!!!!!!!! 错误 !!!!!!!!!!
    echo  步骤3 ^(feishu_write.py^) 执行失败。
    echo  请检查上面的错误信息。
    goto END
)
echo.
echo  步骤3 完成。等待5秒...
timeout /t 5 /nobreak >nul

:NEXT_PROCESS_4
cls
echo.
echo  ======================================================
echo  [4/4] 正在执行: 高消耗素材筛选与上传...
echo  ======================================================
echo.
python filter_high_cost_materials.py
if %errorlevel% neq 0 (
    echo.
    echo  !!!!!!!!!! 错误 !!!!!!!!!!
    echo  步骤4 ^(filter_high_cost_materials.py^) 执行失败。
    echo  请检查上面的错误信息。
    goto END
)
echo.
echo  步骤4 完成。

:SUCCESS
cls
echo.
echo  ======================================================
echo      🎉 全部流程成功执行完毕！
echo  ======================================================
echo.
goto END

:END
echo.
echo  脚本执行结束。
pause
endlocal 