#!/usr/bin/env python3
"""
檢查不同賽道的 Sector 座標
Check Sector Coordinates for Different Tracks

比較 Brazil 和 Bahrain 的 sector_boundaries 座標
"""

import json
from pathlib import Path

def check_sector_coordinates():
    """檢查並比較不同賽道的 Sector 座標"""
    
    json_dir = Path("json")
    
    # Brazil 座標
    print("=" * 80)
    print("Brazil Sector Boundaries")
    print("=" * 80)
    brazil_json = json_dir / "historical_flags_Brazil_2022-2025.json"
    if brazil_json.exists():
        with open(brazil_json, 'r', encoding='utf-8') as f:
            brazil_data = json.load(f)
        
        brazil_sb = brazil_data.get('data', {}).get('sector_boundaries', [])
        for sb in brazil_sb:
            print(f"{sb.get('name'):25} | X: {sb.get('position_x'):10.1f} | Y: {sb.get('position_y'):10.1f} | Dist: {sb.get('distance_m'):8.1f}m")
    
    # Bahrain 座標
    print("\n" + "=" * 80)
    print("Bahrain Sector Boundaries")
    print("=" * 80)
    bahrain_json = json_dir / "historical_flags_Bahrain_2022-2025.json"
    if bahrain_json.exists():
        with open(bahrain_json, 'r', encoding='utf-8') as f:
            bahrain_data = json.load(f)
        
        bahrain_sb = bahrain_data.get('data', {}).get('sector_boundaries', [])
        for sb in bahrain_sb:
            print(f"{sb.get('name'):25} | X: {sb.get('position_x'):10.1f} | Y: {sb.get('position_y'):10.1f} | Dist: {sb.get('distance_m'):8.1f}m")
    
    # 比較
    print("\n" + "=" * 80)
    print("座標差異分析")
    print("=" * 80)
    print("""
如果截圖中顯示的是 Brazil 賽道，但 Sector 位置不對：
- 檢查 Console 輸出中的座標
- 如果看到 Bahrain 的座標（X: 5806.0, Y: 4839.0），則說明保留了舊座標
- 如果看到 Brazil 的座標（X: 2126.9, Y: -2616.1），則座標正確

Brazil 特徵座標：
  S1 End: X ≈ 2126.9, Y ≈ -2616.1
  S2 End: X ≈ -4.0,    Y ≈ 660.0
  S3 End: X ≈ -3674.2, Y ≈ -5269.4

Bahrain 特徵座標：
  S1 End: X ≈ 5806.0, Y ≈ 4839.0
  S2 End: X ≈ 5996.4, Y ≈ 1202.7
  S3 End: X ≈ -379.6, Y ≈ 1297.7

問題診斷：
如果在 Brazil 賽道上看到 Bahrain 的座標 → 保護性邏輯過度保留了舊數據
解決方案：需要在切換賽道時檢測到新賽道，並且只在同一賽道內保留座標
""")

if __name__ == "__main__":
    check_sector_coordinates()
