@echo off
setlocal EnableExtensions

REM --- Run from the script's directory so paths are predictable ---
cd /d "%~dp0"

echo.
echo === OmniParser weights bootstrap (requires Python 3.12+) ===
echo.

REM --- Select a Python that is >= 3.12 (tries several candidates) ---
set "PY_CMD="

where py >nul 2>&1
if not errorlevel 1 (
    py -3.13 -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1 && set "PY_CMD=py -3.13"
    if not defined PY_CMD (
        py -3.12 -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1 && set "PY_CMD=py -3.12"
    )
    if not defined PY_CMD (
        py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1 && set "PY_CMD=py -3"
    )
)

if not defined PY_CMD (
    where python >nul 2>&1 && (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1 && set "PY_CMD=python"
    )
)

if not defined PY_CMD (
    call :err "Python 3.12+ is required but not found. Install Python 3.12 or newer and ensure it is on PATH (or available via 'py')."
    exit /b 1
)

for /f "delims=" %%V in ('%PY_CMD% -c "import sys;print(sys.version.split()[0])" 2^>nul') do set "CUR_PY_VER=%%V"
echo Using Python: %PY_CMD%  (version %CUR_PY_VER%)
echo.

REM --- Ensure Hugging Face CLI is available ---
where hf >nul 2>&1
if errorlevel 1 (
    echo "hf" CLI not found. Installing huggingface_hub[cli]...
    %PY_CMD% -m pip install --upgrade "huggingface_hub[cli]"
    if errorlevel 1 (
        call :err "Failed to install huggingface_hub CLI. Check internet/proxy and try again."
        exit /b 1
    )
)

REM --- Temporarily prepend likely Scripts paths to PATH (session only) ---
for /f "delims=" %%S in ('%PY_CMD% -c "import sys,site,os; print(os.path.join(sys.exec_prefix, \"Scripts\")); u=site.getusersitepackages(); print(os.path.join(os.path.dirname(u), \"Scripts\"))"') do (
    if exist "%%~S" set "PATH=%%~S;%PATH%"
)

REM --- Verify hf is callable now ---
where hf >nul 2>&1
if errorlevel 1 (
    call :err "The 'hf' CLI is not on PATH after installation. Try opening a new terminal or add your Python Scripts folder to PATH."
    exit /b 1
)

REM --- Download weights ---
set "WDIR=%cd%\weights"
if not exist "%WDIR%" mkdir "%WDIR%"

set "REPO=microsoft/OmniParser-v2.0"
REM Optional: pin to a specific revision by adding: --revision <tag-or-commit>
echo Downloading model files from %REPO% into:
echo   %WDIR%
echo.

hf download %REPO% --local-dir "%WDIR%" --local-dir-use-symlinks False ^
  --include "icon_detect/train_args.yaml,icon_detect/model.pt,icon_detect/model.yaml,icon_caption/config.json,icon_caption/generation_config.json,icon_caption/model.safetensors"

if errorlevel 1 (
    call :err "Download failed. Check network/permissions and try again."
    exit /b 1
)

REM --- Organize: rename icon_caption -> icon_caption_florence ---
echo.
echo Organizing directories...
if exist "%WDIR%\icon_caption" (
    if exist "%WDIR%\icon_caption_florence" (
        echo Removing existing "%WDIR%\icon_caption_florence"...
        rmdir /s /q "%WDIR%\icon_caption_florence"
        if errorlevel 1 (
            call :err "Failed to remove existing icon_caption_florence directory."
            exit /b 1
        )
    )
    move "%WDIR%\icon_caption" "%WDIR%\icon_caption_florence" >nul
    if errorlevel 1 (
        call :err "Failed to move icon_caption to icon_caption_florence."
        exit /b 1
    )
) else (
    echo NOTE: "%WDIR%\icon_caption" not found. Skipping rename.
)

echo.
echo Download complete! Model weights are ready here:
echo   %WDIR%
echo.
pause
exit /b 0

:err
echo.
echo ERROR: %~1
echo.
goto :eof
