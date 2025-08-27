@echo off
rem F1 Analysis Batch Processing - 參數化批次執行
rem 根據核心開發原則，提供無互動式的批次分析功能

echo ==========================================
echo F1 Analysis 批次處理系統
echo 參數化模式 - 符合核心開發原則
echo ==========================================

echo.
echo 🚀 選擇分析功能:
echo.
echo [基礎分析模組]
echo   1. 降雨強度分析
echo   2. 賽道路線分析
echo   3. 進站策略分析
echo   4. 事故分析
echo.
echo [單車手分析模組]
echo   5. 單一車手綜合分析
echo   6. 單一車手詳細遙測分析
echo   7. 車手對比分析
echo.
echo [全部車手分析模組]
echo   14.1 車手數據統計總覽
echo   14.2 車手遙測資料統計
echo   14.3 車手超車分析
echo   14.4 最速圈排名分析
echo.
echo [系統功能]
echo   19. 顯示模組狀態
echo   20. 顯示幫助信息
echo.

set /p FUNCTION_ID=請輸入功能編號: 

if "%FUNCTION_ID%"=="" (
    echo ❌ 未輸入功能編號
    pause
    exit /b 1
)

echo.
echo 🏁 選擇賽事參數:
echo.
echo 年份選項: 2024, 2025
set /p YEAR=請輸入年份 (預設: 2025): 
if "%YEAR%"=="" set YEAR=2025

echo.
echo 2025年賽事: Australia, China, Japan, Bahrain, Saudi Arabia, Miami,
echo             Monaco, Spain, Canada, Austria, Great Britain, Hungary,
echo             Belgium, Netherlands, Italy, Azerbaijan, Singapore,
echo             United States, Mexico, Brazil, Qatar, Abu Dhabi
echo.
set /p RACE=請輸入賽事名稱 (預設: Japan): 
if "%RACE%"=="" set RACE=Japan

echo.
echo 賽段類型: R(正賽), Q(排位賽), FP1/FP2/FP3(練習賽), S(衝刺賽)
set /p SESSION=請輸入賽段類型 (預設: R): 
if "%SESSION%"=="" set SESSION=R

echo.
echo ==========================================
echo 🚀 開始執行分析...
echo ==========================================
echo 參數: Year=%YEAR%, Race=%RACE%, Session=%SESSION%, Function=%FUNCTION_ID%
echo.

rem 執行參數化分析
python f1_analysis_modular_main.py -y %YEAR% -r %RACE% -s %SESSION% -f %FUNCTION_ID%

echo.
echo ==========================================
if %ERRORLEVEL% equ 0 (
    echo ✅ 分析執行完成
) else (
    echo ❌ 分析執行失敗 (錯誤代碼: %ERRORLEVEL%)
)
echo ==========================================

echo.
echo 📊 輸出檔案位置:
echo   - JSON 數據: json/ 目錄
echo   - 圖表檔案: cache/ 目錄
echo   - 日誌檔案: logs/ 目錄
echo.

pause
