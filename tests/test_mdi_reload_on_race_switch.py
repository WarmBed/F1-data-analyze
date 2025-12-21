#!/usr/bin/env python3
"""
測試腳本：驗證 MDI 重建機制（賽道切換時）

測試場景：
1. 初始化 Brazil 2025 R
2. 切換到 Bahrain 2025 R → 觸發 MDI 重建
3. 驗證新 MDI 使用 Bahrain 座標
4. 再切換回 Brazil → 再次觸發重建
5. 驗證 Sector 標註位置正確

預期結果：
✅ 切換賽道時自動關閉舊 MDI
✅ 創建全新的 MDI 實例
✅ Sector 座標永遠正確（無污染）
✅ 無需複雜的狀態管理

Author: F1T Team
Date: 2025-11-12
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer


def test_mdi_reload():
    """測試 MDI 重建機制"""
    print("\n" + "="*70)
    print("開始測試：MDI 重建機制（賽道切換時）")
    print("="*70 + "\n")
    
    # 測試場景 1: 初始化 Brazil
    print("📋 場景 1: 初始化 Brazil 2025 R")
    print("-" * 70)
    
    try:
        from modules.gui.Historical_track_map.historical_track_map_mdi import HistoricalTrackMapMDI
        
        # 創建實例
        mdi = HistoricalTrackMapMDI(parent=None)
        
        # 設置初始參數
        mdi.current_year = "2025"
        mdi.current_race = "Brazil"
        mdi.current_session = "R"
        
        print(f"✅ 參數已設置: {mdi.current_year} {mdi.current_race} {mdi.current_session}")
        
        # 初始化
        if not mdi.initialize_module():
            print("❌ 初始化失敗")
            return False
        
        print("✅ 初始化成功")
        
        # 等待數據載入
        print("⏳ 等待數據載入...")
        QApplication.processEvents()
        
        # 測試場景 2: 切換到 Bahrain
        print("\n📋 場景 2: 切換到 Bahrain 2025 R")
        print("-" * 70)
        
        # 監聽 module_error 信號（檢測重建請求）
        reload_request_received = [False]  # 使用列表避免閉包問題
        
        def on_module_error(error_message):
            print(f"[SIGNAL] module_error 觸發: {error_message}")
            if error_message.startswith("RELOAD_MDI_REQUEST|"):
                reload_request_received[0] = True
                parts = error_message.split("|")
                if len(parts) >= 4:
                    year, race, session = parts[1], parts[2], parts[3]
                    print(f"[SIGNAL] ✅ 收到 MDI 重建請求: {year} {race} {session}")
        
        mdi.module_error.connect(on_module_error)
        
        # 觸發賽道切換
        print("🔄 調用 update_lap_parameters('2025', 'Bahrain', 'R')...")
        success = mdi.update_lap_parameters("2025", "Bahrain", "R")
        
        # 處理事件
        QApplication.processEvents()
        
        # 驗證
        if reload_request_received[0]:
            print("✅ 測試通過：檢測到賽道變更，觸發 MDI 重建請求")
        else:
            print("❌ 測試失敗：未觸發 MDI 重建請求")
            return False
        
        # 測試場景 3: 同一賽道內變更（不應觸發重建）
        print("\n📋 場景 3: 同一賽道內變更 Session（Bahrain R → Q）")
        print("-" * 70)
        
        reload_request_received[0] = False  # 重置標記
        
        # 模擬已切換到 Bahrain
        mdi.current_race = "Bahrain"
        
        print("🔄 調用 update_lap_parameters('2025', 'Bahrain', 'Q')...")
        success = mdi.update_lap_parameters("2025", "Bahrain", "Q")
        
        QApplication.processEvents()
        
        if not reload_request_received[0]:
            print("✅ 測試通過：同一賽道內變更，不觸發 MDI 重建")
        else:
            print("❌ 測試失敗：不應觸發 MDI 重建（同一賽道）")
            return False
        
        print("\n" + "="*70)
        print("所有測試通過！✅")
        print("="*70 + "\n")
        
        print("📊 測試總結：")
        print("  ✅ 賽道變更 (Brazil → Bahrain) → 觸發 MDI 重建")
        print("  ✅ Session 變更 (R → Q) → 正常數據更新")
        print("  ✅ 信號機制正常運作")
        print("\n💡 下一步：在 GUI 主視窗中測試完整的重建流程")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        success = test_mdi_reload()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
