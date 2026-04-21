@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   Activity Review - Build EXE
echo ============================================================
echo.

:: ── 0. Select Python 3.11 explicitly ────────────────────────────────────────
set PYTHON_CMD=py -3.11
%PYTHON_CMD% --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARN] py -3.11 not found, falling back to python
    set PYTHON_CMD=python
)
echo [INFO] Using: %PYTHON_CMD%

:: ── 1. Check prerequisites ─────────────────────────────────────────────────
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js first.
    goto :fail
)

%PYTHON_CMD% -c "import PyInstaller" >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARN] PyInstaller not installed. Installing now...
    %PYTHON_CMD% -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyInstaller.
        goto :fail
    )
)

:: ── 2. Build frontend ──────────────────────────────────────────────────────
echo.
echo [1/4] Building frontend (npm run build) ...
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed.
    goto :fail
)
echo [OK] Frontend built to dist/

:: ── 3. Generate icon (optional) ────────────────────────────────────────────
echo.
echo [2/4] Generating icons ...
if exist "public\icon.ico" (
    echo [OK] icon.ico already exists, skipping.
) else (
    %PYTHON_CMD% -c "from PIL import Image; img=Image.open('public/icon.png').convert('RGBA'); s=[16,32,48,64,128,256]; imgs=[img.resize((x,x)) for x in s]; imgs[0].save('public/icon.ico',format='ICO',sizes=[(x,x) for x in s],append_images=imgs[1:])" >nul 2>nul
    if !errorlevel! equ 0 (
        echo [OK] icon.ico generated.
    ) else (
        echo [WARN] Icon generation failed. Building without custom icon.
    )
)

:: ── 4. Run PyInstaller ─────────────────────────────────────────────────────
echo.
echo [3/4] Running PyInstaller ...
%PYTHON_CMD% -m PyInstaller --clean --noconfirm --distpath build_output --workpath build_temp activity_review.spec
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    goto :fail
)
echo [OK] PyInstaller build complete.

:: ── 5. Done ────────────────────────────────────────────────────────────────
echo.
echo [4/4] Verifying output ...
if exist "build_output\ActivityReview\ActivityReview.exe" (
    echo ============================================================
    echo   BUILD SUCCESSFUL
    echo   Output: build_output\ActivityReview\ActivityReview.exe
    echo ============================================================
) else (
    echo [ERROR] Expected output not found at build_output\ActivityReview\ActivityReview.exe
    goto :fail
)

echo.
echo Done. You can run the application by executing:
echo   build_output\ActivityReview\ActivityReview.exe
echo.
goto :end

:fail
echo.
echo ============================================================
echo   BUILD FAILED
echo ============================================================
exit /b 1

:end
endlocal
