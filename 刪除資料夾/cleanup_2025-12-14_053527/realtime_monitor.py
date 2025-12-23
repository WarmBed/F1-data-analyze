"""
即時性能監控工具
=================

在 Live Timing 播放時即時監控各模組的更新耗時

使用方式：
    1. 先啟動 GUI 並載入賽事
    2. 在另一個終端執行: python realtime_monitor.py
    3. 查看即時統計

Author: F1T Team
Date: 2025-12-10
"""

import sys
import time
import threading
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List

class PerformanceMonitor:
    """性能監控器 - 追蹤各模組的更新時間"""
    
    def __init__(self):
        # 記錄每個函數的更新耗時（最近 100 次）
        self.function_timings = defaultdict(lambda: deque(maxlen=100))
        
        # 記錄快照處理時間
        self.snapshot_timings = deque(maxlen=50)
        
        # 統計計數器
        self.total_snapshots = 0
        self.slow_updates = defaultdict(int)  # 超過閾值的次數
        
        # 慢更新閾值（毫秒）
        self.slow_threshold_ms = 50.0  # 50ms = 20 FPS
        
        # 鎖
        self.lock = threading.Lock()
        
    def record_timing(self, func_name: str, elapsed_ms: float):
        """記錄函數執行時間"""
        with self.lock:
            self.function_timings[func_name].append(elapsed_ms)
            
            if elapsed_ms > self.slow_threshold_ms:
                self.slow_updates[func_name] += 1
    
    def record_snapshot(self, elapsed_ms: float):
        """記錄快照處理時間"""
        with self.lock:
            self.snapshot_timings.append(elapsed_ms)
            self.total_snapshots += 1
    
    def get_stats_report(self) -> str:
        """生成統計報告"""
        with self.lock:
            lines = []
            lines.append("=" * 100)
            lines.append(f"Live Timing 即時性能監控 - {datetime.now().strftime('%H:%M:%S')}")
            lines.append("=" * 100)
            
            # 快照統計
            if self.snapshot_timings:
                avg_snapshot = sum(self.snapshot_timings) / len(self.snapshot_timings)
                max_snapshot = max(self.snapshot_timings)
                min_snapshot = min(self.snapshot_timings)
                recent_10 = list(self.snapshot_timings)[-10:]
                recent_avg = sum(recent_10) / len(recent_10) if recent_10 else 0
                
                lines.append(f"\n📊 快照處理統計:")
                lines.append(f"  總快照數: {self.total_snapshots}")
                lines.append(f"  平均耗時: {avg_snapshot:.2f}ms")
                lines.append(f"  最大耗時: {max_snapshot:.2f}ms")
                lines.append(f"  最小耗時: {min_snapshot:.2f}ms")
                lines.append(f"  最近10次平均: {recent_avg:.2f}ms")
                
                # FPS 估算
                if avg_snapshot > 0:
                    estimated_fps = 1000 / avg_snapshot
                    lines.append(f"  估算 FPS: {estimated_fps:.1f}")
                
                if avg_snapshot > self.slow_threshold_ms:
                    lines.append(f"  ⚠️  平均超過閾值 ({self.slow_threshold_ms:.0f}ms)")
                else:
                    lines.append(f"  ✅ 性能良好")
            
            # 函數統計（按平均耗時排序）
            if self.function_timings:
                lines.append(f"\n🔍 函數執行耗時統計（前 15 名）:")
                
                func_stats = []
                for func_name, timings in self.function_timings.items():
                    if not timings:
                        continue
                        
                    avg_time = sum(timings) / len(timings)
                    max_time = max(timings)
                    min_time = min(timings)
                    slow_count = self.slow_updates[func_name]
                    slow_rate = (slow_count / len(timings)) * 100 if timings else 0
                    
                    # 最近 10 次平均
                    recent = list(timings)[-10:]
                    recent_avg = sum(recent) / len(recent) if recent else 0
                    
                    func_stats.append({
                        'name': func_name,
                        'avg': avg_time,
                        'max': max_time,
                        'min': min_time,
                        'recent_avg': recent_avg,
                        'count': len(timings),
                        'slow_count': slow_count,
                        'slow_rate': slow_rate
                    })
                
                # 按平均耗時排序
                func_stats.sort(key=lambda x: x['avg'], reverse=True)
                
                for i, stat in enumerate(func_stats[:15], 1):
                    lines.append(f"\n  {i}. {stat['name']}")
                    lines.append(f"     平均: {stat['avg']:.2f}ms | 最大: {stat['max']:.2f}ms | 最小: {stat['min']:.2f}ms")
                    lines.append(f"     最近10次: {stat['recent_avg']:.2f}ms | 調用次數: {stat['count']}")
                    
                    if stat['slow_rate'] > 10:
                        lines.append(f"     ⚠️  慢更新率: {stat['slow_rate']:.1f}% ({stat['slow_count']}/{stat['count']})")
                    
                    # 性能狀態指示
                    if stat['avg'] > 100:
                        lines.append(f"     🔴 嚴重阻塞")
                    elif stat['avg'] > 50:
                        lines.append(f"     🟡 輕微阻塞")
                    elif stat['avg'] > 20:
                        lines.append(f"     🟢 性能尚可")
                    else:
                        lines.append(f"     ✅ 性能良好")
            
            # 優化建議
            lines.append(f"\n💡 優化建議:")
            
            if self.function_timings:
                slowest = max(self.function_timings.items(), 
                             key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0)
                if slowest[1]:
                    avg = sum(slowest[1]) / len(slowest[1])
                    if avg > 50:
                        lines.append(f"  🎯 {slowest[0]} 平均耗時 {avg:.2f}ms")
                        lines.append(f"     建議: 移至背景執行緒或增加緩存")
            
            if self.snapshot_timings:
                recent_avg = sum(list(self.snapshot_timings)[-20:]) / min(20, len(self.snapshot_timings))
                if recent_avg > 100:
                    lines.append(f"  🎯 快照處理時間過長（{recent_avg:.2f}ms）")
                    lines.append(f"     建議: 減少開啟的模組數量或優化渲染")
            
            lines.append("=" * 100)
            return "\n".join(lines)


def inject_monitoring():
    """注入性能監控到 DataManager"""
    try:
        # 重要：不要創建新的 QApplication，直接導入模組
        # DataManager 是單例，會在已存在的 QApplication 中運行
        
        from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
        import functools
        
        monitor = PerformanceMonitor()
        
        # 獲取單例實例（如果 GUI 已啟動，這會返回現有實例）
        try:
            mgr = LiveTimingDataManager._instance
            if mgr is None:
                print("❌ DataManager 尚未初始化")
                print("💡 這表示 GUI 可能未啟動或 Live Timing 模組未載入")
                print("\n請先:")
                print("   1. 啟動 GUI: python f1t_gui_main.py")
                print("   2. 打開 Live Timing Control Dock")
                print("   3. 載入賽事並開始播放")
                print("   4. 再執行此監控工具")
                return None
        except AttributeError:
            print("❌ 無法訪問 DataManager 實例")
            print("💡 請確保 GUI 已啟動並且 Live Timing 模組已初始化")
            return None
        
        # 檢查是否有正在載入的賽事
        if not mgr._race_info:
            print("⚠️  DataManager 已初始化，但未載入賽事")
            print("💡 請在 GUI 中:")
            print("   1. 打開 Live Timing Control")
            print("   2. 選擇賽事（例如 Abu Dhabi 2025）")
            print("   3. 點擊 Load 按鈕")
            print("   4. 開始播放")
            print("   5. 再執行此監控工具")
            return None
        
        print(f"✅ 檢測到賽事: {mgr._race_info.get('year')} {mgr._race_info.get('race')} {mgr._race_info.get('session')}")
        print(f"   總快照數: {len(mgr._snapshots)}")
        print(f"   當前位置: {mgr._current_index}/{len(mgr._snapshots)}")
        print(f"   播放狀態: {mgr._playback_state}")
        
        # 包裝 _on_playback_tick
        original_tick = mgr._on_playback_tick
        
        @functools.wraps(original_tick)
        def monitored_tick():
            start = time.perf_counter()
            try:
                original_tick()
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                monitor.record_snapshot(elapsed_ms)
                monitor.record_timing("DataManager._on_playback_tick", elapsed_ms)
        
        mgr._on_playback_tick = monitored_tick
        
        print("✅ 性能監控已注入")
        return monitor
        
    except Exception as e:
        print(f"❌ 注入失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函數 - 純終端模式"""
    print("=" * 100)
    print("Live Timing 即時性能監控工具")
    print("=" * 100)
    print("\n⏳ 正在連接到 DataManager...")
    
    # 注入監控
    monitor = inject_monitoring()
    
    if not monitor:
        return 1
    
    print("📈 開始監控（每 2 秒更新一次，按 Ctrl+C 停止）\n")
    
    try:
        while True:
            time.sleep(2)
            
            # 清空終端（Windows）
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 顯示報告
            report = monitor.get_stats_report()
            print(report)
            
    except KeyboardInterrupt:
        print("\n\n✅ 監控已停止")
        print("💾 最終報告:")
        print(monitor.get_stats_report())
        return 0


if __name__ == "__main__":
    sys.exit(main())
