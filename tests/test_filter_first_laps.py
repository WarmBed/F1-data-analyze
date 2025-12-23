"""測試 Filter First Laps 功能實作"""

import sys
from PyQt5.QtWidgets import QApplication
from core.gui_settings_manager import gui_settings_manager

def test_filter_first_laps_settings():
    """測試 Filter First Laps 設定功能"""
    
    print("=" * 80)
    print("🧪 測試 Filter First Laps 功能")
    print("=" * 80)
    
    # 1. 檢查初始設定
    print("\n[階段 1] 檢查初始設定")
    initial_settings = gui_settings_manager.get_boxplot_settings()
    print(f"初始設定: {initial_settings}")
    
    assert "filter_first_laps" in initial_settings, "❌ filter_first_laps 欄位不存在！"
    print(f"✅ filter_first_laps 欄位存在")
    print(f"   預設值: {initial_settings['filter_first_laps']}")
    
    # 2. 測試設定更新
    print("\n[階段 2] 測試設定更新功能")
    print("  → 設定 filter_first_laps=False")
    gui_settings_manager.update_boxplot_settings(
        filter_first_laps=False
    )
    
    updated_settings = gui_settings_manager.get_boxplot_settings()
    print(f"  → 更新後: filter_first_laps={updated_settings.get('filter_first_laps')}")
    assert updated_settings.get('filter_first_laps') == False, "❌ 設定更新失敗！"
    print(f"✅ 設定更新成功")
    
    # 3. 測試恢復預設值
    print("\n[階段 3] 測試恢復預設值")
    print("  → 設定 filter_first_laps=True")
    gui_settings_manager.update_boxplot_settings(
        filter_first_laps=True
    )
    
    restored_settings = gui_settings_manager.get_boxplot_settings()
    print(f"  → 恢復後: filter_first_laps={restored_settings.get('filter_first_laps')}")
    assert restored_settings.get('filter_first_laps') == True, "❌ 恢復預設值失敗！"
    print(f"✅ 恢復預設值成功")
    
    # 4. 測試完整設定結構
    print("\n[階段 4] 驗證完整設定結構")
    all_settings = gui_settings_manager.get_boxplot_settings()
    expected_keys = [
        "filter_pit_laps",
        "filter_outliers",
        "outlier_threshold",
        "filter_yellow_flags",
        "filter_red_flags",
        "filter_first_laps",  # 新增
    ]
    
    for key in expected_keys:
        if key in all_settings:
            print(f"  ✅ {key}: {all_settings[key]}")
        else:
            print(f"  ❌ {key}: 缺少！")
            assert False, f"設定結構缺少 {key}"
    
    print("\n" + "=" * 80)
    print("✅ 所有測試通過！")
    print("=" * 80)
    return True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        test_filter_first_laps_settings()
        print("\n✅ Filter First Laps 功能實作完成！")
        sys.exit(0)
    except Exception as exc:
        print(f"\n❌ 測試失敗: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
