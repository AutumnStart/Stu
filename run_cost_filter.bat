@echo off
setlocal enabledelayedexpansion

title High Cost Material Filter to Feishu

:: Set console color
color 0B

:: Install required Python packages
echo Checking and installing required Python packages...
pip install pandas openpyxl lark-oapi --quiet

cls
echo =================================================
echo        High Cost Material to Feishu Uploader     
echo =================================================
echo.

echo Checking for Python environment...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python and try again.
    echo Exiting in 5 seconds...
    timeout /t 5 >nul
    exit /b
)

:: Check if the main script exists
if not exist filter_high_cost_materials.py (
    echo [ERROR] filter_high_cost_materials.py not found.
    echo Please ensure the script is in the same directory.
    echo Exiting in 5 seconds...
    timeout /t 5 >nul
    exit /b
)

:: Scan for data files
echo Scanning for data files...
set "file_count=0"
if not exist form (
    echo [ERROR] 'form' directory not found.
    echo Please create the 'form' directory and place Excel files inside.
    pause
    exit /b
)

for %%f in (form\*.xlsx) do set /a file_count+=1

if %file_count% EQU 0 (
    echo [ERROR] No Excel files found in the 'form' directory.
    pause
    exit /b
)

echo Found %file_count% Excel file(s) in 'form' directory.
echo The script will automatically analyze the latest file.
echo.

echo Running high-cost material analysis and upload...
echo.

:: Execute the Python script
python filter_high_cost_materials.py

echo.
if %errorlevel% NEQ 0 (
    echo [ERROR] An error occurred during script execution.
    pause
    exit /b
)

echo.
echo =================================================
echo           Analysis Completed!                
echo =================================================
echo.
echo The script has finished. The window will close in 10 seconds.
timeout /t 10 >nul
        exit /b
