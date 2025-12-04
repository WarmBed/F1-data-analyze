"""
Live Timing 數據管理器
=======================

單例模式的數據管理器，負責：
- 載入/卸載賽事數據
- 管理播放狀態
- 發送數據更新信號
- 即時勝率預測

Author: F1T Team
Date: 2025-12-03
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# 勝率預測器：延遲導入（避免 numba 與 core.logger 衝突）
WIN_PROBABILITY_AVAILABLE = False
LiveWinProbabilityPredictor = None

def _lazy_import_predictor():
    """延遲導入勝率預測器，避免與 numba 衝突"""
    global WIN_PROBABILITY_AVAILABLE, LiveWinProbabilityPredictor
    if WIN_PROBABILITY_AVAILABLE:
        return True
    try:
        from CLI_modules.cli.prediction.live_win_probability.predictor import LiveWinProbabilityPredictor as _Predictor
        LiveWinProbabilityPredictor = _Predictor
        WIN_PROBABILITY_AVAILABLE = True
        print(f"[DATA_MANAGER] 勝率預測器導入成功")
        return True
    except Exception as e:
        print(f"[DATA_MANAGER] 勝率預測不可用: {type(e).__name__}: {e}")
        return False


class LiveTimingDataManager(QObject):
    """
    Live Timing 數據管理器 - 單例模式
    
    負責統一管理 Live Timing 數據的載入、播放和分發。
    所有 Live Timing MDI 視窗都訂閱此管理器的信號。
    
    信號：
    - snapshot_updated(dict): 數據快照更新
    - race_loaded(dict): 賽事載入完成
    - race_unloaded(): 賽事卸載
    - playback_state_changed(str): 播放狀態改變
    - time_changed(float): 當前時間改變
    - progress_changed(float): 進度改變 (0.0 ~ 1.0)
    """
    
    # 單例實例
    _instance = None
    
    # 信號定義
    snapshot_updated = pyqtSignal(dict)
    # 插值信號: (current_snapshot, next_snapshot, alpha, race_time_seconds)
    # alpha: 0.0~1.0 表示當前時間在兩個快照之間的位置
    interpolation_updated = pyqtSignal(dict, dict, float, float)
    race_loaded = pyqtSignal(dict)
    race_unloaded = pyqtSignal()
    playback_state_changed = pyqtSignal(str)  # 'playing', 'paused', 'stopped'
    time_changed = pyqtSignal(float)
    progress_changed = pyqtSignal(float)
    driver_selected = pyqtSignal(str)  # 車手選擇信號 (driver_num)
    
    _initialized = False  # 類變數層級追蹤初始化狀態
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, parent=None):
        # 避免重複初始化 - 使用類變數而非實例變數
        if LiveTimingDataManager._initialized:
            return
        
        super().__init__(parent)
        LiveTimingDataManager._initialized = True
        
        # 數據源和處理器
        self._data_source = None
        self._processor = None
        
        # 快照列表
        self._snapshots: List[Dict[str, Any]] = []
        self._current_index: int = 0
        
        # 播放狀態
        self._playback_state: str = 'stopped'  # 'playing', 'paused', 'stopped'
        self._playback_speed: float = 1.0
        
        # 賽事資訊
        self._race_info: Optional[Dict[str, Any]] = None
        
        # 播放計時器
        self._playback_timer = QTimer(self)
        self._playback_timer.timeout.connect(self._on_playback_tick)
        self._timer_interval_ms = 50  # 固定 50ms (20 FPS UI 更新)
        
        # 真實時間播放相關（與 Demo 一致）
        self._playback_time: float = 0.0  # 當前播放的賽事時間 (秒)
        self._last_tick_time: float = 0.0  # 上次 tick 的系統時間
        
        # 調試計數器
        self._debug_update_count: int = 0
        self._debug_last_report_time: float = 0.0
        self._debug_updates_since_report: int = 0
        
        # 賽道資料
        self._track_data: Optional[Dict[str, Any]] = None
        
        # 快取輪胎狀態索引（從快取載入時使用）
        self._cached_tyre_state_index: Dict[str, Dict[str, Any]] = {}
        self._cached_tyre_timestamps: List[str] = []
        
        # 勝率預測器
        self._win_predictor: Optional['LiveWinProbabilityPredictor'] = None
        self._cached_predictions: Dict[str, Dict[str, float]] = {}
        self._last_prediction_lap: int = -1
        self._init_win_predictor()
        
        print("[DATA_MANAGER] LiveTimingDataManager 初始化完成")
    
    def _init_win_predictor(self):
        """初始化勝率預測器"""
        # 延遲導入
        if not _lazy_import_predictor():
            print("[DATA_MANAGER] 勝率預測不可用")
            return
            
        try:
            self._win_predictor = LiveWinProbabilityPredictor()
            
            # 尋找模型檔案
            root_dir = Path(__file__).parent.parent.parent.parent.parent
            model_path = root_dir / 'models' / 'win_probability_xgb_v2.pkl'
            
            if model_path.exists():
                if self._win_predictor.load_model(str(model_path)):
                    print(f"[DATA_MANAGER] 勝率模型載入成功: {model_path}")
                else:
                    print(f"[DATA_MANAGER] 勝率模型載入失敗")
                    self._win_predictor = None
            else:
                print(f"[DATA_MANAGER] 找不到勝率模型: {model_path}")
                self._win_predictor = None
        except Exception as e:
            print(f"[DATA_MANAGER] 初始化勝率預測器失敗: {e}")
            self._win_predictor = None
    
    @classmethod
    def instance(cls) -> 'LiveTimingDataManager':
        """獲取單例實例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ===========================================
    # 賽事載入/卸載
    # ===========================================
    def load_race(self, year: int, race: str, session: str = "Race", 
                  source_type: str = "local", progress_callback=None) -> bool:
        """
        載入賽事數據（優先使用 PKL 快取，若不存在則從官方 API 下載）
        
        載入策略（2025-12-04 更新）：
        1. 檢查 PKL 快取是否存在且有效
        2. 如果 PKL 快取有效 → 直接讀取 PKL (~1-2秒)
        3. 如果 PKL 快取無效 → 從 F1 官方 API 下載 → 處理 → 儲存 PKL
        4. 向後相容：若新系統失敗，嘗試舊的本地 JSON 系統
        
        Args:
            year: 年份
            race: 賽事名稱（支援 "Japan" 或 "Japanese_Race" 格式）
            session: 會話類型
            source_type: 數據源類型 ("local" 舊系統, "api" 新系統, "remote" 網路)
            progress_callback: 可選的進度回調 (percent, message) -> None
            
        Returns:
            是否載入成功
        """
        print(f"[DATA_MANAGER] 載入賽事: {year} {race} {session}")
        
        def _report(percent, msg):
            if progress_callback:
                progress_callback(percent, msg)
        
        # 先卸載現有賽事
        if self._race_info is not None:
            self.unload_race()
        
        try:
            _report(5, "Checking PKL cache...")
            
            # ===== 新系統：使用 F1APIDownloader =====
            from .f1_api_downloader import F1APIDownloader
            
            downloader = F1APIDownloader()
            
            # 檢查 PKL 快取
            if downloader.is_cache_valid(year, race, session):
                print("[DATA_MANAGER] 使用 PKL 快取")
                _report(10, "Loading from PKL cache...")
                
                cache_data = downloader.load_cache(year, race, session)
                if cache_data:
                    return self._load_from_pkl_cache(cache_data, year, race, session, _report)
            
            # PKL 快取不存在，嘗試從官方 API 下載
            print("[DATA_MANAGER] PKL 快取不存在，從官方 API 下載...")
            _report(10, "Downloading from F1 API...")
            
            # 使用 F1APIDownloader 下載並處理
            cache_data = downloader.download_and_cache(
                year, race, session, 
                force=False,
                progress_callback=_report
            )
            
            if cache_data:
                return self._load_from_pkl_cache(cache_data, year, race, session, _report)
            
            # ===== 向後相容：舊的本地 JSON 系統 =====
            print("[DATA_MANAGER] 官方 API 下載失敗，嘗試本地 JSON...")
            return self._load_from_legacy_json(year, race, session, source_type, _report)
            
        except Exception as e:
            print(f"[DATA_MANAGER] 載入賽事失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_from_pkl_cache(self, cache_data: dict, year: int, race: str, 
                              session: str, _report) -> bool:
        """
        從 PKL 快取數據載入賽事（新系統）
        
        Args:
            cache_data: PKL 快取數據字典
            year: 年份
            race: 賽事名稱
            session: 會話類型
            _report: 進度報告函數
        """
        try:
            _report(80, "Restoring snapshots...")
            
            self._snapshots = cache_data.get('snapshots', [])
            
            if not self._snapshots:
                print("[DATA_MANAGER] PKL 快取中無快照數據")
                return False
            
            # 確保每個 snapshot 都有 current_lap
            for snapshot in self._snapshots:
                if 'current_lap' not in snapshot:
                    drivers = snapshot.get('drivers', {})
                    current_lap = 0
                    for driver_data in drivers.values():
                        lap = driver_data.get('lap', 0)
                        if lap and lap > current_lap:
                            current_lap = lap
                    snapshot['current_lap'] = current_lap
            
            _report(90, "Restoring metadata...")
            
            # 恢復輪胎狀態索引
            self._cached_tyre_state_index = cache_data.get('tyre_state_index', {})
            self._cached_tyre_timestamps = cache_data.get('tyre_timestamps', [])
            
            # 恢復比賽控制訊息
            self._cached_race_control_messages = cache_data.get('race_control_messages', [])
            
            # 恢復賽道狀態資料
            self._cached_track_status = cache_data.get('track_status', [])
            
            # 重置狀態
            self._current_index = 0
            self._playback_state = 'stopped'
            
            # 從快取獲取賽事資訊
            cached_race_info = cache_data.get('race_info', {})
            total_laps = cached_race_info.get('total_laps', 0)
            
            # 如果沒有 total_laps，重新計算
            if not total_laps and self._snapshots:
                last_snapshot = self._snapshots[-1]
                for driver_data in last_snapshot.get('drivers', {}).values():
                    lap = driver_data.get('lap', 0)
                    if lap and lap > total_laps:
                        total_laps = lap
            
            # 設置賽事資訊
            self._race_info = {
                'year': year,
                'race': race,
                'session': session,
                'circuit': race,  # 使用 race 名稱作為 circuit key (e.g., 'Qatar', 'Japan')
                'total_snapshots': len(self._snapshots),
                'total_laps': total_laps,
                'duration_seconds': cached_race_info.get('duration_seconds', 0),
                'driver_info': cache_data.get('driver_info', {}),
                'pit_events': cache_data.get('pit_events', []),
                'driver_stints': cache_data.get('driver_stints', {}),
            }
            
            _report(95, "Finalizing...")
            
            print(f"[DATA_MANAGER] 從 PKL 快取載入 {len(self._snapshots)} 個快照")
            
            _report(100, "Loaded from PKL cache")
            
            # 發送載入完成信號
            self.race_loaded.emit(self._race_info)
            
            # 發送第一個快照
            if self._snapshots:
                self.snapshot_updated.emit(self._snapshots[0])
                self.time_changed.emit(self._snapshots[0]['race_time_seconds'])
                self.progress_changed.emit(0.0)
            
            return True
            
        except Exception as e:
            print(f"[DATA_MANAGER] 從 PKL 快取載入失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_from_legacy_json(self, year: int, race: str, session: str,
                                source_type: str, _report) -> bool:
        """
        從舊的本地 JSON 系統載入（向後相容）
        
        這是原來的載入邏輯，作為新系統的備用方案。
        """
        try:
            _report(10, "Loading from legacy JSON...")
            
            # 初始化數據源
            if source_type == "local":
                from .local_source import LocalLiveF1DataSource
                self._data_source = LocalLiveF1DataSource(year, race)
            else:
                from .local_source import LiveF1DataSource
                self._data_source = LiveF1DataSource(year, race, session)
            
            # 嘗試舊的快取系統
            from .snapshot_cache import SnapshotCache
            cache = SnapshotCache(self._data_source.data_dir)
            
            if cache.is_cache_valid():
                _report(15, "Loading from legacy cache...")
                cache_data = cache.load_cache()
                
                if cache_data:
                    return self._load_from_cache(cache_data, year, race, session, _report)
            
            # 執行完整處理流程
            print("[DATA_MANAGER] 舊快取無效，執行完整處理...")
            _report(20, "Loading JSON files...")
            
            def file_progress(current, total, filename):
                percent = 20 + int((current / total) * 30) if total > 0 else 20
                _report(percent, f"Loading {filename}...")
            
            if not self._data_source.load_all_data(progress_callback=file_progress):
                print("[DATA_MANAGER] JSON 數據載入失敗")
                return False
            
            _report(55, "Processing position data...")
            
            from .position_processor import LivePositionDataProcessor
            self._processor = LivePositionDataProcessor(self._data_source)
            
            def processor_progress(percent, msg):
                mapped_percent = 55 + int(percent * 0.35)
                _report(mapped_percent, msg)
            
            self._processor.process_and_align_data(progress_callback=processor_progress)
            
            _report(92, "Building snapshots...")
            self._snapshots = self._processor.get_aligned_snapshots()
            
            if not self._snapshots:
                print("[DATA_MANAGER] 無可用快照")
                return False
            
            print(f"[DATA_MANAGER] 載入 {len(self._snapshots)} 個快照")
            
            # 儲存舊格式快取
            _report(94, "Saving legacy cache...")
            
            race_info_for_cache = {
                'year': year,
                'race': race,
                'session': session,
                'total_snapshots': len(self._snapshots),
                'duration_seconds': (
                    self._snapshots[-1]['race_time_seconds'] - 
                    self._snapshots[0]['race_time_seconds']
                ) if self._snapshots else 0,
            }
            
            cache.save_cache(
                snapshots=self._snapshots,
                race_info=race_info_for_cache,
                driver_info=self._processor.get_driver_info(),
                pit_events=self._processor.get_pit_events(),
                driver_stints=self._processor.get_driver_stints(),
                tyre_state_index=self._processor._tyre_state_index,
                tyre_timestamps=self._processor._tyre_timestamps,
                race_control_messages=self._data_source.get_race_control_messages() if hasattr(self._data_source, 'get_race_control_messages') else [],
                track_status=self._data_source.get_track_status() if hasattr(self._data_source, 'get_track_status') else []
            )
            
            _report(96, "Finalizing...")
            
            self._current_index = 0
            self._playback_state = 'stopped'
            
            total_laps = 0
            if self._snapshots:
                last_snapshot = self._snapshots[-1]
                for driver_data in last_snapshot.get('drivers', {}).values():
                    lap = driver_data.get('lap', 0)
                    if lap and lap > total_laps:
                        total_laps = lap
            
            self._race_info = {
                'year': year,
                'race': race,
                'session': session,
                'circuit': race,  # 使用 race 名稱作為 circuit key
                'total_snapshots': len(self._snapshots),
                'total_laps': total_laps,
                'duration_seconds': (
                    self._snapshots[-1]['race_time_seconds'] - 
                    self._snapshots[0]['race_time_seconds']
                ) if self._snapshots else 0,
                'driver_info': self._processor.get_driver_info(),
                'pit_events': self._processor.get_pit_events(),
                'driver_stints': self._processor.get_driver_stints(),
            }
            
            _report(100, "Loaded from legacy JSON")
            
            self.race_loaded.emit(self._race_info)
            
            if self._snapshots:
                self.snapshot_updated.emit(self._snapshots[0])
                self.time_changed.emit(self._snapshots[0]['race_time_seconds'])
                self.progress_changed.emit(0.0)
            
            return True
            
        except Exception as e:
            print(f"[DATA_MANAGER] 從舊系統載入失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_from_cache(self, cache_data: dict, year: int, race: str, 
                         session: str, _report) -> bool:
        """
        從快取數據載入賽事
        
        Args:
            cache_data: 快取數據字典
            year: 年份
            race: 賽事名稱
            session: 會話類型
            _report: 進度報告函數
        """
        try:
            _report(50, "Restoring snapshots...")
            
            self._snapshots = cache_data.get('snapshots', [])
            
            if not self._snapshots:
                print("[DATA_MANAGER] 快取中無快照數據")
                return False
            
            # 確保每個 snapshot 都有 current_lap（相容舊快取）
            for snapshot in self._snapshots:
                if 'current_lap' not in snapshot:
                    drivers = snapshot.get('drivers', {})
                    current_lap = 0
                    for driver_data in drivers.values():
                        lap = driver_data.get('lap', 0)
                        if lap and lap > current_lap:
                            current_lap = lap
                    snapshot['current_lap'] = current_lap
            
            _report(80, "Restoring metadata...")
            
            # 恢復輪胎狀態索引（用於 get_tyre_state_at_time）
            self._cached_tyre_state_index = cache_data.get('tyre_state_index', {})
            self._cached_tyre_timestamps = cache_data.get('tyre_timestamps', [])
            
            # 恢復比賽控制訊息
            self._cached_race_control_messages = cache_data.get('race_control_messages', [])
            
            # 恢復賽道狀態資料
            self._cached_track_status = cache_data.get('track_status', [])
            
            # 重置狀態
            self._current_index = 0
            self._playback_state = 'stopped'
            
            # 計算總圈數（從最後一個 snapshot 獲取）
            total_laps = 0
            if self._snapshots:
                last_snapshot = self._snapshots[-1]
                for driver_data in last_snapshot.get('drivers', {}).values():
                    lap = driver_data.get('lap', 0)
                    if lap and lap > total_laps:
                        total_laps = lap
            
            # 設置賽事資訊
            cached_race_info = cache_data.get('race_info', {})
            self._race_info = {
                'year': year,
                'race': race,
                'session': session,
                'circuit': race,  # 使用 race 名稱作為 circuit key
                'total_snapshots': len(self._snapshots),
                'total_laps': total_laps,
                'duration_seconds': cached_race_info.get('duration_seconds', 0),
                'driver_info': cache_data.get('driver_info', {}),
                'pit_events': cache_data.get('pit_events', []),
                'driver_stints': cache_data.get('driver_stints', {}),
            }
            
            _report(95, "Finalizing...")
            
            print(f"[DATA_MANAGER] 從快取載入 {len(self._snapshots)} 個快照")
            
            _report(100, "Loaded from cache")
            
            # 發送載入完成信號
            self.race_loaded.emit(self._race_info)
            
            # 發送第一個快照
            if self._snapshots:
                self.snapshot_updated.emit(self._snapshots[0])
                self.time_changed.emit(self._snapshots[0]['race_time_seconds'])
                self.progress_changed.emit(0.0)
            
            return True
            
        except Exception as e:
            print(f"[DATA_MANAGER] 從快取載入失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unload_race(self):
        """卸載當前賽事"""
        print("[DATA_MANAGER] 卸載賽事")
        
        # 停止播放
        self.stop()
        
        # 清空數據
        self._data_source = None
        self._processor = None
        self._snapshots = []
        self._current_index = 0
        self._race_info = None
        self._track_data = None
        
        # 發送卸載信號
        self.race_unloaded.emit()
    
    # ===========================================
    # 播放控制
    # ===========================================
    def play(self):
        """開始播放 - 使用真實時間模擬（與 Demo 一致）"""
        import time
        
        if not self._snapshots:
            return
        
        self._playback_state = 'playing'
        
        # 初始化播放時間為當前快照的賽事時間
        if 0 <= self._current_index < len(self._snapshots):
            self._playback_time = self._snapshots[self._current_index].get('race_time_seconds', 0.0)
        else:
            self._playback_time = 0.0
        
        # 記錄開始時的系統時間
        self._last_tick_time = time.time()
        
        # 使用固定 50ms 間隔（與 Demo 一致）
        self._playback_timer.start(self._timer_interval_ms)
        self.playback_state_changed.emit('playing')
        print(f"[DATA_MANAGER] 開始播放，初始賽事時間: {self._playback_time:.2f}s")
    
    def pause(self):
        """暫停播放"""
        self._playback_state = 'paused'
        self._playback_timer.stop()
        self.playback_state_changed.emit('paused')
        print("[DATA_MANAGER] 暫停播放")
    
    def stop(self):
        """停止播放"""
        self._playback_state = 'stopped'
        self._playback_timer.stop()
        self._current_index = 0
        self.playback_state_changed.emit('stopped')
        
        # 重置到開始
        if self._snapshots:
            self.snapshot_updated.emit(self._snapshots[0])
            self.time_changed.emit(self._snapshots[0]['race_time_seconds'])
            self.progress_changed.emit(0.0)
        
        print("[DATA_MANAGER] 停止播放")
    
    def set_speed(self, speed: float):
        """
        設置播放速度
        
        Args:
            speed: 播放速度倍率 (0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0)
        """
        self._playback_speed = max(0.1, min(128.0, speed))
        
        # 固定 50ms timer 間隔，速度通過時間計算控制（與 Demo 一致）
        # 不需要調整 timer 間隔
        
        print(f"[DATA_MANAGER] 播放速度: {self._playback_speed}x")
    
    def seek(self, time_seconds: float):
        """
        跳轉到指定時間
        
        Args:
            time_seconds: 目標時間（秒）
        """
        if not self._snapshots:
            return
        
        # 二分查找最接近的快照
        target_index = self._find_snapshot_by_time(time_seconds)
        self._current_index = target_index
        
        snapshot = self._snapshots[self._current_index]
        self.snapshot_updated.emit(snapshot)
        self.time_changed.emit(snapshot['race_time_seconds'])
        
        # 計算進度
        progress = self._current_index / max(1, len(self._snapshots) - 1)
        self.progress_changed.emit(progress)
    
    def seek_by_progress(self, progress: float):
        """
        根據進度跳轉
        
        Args:
            progress: 進度 (0.0 ~ 1.0)
        """
        if not self._snapshots:
            return
        
        target_index = int(progress * (len(self._snapshots) - 1))
        target_index = max(0, min(len(self._snapshots) - 1, target_index))
        self._current_index = target_index
        
        snapshot = self._snapshots[self._current_index]
        self.snapshot_updated.emit(snapshot)
        self.time_changed.emit(snapshot['race_time_seconds'])
        self.progress_changed.emit(progress)
    
    # ===========================================
    # 數據存取
    # ===========================================
    def get_current_snapshot(self) -> Optional[Dict[str, Any]]:
        """獲取當前快照"""
        if self._snapshots and 0 <= self._current_index < len(self._snapshots):
            return self._snapshots[self._current_index]
        return None
    
    def get_race_info(self) -> Optional[Dict[str, Any]]:
        """獲取賽事資訊"""
        return self._race_info
    
    def get_driver_info(self) -> Dict[str, Dict[str, str]]:
        """獲取車手資訊"""
        if self._processor:
            return self._processor.get_driver_info()
        return {}
    
    def get_tyre_state_at_time(self, timestamp: str) -> Dict[str, Dict[str, Any]]:
        """
        獲取指定時間的輪胎狀態
        
        優先使用 processor，如果 processor 不存在則使用快取的索引
        """
        # 優先使用 processor（正常載入時）
        if self._processor:
            return self._processor.get_tyre_state_at_time(timestamp)
        
        # 使用快取的輪胎狀態索引（從快取載入時）
        if self._cached_tyre_timestamps:
            return self._get_tyre_state_from_cache(timestamp)
        
        return {}
    
    def _get_tyre_state_from_cache(self, timestamp: str) -> Dict[str, Dict[str, Any]]:
        """從快取索引中獲取輪胎狀態"""
        if not self._cached_tyre_timestamps:
            return {}
        
        target_seconds = self._time_str_to_seconds(timestamp)
        if target_seconds is None:
            return {}
        
        # 找到最接近的時間戳（小於等於目標時間）
        target_ts = None
        for ts in self._cached_tyre_timestamps:
            ts_seconds = self._time_str_to_seconds(ts)
            if ts_seconds is not None and ts_seconds <= target_seconds:
                target_ts = ts
            elif ts_seconds is not None and ts_seconds > target_seconds:
                break
        
        if target_ts and target_ts in self._cached_tyre_state_index:
            return self._cached_tyre_state_index[target_ts]
        
        return {}
    
    def _time_str_to_seconds(self, time_str: str) -> Optional[float]:
        """將時間字串轉換為秒數"""
        if not time_str:
            return None
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return int(minutes) * 60 + float(seconds)
        except (ValueError, IndexError):
            pass
        return None
    
    def get_tyre_state(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取當前時間的輪胎狀態
        
        Returns:
            {driver_num: {compound, new, stint_count, tyre_age, stints}}
        """
        if self._current_index >= 0 and self._current_index < len(self._snapshots):
            current_snapshot = self._snapshots[self._current_index]
            timestamp = current_snapshot.get('race_time', '')
            if timestamp:
                return self.get_tyre_state_at_time(timestamp)
        return {}
    
    def get_track_status_at_time(self, timestamp: str) -> str:
        """獲取指定時間的賽道狀態"""
        # 優先使用 processor（完整載入模式）
        if self._processor:
            return self._processor.get_track_status_at_time(timestamp)
        
        # 使用快取的 track_status（快取載入模式）
        if hasattr(self, '_cached_track_status') and self._cached_track_status:
            return self._get_track_status_from_cache(timestamp)
        
        return "1"
    
    def _get_track_status_from_cache(self, timestamp: str) -> str:
        """從快取的 track_status 資料查詢狀態"""
        from .position_processor import LivePositionDataProcessor
        
        target_seconds = LivePositionDataProcessor._time_str_to_seconds(timestamp)
        if target_seconds is None:
            return "1"
        
        current_status = "1"
        for record in self._cached_track_status:
            ts = record.get('timestamp', '')
            ts_seconds = LivePositionDataProcessor._time_str_to_seconds(ts)
            if ts_seconds is not None and ts_seconds <= target_seconds:
                data = record.get('data', {})
                status = data.get('Status')
                if status:
                    current_status = str(status)
            elif ts_seconds is not None and ts_seconds > target_seconds:
                break
        
        return current_status
    
    def get_race_control_messages(self) -> List[Dict[str, Any]]:
        """獲取比賽控制訊息"""
        # 先檢查快取
        if hasattr(self, '_cached_race_control_messages') and self._cached_race_control_messages:
            return self._cached_race_control_messages
        # 否則從數據源獲取
        if self._data_source and hasattr(self._data_source, 'get_race_control_messages'):
            return self._data_source.get_race_control_messages()
        return []
    
    def is_race_loaded(self) -> bool:
        """檢查是否已載入賽事"""
        return self._race_info is not None
    
    def get_playback_state(self) -> str:
        """獲取播放狀態"""
        return self._playback_state
    
    def get_playback_speed(self) -> float:
        """獲取播放速度"""
        return self._playback_speed
    
    def get_total_snapshots(self) -> int:
        """獲取快照總數"""
        return len(self._snapshots)
    
    def get_current_index(self) -> int:
        """獲取當前快照索引"""
        return self._current_index
    
    # ===========================================
    # 賽道資料
    # ===========================================
    def load_track_data(self, track_json_path: str) -> bool:
        """
        載入賽道資料
        
        Args:
            track_json_path: 賽道 JSON 檔案路徑
        """
        try:
            import json
            with open(track_json_path, 'r', encoding='utf-8') as f:
                self._track_data = json.load(f)
            print(f"[DATA_MANAGER] 賽道資料載入完成: {track_json_path}")
            return True
        except Exception as e:
            print(f"[DATA_MANAGER] 載入賽道資料失敗: {e}")
            return False
    
    def get_track_data(self) -> Optional[Dict[str, Any]]:
        """獲取賽道資料"""
        return self._track_data
    
    def _update_win_probabilities(self, snapshot: Dict[str, Any]):
        """
        計算並更新 snapshot 中的勝率數據
        
        每圈更新一次勝率預測（避免頻繁計算）
        """
        if not self._win_predictor:
            return
        
        drivers = snapshot.get('drivers', {})
        if not drivers:
            return
        
        # 獲取當前圈數（只在圈數變化時重新計算）
        current_lap = 0
        for driver_data in drivers.values():
            lap = driver_data.get('lap', 0)
            if lap and lap > current_lap:
                current_lap = lap
        
        # 如果圈數沒變，使用緩存
        if current_lap == self._last_prediction_lap and self._cached_predictions:
            for driver_num, probs in self._cached_predictions.items():
                if driver_num in drivers:
                    drivers[driver_num]['win_probability'] = probs.get('win_prob', 0) * 100
                    drivers[driver_num]['p2_probability'] = probs.get('p2_prob', 0) * 100
                    drivers[driver_num]['p3_probability'] = probs.get('podium_prob', 0) * 100
            return
        
        # 新圈數，重新計算
        try:
            # 準備輪胎狀態
            tyre_state = self.get_tyre_state()
            
            # 準備賽事資訊
            race_info = {
                'total_laps': 60,  # 預設
                'current_lap': current_lap,  # 當前圈數（必須！）
                'circuit': self._race_info.get('race', 'Unknown') if self._race_info else 'Unknown',
            }
            
            # 呼叫預測器
            predictions = self._win_predictor.predict_for_snapshot(snapshot, tyre_state, race_info)
            
            if predictions:
                self._cached_predictions = predictions
                self._last_prediction_lap = current_lap
                
                # 更新 snapshot
                for driver_num, probs in predictions.items():
                    if driver_num in drivers:
                        drivers[driver_num]['win_probability'] = probs.get('win_prob', 0) * 100
                        drivers[driver_num]['p2_probability'] = probs.get('p2_prob', 0) * 100
                        drivers[driver_num]['p3_probability'] = probs.get('podium_prob', 0) * 100
                
                # 調試輸出（每圈只印一次）
                print(f"[DATA_MANAGER] 勝率已更新 (圈 {current_lap}): {len(predictions)} 車手")
            else:
                print(f"[DATA_MANAGER] 勝率預測返回空結果 (圈 {current_lap})")
                
        except Exception as e:
            print(f"[DATA_MANAGER] 勝率預測失敗: {e}")
    
    # ===========================================
    # 內部方法
    # ===========================================
    def _on_playback_tick(self):
        """
        播放計時器回調 - 真實時間模擬（與 Demo 一致）
        
        邏輯：
        1. 計算自上次 tick 經過的真實時間
        2. 乘以播放速度，得到賽事時間增量
        3. 更新播放時間，找到對應的 snapshot
        4. 發送插值信號供平滑動畫使用
        """
        import time
        
        if self._playback_state != 'playing':
            return
        
        if not self._snapshots:
            return
        
        current_time = time.time()
        if self._last_tick_time == 0:
            self._last_tick_time = current_time
            self._debug_last_report_time = current_time
            return
        
        # 計算經過的真實時間 (秒)
        elapsed_real = current_time - self._last_tick_time
        self._last_tick_time = current_time
        
        # 計算賽事時間增量 (乘以播放速度)
        elapsed_race = elapsed_real * self._playback_speed
        self._playback_time += elapsed_race
        
        # 找到對應的 snapshot 索引
        new_index = self._find_snapshot_by_time(self._playback_time)
        
        # 檢查是否到達結尾
        if new_index >= len(self._snapshots) - 1:
            self._current_index = len(self._snapshots) - 1
            self.pause()
            return
        
        # === 插值信號 (每次 tick 都發送) ===
        current_snap = self._snapshots[new_index]
        next_snap = self._snapshots[min(new_index + 1, len(self._snapshots) - 1)]
        
        # 計算插值因子 alpha (0.0 ~ 1.0)
        t0 = current_snap['race_time_seconds']
        t1 = next_snap['race_time_seconds']
        if t1 > t0:
            alpha = (self._playback_time - t0) / (t1 - t0)
            alpha = max(0.0, min(1.0, alpha))
        else:
            alpha = 0.0
        
        # 發送插值信號
        self.interpolation_updated.emit(current_snap, next_snap, alpha, self._playback_time)
        
        # 只有索引變化時才發送完整快照更新
        if new_index != self._current_index:
            self._current_index = new_index
            
            # 取得快照並計算勝率
            snapshot = self._snapshots[self._current_index]
            self._update_win_probabilities(snapshot)
            
            # 發送快照
            self.snapshot_updated.emit(snapshot)
            self.time_changed.emit(snapshot['race_time_seconds'])
            
            # 調試輸出：每秒報告一次更新頻率
            self._debug_update_count += 1
            self._debug_updates_since_report += 1
            
            time_since_report = current_time - self._debug_last_report_time
            if time_since_report >= 1.0:
                updates_per_sec = self._debug_updates_since_report / time_since_report
                print(f"[PLAYBACK_DEBUG] 更新頻率: {updates_per_sec:.1f}/秒 | "
                      f"總更新: {self._debug_update_count} | "
                      f"索引: {new_index}/{len(self._snapshots)} | "
                      f"賽事時間: {snapshot['race_time']} | "
                      f"播放速度: {self._playback_speed}x")
                self._debug_last_report_time = current_time
                self._debug_updates_since_report = 0
            
            # 計算進度
            progress = self._current_index / max(1, len(self._snapshots) - 1)
            self.progress_changed.emit(progress)
    
    def _find_snapshot_by_time(self, time_seconds: float) -> int:
        """二分查找指定時間的快照索引"""
        if not self._snapshots:
            return 0
        
        left, right = 0, len(self._snapshots) - 1
        result = 0
        
        while left <= right:
            mid = (left + right) // 2
            mid_time = self._snapshots[mid]['race_time_seconds']
            
            if mid_time <= time_seconds:
                result = mid
                left = mid + 1
            else:
                right = mid - 1
        
        return result
