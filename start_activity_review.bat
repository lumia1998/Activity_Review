@echo off
setlocal
cd /d "%~dp0"

echo [Activity Review] 检查后端状态...
python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)" >nul 2>nul
if %errorlevel%==0 (
  echo [Activity Review] 后端已在运行，跳过重复启动。
) else (
  echo [Activity Review] 正在启动后端...
  start "Activity Review Backend" cmd /k "cd /d "%~dp0" && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
  echo [Activity Review] 等待后端启动...
  timeout /t 2 /nobreak >nul
)

echo [Activity Review] 正在启动桌面宿主...
start "Activity Review Desktop" cmd /k "cd /d "%~dp0" && python -m desktop.main"

echo [Activity Review] 已发起启动。
echo - 若看到“后端已在运行”，属于正常现象
echo - 后端窗口: Activity Review Backend
echo - 桌面窗口: Activity Review Desktop
endlocal
