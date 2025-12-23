#!/usr/bin/env python3
"""測試 FPQDataCollector 收集 Saudi Arabia 2025 數據"""

import sys
sys.path.insert(0, '.')

from CLI_modules.cli.prediction.fp_q_data_collector import FPQDataCollector

collector = FPQDataCollector(verbose=True)

print("=" * 70)
print("測試 Saudi Arabia 2025 FP+Q 數據收集（衝刺賽週末）")
print("=" * 70)

result = collector.collect_race_data(
    year=2025,
    race="Saudi Arabia",
    include_fp1=True,
    include_fp2=True,
    include_fp3=True  # 應該會回退到衝刺賽
)

if result:
    practice_sessions = result.get('practice_sessions', {})
    print(f"\n✅ 收集成功！")
    print(f"練習賽會話: {list(practice_sessions.keys())}")
    
    fp3 = practice_sessions.get('FP3', {})
    if fp3:
        drivers = fp3.get('driver_data', {})
        print(f"FP3 車手數: {len(drivers)}")
else:
    print("\n❌ 收集失敗")
