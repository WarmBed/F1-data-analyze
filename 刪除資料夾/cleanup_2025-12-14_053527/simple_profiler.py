"""
簡化版性能分析 - 使用 cProfile
====================================

使用 cProfile 分析 Live Timing 播放時的性能瓶頸

使用方式：
    python simple_profiler.py

會自動：
1. 啟動 GUI
2. 載入賽事
3. 播放 30 秒
4. 生成性能報告和視覺化

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

def profile_live_timing():
    """性能分析主函數"""
    print("="*60)
    print("Live Timing 性能分析工具")
    print("="*60)
    
    # 啟動 GUI
    print("\n⏳ 正在啟動 GUI...")
    app = QApplication(sys.argv)
    
    from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
    
    mgr = LiveTimingDataManager.instance()
    print("✅ DataManager 初始化完成")
    
    # 載入賽事
    print("\n⏳ 正在載入賽事數據...")
    success = mgr.load_race(2024, "Japan", "R", "local")
    
    if not success:
        print("❌ 載入失敗，請確保有緩存數據")
        return 1
    
    print(f"✅ 賽事載入完成: {len(mgr._snapshots)} 個快照")
    
    # 跳到 Lap 5
    print("\n⏳ 跳到 Lap 5...")
    for idx, snap in enumerate(mgr._snapshots):
        drivers = snap.get('drivers', {})
        if drivers:
            max_lap = max((d.get('lap', 0) for d in drivers.values()), default=0)
            if max_lap >= 5:
                mgr._current_index = idx
                break
    
    print(f"✅ 當前位置: Index {mgr._current_index}")
    
    # 開始性能分析
    print("\n🔬 開始性能分析...")
    print("📊 將播放 30 秒並記錄所有函數調用...")
    
    profiler = cProfile.Profile()
    
    # 開始播放並分析
    mgr.play()
    profiler.enable()
    
    # 使用 QTimer 在 30 秒後停止
    def stop_profiling():
        profiler.disable()
        mgr.pause()
        
        print("\n✅ 分析完成，正在生成報告...\n")
        
        # 生成報告
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.strip_dirs()
        ps.sort_stats('cumulative')
        
        print("="*60)
        print("前 30 個最耗時的函數（按累計時間）")
        print("="*60)
        ps.print_stats(30)
        
        print("\n" + "="*60)
        print("前 30 個最耗時的函數（按單次調用時間）")
        print("="*60)
        ps.sort_stats('tottime')
        ps.print_stats(30)
        
        # 保存詳細報告
        output_file = "performance_report.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            ps = pstats.Stats(profiler, stream=f)
            ps.strip_dirs()
            ps.sort_stats('cumulative')
            ps.print_stats()
        
        print(f"\n✅ 詳細報告已保存到: {output_file}")
        
        # 生成 snakeviz 可視化（如果已安裝）
        try:
            profiler.dump_stats('performance_profile.prof')
            print(f"✅ 性能數據已保存: performance_profile.prof")
            print("\n💡 使用 snakeviz 查看視覺化:")
            print("   pip install snakeviz")
            print("   snakeviz performance_profile.prof")
        except Exception as e:
            print(f"⚠️  無法保存 .prof 文件: {e}")
        
        # 關鍵指標分析
        print("\n" + "="*60)
        print("🔍 關鍵性能指標分析")
        print("="*60)
        
        # 查找 Live Timing 相關的慢函數
        ps = pstats.Stats(profiler)
        ps.strip_dirs()
        
        total_time = ps.total_tt
        print(f"\n總執行時間: {total_time:.2f} 秒")
        
        # 查找特定模組
        keywords = [
            'live_timing',
            'prediction',
            'ranking_tower',
            'update_display',
            '_on_playback_tick',
            'snapshot_updated'
        ]
        
        print("\n📌 Live Timing 相關函數:")
        for func_name, stats_data in ps.stats.items():
            func_str = f"{func_name[0]}:{func_name[1]}:{func_name[2]}"
            
            if any(kw in func_str.lower() for kw in keywords):
                cc, nc, tt, ct, callers = stats_data
                percent = (ct / total_time * 100) if total_time > 0 else 0
                
                if percent > 1.0:  # 只顯示占比 > 1% 的函數
                    print(f"  {func_name[2]}")
                    print(f"    累計時間: {ct:.3f}s ({percent:.1f}%)")
                    print(f"    調用次數: {nc}")
                    print(f"    平均耗時: {(ct/nc*1000):.2f}ms" if nc > 0 else "")
                    print()
        
        # 退出
        QTimer.singleShot(2000, app.quit)
    
    QTimer.singleShot(30000, stop_profiling)
    
    # 運行事件循環
    return app.exec_()


if __name__ == "__main__":
    sys.exit(profile_live_timing())
