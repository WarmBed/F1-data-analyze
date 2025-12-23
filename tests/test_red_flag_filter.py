"""
測試腳本：驗證 Filter Red Flag Laps 功能
遵循反幻覺編碼五原則
"""

import sys
from PyQt5.QtWidgets import QApplication
from core.gui_settings_manager import gui_settings_manager

def test_red_flag_filter():
    """測試紅旗過濾功能"""
    print("=" * 60)
    print("開始測試 Filter Red Flag Laps 功能")
    print("=" * 60)
    
    # 階段 1: 測試預設值
    print("\n[階段 1] 測試預設值")
    settings = gui_settings_manager.get_boxplot_settings()
    print(f"✅ 預設設定: {settings}")
    
    assert "filter_red_flags" in settings, "❌ 錯誤: filter_red_flags 不存在於設定中"
    assert settings["filter_red_flags"] == True, "❌ 錯誤: 預設值應為 True"
    print("✅ 預設值測試通過: filter_red_flags = True")
    
    # 階段 2: 測試更新功能
    print("\n[階段 2] 測試更新功能")
    gui_settings_manager.update_boxplot_settings(filter_red_flags=False)
    updated_settings = gui_settings_manager.get_boxplot_settings()
    print(f"✅ 更新後設定: {updated_settings}")
    
    assert updated_settings["filter_red_flags"] == False, "❌ 錯誤: 更新失敗"
    print("✅ 更新功能測試通過: filter_red_flags = False")
    
    # 階段 3: 測試信號發射
    print("\n[階段 3] 測試信號發射")
    signal_received = {"count": 0, "data": None}
    
    def on_settings_changed(new_settings):
        signal_received["count"] += 1
        signal_received["data"] = new_settings
        print(f"📡 接收到信號: {new_settings}")
    
    gui_settings_manager.boxplot_settings_changed.connect(on_settings_changed)
    gui_settings_manager.update_boxplot_settings(filter_red_flags=True)
    
    assert signal_received["count"] == 1, "❌ 錯誤: 信號未發射"
    assert signal_received["data"]["filter_red_flags"] == True, "❌ 錯誤: 信號數據不正確"
    print("✅ 信號發射測試通過")
    
    # 階段 4: 驗證所有欄位
    print("\n[階段 4] 驗證完整設定結構")
    final_settings = gui_settings_manager.get_boxplot_settings()
    expected_keys = [
        "filter_pit_laps",
        "filter_outliers",
        "outlier_threshold",
        "filter_yellow_flags",
        "filter_red_flags"  # 新增的欄位
    ]
    
    for key in expected_keys:
        assert key in final_settings, f"❌ 錯誤: {key} 不存在"
        print(f"  ✅ {key}: {final_settings[key]}")
    
    print("\n" + "=" * 60)
    print("所有測試通過！Filter Red Flag Laps 功能正常運作")
    print("=" * 60)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        test_red_flag_filter()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
