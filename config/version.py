#!/usr/bin/env python3
"""
F1T 版本管理
Version Management for F1 TelemetryStation Pro

集中管理所有版本相關常數，確保整個應用程式版本一致性
"""

# 應用程式版本號
APP_VERSION = "V0.9.0"

# 完整版本資訊
APP_NAME = "F1 TelemetryStation Pro"
APP_FULL_TITLE = f"{APP_NAME} {APP_VERSION}"

# 版本歷史
VERSION_HISTORY = {
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
