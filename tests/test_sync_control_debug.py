"""
測試 MDI 視窗同步控制的調試腳本

這個腳本會模擬視窗設定對話框的行為，並添加大量調試輸出
來確認 sync_enabled 的值是否正確更新。

使用方法:
1. 打開 F1T GUI
2. 打開 Ideal Lap Ranking Table 視窗
3. 在 Python Debug Console 中執行這個腳本
4. 觀察輸出，確認 sync_enabled 的值

@date: 2025-10-20
@author: GitHub Copilot
"""

def test_sync_control():
    """測試同步控制"""
    print("=" * 80)
    print("🔍 MDI 視窗同步控制調試")
    print("=" * 80)
    
    # 導入必要的模組
    try:
        from PyQt5.QtWidgets import QApplication, QMdiArea
        import sys
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        return
    
    # 獲取 QApplication 實例
    app = QApplication.instance()
    if not app:
        print("❌ 找不到 QApplication 實例，請確保 GUI 已啟動")
        return
    
    print("✅ QApplication 實例已找到")
    
    # 查找主視窗
    for widget in app.topLevelWidgets():
        if widget.objectName() == "MainWindow":
            main_window = widget
            print(f"✅ 找到主視窗: {widget.windowTitle()}")
            break
    else:
        print("❌ 找不到主視窗")
        return
    
    # 查找所有 MDI 區域
    mdi_areas = []
    for obj in main_window.findChildren(QMdiArea):
        mdi_areas.append(obj)
        print(f"✅ 找到 MDI 區域: {obj.objectName()}")
    
    if not mdi_areas:
        print("❌ 找不到 MDI 區域")
        return
    
    print(f"\n📊 共找到 {len(mdi_areas)} 個 MDI 區域")
    
    # 查找所有子視窗
    all_subwindows = []
    for mdi_area in mdi_areas:
        subwindows = mdi_area.subWindowList()
        all_subwindows.extend(subwindows)
        print(f"\n📌 MDI 區域 {mdi_area.objectName()} 的子視窗:")
        for i, sw in enumerate(subwindows, 1):
            title = sw.windowTitle()
            has_sync = hasattr(sw, 'sync_enabled')
            sync_val = getattr(sw, 'sync_enabled', None) if has_sync else "N/A"
            print(f"   {i}. {title}")
            print(f"      - 有 sync_enabled 屬性: {has_sync}")
            print(f"      - sync_enabled 值: {sync_val}")
            
            # 檢查是否有 analysis_module
            has_module = hasattr(sw, 'analysis_module')
            print(f"      - 有 analysis_module: {has_module}")
            
            # 檢查 local 參數
            if hasattr(sw, 'local_year'):
                print(f"      - local_year: {sw.local_year}")
            if hasattr(sw, 'local_race'):
                print(f"      - local_race: {sw.local_race}")
            if hasattr(sw, 'local_session'):
                print(f"      - local_session: {sw.local_session}")
    
    print("\n" + "=" * 80)
    print("🎯 查找 Ideal Lap Ranking Table 視窗")
    print("=" * 80)
    
    # 查找 Ideal Lap Ranking Table
    ideal_lap_windows = []
    for sw in all_subwindows:
        if "Ideal Lap Ranking" in sw.windowTitle() or "理想圈速排名" in sw.windowTitle():
            ideal_lap_windows.append(sw)
            print(f"✅ 找到: {sw.windowTitle()}")
    
    if not ideal_lap_windows:
        print("❌ 找不到 Ideal Lap Ranking Table 視窗")
        print("💡 請先打開 Ideal Lap Ranking Table 視窗再執行此腳本")
        return
    
    print(f"\n📊 共找到 {len(ideal_lap_windows)} 個 Ideal Lap Ranking Table 視窗")
    
    # 詳細檢查第一個視窗
    target_window = ideal_lap_windows[0]
    print("\n" + "=" * 80)
    print(f"🔬 詳細檢查: {target_window.windowTitle()}")
    print("=" * 80)
    
    # 檢查所有相關屬性
    attrs_to_check = [
        'sync_enabled',
        'analysis_module',
        'local_year',
        'local_race',
        'local_session',
        '_parameter_provider',
        'sync_windows_checkbox'
    ]
    
    for attr in attrs_to_check:
        has_attr = hasattr(target_window, attr)
        value = getattr(target_window, attr, None) if has_attr else "N/A"
        print(f"   {attr:30s}: {has_attr:5s} | 值: {value}")
    
    # 測試修改 sync_enabled
    print("\n" + "=" * 80)
    print("🧪 測試修改 sync_enabled")
    print("=" * 80)
    
    if hasattr(target_window, 'sync_enabled'):
        original_value = target_window.sync_enabled
        print(f"   原始值: {original_value}")
        
        # 修改為 False
        target_window.sync_enabled = False
        new_value = target_window.sync_enabled
        print(f"   修改後: {new_value}")
        
        # 確認修改成功
        if new_value == False:
            print("   ✅ sync_enabled 修改成功")
        else:
            print("   ❌ sync_enabled 修改失敗")
        
        # 還原
        target_window.sync_enabled = original_value
        print(f"   已還原: {target_window.sync_enabled}")
    else:
        print("   ❌ 視窗沒有 sync_enabled 屬性")
    
    print("\n" + "=" * 80)
    print("✅ 調試完成")
    print("=" * 80)

if __name__ == "__main__":
    test_sync_control()
