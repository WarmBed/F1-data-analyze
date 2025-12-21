"""
Live Timing 性能分析工具
使用 cProfile 生成詳細的性能報告

⚠️ 使用方式：
   方法 1 (推薦): 在 GUI 的 Python Debug Console 執行
   >>> exec(open('profile_live_timing.py').read())
   >>> start_profiling(30)  # 分析 30 秒
   
   方法 2: 從 GUI 選單執行
   Tools → Start Performance Profiling
"""

import cProfile
import pstats
import io
import sys
import time
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QTimer

# 全局 profiler
_profiler = None
_profiling_timer = None
_profiling_start_time = None


def start_profiling(duration_seconds=30):
    """
    開始性能分析
    
    ⚠️ 必須在 GUI 內部調用（Python Debug Console 或選單）
    
    Args:
        duration_seconds: 分析持續時間（秒）
    """
    global _profiler, _profiling_timer, _profiling_start_time
    
    print("=" * 80)
    print("Live Timing 性能分析工具")
    print("=" * 80)
    print(f"分析時長: {duration_seconds} 秒")
    
    # 檢查 GUI 是否運行
    app = QApplication.instance()
    if not app:
        print("❌ 錯誤：必須在 GUI 內部運行此腳本")
        print("\n使用方式：")
        print("1. 啟動 GUI: python f1t_gui_main.py")
        print("2. 在 Python Debug Console 執行:")
        print("   >>> exec(open('profile_live_timing.py').read())")
        print("   >>> start_profiling(30)")
        return
    
    # 導入 DataManager
    try:
        from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
    except ImportError as e:
        print(f"❌ 無法導入 DataManager: {e}")
        return
    
    # 獲取 DataManager 實例
    mgr = LiveTimingDataManager._instance
    if not mgr:
        print("❌ DataManager 實例不存在，請先載入賽事")
        return
    
    if not mgr._race_info:
        print("❌ 尚未載入賽事")
        return
    
    print(f"\n✅ 找到賽事: {mgr._race_info.get('year')} {mgr._race_info.get('race')} {mgr._race_info.get('session')}")
    print(f"✅ 快照數: {len(mgr._snapshots) if mgr._snapshots else 0}")
    print(f"✅ 播放狀態: {mgr._playback_state}")
    
    # 確保正在播放
    if mgr._playback_state != "playing":
        print("\n⚠️  賽事未在播放，開始播放...")
        mgr.play()
        time.sleep(0.5)
    
    print(f"\n🔍 開始 {duration_seconds} 秒性能分析...")
    print("   (分析期間 GUI 可能會卡頓，這是正常現象)")
    print("   ⏳ 請稍候...")
    
    # 創建 profiler
    _profiler = cProfile.Profile()
    _profiler.enable()
    _profiling_start_time = time.time()
    
    # 設置定時器在指定時間後停止
    _profiling_timer = QTimer()
    _profiling_timer.setSingleShot(True)
    _profiling_timer.timeout.connect(lambda: _stop_profiling(duration_seconds))
    _profiling_timer.start(duration_seconds * 1000)
    
    print(f"✅ 分析已開始！將在 {duration_seconds} 秒後自動停止...")


def _stop_profiling(duration_seconds):
    """停止分析並生成報告"""
    global _profiler, _profiling_timer, _profiling_start_time
    
    if not _profiler:
        print("❌ 沒有正在運行的分析")
        return
    
    print("\n⏹️  停止分析...")
    _profiler.disable()
    
    actual_duration = time.time() - _profiling_start_time
    print(f"✅ 分析完成！實際時長: {actual_duration:.1f} 秒")
    
    # 生成報告
    _generate_reports(_profiler, duration_seconds)
    
    # 清理
    _profiler = None
    _profiling_timer = None
    _profiling_start_time = None


def _generate_reports(profiler, duration_seconds):
    """生成分析報告"""
    
    # 創建輸出目錄
    output_dir = Path("reports/performance")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(time.time())
    
    # 1. 保存 .prof 文件（用於 snakeviz）
    prof_file = output_dir / f"live_timing_{timestamp}.prof"
    profiler.dump_stats(str(prof_file))
    print(f"\n📊 已保存 .prof 文件: {prof_file}")
    
    # 2. 生成文字報告
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    
    # 按累積時間排序
    ps.sort_stats('cumulative')
    ps.print_stats(50)
    
    report_text = s.getvalue()
    
    # 保存文字報告
    txt_file = output_dir / f"live_timing_{timestamp}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write(f"Live Timing 性能分析報告\n")
        f.write(f"分析時長: {duration_seconds} 秒\n")
        f.write("=" * 100 + "\n\n")
        f.write(report_text)
        
        # 添加按內部時間排序的報告
        s2 = io.StringIO()
        ps2 = pstats.Stats(profiler, stream=s2)
        ps2.sort_stats('tottime')
        ps2.print_stats(50)
        
        f.write("\n\n" + "=" * 100 + "\n")
        f.write("按內部時間排序 (tottime)\n")
        f.write("=" * 100 + "\n\n")
        f.write(s2.getvalue())
    
    print(f"📄 已保存文字報告: {txt_file}")
    
    # 3. 提取模組相關的統計
    print("\n" + "=" * 80)
    print("🔍 Live Timing 模組性能統計 (前 30 名):")
    print("=" * 80)
    
    # 過濾模組相關的函數
    module_stats = []
    for func, (cc, nc, tt, ct, callers) in ps.stats.items():
        filename, line, func_name = func
        
        # 只關注 live_timing 相關
        if 'live_timing' in filename.lower() or '_on_snapshot_updated' in func_name or '_on_playback_tick' in func_name:
            module_stats.append({
                'file': Path(filename).name,
                'func': func_name,
                'ncalls': nc,
                'tottime': tt,
                'cumtime': ct,
                'percall_tot': tt / nc if nc > 0 else 0,
                'percall_cum': ct / nc if nc > 0 else 0
            })
    
    # 按累積時間排序
    module_stats.sort(key=lambda x: x['cumtime'], reverse=True)
    
    # 顯示前 30 名
    print(f"\n{'函數':<50} {'調用次數':<10} {'總時間(s)':<12} {'累積(s)':<12} {'平均(ms)':<10}")
    print("-" * 104)
    
    for stat in module_stats[:30]:
        func_display = f"{stat['file']}::{stat['func']}"
        if len(func_display) > 48:
            func_display = "..." + func_display[-45:]
        
        avg_ms = stat['percall_cum'] * 1000
        status = "🔴" if avg_ms > 50 else ("🟡" if avg_ms > 20 else "✅")
        
        print(f"{func_display:<50} {stat['ncalls']:<10} {stat['tottime']:<12.4f} {stat['cumtime']:<12.4f} {avg_ms:<9.2f} {status}")
    
    # 4. 啟動 snakeviz
    print("\n" + "=" * 80)
    print("🌐 啟動 snakeviz 可視化...")
    print("=" * 80)
    
    try:
        import subprocess
        
        print(f"\n執行命令: snakeviz {prof_file}")
        print("\n⚠️  snakeviz 會開啟瀏覽器視窗")
        print("   按 Ctrl+C 可停止服務器（在啟動 snakeviz 的終端）")
        
        # 非阻塞方式啟動 snakeviz
        subprocess.Popen(["snakeviz", str(prof_file)])
        
        print("\n✅ snakeviz 已在背景啟動")
        
    except FileNotFoundError:
        print("\n⚠️  snakeviz 未安裝")
        print("安裝命令: pip install snakeviz")
        print(f"\n手動啟動: snakeviz {prof_file}")
    
    print("\n✅ 分析完成！")
    print(f"📊 .prof 文件: {prof_file}")
    print(f"📄 文字報告: {txt_file}")
    print(f"\n💡 提示: 在 snakeviz 中查找以下函數:")
    print("   - _on_snapshot_updated (各模組)")
    print("   - _on_playback_tick (主循環)")
    print("   - _update_* (數據更新)")
    print("   - draw_* / render_* (繪圖)")


if __name__ == "__main__":
    print("=" * 80)
    print("Live Timing 性能分析工具")
    print("=" * 80)
    print("\n⚠️  此腳本必須在 GUI 內部運行")
    print("\n正確使用方式:")
    print("\n步驟 1: 啟動 GUI")
    print("  python f1t_gui_main.py")
    print("\n步驟 2: 載入賽事並開始播放")
    print("  - 開啟至少 5+ 個 Live Timing 模組")
    print("  - 點擊播放按鈕")
    print("\n步驟 3: 在 Python Debug Console 執行")
    print("  >>> exec(open('profile_live_timing.py').read())")
    print("  >>> start_profiling(30)  # 分析 30 秒")
    print("\n或者:")
    print("  >>> start_profiling(60)  # 分析 60 秒（更準確）")
    print("\n" + "=" * 80)


