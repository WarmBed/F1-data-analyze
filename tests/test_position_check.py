#!/usr/bin/env python3
"""
測試 _check_position_data_availability 方法
"""

import sys
sys.path.insert(0, '.')

import fastf1

# 模擬 data_loader
class MockDataLoader:
    def __init__(self):
        fastf1.Cache.enable_cache('f1_analysis_cache')
        self.session = fastf1.get_session(2018, 'Great Britain', 'FP3')
        self.session.load(telemetry=True, laps=True, weather=False)
        self.session_loaded = True

# 創建分析器
from CLI_modules.cli.analyzer.all_drivers_straight_line_speed import AllDriversStraightLineSpeedAnalysis

data_loader = MockDataLoader()
analyzer = AllDriversStraightLineSpeedAnalysis(
    data_loader,
    year=2018,
    race="Great Britain",
    session="FP3"
)

# 測試位置數據檢查
print("=" * 60)
print("測試 _check_position_data_availability()")
print("=" * 60)

try:
    result = analyzer._check_position_data_availability()
    print(f"\n結果: {result}")
    
    if result:
        print("\n✅ 位置數據檢查通過！")
    else:
        print("\n❌ 位置數據檢查失敗！")
        
except Exception as e:
    print(f"\n❌ 異常: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
