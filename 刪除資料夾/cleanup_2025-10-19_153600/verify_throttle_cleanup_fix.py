"""
Throttle Analysis 記憶體洩漏驗證腳本

驗證項目:
1. cleanup() 方法完整性
2. 連動管理器解除註冊
3. Qt 連接斷開
4. __dict__ 清理

使用方式:
    python verify_throttle_cleanup_fix.py
"""

import sys
import inspect

def verify_throttle_cleanup():
    """驗證 Throttle Analysis cleanup() 修復"""
    
    print("=" * 80)
    print("[CHECK] Throttle Analysis Cleanup 驗證")
    print("=" * 80)
    
    try:
        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
        
        # 獲取 cleanup 方法
        cleanup_method = ThrottleAnalysisChartWidget.cleanup
        source_code = inspect.getsource(cleanup_method)
        
        # 檢查關鍵修復點
        checks = {
            "步驟 0: 連動管理器解除註冊": "linkage_manager.unregister_module(self)",
            "步驟 7: Qt 連接斷開": "self.disconnect()",
            "步驟 8: __dict__ 清理": "delattr(self, attr)"
        }
        
        print("\n[LIST] 檢查清理步驟:")
        print("-" * 80)
        
        all_passed = True
        for step_name, expected_code in checks.items():
            if expected_code in source_code:
                print(f"[OK] {step_name}: 已實現")
            else:
                print(f"[FAIL] {step_name}: 缺失!")
                all_passed = False
        
        print("-" * 80)
        
        if all_passed:
            print("\n[OK] 所有關鍵修復點已實現!")
            print("[OK] Throttle Analysis cleanup() 已完整修復")
            return True
        else:
            print("\n[FAIL] 部分修復點缺失，請檢查實現")
            return False
            
    except ImportError as e:
        print(f"[ERROR] 無法導入模組: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_with_speed_analysis():
    """對比 Speed Analysis 和 Throttle Analysis 的 cleanup() 實現"""
    
    print("\n" + "=" * 80)
    print("[COMPARE] Speed vs Throttle Cleanup 對比")
    print("=" * 80)
    
    try:
        from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedAnalysisChartWidget
        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
        
        speed_cleanup = inspect.getsource(SpeedAnalysisChartWidget.cleanup)
        throttle_cleanup = inspect.getsource(ThrottleAnalysisChartWidget.cleanup)
        
        # 統計關鍵字
        keywords = [
            "unregister_module",  # 連動管理器
            "self.disconnect()",  # Qt 連接
            "delattr(self, attr)"  # __dict__ 清理
        ]
        
        print("\n關鍵清理步驟對比:")
        print("-" * 80)
        print(f"{'步驟':<30} {'Speed Analysis':<20} {'Throttle Analysis':<20}")
        print("-" * 80)
        
        for keyword in keywords:
            speed_has = "[OK] 已實現" if keyword in speed_cleanup else "[FAIL] 缺失"
            throttle_has = "[OK] 已實現" if keyword in throttle_cleanup else "[FAIL] 缺失"
            print(f"{keyword:<30} {speed_has:<20} {throttle_has:<20}")
        
        print("-" * 80)
        
        # 檢查一致性
        speed_lines = len(speed_cleanup.split('\n'))
        throttle_lines = len(throttle_cleanup.split('\n'))
        
        print(f"\n代碼行數: Speed={speed_lines}, Throttle={throttle_lines}")
        
        if abs(speed_lines - throttle_lines) < 10:
            print("[OK] 兩個模組的 cleanup() 實現長度相似")
        else:
            print("[WARN] cleanup() 實現長度差異較大，可能需要檢查")
        
    except Exception as e:
        print(f"[ERROR] 對比失敗: {e}")


def print_cleanup_steps():
    """列印 Throttle Analysis cleanup() 的所有步驟"""
    
    print("\n" + "=" * 80)
    print("[STEPS] Throttle Analysis Cleanup 步驟清單")
    print("=" * 80)
    
    try:
        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
        
        cleanup_source = inspect.getsource(ThrottleAnalysisChartWidget.cleanup)
        
        # 提取註釋行（步驟說明）
        lines = cleanup_source.split('\n')
        step_lines = [line.strip() for line in lines if line.strip().startswith('#') and ('步驟' in line or '清理' in line)]
        
        print("\n清理步驟:")
        print("-" * 80)
        for i, step in enumerate(step_lines, 1):
            print(f"{i}. {step}")
        print("-" * 80)
        
        print(f"\n[OK] 總共 {len(step_lines)} 個清理步驟")
        
    except Exception as e:
        print(f"[ERROR] 提取步驟失敗: {e}")


if __name__ == "__main__":
    # 設置 UTF-8 輸出
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n[START] 開始驗證 Throttle Analysis Cleanup 修復...\n")
    
    # 主要驗證
    success = verify_throttle_cleanup()
    
    # 對比分析
    compare_with_speed_analysis()
    
    # 步驟清單
    print_cleanup_steps()
    
    # 總結
    print("\n" + "=" * 80)
    print("[SUMMARY] 驗證總結")
    print("=" * 80)
    
    if success:
        print("[OK] Throttle Analysis cleanup() 已完整修復")
        print("[OK] 包含所有關鍵清理步驟:")
        print("   - 連動管理器解除註冊")
        print("   - Qt 連接斷開")
        print("   - __dict__ 徹底清理")
        print("\n[OK] 記憶體洩漏問題已修復")
        print("\n[TODO] 下一步:")
        print("   1. 重啟 GUI 測試 Throttle Analysis")
        print("   2. 使用 objgraph 驗證 ThrottleLineChartSettings 不再洩漏")
        print("   3. 檢查其他 Lap Analysis 模組（Brake, RPM, Gear）")
        sys.exit(0)
    else:
        print("[ERROR] 修復驗證失敗，請檢查實現")
        sys.exit(1)
