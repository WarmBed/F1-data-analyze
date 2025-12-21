#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

# 確保路徑正確
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from CLI_modules.cli.prediction.overtake_prediction.data_collector import run_f81_data_collection

print("=" * 70)
print("F81: 收集 2023-2024 年訓練數據")
print("=" * 70)

try:
    result = run_f81_data_collection(
        years=[2023, 2024], 
        split_by_year=True, 
        validation_year=2025,
        verbose=True
    )
    
    print("\n" + "=" * 70)
    print("收集完成")
    print("=" * 70)
    print(f"處理賽事: {result.get('races_processed', 0)}")
    print(f"超車事件: {result.get('total_overtakes', 0)}")
    print(f"訓練樣本: {result.get('total_samples', 0)}")
    if 'positive_ratio' in result:
        print(f"正樣本比例: {result['positive_ratio']:.2%}")
        
except Exception as e:
    print(f"\n[錯誤] {e}")
    import traceback
    traceback.print_exc()

