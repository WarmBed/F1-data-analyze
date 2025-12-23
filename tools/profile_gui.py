#!/usr/bin/env python3
"""
F1T GUI 性能分析工具 - 視覺化版本
使用 cProfile + SnakeViz 分析 GUI 性能瓶頸

使用方式:
    python tools/profile_gui.py --mode startup    # 分析啟動速度
    python tools/profile_gui.py --mode runtime    # 分析運行時性能
    python tools/profile_gui.py --mode live       # 分析 Live timing 大量開啟
"""

import sys
import os
import cProfile
import pstats
import io
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class F1TGUIProfiler:
    """F1T GUI 性能分析器"""
    
    def __init__(self, output_dir: str = "reports/profiling"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def profile_startup(self):
        """分析 GUI 啟動速度"""
        print("=" * 70)
        print("🚀 F1T GUI 啟動性能分析")
        print("=" * 70)
        
        profile_file = self.output_dir / f"gui_startup_{self.timestamp}.prof"
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        # 啟動 GUI（不顯示視窗，僅測試初始化）
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            
            app = QApplication(sys.argv)
            
            # 導入主視窗（這會觸發所有初始化代碼）
            print("⏳ 正在初始化主視窗...")
            from f1t_gui_main import StyleHMainWindow
            main_window = StyleHMainWindow()
            
            # 1 秒後自動關閉（足夠測試初始化）
            QTimer.singleShot(1000, app.quit)
            
            print("✅ 主視窗初始化完成")
            app.exec_()
            
        except Exception as e:
            print(f"❌ 錯誤: {e}")
        finally:
            profiler.disable()
            
        # 保存性能數據
        profiler.dump_stats(str(profile_file))
        print(f"\n💾 性能數據已保存: {profile_file}")
        
        # 生成文字報告
        self._generate_text_report(profile_file, "啟動階段")
        
        # 啟動視覺化工具
        self._launch_snakeviz(profile_file)
        
    def profile_runtime(self, duration: int = 30):
        """分析運行時性能
        
        Args:
            duration: 分析持續時間（秒）
        """
        print("=" * 70)
        print(f"⚡ F1T GUI 運行時性能分析 (持續 {duration} 秒)")
        print("=" * 70)
        
        profile_file = self.output_dir / f"gui_runtime_{self.timestamp}.prof"
        
        profiler = cProfile.Profile()
        
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            
            app = QApplication(sys.argv)
            from f1t_gui_main import StyleHMainWindow
            main_window = StyleHMainWindow()
            main_window.show()
            
            print(f"⏳ 開始分析 {duration} 秒的運行時性能...")
            print("💡 提示: 請正常操作 GUI，打開選單、分析模組等")
            
            # 延遲啟動 profiler（跳過初始化階段）
            def start_profiling():
                profiler.enable()
                print("✅ Profiler 已啟動")
                # 設定結束時間
                QTimer.singleShot(duration * 1000, stop_profiling)
            
            def stop_profiling():
                profiler.disable()
                print("🛑 Profiler 已停止")
                app.quit()
            
            QTimer.singleShot(2000, start_profiling)
            app.exec_()
            
        except Exception as e:
            print(f"❌ 錯誤: {e}")
        finally:
            if profiler:
                profiler.disable()
        
        # 保存性能數據
        profiler.dump_stats(str(profile_file))
        print(f"\n💾 性能數據已保存: {profile_file}")
        
        # 生成文字報告
        self._generate_text_report(profile_file, "運行階段")
        
        # 啟動視覺化工具
        self._launch_snakeviz(profile_file)
        
    def profile_live_timing_stress_test(self, num_windows: int = 8):
        """分析 Live timing 模組大量開啟的性能
        
        Args:
            num_windows: 要開啟的 Live timing 視窗數量
        """
        print("=" * 70)
        print(f"🔥 Live Timing 壓力測試 (開啟 {num_windows} 個視窗)")
        print("=" * 70)
        
        profile_file = self.output_dir / f"gui_live_timing_stress_{self.timestamp}.prof"
        
        profiler = cProfile.Profile()
        
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            
            app = QApplication(sys.argv)
            from f1t_gui_main import StyleHMainWindow
            main_window = StyleHMainWindow()
            main_window.show()
            
            print(f"⏳ 準備開啟 {num_windows} 個 Live timing 視窗...")
            
            def start_stress_test():
                profiler.enable()
                print("✅ Profiler 已啟動，開始壓力測試...")
                
                # 模擬開啟多個 Live timing 視窗
                try:
                    # 檢查是否有 Live timing 工廠方法
                    if hasattr(main_window, 'live_timing_factory'):
                        available_modules = [
                            "track_map",
                            "ranking_tower", 
                            "pit_window",
                            "race_control_messages",
                            "lap_time_distribution",
                            "circle_map",
                            "tyre_strategy",
                            "lap_history_lap_time"
                        ]
                        
                        opened_count = 0
                        for i in range(min(num_windows, len(available_modules))):
                            module_key = available_modules[i % len(available_modules)]
                            print(f"  📊 開啟視窗 {i+1}/{num_windows}: {module_key}")
                            
                            # 嘗試創建模組
                            try:
                                main_window.live_timing_factory.create_module(module_key)
                                opened_count += 1
                            except Exception as e:
                                print(f"    ⚠️  無法創建 {module_key}: {e}")
                        
                        print(f"\n✅ 成功開啟 {opened_count}/{num_windows} 個視窗")
                    else:
                        print("⚠️  找不到 live_timing_factory，嘗試手動創建...")
                        # 後備方案：嘗試直接調用選單動作
                        pass
                        
                except Exception as e:
                    print(f"❌ 壓力測試執行錯誤: {e}")
                
                # 5 秒後停止分析
                QTimer.singleShot(5000, stop_profiling)
            
            def stop_profiling():
                profiler.disable()
                print("🛑 Profiler 已停止")
                app.quit()
            
            # 2 秒後開始壓力測試
            QTimer.singleShot(2000, start_stress_test)
            app.exec_()
            
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
        finally:
            profiler.disable()
        
        # 保存性能數據（僅在 profiler 有數據時）
        try:
            profiler.dump_stats(str(profile_file))
            print(f"\n💾 性能數據已保存: {profile_file}")
            
            # 生成文字報告
            self._generate_text_report(profile_file, "Live Timing 壓力測試")
            
            # 啟動視覺化工具
            self._launch_snakeviz(profile_file)
        except Exception as e:
            print(f"⚠️  保存性能數據時發生錯誤: {e}")
        
    def _generate_text_report(self, profile_file: Path, stage_name: str):
        """生成文字格式的性能報告"""
        report_file = profile_file.with_suffix('.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"F1T GUI 性能分析報告 - {stage_name}\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            # 載入性能數據
            stats = pstats.Stats(str(profile_file), stream=f)
            
            # 按累計時間排序，顯示前 30 個最慢的函數
            f.write("\n📊 累計時間排名 (Top 30)\n")
            f.write("-" * 70 + "\n")
            stats.sort_stats('cumulative')
            stats.print_stats(30)
            
            # 按總時間排序，顯示前 30 個
            f.write("\n\n⏱️  總執行時間排名 (Top 30)\n")
            f.write("-" * 70 + "\n")
            stats.sort_stats('tottime')
            stats.print_stats(30)
            
            # 按調用次數排序，顯示前 30 個
            f.write("\n\n🔢 調用次數排名 (Top 30)\n")
            f.write("-" * 70 + "\n")
            stats.sort_stats('ncalls')
            stats.print_stats(30)
            
        print(f"📄 文字報告已生成: {report_file}")
        
    def _launch_snakeviz(self, profile_file: Path):
        """啟動 SnakeViz 視覺化工具"""
        try:
            # 檢查是否安裝 snakeviz
            result = subprocess.run(
                ["python", "-m", "snakeviz", "--version"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("\n⚠️  SnakeViz 未安裝")
                print("📦 安裝指令: pip install snakeviz")
                print("💡 安裝後可手動執行: python -m snakeviz", profile_file)
                return
                
            print("\n🌐 正在啟動 SnakeViz 視覺化工具...")
            print("💡 瀏覽器將自動開啟，顯示互動式性能火焰圖")
            
            # 啟動 snakeviz（會自動開啟瀏覽器）
            subprocess.Popen(
                ["python", "-m", "snakeviz", str(profile_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
        except Exception as e:
            print(f"⚠️  無法啟動 SnakeViz: {e}")
            print(f"💡 你可以手動執行: python -m snakeviz {profile_file}")


def main():
    parser = argparse.ArgumentParser(
        description="F1T GUI 性能分析工具 - 視覺化版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 分析啟動速度
  python tools/profile_gui.py --mode startup
  
  # 分析 30 秒運行時性能
  python tools/profile_gui.py --mode runtime --duration 30
  
  # Live timing 壓力測試（開啟 10 個視窗）
  python tools/profile_gui.py --mode live --windows 10
  
  # 對比不同場景
  python tools/profile_gui.py --mode startup
  python tools/profile_gui.py --mode live --windows 5
  python tools/profile_gui.py --mode live --windows 10
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['startup', 'runtime', 'live'],
        default='startup',
        help='性能分析模式'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=30,
        help='運行時分析持續時間（秒），僅用於 runtime 模式'
    )
    
    parser.add_argument(
        '--windows',
        type=int,
        default=8,
        help='Live timing 視窗數量，僅用於 live 模式'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='reports/profiling',
        help='輸出目錄'
    )
    
    args = parser.parse_args()
    
    profiler = F1TGUIProfiler(output_dir=args.output)
    
    if args.mode == 'startup':
        profiler.profile_startup()
    elif args.mode == 'runtime':
        profiler.profile_runtime(duration=args.duration)
    elif args.mode == 'live':
        profiler.profile_live_timing_stress_test(num_windows=args.windows)


if __name__ == "__main__":
    main()
