@echo off
echo ========================================================
echo            SmartVax Healthcare Platform
echo ========================================================
echo.

:: Detect Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not installed. 
        echo Please install it from https://www.python.org/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b
    ) else (
        set "PY_CMD=py"
    )
) else (
    set "PY_CMD=python"
)

:: Run the robust Python starter
%PY_CMD% run_smartvax.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The launcher failed. 
    echo Please make sure you have extracted all files from the ZIP.
    pause
)
