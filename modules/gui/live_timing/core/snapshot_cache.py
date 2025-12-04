"""
Live Timing 快照快取管理器
===========================

提供預處理快照的快取讀寫功能，大幅加速 Historical 模式的載入速度。

快取策略：
- 首次載入：完整處理 + 儲存快取 (~30秒)
- 後續載入：直接讀取快取 (~2秒)

快取檔案位置：
- json/LiveF1/{year}/{race}_Race/_aligned_cache.pkl

Author: F1T Team
Date: 2025-12-04
"""

import os
import pickle
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class SnapshotCache:
    """
    快照快取管理器
    
    負責：
    - 檢查快取是否存在且有效
    - 讀取已快取的對齊快照
    - 儲存新處理的快照到快取
    """
    
    CACHE_VERSION = "1.0"
    CACHE_FILENAME = "_aligned_cache.pkl"
    
    def __init__(self, data_dir: str):
        """
        初始化快取管理器
        
        Args:
            data_dir: 賽事數據目錄 (例如 json/LiveF1/2025/Qatar_Race)
        """
        self.data_dir = Path(data_dir)
        self.cache_path = self.data_dir / self.CACHE_FILENAME
    
    def get_cache_info(self) -> Optional[Dict[str, Any]]:
        """
        獲取快取資訊（不載入完整數據）
        
        Returns:
            快取元數據，如果快取不存在則返回 None
        """
        if not self.cache_path.exists():
            return None
        
        try:
            with open(self.cache_path, 'rb') as f:
                data = pickle.load(f)
            
            return {
                'version': data.get('version'),
                'created_at': data.get('created_at'),
                'source_hash': data.get('source_hash'),
                'snapshot_count': len(data.get('snapshots', [])),
                'race_info': data.get('race_info'),
                'cache_size_mb': self.cache_path.stat().st_size / (1024 * 1024)
            }
        except Exception as e:
            print(f"[CACHE] 讀取快取資訊失敗: {e}")
            return None
    
    def is_cache_valid(self) -> bool:
        """
        檢查快取是否有效
        
        驗證條件：
        1. 快取檔案存在
        2. 版本號匹配
        3. 源檔案未變更（通過 hash 檢查）
        """
        if not self.cache_path.exists():
            print("[CACHE] 快取不存在")
            return False
        
        try:
            with open(self.cache_path, 'rb') as f:
                data = pickle.load(f)
            
            # 檢查版本
            if data.get('version') != self.CACHE_VERSION:
                print(f"[CACHE] 版本不匹配: {data.get('version')} != {self.CACHE_VERSION}")
                return False
            
            # 檢查源檔案 hash
            current_hash = self._calculate_source_hash()
            cached_hash = data.get('source_hash')
            
            if current_hash != cached_hash:
                print("[CACHE] 源檔案已變更，快取失效")
                return False
            
            print(f"[CACHE] 快取有效 (建立於 {data.get('created_at')})")
            return True
            
        except Exception as e:
            print(f"[CACHE] 驗證快取失敗: {e}")
            return False
    
    def load_cache(self) -> Optional[Dict[str, Any]]:
        """
        載入快取數據
        
        Returns:
            包含所有快取數據的字典:
            {
                'snapshots': [...],
                'race_info': {...},
                'driver_info': {...},
                'pit_events': [...],
                'driver_stints': {...},
                'tyre_state_index': {...},
                'tyre_timestamps': [...]
            }
        """
        if not self.is_cache_valid():
            return None
        
        try:
            start_time = time.time()
            
            with open(self.cache_path, 'rb') as f:
                data = pickle.load(f)
            
            load_time = time.time() - start_time
            snapshot_count = len(data.get('snapshots', []))
            
            print(f"[CACHE] 快取載入完成: {snapshot_count} 個快照, {load_time:.2f} 秒")
            
            return data
            
        except Exception as e:
            print(f"[CACHE] 載入快取失敗: {e}")
            return None
    
    def save_cache(self, 
                   snapshots: List[Dict[str, Any]],
                   race_info: Dict[str, Any],
                   driver_info: Dict[str, Dict[str, str]],
                   pit_events: List[Dict[str, Any]],
                   driver_stints: Dict[str, List[Dict[str, Any]]],
                   tyre_state_index: Dict[str, Dict[str, Dict[str, Any]]],
                   tyre_timestamps: List[str],
                   race_control_messages: List[Dict[str, Any]] = None,
                   track_status: List[Dict[str, Any]] = None) -> bool:
        """
        儲存快取數據
        
        Args:
            snapshots: 對齊後的快照列表
            race_info: 賽事資訊
            driver_info: 車手資訊
            pit_events: PIT 事件
            driver_stints: 車手輪胎策略
            tyre_state_index: 輪胎狀態索引
            tyre_timestamps: 輪胎狀態時間戳
            race_control_messages: 比賽控制訊息
            track_status: 賽道狀態資料
            
        Returns:
            是否儲存成功
        """
        try:
            start_time = time.time()
            
            cache_data = {
                'version': self.CACHE_VERSION,
                'created_at': datetime.now().isoformat(),
                'source_hash': self._calculate_source_hash(),
                'snapshots': snapshots,
                'race_info': race_info,
                'driver_info': driver_info,
                'pit_events': pit_events,
                'driver_stints': driver_stints,
                'tyre_state_index': tyre_state_index,
                'tyre_timestamps': tyre_timestamps,
                'race_control_messages': race_control_messages or [],
                'track_status': track_status or []
            }
            
            with open(self.cache_path, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            save_time = time.time() - start_time
            cache_size = self.cache_path.stat().st_size / (1024 * 1024)
            
            print(f"[CACHE] 快取儲存完成: {len(snapshots)} 個快照")
            print(f"[CACHE] 檔案大小: {cache_size:.2f} MB, 耗時: {save_time:.2f} 秒")
            
            return True
            
        except Exception as e:
            print(f"[CACHE] 儲存快取失敗: {e}")
            return False
    
    def invalidate_cache(self) -> bool:
        """
        使快取失效（刪除快取檔案）
        
        Returns:
            是否成功刪除
        """
        try:
            if self.cache_path.exists():
                self.cache_path.unlink()
                print("[CACHE] 快取已刪除")
            return True
        except Exception as e:
            print(f"[CACHE] 刪除快取失敗: {e}")
            return False
    
    def _calculate_source_hash(self) -> str:
        """
        計算源檔案的 hash 值
        
        使用關鍵檔案的大小和修改時間來計算 hash，
        避免讀取大檔案內容。
        """
        key_files = [
            "Position.json",
            "CarData.json", 
            "TimingData.json",
            "TimingAppData.json"
        ]
        
        hash_input = []
        
        for filename in key_files:
            filepath = self.data_dir / filename
            if filepath.exists():
                stat = filepath.stat()
                hash_input.append(f"{filename}:{stat.st_size}:{stat.st_mtime}")
        
        hash_str = "|".join(hash_input)
        return hashlib.md5(hash_str.encode()).hexdigest()


def preprocess_race_data(year: int, race: str, force: bool = False) -> bool:
    """
    預處理單場賽事數據並建立快取
    
    Args:
        year: 年份
        race: 賽事名稱
        force: 是否強制重建快取
        
    Returns:
        是否成功
    """
    from .local_source import LocalLiveF1DataSource
    from .position_processor import LivePositionDataProcessor
    
    print(f"\n{'='*70}")
    print(f"預處理賽事數據: {year} {race}")
    print(f"{'='*70}")
    
    # 初始化數據源
    data_source = LocalLiveF1DataSource(year, race)
    cache = SnapshotCache(data_source.data_dir)
    
    # 檢查快取
    if not force and cache.is_cache_valid():
        print("[PREPROCESS] 快取已存在且有效，跳過處理")
        return True
    
    # 載入原始數據
    print("[PREPROCESS] 載入原始數據...")
    start_time = time.time()
    
    if not data_source.load_all_data():
        print("[PREPROCESS] 數據載入失敗")
        return False
    
    load_time = time.time() - start_time
    print(f"[PREPROCESS] 數據載入完成: {load_time:.2f} 秒")
    
    # 處理數據
    print("[PREPROCESS] 處理並對齊數據...")
    process_start = time.time()
    
    processor = LivePositionDataProcessor(data_source)
    processor.process_and_align_data()
    
    process_time = time.time() - process_start
    print(f"[PREPROCESS] 數據處理完成: {process_time:.2f} 秒")
    
    # 獲取處理結果
    snapshots = processor.get_aligned_snapshots()
    
    if not snapshots:
        print("[PREPROCESS] 無可用快照")
        return False
    
    # 建立賽事資訊
    race_info = {
        'year': year,
        'race': race,
        'session': 'Race',
        'total_snapshots': len(snapshots),
        'duration_seconds': (
            snapshots[-1]['race_time_seconds'] - 
            snapshots[0]['race_time_seconds']
        ) if snapshots else 0,
    }
    
    # 儲存快取
    print("[PREPROCESS] 儲存快取...")
    
    success = cache.save_cache(
        snapshots=snapshots,
        race_info=race_info,
        driver_info=processor.get_driver_info(),
        pit_events=processor.get_pit_events(),
        driver_stints=processor.get_driver_stints(),
        tyre_state_index=processor._tyre_state_index,
        tyre_timestamps=processor._tyre_timestamps,
        race_control_messages=data_source.get_race_control_messages() if hasattr(data_source, 'get_race_control_messages') else []
    )
    
    total_time = time.time() - start_time
    print(f"\n[PREPROCESS] 總耗時: {total_time:.2f} 秒")
    
    return success
