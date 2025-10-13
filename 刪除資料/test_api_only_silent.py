#!/usr/bin/env python3
"""
測試 API-ONLY 模式下的靜默錯誤處理
Test Silent Error Handling in API-ONLY Mode

驗證當找不到本地 JSON 時，系統不會彈出錯誤視窗

Author: F1T Team
Date: 2025-10-10
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_data_loader import IdealLapRankingTableDataLoader


def test_no_json_no_error_popup():
    """測試：找不到 JSON 時不彈出錯誤視窗"""
    
    print("="*60)
    print("🧪 測試 API-ONLY 模式靜默錯誤處理")
    print("="*60)
    
    # 創建載入器（使用不存在的賽事數據）
    loader = IdealLapRankingTableDataLoader(
        year="2099",  # 未來年份，確保找不到 JSON
        race="Mars",   # 不存在的賽事
        session="R"
    )
    
    # 連接錯誤信號
    error_received = []
    def on_error(msg):
        error_received.append(msg)
        print(f"❌ 接收到錯誤信號: {msg}")
    
    loader.load_error.connect(on_error)
    
    # 嘗試載入數據
    print("\n📂 嘗試載入不存在的數據...")
    result = loader.load_data(
        year="2099",
        race="Mars",
        session="R"
    )
    
    print(f"\n結果: load_data() 返回 {result}")
    print(f"錯誤信號數量: {len(error_received)}")
    
    # 驗證結果
    print("\n" + "="*60)
    if len(error_received) == 0:
        print("✅ 測試通過: 找不到 JSON 時沒有發送錯誤信號")
        print("✅ 用戶不會看到錯誤彈窗")
        print("💡 系統會靜默處理，等待用戶使用 API 獲取數據")
    else:
        print("❌ 測試失敗: 仍然發送了錯誤信號")
        print(f"   錯誤訊息: {error_received}")
    print("="*60)


def main():
    app = QApplication(sys.argv)
    
    # 執行測試
    test_no_json_no_error_popup()
    
    # 立即退出（不需要啟動事件循環）
    QTimer.singleShot(100, app.quit)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
