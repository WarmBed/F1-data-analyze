#!/usr/bin/env python3
"""
F101 數據載入測試（無 GUI）
測試 StartReactionDataLoader 能否正確載入 Abu Dhabi 2025 數據
"""

import sys
import os
os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

print("=" * 60)
print("F101 起跑反應分析 - 數據載入測試")
print("=" * 60)

try:
    print("\n[1] 導入 StartReactionDataLoader...")
    from modules.gui.race_analysis.start_reaction.start_reaction_loader import StartReactionDataLoader
    print("    OK")
    
    print("\n[2] 創建載入器 (2025 Abu_Dhabi R)...")
    loader = StartReactionDataLoader(2025, "Abu_Dhabi", "R")
    print("    OK")
    
    print("\n[3] 載入數據...")
    data = loader.load_data()
    
    if data:
        print(f"    OK - 載入成功!")
        print(f"\n[4] 數據摘要:")
        print(f"    - 車手數量: {len(data.get('drivers', []))}")
        print(f"    - 賽道: {data.get('race', 'N/A')}")
        print(f"    - 賽季: {data.get('year', 'N/A')}")
        print(f"    - 會話: {data.get('session', 'N/A')}")
        
        drivers = data.get('drivers', [])
        if drivers:
            print(f"\n[5] 前 5 名車手數據:")
            for i, driver in enumerate(drivers[:5]):
                code = driver.get('code', 'N/A')
                t50 = driver.get('time_0_50', 0)
                t100 = driver.get('time_0_100', 0)
                pos_change = driver.get('position_change', 0)
                print(f"    {i+1}. {code}: 0-50={t50:.3f}s, 0-100={t100:.3f}s, 位置變化={pos_change:+d}")
        
        print("\n" + "=" * 60)
        print(" 數據載入測試通過!")
        print("=" * 60)
    else:
        print("    FAIL - 無數據返回")
        sys.exit(1)
        
except Exception as e:
    print(f"\n ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
