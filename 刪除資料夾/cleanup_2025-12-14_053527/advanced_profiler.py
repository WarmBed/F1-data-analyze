"""
Live Timing 深度性能分析工具
==============================

專門分析 Live Timing 播放時的性能瓶頸

使用方式：
    python advanced_profiler.py

會自動：
1. 啟動 GUI（不顯示主視窗）
2. 載入 Abu Dhabi 2025 Race
3. 跳到 Lap 5
4. 播放 120 秒並進行性能分析
5. 生成詳細報告和視覺化

Author: F1T Team
Date: 2025-12-10
"""

import sys
import cProfile
import pstats
import time
from io import StringIO
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def profile_live_timing_playback():
    """性能分析主函數"""
    print("="*80)
    print("Live Timing 深度性能分析工具")
    print("="*80)
    print("\n目標：分析 Abu Dhabi 2025 播放 120 秒的性能瓶頸")
    print("="*80)
    
    # 創建 QApplication（不顯示主視窗）
    print("\n[1/6] 正在初始化 Qt 應用...")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 不要在關閉視窗時退出
    
    # 初始化 DataManager
    print("[2/6] 正在初始化 DataManager...")
    from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
    
    mgr = LiveTimingDataManager.instance()
    print("     ✅ DataManager 初始化完成")
    
    # 載入賽事
    print("\n[3/6] 正在載入賽事數據...")
    print("     賽事: 2025 Abu Dhabi Race")
    
    def progress_callback(percent, message):
        """載入進度回調"""
        if percent % 20 == 0:  # 每 20% 顯示一次
            print(f"     進度: {percent}% - {message}")
    
    # 嘗試載入 Abu Dhabi 2025
    success = mgr.load_race(
        year=2025,
        race="Abu Dhabi",
        session="Race",
        source_type="local",
        progress_callback=progress_callback
    )
    
    if not success:
        print("     ❌ 載入失敗！")
        print("\n💡 請確認:")
        print("   1. 是否有 Abu Dhabi 2025 的緩存數據？")
        print("   2. 可用的賽事列表:")
        
        # 嘗試列出可用賽事
        try:
            from pathlib import Path
            cache_dir = Path("Live_timing_test/pkl_cache")
            if cache_dir.exists():
                pkl_files = list(cache_dir.glob("*.pkl"))
                if pkl_files:
                    print("\n   可用的 PKL 緩存:")
                    for f in pkl_files[:10]:
                        print(f"     - {f.name}")
                else:
                    print("   ❌ 沒有找到 PKL 緩存檔案")
        except Exception as e:
            print(f"   ❌ 無法列出緩存: {e}")
        
        return 1
    
    print(f"     ✅ 賽事載入完成: {len(mgr._snapshots)} 個快照")
    
    # 跳到 Lap 5
    print("\n[4/6] 正在跳到 Lap 5...")
    target_lap = 5
    found = False
    
    for idx, snap in enumerate(mgr._snapshots):
        drivers = snap.get('drivers', {})
        if drivers:
            max_lap = max((d.get('lap', 0) for d in drivers.values()), default=0)
            if max_lap >= target_lap:
                mgr._current_index = idx
                found = True
                print(f"     ✅ 已跳到 Lap {max_lap} (Index: {idx})")
                break
    
    if not found:
        print(f"     ⚠️  無法跳到 Lap {target_lap}，從頭開始")
        mgr._current_index = 0
    
    # 開始性能分析
    print("\n[5/6] 開始性能分析...")
    print("     📊 將播放 120 秒並記錄所有函數調用")
    print("     ⏱️  請稍候...")
    
    profiler = cProfile.Profile()
    
    # 記錄開始時間
    start_time = time.time()
    analysis_duration = 120  # 120 秒
    
    # 開始播放並分析
    mgr.play()
    profiler.enable()
    
    # 定時更新進度
    elapsed_times = []
    
    def print_progress():
        elapsed = time.time() - start_time
        elapsed_times.append(elapsed)
        if len(elapsed_times) % 10 == 0:  # 每 10 次更新顯示一次
            print(f"     進度: {elapsed:.1f}s / {analysis_duration}s")
    
    progress_timer = QTimer()
    progress_timer.timeout.connect(print_progress)
    progress_timer.start(1000)  # 每秒更新
    
    # 在指定時間後停止
    def stop_profiling():
        profiler.disable()
        mgr.pause()
        progress_timer.stop()
        
        elapsed = time.time() - start_time
        print(f"     ✅ 分析完成: 實際執行 {elapsed:.2f} 秒")
        
        # 生成報告
        print("\n[6/6] 正在生成報告...")
        generate_reports(profiler, elapsed)
        
        # 退出
        QTimer.singleShot(1000, app.quit)
    
    QTimer.singleShot(analysis_duration * 1000, stop_profiling)
    
    # 運行事件循環
    return app.exec_()


def generate_reports(profiler, elapsed_time):
    """生成性能分析報告"""
    
    # 獲取統計數據
    ps = pstats.Stats(profiler)
    ps.strip_dirs()
    
    # === 報告 1: 終端輸出 ===
    print("\n" + "="*80)
    print("性能分析報告")
    print("="*80)
    
    print(f"\n總執行時間: {elapsed_time:.2f} 秒")
    print(f"總 CPU 時間: {ps.total_tt:.2f} 秒")
    print(f"CPU 使用率: {(ps.total_tt / elapsed_time * 100):.1f}%")
    
    print("\n" + "="*80)
    print("前 30 個最耗時的函數（按累計時間）")
    print("="*80)
    ps.sort_stats('cumulative')
    ps.print_stats(30)
    
    print("\n" + "="*80)
    print("前 30 個最耗時的函數（按單次調用時間）")
    print("="*80)
    ps.sort_stats('tottime')
    ps.print_stats(30)
    
    # === 報告 2: 保存詳細報告 ===
    output_file = "live_timing_performance_report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Live Timing 性能分析報告\n")
        f.write("="*80 + "\n\n")
        f.write(f"總執行時間: {elapsed_time:.2f} 秒\n")
        f.write(f"總 CPU 時間: {ps.total_tt:.2f} 秒\n")
        f.write(f"CPU 使用率: {(ps.total_tt / elapsed_time * 100):.1f}%\n\n")
        
        # 所有函數統計
        ps_detailed = pstats.Stats(profiler, stream=f)
        ps_detailed.strip_dirs()
        ps_detailed.sort_stats('cumulative')
        ps_detailed.print_stats()
    
    print(f"\n✅ 詳細報告已保存到: {output_file}")
    
    # === 報告 3: snakeviz 可視化 ===
    try:
        prof_file = 'live_timing_performance.prof'
        profiler.dump_stats(prof_file)
        print(f"✅ 性能數據已保存: {prof_file}")
        print("\n💡 使用 snakeviz 查看視覺化:")
        print(f"   pip install snakeviz")
        print(f"   snakeviz {prof_file}")
    except Exception as e:
        print(f"⚠️  無法保存 .prof 文件: {e}")
    
    # === 報告 4: 關鍵指標分析 ===
    print("\n" + "="*80)
    print("🔍 關鍵性能指標分析")
    print("="*80)
    
    # 查找 Live Timing 相關的慢函數
    keywords = [
        'live_timing',
        'prediction',
        'ranking_tower',
        'update_display',
        '_on_playback_tick',
        'snapshot_updated',
        'data_manager',
        'predict_overtake',
        'predict_close_combat',
        'draw_',
        'paint',
        'update',
    ]
    
    print("\n📌 Live Timing 相關函數（耗時 > 1% 總時間）:")
    
    func_analysis = []
    for func_name, stats_data in ps.stats.items():
        func_str = f"{func_name[0]}:{func_name[1]}:{func_name[2]}".lower()
        
        if any(kw in func_str for kw in keywords):
            cc, nc, tt, ct, callers = stats_data
            percent = (ct / ps.total_tt * 100) if ps.total_tt > 0 else 0
            
            if percent > 1.0:  # 只顯示占比 > 1% 的函數
                func_analysis.append({
                    'name': func_name[2],
                    'file': func_name[0],
                    'cumtime': ct,
                    'tottime': tt,
                    'ncalls': nc,
                    'percent': percent
                })
    
    # 按累計時間排序
    func_analysis.sort(key=lambda x: x['cumtime'], reverse=True)
    
    for i, func in enumerate(func_analysis[:20], 1):
        print(f"\n  {i}. {func['name']}")
        print(f"     檔案: {func['file']}")
        print(f"     累計時間: {func['cumtime']:.3f}s ({func['percent']:.1f}%)")
        print(f"     自身時間: {func['tottime']:.3f}s")
        print(f"     調用次數: {func['ncalls']}")
        if func['ncalls'] > 0:
            print(f"     平均耗時: {(func['cumtime']/func['ncalls']*1000):.2f}ms")
    
    # === 優化建議 ===
    print("\n" + "="*80)
    print("💡 優化建議")
    print("="*80)
    
    if func_analysis:
        top_func = func_analysis[0]
        print(f"\n1. 最大瓶頸: {top_func['name']}")
        print(f"   - 占用 {top_func['percent']:.1f}% 的總時間")
        print(f"   - 建議優先優化此函數")
        
        if top_func['ncalls'] > 1000:
            print(f"   - 調用次數過多 ({top_func['ncalls']} 次)")
            print(f"   - 考慮增加緩存或減少調用頻率")
        
        avg_time = (top_func['cumtime'] / top_func['ncalls'] * 1000) if top_func['ncalls'] > 0 else 0
        if avg_time > 10:
            print(f"   - 單次調用耗時過長 ({avg_time:.2f}ms)")
            print(f"   - 考慮優化算法或移至背景執行緒")
    
    # 檢查 GUI 更新頻率
    playback_tick_funcs = [f for f in func_analysis if 'playback_tick' in f['name'].lower()]
    if playback_tick_funcs:
        tick_func = playback_tick_funcs[0]
        fps = tick_func['ncalls'] / elapsed_time
        print(f"\n2. GUI 更新頻率: {fps:.1f} FPS")
        if fps > 25:
            print(f"   - 更新頻率較高，可考慮降低到 20 FPS")
        if fps < 15:
            print(f"   - ⚠️  更新頻率過低，可能有阻塞")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    sys.exit(profile_live_timing_playback())
