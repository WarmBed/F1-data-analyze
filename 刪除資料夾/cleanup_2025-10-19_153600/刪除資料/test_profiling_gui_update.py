"""
Performance Profiling for update_all_lap_analysis
測試目標：找出 GUI 凍結 47 秒的真正原因
"""
import cProfile
import pstats
import io
import time
import sys
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

def profile_update_all_lap_analysis():
    """
    使用 cProfile 分析 update_all_lap_analysis() 的性能
    """
    from PyQt5.QtWidgets import QApplication
    from f1t_gui_main import StyleHMainWindow
    
    print("=" * 80)
    print("🔬 Performance Profiling: update_all_lap_analysis()")
    print("=" * 80)
    
    # 創建 QApplication
    app = QApplication(sys.argv)
    
    # 創建主視窗
    print("\n📦 創建主視窗...")
    main_window = StyleHMainWindow()
    main_window.show()
    
    # 設置基本參數
    print("\n⚙️ 設置測試參數...")
    main_window.year_combo.setCurrentText("2025")
    main_window.race_combo.setCurrentText("Japan")
    main_window.session_combo.setCurrentText("R")
    main_window.driver1_combo.setCurrentText("VER")
    main_window.driver2_combo.setCurrentText("LEC")
    
    QApplication.processEvents()
    
    # 創建多個測試視窗
    print("\n🏗️ 創建測試視窗...")
    window_types = [
        ('速度分析', 'open_speed_analysis'),
        ('油門分析', 'open_throttle_analysis'),
        ('煞車分析', 'open_brake_analysis'),
        ('檔位分析', 'open_gear_analysis'),
        ('RPM分析', 'open_rpm_analysis'),
    ]
    
    created_count = 0
    for type_name, method_name in window_types:
        try:
            if hasattr(main_window, method_name):
                method = getattr(main_window, method_name)
                method()
                created_count += 1
                print(f"  ✅ 已創建: {type_name}")
                QApplication.processEvents()
        except Exception as e:
            print(f"  ❌ 創建失敗 {type_name}: {e}")
    
    print(f"\n✅ 共創建 {created_count} 個視窗")
    print(f"📊 當前活動視窗數: {len(main_window.lap_analysis_windows)}")
    
    # 等待視窗完全創建
    time.sleep(2)
    QApplication.processEvents()
    
    # 開始 Profiling
    print("\n" + "=" * 80)
    print("🚀 開始性能分析...")
    print("=" * 80)
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 執行測試目標
    start_time = time.time()
    main_window.update_all_lap_analysis()
    elapsed = time.time() - start_time
    
    profiler.disable()
    
    print("\n" + "=" * 80)
    print(f"⏱️ 執行時間: {elapsed:.2f} 秒")
    print("=" * 80)
    
    # 生成報告
    print("\n📊 性能分析報告 (Top 30 耗時操作):\n")
    
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.strip_dirs()
    ps.sort_stats('cumulative')
    ps.print_stats(30)
    
    report = s.getvalue()
    print(report)
    
    # 保存詳細報告
    report_file = Path(__file__).parent / "profiling_report_update_all_lap.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Performance Profiling Report\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total execution time: {elapsed:.2f} seconds\n")
        f.write(f"Active windows: {len(main_window.lap_analysis_windows)}\n")
        f.write("=" * 80 + "\n\n")
        f.write(report)
    
    print(f"\n💾 詳細報告已保存: {report_file}")
    
    # 分析關鍵函數
    print("\n" + "=" * 80)
    print("🔍 關鍵函數分析:")
    print("=" * 80)
    
    ps.sort_stats('time')
    ps.print_stats('update_lap_parameters', 10)
    ps.print_stats('load_telemetry_data', 10)
    ps.print_stats('processEvents', 10)
    
    # 清理
    app.quit()
    
    return elapsed

def simple_timing_test():
    """
    簡單的時間測試（不使用 profiler）
    """
    from PyQt5.QtWidgets import QApplication
    from f1t_gui_main import StyleHMainWindow
    
    print("\n" + "=" * 80)
    print("⏱️ 簡單時間測試")
    print("=" * 80)
    
    app = QApplication(sys.argv)
    main_window = StyleHMainWindow()
    main_window.show()
    
    # 設置參數
    main_window.year_combo.setCurrentText("2025")
    main_window.race_combo.setCurrentText("Japan")
    main_window.session_combo.setCurrentText("R")
    
    QApplication.processEvents()
    
    # 創建視窗
    print("\n創建測試視窗...")
    methods = ['open_speed_analysis', 'open_throttle_analysis', 'open_brake_analysis']
    
    for method_name in methods:
        if hasattr(main_window, method_name):
            start = time.time()
            getattr(main_window, method_name)()
            elapsed = time.time() - start
            print(f"  {method_name}: {elapsed*1000:.1f}ms")
            QApplication.processEvents()
    
    print(f"\n總視窗數: {len(main_window.lap_analysis_windows)}")
    
    # 測試更新
    print("\n測試更新操作...")
    
    # 單次更新測試
    timings = []
    for i in range(3):
        start = time.time()
        main_window.update_all_lap_analysis()
        elapsed = time.time() - start
        timings.append(elapsed)
        print(f"  第 {i+1} 次更新: {elapsed:.2f}s")
        time.sleep(1)
    
    avg_time = sum(timings) / len(timings)
    print(f"\n平均更新時間: {avg_time:.2f}s")
    
    app.quit()
    return avg_time

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║  F1T GUI Performance Profiling                                    ║
║  目標：分析 update_all_lap_analysis() 的性能瓶頸                  ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # 選擇測試模式
    print("\n請選擇測試模式:")
    print("1. 完整 Profiling 分析 (詳細但較慢)")
    print("2. 簡單時間測試 (快速)")
    print("3. 兩者都執行")
    
    choice = input("\n輸入選項 (1/2/3, 預設=3): ").strip() or "3"
    
    if choice in ['1', '3']:
        print("\n" + "=" * 80)
        print("執行完整 Profiling 分析...")
        print("=" * 80)
        try:
            elapsed = profile_update_all_lap_analysis()
            print(f"\n✅ Profiling 完成，總時間: {elapsed:.2f}s")
        except Exception as e:
            print(f"\n❌ Profiling 失敗: {e}")
            import traceback
            traceback.print_exc()
    
    if choice in ['2', '3']:
        print("\n" + "=" * 80)
        print("執行簡單時間測試...")
        print("=" * 80)
        try:
            avg_time = simple_timing_test()
            print(f"\n✅ 簡單測試完成，平均時間: {avg_time:.2f}s")
        except Exception as e:
            print(f"\n❌ 簡單測試失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("測試完成！")
    print("=" * 80)
