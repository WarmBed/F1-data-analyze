#!/usr/bin/env python3
"""
Live Timing 
 XGBoost 

:
    python tools/diagnose_playback_lag.py --year 2025 --race Qatar
"""

import sys
import cProfile
import pstats
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def profile_prediction_overhead():
    """"""
    print("=" * 70)
    print("Live Timing ")
    print("=" * 70)
    
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
    
    # 
    print(" ...")
    data_manager = LiveTimingDataManager()
    success = data_manager.load_race(2025, "Qatar", session="Race")
    
    if not success:
        print(" ")
        return
    
    print(f"  {len(data_manager._snapshots):,} ")
    
    # 
    print("\n" + "=" * 70)
    print("")
    print("=" * 70)
    
    # 
    test_snapshot_idx = len(data_manager._snapshots) // 2
    test_snapshot = data_manager._snapshots[test_snapshot_idx].copy()
    
    print(f": #{test_snapshot_idx} / {len(data_manager._snapshots)}")
    print(f": {test_snapshot.get('race_time', 'N/A')}")
    print(f": {len(test_snapshot.get('drivers', {}))}")
    
    # 
    results = {}
    
    # 1. 
    print("\n1   (Win Probability)...")
    times = []
    for i in range(10):
        start = time.time()
        data_manager._update_win_probabilities(test_snapshot)
        elapsed = (time.time() - start) * 1000  # 
        times.append(elapsed)
    
    results['win_prob'] = {
        'avg': sum(times) / len(times),
        'min': min(times),
        'max': max(times),
        'times': times
    }
    print(f"   : {results['win_prob']['avg']:.2f} ms")
    print(f"   : {results['win_prob']['min']:.2f} - {results['win_prob']['max']:.2f} ms")
    
    # 2. 
    print("\n2   (Overtake Probability)...")
    times = []
    for i in range(10):
        start = time.time()
        data_manager._update_overtake_predictions(test_snapshot)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    results['overtake'] = {
        'avg': sum(times) / len(times),
        'min': min(times),
        'max': max(times),
        'times': times
    }
    print(f"   : {results['overtake']['avg']:.2f} ms")
    print(f"   : {results['overtake']['min']:.2f} - {results['overtake']['max']:.2f} ms")
    
    # 3. 
    print("\n3   (Close Combat)...")
    times = []
    for i in range(10):
        start = time.time()
        data_manager._update_close_combat_predictions(test_snapshot)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    results['close_combat'] = {
        'avg': sum(times) / len(times),
        'min': min(times),
        'max': max(times),
        'times': times
    }
    print(f"   : {results['close_combat']['avg']:.2f} ms")
    print(f"   : {results['close_combat']['min']:.2f} - {results['close_combat']['max']:.2f} ms")
    
    # 4. 
    print("\n4   ()...")
    times = []
    for i in range(10):
        snapshot_copy = test_snapshot.copy()
        start = time.time()
        data_manager._update_win_probabilities(snapshot_copy)
        data_manager._update_overtake_predictions(snapshot_copy)
        data_manager._update_close_combat_predictions(snapshot_copy)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    results['total'] = {
        'avg': sum(times) / len(times),
        'min': min(times),
        'max': max(times),
        'times': times
    }
    print(f"   : {results['total']['avg']:.2f} ms")
    print(f"   : {results['total']['min']:.2f} - {results['total']['max']:.2f} ms")
    
    # 
    print("\n" + "=" * 70)
    print(" ")
    print("=" * 70)
    
    total_avg = results['total']['avg']
    target_fps = 20  #  20 FPS50ms/
    target_ms = 1000 / target_fps
    
    print(f"\n  : {total_avg:.2f} ms")
    print(f"  (20 FPS): {target_ms:.2f} ms")
    print(f"  FPS: {1000/total_avg:.1f} /")
    
    if total_avg > target_ms:
        overhead = total_avg - target_ms
        print(f"\n  ****:  {overhead:.2f} ms ({overhead/target_ms*100:.1f}%)")
        print(f"    ")
    else:
        headroom = target_ms - total_avg
        print(f"\n :  {headroom:.2f} ms  ({headroom/target_ms*100:.1f}%)")
    
    print(f"\n :")
    print(f"   : {results['win_prob']['avg']:.2f} ms ({results['win_prob']['avg']/total_avg*100:.1f}%)")
    print(f"   : {results['overtake']['avg']:.2f} ms ({results['overtake']['avg']/total_avg*100:.1f}%)")
    print(f"   : {results['close_combat']['avg']:.2f} ms ({results['close_combat']['avg']/total_avg*100:.1f}%)")
    
    # 
    print("\n" + "=" * 70)
    print("  ( 5 )")
    print("=" * 70)
    
    update_count = 0
    total_time = 0
    lag_count = 0
    
    #  100  5 
    start_idx = test_snapshot_idx
    end_idx = min(start_idx + 100, len(data_manager._snapshots))
    
    for idx in range(start_idx, end_idx):
        snapshot = data_manager._snapshots[idx].copy()
        
        start = time.time()
        data_manager._update_win_probabilities(snapshot)
        data_manager._update_overtake_predictions(snapshot)
        data_manager._update_close_combat_predictions(snapshot)
        elapsed = (time.time() - start) * 1000
        
        total_time += elapsed
        update_count += 1
        
        if elapsed > target_ms:
            lag_count += 1
    
    avg_update_time = total_time / update_count
    lag_percentage = (lag_count / update_count) * 100
    
    print(f"\n: {update_count}")
    print(f": {avg_update_time:.2f} ms")
    print(f": {lag_count} / {update_count} ({lag_percentage:.1f}%)")
    print(f" FPS: {1000/avg_update_time:.1f} /")
    
    if lag_percentage > 20:
        print(f"\n ****: {lag_percentage:.1f}%  {target_ms:.0f}ms")
        print("   ")
    elif lag_percentage > 5:
        print(f"\n  ****: {lag_percentage:.1f}%  {target_ms:.0f}ms")
        print("   ")
    else:
        print(f"\n ****:  {lag_percentage:.1f}% ")
    
    # 
    print("\n" + "=" * 70)
    print(" ")
    print("=" * 70)
    
    print("\n1  ****  ")
    print("   -  XGBoost  QThread ")
    print("   -  UI")
    print("   - : 100% ()")
    
    print("\n2  ****")
    print("   -  0.5 ")
    print(f"   - : 50-70% ( {100 - 1000/(avg_update_time*2):.0f}% )")
    
    print("\n3  ****")
    print("   -  < 3 ")
    print("   - ")
    print("   - : 30-50%")
    
    print("\n4  ****")
    print("   - ")
    print("   - : 20-30%")
    
    print("\n5  ****")
    print("   -  XGBoost ")
    print("   - ")
    print("   - : 10-20%")
    
    print("\n" + "=" * 70)
    print(" ")
    print("=" * 70)


if __name__ == "__main__":
    profile_prediction_overhead()

