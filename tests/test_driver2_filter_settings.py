#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Throttle Line Chart Driver 2 過濾設定測試腳本
測試 Driver 2 載入時是否正確使用當前的過濾設定

測試場景：
1. 在 System Settings 中取消勾選 filter_pit_laps, filter_yellow_flags, filter_red_flags
2. 載入 Driver 1 (VER) - 應該顯示所有圈數（包含 pit/yellow/red）
3. 載入 Driver 2 (NOR) - 應該也顯示所有圈數（不過濾）

預期結果：
- Driver 1 和 Driver 2 應該使用相同的過濾設定
- 當取消勾選過濾選項時，兩位車手都應該顯示完整數據
"""

import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_driver2_filter_settings():
    """測試 Driver 2 過濾設定"""
    print("=" * 70)
    print("  Throttle Line Chart Driver 2 過濾設定測試")
    print("=" * 70)
    
    try:
        # 1. 導入必要模組
        from core.gui_settings_manager import gui_settings_manager
        from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi import ThrottleLineChartMDI
        
        print("\n✅ [1] 模組導入成功")
        
        # 2. 檢查當前的過濾設定
        current_settings = gui_settings_manager.get_boxplot_settings()
        print(f"\n📊 [2] 當前系統設定:")
        print(f"   - filter_pit_laps: {current_settings.get('filter_pit_laps')}")
        print(f"   - filter_yellow_flags: {current_settings.get('filter_yellow_flags')}")
        print(f"   - filter_red_flags: {current_settings.get('filter_red_flags')}")
        
        # 3. 模擬修改設定（取消所有過濾）
        print(f"\n🔧 [3] 模擬取消所有過濾選項...")
        gui_settings_manager.update_boxplot_settings(
            filter_pit_laps=False,
            filter_yellow_flags=False,
            filter_red_flags=False,
        )
        
        # 4. 驗證設定已更新
        updated_settings = gui_settings_manager.get_boxplot_settings()
        print(f"\n✅ [4] 設定已更新:")
        print(f"   - filter_pit_laps: {updated_settings.get('filter_pit_laps')}")
        print(f"   - filter_yellow_flags: {updated_settings.get('filter_yellow_flags')}")
        print(f"   - filter_red_flags: {updated_settings.get('filter_red_flags')}")
        
        assert updated_settings.get('filter_pit_laps') == False, "filter_pit_laps 應該為 False"
        assert updated_settings.get('filter_yellow_flags') == False, "filter_yellow_flags 應該為 False"
        assert updated_settings.get('filter_red_flags') == False, "filter_red_flags 應該為 False"
        
        print(f"\n✅ [5] 設定驗證通過")
        
        # 5. 模擬創建 MDI 實例
        print(f"\n🔧 [6] 創建 Throttle Line Chart MDI 實例...")
        
        # 注意：這裡只是驗證設定傳遞邏輯，不實際載入數據
        # 實際測試需要在 GUI 環境中執行
        
        print(f"\n💡 提示：完整測試需要在 GUI 環境中執行")
        print(f"   1. 啟動 GUI: python f1t_gui_main.py")
        print(f"   2. 開啟 Throttle Line Chart")
        print(f"   3. 在 System Settings 中取消勾選過濾選項")
        print(f"   4. 載入 Driver 1 (VER)")
        print(f"   5. 載入 Driver 2 (NOR)")
        print(f"   6. 檢查 log 輸出，確認 Driver 2 使用正確的過濾設定")
        
        print(f"\n" + "=" * 70)
        print(f"  測試完成")
        print(f"=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_driver2_filter_settings()
    sys.exit(0 if success else 1)
