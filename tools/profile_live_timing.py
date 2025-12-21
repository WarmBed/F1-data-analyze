#!/usr/bin/env python3
"""
Live Timing PKL 載入與播放性能分析工具

測試場景:
1. PKL 檔案載入速度（101MB+ 的緩存檔案）
2. 播放器初始化和播放性能
3. 多個 Live timing 視窗同時播放的性能

使用方式:
    python tools/profile_live_timing.py --year 2025 --race Qatar --mode load
    python tools/profile_live_timing.py --year 2025 --race Qatar --mode play --duration 30
    python tools/profile_live_timing.py --year 2025 --race Qatar --mode stress --windows 5
"""

import sys
import os
import cProfile
import pstats
import argparse
import time
from pathlib import Path
from datetime import datetime

# 添加專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class LiveTimingProfiler:
    """Live Timing 性能分析器"""
    
    def __init__(self, year: int, race: str, output_dir: str = "reports/profiling"):
        self.year = year
        self.race = race
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def profile_pkl_load(self):
        """分析 PKL 檔案載入速度"""
        print("=" * 70)
        print(f"📦 Live Timing PKL 載入性能分析")
        print(f"   賽事: {self.year} {self.race}")
        print("=" * 70)
        
        profile_file = self.output_dir / f"live_timing_load_{self.year}_{self.race}_{self.timestamp}.prof"
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            from PyQt5.QtWidgets import QApplication
            
            # 創建 QApplication（必須）
            app = QApplication(sys.argv)
            
            print("⏳ 正在載入數據管理器...")
            from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
            
            # 實例化數據管理器（單例模式）
            data_manager = LiveTimingDataManager()
            
            # 檢查 PKL 檔案是否存在
            pkl_path = PROJECT_ROOT / "json" / "LiveF1" / str(self.year) / f"{self.race}_Race" / "_aligned_cache.pkl"
            if not pkl_path.exists():
                print(f"❌ 找不到 PKL 檔案: {pkl_path}")
                profiler.disable()
                return
            
            file_size_mb = pkl_path.stat().st_size / (1024 * 1024)
            print(f"📁 PKL 檔案大小: {file_size_mb:.2f} MB")
            print(f"📂 檔案路徑: {pkl_path}")
            
            # 測試載入速度
            print("\n⏱️  開始載入 PKL 檔案...")
            start_time = time.time()
            
            # 載入數據（使用正確的方法名稱）
            success = data_manager.load_race(self.year, self.race, session="Race")
            
            load_time = time.time() - start_time
            
            if success:
                print(f"✅ 載入成功！耗時: {load_time:.3f} 秒")
                print(f"📊 載入速度: {file_size_mb / load_time:.2f} MB/s")
                
                # 獲取數據統計
                if hasattr(data_manager, 'data') and data_manager.data:
                    print(f"\n📈 數據統計:")
                    print(f"   總幀數: {len(data_manager.data):,}")
                    if data_manager.data:
                        first_frame = data_manager.data[0]
                        print(f"   數據欄位: {len(first_frame)} 個")
            else:
                print(f"❌ 載入失敗")
            
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
            self._generate_text_report(profile_file, f"PKL 載入 - {self.year} {self.race}")
            
            # 啟動 SnakeViz
            self._launch_snakeviz(profile_file)
        except Exception as e:
            print(f"⚠️  保存性能數據時發生錯誤: {e}")
            
    def profile_playback(self, duration: int = 30):
        """分析播放器性能"""
        print("=" * 70)
        print(f"▶️  Live Timing 播放性能分析 (持續 {duration} 秒)")
        print(f"   賽事: {self.year} {self.race}")
        print("=" * 70)
        
        profile_file = self.output_dir / f"live_timing_play_{self.year}_{self.race}_{self.timestamp}.prof"
        
        profiler = cProfile.Profile()
        
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            
            app = QApplication(sys.argv)
            
            print("⏳ 正在初始化播放器...")
            from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
            from modules.gui.live_timing.core.playback_controller import PlaybackController
            
            # 載入數據
            data_manager = LiveTimingDataManager()
            success = data_manager.load_race(self.year, self.race, session="Race")
            
            if not success:
                print(f"❌ 無法載入數據")
                return
            
            print(f"✅ 數據載入完成")
            
            # 創建播放控制器
            playback = PlaybackController()
            
            # 延遲啟動 profiler
            def start_profiling():
                profiler.enable()
                print("✅ Profiler 已啟動")
                print(f"⏱️  開始播放 {duration} 秒...")
                
                # 開始播放
                playback.play()
                
                # 設定停止時間
                QTimer.singleShot(duration * 1000, stop_profiling)
            
            def stop_profiling():
                playback.pause()
                profiler.disable()
                print("🛑 播放停止，Profiler 已停止")
                app.quit()
            
            # 2 秒後開始播放
            QTimer.singleShot(2000, start_profiling)
            
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
            self._generate_text_report(profile_file, f"播放測試 - {self.year} {self.race}")
            
            # 啟動 SnakeViz
            self._launch_snakeviz(profile_file)
        except Exception as e:
            print(f"⚠️  保存性能數據時發生錯誤: {e}")
            
    def profile_stress_test(self, num_windows: int = 5, duration: int = 30):
        """壓力測試：多個 Live timing 視窗同時播放"""
        print("=" * 70)
        print(f"🔥 Live Timing 壓力測試")
        print(f"   賽事: {self.year} {self.race}")
        print(f"   視窗數量: {num_windows}")
        print(f"   播放時長: {duration} 秒")
        print("=" * 70)
        
        profile_file = self.output_dir / f"live_timing_stress_{num_windows}win_{self.timestamp}.prof"
        
        profiler = cProfile.Profile()
        
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            
            app = QApplication(sys.argv)
            
            print("⏳ 正在載入數據...")
            from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
            
            # 載入數據
            data_manager = LiveTimingDataManager()
            success = data_manager.load_race(self.year, self.race, session="Race")
            
            if not success:
                print(f"❌ 無法載入數據")
                return
            
            print(f"✅ 數據載入完成")
            print(f"⏳ 正在創建 {num_windows} 個 Live timing 視窗...")
            
            # 創建主視窗
            from f1t_gui_main import StyleHMainWindow
            main_window = StyleHMainWindow()
            main_window.show()
            
            # 延遲創建視窗並開始分析
            def start_stress_test():
                profiler.enable()
                print("✅ Profiler 已啟動")
                
                # 創建多個 Live timing 視窗
                try:
                    if hasattr(main_window, 'live_timing_factory'):
                        available_modules = [
                            "track_map",
                            "ranking_tower",
                            "pit_window",
                            "race_control_messages",
                            "lap_time_distribution"
                        ]
                        
                        opened_count = 0
                        for i in range(min(num_windows, len(available_modules))):
                            module_key = available_modules[i % len(available_modules)]
                            print(f"  📊 創建視窗 {i+1}/{num_windows}: {module_key}")
                            
                            try:
                                main_window.live_timing_factory.create_module(module_key)
                                opened_count += 1
                            except Exception as e:
                                print(f"    ⚠️  無法創建 {module_key}: {e}")
                        
                        print(f"\n✅ 成功創建 {opened_count}/{num_windows} 個視窗")
                        
                        # 開始播放
                        print(f"▶️  開始播放 {duration} 秒...")
                        from modules.gui.live_timing.core.playback_controller import PlaybackController
                        playback = PlaybackController()
                        playback.play()
                        
                        # 設定停止時間
                        QTimer.singleShot(duration * 1000, stop_profiling)
                    else:
                        print("⚠️  找不到 live_timing_factory")
                        app.quit()
                        
                except Exception as e:
                    print(f"❌ 壓力測試執行錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    app.quit()
            
            def stop_profiling():
                profiler.disable()
                print("🛑 Profiler 已停止")
                app.quit()
            
            # 3 秒後開始壓力測試
            QTimer.singleShot(3000, start_stress_test)
            
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
            self._generate_text_report(profile_file, f"壓力測試 {num_windows}視窗 - {self.year} {self.race}")
            
            # 啟動 SnakeViz
            self._launch_snakeviz(profile_file)
        except Exception as e:
            print(f"⚠️  保存性能數據時發生錯誤: {e}")
            
    def _generate_text_report(self, profile_file: Path, stage_name: str):
        """生成文字格式的性能報告"""
        report_file = profile_file.with_suffix('.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"Live Timing 性能分析報告 - {stage_name}\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            # 載入性能數據
            stats = pstats.Stats(str(profile_file), stream=f)
            
            # 按累計時間排序
            f.write("\n📊 累計時間排名 (Top 30)\n")
            f.write("-" * 70 + "\n")
            stats.sort_stats('cumulative')
            stats.print_stats(30)
            
            # 按總時間排序
            f.write("\n\n⏱️  總執行時間排名 (Top 30)\n")
            f.write("-" * 70 + "\n")
            stats.sort_stats('tottime')
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
            
            # 啟動 snakeviz
            subprocess.Popen(
                ["python", "-m", "snakeviz", str(profile_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
        except Exception as e:
            print(f"⚠️  無法啟動 SnakeViz: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Live Timing PKL 載入與播放性能分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 測試 PKL 載入速度
  python tools/profile_live_timing.py --year 2025 --race Qatar --mode load
  
  # 測試播放性能（30 秒）
  python tools/profile_live_timing.py --year 2025 --race Qatar --mode play --duration 30
  
  # 壓力測試（5 個視窗同時播放）
  python tools/profile_live_timing.py --year 2025 --race Qatar --mode stress --windows 5 --duration 30
        """
    )
    
    parser.add_argument('--year', type=int, required=True, help='賽季年份')
    parser.add_argument('--race', type=str, required=True, help='賽事名稱 (例如: Qatar, Abu_Dhabi)')
    parser.add_argument('--mode', choices=['load', 'play', 'stress'], default='load', help='測試模式')
    parser.add_argument('--duration', type=int, default=30, help='播放或壓力測試的持續時間（秒）')
    parser.add_argument('--windows', type=int, default=5, help='壓力測試的視窗數量')
    parser.add_argument('--output', type=str, default='reports/profiling', help='輸出目錄')
    
    args = parser.parse_args()
    
    profiler = LiveTimingProfiler(
        year=args.year,
        race=args.race,
        output_dir=args.output
    )
    
    if args.mode == 'load':
        profiler.profile_pkl_load()
    elif args.mode == 'play':
        profiler.profile_playback(duration=args.duration)
    elif args.mode == 'stress':
        profiler.profile_stress_test(num_windows=args.windows, duration=args.duration)


if __name__ == "__main__":
    main()
