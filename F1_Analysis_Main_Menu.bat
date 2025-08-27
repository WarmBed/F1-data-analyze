@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title F1 Analysis CLI - 模組化版本 v5.5 - Function 17 動態彎道檢測升級版 (53個功能)

REM 設定工作目錄為批次檔案所在目錄
cd /d "%~dp0"

REM ================================================================================
REM F1 Analysis CLI - 模組化主程式批次版本
REM F1 Analysis CLI - Modular Main Program Batch Version
REM 版本: 5.5 - Function 17 動態彎道檢測升級版 (新增動態彎道檢測功能)
REM 作者: F1 Analysis Team
REM
REM 專用模組化主程式，負責呼叫各個獨立分析模組
REM 新增: Function 17 動態彎道檢測、Function 18-24 功能重新編號
REM 增強: AI動態彎道檢測、Function 18整合Function 17結果、完整53功能支援
REM 功能統計: 基礎功能10個 + 進階功能14個 + 分拆功能4個 + 預留功能19個 + 系統功能5個 = 總計53個功能
REM ================================================================================

REM 初始化變數，不設定預設值
set DEFAULT_YEAR=
set DEFAULT_RACE=
set DEFAULT_SESSION=

:main_menu
cls
echo ================================================================================
echo                F1 Analysis CLI - 模組化版本 v5.5 - Function 17 動態彎道檢測升級版
echo                F1 Telemetry Analysis - Dynamic Corner Detection Enhanced Edition
echo ================================================================================
echo  🏎️  基於 FastF1 和 OpenF1 的專業F1遙測分析系統
echo  📊  完全模組化設計，支援2024-2025年賽季數據  
echo  🎯  新增: Function 17 動態彎道檢測、AI驅動彎道分析
echo  ✅  53個功能完整支援，Function 18整合Function 17結果
echo ================================================================================
echo.
echo 🔧 初始化系統 - 請選擇要分析的賽事
echo ================================================================================
echo.
set /p DEFAULT_YEAR="請輸入賽季年份 (2024/2025，直接按 Enter 使用 2025): "
if "%DEFAULT_YEAR%"=="" (
    set DEFAULT_YEAR=2025
    echo ✅ 使用預設年份: 2025
)

echo.
echo 正在載入 %DEFAULT_YEAR% 年賽事列表...
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% --list-races

echo.
REM 根據年份設置賽事編號範圍提示
if "%DEFAULT_YEAR%"=="2024" (
    set /p race_choice="請選擇賽事編號 (1-24，或直接按 Enter 使用 Japan): "
) else (
    set /p race_choice="請選擇賽事編號 (1-22，或直接按 Enter 使用 Japan): "
)
if "%race_choice%"=="" (
    set DEFAULT_RACE=Japan
    echo ✅ 使用預設賽事: Japan
) else (
    set DEFAULT_RACE=%race_choice%
)

echo.
echo 🏎️  賽段類型選項:
echo    R  - 正賽 (Race)
echo    Q  - 排位賽 (Qualifying)
echo    FP1, FP2, FP3 - 自由練習
echo    S  - 短衝刺賽 (Sprint)
set /p DEFAULT_SESSION="請輸入賽段類型 (直接按 Enter 使用 R): "
if "%DEFAULT_SESSION%"=="" (
    set DEFAULT_SESSION=R
    echo ✅ 使用預設賽段類型: R
)

cls
echo ================================================================================
echo                🏎️  F1 賽事分析 CLI 模組化版本 v5.5 - 共53個分析功能
echo ================================================================================
if "%session_loaded%"=="true" (
    echo 📊 數據狀態: ✅ 已載入賽事數據
) else (
    echo 📊 數據狀態: ❌ 尚未載入賽事數據
)
echo 當前設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo ================================================================================
echo.
echo 🎯 功能統計摘要:
echo    📊 基礎功能: 10 個 (1-10)
echo    🔧 進階功能: 14 個 (11-24) ⭐ 包含新Function 17動態彎道檢測
echo    🏎️ 分拆功能: 4 個 (25-28) 
echo    🚀 預留功能: 19 個 (29-47)
echo    ✅ 系統功能: 5 個 (49-53)
echo    🏆 總功能數: 53 個整數化功能 (新增動態彎道檢測)
echo ================================================================================ 
echo.
echo 基礎分析模組 (1-10)
echo 1.  🌧️ 降雨強度分析                 (Rain Intensity Analysis)
echo 2.  🛣️ 賽道路線分析                 (Track Path Analysis)
echo 3.  🏆 車手最快進站時間排行榜       (Driver Fastest Pitstop Ranking)
echo 4.  🏁 車隊進站時間排行榜           (Team Pitstop Ranking)
echo 5.  🛞 車手進站詳細記錄             (Driver Detailed Pitstop Records)
echo 6.  🚨 事故統計摘要分析             (Accident Statistics Summary)
echo 7.  ⚠️ 嚴重程度分佈分析             (Severity Distribution Analysis)
echo 8.  📋 所有事件詳細列表分析         (All Incidents Summary)
echo 9.  🚨 特殊事件報告分析             (Special Incident Reports)
echo 10. 🔑 關鍵事件摘要分析             (Key Events Summary)
echo.
echo 進階分析模組 (11-24) ⭐ 新增Function 17
echo 11. 🏎️ 單一車手綜合分析             (Single Driver Comprehensive Analysis) ⚠️ DEPRECATED
echo 12. 📡 單一車手詳細遙測分析         (Single Driver Detailed Telemetry)
echo 13. 🤝 雙車手比較分析               (Two Driver Comparison)
echo 14. 📈 賽事位置變化圖               (Race Position Changes Chart) ⚠️ DEPRECATED
echo 15. � 賽事超車統計分析             (Race Overtaking Statistics)
echo 16. 🏁 單一車手超車分析             (Single Driver Overtaking Analysis)
echo 17. 🎯 動態彎道檢測分析 ⭐ 新功能   (Dynamic Corner Detection Analysis)
echo 18. � 彎道詳細分析                 (Corner Detailed Analysis - 整合F17)
echo 19. � 單一車手DNF分析              (Single Driver DNF Analysis)
echo 20. �📊 單一車手全部彎道詳細分析     (Single Driver All Corners Analysis)
echo 21. 👥 所有車手綜合分析             (All Drivers Comprehensive Analysis)
echo 22. 🚀 彎道速度分析                 (Corner Speed Analysis) ⚠️ DEPRECATED
echo 23. 🏎️ 全部車手超車分析             (All Drivers Overtaking Analysis)
echo 24. 📊 全部車手DNF分析              (All Drivers DNF Analysis)
echo.
echo 分拆的單一車手分析 (25-28)
echo 25. 🏁 車手比賽位置分析             (Driver Race Position Analysis)
echo 26. 🛞 車手輪胎策略分析             (Driver Tire Strategy Analysis)  
echo 27. ⚡ 車手最速圈速分析             (Driver Fastest Lap Analysis)
echo 28. ⏱️ 車手每圈圈速分析             (Driver Lap Time Analysis)
echo.
echo 系統功能 (49-53)
echo 49. � 數據導出管理                 (Data Export Management)
echo 50. � 暫存優化                     (Cache Optimization)
echo 51. � 系統診斷                     (System Diagnostics)
echo 52. ⚡ 性能基準測試                 (Performance Benchmarking)
echo 53. 🛡️ 數據完整性檢查               (Data Integrity Check)
echo.
echo 設定功能
echo S.  ⚙️ 重新設定賽事參數             (Change Race Settings)
echo L.  📋 列出支援的賽事               (List Supported Races)
echo C.  🔍 暫存狀態檢查                 (Check Cache Status)  
echo D.  🔍 DNF暫存檢查                  (Check DNF Cache)
echo E.  📖 顯示參數使用範例             (Show Parameter Examples)
echo.
echo 0.  退出程式 (Exit)
echo.
echo ================================================================================
echo 🎯 Function 17 動態彎道檢測: AI驅動的智能彎道識別，支援18彎道精確檢測
echo 📋 可用功能編號: 1-28 (基礎+進階+分拆), 29-47 (預留), 49-53 (系統)
echo 🔧 新增參數支援: -d VER (車手), -d2 LEC (第二車手), --lap 1 (圈數), --show-detailed-output (詳細模式)
echo ✅ 系統功能: S(重新設定) L(列出賽事) C(檢查暫存) D(檢查DNF暫存) E(使用範例) 0(退出)
echo ⭐ Function 18 已整合 Function 17 結果，實現智能彎道分析
echo ================================================================================
echo.

set /p choice="請選擇功能編號: "

if /i "%choice%"=="0" goto exit
if /i "%choice%"=="S" goto settings
if /i "%choice%"=="L" goto list_races
if /i "%choice%"=="C" goto check_cache
if /i "%choice%"=="D" goto check_dnf_cache
if /i "%choice%"=="E" goto show_examples

REM 基礎分析模組 (1-10)
if "%choice%"=="1" goto function_1
if "%choice%"=="2" goto function_2
if "%choice%"=="3" goto function_3
if "%choice%"=="4" goto function_4
if "%choice%"=="5" goto function_5
if "%choice%"=="6" goto function_6
if "%choice%"=="7" goto function_7
if "%choice%"=="8" goto function_8
if "%choice%"=="9" goto function_9
if "%choice%"=="10" goto function_10

REM 進階分析模組 (11-24) ⭐ 包含新Function 17
if "%choice%"=="11" goto function_11
if "%choice%"=="12" goto function_12
if "%choice%"=="13" goto function_13
if "%choice%"=="14" goto function_14
if "%choice%"=="15" goto function_15
if "%choice%"=="16" goto function_16
if "%choice%"=="17" goto function_17
if "%choice%"=="18" goto function_18
if "%choice%"=="19" goto function_19
if "%choice%"=="20" goto function_20
if "%choice%"=="21" goto function_21
if "%choice%"=="22" goto function_22
if "%choice%"=="23" goto function_23
if "%choice%"=="24" goto function_24

REM 分拆的單一車手分析功能 (25-28)
if "%choice%"=="25" goto function_25
if "%choice%"=="26" goto function_26
if "%choice%"=="27" goto function_27
if "%choice%"=="28" goto function_28

REM 系統功能 (49-53)
if "%choice%"=="49" goto function_49
if "%choice%"=="50" goto function_50
if "%choice%"=="51" goto function_51
if "%choice%"=="52" goto function_52
if "%choice%"=="53" goto function_53
if "%choice%"=="52" goto function_52

echo 無效的選擇，請輸入有效的選項！
pause
goto main_menu

:settings
cls
echo ================================================================================
echo 重新設定賽事參數 (Change Race Settings)
echo ================================================================================
echo.
echo 當前設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 請輸入新的設定:
echo.

set /p new_year="賽季年份 (2024/2025，直接按 Enter 保持原設定): "
if "%new_year%"=="" (
    echo 保持原設定: %DEFAULT_YEAR%
) else (
    set DEFAULT_YEAR=%new_year%
)

echo.
echo 正在載入 %DEFAULT_YEAR% 年賽事列表...
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% --list-races

echo.
set /p new_race="請選擇賽事編號或輸入賽事名稱 (直接按 Enter 保持原設定): "
if "%new_race%"=="" (
    echo 保持原設定: %DEFAULT_RACE%
) else (
    set DEFAULT_RACE=%new_race%
)

echo.
echo 🏎️  賽段類型選項:
echo    R  - 正賽 (Race)
echo    Q  - 排位賽 (Qualifying)
echo    FP1, FP2, FP3 - 自由練習
echo    S  - 短衝刺賽 (Sprint)
set /p new_session="請輸入賽段類型 (直接按 Enter 保持原設定): "
if "%new_session%"=="" (
    echo 保持原設定: %DEFAULT_SESSION%
) else (
    set DEFAULT_SESSION=%new_session%
)

echo.
echo 設定已更新為: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 賽段類型說明:
echo    R  = 正賽 (Race)
echo    Q  = 排位賽 (Qualifying)  
echo    FP1/FP2/FP3 = 練習賽 (Free Practice)
echo    S  = 短衝刺賽 (Sprint)
echo.
pause
goto main_menu

:list_races
cls
echo ================================================================================
echo 列出支援的賽事 (List Supported Races)
echo ================================================================================
echo.
python f1_analysis_modular_main.py --list-races
echo.
pause
goto main_menu

:function_1
cls
echo ================================================================================
echo 功能1: 降雨強度分析 (Rain Intensity Analysis)
echo ================================================================================
echo.
echo 正在執行降雨強度分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 1
echo.
echo 降雨強度分析完成！
echo.
pause
goto main_menu

:function_2
cls
echo ================================================================================
echo 功能2: 賽道路線分析 (Track Path Analysis)
echo ================================================================================
echo.
echo 正在執行賽道路線分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 2
echo.
echo 賽道路線分析完成！
echo.
pause
goto main_menu

:function_3
cls
echo ================================================================================
echo 功能3: 車手最快進站時間排行榜 (Driver Fastest Pitstop Ranking)
echo ================================================================================
echo.
echo 正在執行車手最快進站時間排行榜...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 3
echo.
echo 車手最快進站時間排行榜完成！
echo.
pause
goto main_menu

:function_4
cls
echo ================================================================================
echo 功能4: 車隊進站時間排行榜 (Team Pitstop Ranking)
echo ================================================================================
echo.
echo 正在執行車隊進站時間排行榜...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 4
echo.
echo 車隊進站時間排行榜完成！
echo.
pause
goto main_menu

:function_6
cls
echo ================================================================================
echo 功能6: 事故統計摘要分析 (Accident Statistics Summary)
echo ================================================================================
echo.
echo 正在執行事故統計摘要分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 6
echo.
echo 事故統計摘要分析完成！
echo.
pause
goto main_menu

:function_7
cls
echo ================================================================================
echo 功能7: 嚴重程度分佈分析 (Severity Distribution Analysis)
echo ================================================================================
echo.
echo 正在執行嚴重程度分佈分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 7
echo.
echo 嚴重程度分佈分析完成！
echo.
pause
goto main_menu

:function_8
cls
echo ================================================================================
echo 功能8: 所有事件詳細列表分析 (All Incidents Summary)
echo ================================================================================
echo.
echo 正在執行所有事件詳細列表分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 8
echo.
echo 所有事件詳細列表分析完成！
echo.
pause
goto main_menu

:function_9
cls
echo ================================================================================
echo 功能9: 特殊事件報告分析 (Special Incident Reports)
echo ================================================================================
echo.
echo 正在執行特殊事件報告分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 9
echo.
echo 特殊事件報告分析完成！
echo.
pause
goto main_menu

:function_10
cls
echo ================================================================================
echo 功能10: 關鍵事件摘要分析 (Key Events Summary)
echo ================================================================================
echo.
echo 正在執行關鍵事件摘要分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 10
echo.
echo 關鍵事件摘要分析完成！
echo.
pause
goto main_menu

:function_11
cls
echo ================================================================================
echo 功能11: 單一車手綜合分析 (Single Driver Comprehensive Analysis) ⚠️ DEPRECATED
echo ================================================================================
echo ⚠️⚠️⚠️ 此功能已於 2025年8月9日 正式廢棄 ⚠️⚠️⚠️
echo.
echo ❌ 功能狀態: 已廢棄，不再維護
echo 📋 廢棄原因: 功能整合優化，已被其他專業分析功能取代
echo.
echo 💡 建議替代方案:
echo    • 功能12: 單一車手詳細遙測分析
echo    • 功能16: 單一車手超車分析
echo    • 功能25: 車手比賽位置分析
echo    • 功能26: 車手輪胎策略分析
echo.
echo 🔄 正在執行廢棄功能檢查...
echo 功能說明:
echo    - 車手基本統計資訊
echo    - 圈速分析 (最快圈、平均圈速)
echo    - 比賽位置分析 (起始位置vs最終位置)
echo    - 輪胎策略統計
echo    - 進站策略摘要
echo    - JSON格式完整數據輸出
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 11
echo.
:function_12
cls
echo ================================================================================
echo 功能12: 單一車手詳細遙測分析 (Single Driver Detailed Telemetry)
echo ================================================================================
echo.
echo 🎯 本功能支援多種分析模式:
echo    1. 自動車手選擇 (系統自動選擇第一位車手)
echo    2. 指定車手分析 (手動指定車手代碼)
echo    3. 指定圈數分析 (使用 --lap 參數)
echo    4. 詳細輸出控制 (使用 --show-detailed-output 或 --no-detailed-output)
echo.
echo 📋 範例命令:
echo    - 自動模式: f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 12
echo    - 指定車手: f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 12 -d VER
echo    - 指定圈數: f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 12 -d VER --lap 1
echo    - 快速模式: f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 12 -d VER --no-detailed-output
echo.
echo 正在執行單一車手詳細遙測分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 12
echo.
echo 單一車手詳細遙測分析完成！
echo.
pause
goto main_menu

:function_13
cls
echo ================================================================================
echo 功能13: 雙車手比較分析 (Two Driver Comparison)
echo ================================================================================
echo.
echo 🎯 本功能支援多種比較模式:
echo    1. 最快圈比較 (預設模式)
echo    2. 指定圈數比較 (使用 --lap 參數)
echo    3. 不同車手不同圈數比較
echo    4. 詳細輸出控制 (支援 --show-detailed-output)
echo.
echo 📋 範例命令:
echo    - 最快圈比較: f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 13 -d VER -d2 LEC
echo    - 指定圈數: f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 13 -d VER -d2 LEC --lap 1
echo    - 快速模式: f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 13 -d VER -d2 LEC --no-detailed-output
echo.
echo 正在執行雙車手比較分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 13 -d VER -d2 LEC
echo.
echo 雙車手比較分析完成！
echo.
pause
goto main_menu

:function_14
cls
echo ================================================================================
echo 功能14: 賽事位置變化圖 (Race Position Changes Chart) ⚠️ DEPRECATED
echo ================================================================================
echo ⚠️⚠️⚠️ 此功能已於 2025年8月9日 正式廢棄 ⚠️⚠️⚠️
echo.
echo ❌ 功能狀態: 已廢棄，不再維護
echo 📋 廢棄原因: 圖表生成功能重複，已被更專業的分析功能取代
echo.
echo 💡 建議替代方案:
echo    • 功能15: 賽事超車統計分析
echo    • 功能21: 所有車手綜合分析  
echo    • 功能25: 車手比賽位置分析
echo.
echo 🔄 正在執行廢棄功能檢查...
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 14
echo.
echo 賽事位置變化圖分析完成！
echo.
pause
goto main_menu

:function_15
cls
echo ================================================================================
echo 功能15: 賽事超車統計分析 (Race Overtaking Statistics)
echo ================================================================================
echo.
echo 正在執行賽事超車統計分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 15
echo.
echo 賽事超車統計分析完成！
echo.
pause
goto main_menu

:function_16
cls
echo ================================================================================
echo 功能16: 單一車手超車分析 (Single Driver Overtaking Analysis)
echo ================================================================================
echo.
echo 正在執行單一車手超車分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 16
echo.
echo 單一車手超車分析完成！
echo.
pause
goto main_menu

:function_17
cls
echo ================================================================================
echo 功能17: 動態彎道檢測分析 ⭐ 新功能 (Dynamic Corner Detection Analysis)
echo ================================================================================
echo.
echo 正在執行動態彎道檢測分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 🎯 Function 17 - AI驅動的智能彎道識別
echo "📊 支援自動檢測18個彎道的精確位置"
echo 🔍 使用速度下降和方向變化進行檢測
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -d VER -f 17
echo.
echo 動態彎道檢測分析完成！
echo.
pause
goto main_menu

:function_18
cls
echo ================================================================================
echo 功能18: 單一車手單彎道分析 (Single Driver Single Corner Analysis)
echo ================================================================================
echo.
echo 正在執行單一車手單彎道分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 🎯 Function 18 - 單一車手單彎道分析
echo 📊 使用AI檢測的精確彎道位置進行詳細分析
echo 🔍 智能回退機制，確保分析可靠性
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -d VER -f 18
echo.
echo 單一車手單彎道分析完成！
echo.
pause
goto main_menu

:function_19
cls
echo ================================================================================
echo 功能19: 單一車手DNF分析 (Single Driver DNF Analysis)
echo ================================================================================
echo.
echo 正在執行單一車手DNF分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 19
echo.
echo 單一車手DNF分析完成！
echo.
pause
goto main_menu

:function_20
cls
echo ================================================================================
echo 功能20: 單一車手全部彎道詳細分析 (Single Driver All Corners Analysis)
echo ================================================================================
echo.
echo 正在執行單一車手全部彎道詳細分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 20
echo.
echo 單一車手全部彎道詳細分析完成！
echo.
pause
goto main_menu

:function_21
cls
echo ================================================================================
echo 功能21: 所有車手綜合分析 (All Drivers Comprehensive Analysis)
echo ================================================================================
echo.
echo 正在執行所有車手綜合分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 21
echo.
echo 彎道速度分析完成！
echo.
pause
goto main_menu

:function_22
cls
echo ================================================================================
echo 功能22: 彎道速度分析 (Corner Speed Analysis) ⚠️ DEPRECATED
echo ================================================================================
echo ⚠️⚠️⚠️ 此功能已於 2025年8月9日 正式廢棄 ⚠️⚠️⚠️
echo.
echo ❌ 功能狀態: 已廢棄，不再維護
echo 📋 廢棄原因: 分析功能重複，已被更專業的彎道分析功能取代
echo.
echo 💡 建議替代方案:
echo    • 功能17: 動態彎道檢測分析
echo    • 功能18: 彎道詳細分析
echo    • 功能20: 單一車手全部彎道分析
echo.
echo 🔄 正在執行廢棄功能檢查...
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 22
echo.
echo 彎道速度分析完成！
echo.
pause
goto main_menu

:function_23
cls
echo ================================================================================
echo 功能23: 全部車手超車分析 (All Drivers Overtaking Analysis)
echo ================================================================================
echo.
echo 正在執行全部車手超車分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 23
echo.
echo 全部車手超車分析完成！
echo.
pause
goto main_menu

:function_24
cls
echo ================================================================================
echo 功能24: 全部車手DNF分析 (All Drivers DNF Analysis)
echo ================================================================================
echo.
echo 正在執行全部車手DNF分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 24
echo.
echo 全部車手DNF分析完成！
echo.
pause
goto main_menu

:function_25
cls
echo ================================================================================
echo 功能25: 車手比賽位置分析 (Driver Race Position Analysis)
echo ================================================================================
echo.
echo 正在執行車手比賽位置分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 25
echo.
echo 車手比賽位置分析完成！
echo.
pause
goto main_menu
echo ================================================================================
echo 功能25: 車手輪胎策略分析 (Driver Tire Strategy Analysis)
echo ================================================================================
echo.
echo 正在執行車手輪胎策略分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo 車手: %DEFAULT_DRIVER%
echo.
echo python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -d %DEFAULT_DRIVER% -f 25
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -d %DEFAULT_DRIVER% -f 25
pause
goto main_menu

:function_26
cls
echo ================================================================================
echo 功能26: 車手最速圈速分析 (Driver Fastest Lap Analysis)
echo ================================================================================
echo.
echo 正在執行車手最速圈速分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo 車手: %DEFAULT_DRIVER%
echo.
echo python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -d %DEFAULT_DRIVER% -f 26
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -d %DEFAULT_DRIVER% -f 26
pause
goto main_menu

:function_27
cls
echo ================================================================================
echo 功能27: 車手每圈圈速分析 (Driver Lap Time Analysis)
echo ================================================================================
echo 分析內容包含:
echo • 每一圈的圈速時間
echo • 使用的輪胎配方和胎齡
echo • 進站標記和天氣情況
echo • I1速度、I2速度、終點速度
echo • 特殊事件備註 (進站、黃旗、安全車等)
echo ================================================================================
echo.
echo 正在執行車手每圈圈速詳細分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo 車手: %DEFAULT_DRIVER%
echo.
echo python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -d %DEFAULT_DRIVER% -f 27
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -d %DEFAULT_DRIVER% -f 27
pause
goto main_menu

:function_48
cls
echo ================================================================================
echo 功能48: 重新載入賽事數據 (Reload Race Data)
echo ================================================================================
echo.
echo 正在重新載入賽事數據...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 48
echo.
echo 賽事數據重新載入完成！
echo.
pause
goto main_menu

:function_49
cls
echo ================================================================================
echo 功能49: 數據導出管理 (Data Export Management)
echo ================================================================================
echo.
echo 正在執行數據導出管理...
echo.
python f1_analysis_modular_main.py -f 49
echo.
echo 數據導出管理完成！
echo.
pause
goto main_menu

:function_50
cls
echo ================================================================================
echo 功能50: 暫存優化 (Cache Optimization)
echo ================================================================================
echo.
echo 正在執行暫存優化...
echo.
python f1_analysis_modular_main.py -f 50
echo.
echo 暫存優化完成！
echo.
pause
goto main_menu

:function_51
cls
echo ================================================================================
echo 功能51: 系統診斷 (System Diagnostics)
echo ================================================================================
echo.
echo 正在執行系統診斷...
echo.
python f1_analysis_modular_main.py -f 51
echo.
echo 系統診斷完成！
echo.
pause
goto main_menu

:function_52
cls
echo ================================================================================
echo 功能52: 性能基準測試 (Performance Benchmarking)
echo ================================================================================
echo.
echo 正在執行性能基準測試...
echo.
python f1_analysis_modular_main.py -f 52
echo.
echo 性能基準測試完成！
echo.
pause
goto main_menu

:function_53
cls
echo ================================================================================
echo 功能53: 數據完整性檢查 (Data Integrity Check)
echo ================================================================================
echo.
echo 正在執行數據完整性檢查...
echo.
python f1_analysis_modular_main.py -f 53
echo.
echo 數據完整性檢查完成！
echo.
pause
goto main_menu

:driver_statistics_overview
cls
echo ================================================================================
echo 車手數據統計總覽 (Driver Statistics Overview) - 功能 14.1
echo ================================================================================
echo.
echo 正在執行車手數據統計總覽分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 功能說明:
echo    - 車手基本數據統計（按比賽名次排序）
echo    - 輪胎策略分析
echo    - 比賽成績統計
echo    - JSON格式數據輸出
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 14.1
echo.
echo 車手數據統計總覽分析完成！
echo.
pause
goto main_menu

:driver_telemetry_statistics
cls
echo ================================================================================
echo 車手遙測資料統計 (Driver Telemetry Statistics) - 功能 14.2
echo ================================================================================
echo.
echo 正在執行車手遙測資料統計分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 功能說明:
echo    - 車手遙測數據統計（按比賽名次排序）
echo    - 油門、煞車、速度、轉速分析
echo    - 遙測性能對比
echo    - JSON格式數據輸出
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 14.2
echo.
echo 車手遙測資料統計分析完成！
echo.
pause
goto main_menu

:driver_overtaking_analysis
cls
echo ================================================================================
echo 車手超車分析 (Driver Overtaking Analysis) - 功能 14.3
echo ================================================================================
echo.
echo 正在執行車手超車分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 功能說明:
echo    - 車手超車分析（當前比賽）
echo    - 超車次數與被超次數統計
echo    - 名次變化分析
echo    - JSON格式數據輸出
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 14.3
echo.
echo 車手超車分析完成！
echo.
pause
goto main_menu

:driver_fastest_lap_ranking
cls
echo ================================================================================
echo 最速圈排名分析 (Fastest Lap Ranking Analysis) - 功能 14.4
echo ================================================================================
echo.
echo 正在執行最速圈排名分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 功能說明:
echo    - 最速圈排名分析（含區間時間）
echo    - 各車手最佳單圈時間對比
echo    - 分段時間詳細分析
echo    - 輪胎使用策略統計
echo    - JSON格式數據輸出
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 14.4
echo.
echo 最速圈排名分析完成！
echo.
pause
goto main_menu

:all_drivers_comprehensive
cls
echo ================================================================================
echo 完整綜合分析 (Full Comprehensive Analysis) - 功能 14.9
echo ================================================================================
echo.
echo 正在執行完整綜合分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 功能說明:
echo    - 包含所有車手綜合分析功能
echo    - 統計、遙測、超車三合一分析
echo    - 完整的JSON數據輸出
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 14.9
echo.
echo 完整綜合分析完成！
echo.
pause
goto main_menu

:all_drivers_analysis
cls
echo ================================================================================
echo 所有車手綜合分析 (All Drivers Comprehensive Analysis) - 功能 14
echo ================================================================================
echo.
echo 💡 提示: 此功能已拆分為多個子功能，您可以選擇:
echo    14.1 📊 車手數據統計總覽
echo    14.2 🔧 車手遙測資料統計  
echo    14.3 🚀 車手超車分析
echo    14.4 🏆 最速圈排名分析
echo    14.9 👥 完整綜合分析 (包含以上所有功能)
echo.
echo 正在執行完整綜合分析 (相當於功能 14.9)...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 14
echo.
echo 所有車手綜合分析完成！
echo.
pause
goto main_menu

:pitstop_analysis
cls
echo ================================================================================
echo 進站策略分析 (Pitstop Strategy Analysis)
echo ================================================================================
echo.
echo 正在執行進站策略分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 3
echo.
echo 進站策略分析完成！
echo.
pause
goto main_menu

:race_pitstop_statistics
cls
echo ================================================================================
echo 單場賽事進站統計分析 (Race Pitstop Statistics + Table + JSON)
echo ================================================================================
echo.
echo 正在執行單場賽事進站統計分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 功能說明:
echo    - 每位車手進站次數統計
echo    - 進站對應圈數詳細記錄  
echo    - 進站類型與時間分析 (含OpenF1精確時間)
echo    - 表格格式清晰顯示 (按車手分類)
echo    - JSON格式完整輸出
echo    - 支援OpenF1 API + FastF1雙重數據源
echo 結果保存為統計表格和JSON檔案
echo.
echo 注意：此功能為進站策略分析的統計子功能 (增強雙重數據源版)
echo 啟動單場賽事進站統計分析模組...
echo.
python modules\race_pitstop_statistics_enhanced.py %DEFAULT_YEAR% %DEFAULT_RACE% %DEFAULT_SESSION%
echo.
echo 單場賽事進站統計分析完成！
echo.
pause
goto main_menu

:accident_analysis
cls
echo ================================================================================
echo 獨立事故分析 (Independent Accident Analysis)
echo ================================================================================
echo.
echo 正在執行獨立事故分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 4
echo.
echo 獨立事故分析完成！
echo.
pause
goto main_menu

:telemetry_analysis
cls
echo ================================================================================
echo 單一車手詳細遙測分析 (Single Driver Detailed Telemetry)
echo ================================================================================
echo.
echo 正在執行單一車手詳細遙測分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 6
echo.
echo 單一車手詳細遙測分析完成！
echo.
pause
goto main_menu

:driver_comparison
cls
echo ================================================================================
echo 車手對比分析 (Driver Comparison)
echo ================================================================================
echo.
echo 正在執行車手對比分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 7
echo.
echo 車手對比分析完成！
echo.
pause
goto main_menu

:single_overtaking
cls
echo ================================================================================
echo 單一車手超車分析 (Single Driver Overtaking Analysis)
echo ================================================================================
echo.
echo 正在執行單一車手超車分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 此功能會分析:
echo    - 車手超車表現統計
echo    - 超車趨勢分析
echo    - 統計圖表製作
echo 結果保存為圖表檔案
echo.
echo 注意：位置變化圖已拆分至功能8 (賽事位置變化圖)
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 10
echo.
echo 單一車手超車分析完成！
echo.
pause
goto main_menu

:all_overtaking_submenu
cls
echo ================================================================================
echo 全部車手超車分析子選單 (All Drivers Overtaking Submenu)
echo ================================================================================
echo.
echo 請選擇分析類型:
echo 16.1 📊 年度超車統計               (Annual Overtaking Statistics)
echo 16.2 🏁 表現比較分析               (Performance Comparison)
echo 16.3 📈 視覺化分析                 (Visualization Analysis)
echo 16.4 📈 趨勢分析                   (Trends Analysis)
echo 0.   ↩️ 返回主選單                 (Back to Main Menu)
echo.
set /p submenu_choice=請輸入選項 (16.1, 16.2, 16.3, 16.4, 0): 

if "%submenu_choice%"=="16.1" goto all_drivers_annual_overtaking_statistics
if "%submenu_choice%"=="16.2" goto all_drivers_overtaking_performance_comparison
if "%submenu_choice%"=="16.3" goto all_drivers_overtaking_visualization_analysis
if "%submenu_choice%"=="16.4" goto all_drivers_overtaking_trends_analysis
if "%submenu_choice%"=="0" goto main_menu

echo 無效的選擇，請輸入有效的選項！
pause
goto all_overtaking_submenu

:all_drivers_annual_overtaking_statistics
cls
echo ================================================================================
echo 年度超車統計分析 (Annual Overtaking Statistics)
echo ================================================================================
echo.
echo 正在執行年度超車統計分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 16.1
echo.
echo 年度超車統計分析完成！
echo.
pause
goto main_menu

:all_drivers_overtaking_performance_comparison
cls
echo ================================================================================
echo 表現比較分析 (Performance Comparison)
echo ================================================================================
echo.
echo 正在執行表現比較分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 16.2
echo.
echo 表現比較分析完成！
echo.
pause
goto main_menu

:all_drivers_overtaking_visualization_analysis
cls
echo ================================================================================
echo 視覺化分析 (Visualization Analysis)
echo ================================================================================
echo.
echo 正在執行視覺化分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 16.3
echo.
echo 視覺化分析完成！
echo.
pause
goto main_menu

:all_drivers_overtaking_trends_analysis
cls
echo ================================================================================
echo 趨勢分析 (Trends Analysis)
echo ================================================================================
echo.
echo 正在執行趨勢分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 16.4
echo.
echo 趨勢分析完成！
echo.
pause
goto main_menu

:all_dnf_analysis
cls
echo ================================================================================
echo 獨立全部車手DNF分析 (Independent All Drivers DNF)
echo ================================================================================
echo.
echo 正在執行獨立全部車手DNF分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 15
echo.
echo 獨立全部車手DNF分析完成！
echo.
pause
goto main_menu

:single_dnf_analysis
cls
echo ================================================================================
echo 獨立單一車手DNF分析 (Independent Single Driver DNF)
echo ================================================================================
echo.
echo 正在執行獨立單一車手DNF分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 11
echo.
echo 獨立單一車手DNF分析完成！
echo.
pause
goto main_menu

:corner_speed_analysis
cls
echo ================================================================================
echo 彎道速度分析 (Corner Speed Analysis)
echo ================================================================================
echo.
echo 正在執行彎道速度分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 15
echo.
echo 彎道速度分析完成！
echo.
pause
goto main_menu

:corner_detailed_analysis
cls
echo ================================================================================
echo 單賽事指定彎道詳細分析 (Single Race Specific Corner Detailed Analysis)
echo ================================================================================
echo.
echo 正在執行單賽事指定彎道詳細分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 12
echo.
echo 單賽事指定彎道詳細分析完成！
echo.
pause
goto main_menu

:single_driver_all_corners_analysis
cls
echo ================================================================================
echo 單一車手指定賽事全部彎道詳細分析 (Single Driver All Corners Detailed Analysis)
echo ================================================================================
echo.
echo 正在執行單一車手指定賽事全部彎道詳細分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 📊 綜合分析該車手在此賽事所有彎道的表現與穩定性...
echo 🎯 分析項目: 彎道速度、入彎/出彎表現、穩定性評分、與理想賽車線對比
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 13
echo.
echo 單一車手指定賽事全部彎道詳細分析完成！
echo.
pause
goto main_menu

:reload_data
cls
echo ================================================================================
echo 重新載入賽事數據 (Reload Race Data)
echo ================================================================================
echo.
echo 正在重新載入賽事數據...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 18
echo.
echo 賽事數據重新載入完成！
echo.
pause
goto main_menu

:show_status
cls
echo ================================================================================
echo 顯示模組狀態 (Show Module Status)
echo ================================================================================
echo.
echo 正在檢查模組狀態...
echo.
python f1_analysis_modular_main.py -f 19
echo.
echo 模組狀態檢查完成！
echo.
pause
goto main_menu

:show_help
cls
echo ================================================================================
echo 顯示幫助信息 (Show Help)
echo ================================================================================
echo.
echo 正在顯示幫助信息...
echo.
python f1_analysis_modular_main.py -f 20
echo.
echo 幫助信息顯示完成！
echo.
pause
goto main_menu

:cache_management
cls
echo ================================================================================
echo 超車暫存管理 (Overtaking Cache Management)
echo ================================================================================
echo.
echo 正在檢查超車分析暫存狀態...
echo.
python overtaking_cache_manager.py status
echo.
echo 暫存管理選項:
echo    - 檢查狀態: python overtaking_cache_manager.py status
echo    - 清理過期: python overtaking_cache_manager.py clean [天數]
echo    - 清空全部: python overtaking_cache_manager.py clear
echo.
echo 暫存狀態檢查完成！
echo.
pause
goto main_menu

:check_cache
cls
echo ================================================================================
echo 暫存狀態檢查 (Check Cache Status)
echo ================================================================================
echo.
echo 正在檢查所有暫存狀態...
echo.
python overtaking_cache_manager.py status
echo.
pause
goto main_menu

:check_dnf_cache
cls
echo ================================================================================
echo DNF暫存狀態檢查 (Check DNF Cache Status)
echo ================================================================================
echo.
echo 正在檢查DNF暫存狀態...
echo.
python dnf_cache_manager.py status
echo.
pause
goto main_menu

:dnf_cache_management
cls
echo ================================================================================
echo DNF暫存管理 (DNF Cache Management)
echo ================================================================================
echo.
echo 正在檢查DNF分析暫存狀態...
echo.
python dnf_cache_manager.py status
echo.
echo DNF暫存管理選項:
echo    - 檢查狀態: python dnf_cache_manager.py status
echo    - 清理過期: python dnf_cache_manager.py clean [天數]
echo    - 清空全部: python dnf_cache_manager.py clear
echo.
echo DNF暫存狀態檢查完成！
echo.
pause
goto main_menu

REM ================================================================================
REM 新增的事故分析子功能
REM ================================================================================

:accident_key_events
cls
echo ================================================================================
echo 關鍵事件摘要分析 (Key Events Summary)
echo ================================================================================
echo.
echo 正在執行關鍵事件摘要分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為獨立事故分析的子功能
echo 啟動獨立事故分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 4
echo.
echo 關鍵事件摘要分析完成！
echo.
pause
goto main_menu

:accident_special_incidents
cls
echo ================================================================================
echo 特殊事件報告分析 (Special Incident Reports)
echo ================================================================================
echo.
echo 正在執行特殊事件報告分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為獨立事故分析的子功能
echo 啟動獨立事故分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 4
echo.
echo 特殊事件報告分析完成！
echo.
pause
goto main_menu

:accident_driver_severity
cls
echo ================================================================================
echo 車手嚴重程度分數統計 (Driver Severity Scores)
echo ================================================================================
echo.
echo 正在執行車手嚴重程度分數統計...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為獨立事故分析的子功能
echo 啟動獨立事故分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 4
echo.
echo 車手嚴重程度分數統計完成！
echo.
pause
goto main_menu

:accident_team_risk
cls
echo ================================================================================
echo 車隊風險分數統計 (Team Risk Scores)
echo ================================================================================
echo.
echo 正在執行車隊風險分數統計...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為獨立事故分析的子功能
echo 啟動獨立事故分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 4
echo.
echo 車隊風險分數統計完成！
echo.
pause
goto main_menu

:accident_all_incidents
cls
echo ================================================================================
echo 所有事件詳細列表分析 (All Incidents Summary)
echo ================================================================================
echo.
echo 正在執行所有事件詳細列表分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為獨立事故分析的子功能
echo 啟動獨立事故分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 4
echo.
echo 所有事件詳細列表分析完成！
echo.
pause
goto main_menu

REM ================================================================================
REM 新增的遙測分析子功能
REM ================================================================================

:telemetry_complete_lap
cls
echo ================================================================================
echo 詳細圈次分析 (Complete Lap Analysis)
echo ================================================================================
echo.
echo 正在執行詳細圈次分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為單一車手詳細遙測分析的子功能
echo 啟動單一車手詳細遙測分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 6
echo.
echo 詳細圈次分析完成！
echo.
pause
goto main_menu

:telemetry_tire_strategy
cls
echo ================================================================================
echo 詳細輪胎策略分析 (Detailed Tire Strategy)
echo ================================================================================
echo.
echo 正在執行詳細輪胎策略分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為單一車手詳細遙測分析的子功能
echo 啟動單一車手詳細遙測分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 6
echo.
echo 詳細輪胎策略分析完成！
echo.
pause
goto main_menu

:telemetry_tire_performance
cls
echo ================================================================================
echo 輪胎性能詳細分析 (Tire Performance Analysis)
echo ================================================================================
echo.
echo 正在執行輪胎性能詳細分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為單一車手詳細遙測分析的子功能
echo 啟動單一車手詳細遙測分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 6
echo.
echo 輪胎性能詳細分析完成！
echo.
pause
goto main_menu

:telemetry_pitstop_records
cls
echo ================================================================================
echo 進站記錄分析 (Pitstop Records)
echo ================================================================================
echo.
echo 正在執行進站記錄分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為單一車手詳細遙測分析的子功能
echo 啟動單一車手詳細遙測分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 6
echo.
echo 進站記錄分析完成！
echo.
pause
goto main_menu

:telemetry_special_events
cls
echo ================================================================================
echo 特殊事件分析 (Special Events)
echo ================================================================================
echo.
echo 正在執行特殊事件分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為單一車手詳細遙測分析的子功能
echo 啟動單一車手詳細遙測分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 6
echo.
echo 特殊事件分析完成！
echo.
pause
goto main_menu

:telemetry_fastest_lap
cls
echo ================================================================================
echo 最快圈速度遙測數據 (Fastest Lap Speed Data)
echo ================================================================================
echo.
echo 正在執行最快圈速度遙測數據分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為單一車手詳細遙測分析的子功能
echo 啟動單一車手詳細遙測分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 6
echo.
echo 最快圈速度遙測數據分析完成！
echo.
pause
goto main_menu

:telemetry_specific_lap
cls
echo ================================================================================
echo 指定圈次完整遙測數據 (Specific Lap Full Telemetry)
echo ================================================================================
echo.
echo 正在執行指定圈次完整遙測數據分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 注意：此功能為單一車手詳細遙測分析的子功能
echo 啟動單一車手詳細遙測分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 6
echo.
echo 指定圈次完整遙測數據分析完成！
echo.
pause
goto main_menu

REM ================================================================================
REM 新增的雙車手比較分析子功能
REM ================================================================================

:speed_gap_analysis
cls
echo ================================================================================
echo 速度差距分析 + 原始數據預覽 (Speed Gap Analysis + Raw Data Preview)
echo ================================================================================
echo.
echo 正在執行速度差距分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 請輸入要比較的車手:
set /p DRIVER1="第一位車手代碼 (如: VER, LEC, HAM, 直接按 Enter 使用 VER): "
if "%DRIVER1%"=="" set DRIVER1=VER

set /p DRIVER2="第二位車手代碼 (如: LEC, HAM, NOR, 直接按 Enter 使用 LEC): "
if "%DRIVER2%"=="" set DRIVER2=LEC

echo.
echo 比較設定: %DRIVER1% vs %DRIVER2%
echo 注意：此功能為雙車手比較分析的子功能
echo 啟動雙車手比較分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 7.1 -d %DRIVER1% -d2 %DRIVER2%
echo.
echo 速度差距分析完成！
echo.
pause
goto main_menu

:distance_gap_analysis
cls
echo ================================================================================
echo 距離差距分析 + 原始數據預覽 (Distance Gap Analysis + Raw Data Preview)
echo ================================================================================
echo.
echo 正在執行距離差距分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 請輸入要比較的車手:
set /p DRIVER1="第一位車手代碼 (如: VER, LEC, HAM, 直接按 Enter 使用 VER): "
if "%DRIVER1%"=="" set DRIVER1=VER

set /p DRIVER2="第二位車手代碼 (如: LEC, HAM, NOR, 直接按 Enter 使用 LEC): "
if "%DRIVER2%"=="" set DRIVER2=LEC

echo.
echo 比較設定: %DRIVER1% vs %DRIVER2%
echo 注意：此功能為雙車手比較分析的子功能
echo 啟動雙車手比較分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 7.2 -d %DRIVER1% -d2 %DRIVER2%
echo.
echo 距離差距分析完成！
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 7.2
echo.
echo 距離差距分析完成！
echo.
pause
goto main_menu

REM ================================================================================
REM 新增的賽事位置變化圖功能
REM ================================================================================

:race_position_changes
cls
echo ================================================================================
echo 賽事位置變化圖 (Race Position Changes Chart)
echo ================================================================================
echo.
echo 正在執行賽事位置變化圖分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 功能說明:
echo    - 車手位置變化分析
echo    - 位置統計數據
echo    - 位置變化記錄
echo    - Raw Data 原始數據輸出
echo 結果僅輸出數據不生成圖片
echo.
echo 注意：此功能為位置變化視覺化的專門工具
echo 啟動位置變化分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 8
echo.
echo 賽事位置變化圖分析完成！
echo.
pause
goto main_menu

:race_overtaking_statistics
cls
echo ================================================================================
echo 賽事超車統計分析 (Race Overtaking Statistics)
echo ================================================================================
echo.
echo 正在執行賽事超車統計分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 分析功能說明:
echo    - 超車行為統計分析
echo    - 超車成功率分析
echo    - 超車區域分析
echo    - Raw Data 原始數據輸出
echo 結果自動保存為圖表檔案
echo.
echo 注意：此功能為超車行為的專門統計工具
echo 啟動超車統計分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 9
echo.
echo 賽事超車統計分析完成！
echo.
pause
goto main_menu

REM ================================================================================
REM 新增的DNF分析子功能
REM ================================================================================

:dnf_detailed_analysis
cls
echo ================================================================================
echo 詳細DNF與責任事故分析 (Detailed DNF & Incident Analysis)
echo ================================================================================
echo.
echo 正在執行詳細DNF與責任事故分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 請輸入要分析的車手:
set /p TARGET_DRIVER="目標車手代碼 (如: VER, LEC, HAM, 直接按 Enter 使用 VER): "
if "%TARGET_DRIVER%"=="" set TARGET_DRIVER=VER

echo.
echo 分析目標: %TARGET_DRIVER%
echo 功能說明:
echo    - DNF車手詳細分析
echo    - 責任事故判定
echo    - 圈速異常檢測
echo    - Raw Data 原始數據輸出
echo 結果保存為詳細報告檔案
echo.
echo 注意：此功能為DNF分析的詳細版本 (符合開發核心標準)
echo 啟動詳細DNF與責任事故分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 11.1 -d %TARGET_DRIVER%
echo.
echo 詳細DNF與責任事故分析完成！
echo.
pause
goto main_menu

:dnf_annual_statistics
cls
echo ================================================================================
echo 年度DNF統計摘要 - 全車手全年度報告 (Annual DNF Statistics Summary - All Drivers)
echo ================================================================================
echo.
echo 正在執行年度DNF統計摘要分析...
echo 賽事設定: %DEFAULT_YEAR% 年 (全年度分析，不限特定賽事)
echo.
echo 功能說明:
echo    - 全車手年度DNF統計分析
echo    - DNF原因分類與排名統計
echo    - 車手DNF可靠性評比
echo    - 車隊DNF風險分析
echo    - DNF嚴重程度趨勢分析
echo    - Raw Data 原始數據完整輸出
echo 結果保存為年度統計報告檔案
echo.
echo 注意：此功能分析整年度所有車手的DNF趨勢與比較
echo 啟動年度DNF統計摘要分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 11.2
echo.
echo 年度DNF統計摘要分析完成！
echo.
pause
goto main_menu

REM ================================================================================
REM 新增的彎道分析子功能 12.1 和 12.2
REM ================================================================================

:single_driver_corner_analysis
cls
echo ================================================================================
echo 單一車手詳細彎道分析 (Single Driver Corner Analysis + JSON)
echo ================================================================================
echo.
echo 正在執行單一車手詳細彎道分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 功能說明:
echo    - 預設車手: VER
echo    - 預設彎道: 第 1 彎
echo    - 詳細彎道性能分析
echo    - JSON 原始數據輸出
echo 結果保存為 JSON 分析報告
echo.
echo 注意：此功能為彎道分析的增強版本，含 JSON 輸出
echo 啟動單一車手詳細彎道分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 12.1
echo.
echo 單一車手詳細彎道分析完成！
echo.
pause
goto main_menu

:team_drivers_corner_comparison
cls
echo ================================================================================
echo 團隊車手對比彎道分析 (Team Drivers Corner Comparison + JSON)
echo ================================================================================
echo.
echo 正在執行團隊車手對比彎道分析...
echo 賽事設定: %DEFAULT_YEAR% 年 %DEFAULT_RACE% 站 %DEFAULT_SESSION% 賽段
echo.
echo 功能說明:
echo    - 預設車手: VER vs NOR
echo    - 預設彎道: 第 1 彎
echo    - 車手對比性能分析
echo    - 彎道優勢判定
echo    - JSON 原始數據輸出
echo 結果保存為 JSON 對比分析報告
echo.
echo 注意：此功能為彎道對比分析專門工具，含 JSON 輸出
echo 啟動團隊車手對比彎道分析模組...
echo.
python f1_analysis_modular_main.py -y %DEFAULT_YEAR% -r %DEFAULT_RACE% -s %DEFAULT_SESSION% -f 12.2
echo.
echo 團隊車手對比彎道分析完成！
echo.
pause
goto main_menu

:show_examples
cls
echo ================================================================================
echo 📖 F1 Analysis CLI - 參數使用範例和說明
echo ================================================================================
echo.
echo 🎯 基本參數說明:
echo    -y 年份     : 賽季年份 (2024 或 2025)
echo    -r 賽事     : 賽事名稱 (如: Japan, Bahrain, Australia)
echo    -s 賽段     : 賽段類型 (R=正賽, Q=排位賽, FP1/FP2/FP3=練習賽, S=短衝刺賽)
echo    -f 功能     : 功能編號 (1-52)
echo    -d 車手     : 主要車手代碼 (如: VER, LEC, HAM, PER, SAI)
echo    -d2 車手    : 次要車手代碼 (用於雙車手比較)
echo    --lap 圈數  : 指定圈數 (用於特定圈數分析)
echo.
echo 🔧 輸出控制參數:
echo    --show-detailed-output   : 強制顯示詳細輸出 (預設啟用)
echo    --no-detailed-output     : 快速模式，僅顯示摘要
echo    --list-races            : 列出支援的賽事列表
echo    --version               : 顯示版本資訊
echo.
echo ================================= 實用範例 =====================================
echo.
echo 📊 Function 12 - 單一車手詳細遙測分析:
echo    基本用法: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 12
echo    指定車手: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 12 -d VER
echo    指定圈數: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 12 -d VER --lap 1
echo    快速模式: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 12 -d VER --no-detailed-output
echo.
echo 🔄 Function 13 - 雙車手比較分析:
echo    最快圈比較: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 13 -d VER -d2 LEC
echo    指定圈數: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 13 -d VER -d2 LEC --lap 5
echo    詳細輸出: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 13 -d VER -d2 LEC --show-detailed-output
echo.
echo 📈 Function 15 - 賽事超車統計 (Function 15 標準範本):
echo    基本分析: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 15
echo    詳細模式: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 15 --show-detailed-output
echo    快速模式: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 15 --no-detailed-output
echo.
echo 🏎️ Function 11 - 單一車手綜合分析:
echo    指定車手: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 11 -d VER
echo    詳細輸出: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 11 -d VER --show-detailed-output
echo.
echo ============================= 進階功能範例 ===================================
echo.
echo 🔍 查看支援的賽事:
echo    python f1_analysis_modular_main.py -y 2025 --list-races
echo    python f1_analysis_modular_main.py -y 2024 --list-races
echo.
echo 🎯 Function 15 標準功能 (26個功能已升級):
echo    • 所有升級功能都支援 --show-detailed-output 和 --no-detailed-output
echo    • 預設啟用詳細輸出模式，即使有緩存也會顯示完整表格
echo    • 快速模式 (--no-detailed-output) 僅在緩存存在時顯示摘要
echo.
echo ========================== 常用車手代碼參考 ==============================
echo.
echo 🏆 2024-2025 主要車手代碼:
echo    Red Bull:    VER (Verstappen), PER (Perez)
echo    Ferrari:     LEC (Leclerc), SAI (Sainz)
echo    Mercedes:    HAM (Hamilton), RUS (Russell)
echo    McLaren:     NOR (Norris), PIA (Piastri)
echo    Aston Martin: ALO (Alonso), STR (Stroll)
echo    Alpine:      OCO (Ocon), GAS (Gasly)
echo.
echo ================================================================================
echo 💡 提示: 所有升級到 Function 15 標準的功能都支援智能緩存和詳細輸出控制
echo ✅ 升級進度: 26/53 功能 (49.1%) 已完成 Function 15 標準升級
echo ================================================================================
echo.
pause
goto main_menu

:exit
cls
echo ================================================================================
echo 感謝使用 F1 Analysis CLI - 模組化版本 v5.5 - Function 15 標準升級版
echo ================================================================================
echo.
echo 🏎️  F1 Telemetry Analysis - Enhanced Parameters & Output Control
echo 📊  完全模組化設計，支援2024-2025年賽季數據
echo 🎯  新增: Function 17 動態彎道偵測、詳細輸出控制
echo ✅  26個功能已升級到 Function 15 標準 (49.1% 完成)
echo 🚀  支援智能緩存管理和用戶體驗控制
echo.
echo 程式已安全退出！
echo.
pause
exit