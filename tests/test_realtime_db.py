"""
即時資料庫測試工具
===================

測試 RealtimeDatabase 和 DatabaseReader 的功能。

使用方式:
1. 先啟動 GUI 並連接 Live Timing
2. 執行此腳本查看資料庫內容

Author: F1T Team
Date: 2025-12-07
"""

import sys
import os
import time

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.gui.live_timing.core.realtime_database import get_realtime_db


def main():
    """主程式"""
    print("=" * 60)
    print("即時資料庫測試工具")
    print("=" * 60)
    
    db = get_realtime_db()
    db.connect()
    
    # 讀取圈數
    lap_count = db.get_lap_count()
    print(f"\n圈數: {lap_count['current_lap']}/{lap_count['total_laps']}")
    
    # 讀取所有車手
    drivers = db.get_all_drivers()
    print(f"\n車手數量: {len(drivers)}")
    
    if drivers:
        print("\n車手列表 (依排名):")
        print("-" * 80)
        print(f"{'Pos':>3} {'TLA':<4} {'Gap':>10} {'Interval':>10} {'Last Lap':>12} {'Tyre':>6} {'Age':>3} {'Pit':>3}")
        print("-" * 80)
        
        # 排序
        sorted_drivers = sorted(drivers.values(), key=lambda x: x.get('position', 99))
        
        for d in sorted_drivers[:20]:  # 只顯示前 20
            pos = d.get('position', 'N/A')
            tla = d.get('tla', '???')
            gap = d.get('gap_to_leader_raw', '') or d.get('gap_to_leader', '')
            interval = d.get('interval', '')
            last_lap = d.get('last_lap_time', '')
            compound = d.get('compound', 'UNK')[:1]  # 只取首字母
            age = d.get('tyre_age', 0)
            pit = d.get('pit_count', 0)
            
            print(f"{pos:>3} {tla:<4} {str(gap):>10} {str(interval):>10} {str(last_lap):>12} {compound:>6} {age:>3} {pit:>3}")
    
    # 獲取完整快照
    snapshot = db.get_snapshot()
    print(f"\n快照內容:")
    print(f"  - current_lap: {snapshot.get('current_lap')}")
    print(f"  - total_laps: {snapshot.get('total_laps')}")
    print(f"  - track_status: {snapshot.get('track_status')}")
    print(f"  - drivers count: {len(snapshot.get('drivers', {}))}")
    
    # 查看一個車手的詳細數據
    if drivers:
        sample_num = next(iter(drivers.keys()))
        sample = drivers[sample_num]
        print(f"\n範例車手 ({sample_num}) 詳細數據:")
        for key, value in sample.items():
            if key != 'stints':
                print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
