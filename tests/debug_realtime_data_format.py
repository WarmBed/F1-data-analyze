"""
即時數據格式分析調試工具
=========================

連接 F1 官方 Live Timing SignalR 服務，分析並記錄接收到的數據格式。
用於調試和理解即時數據結構。

功能:
- 連接 F1 Live Timing SignalR
- 分析每種 topic 的數據結構
- 記錄樣本數據到 JSON 檔案
- 統計數據接收頻率
- 顯示數據欄位和類型

用法:
    python debug_realtime_data_format.py [--duration SECONDS] [--output-dir DIR]
    
範例:
    python debug_realtime_data_format.py --duration 60
    python debug_realtime_data_format.py --duration 300 --output-dir debug_samples

Author: F1T Team
Date: 2025-12-05
"""

import sys
import os
import json
import time
import threading
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Set

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.gui.live_timing.core.signalr_client import (
    F1SignalRClient,
    WEBSOCKETS_AVAILABLE,
)


class RealtimeDataAnalyzer:
    """即時數據格式分析器"""
    
    def __init__(self, output_dir: str = "debug_realtime_samples"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 統計數據
        self.topic_counts: Dict[str, int] = defaultdict(int)
        self.topic_samples: Dict[str, List[Dict]] = defaultdict(list)
        self.topic_fields: Dict[str, Set[str]] = defaultdict(set)
        self.topic_first_received: Dict[str, datetime] = {}
        self.topic_last_received: Dict[str, datetime] = {}
        
        # 數據記錄
        self.all_messages: List[Dict] = []
        self.max_samples_per_topic = 10  # 每個 topic 最多保留的樣本數
        
        # 時間戳
        self.start_time = None
        self.end_time = None
        
        # 客戶端
        self.client = None
        self._running = False
        
    def _on_data(self, topic: str, data: Any):
        """處理接收到的數據"""
        now = datetime.now()
        
        # 更新統計
        self.topic_counts[topic] += 1
        
        if topic not in self.topic_first_received:
            self.topic_first_received[topic] = now
        self.topic_last_received[topic] = now
        
        # 分析數據結構
        if isinstance(data, list):
            for item in data:
                self._analyze_item(topic, item)
        elif isinstance(data, dict):
            self._analyze_item(topic, data)
        
        # 保存樣本
        if len(self.topic_samples[topic]) < self.max_samples_per_topic:
            sample = {
                "timestamp": now.isoformat(),
                "data": data
            }
            self.topic_samples[topic].append(sample)
        
        # 記錄所有訊息（用於詳細分析）
        if len(self.all_messages) < 1000:  # 限制總訊息數
            self.all_messages.append({
                "timestamp": now.isoformat(),
                "topic": topic,
                "data": data
            })
        
        # 即時顯示
        self._print_data_summary(topic, data)
    
    def _analyze_item(self, topic: str, item: Any):
        """分析單個數據項目的結構"""
        if isinstance(item, dict):
            for key in item.keys():
                self.topic_fields[topic].add(key)
    
    def _print_data_summary(self, topic: str, data: Any):
        """即時顯示數據摘要"""
        count = self.topic_counts[topic]
        
        # 格式化數據預覽
        if isinstance(data, list):
            preview = f"[{len(data)} items]"
            if data and isinstance(data[0], dict):
                keys = list(data[0].keys())[:5]
                preview += f" keys: {keys}"
        elif isinstance(data, dict):
            keys = list(data.keys())[:5]
            preview = f"{{keys: {keys}}}"
        else:
            preview = str(data)[:80]
        
        # 限制預覽長度
        if len(preview) > 100:
            preview = preview[:100] + "..."
        
        print(f"[{topic}] #{count}: {preview}")
    
    def _on_status(self, status: str):
        """處理連接狀態"""
        print(f"\n[STATUS] {status}\n")
    
    def _on_error(self, error: str):
        """處理錯誤"""
        print(f"\n[ERROR] {error}\n")
    
    def start(self, duration_seconds: int = 60):
        """開始分析"""
        if not WEBSOCKETS_AVAILABLE:
            print("[ERROR] websockets package not installed!")
            print("Run: pip install websockets")
            return False
        
        print("=" * 70)
        print("F1 Realtime Data Format Analyzer")
        print("=" * 70)
        print(f"Output directory: {self.output_dir}")
        print(f"Duration: {duration_seconds} seconds")
        print()
        
        # 訂閱的數據主題
        topics = [
            "CarData.z",
            "Position.z",
            "TimingData",
            "DriverList",
            "WeatherData",
            "TrackStatus",
            "RaceControlMessages",
            "SessionInfo",
            "SessionStatus",
            "LapCount",
            "CurrentTyres",
            "TyreStintSeries",
            "PitStopSeries",
            "TimingAppData",
            "TimingStats",
            "ExtrapolatedClock",
            "Heartbeat",
        ]
        
        self.client = F1SignalRClient(
            topics=topics,
            on_data_callback=self._on_data,
            on_status_callback=self._on_status,
            on_error_callback=self._on_error
        )
        
        print("[INFO] Connecting to F1 Live Timing...")
        print(f"[INFO] Subscribing to {len(topics)} topics:")
        for topic in topics:
            print(f"  - {topic}")
        print()
        
        self.start_time = datetime.now()
        self._running = True
        
        # 在背景執行緒中運行客戶端
        def run_client():
            try:
                self.client.run()
            except Exception as e:
                print(f"[ERROR] Client error: {e}")
        
        client_thread = threading.Thread(target=run_client, daemon=True)
        client_thread.start()
        
        # 等待指定時間
        print(f"[INFO] Collecting data for {duration_seconds} seconds...")
        print("[INFO] Press Ctrl+C to stop early")
        print()
        print("-" * 70)
        
        try:
            time.sleep(duration_seconds)
        except KeyboardInterrupt:
            print("\n[INFO] Stopped by user")
        
        self.end_time = datetime.now()
        self._running = False
        
        # 停止客戶端
        if self.client:
            self.client.stop()
        
        time.sleep(1)  # 等待客戶端停止
        
        # 生成報告
        self._generate_report()
        
        return True
    
    def _generate_report(self):
        """生成分析報告"""
        print()
        print("=" * 70)
        print("Data Collection Complete - Generating Report")
        print("=" * 70)
        print()
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        # 1. 統計摘要
        report = {
            "collection_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": duration,
            },
            "topic_statistics": {},
            "topic_fields": {},
            "samples": {}
        }
        
        print("=== Topic Statistics ===\n")
        print(f"{'Topic':<25} {'Count':>8} {'Rate (msg/s)':>12} {'Fields':>8}")
        print("-" * 60)
        
        for topic in sorted(self.topic_counts.keys()):
            count = self.topic_counts[topic]
            rate = count / duration if duration > 0 else 0
            fields_count = len(self.topic_fields[topic])
            
            print(f"{topic:<25} {count:>8} {rate:>12.2f} {fields_count:>8}")
            
            report["topic_statistics"][topic] = {
                "count": count,
                "rate_per_second": round(rate, 2),
                "first_received": self.topic_first_received.get(topic, "").isoformat() if topic in self.topic_first_received else None,
                "last_received": self.topic_last_received.get(topic, "").isoformat() if topic in self.topic_last_received else None,
            }
        
        print()
        total_messages = sum(self.topic_counts.values())
        print(f"Total messages: {total_messages}")
        print(f"Total rate: {total_messages / duration:.2f} msg/s" if duration > 0 else "N/A")
        print()
        
        # 2. 欄位分析
        print("=== Topic Fields ===\n")
        
        for topic in sorted(self.topic_fields.keys()):
            fields = sorted(self.topic_fields[topic])
            print(f"{topic}:")
            for field in fields:
                print(f"  - {field}")
            print()
            
            report["topic_fields"][topic] = fields
        
        # 3. 保存樣本
        for topic, samples in self.topic_samples.items():
            report["samples"][topic] = samples
        
        # 4. 保存報告
        report_path = self.output_dir / f"analysis_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"[INFO] Report saved to: {report_path}")
        
        # 5. 保存所有訊息（用於詳細分析）
        if self.all_messages:
            messages_path = self.output_dir / f"all_messages_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(messages_path, 'w', encoding='utf-8') as f:
                json.dump(self.all_messages, f, indent=2, ensure_ascii=False, default=str)
            print(f"[INFO] All messages saved to: {messages_path}")
        
        # 6. 生成欄位類型分析
        self._analyze_field_types(report_path.parent)
        
        print()
        print("=" * 70)
        print("Analysis Complete!")
        print("=" * 70)
    
    def _analyze_field_types(self, output_dir: Path):
        """分析每個欄位的數據類型"""
        field_types: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        for topic, samples in self.topic_samples.items():
            if topic not in field_types:
                field_types[topic] = {}
            
            for sample in samples:
                data = sample.get("data", [])
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = [data]
                else:
                    continue
                
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    
                    for key, value in item.items():
                        if key not in field_types[topic]:
                            field_types[topic][key] = {
                                "types": set(),
                                "sample_values": [],
                                "nullable": False
                            }
                        
                        # 記錄類型
                        value_type = type(value).__name__
                        field_types[topic][key]["types"].add(value_type)
                        
                        # 記錄樣本值
                        if len(field_types[topic][key]["sample_values"]) < 3:
                            # 限制樣本值長度
                            sample_value = str(value)[:100] if value is not None else "null"
                            if sample_value not in field_types[topic][key]["sample_values"]:
                                field_types[topic][key]["sample_values"].append(sample_value)
                        
                        # 檢查是否可為空
                        if value is None:
                            field_types[topic][key]["nullable"] = True
        
        # 轉換 set 為 list 以便 JSON 序列化
        for topic in field_types:
            for field in field_types[topic]:
                field_types[topic][field]["types"] = list(field_types[topic][field]["types"])
        
        # 保存欄位類型分析
        types_path = output_dir / f"field_types_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(types_path, 'w', encoding='utf-8') as f:
            json.dump(field_types, f, indent=2, ensure_ascii=False)
        
        print(f"[INFO] Field types saved to: {types_path}")
        
        # 打印欄位類型摘要
        print("\n=== Field Types Summary ===\n")
        
        for topic in sorted(field_types.keys()):
            print(f"{topic}:")
            for field, info in sorted(field_types[topic].items()):
                types_str = ", ".join(info["types"])
                nullable_str = " (nullable)" if info["nullable"] else ""
                print(f"  {field}: {types_str}{nullable_str}")
                if info["sample_values"]:
                    for sample in info["sample_values"][:2]:
                        print(f"    -> {sample[:60]}{'...' if len(sample) > 60 else ''}")
            print()


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="F1 Realtime Data Format Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python debug_realtime_data_format.py --duration 60
  python debug_realtime_data_format.py --duration 300 --output-dir my_debug
        """
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=60,
        help="Duration to collect data in seconds (default: 60)"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="debug_realtime_samples",
        help="Output directory for samples and reports (default: debug_realtime_samples)"
    )
    
    args = parser.parse_args()
    
    analyzer = RealtimeDataAnalyzer(output_dir=args.output_dir)
    
    try:
        analyzer.start(duration_seconds=args.duration)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
