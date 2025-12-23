"""
Live Timing 性能分析工具
========================

即時監控各模組的更新耗時，找出卡頓的根源

使用方式：
1. 啟動 GUI
2. 在另一個終端執行：python performance_profiler.py
3. 查看即時統計

Author: F1T Team
Date: 2025-12-10
"""

import sys
import time
import threading
from collections import defaultdict, deque
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget

class PerformanceMonitor(QObject):
    """性能監控器 - 追蹤各模組的更新時間"""
    
    stats_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # 記錄每個模組的更新耗時（最近 100 次）
        self.module_timings = defaultdict(lambda: deque(maxlen=100))
        
        # 記錄每個快照的處理時間
        self.snapshot_timings = deque(maxlen=50)
        
        # 當前快照開始時間
        self.current_snapshot_start = None
        
        # 統計計數器
        self.total_snapshots = 0
        self.slow_updates = defaultdict(int)  # 超過閾值的次數
        
        # 慢更新閾值（毫秒）
        self.slow_threshold_ms = 16.67  # 60 FPS = 16.67ms per frame
        
    def start_snapshot(self):
        """開始追蹤一個快照"""
        self.current_snapshot_start = time.perf_counter()
        
    def end_snapshot(self):
        """結束追蹤一個快照"""
        if self.current_snapshot_start:
            elapsed = (time.perf_counter() - self.current_snapshot_start) * 1000
            self.snapshot_timings.append(elapsed)
            self.total_snapshots += 1
            self.current_snapshot_start = None
            
    def record_module_update(self, module_name: str, elapsed_ms: float):
        """記錄模組更新時間"""
        self.module_timings[module_name].append(elapsed_ms)
        
        if elapsed_ms > self.slow_threshold_ms:
            self.slow_updates[module_name] += 1
    
    def get_stats_report(self) -> str:
        """生成統計報告"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"Live Timing 性能分析報告 - {datetime.now().strftime('%H:%M:%S')}")
        lines.append("=" * 80)
        
        # 快照統計
        if self.snapshot_timings:
            avg_snapshot = sum(self.snapshot_timings) / len(self.snapshot_timings)
            max_snapshot = max(self.snapshot_timings)
            min_snapshot = min(self.snapshot_timings)
            
            lines.append(f"\n📊 快照處理統計:")
            lines.append(f"  總快照數: {self.total_snapshots}")
            lines.append(f"  平均耗時: {avg_snapshot:.2f}ms")
            lines.append(f"  最大耗時: {max_snapshot:.2f}ms")
            lines.append(f"  最小耗時: {min_snapshot:.2f}ms")
            
            if avg_snapshot > self.slow_threshold_ms:
                lines.append(f"  ⚠️  平均超過 60 FPS 閾值 ({self.slow_threshold_ms:.2f}ms)")
        
        # 模組統計（按平均耗時排序）
        if self.module_timings:
            lines.append(f"\n🔍 模組更新耗時（前 10 名）:")
            
            module_stats = []
            for module_name, timings in self.module_timings.items():
                if not timings:
                    continue
                    
                avg_time = sum(timings) / len(timings)
                max_time = max(timings)
                slow_count = self.slow_updates[module_name]
                slow_rate = (slow_count / len(timings)) * 100 if timings else 0
                
                module_stats.append({
                    'name': module_name,
                    'avg': avg_time,
                    'max': max_time,
                    'count': len(timings),
                    'slow_count': slow_count,
                    'slow_rate': slow_rate
                })
            
            # 按平均耗時排序
            module_stats.sort(key=lambda x: x['avg'], reverse=True)
            
            for i, stat in enumerate(module_stats[:10], 1):
                lines.append(f"\n  {i}. {stat['name']}")
                lines.append(f"     平均: {stat['avg']:.2f}ms | 最大: {stat['max']:.2f}ms | 更新次數: {stat['count']}")
                
                if stat['slow_rate'] > 10:
                    lines.append(f"     ⚠️  慢更新率: {stat['slow_rate']:.1f}% ({stat['slow_count']}/{stat['count']})")
        
        # 建議
        lines.append(f"\n💡 優化建議:")
        
        if self.module_timings:
            slowest = max(self.module_timings.items(), 
                         key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0)
            if slowest[1]:
                avg = sum(slowest[1]) / len(slowest[1])
                if avg > 10:
                    lines.append(f"  - {slowest[0]} 平均耗時 {avg:.2f}ms，建議優化")
        
        if self.snapshot_timings:
            recent_avg = sum(list(self.snapshot_timings)[-20:]) / min(20, len(self.snapshot_timings))
            if recent_avg > 50:
                lines.append(f"  - 快照處理時間過長（{recent_avg:.2f}ms），考慮減少模組數量")
        
        lines.append("=" * 80)
        return "\n".join(lines)


class PerformanceMonitorWindow(QMainWindow):
    """性能監控視窗"""
    
    def __init__(self, monitor: PerformanceMonitor):
        super().__init__()
        self.monitor = monitor
        
        self.setWindowTitle("F1T Live Timing 性能監控")
        self.setGeometry(100, 100, 900, 600)
        
        # 文字顯示區域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        
        layout = QVBoxLayout()
        layout.addWidget(self.text_display)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # 定時更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # 每秒更新一次
        
    def update_display(self):
        """更新顯示"""
        report = self.monitor.get_stats_report()
        self.text_display.setPlainText(report)


def inject_monitoring():
    """注入性能監控到 DataManager"""
    from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
    
    monitor = PerformanceMonitor()
    mgr = LiveTimingDataManager.instance()
    
    # 保存原始方法
    original_on_snapshot_updated = mgr._on_playback_tick
    
    # 包裝方法以記錄時間
    def monitored_on_playback_tick():
        monitor.start_snapshot()
        start = time.perf_counter()
        
        try:
            original_on_snapshot_updated()
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            monitor.record_module_update("DataManager._on_playback_tick", elapsed_ms)
            monitor.end_snapshot()
    
    # 替換方法
    mgr._on_playback_tick = monitored_on_playback_tick
    
    print("✅ 性能監控已注入到 DataManager")
    print("📊 正在啟動監控視窗...")
    
    return monitor


def main():
    """主函數"""
    # 檢查是否有 GUI 實例
    app = QApplication.instance()
    if app is None:
        print("❌ 未檢測到運行中的 F1T GUI")
        print("💡 請先啟動 GUI: python f1t_gui_main.py")
        return 1
    
    try:
        # 注入監控
        monitor = inject_monitoring()
        
        # 創建監控視窗
        window = PerformanceMonitorWindow(monitor)
        window.show()
        
        print("✅ 性能監控視窗已啟動")
        print("📈 開始即時監控...")
        
        # 不需要 exec，因為 GUI 已經在運行
        
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
