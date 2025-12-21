@echo off
REM ============================================
REM F1T API - Cloudflare Tunnel 啟動腳本
REM ============================================
echo.
echo [F1T] 正在啟動 Cloudflare Tunnel...
echo [F1T] Tunnel 名稱: myfastapi
echo [F1T] 公開網址: https://api.f1telemetrystationpro.org
echo.

REM 切換到 cloudflared 目錄
cd /d "%~dp0cloudflared"

REM 啟動 Cloudflare Tunnel
cloudflared.exe --config "%~dp0cloudflared\config.yml" tunnel run myfastapi

REM 若 Tunnel 關閉則顯示訊息
echo.
echo [F1T] Cloudflare Tunnel 已停止
pause
