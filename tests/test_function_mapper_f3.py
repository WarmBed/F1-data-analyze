#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接測試功能映射器的執行"""

import sys
import os

# 設置 UTF-8 編碼
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("[TEST] Function Mapper - Function 3")
print("=" * 80)

try:
    print("\n📡 導入功能映射器...")
    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
    from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
    
    print("✅ 導入成功")
    
    # 創建數據載入器
    print("\n📊 創建數據載入器...")
    data_loader = CompatibleF1DataLoader()
    
    # 載入數據
    print("\n📡 載入 2025 United States R 數據...")
    success = data_loader.load_race_data(2025, "United States", "R")
    
    if not success:
        print("❌ 數據載入失敗")
        sys.exit(1)
    
    print("✅ 數據載入成功")
    
    # 創建功能映射器
    print("\n🔧 創建功能映射器...")
    mapper = F1AnalysisFunctionMapper(
        data_loader=data_loader,
        driver="VER",
        driver2="LEC"
    )
    
    # 執行功能 3
    print("\n🚀 執行功能 3...")
    result = mapper._execute_driver_fastest_pitstop_ranking(show_detailed_output=True)
    
    if result and result.get("success"):
        print("\n✅ 功能 3 執行成功！")
        data = result.get("data", [])
        print(f"📊 找到 {len(data)} 個車手的進站記錄")
        
        if data:
            print("\n前 5 名:")
            for i, item in enumerate(data[:5], 1):
                print(f"  {i}. {item.get('driver')} ({item.get('team')}): {item.get('fastest_time', 0):.1f}秒")
    else:
        print("\n❌ 功能 3 執行失敗")
        print(f"結果: {result}")
        
except Exception as e:
    print(f"\n❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
