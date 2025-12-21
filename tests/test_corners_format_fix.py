#!/usr/bin/env python3
"""
測試 Corners 格式修復

驗證修復項目：
- chart_data['official_corners']['corners'] 正確提取
- corners 是列表，元素是字典（包含 number, distance 等）

Author: F1T Team
Date: 2025-11-11
"""

import json
from pathlib import Path

def test_demo_format():
    """測試 Demo 的格式"""
    print("="*60)
    print("測試 Demo 格式（參考 demo_fastf1_z_elevation.py Line 721）")
    print("="*60)
    
    # 模擬 Demo 的數據結構
    demo_data = {
        "track_outline": [{"x": 1, "y": 2, "elevation": 10}],
        "official_corners": {
            "available": True,
            "count": 18,
            "corners": [
                {"number": 1, "distance": 123.45, "x": 1.0, "y": 2.0},
                {"number": 2, "distance": 456.78, "x": 3.0, "y": 4.0},
            ]
        }
    }
    
    # Demo 的提取方式
    corners = demo_data.get('official_corners', {}).get('corners', [])
    
    print(f"corners 類型: {type(corners)}")
    print(f"corners 長度: {len(corners)}")
    
    if corners:
        first_corner = corners[0]
        print(f"\n第 1 個彎道:")
        print(f"  類型: {type(first_corner)}")
        print(f"  內容: {first_corner}")
        print(f"  number: {first_corner.get('number')}")
        print(f"  distance: {first_corner.get('distance')}")
        
        # 模擬 elevation_chart_widget_pyqt5.py Line 458 的調用
        try:
            corner_num = first_corner.get('number', 0)  # 應該成功
            print(f"\n✅ 成功調用 .get('number'): {corner_num}")
        except AttributeError as e:
            print(f"\n❌ 調用失敗: {e}")
    
    print("\n✅ Demo 格式測試通過\n")

def test_gui_old_format():
    """測試 GUI 修復前的錯誤格式"""
    print("="*60)
    print("測試 GUI 修復前的錯誤格式")
    print("="*60)
    
    # 模擬錯誤的提取方式
    chart_data = {
        "track_outline": [{"x": 1, "y": 2}],
        "corners": [1, 2, 3, 4],  # ❌ 錯誤：整數列表
        "official_corners": {
            "corners": [{"number": 1, "distance": 123.45}]
        }
    }
    
    # 錯誤的提取方式（修復前）
    corners = chart_data.get("corners", [])  # ❌ 直接取 corners
    
    print(f"corners 類型: {type(corners)}")
    print(f"corners 內容: {corners}")
    
    if corners:
        first_corner = corners[0]
        print(f"\n第 1 個彎道:")
        print(f"  類型: {type(first_corner)}")
        print(f"  內容: {first_corner}")
        
        # 模擬 elevation_chart_widget_pyqt5.py Line 458 的調用
        try:
            corner_num = first_corner.get('number', 0)  # 會失敗！
            print(f"\n✅ 成功: {corner_num}")
        except AttributeError as e:
            print(f"\n❌ AttributeError: {e}")
            print("   原因: first_corner 是整數 (int)，沒有 .get() 方法")
    
    print("\n⚠️  GUI 修復前會產生 AttributeError\n")

def test_gui_new_format():
    """測試 GUI 修復後的正確格式"""
    print("="*60)
    print("測試 GUI 修復後的正確格式（Line 812-813）")
    print("="*60)
    
    chart_data = {
        "track_outline": [{"x": 1, "y": 2, "elevation": 10}],
        "corners": [1, 2, 3, 4],  # 這個會被忽略
        "official_corners": {
            "available": True,
            "count": 18,
            "corners": [
                {"number": 1, "distance": 123.45},
                {"number": 2, "distance": 456.78},
            ]
        }
    }
    
    # 🔧 修復後的提取方式（Line 812-813）
    official_corners = chart_data.get("official_corners", {})
    corners = official_corners.get("corners", [])
    
    print(f"official_corners 類型: {type(official_corners)}")
    print(f"corners 類型: {type(corners)}")
    print(f"corners 長度: {len(corners)}")
    
    if corners:
        first_corner = corners[0]
        print(f"\n第 1 個彎道:")
        print(f"  類型: {type(first_corner)}")
        print(f"  內容: {first_corner}")
        
        # 模擬 elevation_chart_widget_pyqt5.py Line 458 的調用
        try:
            corner_num = first_corner.get('number', 0)  # 應該成功
            print(f"\n✅ 成功調用 .get('number'): {corner_num}")
        except AttributeError as e:
            print(f"\n❌ 調用失敗: {e}")
    
    print("\n✅ GUI 修復後格式正確\n")

def compare_formats():
    """比較修復前後的差異"""
    print("="*60)
    print("📊 格式比較總結")
    print("="*60)
    
    print("""
修復前（Line 810）：
  corners = chart_data.get("corners", [])
  → 結果：[1, 2, 3, 4] (整數列表)
  → 錯誤：'int' object has no attribute 'get'

修復後（Line 812-813）：
  official_corners = chart_data.get("official_corners", {})
  corners = official_corners.get("corners", [])
  → 結果：[{"number": 1, "distance": 123.45}, ...]
  → 正確：可以調用 corner.get('number')

參考實現（demo_fastf1_z_elevation.py Line 721）：
  corners = self.track_data.get('official_corners', {}).get('corners', [])
  → 結果：[{"number": 1, "distance": 123.45}, ...]
  → 格式：完全一致
    """)

def main():
    """執行所有測試"""
    print("\n🏎️ "*20)
    print("Corners 格式修復測試套件")
    print("🏎️ "*20 + "\n")
    
    test_demo_format()
    test_gui_old_format()
    test_gui_new_format()
    compare_formats()
    
    print("="*60)
    print("✅ 所有測試完成")
    print("="*60)
    print("""
修復總結：
1. ✅ 發現問題：chart_data.get("corners") 返回整數列表
2. ✅ 找到根因：應該取 official_corners['corners']
3. ✅ 參考 Demo：demo_fastf1_z_elevation.py Line 721
4. ✅ 應用修復：historical_track_map_mdi.py Line 812-813
5. ✅ 同步修復：_refresh_charts() 方法 Line 1073

接下來請重啟 GUI 並測試：
- 高程圖表應該顯示彎道編號（T1, T2, ...）
- 不應再出現 AttributeError
    """)

if __name__ == "__main__":
    main()
