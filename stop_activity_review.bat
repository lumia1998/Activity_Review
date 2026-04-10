@echo off
setlocal

echo [Activity Review] 正在停止 8000 端口上的后端...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr 127.0.0.1:8000 ^| findstr LISTENING') do (
  taskkill /PID %%a /F >nul 2>nul
)

echo [Activity Review] 正在停止桌面宿主...
taskkill /FI "WINDOWTITLE eq Activity Review Desktop" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Activity Review Backend" /F >nul 2>nul

echo [Activity Review] 已尝试停止相关进程。
endlocal
