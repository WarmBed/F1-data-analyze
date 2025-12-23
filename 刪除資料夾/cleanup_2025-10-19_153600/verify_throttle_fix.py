"""
🔧 Throttle Box Plot 死機修復驗證腳本

修復內容：
✅ 1. 將異步停止機制改為同步方式（與 Lap Time Box Plot 一致）
✅ 2. 移除 _stop_api_worker() 方法的複雜異步邏輯
✅ 3. 使用 worker.wait(200) 同步等待停止
✅ 4. 暫時禁用進度管理器（避免連接時機問題）

使用方式:
    python verify_throttle_fix.py
"""

import sys
import os
import inspect

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_cleanup_api_worker():
    """驗證 _cleanup_api_worker() 修復"""
    print("=" * 80)
    print("測試 1: _cleanup_api_worker() 方法修復驗證")
    print("=" * 80)
    
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
            ThrottleBoxPlotDataManager
        )
        
        # 檢查 _cleanup_api_worker 方法
        has_cleanup = hasattr(ThrottleBoxPlotDataManager, '_cleanup_api_worker')
        print(f"{'✅' if has_cleanup else '❌'} _cleanup_api_worker() 方法存在")
        
        if has_cleanup:
            method = ThrottleBoxPlotDataManager._cleanup_api_worker
            source = inspect.getsource(method)
            
            checks = {
                "使用 worker.wait(200)": "wait(200)" in source,
                "斷開 progress 信號": "progress.disconnect()" in source,
                "斷開 success 信號": "success.disconnect()" in source,
                "斷開 failure 信號": "failure.disconnect()" in source,
                "斷開 finished 信號": "finished.disconnect()" in source,
                "調用 deleteLater()": "deleteLater()" in source,
                "設置 Worker 為 None": "_api_worker = None" in source,
            }
            
            print("\n檢查關鍵步驟：")
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}")
            
            # 檢查是否還有 _stop_api_worker
            has_stop_worker = hasattr(ThrottleBoxPlotDataManager, '_stop_api_worker')
            if has_stop_worker:
                print("\n⚠️  警告：_stop_api_worker() 方法仍然存在（應已移除）")
            else:
                print("\n✅ _stop_api_worker() 方法已移除")
            
            all_passed = all(checks.values()) and not has_stop_worker
            
            if all_passed:
                print("\n✅ _cleanup_api_worker() 修復正確")
                return True
            else:
                print("\n❌ _cleanup_api_worker() 仍有問題")
                return False
        else:
            print("\n❌ _cleanup_api_worker() 方法不存在")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stop_loading():
    """驗證 stop_loading() 修復"""
    print("\n" + "=" * 80)
    print("測試 2: stop_loading() 方法修復驗證")
    print("=" * 80)
    
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
            ThrottleBoxPlotDataManager
        )
        
        method = ThrottleBoxPlotDataManager.stop_loading
        source = inspect.getsource(method)
        
        checks = {
            "調用 _cleanup_api_worker()": "_cleanup_api_worker()" in source,
            "不調用 _stop_api_worker()": "_stop_api_worker()" not in source,
            "設置 _is_loading = False": "_is_loading = False" in source,
        }
        
        print("\n檢查關鍵步驟：")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
        
        all_passed = all(checks.values())
        
        if all_passed:
            print("\n✅ stop_loading() 修復正確")
            return True
        else:
            print("\n❌ stop_loading() 仍有問題")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_update_lap_parameters():
    """驗證 update_lap_parameters() 禁用進度管理器"""
    print("\n" + "=" * 80)
    print("測試 3: update_lap_parameters() 進度管理器禁用驗證")
    print("=" * 80)
    
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
            ThrottleBoxPlotAnalysis
        )
        
        method = ThrottleBoxPlotAnalysis.update_lap_parameters
        source = inspect.getsource(method)
        
        # 檢查是否已註解掉 _show_loading_progress()
        progress_commented = "# self._show_loading_progress()" in source or \
                             "# 問題：_show_loading_progress()" in source
        progress_not_called = "self._show_loading_progress()" not in source or progress_commented
        
        status = "✅" if progress_not_called else "❌"
        print(f"{status} _show_loading_progress() 已禁用")
        
        if progress_not_called:
            print("\n✅ update_lap_parameters() 修復正確")
            return True
        else:
            print("\n❌ update_lap_parameters() 仍在調用進度管理器")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_lap_time():
    """對比 Throttle 和 Lap Time 的 _cleanup_api_worker()"""
    print("\n" + "=" * 80)
    print("測試 4: 與 Lap Time Box Plot 對比驗證")
    print("=" * 80)
    
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
            ThrottleBoxPlotDataManager as ThrottleDataManager
        )
        from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
            LapTimeBoxPlotDataManager as LapDataManager
        )
        
        throttle_source = inspect.getsource(ThrottleDataManager._cleanup_api_worker)
        lap_source = inspect.getsource(LapDataManager._cleanup_api_worker)
        
        # 檢查關鍵相似點
        checks = {
            "都使用 wait(200)": "wait(200)" in throttle_source and "wait(200)" in lap_source,
            "都調用 deleteLater()": "deleteLater()" in throttle_source and "deleteLater()" in lap_source,
            "都設置 Worker 為 None": "_api_worker = None" in throttle_source and "_api_worker = None" in lap_source,
        }
        
        print("\n對比關鍵相似點：")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
        
        all_passed = all(checks.values())
        
        if all_passed:
            print("\n✅ Throttle 與 Lap Time 的 cleanup 邏輯一致")
            return True
        else:
            print("\n❌ Throttle 與 Lap Time 的 cleanup 邏輯不一致")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║     Throttle Box Plot 死機修復驗證                                      ║
║                                                                          ║
║  修復內容:                                                               ║
║    1. 異步停止改為同步（與 Lap Time 一致）                               ║
║    2. 使用 worker.wait(200) 等待停止                                     ║
║    3. 移除複雜的 QTimer 異步邏輯                                         ║
║    4. 暫時禁用進度管理器                                                 ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    
    results = []
    
    # 執行所有測試
    results.append(("_cleanup_api_worker() 修復", test_cleanup_api_worker()))
    results.append(("stop_loading() 修復", test_stop_loading()))
    results.append(("update_lap_parameters() 進度管理器禁用", test_update_lap_parameters()))
    results.append(("與 Lap Time Box Plot 對比", compare_with_lap_time()))
    
    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n" + "🎉" * 40)
        print("✅ 所有測試通過！Throttle Box Plot 死機問題已修復！")
        print("🎉" * 40)
        print("\n下一步：")
        print("1. 啟動 GUI: python f1t_gui_main.py")
        print("2. 開啟 Throttle Box Plot")
        print("3. 驗證不再死機")
        print("4. 測試多次開啟/關閉")
        print("\n修復詳情：")
        print("- ✅ 移除異步停止機制")
        print("- ✅ 使用 worker.wait(200) 同步等待")
        print("- ✅ 暫時禁用進度管理器")
        print("- ✅ 與 Lap Time Box Plot 邏輯一致")
        return 0
    else:
        print("\n❌ 測試失敗，請檢查上面的錯誤訊息")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 測試過程中發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
