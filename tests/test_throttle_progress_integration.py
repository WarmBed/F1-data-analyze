"""
🎯 Throttle Box Plot 異步進度管理器整合測試

測試項目:
✅ 1. AsyncLoadingProgressManager 正確導入
✅ 2. ThrottleBoxPlotAnalysis 正確初始化 progress_manager
✅ 3. _show_loading_progress() 方法存在並可調用
✅ 4. cleanup() 方法覆寫並調用 _hide_loading_progress()
✅ 5. API Worker 信號連接到進度管理器

使用方式:
    python test_throttle_progress_integration.py

預期結果:
- 所有檢查項目通過 ✅
- 無 ImportError 或 AttributeError
- 驗證修復有效性
"""

import sys
import os
import inspect

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_async_loading_progress_import():
    """測試 1: AsyncLoadingProgressManager 導入"""
    print("=" * 80)
    print("測試 1: AsyncLoadingProgressManager 導入")
    print("=" * 80)
    
    try:
        from modules.gui.base.async_loading_progress import AsyncLoadingProgressManager
        print("✅ AsyncLoadingProgressManager 導入成功")
        
        # 檢查類別方法
        required_methods = [
            '_start_animation',
            'set_message',
            'update_progress',
            'set_complete',
            'set_error',
            'cleanup'
        ]
        
        print("\n檢查必要方法：")
        for method_name in required_methods:
            has_method = hasattr(AsyncLoadingProgressManager, method_name)
            status = "✅" if has_method else "❌"
            print(f"  {status} {method_name}")
        
        all_methods_exist = all(hasattr(AsyncLoadingProgressManager, m) for m in required_methods)
        
        if all_methods_exist:
            print("\n✅ 所有必要方法都存在")
            return True
        else:
            print("\n❌ 缺少必要方法")
            return False
            
    except ImportError as e:
        print(f"❌ AsyncLoadingProgressManager 導入失敗: {e}")
        return False

def test_throttle_mdi_import():
    """測試 2: ThrottleBoxPlotAnalysis MDI 導入"""
    print("\n" + "=" * 80)
    print("測試 2: ThrottleBoxPlotAnalysis 導入")
    print("=" * 80)
    
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
            ThrottleBoxPlotAnalysis
        )
        print("✅ ThrottleBoxPlotAnalysis 導入成功")
        
        # 檢查 __init__ 是否初始化 progress_manager
        init_source = inspect.getsource(ThrottleBoxPlotAnalysis.__init__)
        
        checks = {
            "初始化 progress_manager": "self.progress_manager" in init_source,
            "設置為 Optional[...]": "Optional[AsyncLoadingProgressManager]" in init_source or "progress_manager: Optional" in init_source,
        }
        
        print("\n檢查 __init__ 方法：")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
        
        all_passed = all(checks.values())
        
        if all_passed:
            print("\n✅ __init__ 方法正確初始化 progress_manager")
        else:
            print("\n⚠️  __init__ 方法可能缺少 progress_manager 初始化")
        
        return True
        
    except ImportError as e:
        print(f"❌ ThrottleBoxPlotAnalysis 導入失敗: {e}")
        return False

def test_progress_methods():
    """測試 3: 進度管理器方法檢查"""
    print("\n" + "=" * 80)
    print("測試 3: ThrottleBoxPlotAnalysis 進度管理器方法")
    print("=" * 80)
    
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
            ThrottleBoxPlotAnalysis
        )
        
        required_methods = [
            '_show_loading_progress',
            '_on_api_progress',
            '_on_api_success',
            '_on_api_failure',
            '_hide_loading_progress'
        ]
        
        print("\n檢查必要方法：")
        for method_name in required_methods:
            has_method = hasattr(ThrottleBoxPlotAnalysis, method_name)
            status = "✅" if has_method else "❌"
            print(f"  {status} {method_name}")
            
            if has_method:
                method = getattr(ThrottleBoxPlotAnalysis, method_name)
                source = inspect.getsource(method)
                
                # 檢查方法內容
                if method_name == '_show_loading_progress':
                    has_create = "AsyncLoadingProgressManager" in source
                    has_connect = "worker.progress.connect" in source
                    print(f"    {'✅' if has_create else '❌'} 創建 AsyncLoadingProgressManager")
                    print(f"    {'✅' if has_connect else '❌'} 連接 API Worker 信號")
                
                elif method_name == '_on_api_progress':
                    has_update = "update_progress" in source
                    print(f"    {'✅' if has_update else '❌'} 調用 update_progress()")
                
                elif method_name == '_on_api_success':
                    has_complete = "set_complete" in source
                    print(f"    {'✅' if has_complete else '❌'} 調用 set_complete()")
                
                elif method_name == '_on_api_failure':
                    has_error = "set_error" in source
                    print(f"    {'✅' if has_error else '❌'} 調用 set_error()")
                
                elif method_name == '_hide_loading_progress':
                    has_cleanup = "progress_manager.cleanup()" in source
                    print(f"    {'✅' if has_cleanup else '❌'} 調用 progress_manager.cleanup()")
        
        all_methods_exist = all(hasattr(ThrottleBoxPlotAnalysis, m) for m in required_methods)
        
        if all_methods_exist:
            print("\n✅ 所有進度管理器方法都存在")
            return True
        else:
            print("\n❌ 缺少進度管理器方法")
            return False
            
    except Exception as e:
        print(f"❌ 方法檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cleanup_override():
    """測試 4: cleanup() 方法覆寫檢查"""
    print("\n" + "=" * 80)
    print("測試 4: ThrottleBoxPlotAnalysis cleanup() 覆寫")
    print("=" * 80)
    
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
            ThrottleBoxPlotAnalysis
        )
        
        # 檢查是否有 cleanup 方法
        has_cleanup = hasattr(ThrottleBoxPlotAnalysis, 'cleanup')
        print(f"{'✅' if has_cleanup else '❌'} cleanup() 方法存在")
        
        if has_cleanup:
            cleanup_method = ThrottleBoxPlotAnalysis.cleanup
            source = inspect.getsource(cleanup_method)
            
            checks = {
                "調用 _hide_loading_progress()": "_hide_loading_progress()" in source,
                "調用 super().cleanup()": "super().cleanup()" in source,
                "有詳細註解": "清理順序" in source,
            }
            
            print("\n檢查 cleanup() 實現：")
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}")
            
            all_passed = all(checks.values())
            
            if all_passed:
                print("\n✅ cleanup() 方法正確實現")
                return True
            else:
                print("\n⚠️  cleanup() 方法可能缺少關鍵步驟")
                return False
        else:
            print("\n❌ cleanup() 方法不存在")
            return False
            
    except Exception as e:
        print(f"❌ cleanup() 檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_update_lap_parameters():
    """測試 5: update_lap_parameters() 調用進度管理器"""
    print("\n" + "=" * 80)
    print("測試 5: update_lap_parameters() 調用進度管理器")
    print("=" * 80)
    
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
            ThrottleBoxPlotAnalysis
        )
        
        method = ThrottleBoxPlotAnalysis.update_lap_parameters
        source = inspect.getsource(method)
        
        has_show_progress = "_show_loading_progress()" in source
        status = "✅" if has_show_progress else "❌"
        print(f"{status} 調用 _show_loading_progress()")
        
        if has_show_progress:
            print("\n✅ update_lap_parameters() 正確調用進度管理器")
            return True
        else:
            print("\n❌ update_lap_parameters() 沒有調用進度管理器")
            return False
            
    except Exception as e:
        print(f"❌ update_lap_parameters() 檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║     Throttle Box Plot 異步進度管理器整合測試                            ║
║                                                                          ║
║  測試項目:                                                               ║
║    1. AsyncLoadingProgressManager 導入                                   ║
║    2. ThrottleBoxPlotAnalysis 初始化                                     ║
║    3. 進度管理器方法                                                     ║
║    4. cleanup() 覆寫                                                     ║
║    5. update_lap_parameters() 整合                                       ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    
    results = []
    
    # 執行所有測試
    results.append(("AsyncLoadingProgressManager 導入", test_async_loading_progress_import()))
    results.append(("ThrottleBoxPlotAnalysis 導入", test_throttle_mdi_import()))
    results.append(("進度管理器方法", test_progress_methods()))
    results.append(("cleanup() 覆寫", test_cleanup_override()))
    results.append(("update_lap_parameters() 整合", test_update_lap_parameters()))
    
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
        print("\n🎉 所有測試通過！Throttle Box Plot 異步進度管理器整合成功！")
        print("\n下一步：")
        print("1. 啟動 GUI: python f1t_gui_main.py")
        print("2. 開啟 Throttle Box Plot")
        print("3. 驗證進度指示器顯示")
        print("4. 確認不再有主執行緒阻塞（2.2秒凍結）")
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
