@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   Activity Review - Build Installer
echo ============================================================
echo.

:: ── 0. Select Python ────────────────────────────────────────────────────────
set PYTHON_CMD=py -3.11
%PYTHON_CMD% --version >nul 2>nul
if %errorlevel% neq 0 (
    set PYTHON_CMD=python
)

:: ── 1. Check Inno Setup ─────────────────────────────────────────────────────
set ISCC=
for %%p in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
) do (
    if exist %%p (
        set ISCC=%%~p
        goto :found_iscc
    )
)
echo [ERROR] Inno Setup not found.
echo.
echo Please download and install Inno Setup 6 from:
echo   https://jrsoftware.org/isdl.php
echo.
goto :fail
:found_iscc
echo [INFO] Using Inno Setup: %ISCC%

:: ── 2. Check build output exists ────────────────────────────────────────────
if not exist "build_output\ActivityReview\ActivityReview.exe" (
    echo [ERROR] Build output not found. Run build_exe.bat first.
    goto :fail
)

:: ── 3. Generate icon.ico if missing ─────────────────────────────────────────
if not exist "public\icon.ico" (
    echo [INFO] Generating icon.ico from icon.png...
    %PYTHON_CMD% -c "from PIL import Image; img=Image.open('public/icon.png').convert('RGBA'); s=[16,32,48,64,128,256]; imgs=[img.resize((x,x)) for x in s]; imgs[0].save('public/icon.ico',format='ICO',sizes=[(x,x) for x in s],append_images=imgs[1:])"
    if !errorlevel! neq 0 (
        echo [WARN] Icon generation failed, building without custom icon.
    ) else (
        echo [OK] icon.ico generated.
    )
) else (
    echo [OK] icon.ico already exists.
)

:: ── 4. Create output dir ─────────────────────────────────────────────────────
if not exist "installer_output" mkdir installer_output

:: ── 5. Compile installer ─────────────────────────────────────────────────────
echo.
echo [1/1] Compiling installer with Inno Setup...
"%ISCC%" installer.iss
if %errorlevel% neq 0 (
    echo [ERROR] Inno Setup compilation failed.
    goto :fail
)

:: ── 6. Done ──────────────────────────────────────────────────────────────────
echo.
echo ============================================================
echo   INSTALLER BUILD SUCCESSFUL
for %%f in (installer_output\*.exe) do echo   Output: installer_output\%%~nxf
echo ============================================================
goto :end

:fail
echo.
echo ============================================================
echo   INSTALLER BUILD FAILED
echo ============================================================
exit /b 1

:end
endlocal
