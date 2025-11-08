@echo off
REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.12 and add it to your PATH.
    pause
    exit /b 1
)

python -c "import sys; print(str(sys.version_info.major) + '.' + str(sys.version_info.minor))" > temp_pyver.txt 2>nul
if errorlevel 1 (
    echo Error: Failed to determine Python version.
    echo Please ensure Python 3.12 is properly installed.
    del temp_pyver.txt 2>nul
    pause
    exit /b 1
)

set /p pyver=<temp_pyver.txt
del temp_pyver.txt

if not "%pyver:~0,1%"=="3" (
    echo Error: This script requires Python 3.12 or higher.
    echo Current Python version: %pyver%
    echo Please install Python 3.12 or higher and ensure it's the default python command.
    pause
    exit /b 1
)

if "%pyver:~2%" lss "12" (
    echo Error: This script requires Python 3.12 or higher.
    echo Current Python version: %pyver%
    echo Please install Python 3.12 or higher and ensure it's the default python command.
    pause
    exit /b 1
)

echo Downloading OmniParser model weights...
echo.

REM Temporarily modify PATH to prioritize Python Scripts directory
for /f "delims=" %%i in ('python -c "import sys, os; print(os.path.join(sys.exec_prefix, 'Scripts'))"') do set "PYTHON_SCRIPTS=%%i"
set "PATH=%PYTHON_SCRIPTS%;%PATH%"

REM Create weights directory if it doesn't exist
if not exist weights mkdir weights

REM Download icon detection model files
echo Downloading icon detection model files...
hf download microsoft/OmniParser-v2.0 icon_detect/train_args.yaml --local-dir weights
hf download microsoft/OmniParser-v2.0 icon_detect/model.pt --local-dir weights
hf download microsoft/OmniParser-v2.0 icon_detect/model.yaml --local-dir weights

REM Download icon caption model files
echo.
echo Downloading icon caption model files...
hf download microsoft/OmniParser-v2.0 icon_caption/config.json --local-dir weights
hf download microsoft/OmniParser-v2.0 icon_caption/generation_config.json --local-dir weights
hf download microsoft/OmniParser-v2.0 icon_caption/model.safetensors --local-dir weights

REM Move the icon_caption directory to icon_caption_florence
echo.
echo Organizing directories...
move weights\icon_caption weights\icon_caption_florence

echo.
echo Download complete! Model weights are ready.
echo.
pause
