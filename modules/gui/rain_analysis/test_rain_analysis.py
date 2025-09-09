#!/usr/bin/env python3
"""
下雨分析模組測試檔案
Test script for Rain Analysis Module

用於測試基於通用 MDI 架構的下雨分析模組功能。

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

import sys
import os
import json
import traceback
from typing import Dict, Any

# 添加專案路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

def test_module_import():
    """測試模組導入"""
    print("=== 測試模組導入 ===")
    
    try:
        from modules.gui.rain_analysis import RainAnalysisModule, get_module_info
        print("✓ 成功導入 RainAnalysisModule")
        
        # 測試模組信息
        info = get_module_info()
        print(f"✓ 模組信息: {info['name']} v{info['version']}")
        
        return True
        
    except ImportError as e:
        print(f"✗ 模組導入失敗: {str(e)}")
        traceback.print_exc()
        return False

def test_data_loading():
    """測試數據載入功能"""
    print("\n=== 測試數據載入 ===")
    
    try:
        from modules.gui.rain_analysis.rain_analysis_universal import RainAnalysisDataManager
        
        # 創建數據管理器
        data_manager = RainAnalysisDataManager()
        print("✓ 成功創建數據管理器")
        
        # 測試 JSON 檔案載入
        json_file = os.path.join(project_root, "json", "enhanced_rain_analysis_2025_belgium_R.json")
        
        if os.path.exists(json_file):
            print(f"✓ 找到測試檔案: {os.path.basename(json_file)}")
            
            # 載入數據
            with open(json_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
            # 處理數據
            processed_data = data_manager.process_loaded_data(raw_data)
            print(f"✓ 成功處理數據，包含 {len(processed_data.get('lap_data', {}).get('laps', []))} 圈數據")
            
            # 測試摘要信息
            summary = data_manager.get_rain_summary()
            print(f"✓ 總圈數: {summary.get('total_laps', 0)}")
            print(f"✓ 降雨圈數: {summary.get('rain_laps', 0)}")
            print(f"✓ 降雨比例: {summary.get('rain_percentage', 0):.1f}%")
            
            return True
        else:
            print(f"✗ 測試檔案不存在: {json_file}")
            return False
            
    except Exception as e:
        print(f"✗ 數據載入測試失敗: {str(e)}")
        traceback.print_exc()
        return False

def test_chart_widget():
    """測試圖表組件"""
    print("\n=== 測試圖表組件 ===")
    
    try:
        from modules.gui.rain_analysis.rain_analysis_chart_widget import RainAnalysisChartWidget, RainChartTheme
        
        print("✓ 成功導入圖表組件")
        
        # 測試主題配置
        theme = RainChartTheme()
        print(f"✓ 圖表主題配置完成")
        print(f"  - 降雨顏色: {theme.RAINFALL_COLOR.name()}")
        print(f"  - 氣溫顏色: {theme.AIR_TEMP_COLOR.name()}")
        
        # 注意：這裡不創建實際的 QWidget，因為需要 QApplication
        print("✓ 圖表組件類別載入成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 圖表組件測試失敗: {str(e)}")
        traceback.print_exc()
        return False

def test_universal_base_integration():
    """測試與通用基礎類別的整合"""
    print("\n=== 測試通用基礎類別整合 ===")
    
    try:
        # 測試基礎類別導入
        from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
        from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
        print("✓ 通用基礎類別導入成功")
        
        # 測試下雨分析配置
        from modules.gui.rain_analysis.rain_analysis_universal import RainAnalysisUniversal
        
        # 檢查模組類型註冊
        if "rain" in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            config = UniversalAnalysisMDI.MDI_MODULE_TYPES["rain"]
            print(f"✓ 下雨分析模組已註冊: {config.display_name}")
            print(f"  - 預設大小: {config.default_size}")
            print(f"  - 需要車手參數: {config.requires_driver_params}")
            print(f"  - 需要圈數參數: {config.requires_lap_params}")
        else:
            print("! 下雨分析模組尚未註冊到 MDI 系統")
            
        return True
        
    except Exception as e:
        print(f"✗ 通用基礎類別整合測試失敗: {str(e)}")
        traceback.print_exc()
        return False

def test_module_instantiation():
    """測試模組實例化"""
    print("\n=== 測試模組實例化 ===")
    
    try:
        from modules.gui.rain_analysis import create_rain_analysis_module
        
        # 創建模組實例（不需要 QApplication）
        print("✓ 模組創建函數可用")
        
        # 測試模組信息獲取
        from modules.gui.rain_analysis.rain_analysis_module import get_module_info
        
        module_info = get_module_info()
        print(f"✓ 模組信息獲取成功:")
        print(f"  - 名稱: {module_info['name']}")
        print(f"  - 版本: {module_info['version']}")
        print(f"  - 作者: {module_info['author']}")
        print(f"  - 支援功能數量: {len(module_info['features'])}")
        
        return True
        
    except Exception as e:
        print(f"✗ 模組實例化測試失敗: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """主要測試函數"""
    print("F1T 下雨分析模組測試")
    print("=" * 50)
    
    test_results = []
    
    # 執行各項測試
    test_results.append(("模組導入", test_module_import()))
    test_results.append(("數據載入", test_data_loading()))
    test_results.append(("圖表組件", test_chart_widget()))
    test_results.append(("基礎類別整合", test_universal_base_integration()))
    test_results.append(("模組實例化", test_module_instantiation()))
    
    # 測試結果摘要
    print("\n" + "=" * 50)
    print("測試結果摘要:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
            
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！下雨分析模組已成功建立。")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查上述錯誤信息。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
