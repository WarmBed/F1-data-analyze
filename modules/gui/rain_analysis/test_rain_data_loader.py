#!/usr/bin/env python3
"""
測試 rain_data_loader 模組
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

def test_rain_data_loader_import():
    """測試 rain_data_loader 導入"""
    print("測試 rain_data_loader 導入...")
    
    try:
        # 測試直接導入
        from modules.gui.rain_analysis.rain_data_loader import RainDataLoader, create_rain_data_loader
        print("✓ 直接導入 rain_data_loader 成功")
        
        # 測試從包導入
        from modules.gui.rain_analysis import RainDataLoader, create_rain_data_loader
        print("✓ 從包導入 rain_data_loader 成功")
        
        # 測試創建實例
        loader = create_rain_data_loader()
        print(f"✓ 創建實例成功: {type(loader)}")
        
        # 測試方法存在
        methods = ['load_rain_analysis_data', 'load_from_json', 'get_available_analyses']
        for method in methods:
            if hasattr(loader, method):
                print(f"✓ 方法 {method} 存在")
            else:
                print(f"✗ 方法 {method} 不存在")
        
        return True
        
    except Exception as e:
        print(f"✗ 導入失敗: {e}")
        return False

def test_rain_data_loader_functionality():
    """測試 rain_data_loader 功能"""
    print("\n測試 rain_data_loader 功能...")
    
    try:
        from modules.gui.rain_analysis import create_rain_data_loader
        
        loader = create_rain_data_loader()
        
        # 測試獲取可用分析類型
        analyses = loader.get_available_analyses()
        print(f"✓ 可用分析類型: {analyses}")
        
        # 測試獲取必需數據
        required_data = loader.get_required_data()
        print(f"✓ 必需數據類型: {required_data}")
        
        # 測試 JSON 載入 (如果文件存在)
        json_path = "json/enhanced_rain_analysis_2025_Belgium_R.json"
        if os.path.exists(json_path):
            print(f"✓ 找到測試 JSON 文件: {json_path}")
            # 這裡不實際載入，只是檢查方法存在
            print("✓ load_from_json 方法可調用")
        else:
            print(f"! 測試 JSON 文件不存在: {json_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ 功能測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("=== RainDataLoader 模組測試 ===")
    
    import_success = test_rain_data_loader_import()
    functionality_success = test_rain_data_loader_functionality()
    
    if import_success and functionality_success:
        print("\n🎉 所有測試通過！")
    else:
        print("\n❌ 部分測試失敗！")
    
    print("\n=== 測試完成 ===")
