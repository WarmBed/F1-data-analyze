"""
測試 Performance Monitor 監控注入邏輯
在 GUI 運行時執行此腳本來診斷問題
"""

def diagnose_live_timing_modules():
    """診斷 Live Timing 模組"""
    print("=" * 60)
    print("Performance Monitor 診斷工具")
    print("=" * 60)

    # 1. 檢查 QApplication
    print("\n[1] 檢查 QApplication...")
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            print(f"   ✅ QApplication 存在")
            all_widgets = app.allWidgets()
            print(f"   ✅ 總共 {len(all_widgets)} 個 widgets")
        else:
            print("   ❌ QApplication 不存在")
            return
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return

    # 2. 檢查 DataManager
    print("\n[2] 檢查 DataManager...")
    try:
        from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
        mgr = LiveTimingDataManager._instance
        if mgr:
            print(f"   ✅ DataManager 實例存在")
            print(f"   - 賽事資訊: {mgr._race_info}")
            print(f"   - 快照數量: {len(mgr._snapshots) if hasattr(mgr, '_snapshots') and mgr._snapshots else 0}")
            print(f"   - 播放狀態: {mgr._playback_state if hasattr(mgr, '_playback_state') else 'unknown'}")
        else:
            print("   ❌ DataManager 實例不存在")
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")

    # 3. 檢查 BaseLiveTimingMDI
    print("\n[3] 檢查 BaseLiveTimingMDI...")
    try:
        from modules.gui.live_timing.core.base_live_mdi import BaseLiveTimingMDI
        print(f"   ✅ BaseLiveTimingMDI 已導入")

        # 統計繼承自 BaseLiveTimingMDI 的 widgets
        live_timing_widgets = []
        for widget in all_widgets:
            if isinstance(widget, BaseLiveTimingMDI):
                live_timing_widgets.append(widget)

        print(f"   ✅ 找到 {len(live_timing_widgets)} 個 Live Timing 模組")

        for i, widget in enumerate(live_timing_widgets, 1):
            class_name = widget.__class__.__name__
            has_handle = hasattr(widget, '_handle_snapshot_updated')
            has_on = hasattr(widget, '_on_snapshot_updated')
            is_visible = widget.isVisible()
            print(f"   {i}. {class_name}")
            print(f"      - 可見: {is_visible}")
            print(f"      - _handle_snapshot_updated: {has_handle}")
            print(f"      - _on_snapshot_updated: {has_on}")

            if has_handle:
                method = getattr(widget, '_handle_snapshot_updated')
                is_monitored = hasattr(method, '_is_monitored')
                print(f"      - 已監控: {is_monitored}")

    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

    # 4. 檢查 MDI 區域
    print("\n[4] 檢查 MDI 區域...")
    try:
        mdi_count = 0
        sub_window_count = 0

        for widget in app.topLevelWidgets():
            class_name = widget.__class__.__name__

            # 找 CustomMdiArea
            children = widget.findChildren(object)
            for child in children:
                if hasattr(child, 'subWindowList'):
                    mdi_count += 1
                    sub_windows = child.subWindowList()
                    sub_window_count += len(sub_windows)
                    print(f"   MDI Area: {child.__class__.__name__} - {len(sub_windows)} 個子視窗")

                    for sub in sub_windows:
                        if sub and sub.widget():
                            sw_class = sub.widget().__class__.__name__
                            print(f"      - {sw_class}")

        print(f"   ✅ 找到 {mdi_count} 個 MDI 區域, {sub_window_count} 個子視窗")

    except Exception as e:
        print(f"   ❌ 錯誤: {e}")

    # 5. 檢查頂層視窗
    print("\n[5] 頂層視窗列表...")
    try:
        for widget in app.topLevelWidgets():
            class_name = widget.__class__.__name__
            is_visible = widget.isVisible()
            title = widget.windowTitle() if hasattr(widget, 'windowTitle') else 'N/A'
            print(f"   - {class_name}: '{title}' (可見: {is_visible})")
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")

    print("\n" + "=" * 60)
    print("診斷完成")
    print("=" * 60)


if __name__ == "__main__":
    print("請在 GUI 運行時執行此腳本")
    print("方法: 在 Python 控制台執行:")
    print(">>> exec(open('test_perf_monitor_injection.py').read())")
    print(">>> diagnose_live_timing_modules()")
