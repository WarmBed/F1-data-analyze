"""
測試背景預測執行緒是否正常工作
"""
import sys
import time
from PyQt5.QtCore import QCoreApplication
from modules.gui.live_timing.core.data_manager import LiveTimingDataManager

def test_predictions():
    """測試預測功能"""
    app = QCoreApplication(sys.argv)
    
    # 初始化管理器
    mgr = LiveTimingDataManager.instance()
    print(f"✅ Prediction worker active: {mgr._prediction_worker is not None}")
    print(f"✅ OT predictor loaded: {mgr._overtake_predictor is not None}")
    print(f"✅ CC predictor loaded: {mgr._close_combat_predictor is not None}")
    
    # 嘗試載入最近的賽事數據
    print("\n⏳ Loading race data...")
    
    # 使用 PKL 快取（最快）
    cache_dir = "f1_analysis_cache/livetiming"
    import os
    pkl_files = []
    if os.path.exists(cache_dir):
        pkl_files = [f for f in os.listdir(cache_dir) if f.endswith('.pkl')]
    
    if pkl_files:
        print(f"📦 Found {len(pkl_files)} PKL cache files")
        # 使用第一個 PKL
        pkl_path = os.path.join(cache_dir, pkl_files[0])
        print(f"📂 Loading: {pkl_files[0]}")
        
        # 從檔名解析賽事資訊
        # 格式: livetiming_2024_Japan_R_XXXXXXX.pkl
        parts = pkl_files[0].replace('.pkl', '').split('_')
        if len(parts) >= 4:
            year = int(parts[1])
            race = parts[2]
            session = parts[3]
            
            result = mgr.load_race(year, race, session, 'local')
            print(f"✅ Load result: {result}")
            
            if result and mgr._snapshots:
                print(f"✅ Total snapshots: {len(mgr._snapshots)}")
                
                # 模擬播放：跳到中間
                mid_index = len(mgr._snapshots) // 2
                mgr._current_index = mid_index
                snapshot = mgr._snapshots[mid_index]
                
                print(f"\n📊 Testing snapshot at index {mid_index}")
                print(f"   Race time: {snapshot.get('race_time', 'N/A')}")
                
                # 手動調用預測更新（模擬播放）
                print("\n🔄 Calling _update_win_probabilities...")
                mgr._update_win_probabilities(snapshot)
                
                drivers = snapshot.get('drivers', {})
                print(f"\n👥 Total drivers: {len(drivers)}")
                
                # 檢查預測值（播放前）
                print("\n" + "="*60)
                print("BEFORE background prediction:")
                print("="*60)
                for i, (driver_num, data) in enumerate(sorted(drivers.items(), key=lambda x: x[1].get('position', 99))[:5]):
                    pos = data.get('position', '?')
                    ot = data.get('overtake_probability', 'N/A')
                    cc = data.get('close_combat_probability', 'N/A')
                    gap = data.get('gap_to_ahead', 'N/A')
                    gap_trend = data.get('gap_trend', 'N/A')
                    print(f"  P{pos} {driver_num}: OT={ot}%, CC={cc}%, gap={gap}, trend={gap_trend}")
                
                # 模擬播放：調用主執行緒的預測邏輯
                print("\n🚀 Triggering background prediction...")
                
                # 手動執行主執行緒邏輯
                if mgr._prediction_worker:
                    # 步驟 1：計算 gap_trend
                    current_lap = max((d.get('lap', 0) for d in drivers.values()), default=0)
                    
                    sorted_drivers = []
                    for driver_num, driver_data in drivers.items():
                        pos = driver_data.get('position', 99)
                        sorted_drivers.append((driver_num, driver_data, pos))
                    sorted_drivers.sort(key=lambda x: x[2])
                    
                    for i, (driver_num, driver_data, position) in enumerate(sorted_drivers):
                        if position == 1 or i == 0:
                            drivers[driver_num]['gap_trend'] = 0.0
                            drivers[driver_num]['overtake_probability'] = 0
                            drivers[driver_num]['close_combat_probability'] = 0
                            continue
                        
                        gap_str = driver_data.get('gap_to_ahead', '') or driver_data.get('gap_to_ahead_display', '')
                        gap_seconds = mgr._parse_gap_seconds(gap_str)
                        current_lap_num = driver_data.get('lap', 0)
                        gap_trend = mgr._update_gap_history_and_calc_lap_trend(
                            driver_num, gap_seconds, current_lap_num
                        )
                        drivers[driver_num]['gap_trend'] = gap_trend
                        
                        cache = mgr._prediction_cache.get(driver_num, {})
                        drivers[driver_num]['overtake_probability'] = cache.get('ot%', 0)
                        drivers[driver_num]['close_combat_probability'] = cache.get('cc%', 0)
                    
                    # 步驟 2：發送到背景執行緒
                    tyre_state = mgr.get_tyre_state()
                    total_laps = mgr._race_info.get('total_laps', 60) if mgr._race_info else 60
                    race_progress = current_lap / total_laps if total_laps > 0 else 0.5
                    
                    mgr._prediction_worker.queue_prediction(
                        snapshot=snapshot,
                        tyre_state=tyre_state,
                        race_progress=race_progress,
                        track_status_green=True
                    )
                    
                    print("⏳ Waiting for background prediction (2 seconds)...")
                    
                    # 等待背景執行緒完成
                    prediction_received = [False]
                    
                    def on_predictions_ready(results):
                        print(f"\n✅ Background prediction completed! Received {len(results)} results")
                        prediction_received[0] = True
                        
                        # 手動調用處理方法
                        mgr._on_predictions_ready(results)
                    
                    # 連接信號
                    mgr._prediction_worker.predictions_ready.connect(on_predictions_ready)
                    
                    # 處理事件循環
                    start_time = time.time()
                    while not prediction_received[0] and (time.time() - start_time < 3):
                        app.processEvents()
                        time.sleep(0.01)
                    
                    if prediction_received[0]:
                        print("\n" + "="*60)
                        print("AFTER background prediction:")
                        print("="*60)
                        for i, (driver_num, data) in enumerate(sorted(drivers.items(), key=lambda x: x[1].get('position', 99))[:5]):
                            pos = data.get('position', '?')
                            ot = data.get('overtake_probability', 'N/A')
                            cc = data.get('close_combat_probability', 'N/A')
                            gap = data.get('gap_to_ahead', 'N/A')
                            gap_trend = data.get('gap_trend', 'N/A')
                            print(f"  P{pos} {driver_num}: OT={ot}%, CC={cc}%, gap={gap}, trend={gap_trend}")
                        
                        # 檢查是否有非零值
                        has_nonzero_ot = any(d.get('overtake_probability', 0) > 0 for d in drivers.values())
                        has_nonzero_cc = any(d.get('close_combat_probability', 0) > 0 for d in drivers.values())
                        
                        print("\n" + "="*60)
                        if has_nonzero_ot or has_nonzero_cc:
                            print("✅ TEST PASSED: Predictions are working!")
                        else:
                            print("❌ TEST FAILED: All predictions are still 0")
                        print("="*60)
                    else:
                        print("\n❌ Timeout: Background prediction did not complete")
                
                # 清理
                mgr.unload_race()
            else:
                print("❌ Failed to load race data")
        else:
            print("❌ Invalid PKL filename format")
    else:
        print("❌ No PKL cache files found")
        print("💡 Please run Live Timing first to generate cache")

if __name__ == "__main__":
    test_predictions()
