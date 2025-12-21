#!/usr/bin/env python3
"""
F1T Live Timing 播放性能分析工具
專門分析 PKL 檔案載入和播放的性能瓶頸

測試場景:
1. PKL 檔案載入速度
2. 數據處理和快照生成
3. 播放時的 UI 更新性能
4. 多視窗同時播放的性能影響

使用方式:
    python tools/profile_live_timing_playback.py --year 2024 --race Japan --session Race --windows 5 --duration 30
"""

import sys
import os
import cProfile
import pstats
import argparse
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class LiveTimingPlaybackProfiler:
    """Live Timing 播放性能分析器"""
    
    def __init__(self, output_dir: str = "reports/profiling"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def profile_pkl_loading(self, year: int, race: str, session: str):
        """分析 PKL 檔案載入性能
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型
        """
        print("=" * 70)
        print(f"📦 Live Timing PKL 載入性能分析")
        print(f"   賽事: {year} {race} {session}")
        print("=" * 70)
        
        profile_file = self.output_dir / f"live_timing_pkl_loading_{self.timestamp}.prof"
        
        profiler = cProfile.Profile()
        
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            
            app = QApplication(sys.argv)
            from f1t_gui_main import StyleHMainWindow
            main_window = StyleHMainWindow()
            
            print(f"⏳ 準備載入 PKL 檔案...")
            
            # 獲取 DataManager（單例模式，直接實例化）
            from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
            dm = LiveTimingDataManager()
            
            load_success = False
            
            def start_loading():
                nonlocal load_success
                profiler.enable()
                print("✅ Profiler 已啟動，開始載入 PKL...")
                
                # 定義進度回調
                def progress_callback(percent, message):
                    print(f"  [{percent:3.0f}%] {message}")
                
                # 載入賽事（會優先使用 PKL 快取）
                load_success = dm.load_race(
                    year=year,
                    race=race,
                    session=session,
                    source_type="api",  # 使用新的 API 系統（PKL）
                    progress_callback=progress_callback
                )
                
                if load_success:
                    print("✅ PKL 載入成功")
                else:
                    print("❌ PKL 載入失敗")
                
                profiler.disable()
                
                # 1 秒後關閉
                QTimer.singleShot(1000, app.quit)
            
            # 2 秒後開始載入
            QTimer.singleShot(2000, start_loading)
            app.exec_()
            
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
        finally:
            profiler.disable()
        
        # 保存性能數據
        try:
            profiler.dump_stats(str(profile_file))
            print(f"\n💾 性能數據已保存: {profile_file}")
            
            # 生成文字報告
            self._generate_text_report(profile_file, "PKL 載入階段")
            
            # 啟動視覺化工具
            self._launch_snakeviz(profile_file)
        except Exception as e:
            print(f"⚠️  保存性能數據時發生錯誤: {e}")
            
    def profile_playback_performance(self, year: int, race: str, session: str, 
                                    num_windows: int = 5, playback_duration: int = 30):
        """分析播放性能（載入 + 多視窗 + 播放）
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型
            num_windows: 要開啟的視窗數量
            playback_duration: 播放持續時間（秒）
        """
        print("=" * 70)
        print(f"🎬 Live Timing 播放性能分析")
        print(f"   賽事: {year} {race} {session}")
        print(f"   視窗數量: {num_windows}")
        print(f"   播放時長: {playback_duration} 秒")
        print("=" * 70)
        
        profile_file = self.output_dir / f"live_timing_playback_{num_windows}windows_{self.timestamp}.prof"
        
        profiler = cProfile.Profile()
        
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            
            app = QApplication(sys.argv)
            from f1t_gui_main import StyleHMainWindow
            main_window = StyleHMainWindow()
            main_window.show()
            
            print(f"⏳ 初始化 Live Timing 系統...")
            
            from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
            dm = LiveTimingDataManager()
            
            load_success = False
            
            def start_test():
                nonlocal load_success
                profiler.enable()
                print("✅ Profiler 已啟動")
                
                # 階段 1: 載入 PKL
                print(f"\n📦 階段 1: 載入 PKL 檔案...")
                
                def progress_callback(percent, message):
                    print(f"  [{percent:3.0f}%] {message}")
                
                load_success = dm.load_race(
                    year=year,
                    race=race,
                    session=session,
                    source_type="api",
                    progress_callback=progress_callback
                )
                
                if not load_success:
                    print("❌ PKL 載入失敗，無法繼續測試")
                    profiler.disable()
                    app.quit()
                    return
                
                print("✅ PKL 載入完成")
                
                # 階段 2: 開啟多個視窗
                print(f"\n📊 階段 2: 開啟 {num_windows} 個 Live timing 視窗...")
                
                try:
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
                            
                            try:
                                main_window.live_timing_factory.create_module(module_key)
                                opened_count += 1
                            except Exception as e:
                                print(f"    ⚠️  無法創建 {module_key}: {e}")
                        
                        print(f"✅ 成功開啟 {opened_count}/{num_windows} 個視窗")
                    else:
                        print("⚠️  找不到 live_timing_factory")
                        
                except Exception as e:
                    print(f"❌ 開啟視窗時發生錯誤: {e}")
                
                # 階段 3: 開始播放
                print(f"\n▶️  階段 3: 開始播放 {playback_duration} 秒...")
                
                dm.play()
                print("✅ 播放已開始")
                
                # 設定播放結束時間
                QTimer.singleShot(playback_duration * 1000, stop_playback)
            
            def stop_playback():
                print("\n🛑 停止播放")
                dm.pause()
                profiler.disable()
                
                # 1 秒後關閉
                QTimer.singleShot(1000, app.quit)
            
            # 2 秒後開始測試
            QTimer.singleShot(2000, start_test)
            app.exec_()
            
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
        finally:
            profiler.disable()
        
        # 保存性能數據
        try:
            profiler.dump_stats(str(profile_file))
            print(f"\n💾 性能數據已保存: {profile_file}")
            
            # 生成文字報告
            self._generate_text_report(profile_file, f"Live Timing 播放 ({num_windows} 視窗)")
            
            # 啟動視覺化工具
            self._launch_snakeviz(profile_file)
        except Exception as e:
            print(f"⚠️  保存性能數據時發生錯誤: {e}")
            
    def _generate_text_report(self, profile_file: Path, stage_name: str):
        """生成文字格式的性能報告"""
        report_file = profile_file.with_suffix('.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"F1T Live Timing 性能分析報告 - {stage_name}\n")
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
            import subprocess
            
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
        description="F1T Live Timing 播放性能分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:

# 1. 僅測試 PKL 載入速度
python tools/profile_live_timing_playback.py --mode loading --year 2024 --race Japan --session Race

# 2. 測試完整播放流程（載入 + 5個視窗 + 播放30秒）
python tools/profile_live_timing_playback.py --mode playback --year 2024 --race Japan --session Race --windows 5 --duration 30

# 3. 測試極限情況（10個視窗 + 播放60秒）
python tools/profile_live_timing_playback.py --mode playback --year 2024 --race Japan --session Race --windows 10 --duration 60

# 4. 對比不同視窗數量的性能
python tools/profile_live_timing_playback.py --mode playback --year 2024 --race Japan --windows 2 --duration 20
python tools/profile_live_timing_playback.py --mode playback --year 2024 --race Japan --windows 5 --duration 20
python tools/profile_live_timing_playback.py --mode playback --year 2024 --race Japan --windows 10 --duration 20

# 然後使用對比工具
python tools/compare_performance.py --files reports/profiling/live_timing_playback_*.prof --labels "2視窗" "5視窗" "10視窗"

可用的賽事範例:
- 2024 Japan Race
- 2024 Italy Race
- 2024 Singapore Race
- 2025 Las_Vegas Race
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['loading', 'playback'],
        default='playback',
        help='分析模式：loading=僅PKL載入, playback=完整播放流程'
    )
    
    parser.add_argument(
        '--year',
        type=int,
        default=2024,
        help='賽事年份'
    )
    
    parser.add_argument(
        '--race',
        type=str,
        default='Japan',
        help='賽事名稱（例如: Japan, Italy, Singapore）'
    )
    
    parser.add_argument(
        '--session',
        type=str,
        default='Race',
        help='會話類型（Race, Qualifying, Sprint等）'
    )
    
    parser.add_argument(
        '--windows',
        type=int,
        default=5,
        help='Live timing 視窗數量（playback 模式）'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=30,
        help='播放持續時間（秒，playback 模式）'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='reports/profiling',
        help='輸出目錄'
    )
    
    args = parser.parse_args()
    
    profiler = LiveTimingPlaybackProfiler(output_dir=args.output)
    
    if args.mode == 'loading':
        profiler.profile_pkl_loading(
            year=args.year,
            race=args.race,
            session=args.session
        )
    elif args.mode == 'playback':
        profiler.profile_playback_performance(
            year=args.year,
            race=args.race,
            session=args.session,
            num_windows=args.windows,
            playback_duration=args.duration
        )


if __name__ == "__main__":
    main()
