#!/usr/bin/env python3
"""測試功能 3 的實際執行情況"""

import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 測試功能 3 - United States 2025 R")
print("=" * 80)

try:
    from core.data_loader import F1DataLoader
    from CLI_modules.cli.analyzer.driver_fastest_pitstop_ranking import (
        get_session_info,
        analyze_driver_fastest_pitstops
    )
    
    # 載入數據
    print("\n📡 步驟 1: 載入 FastF1 數據...")
    loader = F1DataLoader()
    success = loader.load_data(2025, "United States", "R")
    
    if not success:
        print("❌ 數據載入失敗")
        sys.exit(1)
    
    print("✅ 數據載入成功")
    
    # 獲取會話資訊
    print("\n📊 步驟 2: 獲取會話資訊...")
    session_info = get_session_info(loader)
    
    print(f"\n會話資訊:")
    for key, value in session_info.items():
        print(f"  {key}: {value}")
    
    # 執行分析
    print("\n🔍 步驟 3: 執行進站分析...")
    result = analyze_driver_fastest_pitstops(loader, session_info)
    
    if result:
        print(f"\n✅ 分析成功！找到 {len(result)} 個車手的進站記錄")
        print("\n前 3 名:")
        for i, item in enumerate(result[:3], 1):
            print(f"  {i}. {item['driver']} ({item['team']}): {item['fastest_time']:.1f}秒")
    else:
        print("\n❌ 分析失敗")
        
except Exception as e:
    print(f"\n❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
