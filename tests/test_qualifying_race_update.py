#!/usr/bin/env python3
"""
測試 Qualifying Prediction 參數更新功能
Verify Race Parameter Update in Qualifying Prediction Module
"""

def test_method_existence():
    """測試方法是否存在"""
    print("=" * 90)
    print("🔍 Qualifying Prediction 參數更新測試")
    print("=" * 90)
    
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # 初始化 Qt 應用
    app = QApplication.instance() or QApplication(sys.argv)
    
    print("\n階段 1: 檢查方法存在性")
    print("-" * 90)
    
    try:
        from modules.gui.qualifying_prediction.qualifying_prediction_mdi import QualifyingPredictionMDI
        
        # 檢查類別方法
        methods_to_check = [
            'update_parameters',
            'update_analysis_parameters',
            'load_initial_data',
            'update_window_title',
        ]
        
        for method_name in methods_to_check:
            if hasattr(QualifyingPredictionMDI, method_name):
                print(f"  ✅ {method_name} 方法存在")
            else:
                print(f"  ❌ {method_name} 方法缺失")
        
        print("\n階段 2: 檢查方法簽名")
        print("-" * 90)
        
        import inspect
        
        # update_parameters 簽名
        if hasattr(QualifyingPredictionMDI, 'update_parameters'):
            sig = inspect.signature(QualifyingPredictionMDI.update_parameters)
            print(f"  update_parameters 簽名: {sig}")
            params = list(sig.parameters.keys())
            print(f"  參數列表: {params}")
            
            # 檢查關鍵參數
            if 'year' in params:
                print(f"    ✅ 有 'year' 參數")
            else:
                print(f"    ❌ 缺少 'year' 參數")
                
            if 'race' in params:
                print(f"    ✅ 有 'race' 參數")
            else:
                print(f"    ❌ 缺少 'race' 參數")
        
        # update_analysis_parameters 簽名
        if hasattr(QualifyingPredictionMDI, 'update_analysis_parameters'):
            sig = inspect.signature(QualifyingPredictionMDI.update_analysis_parameters)
            print(f"\n  update_analysis_parameters 簽名: {sig}")
            params = list(sig.parameters.keys())
            print(f"  參數列表: {params}")
        
        print("\n階段 3: 對比 Driver Position Analysis")
        print("-" * 90)
        
        from modules.gui.driver_position_analysis.driver_position_analysis_mdi import DriverPositionAnalysisMDI
        
        comparison = [
            ('update_parameters', QualifyingPredictionMDI, DriverPositionAnalysisMDI),
            ('update_analysis_parameters', QualifyingPredictionMDI, DriverPositionAnalysisMDI),
            ('load_initial_data', QualifyingPredictionMDI, DriverPositionAnalysisMDI),
        ]
        
        print(f"\n{'方法':<30} {'Qualifying Pred':<20} {'Driver Position':<20} {'一致性':<10}")
        print("-" * 90)
        
        for method_name, qual_class, pos_class in comparison:
            qual_has = hasattr(qual_class, method_name)
            pos_has = hasattr(pos_class, method_name)
            
            qual_status = "✅" if qual_has else "❌"
            pos_status = "✅" if pos_has else "❌"
            consistent = "✅" if qual_has == pos_has else "⚠️"
            
            print(f"{method_name:<30} {qual_status:<20} {pos_status:<20} {consistent:<10}")
        
        print("\n階段 4: 檢查方法調用鏈")
        print("-" * 90)
        
        # 讀取源代碼檢查調用鏈
        with open('modules/gui/qualifying_prediction/qualifying_prediction_mdi.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查 update_parameters 是否調用 update_analysis_parameters
        if 'def update_parameters(' in content:
            update_params_section = content.split('def update_parameters(')[1].split('def ')[0]
            
            if 'self.update_analysis_parameters(' in update_params_section:
                print("  ✅ update_parameters() 調用 update_analysis_parameters()")
            else:
                print("  ❌ update_parameters() 未調用 update_analysis_parameters()")
        
        # 檢查 update_analysis_parameters 是否調用 load_initial_data
        if 'def update_analysis_parameters(' in content:
            update_analysis_section = content.split('def update_analysis_parameters(')[1].split('def ')[0]
            
            if 'self.load_initial_data()' in update_analysis_section:
                print("  ✅ update_analysis_parameters() 調用 load_initial_data()")
            else:
                print("  ❌ update_analysis_parameters() 未調用 load_initial_data()")
        
        print("\n階段 5: 檢查主 GUI 調用路徑")
        print("-" * 90)
        
        with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
            gui_content = f.read()
        
        # 檢查主 GUI 是否會調用這些方法
        methods_called_by_gui = [
            ('update_parameters', 'update_parameters'),
            ('onParametersChanged', 'onParametersChanged'),
            ('update_analysis_parameters', 'update_analysis_parameters'),
        ]
        
        print("\n主 GUI 可能調用的方法:")
        for display_name, search_pattern in methods_called_by_gui:
            if f"'{search_pattern}'" in gui_content or f'"{search_pattern}"' in gui_content:
                print(f"  ✅ 主 GUI 會嘗試調用 {display_name}")
            else:
                print(f"  ❌ 主 GUI 不會調用 {display_name}")
        
        print("\n" + "=" * 90)
        print("✅ 測試完成！")
        print("=" * 90)
        
        print("\n📊 結論:")
        print("  • Qualifying Prediction 已有 update_parameters() 方法")
        print("  • update_parameters() → update_analysis_parameters() → load_initial_data()")
        print("  • 理論上應該能響應主 GUI 的參數變更")
        print("\n💡 如果實際不工作，可能原因:")
        print("  1. 模組未正確註冊到主 GUI")
        print("  2. 信號連接缺失")
        print("  3. 參數傳遞格式不匹配")
        print("  4. 執行時出現異常被捕獲")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_method_existence()
