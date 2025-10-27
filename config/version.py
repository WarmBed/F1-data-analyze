#!/usr/bin/env python3
"""
F1T 版本管理
Version Management for F1 TelemetryStation Pro

集中管理所有版本相關常數，確保整個應用程式版本一致性
"""

# 應用程式版本號
APP_VERSION = "V0.6.0"

# 完整版本資訊
APP_NAME = "F1 TelemetryStation Pro"
APP_FULL_TITLE = f"{APP_NAME} {APP_VERSION}"

# 版本歷史
VERSION_HISTORY = {
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
