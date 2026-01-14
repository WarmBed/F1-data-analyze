#!/usr/bin/env python3
"""
F1T 版本管理
Version Management for F1 TelemetryStation Pro

集中管理所有版本相關常數，確保整個應用程式版本一致性
"""

# 應用程式版本號
APP_VERSION = "V0.15.0"

# 完整版本資訊
APP_NAME = "PIT WALL"
APP_FULL_TITLE = f"{APP_NAME} {APP_VERSION}"

# 版本歷史
VERSION_HISTORY = {
    "V0.15.0": {
        "date": "2026-01-12",
        "features": [
            "新增 Pit Loss Table 模組：24 賽道進站時間損失總覽",
            "進站時間訓練數據修正：Hungaroring/Las Vegas/Yas Marina 映射問題修復",
            "全部 24 賽道皆有真實訓練數據（無估算值）",
            "新增進站時間色彩編碼：綠色（快）/黃色（中）/紅色（慢）",
            "支援 3 種語言（中/英/日）幫助文檔",
        ],
    },
    "V0.14.1": {
        "date": "2026-01-11",
        "features": [
            "Driver Strategy 模組鋸齒狀預測修復：base_lap_time 鎖定機制重構",
            "新增 Stint 偵測邏輯：進站後前 2 圈浮動，第 3 圈鎖定 base_lap_time",
            "增量模擬模式：保持已鎖定的 base_lap_time，防止每圈重新計算",
            "禁用賽道進化（Track Evolution）演算法：簡化預測模型",
            "修復增量模式 base_lap_time 狀態保存問題",
            "預測曲線平滑度改善：消除逐圈播放時的鋸齒狀波動",
        ],
    },
    "V0.13.1": {
        "date": "2025-12-23",
        "features": [
            "新增 Season Start Reaction 模組：年度起跑反應 0-50km/h 箱型圖分析",
            "改進箱型圖車手標籤樣式：圓角背景 + 亮度計算文字顏色",
            "新增右鍵隱藏車手和調整 Y 軸範圍功能",
            "修復 Y 軸裁剪問題：異常值超出範圍時不再顯示",
        ],
    },
    "V0.13.0": {
        "date": "2025-12-21",
        "features": [
            "更新 F1TV 登入機制：改用瀏覽器 Cookie 擷取方式",
            "新增 SF% History 模組：節油百分比歷史追蹤",
            "新增 Throttle 95% History 模組：油門高開度歷史分析",
            "Driver Strategy 與 Chase Strategy 模組效能優化：停用圓點繪製",
            "Live Timing Trace 模組同步 hover 功能：滑鼠懸停時同步顯示數據標籤",
            "Linkage (L) 按鈕控制 hover 同步：可透過標題列按鈕啟用或停用",
        ]
    },
    "V0.12.1": {
        "date": "2025-12-20",
        "features": [
            "修復 Lap Linkage 工具列核取方塊：取消勾選現可正確停止連動",
            "修復 L 按鈕（個別連動控制）：支援所有圖表類型（Speed、Brake、Throttle、RPM、Gear）",
            "修復 Fastest Lap 功能：勾選時自動設定圈數為 99，取消勾選時恢復為 1",
            "改進 PopoutSubWindow 連動控制：統一處理多種圖表 widget 屬性名稱",
            "修正 lap_linkage_toggler.py 缺少的導入：linkage_manager 與 global_signals",
        ]
    },
    "V0.12.0": {
        "date": "2025-12-19",
        "features": [
            "EXE 建構工具更新：輸出檔名改為 PITWALL - {版本}",
            "F1T_GUI_clean.spec 完整更新：280+ 個隱藏導入模組",
            "新增 2026 賽季日曆支援（Function 99）",
            "年份選擇範圍擴展至 2020-2027",
        ]
    },
    "V0.11.1": {
        "date": "2025-12-12",
        "features": [
            "Live Timing 性能優化：分層更新策略",
            "Ranking Tower 分層更新（Gap/DRS 30FPS，其他 10FPS）",
            "Tyre Strategy 改為圈數變化觸發更新",
            "Lap Time Distribution 改為 best_lap_time 變化觸發更新",
            "Race Control Messages 視窗尺寸優化（最小 4 行）",
            "Track Weather 降雨狀態顯示（Dry/Wet）",
            "安全車過濾（241/242/243 不顯示於排名）",
            "修復 P1 gap_leader 顯示問題",
        ]
    },
    "V0.11.0": {
        "date": "2025-12-11",
        "features": [
            "修復 Live Timing DRS 顯示 Bug（DRS=0 被 falsy 判斷過濾）",
            "修復 PKL 檔案命名加入年份（格式：{year}_{race}_{session}.pkl）",
            "修復多個 GUI 模組語法錯誤（import 語句、縮排、缺少引用）",
            "修復 OpenF1 Abu Dhabi 映射錯誤（Yas Island 匹配失敗）",
            "移除 Performance Monitor 模組",
            "EXE 建置優化：禁用 console、log 和 print 輸出",
            "PyInstaller 翻譯檔案過濾（僅保留英文和中文）",
            "Abu Dhabi 2025 進站數據完整支援（Function 3/4 生成成功）",
        ]
    },
    "V0.10.0": {
        "date": "2025-12-09",
        "features": [
            "Chase Strategy 自動追蹤 P1/P2 功能（基於賽事排名）",
            "Gap Evolution 手動切換車手時自動更新顯示",
            "Logger 性能管理系統（GUI System Settings 整合）",
            "Logger 開關工具（tools/toggle_logger.py）",
            "提升系統性能與穩定性",
        ]
    },
    "V0.9.0": {
        "date": "2025-12-05",
        "features": [
            "Live Timing 排名塔 PIT 狀態顯示優化（儲存格合併）",
            "Live Timing 排名高亮功能實作",
            "MDI 視窗 Snap/Dock 功能增強",
            "勝率預測模型診斷工具",
            "AI 輔助分析工具整合（Ollama 本地模型支援）",
        ]
    },
    "V0.8.0": {
        "date": "2025-11-14",
        "features": [
            "修復 Python 3.13 執行緒清理警告（_DeleteDummyThreadOnDel TypeError）",
            "改善主視窗 closeEvent 執行緒清理流程（收集所有活動 QThread）",
            "延長執行緒等待時間（2秒→3秒）並強制終止未退出執行緒",
            "增強 Python 3.13 警告抑制器（sys.excepthook + threading.excepthook）",
            "實作雙層防護：主動清理 + 警告抑制，確保優雅關閉",
            "新增執行緒清理日誌，清楚顯示每個執行緒的清理狀態",
            "修復 QThread 與 Python threading 混用導致的資源洩漏問題",
            "提供完整的執行緒清理測試指南和修復報告文檔",
        ]
    },
    "V0.7.0": {
        "date": "2025-11-08",
        "features": [
            "實作 FIA Parts Analysis 模組完整多國語言化",
            "整合 color_palette_provider 車手與車隊顏色系統",
            "實作內容翻譯映射系統（變更類型、分類、描述）",
            "支援 Type 欄位英文提取（從 '維修 (Repair)' 提取 'Repair'）",
            "支援 Description 欄位完整翻譯（6 種類型說明）",
            "顯示格式完全對齊 Ideal Ranking Table 標準",
            "新增 35 位車手名稱到代碼映射系統",
            "實作 Tooltip 顯示原始中英文內容",
        ]
    },
    "V0.6.0": {
        "date": "2025-10-27",
        "features": [
            "版本號更新至 V0.6.0",
            "持續優化系統穩定性",
            "改進用戶介面體驗",
        ]
    },
    "V0.5.0": {
        "date": "2025-10-20",
        "features": [
            "實作 Constructor/Driver Standings 智能刷新機制（賽前 2 天加速至 12 小時）",
            "實作集中版本管理系統（config/version.py）",
            "統一 Splash Screen 和 GUI 主視窗版本號",
            "強化 Weather Timeline API-ONLY 模式",
            "優化 Season Calendar 智能刷新邏輯",
            "修復多個 Worker 生命週期問題",
        ]
    },
    "V0.4.0": {
        "date": "2025-10-20",
        "features": [
            "Weather Timeline 模組完整實作",
            "API-ONLY 政策執行",
            "Worker 生命週期修復",
        ]
    },
    "V0.3.0": {
        "date": "2025-10-15",
        "features": [
            "整合 Season Calendar 智能刷新",
            "新增 Weather Timeline 模組",
            "實作 API-ONLY 政策",
        ]
    },
    "V0.2.0": {
        "date": "2025-10-10",
        "features": [
            "基礎 GUI 架構完成",
            "多種分析模組整合",
            "MDI 視窗管理系統",
        ]
    },
}

# 版權資訊
COPYRIGHT_YEAR = "2025"
COPYRIGHT_HOLDER = "F1T Development Team"
COPYRIGHT_TEXT = f"© {COPYRIGHT_YEAR} {COPYRIGHT_HOLDER}"

# 完整版本字串（用於關於對話框）
FULL_VERSION_INFO = f"""
{APP_FULL_TITLE}

{COPYRIGHT_TEXT}

Current Version: {APP_VERSION}
Release Date: {VERSION_HISTORY.get(APP_VERSION, {}).get('date', 'Unknown')}
"""


def get_version() -> str:
    """獲取當前版本號"""
    return APP_VERSION


def get_full_title() -> str:
    """獲取完整標題"""
    return APP_FULL_TITLE


def get_version_info() -> str:
    """獲取完整版本資訊"""
    return FULL_VERSION_INFO


if __name__ == "__main__":
    # 測試輸出
    print("=" * 60)
    print("F1T 版本資訊")
    print("=" * 60)
    print(f"應用程式: {APP_NAME}")
    print(f"版本號: {APP_VERSION}")
    print(f"完整標題: {APP_FULL_TITLE}")
    print(f"版權: {COPYRIGHT_TEXT}")
    print("\n當前版本功能:")
    for feature in VERSION_HISTORY[APP_VERSION]["features"]:
        print(f"  • {feature}")
    print("=" * 60)
