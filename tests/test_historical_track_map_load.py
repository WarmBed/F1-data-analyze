#!/usr/bin/env python3
"""
Historical Track Map 模組測試
測試 API 數據載入和轉換流程

測試階段：
1. Import 測試
2. JSON 數據結構驗證
3. API 數據轉換測試
4. GUI 數據格式驗證

Author: F1T Team
Date: 2025-11-11
"""

import sys
import json
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

def test_stage_1_import():
    """階段 1: 測試模組導入"""
    print("\n" + "="*80)
    print("階段 1: 測試模組導入")
    print("="*80)
    
    try:
        from modules.gui.Historical_track_map.historical_track_map_mdi import HistoricalTrackMapMDI
        print("✅ HistoricalTrackMapMDI 導入成功")
        
        from modules.gui.Historical_track_map.historical_track_map_data_loader import HistoricalTrackMapDataLoader
        print("✅ HistoricalTrackMapDataLoader 導入成功")
        
        return True
    except Exception as e:
        print(f"❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stage_2_json_structure():
    """階段 2: 測試 JSON 數據結構"""
    print("\n" + "="*80)
    print("階段 2: 測試 JSON 數據結構")
    print("="*80)
    
    json_file = Path("json/historical_flags_Japan_2022-2025.json")
    if not json_file.exists():
        print(f"⚠️  JSON 檔案不存在: {json_file}")
        print("提示: 請先執行 CLI 生成數據:")
        print("  python f1_analysis_modular_main.py -f 100 -y 2024 -r Japan -s R")
        return False
    
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"✅ JSON 檔案載入成功: {json_file.name}")
        print(f"   頂層鍵: {list(data.keys())}")
        
        # 驗證結構
        assert "function_id" in data, "缺少 function_id"
        assert "data" in data, "缺少 data"
        assert data["function_id"] == 100, f"function_id 錯誤: {data['function_id']}"
        
        api_data = data["data"]
        print(f"   data 鍵: {list(api_data.keys())}")
        
        # 驗證核心欄位
        assert "metadata" in api_data, "缺少 metadata"
        assert "yearly_summary" in api_data, "缺少 yearly_summary"
        assert "detailed_position_records" in api_data, "缺少 detailed_position_records"
        assert "track_bounds" in api_data, "缺少 track_bounds"
        
        print(f"   位置點數量: {len(api_data['detailed_position_records'])}")
        print(f"   年份數量: {len(api_data['yearly_summary'])}")
        print(f"   年份列表: {list(api_data['yearly_summary'].keys())}")
        
        if api_data.get("elevation_profile"):
            elev = api_data["elevation_profile"]
            if elev.get("available"):
                print(f"   ✅ 高程數據可用: {elev['min_elevation']:.1f}m ~ {elev['max_elevation']:.1f}m")
        
        print("✅ JSON 數據結構驗證通過")
        return api_data
    
    except Exception as e:
        print(f"❌ JSON 結構驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_stage_3_data_transformation(api_data):
    """階段 3: 測試 API 數據轉換"""
    print("\n" + "="*80)
    print("階段 3: 測試 API 數據轉換")
    print("="*80)
    
    try:
        from modules.gui.Historical_track_map.historical_track_map_mdi import HistoricalTrackMapMDI
        
        # 創建 MDI 實例（不需要 parent）
        mdi = HistoricalTrackMapMDI()
        print("✅ HistoricalTrackMapMDI 實例創建成功")
        
        # 調用轉換方法
        print("\n開始數據轉換...")
        gui_data = mdi._transform_api_data_to_gui_format(api_data)
        
        # 驗證返回值
        if gui_data is None:
            print("❌ 轉換返回 None！")
            return None
        
        if not isinstance(gui_data, dict):
            print(f"❌ 轉換結果不是字典: {type(gui_data)}")
            return None
        
        print(f"✅ 數據轉換成功")
        print(f"   GUI 數據鍵: {list(gui_data.keys())}")
        
        # 驗證 GUI 數據結構
        required_keys = ["track_data", "chart_data", "yearly_summary", "metadata"]
        for key in required_keys:
            if key not in gui_data:
                print(f"❌ 缺少必要鍵: {key}")
                return None
            print(f"   ✅ {key}: {type(gui_data[key])}")
        
        # 驗證 track_data 結構
        track_data = gui_data["track_data"]
        if "detailed_position_records" not in track_data:
            print("❌ track_data 缺少 detailed_position_records")
            return None
        print(f"   track_data 位置點數: {len(track_data['detailed_position_records'])}")
        
        # 驗證 chart_data 結構
        chart_data = gui_data["chart_data"]
        if "track_outline" not in chart_data:
            print("❌ chart_data 缺少 track_outline")
            return None
        print(f"   chart_data 位置點數: {len(chart_data['track_outline'])}")
        print(f"   chart_data 彎道數: {len(chart_data.get('corners', []))}")
        
        # 驗證高程數據
        if gui_data.get("elevation_profile"):
            elev = gui_data["elevation_profile"]
            if isinstance(elev, dict) and elev.get("available"):
                print(f"   ✅ 高程數據: {elev['min_elevation']:.1f}m ~ {elev['max_elevation']:.1f}m")
        
        print("✅ GUI 數據結構驗證通過")
        return gui_data
    
    except Exception as e:
        print(f"❌ 數據轉換失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_stage_4_method_verification():
    """階段 4: 驗證 MDI 方法存在"""
    print("\n" + "="*80)
    print("階段 4: 驗證 MDI 方法存在")
    print("="*80)
    
    try:
        from modules.gui.Historical_track_map.historical_track_map_mdi import HistoricalTrackMapMDI
        
        mdi = HistoricalTrackMapMDI()
        
        # 檢查必要方法
        required_methods = [
            "initialize_module",
            "load_initial_data",
            "_on_api_success",
            "_on_api_failure",
            "_transform_api_data_to_gui_format",
            "_on_data_loaded",
            "_show_error",
        ]
        
        for method_name in required_methods:
            if hasattr(mdi, method_name):
                print(f"   ✅ {method_name}")
            else:
                print(f"   ❌ 缺少方法: {method_name}")
                return False
        
        print("✅ 所有必要方法已實現")
        return True
    
    except Exception as e:
        print(f"❌ 方法驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """執行所有測試"""
    print("="*80)
    print(" Historical Track Map 模組測試套件")
    print("="*80)
    
    results = []
    
    # 階段 1: Import
    results.append(("Import 測試", test_stage_1_import()))
    if not results[-1][1]:
        print("\n❌ Import 失敗，終止測試")
        return False
    
    # 階段 2: JSON 結構
    api_data = test_stage_2_json_structure()
    results.append(("JSON 結構驗證", api_data is not None))
    if api_data is None:
        print("\n❌ JSON 數據不可用，終止測試")
        return False
    
    # 階段 3: 數據轉換
    gui_data = test_stage_3_data_transformation(api_data)
    results.append(("數據轉換測試", gui_data is not None))
    
    # 階段 4: 方法驗證
    results.append(("方法驗證", test_stage_4_method_verification()))
    
    # 總結
    print("\n" + "="*80)
    print(" 測試總結")
    print("="*80)
    for name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 所有測試通過！模組已準備好整合到 GUI")
    else:
        print("\n⚠️  部分測試失敗，需要修復")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
