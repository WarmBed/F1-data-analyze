#!/usr/bin/env python3
"""
F1T GUI 即時性能監控 - py-spy 版本
使用 py-spy 進行即時性能採樣，無需修改代碼

py-spy 優點:
- 無侵入式採樣（不修改原始代碼）
- 極低開銷（< 1% CPU）
- 可附加到正在運行的進程
- 生成火焰圖和 speedscope 格式

使用方式:
    python tools/profile_gui_pyspy.py --mode record    # 記錄運行並生成火焰圖
    python tools/profile_gui_pyspy.py --mode top       # 即時監控（類似 top）
    python tools/profile_gui_pyspy.py --mode live      # Live timing 壓力測試
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime


class PySpyProfiler:
    """基於 py-spy 的 F1T GUI 性能分析器"""
    
    def __init__(self, output_dir: str = "reports/profiling"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.project_root = Path(__file__).parent.parent
        
    def check_pyspy_installed(self) -> bool:
        """檢查 py-spy 是否已安裝"""
        try:
            result = subprocess.run(
                ["py-spy", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ py-spy 已安裝: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        print("❌ py-spy 未安裝")
        print("\n📦 安裝指令:")
        print("   pip install py-spy")
        print("\n⚠️  注意: Windows 上可能需要管理員權限")
        return False
        
    def record_with_flamegraph(self, duration: int = 60, format: str = "svg"):
        """記錄運行並生成火焰圖
        
        Args:
            duration: 記錄持續時間（秒）
            format: 輸出格式 (svg, speedscope)
        """
        if not self.check_pyspy_installed():
            return
            
        print("=" * 70)
        print(f"🔥 py-spy 火焰圖記錄 (持續 {duration} 秒)")
        print("=" * 70)
        
        output_file = self.output_dir / f"gui_flamegraph_{self.timestamp}.{format}"
        
        # py-spy 命令
        cmd = [
            "py-spy",
            "record",
            "--output", str(output_file),
            "--format", format,
            "--duration", str(duration),
            "--rate", "100",  # 每秒採樣 100 次
            "--subprocesses",  # 追蹤子進程
            "--", "python", "f1t_gui_main.py"
        ]
        
        print(f"⏳ 正在啟動 F1T GUI 並記錄 {duration} 秒...")
        print("💡 提示: 請正常操作 GUI，特別是開啟 Live timing 模組")
        print(f"\n執行命令: {' '.join(cmd)}\n")
        
        try:
            # 切換到專案根目錄
            subprocess.run(cmd, cwd=str(self.project_root), check=True)
            
            print(f"\n✅ 記錄完成！")
            print(f"📊 火焰圖已生成: {output_file}")
            
            if format == "svg":
                print(f"\n💡 用瀏覽器開啟查看: {output_file.absolute()}")
            elif format == "speedscope":
                print(f"\n💡 上傳到 https://www.speedscope.app/ 查看")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ 錯誤: {e}")
        except KeyboardInterrupt:
            print("\n⚠️  用戶中斷")
            
    def top_mode(self):
        """即時監控模式（類似 top 命令）"""
        if not self.check_pyspy_installed():
            return
            
        print("=" * 70)
        print("📊 py-spy 即時監控模式")
        print("=" * 70)
        print("💡 提示: 先手動啟動 F1T GUI，然後此工具會附加到進程")
        print("按 Ctrl+C 停止監控\n")
        
        # 啟動 GUI
        print("⏳ 正在啟動 F1T GUI...")
        gui_process = subprocess.Popen(
            ["python", "f1t_gui_main.py"],
            cwd=str(self.project_root)
        )
        
        # 等待 GUI 啟動
        time.sleep(3)
        
        try:
            # py-spy top 命令
            cmd = [
                "py-spy",
                "top",
                "--pid", str(gui_process.pid),
                "--subprocesses"
            ]
            
            print(f"✅ 開始監控 PID: {gui_process.pid}\n")
            subprocess.run(cmd)
            
        except KeyboardInterrupt:
            print("\n⚠️  停止監控")
        finally:
            gui_process.terminate()
            gui_process.wait()
            
    def profile_live_timing_stress(self, num_windows: int = 8, duration: int = 30):
        """Live timing 壓力測試 + py-spy 記錄
        
        Args:
            num_windows: Live timing 視窗數量
            duration: 記錄時長（秒）
        """
        if not self.check_pyspy_installed():
            return
            
        print("=" * 70)
        print(f"🔥 Live Timing 壓力測試 + py-spy 記錄")
        print(f"   視窗數量: {num_windows}")
        print(f"   記錄時長: {duration} 秒")
        print("=" * 70)
        
        output_svg = self.output_dir / f"live_stress_{num_windows}windows_{self.timestamp}.svg"
        output_json = self.output_dir / f"live_stress_{num_windows}windows_{self.timestamp}.speedscope.json"
        
        # 創建自動化腳本（自動開啟多個 Live timing 視窗）
        automation_script = self._create_automation_script(num_windows)
        
        print(f"⏳ 啟動 GUI 並自動開啟 {num_windows} 個 Live timing 視窗...")
        
        # py-spy 命令
        cmd = [
            "py-spy",
            "record",
            "--output", str(output_svg),
            "--format", "svg",
            "--duration", str(duration),
            "--rate", "100",
            "--subprocesses",
            "--", "python", str(automation_script)
        ]
        
        try:
            subprocess.run(cmd, cwd=str(self.project_root), check=True)
            
            print(f"\n✅ 壓力測試完成！")
            print(f"📊 火焰圖: {output_svg}")
            
            # 同時生成 speedscope 格式
            print("\n⏳ 生成 speedscope 格式...")
            cmd_json = [
                "py-spy",
                "record",
                "--output", str(output_json),
                "--format", "speedscope",
                "--duration", str(duration),
                "--rate", "100",
                "--subprocesses",
                "--", "python", str(automation_script)
            ]
            subprocess.run(cmd_json, cwd=str(self.project_root), check=True)
            print(f"📊 speedscope: {output_json}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 錯誤: {e}")
        except KeyboardInterrupt:
            print("\n⚠️  用戶中斷")
        finally:
            # 清理自動化腳本
            if automation_script.exists():
                automation_script.unlink()
                
    def _create_automation_script(self, num_windows: int) -> Path:
        """創建自動化腳本，用於自動開啟多個 Live timing 視窗"""
        script_path = self.project_root / "tools" / "_temp_automation.py"
        
        script_content = f'''#!/usr/bin/env python3
"""臨時自動化腳本 - 自動開啟 {num_windows} 個 Live timing 視窗"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 添加專案路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from f1t_gui_main import F1TelemetryGUI

def main():
    app = QApplication(sys.argv)
    main_window = F1TelemetryGUI()
    main_window.show()
    
    def open_live_timing_windows():
        """自動開啟 Live timing 視窗"""
        try:
            if hasattr(main_window, 'live_timing_factory'):
                modules = [
                    "track_map",
                    "ranking_tower", 
                    "pit_window",
                    "race_control_messages",
                    "lap_time_distribution",
                    "circle_map",
                    "tyre_strategy",
                    "lap_history_lap_time"
                ]
                
                for i in range({num_windows}):
                    module_key = modules[i % len(modules)]
                    print(f"📊 開啟視窗 {{i+1}}/{num_windows}: {{module_key}}")
                    try:
                        main_window.live_timing_factory.create_module(module_key)
                    except Exception as e:
                        print(f"⚠️  無法創建 {{module_key}}: {{e}}")
                        
                print(f"✅ 已開啟 {num_windows} 個視窗，持續運行以進行性能分析...")
        except Exception as e:
            print(f"❌ 自動化錯誤: {{e}}")
    
    # 2 秒後開始自動化
    QTimer.singleShot(2000, open_live_timing_windows)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
'''
        
        script_path.write_text(script_content, encoding='utf-8')
        return script_path


def main():
    parser = argparse.ArgumentParser(
        description="F1T GUI 即時性能監控 - py-spy 版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 記錄 60 秒並生成 SVG 火焰圖
  python tools/profile_gui_pyspy.py --mode record --duration 60
  
  # 記錄並生成 speedscope 格式（可上傳 speedscope.app）
  python tools/profile_gui_pyspy.py --mode record --duration 60 --format speedscope
  
  # 即時監控模式（類似 top）
  python tools/profile_gui_pyspy.py --mode top
  
  # Live timing 壓力測試（自動開啟 10 個視窗）
  python tools/profile_gui_pyspy.py --mode live --windows 10 --duration 45
  
py-spy 安裝:
  pip install py-spy
  
火焰圖說明:
  - X 軸: 累計時間佔比（不是時間軸）
  - Y 軸: 調用棧深度
  - 顏色: 隨機（無特殊意義）
  - 寬度: 函數佔用的 CPU 時間
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['record', 'top', 'live'],
        default='record',
        help='性能分析模式'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='記錄持續時間（秒）'
    )
    
    parser.add_argument(
        '--format',
        choices=['svg', 'speedscope'],
        default='svg',
        help='輸出格式（record 模式）'
    )
    
    parser.add_argument(
        '--windows',
        type=int,
        default=8,
        help='Live timing 視窗數量（live 模式）'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='reports/profiling',
        help='輸出目錄'
    )
    
    args = parser.parse_args()
    
    profiler = PySpyProfiler(output_dir=args.output)
    
    if args.mode == 'record':
        profiler.record_with_flamegraph(duration=args.duration, format=args.format)
    elif args.mode == 'top':
        profiler.top_mode()
    elif args.mode == 'live':
        profiler.profile_live_timing_stress(num_windows=args.windows, duration=args.duration)


if __name__ == "__main__":
    main()
