@echo off
chcp 65001 >nul
title F1T GUI Demo 啟動器
color 0A

echo.
echo ═══════════════════════════════════════════════════════════════
echo  🏎️  F1T GUI Demo 啟動器
echo ═══════════════════════════════════════════════════════════════
echo.
echo 📋 請選擇要展示的GUI風格:
echo.
echo    [A] 風格A - 現代扁平化設計 (Modern Flat Design)
echo        • 簡潔現代的界面風格
echo        • 扁平化設計元素
echo        • 藍色為主色調
echo        • 適合一般用戶使用
echo.
echo    [B] 風格B - 專業工程設計 (Professional Engineering)
echo        • 專業工程界面風格
echo        • 豐富的系統監控資訊
echo        • 灰色工程色調
echo        • 適合技術專業人員
echo.
echo    [C] 風格C - 90年代復古專業 (90s Retro Professional)
echo        • 經典90年代界面風格
echo        • 緊湊高效的空間利用
echo        • 系統原生色調
echo        • 適合專業高效工作
echo.
echo    [D] 風格D - 專業F1分析工作站 (Professional F1 Workstation)
echo        • 深色專業主題
echo        • 高信息密度布局
echo        • F1分析工具風格
echo        • 適合專業分析師
echo.
echo    [E] 風格E - MoTeC風格專業分析 (MoTeC Style Professional)
echo        • 模仿MoTeC i2 Pro界面
echo        • 深色背景配色彩數據線
echo        • 專業賽車數據分析風格
echo        • 工業級分析工具設計
echo.
echo    [F] 風格F - 工業化專業工作站 (Industrial Professional Workstation)
echo        • 融合風格D+E的專業性
echo        • 緊湊工業風格按鈕
echo        • 高密度信息布局
echo        • MoTeC ECU Manager風格
echo.
echo    [G] 風格G - 緊湊工業化專業F1工作站 (Compact Industrial F1 Workstation)
echo        • 基於風格D的緊湊版本
echo        • 平面化工業按鈕設計
echo        • 最小圓角+可拖動視窗
echo        • 緊湊高效專業布局
echo.
echo    [H] 風格H - 專業賽車分析工作站 (Professional Racing Analysis - Pure Black)
echo        • 移除參數面板，純黑底設計
echo        • 右鍵功能選單+系統日誌
echo        • 遙測曲線圖表+賽道地圖
echo        • 專業視窗控制+完善按鈕
echo.
echo    [Q] 離開
echo.
echo ═══════════════════════════════════════════════════════════════

set /p choice="請輸入你的選擇 (A/B/C/D/E/F/G/H/Q): "

if /i "%choice%"=="A" (
    echo.
    echo 🚀 啟動風格A Demo...
    echo 📋 現代扁平化設計界面
    echo.
    python gui_demo_style_a.py
) else if /i "%choice%"=="B" (
    echo.
    echo 🚀 啟動風格B Demo...
    echo 📋 專業工程設計界面
    echo.
    python gui_demo_style_b.py
) else if /i "%choice%"=="C" (
    echo.
    echo 🚀 啟動風格C Demo...
    echo 📋 90年代復古專業界面
    echo.
    python gui_demo_style_c.py
) else if /i "%choice%"=="D" (
    echo.
    echo 🚀 啟動風格D Demo...
    echo 📋 專業F1分析工作站界面
    echo.
    python gui_demo_style_d.py
) else if /i "%choice%"=="E" (
    echo.
    echo 🚀 啟動風格E Demo...
    echo 📋 MoTeC風格專業數據分析界面
    echo.
    python gui_demo_style_e.py
) else if /i "%choice%"=="F" (
    echo.
    echo 🚀 啟動風格F Demo...
    echo 📋 工業化專業F1分析工作站界面
    echo.
    python gui_demo_style_f.py
) else if /i "%choice%"=="G" (
    echo.
    echo 🚀 啟動風格G Demo...
    echo 📋 緊湊工業化專業F1工作站界面
    echo.
    python gui_demo_style_g.py
) else if /i "%choice%"=="H" (
    echo.
    echo 🚀 啟動風格H Demo...
    echo 📋 專業賽車分析工作站界面 (純黑底)
    echo.
    python gui_demo_style_h.py
) else if /i "%choice%"=="Q" (
    echo.
    echo 👋 感謝使用 F1T GUI Demo
    exit /b 0
) else (
    echo.
    echo ❌ 無效的選擇，請重新選擇
    echo.
    pause
    goto :eof
)

echo.
echo ✅ Demo 已關閉
echo 📋 感謝測試 F1T GUI 設計風格
pause
