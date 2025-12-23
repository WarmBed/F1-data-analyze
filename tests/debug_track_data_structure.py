#!/usr/bin/env python3
"""
調試 track_data 與 chart_data 的結構差異

檢查項目：
1. track_data 是否包含 official_corners
2. chart_data 是否包含 official_corners
3. 兩者的數據格式是否一致

Author: F1T Team
Date: 2025-11-11
"""

import json
from pathlib import Path

def check_json_structure():
    """檢查 JSON 檔案結構"""
    print("="*70)
    print("檢查 Function 100 JSON 結構")
    print("="*70)
    
    # 查找 JSON 檔案
    json_dir = Path('json')
    json_files = list(json_dir.glob('historical_track_flags_*_2024_Japan_R_*.json'))
    
    if not json_files:
        print("⚠️  找不到 JSON 檔案")
        return
    
    print(f"使用檔案: {json_files[0].name}\n")
    
    # 讀取檔案
    with open(json_files[0], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查雙重嵌套
    if "function_id" in data and "data" in data:
        print("⚠️  檢測到雙重嵌套，提取內層 data")
        data = data["data"]
    
    print(f"JSON 頂層鍵: {list(data.keys())}\n")
    
    # 檢查 track_data
    print("="*70)
    print("1️⃣  track_data 結構")
    print("="*70)
    
    track_data = data.get('track_data', {})
    print(f"track_data 鍵: {list(track_data.keys())}\n")
    
    if 'official_corners' in track_data:
        official_corners = track_data['official_corners']
        print(f"✅ track_data 包含 official_corners")
        print(f"   類型: {type(official_corners)}")
        print(f"   鍵: {list(official_corners.keys()) if isinstance(official_corners, dict) else 'N/A'}")
        
        if 'corners' in official_corners:
            corners = official_corners['corners']
            print(f"\n   corners:")
            print(f"     類型: {type(corners)}")
            print(f"     長度: {len(corners) if isinstance(corners, list) else 'N/A'}")
            
            if isinstance(corners, list) and corners:
                print(f"\n     範例 (前 3 個):")
                for i, corner in enumerate(corners[:3]):
                    print(f"       [{i}]: {corner}")
    else:
        print(f"❌ track_data 不包含 official_corners")
    
    # 檢查 chart_data
    print("\n" + "="*70)
    print("2️⃣  chart_data 結構")
    print("="*70)
    
    chart_data = data.get('chart_data', {})
    print(f"chart_data 鍵: {list(chart_data.keys())}\n")
    
    if 'official_corners' in chart_data:
        official_corners = chart_data['official_corners']
        print(f"✅ chart_data 包含 official_corners")
        print(f"   類型: {type(official_corners)}")
        print(f"   鍵: {list(official_corners.keys()) if isinstance(official_corners, dict) else 'N/A'}")
        
        if 'corners' in official_corners:
            corners = official_corners['corners']
            print(f"\n   corners:")
            print(f"     類型: {type(corners)}")
            print(f"     長度: {len(corners) if isinstance(corners, list) else 'N/A'}")
            
            if isinstance(corners, list) and corners:
                print(f"\n     範例 (前 3 個):")
                for i, corner in enumerate(corners[:3]):
                    print(f"       [{i}]: {corner}")
    else:
        print(f"❌ chart_data 不包含 official_corners")
    
    # 比較分析
    print("\n" + "="*70)
    print("3️⃣  問題診斷")
    print("="*70)
    
    has_track_corners = 'official_corners' in track_data
    has_chart_corners = 'official_corners' in chart_data
    
    print(f"\ntrack_data 包含 official_corners: {has_track_corners}")
    print(f"chart_data 包含 official_corners: {has_chart_corners}")
    
    if has_track_corners and has_chart_corners:
        print("\n✅ 兩者都包含 official_corners，數據結構正確")
    elif has_track_corners and not has_chart_corners:
        print("\n⚠️  track_data 有但 chart_data 沒有 official_corners")
        print("   可能原因：chart_data 構建時遺漏了 official_corners")
    elif not has_track_corners and has_chart_corners:
        print("\n⚠️  chart_data 有但 track_data 沒有 official_corners")
        print("   可能原因：track_data 構建時遺漏了 official_corners")
    else:
        print("\n❌ 兩者都沒有 official_corners")
        print("   可能原因：Function 100 未生成 official_corners 數據")
    
    # 檢查 Demo 的數據格式要求
    print("\n" + "="*70)
    print("4️⃣  Demo 數據格式要求")
    print("="*70)
    
    print("""
Demo (demo_fastf1_z_elevation.py) 的數據要求：

TrackMapWidget (Line 115-116):
  → 需要 track_data['official_corners']['corners']
  → 格式：[{"number": 1, "distance": 123.45, "x": 1.0, "y": 2.0}, ...]

ElevationChartWidget (Line 721):
  → 需要 track_data.get('official_corners', {}).get('corners', [])
  → 格式：[{"number": 1, "distance": 123.45}, ...]

主 GUI (historical_track_map_mdi.py) 的傳遞：

Line 791: self.track_map.load_track_data(track_data)
  → 傳遞 track_data（應包含 official_corners）

Line 812-813: 
  official_corners = chart_data.get("official_corners", {})
  corners = official_corners.get("corners", [])
  → 從 chart_data 提取 corners（用於高程圖表）
    """)

if __name__ == "__main__":
    check_json_structure()
