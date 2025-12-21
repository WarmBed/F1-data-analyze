#!/usr/bin/env python3
"""測試 time_difference 生成"""

import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from CLI_modules.cli.core.data_loader import F1DataLoader
from CLI_modules.cli.analyzer.two_driver_telemetry_comparison_fixed import TwoDriverTelemetryComparison

def test_time_diff():
    """測試時間差分析功能"""
    print("=" * 80)
    print("測試 Time Difference 生成")
    print("=" * 80)
    
    # 1. 初始化數據載入器
    print("\n[1] 初始化數據載入器...")
    data_loader = F1DataLoader(year=2025, race_name='Australia', session_type='R')
    
    # 2. 載入賽事數據
    print("[2] 載入賽事數據...")
    race_data = data_loader.load_session_data()
    if not race_data:
        print("❌ 賽事數據載入失敗")
        return False
    
    # 3. 創建分析器
    print("[3] 創建遙測比較分析器...")
    analyzer = TwoDriverTelemetryComparison(
        data_loader=data_loader,
        year=2025,
        race='Australia',
        session='R'
    )
    
    # 4. 執行分析
    print("[4] 執行雙車手比較分析...")
    result = analyzer.analyze(
        driver='VER',
        driver2='LEC',
        lap_number=43,  # 使用實際圈數而非 99
        lap_number1=43,
        lap_number2=43,
        disable_charts=True
    )
    
    # 5. 檢查結果
    print("\n[5] 檢查分析結果...")
    if not result:
        print("❌ 分析失敗，無結果")
        return False
    
    print(f"✅ 分析結果類型: {type(result)}")
    print(f"✅ 分析結果鍵: {list(result.keys())}")
    
    # 6. 檢查 time_difference 區塊
    print("\n[6] 檢查 time_difference 區塊...")
    if 'time_difference' in result:
        time_diff = result['time_difference']
        print(f"✅ time_difference 存在")
        print(f"   鍵: {list(time_diff.keys())}")
        
        if 'reference_time' in time_diff:
            ref_time = time_diff['reference_time']
            print(f"   reference_time: {len(ref_time)} 點")
            print(f"   時間範圍: {ref_time[0]:.2f}s - {ref_time[-1]:.2f}s")
        
        if 'cumulative_time_difference' in time_diff:
            time_diff_vals = time_diff['cumulative_time_difference']
            print(f"   cumulative_time_difference: {len(time_diff_vals)} 點")
            import statistics
            print(f"   時間差範圍: {min(time_diff_vals):.2f}s - {max(time_diff_vals):.2f}s")
            print(f"   平均時間差: {statistics.mean(time_diff_vals):.2f}s")
        
        return True
    else:
        print("❌ time_difference 不存在於結果中")
        print(f"   可用的鍵: {list(result.keys())}")
        return False

if __name__ == '__main__':
    success = test_time_diff()
    sys.exit(0 if success else 1)
