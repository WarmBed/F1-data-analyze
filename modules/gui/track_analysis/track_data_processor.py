#!/usr/bin/env python3
"""
賽道數據處理器 - TrackDataProcessor
Track Data Processor

此檔案為賽道數據處理的核心模組，負責：
1. 解析CLI function 2的JSON輸出
2. 處理座標轉換和正規化
3. 計算賽道特徵和統計數據
4. 提供數據快取和管理

目前為佔位符實現，待後續完整開發
"""

import json
import math
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class TrackDataProcessor:
    """賽道數據處理器"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.ensure_cache_dir()
        
        # 處理結果暫存
        self.last_processed_data = None
        self.processing_stats = {}
    
    def ensure_cache_dir(self):
        """確保快取目錄存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def parse_cli_json_output(self, json_file_path: str) -> Optional[Dict]:
        """
        解析CLI function 2的JSON輸出
        
        Args:
            json_file_path: JSON檔案路徑
            
        Returns:
            解析後的數據字典，失敗時返回None
        """
        try:
            print(f"[TRACK_PROCESSOR] 開始解析JSON檔案: {json_file_path}")
            
            if not os.path.exists(json_file_path):
                print(f"[ERROR] 檔案不存在: {json_file_path}")
                return None
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            print(f"[TRACK_PROCESSOR] JSON解析成功，資料大小: {len(str(raw_data))} 字元")
            
            # 驗證必要欄位
            required_fields = ['session_info', 'position_analysis']
            missing_fields = []
            for field in required_fields:
                if field not in raw_data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"[WARNING] 缺少必要欄位: {missing_fields}")
            
            self.last_processed_data = raw_data
            return raw_data
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON解析錯誤: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] 解析檔案失敗: {e}")
            return None
    
    def extract_position_records(self, raw_data: Dict) -> List[Dict]:
        """
        提取位置記錄
        
        Args:
            raw_data: 原始JSON數據
            
        Returns:
            位置記錄列表
        """
        try:
            position_records = raw_data.get('detailed_position_records', [])
            
            if not position_records:
                print("[WARNING] 沒有找到詳細位置記錄")
                return []
            
            # 驗證記錄格式
            valid_records = []
            for i, record in enumerate(position_records):
                if self._validate_position_record(record):
                    valid_records.append(record)
                else:
                    print(f"[WARNING] 第{i}筆記錄格式不正確，已跳過")
            
            print(f"[TRACK_PROCESSOR] 提取位置記錄: {len(valid_records)}/{len(position_records)} 筆有效")
            return valid_records
            
        except Exception as e:
            print(f"[ERROR] 提取位置記錄失敗: {e}")
            return []
    
    def _validate_position_record(self, record: Dict) -> bool:
        """驗證位置記錄格式"""
        required_fields = ['position_x', 'position_y', 'distance_m']
        return all(field in record for field in required_fields)
    
    def extract_track_bounds(self, raw_data: Dict) -> Dict:
        """
        提取賽道邊界資訊
        
        Args:
            raw_data: 原始JSON數據
            
        Returns:
            賽道邊界字典
        """
        try:
            position_analysis = raw_data.get('position_analysis', {})
            track_bounds = position_analysis.get('track_bounds', {})
            
            if not track_bounds:
                print("[WARNING] 沒有找到賽道邊界資訊")
                return {}
            
            # 驗證邊界資訊
            required_bounds = ['min_x', 'max_x', 'min_y', 'max_y']
            for bound in required_bounds:
                if bound not in track_bounds:
                    print(f"[WARNING] 缺少邊界資訊: {bound}")
            
            print(f"[TRACK_PROCESSOR] 賽道邊界: {track_bounds}")
            return track_bounds
            
        except Exception as e:
            print(f"[ERROR] 提取賽道邊界失敗: {e}")
            return {}
    
    def normalize_coordinates(self, position_records: List[Dict]) -> List[Dict]:
        """
        正規化座標系統
        
        Args:
            position_records: 原始位置記錄
            
        Returns:
            正規化後的位置記錄
        """
        try:
            if not position_records:
                return []
            
            # 提取座標範圍
            x_coords = [record['position_x'] for record in position_records]
            y_coords = [record['position_y'] for record in position_records]
            
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            x_range = x_max - x_min
            y_range = y_max - y_min
            
            # 避免除零錯誤
            if x_range == 0:
                x_range = 1
            if y_range == 0:
                y_range = 1
            
            # 正規化到0-1範圍
            normalized_records = []
            for record in position_records:
                normalized_record = record.copy()
                normalized_record['normalized_x'] = (record['position_x'] - x_min) / x_range
                normalized_record['normalized_y'] = (record['position_y'] - y_min) / y_range
                normalized_records.append(normalized_record)
            
            print(f"[TRACK_PROCESSOR] 座標正規化完成: {len(normalized_records)} 筆記錄")
            print(f"[TRACK_PROCESSOR] X範圍: {x_min:.2f} ~ {x_max:.2f} (範圍: {x_range:.2f})")
            print(f"[TRACK_PROCESSOR] Y範圍: {y_min:.2f} ~ {y_max:.2f} (範圍: {y_range:.2f})")
            
            return normalized_records
            
        except Exception as e:
            print(f"[ERROR] 座標正規化失敗: {e}")
            return position_records
    
    def calculate_track_statistics(self, position_records: List[Dict]) -> Dict:
        """
        計算賽道統計資訊
        
        Args:
            position_records: 位置記錄
            
        Returns:
            統計資訊字典
        """
        try:
            if not position_records:
                return {}
            
            # 基本統計
            distances = [record['distance_m'] for record in position_records]
            x_coords = [record['position_x'] for record in position_records]
            y_coords = [record['position_y'] for record in position_records]
            
            stats = {
                'total_points': len(position_records),
                'track_length_m': max(distances) - min(distances) if distances else 0,
                'distance_range': {
                    'min': min(distances) if distances else 0,
                    'max': max(distances) if distances else 0
                },
                'coordinate_range': {
                    'x_min': min(x_coords) if x_coords else 0,
                    'x_max': max(x_coords) if x_coords else 0,
                    'y_min': min(y_coords) if y_coords else 0,
                    'y_max': max(y_coords) if y_coords else 0
                }
            }
            
            # 計算平均間距
            if len(distances) > 1:
                stats['avg_point_interval_m'] = stats['track_length_m'] / (len(distances) - 1)
            else:
                stats['avg_point_interval_m'] = 0
            
            # 計算賽道中心點
            if x_coords and y_coords:
                stats['track_center'] = {
                    'x': (min(x_coords) + max(x_coords)) / 2,
                    'y': (min(y_coords) + max(y_coords)) / 2
                }
            
            print(f"[TRACK_PROCESSOR] 統計計算完成:")
            print(f"   總點數: {stats['total_points']}")
            print(f"   賽道長度: {stats['track_length_m']:.2f}m")
            print(f"   平均間距: {stats['avg_point_interval_m']:.2f}m")
            
            self.processing_stats = stats
            return stats
            
        except Exception as e:
            print(f"[ERROR] 計算統計資訊失敗: {e}")
            return {}
    
    def calculate_track_segments(self, position_records: List[Dict], segment_count: int = 10) -> List[Dict]:
        """
        計算賽道分段資訊
        
        Args:
            position_records: 位置記錄
            segment_count: 分段數量
            
        Returns:
            分段資訊列表
        """
        try:
            if not position_records or segment_count <= 0:
                return []
            
            total_points = len(position_records)
            points_per_segment = total_points // segment_count
            
            segments = []
            for i in range(segment_count):
                start_idx = i * points_per_segment
                end_idx = min((i + 1) * points_per_segment, total_points)
                
                if start_idx >= total_points:
                    break
                
                segment_records = position_records[start_idx:end_idx]
                if not segment_records:
                    continue
                
                # 計算分段統計
                distances = [r['distance_m'] for r in segment_records]
                segment_info = {
                    'segment_id': i + 1,
                    'start_distance': min(distances) if distances else 0,
                    'end_distance': max(distances) if distances else 0,
                    'point_count': len(segment_records),
                    'start_position': {
                        'x': segment_records[0]['position_x'],
                        'y': segment_records[0]['position_y']
                    },
                    'end_position': {
                        'x': segment_records[-1]['position_x'],
                        'y': segment_records[-1]['position_y']
                    }
                }
                
                segments.append(segment_info)
            
            print(f"[TRACK_PROCESSOR] 賽道分段計算完成: {len(segments)} 個分段")
            return segments
            
        except Exception as e:
            print(f"[ERROR] 計算賽道分段失敗: {e}")
            return []
    
    def process_complete_dataset(self, json_file_path: str) -> Optional[Dict]:
        """
        處理完整數據集
        
        Args:
            json_file_path: JSON檔案路徑
            
        Returns:
            處理完成的數據集
        """
        try:
            print(f"[TRACK_PROCESSOR] 開始處理完整數據集: {json_file_path}")
            
            # 1. 解析JSON
            raw_data = self.parse_cli_json_output(json_file_path)
            if not raw_data:
                return None
            
            # 2. 提取位置記錄
            position_records = self.extract_position_records(raw_data)
            if not position_records:
                print("[ERROR] 沒有有效的位置記錄")
                return None
            
            # 3. 提取賽道邊界
            track_bounds = self.extract_track_bounds(raw_data)
            
            # 4. 正規化座標
            normalized_records = self.normalize_coordinates(position_records)
            
            # 5. 計算統計資訊
            statistics = self.calculate_track_statistics(position_records)
            
            # 6. 計算分段資訊
            segments = self.calculate_track_segments(position_records)
            
            # 7. 組裝完整數據集
            processed_data = {
                'session_info': raw_data.get('session_info', {}),
                'original_position_records': position_records,
                'normalized_position_records': normalized_records,
                'track_bounds': track_bounds,
                'track_statistics': statistics,
                'track_segments': segments,
                'processing_metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'source_file': json_file_path,
                    'total_original_points': len(position_records),
                    'total_normalized_points': len(normalized_records)
                }
            }
            
            print(f"[TRACK_PROCESSOR] 數據處理完成")
            print(f"   原始位置點: {len(position_records)}")
            print(f"   正規化位置點: {len(normalized_records)}")
            print(f"   分段數: {len(segments)}")
            
            return processed_data
            
        except Exception as e:
            print(f"[ERROR] 處理完整數據集失敗: {e}")
            return None
    
    def cache_processed_data(self, processed_data: Dict, cache_key: str) -> bool:
        """
        快取處理後的數據
        
        Args:
            processed_data: 處理後的數據
            cache_key: 快取鍵值
            
        Returns:
            快取是否成功
        """
        try:
            cache_file = os.path.join(self.cache_dir, f"track_data_{cache_key}.json")
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            print(f"[TRACK_PROCESSOR] 數據已快取至: {cache_file}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 快取數據失敗: {e}")
            return False
    
    def load_cached_data(self, cache_key: str) -> Optional[Dict]:
        """
        載入快取的數據
        
        Args:
            cache_key: 快取鍵值
            
        Returns:
            快取的數據，沒有時返回None
        """
        try:
            cache_file = os.path.join(self.cache_dir, f"track_data_{cache_key}.json")
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            print(f"[TRACK_PROCESSOR] 從快取載入數據: {cache_file}")
            return cached_data
            
        except Exception as e:
            print(f"[ERROR] 載入快取數據失敗: {e}")
            return None
    
    def get_processing_summary(self) -> Dict:
        """獲取處理摘要"""
        return {
            'last_processed_data_available': self.last_processed_data is not None,
            'processing_stats': self.processing_stats.copy(),
            'cache_dir': self.cache_dir
        }

# 輔助函數
def generate_cache_key(year: int, race: str, session: str, driver: str = None) -> str:
    """
    生成快取鍵值
    
    Args:
        year: 年份
        race: 比賽
        session: 會話
        driver: 車手（可選）
        
    Returns:
        快取鍵值字串
    """
    key_parts = [str(year), race, session]
    if driver:
        key_parts.append(driver)
    
    return "_".join(key_parts)

if __name__ == "__main__":
    # 測試程式碼
    processor = TrackDataProcessor()
    
    # 測試數據處理
    test_json = "cache/position_analysis_2025_Japan_R_VER.json"
    if os.path.exists(test_json):
        result = processor.process_complete_dataset(test_json)
        if result:
            print("測試成功！")
            summary = processor.get_processing_summary()
            print(f"處理摘要: {summary}")
        else:
            print("測試失敗！")
    else:
        print(f"測試檔案不存在: {test_json}")
