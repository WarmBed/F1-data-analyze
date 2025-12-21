# -*- coding: utf-8 -*-
"""
SignalR Parser

解析錄製的 SignalR JSONL 檔案，提取並整理數據。
"""

import json
import base64
import zlib
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class SignalRParser:
    """SignalR 錄製檔案解析器"""
    
    # CarData.z 頻道定義
    CAR_DATA_CHANNELS = {
        "0": "rpm",
        "2": "speed",
        "3": "n_gear",
        "4": "throttle",
        "5": "brake",
        "45": "drs"
    }
    
    def __init__(self):
        self._data: Dict[str, List[Dict]] = {}
        
    def parse_file(
        self, 
        filepath: str, 
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        解析 JSONL 錄製檔案
        
        Args:
            filepath: JSONL 檔案路徑
            topics: 要提取的 topics (None = 全部)
            
        Returns:
            解析結果字典
        """
        self._data = {}
        topic_counts: Dict[str, int] = {}
        total_messages = 0
        errors = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                    
                try:
                    record = json.loads(line)
                    raw = record.get('raw', '')
                    timestamp = record.get('ts', '')
                    
                    # 解析原始 SignalR 訊息
                    parsed = self._parse_raw_message(raw)
                    
                    if parsed:
                        topic = parsed.get('topic', 'Unknown')
                        
                        # 過濾 topics
                        if topics and topic not in topics:
                            continue
                            
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1
                        total_messages += 1
                        
                        # 儲存解析數據
                        if topic not in self._data:
                            self._data[topic] = []
                            
                        self._data[topic].append({
                            'timestamp': timestamp,
                            'data': parsed.get('data', {})
                        })
                        
                except Exception as e:
                    errors += 1
                    
        return {
            'summary': {
                'total_messages': total_messages,
                'topics': topic_counts,
                'errors': errors,
                'file': filepath
            },
            'data': self._data
        }
        
    def _parse_raw_message(self, raw: str) -> Optional[Dict[str, Any]]:
        """解析原始 SignalR 訊息"""
        if not raw:
            return None
            
        try:
            # 處理舊版 SignalR 格式 (含 M 陣列)
            data = json.loads(raw)
            
            if 'M' in data and data['M']:
                # 舊版格式: {"C": "...", "M": [{"H": "Streaming", "M": "feed", "A": [...]}]}
                for msg in data['M']:
                    if msg.get('M') == 'feed' and 'A' in msg:
                        args = msg['A']
                        if len(args) >= 2:
                            topic = args[0]
                            payload = args[1]
                            return {
                                'topic': topic,
                                'data': self._parse_payload(topic, payload),
                                'timestamp': args[2] if len(args) > 2 else None
                            }
                            
            elif data.get('type') == 1 and 'arguments' in data:
                # 新版 SignalRCore 格式
                args = data['arguments']
                if len(args) >= 2:
                    topic = args[0]
                    payload = args[1]
                    return {
                        'topic': topic,
                        'data': self._parse_payload(topic, payload)
                    }
                    
            # 只有 G (groups) 數據的訊息，通常是初始狀態
            if 'G' in data:
                # 這些是 groups data，暫時跳過
                return None
                
        except json.JSONDecodeError:
            pass
            
        return None
        
    def _parse_payload(self, topic: str, payload: Any) -> Any:
        """解析 payload"""
        if topic.endswith('.z') and isinstance(payload, str):
            # base64 + zlib 壓縮
            try:
                decoded = base64.b64decode(payload)
                decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
                data = json.loads(decompressed.decode('utf-8'))
                
                # CarData.z 特殊處理
                if topic == 'CarData.z' and 'Entries' in data:
                    return self._parse_car_data(data)
                    
                # Position.z 特殊處理
                if topic == 'Position.z' and 'Position' in data:
                    return self._parse_position_data(data)
                    
                return data
            except Exception as e:
                return {'error': str(e)}
        else:
            return payload
            
    def _parse_car_data(self, data: Dict) -> Dict:
        """解析 CarData.z"""
        result = {'entries': []}
        
        for entry in data.get('Entries', []):
            utc = entry.get('Utc', '')
            cars = entry.get('Cars', {})
            
            car_data = {}
            for driver_num, car in cars.items():
                channels = car.get('Channels', {})
                
                # 轉換頻道名稱
                parsed_channels = {}
                for ch_id, value in channels.items():
                    ch_name = self.CAR_DATA_CHANNELS.get(str(ch_id), f'ch_{ch_id}')
                    parsed_channels[ch_name] = value
                    
                car_data[driver_num] = parsed_channels
                
            result['entries'].append({
                'utc': utc,
                'cars': car_data
            })
            
        return result
        
    def _parse_position_data(self, data: Dict) -> Dict:
        """解析 Position.z"""
        result = {'positions': []}
        
        for entry in data.get('Position', []):
            utc = entry.get('Timestamp', '')
            entries = entry.get('Entries', {})
            
            positions = {}
            for driver_num, pos in entries.items():
                positions[driver_num] = {
                    'x': pos.get('X', 0),
                    'y': pos.get('Y', 0),
                    'z': pos.get('Z', 0),
                    'status': pos.get('Status', '')
                }
                
            result['positions'].append({
                'utc': utc,
                'entries': positions
            })
            
        return result
        
    def get_timing_data(self) -> List[Dict]:
        """獲取 TimingData"""
        return self._data.get('TimingData', [])
        
    def get_car_data(self) -> List[Dict]:
        """獲取 CarData.z"""
        return self._data.get('CarData.z', [])
        
    def get_position_data(self) -> List[Dict]:
        """獲取 Position.z"""
        return self._data.get('Position.z', [])
        
    def get_weather_data(self) -> List[Dict]:
        """獲取 WeatherData"""
        return self._data.get('WeatherData', [])
        
    def get_race_control_messages(self) -> List[Dict]:
        """獲取 RaceControlMessages"""
        return self._data.get('RaceControlMessages', [])
        
    def export_to_csv(self, data: Dict, filepath: str):
        """匯出到 CSV"""
        # 匯出 TimingData
        timing_data = data.get('data', {}).get('TimingData', [])
        if timing_data:
            timing_path = filepath.replace('.csv', '_timing.csv')
            with open(timing_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Driver', 'Position', 'GapToLeader', 'Interval', 'LastLapTime'])
                
                for record in timing_data:
                    ts = record.get('timestamp', '')
                    data_dict = record.get('data', {})
                    
                    if isinstance(data_dict, dict) and 'Lines' in data_dict:
                        for driver, info in data_dict['Lines'].items():
                            writer.writerow([
                                ts,
                                driver,
                                info.get('Position', ''),
                                info.get('GapToLeader', ''),
                                info.get('IntervalToPositionAhead', {}).get('Value', ''),
                                info.get('LastLapTime', {}).get('Value', '')
                            ])
                            
        # 匯出 WeatherData
        weather_data = data.get('data', {}).get('WeatherData', [])
        if weather_data:
            weather_path = filepath.replace('.csv', '_weather.csv')
            with open(weather_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'AirTemp', 'TrackTemp', 'Humidity', 'Pressure', 'WindSpeed', 'WindDirection', 'Rainfall'])
                
                for record in weather_data:
                    ts = record.get('timestamp', '')
                    d = record.get('data', {})
                    writer.writerow([
                        ts,
                        d.get('AirTemp', ''),
                        d.get('TrackTemp', ''),
                        d.get('Humidity', ''),
                        d.get('Pressure', ''),
                        d.get('WindSpeed', ''),
                        d.get('WindDirection', ''),
                        d.get('Rainfall', '')
                    ])
                    
    def get_schema_summary(self) -> Dict[str, Any]:
        """獲取數據 schema 摘要，用於開發 GUI"""
        schema = {}
        
        for topic, records in self._data.items():
            if not records:
                continue
                
            # 取樣前幾條記錄分析結構
            samples = records[:5]
            keys_found = set()
            
            for sample in samples:
                data = sample.get('data', {})
                if isinstance(data, dict):
                    keys_found.update(self._get_all_keys(data))
                    
            schema[topic] = {
                'count': len(records),
                'keys': sorted(list(keys_found)),
                'sample': samples[0].get('data', {}) if samples else {}
            }
            
        return schema
        
    def _get_all_keys(self, d: Dict, prefix: str = '') -> List[str]:
        """遞迴獲取所有 keys"""
        keys = []
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.append(full_key)
            if isinstance(v, dict):
                keys.extend(self._get_all_keys(v, full_key))
        return keys
