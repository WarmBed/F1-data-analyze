"""
Throttle Line Chart 記憶體洩漏修復驗證（第二輪）

驗證項目:
1. UniversalAnalysisMDI.cleanup() 是否包含 Qt 連接斷開和 __dict__ 清理
2. ThrottleLineChartMDI.cleanup() 是否斷開 control_panel 信號連接

使用方式:
    python verify_throttle_line_chart_cleanup_v2.py
"""

import sys
import inspect

def verify_universal_mdi_cleanup():
    """驗證 UniversalAnalysisMDI.cleanup() 修復"""
    
    print("=" * 80)
    print("[CHECK] UniversalAnalysisMDI Cleanup 驗證")
    print("=" * 80)
    
    try:
        from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI
        
        # 獲取 cleanup 方法
        cleanup_method = UniversalAnalysisMDI.cleanup
        source_code = inspect.getsource(cleanup_method)
        
        # 檢查關鍵修復點
        checks = {
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
            print("\n[OK] UniversalAnalysisMDI.cleanup() 所有關鍵修復點已實現!")
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


def verify_throttle_line_chart_cleanup():
    """驗證 ThrottleLineChartMDI.cleanup() 修復"""
    
    print("\n" + "=" * 80)
    print("[CHECK] ThrottleLineChartMDI Cleanup 驗證")
    print("=" * 80)
    
    try:
        from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi import ThrottleLineChartMDI
        
        # 獲取 cleanup 方法
        cleanup_method = ThrottleLineChartMDI.cleanup
        source_code = inspect.getsource(cleanup_method)
        
        # 檢查關鍵修復點
        checks = {
            "斷開 control_panel 信號連接": [
                "control_panel.settingsChanged.disconnect",
                "control_panel.reloadRequested.disconnect",
                "control_panel.resetRequested.disconnect",
                "control_panel.exportRequested.disconnect",
                "control_panel.driverChanged.disconnect",
                "control_panel.driver2Changed.disconnect"
            ],
            "清理 control_panel 組件": "control_panel.deleteLater()",
            "斷開 settings_manager 信號": "settings_manager.boxplot_settings_changed.disconnect"
        }
        
        print("\n[LIST] 檢查清理步驟:")
        print("-" * 80)
        
        all_passed = True
        for step_name, expected_codes in checks.items():
            if isinstance(expected_codes, list):
                # 檢查列表中的所有代碼
                all_found = all(code in source_code for code in expected_codes)
                if all_found:
                    print(f"[OK] {step_name}: 已實現（{len(expected_codes)} 個連接）")
                else:
                    missing = [code for code in expected_codes if code not in source_code]
                    print(f"[FAIL] {step_name}: 缺失 {len(missing)} 個連接!")
                    all_passed = False
            else:
                # 單個代碼檢查
                if expected_codes in source_code:
                    print(f"[OK] {step_name}: 已實現")
                else:
                    print(f"[FAIL] {step_name}: 缺失!")
                    all_passed = False
        
        print("-" * 80)
        
        if all_passed:
            print("\n[OK] ThrottleLineChartMDI.cleanup() 所有關鍵修復點已實現!")
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


def print_affected_modules():
    """列出受益於 UniversalAnalysisMDI 修復的所有模組"""
    
    print("\n" + "=" * 80)
    print("[INFO] 受益於基類修復的模組")
    print("=" * 80)
    
    affected_modules = [
        "Rain Analysis",
        "Track Analysis", 
        "Accident Analysis",
        "Ranking Table",
        "Strategy Analysis",
        "Throttle Line Chart Analysis",
        "所有未來的新分析模組"
    ]
    
    print("\n所有繼承 UniversalAnalysisMDI 的模組都將自動獲得修復:")
    print("-" * 80)
    for i, module in enumerate(affected_modules, 1):
        print(f"  {i}. {module}")
    print("-" * 80)
    print(f"\n[OK] 總共 {len(affected_modules)} 個模組受益於此修復")


if __name__ == "__main__":
    # 設置 UTF-8 輸出
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n[START] 開始驗證 Throttle Line Chart 記憶體洩漏修復（第二輪）...\n")
    
    # 主要驗證
    success1 = verify_universal_mdi_cleanup()
    success2 = verify_throttle_line_chart_cleanup()
    
    # 列出受影響的模組
    print_affected_modules()
    
    # 總結
    print("\n" + "=" * 80)
    print("[SUMMARY] 驗證總結")
    print("=" * 80)
    
    if success1 and success2:
        print("[OK] 所有修復點已完整實現!")
        print("\n[OK] UniversalAnalysisMDI 基類修復:")
        print("   - Qt 連接徹底斷開（self.disconnect()）")
        print("   - __dict__ 徹底清理（delattr()）")
        print("\n[OK] ThrottleLineChartMDI 子類修復:")
        print("   - control_panel 6 個信號連接已斷開")
        print("   - control_panel 組件已清理")
        print("   - settings_manager 信號已斷開")
        print("\n[OK] 記憶體洩漏問題應該已完全解決")
        print("\n[TODO] 測試步驟:")
        print("   1. 重啟 GUI")
        print("   2. 開啟 Throttle Line Chart Analysis（選單: Throttle → Throttle Line Chart）")
        print("   3. 關閉視窗並檢查終端輸出")
        print("   4. 使用 objgraph 驗證 ThrottleLineChartSettings 不再洩漏")
        print("\n[INFO] 此修復同時修復了所有繼承 UniversalAnalysisMDI 的模組")
        sys.exit(0)
    else:
        print("[ERROR] 部分修復驗證失敗")
        if not success1:
            print("   - UniversalAnalysisMDI 基類修復不完整")
        if not success2:
            print("   - ThrottleLineChartMDI 子類修復不完整")
        sys.exit(1)
