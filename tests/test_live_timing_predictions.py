"""
完整測試：Live Timing 播放 + 背景預測執行緒
"""
import sys
import time
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 啟用調試日誌
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

# 修復 Windows console 編碼問題
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from modules.gui.live_timing.core.data_manager import LiveTimingDataManager

def main():
    """主測試函數"""
    app = QApplication(sys.argv)
    
    print("="*70)
    print("Live Timing 播放 + 背景預測執行緒測試")
    print("="*70)
    
    # 初始化管理器
    mgr = LiveTimingDataManager.instance()
    print(f"\n✅ DataManager initialized")
    print(f"   - Prediction worker: {mgr._prediction_worker is not None}")
    print(f"   - OT predictor: {mgr._overtake_predictor is not None}")
    print(f"   - CC predictor: {mgr._close_combat_predictor is not None}")
    
    # 載入賽事
    print(f"\n⏳ Loading race data...")
    success = mgr.load_race(2024, "Japan", "R", "local")
    
    if not success or not mgr._snapshots:
        print("❌ Failed to load race data")
        print("💡 Please ensure you have Live Timing cache data")
        return 1
    
    print(f"✅ Race loaded: {len(mgr._snapshots)} snapshots")
    
    # 跳到 Lap 5 附近
    target_lap = 5
    target_index = None
    for idx, snap in enumerate(mgr._snapshots):
        drivers = snap.get('drivers', {})
        if drivers:
            max_lap = max((d.get('lap', 0) for d in drivers.values()), default=0)
            if max_lap >= target_lap:
                target_index = idx
                break
    
    if target_index is None:
        print(f"❌ Could not find Lap {target_lap}")
        return 1
    
    print(f"\n📍 Jumping to index {target_index} (Lap {target_lap})")
    mgr._current_index = target_index - 1  # -1 因為 play() 會增加
    
    # 訂閱更新信號
    update_count = [0]
    prediction_updates = [0]
    last_snapshot = [None]
    
    def on_snapshot_updated(snapshot):
        update_count[0] += 1
        last_snapshot[0] = snapshot
        
        drivers = snapshot.get('drivers', {})
        nonzero_ot = sum(1 for d in drivers.values() if d.get('overtake_probability', 0) > 0)
        nonzero_cc = sum(1 for d in drivers.values() if d.get('close_combat_probability', 0) > 0)
        
        if nonzero_ot > 0 or nonzero_cc > 0:
            prediction_updates[0] += 1
        
        if update_count[0] % 20 == 0:  # 每 20 次更新報告一次
            print(f"   Update #{update_count[0]}: OT>0={nonzero_ot}, CC>0={nonzero_cc}")
    
    mgr.snapshot_updated.connect(on_snapshot_updated)
    
    # 開始播放
    print(f"\n🎬 Starting playback (10 seconds)...")
    mgr.play()
    
    # 使用 QTimer 在 10 秒後停止
    def stop_test():
        mgr.pause()
        print(f"\n⏸️  Playback paused")
        
        # 檢查最後一個快照
        if last_snapshot[0]:
            snapshot = last_snapshot[0]
            drivers = snapshot.get('drivers', {})
            
            print(f"\n📊 Final snapshot analysis:")
            print(f"   Total drivers: {len(drivers)}")
            
            # 顯示前 5 名的預測
            sorted_drivers = sorted(
                drivers.items(),
                key=lambda x: x[1].get('position', 99)
            )[:5]
            
            print(f"\n   Top 5 predictions:")
            for driver_num, data in sorted_drivers:
                pos = data.get('position', '?')
                ot = data.get('overtake_probability', 0)
                cc = data.get('close_combat_probability', 0)
                gap = data.get('gap_to_ahead', 'N/A')
                print(f"     P{pos} {driver_num}: OT={ot}%, CC={cc}%, gap={gap}")
            
            # 統計結果
            nonzero_ot = sum(1 for d in drivers.values() if d.get('overtake_probability', 0) > 0)
            nonzero_cc = sum(1 for d in drivers.values() if d.get('close_combat_probability', 0) > 0)
            
            print(f"\n" + "="*70)
            print(f"測試結果:")
            print(f"  - 總更新次數: {update_count[0]}")
            print(f"  - 有預測更新: {prediction_updates[0]}")
            print(f"  - OT% > 0: {nonzero_ot} 車手")
            print(f"  - CC% > 0: {nonzero_cc} 車手")
            
            if nonzero_ot > 0 or nonzero_cc > 0:
                print(f"\n✅ TEST PASSED: Predictions are working!")
            else:
                print(f"\n❌ TEST FAILED: No predictions generated")
            print("="*70)
        
        # 清理
        mgr.unload_race()
        
        # 退出應用
        QTimer.singleShot(1000, app.quit)
    
    QTimer.singleShot(10000, stop_test)
    
    # 運行事件循環
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
