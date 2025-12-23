"""
測試 Throttle 模組跨賽事功能 - 驗證完整複製
測試範圍：
1. CrossEventThrottleComparisonWorker 類別存在
2. Worker 初始化正常
3. ThrottleAnalysisModule 新增的方法存在
4. 必要屬性正確初始化
"""

import sys
import os

# 設定 PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_worker_import():
    """測試 1: Worker 類別導入"""
    try:
        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import CrossEventThrottleComparisonWorker
        print("✅ CrossEventThrottleComparisonWorker 導入成功")
        return True
    except ImportError as e:
        print(f"❌ Worker 導入失敗: {e}")
        return False

def test_worker_initialization():
    """測試 2: Worker 初始化"""
    try:
        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import CrossEventThrottleComparisonWorker
        
        worker = CrossEventThrottleComparisonWorker(
            driver1="NOR",
            year1=2025,
            race1="Australia",
            session1="R",
            lap1=99,
            driver2="NOR",
            year2=2025,
            race2="Australia",
            session2="Q",
            lap2=99,
            timeout=120.0
        )
        
        # 驗證屬性
        assert worker.driver1 == "NOR"
        assert worker.year1 == 2025
        assert worker.race1 == "Australia"
        assert worker.session1 == "R"
        assert worker.lap1 == 99
        assert worker.driver2 == "NOR"
        assert worker.year2 == 2025
        assert worker.race2 == "Australia"
        assert worker.session2 == "Q"
        assert worker.lap2 == 99
        assert worker.timeout == 120.0
        
        # 驗證信號
        assert hasattr(worker, 'progress')
        assert hasattr(worker, 'success')
        assert hasattr(worker, 'failure')
        
        # 驗證 base_url
        assert hasattr(worker, 'base_url')
        assert isinstance(worker.base_url, str)
        
        print("✅ Worker 初始化驗證通過")
        print(f"   - base_url: {worker.base_url}")
        print(f"   - timeout: {worker.timeout}")
        return True
        
    except Exception as e:
        print(f"❌ Worker 初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_methods():
    """測試 3: ThrottleAnalysisModule 新增方法存在"""
    try:
        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import ThrottleAnalysisModule
        
        # 驗證方法存在
        required_methods = [
            'update_cross_event_comparison',
            '_on_cross_event_data_loaded',
            '_on_cross_event_load_error',
            '_on_api_progress',
            'update_from_shared_params',
            'get_window_title',
            'update_window_title',
            '_update_info_label'
        ]
        
        for method_name in required_methods:
            if not hasattr(ThrottleAnalysisModule, method_name):
                print(f"❌ 缺少方法: {method_name}")
                return False
        
        print("✅ 所有必要方法存在")
        for method in required_methods:
            print(f"   ✓ {method}")
        return True
        
    except Exception as e:
        print(f"❌ 方法驗證失敗: {e}")
        return False

def test_module_attributes():
    """測試 4: ThrottleAnalysisModule 屬性初始化"""
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import ThrottleAnalysisModule
        
        # 創建 QApplication（必要）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建模組實例
        module = ThrottleAnalysisModule()
        
        # 驗證跨賽事屬性
        assert hasattr(module, 'driver1_year')
        assert hasattr(module, 'driver1_race')
        assert hasattr(module, 'driver1_session')
        assert hasattr(module, 'driver2_year')
        assert hasattr(module, 'driver2_race')
        assert hasattr(module, 'driver2_session')
        
        # 驗證同步控制屬性
        assert hasattr(module, 'sync_driver_lap_enabled')
        assert hasattr(module, '_updating_from_shared')
        
        # 驗證時間軸屬性
        assert hasattr(module, 'use_time_axis')
        
        # 驗證預設值
        assert module.driver1_year == "2025"
        assert module.driver1_race == "Japan"
        assert module.driver1_session == "R"
        assert module.sync_driver_lap_enabled == True
        assert module._updating_from_shared == False
        assert module.use_time_axis == False
        
        print("✅ 模組屬性驗證通過")
        print(f"   - driver1_year: {module.driver1_year}")
        print(f"   - driver1_race: {module.driver1_race}")
        print(f"   - sync_driver_lap_enabled: {module.sync_driver_lap_enabled}")
        print(f"   - use_time_axis: {module.use_time_axis}")
        
        # 清理
        module.deleteLater()
        return True
        
    except Exception as e:
        print(f"❌ 屬性驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """執行所有測試"""
    print("=" * 60)
    print("Throttle 模組跨賽事功能測試")
    print("=" * 60)
    print()
    
    results = []
    
    # 測試 1: Worker 導入
    print("測試 1: Worker 類別導入")
    print("-" * 60)
    results.append(test_worker_import())
    print()
    
    # 測試 2: Worker 初始化
    print("測試 2: Worker 初始化")
    print("-" * 60)
    results.append(test_worker_initialization())
    print()
    
    # 測試 3: 模組方法
    print("測試 3: ThrottleAnalysisModule 方法驗證")
    print("-" * 60)
    results.append(test_module_methods())
    print()
    
    # 測試 4: 模組屬性
    print("測試 4: ThrottleAnalysisModule 屬性驗證")
    print("-" * 60)
    results.append(test_module_attributes())
    print()
    
    # 總結
    print("=" * 60)
    print("測試總結")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    print(f"通過: {passed}/{total}")
    
    if all(results):
        print("✅ 所有測試通過！Throttle 模組跨賽事功能複製成功！")
        return 0
    else:
        print("❌ 部分測試失敗，請檢查上面的錯誤訊息")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
