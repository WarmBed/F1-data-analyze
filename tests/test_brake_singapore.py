#!/usr/bin/env python3
"""測試 Singapore 2025 R 的煞車分析"""

import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from CLI_modules.cli.data_loader.telemetry_data_loader import TelemetryDataLoader
from CLI_modules.cli.analyzer.brake_performance_analyzer import BrakePerformanceAnalyzer

print("="*80)
print("測試 Singapore 2025 R - Brake Performance Analysis")
print("="*80)

try:
    # 初始化 data loader
    print("\n[步驟 1] 初始化 TelemetryDataLoader...")
    loader = TelemetryDataLoader(year=2025, race_name="Singapore", session_type="R")
    
    print("[步驟 2] 載入 session...")
    if not loader.load_session():
        print("❌ 載入 session 失敗")
        sys.exit(1)
    
    print("✅ Session 載入成功")
    
    # 初始化分析器
    print("\n[步驟 3] 初始化 BrakePerformanceAnalyzer...")
    analyzer = BrakePerformanceAnalyzer(loader)
    
    # 執行分析
    print("\n[步驟 4] 執行煞車分析...")
    result = analyzer.run()
    
    print("\n" + "="*80)
    print("分析結果:")
    print("="*80)
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    
    if result.get('success'):
        data = result.get('data', {})
        driver_brakes = data.get('driver_brakes', [])
        print(f"\n找到 {len(driver_brakes)} 位車手的煞車數據")
        
        if driver_brakes:
            print("\n前 3 名:")
            for i, record in enumerate(driver_brakes[:3], 1):
                print(f"  {i}. {record['driver']} - {record['max_deceleration_ms2']} m/s² ({record['max_deceleration_g']} G)")
    else:
        print(f"\n❌ 分析失敗")
        print(f"錯誤: {result.get('message')}")
        
except Exception as e:
    print(f"\n❌ 發生異常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("測試完成")
print("="*80)
