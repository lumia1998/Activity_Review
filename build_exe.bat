@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   Activity Review - Build EXE
echo ============================================================
echo.

:: ── 1. Check prerequisites ─────────────────────────────────────
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js first.
    goto :fail
)

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python first.
    goto :fail
)

python -c "import PyInstaller" >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARN] PyInstaller not installed. Installing now...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyInstaller.
        goto :fail
    )
)

:: ── 2. Build frontend ──────────────────────────────────────────
echo.
echo [1/4] Building frontend (npm run build) ...
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed.
    goto :fail
)
echo [OK] Frontend built to dist/

:: ── 3. Generate icon (optional) ────────────────────────────────
echo.
echo [2/4] Generating icons ...
if exist "public\generated-icons\icon.ico" (
    echo [OK] icon.ico already exists, skipping.
) else (
    where ffmpeg >nul 2>nul
    if !errorlevel! equ 0 (
        call npm run icons:build
        if !errorlevel! neq 0 (
            echo [WARN] Icon generation failed. Building without custom icon.
        ) else (
            echo [OK] Icons generated.
        )
    ) else (
        echo [WARN] ffmpeg not found. Skipping icon generation. Building without custom icon.
    )
)

:: ── 4. Run PyInstaller ─────────────────────────────────────────
echo.
echo [3/4] Running PyInstaller ...
pyinstaller --clean --noconfirm --distpath build_output --workpath build_temp activity_review.spec
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    goto :fail
)
echo [OK] PyInstaller build complete.

:: ── 5. Done ────────────────────────────────────────────────────
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
