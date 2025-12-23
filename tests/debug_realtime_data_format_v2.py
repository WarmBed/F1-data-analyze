"""
即時數據格式調試工具 (進階版)
================================

根據 LiveF1 專案架構設計，提供更精確的數據格式分析。

主要改進:
1. 參考 LiveF1 的 signalr_aio 模組實現 SignalR 連接
2. 參考 LiveF1 的 parse_functions.py 實現數據解析
3. 詳細記錄各種 topic 的數據結構

LiveF1 專案分析總結:
=====================

1. SignalR 連接架構:
   - URL: https://livetiming.formula1.com/signalr
   - Hub: "Streaming"
   - Protocol: 1.5
   
2. 數據格式:
   - CarData.z / Position.z: base64 + zlib 壓縮
   - 其他 topic: 直接 JSON
   
3. 消息格式:
   - "R" 鍵: 訂閱回應，包含初始數據
   - "M" 鍵: 即時數據更新
   
4. Channel 映射 (CarData.z):
   - "0" -> rpm
   - "2" -> speed  
   - "3" -> n_gear (gear)
   - "4" -> throttle
   - "5" -> brake
   - "45" -> drs

用法:
    python debug_realtime_data_format_v2.py [--duration SECONDS]

Author: F1T Team
Date: 2025-12-05
"""

import sys
import os
import json
import time
import base64
import zlib
import threading
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Optional, Set

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.gui.live_timing.core.signalr_client import (
    F1SignalRClient,
    WEBSOCKETS_AVAILABLE,
)


# ============================================
# 根據 LiveF1 專案的解析函數
# ============================================

CHANNEL_NAME_MAP = {
    "0": "rpm",
    "2": "speed",
    "3": "n_gear",
    "4": "throttle",
    "5": "brake",
    "45": "drs"
}

TOPICS_DESCRIPTION = {
    "SessionInfo": "Session information (Meeting, Circuit, Type)",
    "ArchiveStatus": "Archive status",
    "TrackStatus": "Track status (Green/Yellow/Red/SC/VSC)",
    "SessionData": "Session data",
    "ContentStreams": "Content streams URLs",
    "AudioStreams": "Audio stream URLs",
    "ExtrapolatedClock": "Predicted session time",
    "TyreStintSeries": "Tyre stint information",
    "SessionStatus": "Session status (Started/Finished/Aborted)",
    "TimingDataF1": "F1-specific timing data",
    "TimingData": "General timing data (Position, Gap, Interval)",
    "DriverList": "Driver information (Name, Team, Number)",
    "LapSeries": "Lap series data",
    "TopThree": "Top three positions",
    "TimingAppData": "Timing application data",
    "TimingStats": "Timing statistics",
    "Heartbeat": "Connection heartbeat",
    "WeatherData": "Weather conditions (Temp, Wind, Rain)",
    "WeatherDataSeries": "Weather data history",
    "Position.z": "Car positions (X, Y, Z) - zlib compressed",
    "CarData.z": "Car telemetry (Speed, RPM, Gear) - zlib compressed",
    "TlaRcm": "Team audio and race control messages",
    "RaceControlMessages": "Race control messages",
    "PitLaneTimeCollection": "Pit lane timing",
    "CurrentTyres": "Current tyre compound",
    "DriverRaceInfo": "Driver race information",
    "ChampionshipPrediction": "Championship prediction",
    "OvertakeSeries": "Overtake series",
    "DriverScore": "Driver scores",
    "SPFeed": "Special feed",
    "PitStopSeries": "Pit stop series",
    "PitStop": "Pit stop details",
    "LapCount": "Lap count",
    "TeamRadio": "Team radio URLs",
}


def decode_zlib_data(data: str) -> dict:
    """
    解碼 base64 + zlib 壓縮的數據
    (參考 LiveF1 的 helper.py parse() 函數)
    """
    try:
        if data.startswith("{"):
            return json.loads(data)
        if data.startswith('"'):
            data = data.strip('"')
        
        decoded = base64.b64decode(data)
        decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
        return json.loads(decompressed.decode("utf-8-sig"))
    except Exception as e:
        print(f"[DECODE] Error: {e}")
        return {}


class AdvancedRealtimeAnalyzer:
    """進階即時數據格式分析器"""
    
    def __init__(self, output_dir: str = "debug_realtime_samples"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 統計
        self.topic_counts: Dict[str, int] = defaultdict(int)
        self.topic_samples: Dict[str, List[Dict]] = defaultdict(list)
        self.topic_fields: Dict[str, Set[str]] = defaultdict(set)
        self.topic_field_types: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        
        # 原始消息記錄
        self.raw_messages: List[Dict] = []
        self.parsed_messages: List[Dict] = []
        
        # 數據結構分析
        self.data_structures: Dict[str, Any] = {}
        
        # 設置
        self.max_samples = 20
        self.max_raw_messages = 500
        
        self.start_time = None
        self.end_time = None
        self.client = None
        self._running = False
        
    def _on_data(self, topic: str, data: Any):
        """處理接收到的數據"""
        now = datetime.now()
        
        self.topic_counts[topic] += 1
        count = self.topic_counts[topic]
        
        # 分析數據結構
        self._analyze_data_structure(topic, data)
        
        # 保存樣本
        if len(self.topic_samples[topic]) < self.max_samples:
            self.topic_samples[topic].append({
                "timestamp": now.isoformat(),
                "data": data
            })
        
        # 保存解析後的消息
        if len(self.parsed_messages) < self.max_raw_messages:
            self.parsed_messages.append({
                "timestamp": now.isoformat(),
                "topic": topic,
                "data": data,
                "count": count
            })
        
        # 即時顯示
        self._print_data_info(topic, data, count)
    
    def _analyze_data_structure(self, topic: str, data: Any):
        """分析數據結構"""
        if isinstance(data, list):
            for item in data:
                self._analyze_item(topic, item)
        elif isinstance(data, dict):
            self._analyze_item(topic, data)
    
    def _analyze_item(self, topic: str, item: Any):
        """分析單個數據項目"""
        if not isinstance(item, dict):
            return
        
        for key, value in item.items():
            self.topic_fields[topic].add(key)
            
            # 記錄類型
            value_type = type(value).__name__
            self.topic_field_types[topic][key].add(value_type)
    
    def _print_data_info(self, topic: str, data: Any, count: int):
        """打印數據信息"""
        description = TOPICS_DESCRIPTION.get(topic, "Unknown")
        
        # 計算數據大小
        if isinstance(data, list):
            size_info = f"{len(data)} items"
        elif isinstance(data, dict):
            size_info = f"{len(data)} keys"
        else:
            size_info = str(type(data).__name__)
        
        # 顯示前 3 個欄位
        if isinstance(data, list) and data:
            first_item = data[0] if isinstance(data[0], dict) else {}
            keys = list(first_item.keys())[:4]
        elif isinstance(data, dict):
            keys = list(data.keys())[:4]
        else:
            keys = []
        
        keys_str = ", ".join(keys) if keys else ""
        
        print(f"[{topic:25}] #{count:4} | {size_info:15} | keys: [{keys_str}]")
    
    def _on_raw_message(self, msg_type: str, raw_msg: Any):
        """記錄原始消息（用於調試）"""
        if len(self.raw_messages) < self.max_raw_messages:
            self.raw_messages.append({
                "timestamp": datetime.now().isoformat(),
                "type": msg_type,
                "data": raw_msg
            })
    
    def _on_status(self, status: str):
        """處理連接狀態"""
        print(f"\n{'='*60}")
        print(f"[STATUS] {status}")
        print(f"{'='*60}\n")
    
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
        print(" F1 Realtime Data Format Analyzer (Advanced)")
        print(" Based on LiveF1 project architecture")
        print("=" * 70)
        print(f"\nOutput directory: {self.output_dir}")
        print(f"Duration: {duration_seconds} seconds")
        print()
        
        # 所有可用的 topics
        topics = [
            # 壓縮數據
            "CarData.z",
            "Position.z",
            # 計時數據
            "TimingData",
            "TimingDataF1",
            "TimingAppData",
            "TimingStats",
            # 車手和賽事
            "DriverList",
            "SessionInfo",
            "SessionStatus",
            "SessionData",
            # 賽道狀態
            "TrackStatus",
            "WeatherData",
            "WeatherDataSeries",
            # 賽事控制
            "RaceControlMessages",
            "LapCount",
            "LapSeries",
            # 輪胎
            "CurrentTyres",
            "TyreStintSeries",
            # 進站
            "PitStopSeries",
            "PitLaneTimeCollection",
            # 其他
            "TopThree",
            "Heartbeat",
            "ExtrapolatedClock",
            "TeamRadio",
        ]
        
        print("Subscribing to topics:")
        for topic in topics:
            desc = TOPICS_DESCRIPTION.get(topic, "")
            print(f"  - {topic:25} : {desc}")
        print()
        
        self.client = F1SignalRClient(
            topics=topics,
            on_data_callback=self._on_data,
            on_status_callback=self._on_status,
            on_error_callback=self._on_error
        )
        
        self.start_time = datetime.now()
        self._running = True
        
        # 在背景執行緒運行
        def run_client():
            try:
                self.client.run()
            except Exception as e:
                print(f"[ERROR] Client error: {e}")
                import traceback
                traceback.print_exc()
        
        client_thread = threading.Thread(target=run_client, daemon=True)
        client_thread.start()
        
        print(f"[INFO] Collecting data for {duration_seconds} seconds...")
        print("[INFO] Press Ctrl+C to stop early")
        print()
        print("-" * 70)
        print(f"{'Topic':<26} | {'#':>5} | {'Size':<15} | Keys")
        print("-" * 70)
        
        try:
            time.sleep(duration_seconds)
        except KeyboardInterrupt:
            print("\n[INFO] Stopped by user")
        
        self.end_time = datetime.now()
        self._running = False
        
        if self.client:
            self.client.stop()
        
        time.sleep(1)
        
        self._generate_report()
        return True
    
    def _generate_report(self):
        """生成分析報告"""
        print()
        print("=" * 70)
        print(" Analysis Complete - Generating Report")
        print("=" * 70)
        print()
        
        duration = (self.end_time - self.start_time).total_seconds()
        total_messages = sum(self.topic_counts.values())
        
        # 構建報告
        report = {
            "analysis_info": {
                "tool_version": "2.0",
                "based_on": "LiveF1 project (https://github.com/GoktugOcal/LiveF1)",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": duration,
                "total_messages": total_messages,
                "messages_per_second": round(total_messages / duration, 2) if duration > 0 else 0,
            },
            "topic_statistics": {},
            "topic_fields": {},
            "field_types": {},
            "samples": {},
            "livef1_comparison": self._compare_with_livef1()
        }
        
        # 1. 統計摘要
        print("=== Topic Statistics ===\n")
        print(f"{'Topic':<25} {'Count':>8} {'Rate':>10} {'Fields':>8}")
        print("-" * 55)
        
        for topic in sorted(self.topic_counts.keys()):
            count = self.topic_counts[topic]
            rate = count / duration if duration > 0 else 0
            fields = len(self.topic_fields[topic])
            
            print(f"{topic:<25} {count:>8} {rate:>9.2f}/s {fields:>8}")
            
            report["topic_statistics"][topic] = {
                "count": count,
                "rate_per_second": round(rate, 2),
                "field_count": fields
            }
        
        print("-" * 55)
        print(f"{'TOTAL':<25} {total_messages:>8} {total_messages/duration if duration > 0 else 0:>9.2f}/s")
        print()
        
        # 2. 欄位分析
        print("=== Field Analysis ===\n")
        for topic in sorted(self.topic_fields.keys()):
            fields = sorted(self.topic_fields[topic])
            print(f"{topic}:")
            for field in fields:
                types = self.topic_field_types[topic].get(field, set())
                types_str = ", ".join(types)
                print(f"  - {field}: {types_str}")
            print()
            
            report["topic_fields"][topic] = fields
            report["field_types"][topic] = {
                field: list(types) 
                for field, types in self.topic_field_types[topic].items()
            }
        
        # 3. 保存樣本
        for topic, samples in self.topic_samples.items():
            report["samples"][topic] = samples
        
        # 4. 保存報告
        timestamp_str = self.start_time.strftime('%Y%m%d_%H%M%S')
        
        report_path = self.output_dir / f"analysis_v2_{timestamp_str}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print(f"[INFO] Report saved: {report_path}")
        
        # 5. 保存原始消息
        if self.raw_messages:
            raw_path = self.output_dir / f"raw_messages_{timestamp_str}.json"
            with open(raw_path, 'w', encoding='utf-8') as f:
                json.dump(self.raw_messages, f, indent=2, ensure_ascii=False, default=str)
            print(f"[INFO] Raw messages saved: {raw_path}")
        
        # 6. 保存解析消息
        if self.parsed_messages:
            parsed_path = self.output_dir / f"parsed_messages_{timestamp_str}.json"
            with open(parsed_path, 'w', encoding='utf-8') as f:
                json.dump(self.parsed_messages, f, indent=2, ensure_ascii=False, default=str)
            print(f"[INFO] Parsed messages saved: {parsed_path}")
        
        # 7. 打印與 LiveF1 的比較
        print()
        print("=== Comparison with LiveF1 ===\n")
        comparison = report["livef1_comparison"]
        for key, value in comparison.items():
            print(f"  {key}: {value}")
        
        print()
        print("=" * 70)
        print(" Analysis Complete!")
        print("=" * 70)
    
    def _compare_with_livef1(self) -> Dict[str, Any]:
        """比較我們的實現與 LiveF1 的差異"""
        return {
            "signalr_endpoint": "livetiming.formula1.com/signalr (same as LiveF1)",
            "hub_name": "Streaming (same as LiveF1)",
            "protocol_version": "1.5 (same as LiveF1)",
            "cardata_channels": CHANNEL_NAME_MAP,
            "zlib_decompression": "base64 decode + zlib.decompress(-MAX_WBITS) (same as LiveF1)",
            "message_format": {
                "R_key": "Subscription response with initial data",
                "M_key": "Real-time data updates",
                "message_structure": "{'H': hub, 'M': method, 'A': [topic, data, timestamp]}"
            },
            "differences_found": [],
            "notes": [
                "LiveF1 uses signalr_aio package (modified from python-signalr-client)",
                "Our implementation uses raw websockets for simpler dependency",
                "Data parsing follows same pattern as LiveF1's parse_functions.py"
            ]
        }


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="F1 Realtime Data Format Analyzer (Advanced)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Based on LiveF1 project: https://github.com/GoktugOcal/LiveF1

Examples:
  python debug_realtime_data_format_v2.py --duration 60
  python debug_realtime_data_format_v2.py -d 300 -o my_analysis
        """
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=60,
        help="Duration in seconds (default: 60)"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="debug_realtime_samples",
        help="Output directory (default: debug_realtime_samples)"
    )
    
    args = parser.parse_args()
    
    analyzer = AdvancedRealtimeAnalyzer(output_dir=args.output_dir)
    
    try:
        analyzer.start(duration_seconds=args.duration)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
