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
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from core.logger import get_logger

# F83 超車預測器：延遲導入
OVERTAKE_PREDICTION_AVAILABLE = False
OvertakePredictor = None

# F85 近距離接觸預測器：延遲導入
CLOSE_COMBAT_PREDICTION_AVAILABLE = False
CloseCombatPredictor = None

logger = get_logger("live_timing.data_manager", component="gui")

def _lazy_import_overtake_predictor():
    """延遲導入 F83 超車預測器"""
    global OVERTAKE_PREDICTION_AVAILABLE, OvertakePredictor
    if OVERTAKE_PREDICTION_AVAILABLE:
        return True
    try:
        from CLI_modules.cli.prediction.overtake_prediction.predictor import OvertakePredictor as _OvertakePredictor
        OvertakePredictor = _OvertakePredictor
        OVERTAKE_PREDICTION_AVAILABLE = True
        logger.info("F83 overtake predictor loaded")
        return True
    except Exception as e:
        logger.warning("F83 overtake predictor unavailable: %s: %s", type(e).__name__, e)
        return False

def _lazy_import_close_combat_predictor():
    """延遲導入 F85 近距離接觸預測器"""
    global CLOSE_COMBAT_PREDICTION_AVAILABLE, CloseCombatPredictor
    if CLOSE_COMBAT_PREDICTION_AVAILABLE:
        return True
    try:
        from CLI_modules.cli.prediction.overtake_prediction.close_combat_predictor import CloseCombatPredictor as _CloseCombatPredictor
        CloseCombatPredictor = _CloseCombatPredictor
        CLOSE_COMBAT_PREDICTION_AVAILABLE = True
        logger.info("F85 close combat predictor loaded")
        return True
    except Exception as e:
        logger.warning("F85 close combat predictor unavailable: %s: %s", type(e).__name__, e)
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
        self._timer_interval_ms = 16  # 改為 16ms (60 FPS UI 更新) - 2025-12-10 優化
        
        # 幀計數器（用於跳幀渲染）
        self._frame_counter = 0
        
        # 真實時間播放相關（與 Demo 一致）
        self._playback_time: float = 0.0  # 當前播放的賽事時間 (秒)
        self._last_tick_time: float = 0.0  # 上次 tick 的系統時間
        
        # 比賽起跑時間偏移（用於將第一個快照時間校準為 0:00）
        # 這是第一個快照的 race_time_seconds，用於計算顯示時間
        self._race_start_offset: float = 0.0
        
        # 調試計數器
        self._debug_update_count: int = 0
        self._debug_last_report_time: float = 0.0
        self._debug_updates_since_report: int = 0
        
        # 賽道資料
        self._track_data: Optional[Dict[str, Any]] = None
        
        # 快取輪胎狀態索引（從快取載入時使用）
        self._cached_tyre_state_index: Dict[str, Dict[str, Any]] = {}
        self._cached_tyre_timestamps: List[str] = []
        
        # F83 超車預測器（即時更新，不需要快取）
        self._overtake_predictor: Optional['OvertakePredictor'] = None
        self._init_overtake_predictor()
        
        # F85 近距離接觸預測器（即時更新，不需要快取）
        self._close_combat_predictor: Optional['CloseCombatPredictor'] = None
        self._init_close_combat_predictor()
        
        # ✅ 策略 B：OT%/CC% 緩存機制
        # 格式: {driver_num: {'gap': float, 'lap': int, 'ot%': int, 'cc%': int, 'timestamp': float}}
        self._prediction_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_gap_threshold = 0.1  # 間距變化超過 0.1s 才重新計算
        self._cache_lap_threshold = 1    # 圈數變化才重新計算
        
        # ✅ 策略 A：背景執行緒預測器
        self._prediction_worker = None
        self._init_prediction_worker()
        
        # Gap 歷史追蹤（用於計算趨勢）
        # 改進版：單圈 gap 變化追蹤
        # 格式: {driver_num: {'last_lap': int, 'last_gap': float, 'current_lap': int, 'current_gap': float}}
        self._gap_history: Dict[str, Dict[str, Any]] = {}
        
        # F87 省胎分數 (由 driver_strategy MDI 更新)
        # 格式: {driver_num: {'score': float, 'level': str, 'adjustment': float}}
        self._tire_saving_scores: Dict[str, Dict[str, Any]] = {}
        
        # F87 Throttle 樣本追蹤器 (用於計算 SF%)
        # 格式: {driver_num: {'samples': list, 'current_lap': int}}
        self._driver_throttle_samples: Dict[str, Dict[str, Any]] = {}
        
        # Top Speed 追蹤器 (用於計算每圈最高速)
        # 格式: {driver_num: {'current_lap': int, 'current_max_speed': float, 'lap_top_speeds': {lap: speed}, 'personal_best': float}}
        self._driver_speed_samples: Dict[str, Dict[str, Any]] = {}
        
        logger.info("[DATA_MANAGER] LiveTimingDataManager 初始化完成")
    
    def _init_overtake_predictor(self):
        """初始化 F83 超車預測器"""
        # 延遲導入
        if not _lazy_import_overtake_predictor():
            logger.warning("[DATA_MANAGER] F83 超車預測不可用")
            return
            
        try:
            # OvertakePredictor 會自動尋找最新版本的模型
            self._overtake_predictor = OvertakePredictor(verbose=False)
            
            if self._overtake_predictor.model is not None:
                logger.info("[DATA_MANAGER] F83 超車預測器載入成功 (v%s)", self._overtake_predictor.model_version)
            else:
                logger.error("[DATA_MANAGER] F83 超車預測器模型載入失敗")
                self._overtake_predictor = None
        except Exception as e:
            logger.exception("[DATA_MANAGER] 初始化 F83 超車預測器失敗: %s", e)
            self._overtake_predictor = None
    
    def _init_close_combat_predictor(self):
        """初始化 F85 近距離接觸預測器"""
        # 延遲導入
        if not _lazy_import_close_combat_predictor():
            logger.warning("[DATA_MANAGER] F85 近距離接觸預測不可用")
            return
            
        try:
            # CloseCombatPredictor 會自動尋找最新版本的模型
            self._close_combat_predictor = CloseCombatPredictor(verbose=False)
            
            if self._close_combat_predictor.model is not None:
                logger.info("[DATA_MANAGER] F85 近距離接觸預測器載入成功 (v%s)", self._close_combat_predictor.model_version)
            else:
                logger.error("[DATA_MANAGER] F85 近距離接觸預測器模型載入失敗")
                self._close_combat_predictor = None
        except Exception as e:
            logger.exception("[DATA_MANAGER] 初始化 F85 近距離接觸預測器失敗: %s", e)
            self._close_combat_predictor = None
    
    def _init_prediction_worker(self):
        """✅ 策略 A：初始化背景預測執行緒"""
        if not self._overtake_predictor or not self._close_combat_predictor:
            logger.warning("[DATA_MANAGER] 預測器未就緒，跳過背景執行緒初始化")
            return
        
        try:
            from modules.gui.live_timing.core.prediction_worker import PredictionWorker
            
            self._prediction_worker = PredictionWorker(
                overtake_predictor=self._overtake_predictor,
                close_combat_predictor=self._close_combat_predictor,
                parent=self
            )
            
            # 連接結果信號
            self._prediction_worker.predictions_ready.connect(self._on_predictions_ready)
            
            # 啟動背景執行緒
            self._prediction_worker.start()
            
            logger.info("[DATA_MANAGER] ✅ 策略 A：背景預測執行緒啟動成功")
        except Exception as e:
            logger.exception("[DATA_MANAGER] ❌ 策略 A 失敗: %s", e)
            self._prediction_worker = None
    
    @classmethod
    def instance(cls) -> 'LiveTimingDataManager':
        """獲取單例實例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'LiveTimingDataManager':
        return cls.instance()

    def _get_display_time(self, raw_time: float) -> float:
        """
        計算顯示時間（減去起跑偏移）
        
        將原始 race_time_seconds 轉換為從第一個快照開始計算的顯示時間。
        例如：如果第一個快照是 3600 秒（1小時），則 3660 秒會顯示為 60 秒（1分鐘）。
        
        Args:
            raw_time: 原始的 race_time_seconds
            
        Returns:
            調整後的顯示時間（秒）
        """
        return max(0.0, raw_time - self._race_start_offset)
    
    def _get_raw_time(self, display_time: float) -> float:
        """
        從顯示時間計算原始時間（加上起跑偏移）
        
        Args:
            display_time: 顯示時間（秒）
            
        Returns:
            原始的 race_time_seconds
        """
        return display_time + self._race_start_offset
    
    def get_race_start_offset(self) -> float:
        """
        獲取比賽起跑時間偏移
        
        返回第一個快照的 race_time_seconds，用於將原始時間轉換為顯示時間。
        模組可以使用此值計算：display_time = raw_time - race_start_offset
        
        Returns:
            起跑時間偏移（秒）
        """
        return self._race_start_offset
    
    def _calculate_race_start_offset(self) -> float:
        """
        計算比賽起跑時間偏移
        
        優先順序：
        1. 從 RaceControlMessages 找到 GREEN LIGHT 訊息的時間戳
        2. 如果找不到 GREEN LIGHT，使用第一個快照的時間
        
        Returns:
            起跑時間偏移（秒）
        """
        # 嘗試從 RaceControlMessages 找到 GREEN LIGHT
        green_light_time = self._find_green_light_time()
        if green_light_time is not None:
            logger.info("[DATA_MANAGER] 從 GREEN LIGHT 訊息計算起跑時間: %.2f 秒", green_light_time)
            return green_light_time
        
        # 否則使用第一個快照的時間
        if self._snapshots:
            first_time = self._snapshots[0].get('race_time_seconds', 0.0)
            logger.info("[DATA_MANAGER] 使用第一個快照時間作為起跑時間: %.2f 秒", first_time)
            return first_time
        
        return 0.0
    
    def _find_green_light_time(self) -> Optional[float]:
        """
        從 RaceControlMessages 找到比賽正式開始的 GREEN LIGHT 時間戳
        
        策略：找到最接近但早於第一個快照時間的 GREEN LIGHT
        （因為可能有多個 GREEN LIGHT，第一個是暖胎圈開始，後面的才是正賽開始）
        
        Returns:
            GREEN LIGHT 時間（秒），如果找不到返回 None
        """
        messages = self.get_race_control_messages()
        
        # 獲取第一個快照時間作為參考
        first_snapshot_time = 0.0
        if self._snapshots:
            first_snapshot_time = self._snapshots[0].get('race_time_seconds', 0.0)
        
        green_light_times = []
        
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            
            # 檢查是否是 GREEN LIGHT 訊息
            message_text = msg.get('Message', '').upper()
            flag = msg.get('Flag', '').upper()
            
            # GREEN LIGHT - PIT EXIT OPEN 表示比賽開始
            if 'GREEN' in flag or 'GREEN LIGHT' in message_text:
                # 嘗試從 timestamp 解析時間
                # timestamp 格式可能是 "00:58:20.712" 或 "HH:MM:SS.mmm"
                timestamp = msg.get('timestamp', '')
                if timestamp:
                    try:
                        parts = timestamp.split(':')
                        if len(parts) >= 3:
                            hours = int(parts[0])
                            minutes = int(parts[1])
                            seconds = float(parts[2])
                            total_seconds = hours * 3600 + minutes * 60 + seconds
                            green_light_times.append((total_seconds, msg.get('Message', '')))
                    except (ValueError, IndexError) as e:
                        logger.warning("[DATA_MANAGER] 解析 GREEN LIGHT 時間戳失敗: %s", e)
        
        if not green_light_times:
            logger.info("[DATA_MANAGER] 未找到 GREEN LIGHT 訊息")
            return None
        
        # 排序並找到最接近但早於第一個快照的 GREEN LIGHT
        green_light_times.sort(key=lambda x: x[0])
        
        # 找到最接近第一個快照時間的 GREEN LIGHT（但要早於它）
        best_match = None
        for time_val, msg_text in green_light_times:
            if time_val <= first_snapshot_time:
                best_match = (time_val, msg_text)
            else:
                break  # 已經超過第一個快照時間，停止搜索
        
        if best_match:
            logger.info("[DATA_MANAGER] 找到比賽開始 GREEN LIGHT: '%s' at %.2f 秒 (第一快照: %.2f 秒)", 
                        best_match[1], best_match[0], first_snapshot_time)
            return best_match[0]
        
        # 如果所有 GREEN LIGHT 都晚於第一個快照，使用最早的
        if green_light_times:
            earliest = green_light_times[0]
            logger.info("[DATA_MANAGER] 所有 GREEN LIGHT 都晚於第一快照，使用最早的: '%s' at %.2f 秒", 
                        earliest[1], earliest[0])
            return earliest[0]
        
        return None

    # ===========================================
    # 賽事載入/卸載
    # ===========================================
    def _normalize_race_key(self, race: str) -> str:
        value = str(race or "").strip()
        if not value:
            return value
        value = re.sub(r"\s*\(\d{4}-\d{2}-\d{2}\)\s*$", "", value)
        return value.strip().rstrip(" _-")

    def _local_year_candidates(self, requested_year: int) -> List[int]:
        return [int(requested_year)]

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
        requested_year = int(year)
        race = self._normalize_race_key(race)
        logger.info("[DATA_MANAGER] 載入賽事: %s %s %s", requested_year, race, session)
        
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
            
            year_candidates = [requested_year]
            if source_type == "local":
                year_candidates = self._local_year_candidates(requested_year)

            # 檢查 PKL 快取（local 模式會自動向前回退年度）
            for candidate_year in year_candidates:
                if downloader.is_cache_valid(candidate_year, race, session):
                    logger.info("[DATA_MANAGER] 使用 PKL 快取: %s %s %s", candidate_year, race, session)
                    _report(10, f"Loading from PKL cache ({candidate_year})...")
                    cache_data = downloader.load_cache(candidate_year, race, session)
                    if cache_data:
                        return self._load_from_pkl_cache(cache_data, candidate_year, race, session, _report)

            if source_type == "local":
                for candidate_year in year_candidates:
                    if self._load_from_legacy_json(candidate_year, race, session, source_type, _report):
                        return True
                logger.error(
                    "[DATA_MANAGER] local mode: no usable PKL/JSON data for %s %s %s",
                    requested_year,
                    race,
                    session,
                )
                return False

            # PKL 快取不存在，嘗試從官方 API 下載
            logger.info("[DATA_MANAGER] PKL 快取不存在，從官方 API 下載...")
            _report(10, "Downloading from F1 API...")
            cache_data = downloader.download_and_cache(
                requested_year, race, session,
                force=False,
                progress_callback=_report
            )
            if cache_data:
                return self._load_from_pkl_cache(cache_data, requested_year, race, session, _report)

            # ===== 向後相容：舊的本地 JSON 系統 =====
            logger.warning("[DATA_MANAGER] 官方 API 下載失敗，嘗試本地 JSON...")
            return self._load_from_legacy_json(requested_year, race, session, source_type, _report)
            
        except Exception as e:
            logger.exception("[DATA_MANAGER] 載入賽事失敗: %s", e)
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
                logger.warning("[DATA_MANAGER] PKL 快取中無快照數據")
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
            
            # 恢復天氣數據
            self._cached_weather_data = cache_data.get('weather_data', [])
            
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
            
            logger.info("[DATA_MANAGER] 從 PKL 快取載入 %d 個快照", len(self._snapshots))
            
            # 設定比賽起跑時間偏移（優先使用 GREEN LIGHT 時間）
            self._race_start_offset = self._calculate_race_start_offset()
            logger.info("[DATA_MANAGER] 設定起跑時間偏移: %.2f 秒", self._race_start_offset)
            
            _report(100, "Loaded from PKL cache")
            
            # 發送載入完成信號
            self.race_loaded.emit(self._race_info)
            
            # 發送第一個快照
            if self._snapshots:
                self.snapshot_updated.emit(self._snapshots[0])
                self.time_changed.emit(self._get_display_time(self._snapshots[0]['race_time_seconds']))
                self.progress_changed.emit(0.0)
            
            return True
            
        except Exception as e:
            logger.exception("[DATA_MANAGER] 從 PKL 快取載入失敗: %s", e)
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
            logger.info("[DATA_MANAGER] 舊快取無效，執行完整處理...")
            _report(20, "Loading JSON files...")
            
            def file_progress(current, total, filename):
                percent = 20 + int((current / total) * 30) if total > 0 else 20
                _report(percent, f"Loading {filename}...")
            
            if not self._data_source.load_all_data(progress_callback=file_progress):
                logger.error("[DATA_MANAGER] JSON 數據載入失敗")
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
                logger.warning("[DATA_MANAGER] 無可用快照")
                return False
            
            logger.info("[DATA_MANAGER] 載入 %d 個快照", len(self._snapshots))
            
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
            
            # 設定比賽起跑時間偏移（優先使用 GREEN LIGHT 時間）
            self._race_start_offset = self._calculate_race_start_offset()
            logger.info("[DATA_MANAGER] 設定起跑時間偏移: %.2f 秒", self._race_start_offset)
            
            self.race_loaded.emit(self._race_info)
            
            if self._snapshots:
                self.snapshot_updated.emit(self._snapshots[0])
                self.time_changed.emit(self._get_display_time(self._snapshots[0]['race_time_seconds']))
                self.progress_changed.emit(0.0)
            
            return True
            
        except Exception as e:
            logger.exception("[DATA_MANAGER] 從舊系統載入失敗: %s", e)
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
                logger.warning("[DATA_MANAGER] 快取中無快照數據")
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
            
            # 恢復天氣數據
            self._cached_weather_data = cache_data.get('weather_data', [])
            
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
            
            logger.info("[DATA_MANAGER] 從快取載入 %d 個快照", len(self._snapshots))
            
            _report(100, "Loaded from cache")
            
            # 設定比賽起跑時間偏移（優先使用 GREEN LIGHT 時間）
            self._race_start_offset = self._calculate_race_start_offset()
            logger.info("[DATA_MANAGER] 設定起跑時間偏移: %.2f 秒", self._race_start_offset)
            
            # 發送載入完成信號
            self.race_loaded.emit(self._race_info)
            
            # 發送第一個快照
            if self._snapshots:
                self.snapshot_updated.emit(self._snapshots[0])
                self.time_changed.emit(self._get_display_time(self._snapshots[0]['race_time_seconds']))
                self.progress_changed.emit(0.0)
            
            return True
            
        except Exception as e:
            logger.exception("[DATA_MANAGER] 從快取載入失敗: %s", e)
            return False
    
    def unload_race(self):
        """卸載當前賽事"""
        logger.info("[DATA_MANAGER] 卸載賽事")
        
        # 停止播放
        self.stop()
        
        # ✅ 策略 A：停止背景預測執行緒
        if self._prediction_worker:
            logger.info("[DATA_MANAGER] 停止背景預測執行緒")
            self._prediction_worker.stop()  # stop() 內部已包含 wait()
            self._prediction_worker = None
        
        # 清空數據
        self._data_source = None
        self._processor = None
        self._snapshots = []
        self._current_index = 0
        self._race_info = None
        self._track_data = None
        
        # 清除 gap 歷史
        self.clear_gap_history()
        
        # 發送卸載信號
        self.race_unloaded.emit()
    
    # ===========================================
    # 即時模式支援 (Realtime Mode)
    # ===========================================
    def update_realtime_snapshot(self, snapshot: Dict[str, Any]):
        """
        更新即時模式快照
        
        從 RealTimeLiveF1DataSource 接收即時數據快照，
        並發送給所有訂閱的 MDI 視窗。
        
        Args:
            snapshot: 即時快照數據，格式與歷史快照相同
        """
        # 更新內部狀態
        self._current_realtime_snapshot = snapshot
        
        # 從快照中提取賽事資訊
        if not self._race_info:
            self._race_info = {
                'year': 'Live',
                'race': 'Live Session',
                'session': snapshot.get('session_info', {}).get('Type', 'Race'),
                'circuit': snapshot.get('session_info', {}).get('Meeting', {}).get('Circuit', {}).get('ShortName', 'Unknown'),
                'total_snapshots': 0,  # 即時模式不計數
                'total_laps': snapshot.get('total_laps', 0),
                'duration_seconds': 0,
                'driver_info': {},
            }
            # 發送載入信號（首次連接時）
            self.race_loaded.emit(self._race_info)
        
        # 更新賽事資訊中的圈數
        if snapshot.get('total_laps', 0) > self._race_info.get('total_laps', 0):
            self._race_info['total_laps'] = snapshot['total_laps']
        
        # 發送快照更新信號
        self.snapshot_updated.emit(snapshot)
        
        # 發送時間更新（即時模式不需要偏移，直接使用原始時間）
        race_time = snapshot.get('race_time_seconds', 0.0)
        self.time_changed.emit(race_time)
    
    def is_realtime_mode(self) -> bool:
        """檢查是否為即時模式"""
        return hasattr(self, '_current_realtime_snapshot') and self._current_realtime_snapshot is not None
    
    def get_realtime_snapshot(self) -> Optional[Dict[str, Any]]:
        """獲取當前即時快照"""
        if hasattr(self, '_current_realtime_snapshot'):
            return self._current_realtime_snapshot
        return None
    
    def clear_realtime_state(self):
        """清除即時模式狀態"""
        if hasattr(self, '_current_realtime_snapshot'):
            self._current_realtime_snapshot = None
        self._race_info = None
        self.race_unloaded.emit()
    
    # ===========================================
    # 播放控制
    # ===========================================
    def play(self):
        """開始播放 - 使用真實時間模擬（與 Demo 一致）"""
        import time
        
        if not self._snapshots:
            logger.warning("[DATA_MANAGER] 無法播放：沒有快照數據")
            return
        
        logger.info("[DATA_MANAGER] 準備播放，當前狀態: %s", self._playback_state)
        
        self._playback_state = 'playing'
        
        # 初始化播放時間為當前快照的賽事時間
        if 0 <= self._current_index < len(self._snapshots):
            self._playback_time = self._snapshots[self._current_index].get('race_time_seconds', 0.0)
        else:
            self._playback_time = 0.0
        
        # ✅ 重要：重置開始時間（修復暫停後無法播放的問題）
        self._last_tick_time = time.time()
        
        # 使用固定 50ms 間隔（與 Demo 一致）
        self._playback_timer.start(self._timer_interval_ms)
        self.playback_state_changed.emit('playing')
        logger.info(
            "[DATA_MANAGER] 開始播放，初始賽事時間: %.2fs, 當前索引: %d/%d",
            self._playback_time,
            self._current_index,
            len(self._snapshots),
        )

    
    def pause(self):
        """暫停播放"""
        self._playback_state = 'paused'
        self._playback_timer.stop()
        self.playback_state_changed.emit('paused')
        logger.info("[DATA_MANAGER] 暫停播放")
    
    def stop(self):
        """停止播放"""
        self._playback_state = 'stopped'
        self._playback_timer.stop()
        self._current_index = 0
        self.playback_state_changed.emit('stopped')
        
        # 重置到開始
        if self._snapshots:
            self.snapshot_updated.emit(self._snapshots[0])
            self.time_changed.emit(self._get_display_time(self._snapshots[0]['race_time_seconds']))
            self.progress_changed.emit(0.0)
        
        logger.info("[DATA_MANAGER] 停止播放")
    
    def set_speed(self, speed: float):
        """
        設置播放速度
        
        Args:
            speed: 播放速度倍率 (0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0)
        """
        self._playback_speed = max(0.1, min(128.0, speed))
        
        # 固定 50ms timer 間隔，速度通過時間計算控制（與 Demo 一致）
        # 不需要調整 timer 間隔
        
        logger.info("[DATA_MANAGER] 播放速度: %.1fx", self._playback_speed)
    
    def seek(self, time_seconds: float):
        """
        跳轉到指定時間
        
        Args:
            time_seconds: 目標時間（秒）- 這是顯示時間，需要轉換為原始時間
        """
        if not self._snapshots:
            return
        
        # 將顯示時間轉換為原始時間
        raw_time = self._get_raw_time(time_seconds)
        
        # 二分查找最接近的快照
        target_index = self._find_snapshot_by_time(raw_time)
        self._current_index = target_index
        
        snapshot = self._snapshots[self._current_index]
        
        # ✅ 更新追蹤數據
        self._update_tire_saving_scores(snapshot)
        self._update_top_speed_tracking(snapshot)
        # ❌ 性能優化：禁用 OT% 和 CC% 預測（占用 80% CPU）
        # self._update_overtake_predictions(snapshot)
        # self._update_close_combat_predictions(snapshot)
        
        self.snapshot_updated.emit(snapshot)
        self.time_changed.emit(self._get_display_time(snapshot['race_time_seconds']))
        
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
        
        # ✅ 更新追蹤數據
        self._update_tire_saving_scores(snapshot)
        self._update_top_speed_tracking(snapshot)
        # ❌ 性能優化：禁用 OT% 和 CC% 預測（占用 80% CPU）
        # self._update_overtake_predictions(snapshot)
        # self._update_close_combat_predictions(snapshot)
        
        self.snapshot_updated.emit(snapshot)
        self.time_changed.emit(self._get_display_time(snapshot['race_time_seconds']))
        self.progress_changed.emit(progress)
    
    def seek_by_offset(self, offset_seconds: float):
        """
        根據時間偏移量跳轉（支援正負值）
        
        Args:
            offset_seconds: 時間偏移量（秒），正數向前，負數向後
                           例如：-30 表示倒退 30 秒
        """
        if not self._snapshots:
            return
        
        # 獲取當前顯示時間
        current_raw_time = self._snapshots[self._current_index].get('race_time_seconds', 0.0)
        current_display_time = self._get_display_time(current_raw_time)
        
        # 計算目標顯示時間
        target_display_time = current_display_time + offset_seconds
        target_display_time = max(0.0, target_display_time)  # 不能小於 0
        
        # 使用 seek 方法跳轉（seek 現在接收顯示時間）
        self.seek(target_display_time)
        
        logger.debug(
            "[DATA_MANAGER] Seek offset: %+0.1fs | Current: %0.1fs -> Target: %0.1fs",
            offset_seconds,
            current_display_time,
            target_display_time,
        )
    
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
    
    # =========================================================================
    # F87 省胎分數管理
    # =========================================================================
    
    def update_tire_saving_score(self, driver_num: str, score: float, level: str, adjustment: float):
        """
        更新車手的省胎分數 (由 driver_strategy MDI 調用)
        
        Args:
            driver_num: 車手編號
            score: 省胎分數 (0-100)
            level: 省胎等級 (NONE/LIGHT/MODERATE/HEAVY)
            adjustment: 補償係數 (0-0.25)
        """
        self._tire_saving_scores[driver_num] = {
            'score': score,
            'level': level,
            'adjustment': adjustment
        }
    
    def get_tire_saving_score(self, driver_num: str) -> Dict[str, Any]:
        """
        獲取車手的省胎分數
        
        Args:
            driver_num: 車手編號
            
        Returns:
            {'score': float, 'level': str, 'adjustment': float} 或空字典
        """
        return self._tire_saving_scores.get(driver_num, {})
    
    def get_all_tire_saving_scores(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有車手的省胎分數
        
        Returns:
            {driver_num: {'score': float, 'level': str, 'adjustment': float}}
        """
        return self._tire_saving_scores.copy()
    
    def get_throttle_history(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有車手的油門 95% 歷史數據
        
        用於 Throttle 95% History 和 SF% Chart 模組在打開時回補歷史數據
        
        Returns:
            {driver_num: {
                'lap_ratios': {lap_num: ratio},
                'pit_laps': set of lap numbers,
                'current_lamp': str,
                'dynamic_baseline': float or None,
                'lap_lamps': {lap_num: lamp_status} (用於 SF% Chart)
            }}
        """
        result = {}
        for driver_num, tracker in self._driver_throttle_samples.items():
            # 為每圈計算 lamp 狀態 (基於當前 baseline)
            lap_lamps = {}
            baseline = tracker.get('dynamic_baseline')
            lap_ratios = tracker.get('lap_ratios', {})
            pit_laps = tracker.get('pit_laps', set())
            
            if baseline and baseline > 0:
                THRESHOLD_HIGH = -5.0
                THRESHOLD_MEDIUM = -3.0
                for lap_num, ratio in lap_ratios.items():
                    if lap_num in pit_laps:
                        lap_lamps[lap_num] = ''
                        continue
                    deviation_pct = ((ratio - baseline) / baseline) * 100
                    if deviation_pct <= THRESHOLD_HIGH:
                        lap_lamps[lap_num] = 'R'
                    elif deviation_pct <= THRESHOLD_MEDIUM:
                        lap_lamps[lap_num] = 'Y'
                    else:
                        lap_lamps[lap_num] = ''
            
            result[driver_num] = {
                'lap_ratios': lap_ratios.copy(),
                'pit_laps': pit_laps.copy(),
                'current_lamp': tracker.get('current_lamp', ''),
                'dynamic_baseline': baseline,
                'lap_lamps': lap_lamps,
            }
        return result
    
    def get_top_speed_history(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有車手的最高速歷史數據
        
        用於 Top Speed History 模組在打開時回補歷史數據
        
        Returns:
            {driver_num: {
                'lap_top_speeds': {lap_num: speed},
                'personal_best': float
            }}
        """
        result = {}
        for driver_num, tracker in self._driver_speed_samples.items():
            result[driver_num] = {
                'lap_top_speeds': tracker.get('lap_top_speeds', {}).copy(),
                'personal_best': tracker.get('personal_best', 0.0),
            }
        return result
    
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
    
    def get_weather_at_time(self, timestamp: str) -> Dict[str, Any]:
        """
        獲取指定時間的天氣數據
        
        Returns:
            Dict with keys: AirTemp, TrackTemp, Humidity, Pressure, WindSpeed, WindDirection, Rainfall
        """
        # 使用快取的天氣數據
        if hasattr(self, '_cached_weather_data') and self._cached_weather_data:
            return self._get_weather_from_cache(timestamp)
        return {}
    
    def _get_weather_from_cache(self, timestamp: str) -> Dict[str, Any]:
        """從快取的天氣數據查詢"""
        from .position_processor import LivePositionDataProcessor
        
        target_seconds = LivePositionDataProcessor._time_str_to_seconds(timestamp)
        if target_seconds is None:
            return {}
        
        current_weather = {}
        for record in self._cached_weather_data:
            ts = record.get('timestamp', '')
            ts_seconds = LivePositionDataProcessor._time_str_to_seconds(ts)
            if ts_seconds is not None and ts_seconds <= target_seconds:
                data = record.get('data', {})
                # 更新天氣數據（增量式）- 轉換字串為浮點數
                try:
                    if 'AirTemp' in data:
                        current_weather['AirTemp'] = float(data['AirTemp'])
                    if 'TrackTemp' in data:
                        current_weather['TrackTemp'] = float(data['TrackTemp'])
                    if 'Humidity' in data:
                        current_weather['Humidity'] = float(data['Humidity'])
                    if 'Pressure' in data:
                        current_weather['Pressure'] = float(data['Pressure'])
                    if 'WindSpeed' in data:
                        current_weather['WindSpeed'] = float(data['WindSpeed'])
                    if 'WindDirection' in data:
                        current_weather['WindDirection'] = float(data['WindDirection'])
                    if 'Rainfall' in data:
                        current_weather['Rainfall'] = int(data['Rainfall']) if data['Rainfall'] else 0
                except (ValueError, TypeError):
                    pass  # 忽略無法轉換的數據
            elif ts_seconds is not None and ts_seconds > target_seconds:
                break
        
        return current_weather
    
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
            logger.info("[DATA_MANAGER] 賽道資料載入完成: %s", track_json_path)
            return True
        except Exception as e:
            logger.exception("[DATA_MANAGER] 載入賽道資料失敗: %s", e)
            return False
    
    def get_track_data(self) -> Optional[Dict[str, Any]]:
        """獲取賽道資料"""
        return self._track_data
    
    def _update_tire_saving_scores(self, snapshot: Dict[str, Any]):
        """
        F87: 計算並更新 snapshot 中的省胎分數與省油燈號
        
        使用動態滾動基線（10圈窗口）計算油門 95% 比率。
        進站前後圈排除不顯示警告燈號。
        
        燈號邏輯:
        - 紅燈: 偏離 < -5% (HIGH)
        - 黃燈: 偏離 -3% ~ -5% (MEDIUM)
        - 無燈: 正常或數據不足
        """
        drivers = snapshot.get('drivers', {})
        if not drivers:
            return
        
        # 動態滾動基線參數
        ROLLING_WINDOW = 10       # 滾動窗口大小
        THRESHOLD_HIGH = -5.0     # 高警告閾值 (紅燈)
        THRESHOLD_MEDIUM = -3.0   # 中警告閾值 (黃燈)
        MIN_LAPS_FOR_BASELINE = 3 # 建立基線所需最少圈數
        OUTLIER_FILTER = 0.7      # 異常值過濾閾值 (排除進站圈)
        
        for driver_num, driver_data in drivers.items():
            # 從 snapshot 獲取 throttle 值
            throttle = driver_data.get('throttle', 0)
            
            # 初始化追蹤器
            if driver_num not in self._driver_throttle_samples:
                self._driver_throttle_samples[driver_num] = {
                    'samples': [],
                    'last_lap': 0,
                    'lap_ratios': {},           # {lap_num: ratio}
                    'pit_laps': set(),          # 進站圈集合
                    'current_score': 0.0,
                    'current_level': 'NONE',
                    'current_lamp': '',         # 燈號: '', 'Y', 'R'
                    'current_throttle_pct': 0.0,  # 當前圈油門95%
                    'dynamic_baseline': None,   # 動態滾動基線
                    'score_calculated_for_lap': 0
                }
            
            tracker = self._driver_throttle_samples[driver_num]
            current_lap = driver_data.get('lap', 0) or 0
            
            # 檢測進站狀態
            is_in_pit = driver_data.get('in_pit', False) or driver_data.get('pit_out', False)
            if is_in_pit and current_lap > 0:
                tracker['pit_laps'].add(current_lap)
                # 進站圈前後也標記
                if current_lap > 1:
                    tracker['pit_laps'].add(current_lap - 1)
                tracker['pit_laps'].add(current_lap + 1)
            
            # 累積 throttle 樣本
            if throttle is not None:
                try:
                    tracker['samples'].append(int(throttle))
                except (ValueError, TypeError):
                    pass
            
            # 圈數變化時：計算上一圈的 ratio
            if current_lap > tracker['last_lap'] and current_lap > 1:
                # 計算上一圈的 full_throttle_ratio (油門 >= 95% 的比率)
                if tracker['samples']:
                    full_throttle_count = sum(1 for s in tracker['samples'] if s >= 95)
                    ratio = full_throttle_count / len(tracker['samples']) * 100  # 轉為百分比
                    completed_lap = tracker['last_lap']
                    tracker['lap_ratios'][completed_lap] = ratio
                    tracker['current_throttle_pct'] = ratio
                
                # 清空樣本
                tracker['samples'] = []
                
                # 計算動態滾動基線（排除進站圈和異常值）
                all_laps = sorted(tracker['lap_ratios'].keys())
                
                if len(all_laps) >= MIN_LAPS_FOR_BASELINE:
                    # 取最近 ROLLING_WINDOW 圈
                    recent_laps = all_laps[-ROLLING_WINDOW:]
                    
                    # 過濾：排除進站圈
                    valid_ratios = [
                        tracker['lap_ratios'][lap]
                        for lap in recent_laps
                        if lap not in tracker['pit_laps']
                    ]
                    
                    if len(valid_ratios) >= MIN_LAPS_FOR_BASELINE:
                        # 計算初步中位數作為基準
                        import statistics
                        median_candidate = statistics.median(valid_ratios)
                        
                        # 進一步過濾：排除低於基準 70% 的異常值
                        filtered_ratios = [
                            r for r in valid_ratios
                            if r > median_candidate * OUTLIER_FILTER
                        ]
                        
                        if len(filtered_ratios) >= MIN_LAPS_FOR_BASELINE:
                            tracker['dynamic_baseline'] = statistics.median(filtered_ratios)
                        else:
                            tracker['dynamic_baseline'] = median_candidate
                
                # 計算偏離度和燈號
                lamp = ''
                level = 'NONE'
                score = 0.0
                
                baseline = tracker['dynamic_baseline']
                current_ratio = tracker['current_throttle_pct']
                completed_lap = tracker['last_lap']
                
                # 檢查是否為進站前後圈（排除警告）
                is_pit_related = completed_lap in tracker['pit_laps']
                
                if baseline is not None and baseline > 0 and not is_pit_related:
                    # 計算偏離百分比
                    deviation = current_ratio - baseline
                    deviation_pct = (deviation / baseline) * 100
                    
                    # 判斷燈號
                    if deviation_pct <= THRESHOLD_HIGH:
                        lamp = 'R'  # 紅燈
                        level = 'HEAVY'
                        score = min(50, abs(deviation_pct))
                    elif deviation_pct <= THRESHOLD_MEDIUM:
                        lamp = 'Y'  # 黃燈
                        level = 'MODERATE'
                        score = min(30, abs(deviation_pct))
                    else:
                        lamp = ''   # 無燈號（正常）
                        level = 'NONE'
                        score = 0.0
                
                # 保存狀態
                tracker['current_lamp'] = lamp
                tracker['current_level'] = level
                tracker['current_score'] = score
                tracker['score_calculated_for_lap'] = current_lap
                
                # 更新 last_lap
                tracker['last_lap'] = current_lap
            elif tracker['last_lap'] == 0:
                tracker['last_lap'] = current_lap
            
            # 輸出到 snapshot
            drivers[driver_num]['tire_saving_score'] = tracker['current_score']
            drivers[driver_num]['tire_saving_level'] = tracker['current_level']
            drivers[driver_num]['fuel_saving_lamp'] = tracker['current_lamp']
            drivers[driver_num]['throttle_95_pct'] = tracker['current_throttle_pct']
            drivers[driver_num]['throttle_baseline'] = tracker.get('dynamic_baseline', 0)
    
    def _update_top_speed_tracking(self, snapshot: Dict[str, Any]):
        """
        追蹤每圈最高速度並更新 snapshot
        
        追蹤邏輯:
        - 持續追蹤每位車手當前圈的最高速度
        - 圈數變化時，儲存上一圈的最高速度
        - 計算個人最高速 (personal_best_speed)
        - 輸出到 snapshot: lap_top_speed, personal_best_speed
        """
        drivers = snapshot.get('drivers', {})
        if not drivers:
            return
        
        for driver_num, driver_data in drivers.items():
            # 獲取當前速度
            current_speed = driver_data.get('speed', 0)
            if current_speed is None:
                current_speed = 0
            try:
                current_speed = float(current_speed)
            except (ValueError, TypeError):
                current_speed = 0
            
            # 獲取當前圈數
            current_lap = driver_data.get('lap', 0) or 0
            
            # 初始化追蹤器
            if driver_num not in self._driver_speed_samples:
                self._driver_speed_samples[driver_num] = {
                    'current_lap': 0,
                    'current_max_speed': 0.0,
                    'lap_top_speeds': {},  # {lap_num: top_speed}
                    'personal_best': 0.0,
                }
            
            tracker = self._driver_speed_samples[driver_num]
            
            # 更新當前圈的最高速度
            if current_speed > tracker['current_max_speed']:
                tracker['current_max_speed'] = current_speed
            
            # 圈數變化：儲存上一圈的最高速度
            if current_lap > tracker['current_lap'] and tracker['current_lap'] > 0:
                completed_lap = tracker['current_lap']
                top_speed = tracker['current_max_speed']
                
                if top_speed > 0:
                    # 儲存上一圈的最高速
                    tracker['lap_top_speeds'][completed_lap] = top_speed
                    
                    # 更新個人最高速
                    if top_speed > tracker['personal_best']:
                        tracker['personal_best'] = top_speed
                
                # 重置當前圈追蹤
                tracker['current_max_speed'] = current_speed
            
            # 初始化第一圈
            if tracker['current_lap'] == 0:
                tracker['current_max_speed'] = current_speed
            
            # 更新圈數
            tracker['current_lap'] = current_lap
            
            # 輸出到 snapshot
            drivers[driver_num]['lap_top_speed'] = tracker['current_max_speed']
            drivers[driver_num]['personal_best_speed'] = tracker['personal_best']
    
    def _update_overtake_predictions(self, snapshot: Dict[str, Any]):
        """
        F83: 即時計算並更新 snapshot 中的超車預測數據（✅ 策略 B：智能緩存版本）
        
        優化策略：
        - 只在間距變化 > 0.1s 或圈數變化時重新計算
        - 使用緩存減少 50-70% 的 ML 推理次數
        - 保持數據實時性，緩存命中時延遲 < 1ms
        """
        if not self._overtake_predictor:
            return
        
        drivers = snapshot.get('drivers', {})
        if not drivers:
            return
        
        # 獲取當前時間戳（用於 gap 歷史追蹤）
        current_time = snapshot.get('race_time_seconds', 0.0)
        
        # 獲取當前圈數（用於計算比賽進度）
        current_lap = 0
        for driver_data in drivers.values():
            lap = driver_data.get('lap', 0)
            if lap and lap > current_lap:
                current_lap = lap
        
        # Lap 1, 2 不計算超車機率（數據不穩定）
        if current_lap <= 2:
            for driver_num in drivers:
                drivers[driver_num]['overtake_probability'] = 0
                drivers[driver_num]['gap_trend'] = 0.0  # 無趨勢
            return
        
        # ✅ 策略 B：使用緩存機制，減少重複計算
        try:
            # 獲取輪胎狀態
            tyre_state = self.get_tyre_state()
            
            # 獲取總圈數
            total_laps = self._race_info.get('total_laps', 60) if self._race_info else 60
            race_progress = current_lap / total_laps if total_laps > 0 else 0.5
            
            # 獲取賽道狀態（是否綠旗）
            track_status_green = True  # 預設綠旗
            
            # 按位置排序車手
            sorted_drivers = []
            for driver_num, driver_data in drivers.items():
                pos = driver_data.get('position', 99)
                sorted_drivers.append((driver_num, driver_data, pos))
            sorted_drivers.sort(key=lambda x: x[2])
            
            # 計算每個車手對前車的超車機率
            for i, (driver_num, driver_data, position) in enumerate(sorted_drivers):
                # P1 沒有前車，超車機率為 0，趨勢也為 0
                if position == 1 or i == 0:
                    drivers[driver_num]['overtake_probability'] = 0
                    drivers[driver_num]['gap_trend'] = 0.0
                    continue
                
                # 獲取前車資訊
                ahead_driver_num, ahead_driver_data, _ = sorted_drivers[i - 1]
                
                # 獲取間距
                gap_str = driver_data.get('gap_to_ahead', '') or driver_data.get('gap_to_ahead_display', '')
                gap_seconds = self._parse_gap_seconds(gap_str)
                
                # 更新 gap 歷史並計算趨勢（改進版：單圈變化）
                current_lap_num = driver_data.get('lap', 0)
                gap_trend = self._update_gap_history_and_calc_lap_trend(
                    driver_num, gap_seconds, current_lap_num
                )
                drivers[driver_num]['gap_trend'] = gap_trend
                
                # ✅ 策略 B：檢查緩存
                cache_entry = self._prediction_cache.get(driver_num, {})
                cached_gap = cache_entry.get('gap')
                cached_lap = cache_entry.get('lap')
                
                # 判斷是否需要重新計算
                need_recalc = (
                    cached_gap is None or
                    cached_lap != current_lap_num or
                    gap_seconds is None or
                    abs(gap_seconds - cached_gap) > self._cache_gap_threshold
                )
                
                # 使用緩存值
                if not need_recalc and 'ot%' in cache_entry:
                    drivers[driver_num]['overtake_probability'] = cache_entry['ot%']
                    continue
                
                # 間距太大（>8秒）或無法解析，超車機率設為 0
                if gap_seconds is None or gap_seconds > 8.0:
                    drivers[driver_num]['overtake_probability'] = 0
                    # ✅ 更新緩存
                    self._prediction_cache[driver_num] = {
                        'gap': gap_seconds if gap_seconds else 999,
                        'lap': current_lap_num,
                        'ot%': 0,
                        'timestamp': current_time
                    }
                    continue
                
                # 獲取輪胎資訊
                attacker_tyre = 'MEDIUM'
                defender_tyre = 'MEDIUM'
                tyre_age_diff = 0
                
                if tyre_state:
                    attacker_tyre_info = tyre_state.get(driver_num, {})
                    defender_tyre_info = tyre_state.get(ahead_driver_num, {})
                    
                    attacker_tyre = attacker_tyre_info.get('compound', 'MEDIUM')
                    defender_tyre = defender_tyre_info.get('compound', 'MEDIUM')
                    
                    attacker_age = attacker_tyre_info.get('age', 0)
                    defender_age = defender_tyre_info.get('age', 0)
                    tyre_age_diff = defender_age - attacker_age
                
                # 判斷 DRS 可用性
                drs_available = gap_seconds < 1.0
                
                # 判斷是否正在追近（根據趨勢）
                is_catching = gap_trend < -0.1  # 趨勢為負表示在追近
                
                # 呼叫 F83 預測
                try:
                    result = self._overtake_predictor.predict(
                        gap_seconds=gap_seconds,
                        gap_delta=gap_trend if gap_trend != 0 else -0.1,  # 使用實際趨勢
                        is_catching=is_catching,
                        drs_available=drs_available,
                        attacker_tyre=attacker_tyre,
                        defender_tyre=defender_tyre,
                        tyre_age_diff=tyre_age_diff,
                        track_status_green=track_status_green,
                        attacker_position=position,
                        race_progress=race_progress
                    )
                    
                    # 轉換為百分比整數 (0-100)
                    ot_probability = int(round(result.probability * 100))
                    drivers[driver_num]['overtake_probability'] = ot_probability
                    
                    # ✅ 策略 B：更新緩存
                    self._prediction_cache[driver_num] = {
                        'gap': gap_seconds,
                        'lap': current_lap_num,
                        'ot%': ot_probability,
                        'timestamp': current_time
                    }
                    
                except Exception as e:
                    drivers[driver_num]['overtake_probability'] = 0
            
        except Exception as e:
            logger.exception("[DATA_MANAGER] F83 超車預測失敗: %s", e)
    
    def _update_close_combat_predictions(self, snapshot: Dict[str, Any]):
        """
        F85: 即時計算並更新 snapshot 中的近距離接觸預測數據（✅ 策略 B：智能緩存版本）
        
        優化策略：
        - 只在間距變化 > 0.1s 或圈數變化時重新計算
        - 與 OT% 共享緩存機制
        - 減少 50-70% 的 ML 推理次數
        """
        if not self._close_combat_predictor:
            return
        
        drivers = snapshot.get('drivers', {})
        if not drivers:
            return
        
        # 獲取當前時間
        current_time = snapshot.get('race_time_seconds', 0.0)
        
        # 獲取當前圈數
        current_lap = 0
        for driver_data in drivers.values():
            lap = driver_data.get('lap', 0)
            if lap and lap > current_lap:
                current_lap = lap
        
        # Lap 1, 2 不計算近距離接觸機率（數據不穩定）
        if current_lap <= 2:
            for driver_num in drivers:
                drivers[driver_num]['close_combat_probability'] = 0
            return
        
        try:
            # 獲取輪胎狀態
            tyre_state = self.get_tyre_state()
            
            # 獲取總圈數
            total_laps = self._race_info.get('total_laps', 60) if self._race_info else 60
            race_progress = current_lap / total_laps if total_laps > 0 else 0.5
            
            # 獲取賽道狀態（是否綠旗）
            track_status_green = True  # 預設綠旗
            
            # 按位置排序車手
            sorted_drivers = []
            for driver_num, driver_data in drivers.items():
                pos = driver_data.get('position', 99)
                sorted_drivers.append((driver_num, driver_data, pos))
            sorted_drivers.sort(key=lambda x: x[2])
            
            # 計算每個車手對前車的近距離接觸機率
            for i, (driver_num, driver_data, position) in enumerate(sorted_drivers):
                # P1 沒有前車，近距離接觸機率為 0
                if position == 1 or i == 0:
                    drivers[driver_num]['close_combat_probability'] = 0
                    continue
                
                # 獲取前車資訊
                ahead_driver_num, ahead_driver_data, _ = sorted_drivers[i - 1]
                
                # 獲取間距
                gap_str = driver_data.get('gap_to_ahead', '') or driver_data.get('gap_to_ahead_display', '')
                gap_seconds = self._parse_gap_seconds(gap_str)
                
                # 獲取當前圈數
                current_lap_num = driver_data.get('lap', 0)
                
                # 獲取 gap_trend（1 圈趨勢）
                gap_trend = self._update_gap_history_and_calc_lap_trend(
                    driver_num, gap_seconds, current_lap_num
                )
                
                # ✅ 策略 B：檢查緩存
                cache_entry = self._prediction_cache.get(driver_num, {})
                cached_gap = cache_entry.get('gap')
                cached_lap = cache_entry.get('lap')
                
                # 判斷是否需要重新計算
                need_recalc = (
                    cached_gap is None or
                    cached_lap != current_lap_num or
                    gap_seconds is None or
                    abs(gap_seconds - cached_gap) > self._cache_gap_threshold
                )
                
                # 使用緩存值
                if not need_recalc and 'cc%' in cache_entry:
                    drivers[driver_num]['close_combat_probability'] = cache_entry['cc%']
                    continue
                
                # 間距太大（>8秒）或無法解析，近距離接觸機率設為 0
                if gap_seconds is None or gap_seconds > 8.0:
                    drivers[driver_num]['close_combat_probability'] = 0
                    # ✅ 更新緩存
                    if driver_num in self._prediction_cache:
                        self._prediction_cache[driver_num]['cc%'] = 0
                    else:
                        self._prediction_cache[driver_num] = {
                            'gap': gap_seconds if gap_seconds else 999,
                            'lap': current_lap_num,
                            'cc%': 0,
                            'timestamp': current_time
                        }
                    continue
                
                # 計算 F85 特有的 3 個額外特徵
                gap_trend_3lap = self._calculate_gap_trend_3lap(driver_num, gap_seconds, current_lap)
                min_gap_last_5lap = self._calculate_min_gap_last_5lap(driver_num, gap_seconds)
                consecutive_catching_laps = self._calculate_consecutive_catching_laps(driver_num, gap_trend)
                
                # 獲取輪胎資訊
                attacker_tyre = 'MEDIUM'
                defender_tyre = 'MEDIUM'
                tyre_age_diff = 0
                
                if tyre_state:
                    attacker_tyre_info = tyre_state.get(driver_num, {})
                    defender_tyre_info = tyre_state.get(ahead_driver_num, {})
                    
                    attacker_tyre = attacker_tyre_info.get('compound', 'MEDIUM')
                    defender_tyre = defender_tyre_info.get('compound', 'MEDIUM')
                    
                    attacker_age = attacker_tyre_info.get('age', 0)
                    defender_age = defender_tyre_info.get('age', 0)
                    tyre_age_diff = defender_age - attacker_age
                
                # 判斷 DRS 可用性
                drs_available = gap_seconds < 1.0
                
                # 判斷是否正在追近（根據趨勢）
                is_catching = gap_trend < -0.1  # 趨勢為負表示在追近
                
                # 呼叫 F85 預測（13 個參數）
                try:
                    result = self._close_combat_predictor.predict(
                        gap_seconds=gap_seconds,
                        gap_delta=gap_trend if gap_trend != 0 else -0.1,  # 使用實際趨勢
                        is_catching=is_catching,
                        drs_available=drs_available,
                        attacker_tyre=attacker_tyre,
                        defender_tyre=defender_tyre,
                        tyre_age_diff=tyre_age_diff,
                        track_status_green=track_status_green,
                        attacker_position=position,
                        race_progress=race_progress,
                        gap_trend_3lap=gap_trend_3lap,
                        min_gap_last_5lap=min_gap_last_5lap,
                        consecutive_catching_laps=consecutive_catching_laps
                    )
                    
                    base_probability = result.probability
                    
                    # 啟發式增強：彌補模型標籤定義過窄的問題（0.2-0.3s → 實際戰鬥範圍更寬）
                    # 使用多條件混合邏輯判斷「激烈戰鬥」場景
                    heuristic_boost = 0.0
                    
                    # 規則 1: 極近距離 + DRS + 強力追近 → 極高機率
                    # 場景：gap < 1.0s，DRS 開啟，追近速度 > 0.3s/lap
                    if gap_seconds < 1.0 and drs_available and gap_trend < -0.3:
                        heuristic_boost = max(heuristic_boost, 0.6)  # 提升 60%
                    
                    # 規則 2: 持續強力追近（3+ 圈，平均 > 0.5s/lap）
                    # 場景：連續追近 3 圈以上，3 圈趨勢斜率 < -0.5
                    elif consecutive_catching_laps >= 3 and gap_trend_3lap < -0.5:
                        heuristic_boost = max(heuristic_boost, 0.4)  # 提升 40%
                    
                    # 規則 3: 中距離但趨勢極強（1.0-2.0s，單圈追近 > 0.8s）
                    # 場景：距離適中但追近速度驚人
                    elif 1.0 <= gap_seconds < 2.0 and gap_trend < -0.8:
                        heuristic_boost = max(heuristic_boost, 0.35)  # 提升 35%
                    
                    # 規則 4: 曾經很接近（min_gap < 1.0s）且仍在追近
                    # 場景：最近 5 圈內曾接近到 1.0s 以內，目前仍在追近
                    elif min_gap_last_5lap < 1.0 and gap_trend < -0.2:
                        heuristic_boost = max(heuristic_boost, 0.25)  # 提升 25%
                    
                    # 規則 5: 近距離（< 1.5s）且穩定追近（2+ 圈）
                    # 場景：中等距離但持續施壓
                    elif gap_seconds < 1.5 and consecutive_catching_laps >= 2 and gap_trend < -0.15:
                        heuristic_boost = max(heuristic_boost, 0.20)  # 提升 20%
                    
                    # 應用增強（不超過 100%）
                    final_probability = min(1.0, base_probability + heuristic_boost)
                    
                    # 轉換為百分比整數 (0-100)
                    drivers[driver_num]['close_combat_probability'] = int(round(final_probability * 100))
                    
                except Exception as e:
                    drivers[driver_num]['close_combat_probability'] = 0
            
        except Exception as e:
            logger.exception("[DATA_MANAGER] F85 近距離接觸預測失敗: %s", e)
    
    def _parse_gap_seconds(self, gap_str: str) -> Optional[float]:
        """
        解析間距字串，返回秒數
        
        支援格式：
        - "+0.812s" → 0.812
        - "0.812" → 0.812
        - "1 LAP" → None (落後一圈，無法超車)
        - "" → None
        """
        if not gap_str:
            return None
        
        gap_str = str(gap_str).strip().upper()
        
        # 落後圈數
        if 'LAP' in gap_str:
            return None
        
        # 移除前綴和後綴
        gap_str = gap_str.replace('+', '').replace('S', '').strip()
        
        try:
            return float(gap_str)
        except ValueError:
            return None
    
    def _update_gap_history_and_calc_lap_trend(
        self, driver_num: str, gap_seconds: Optional[float], current_lap: int
    ) -> float:
        """
        更新 gap 歷史並計算單圈趨勢（改進版）
        
        新邏輯：
        - 比較「當前圈 gap」與「上一圈 gap」
        - 返回單圈變化量（秒）
        - 負值 = 追近（綠色 >）
        - 正值 = 拉開（紅色 <）
        
        ⚠️ 名次變更偵測（2025-12-09 新增）：
        - 當 gap_seconds 與上一圈差距過大（>3秒），判定為名次變更
        - 重置 gap 歷史，避免錯誤的 Trend 顯示
        
        Args:
            driver_num: 車手編號
            gap_seconds: 當前間距（秒），None 表示無法解析
            current_lap: 當前圈數
            
        Returns:
            lap_gap_change: 單圈 gap 變化量（秒）
        """
        # 如果 gap 無法解析，返回 0
        if gap_seconds is None or current_lap <= 0:
            return 0.0
        
        # 初始化該車手的記錄
        if driver_num not in self._gap_history:
            self._gap_history[driver_num] = {
                'last_lap': 0,
                'last_gap': None,
                'current_lap': current_lap,
                'current_gap': gap_seconds
            }
            return 0.0  # 第一次記錄，無法計算趨勢
        
        record = self._gap_history[driver_num]
        
        # ✅ 名次變更偵測（2025-12-09 新增）
        # 如果 gap 突然變化超過 3 秒，很可能是名次變更（前車換人）
        # 此時應重置 gap 歷史，避免顯示錯誤的 Trend
        if record['last_gap'] is not None:
            gap_diff = abs(gap_seconds - record['last_gap'])
            if gap_diff > 3.0:
                # 名次變更！重置歷史
                record['last_lap'] = current_lap
                record['last_gap'] = None
                record['current_lap'] = current_lap
                record['current_gap'] = gap_seconds
                return 0.0  # 重置後無趨勢
        
        # 檢查是否進入新圈
        if current_lap > record['current_lap']:
            # 進入新圈：保存上一圈數據
            record['last_lap'] = record['current_lap']
            record['last_gap'] = record['current_gap']
            record['current_lap'] = current_lap
            record['current_gap'] = gap_seconds
            
            # 計算單圈變化量
            if record['last_gap'] is not None:
                lap_gap_change = gap_seconds - record['last_gap']
                return lap_gap_change
            else:
                return 0.0
        else:
            # 同一圈：更新當前 gap（取最新值）
            record['current_gap'] = gap_seconds
            
            # 如果有上一圈數據，計算當前趨勢（即時預覽）
            if record['last_gap'] is not None:
                lap_gap_change = gap_seconds - record['last_gap']
                return lap_gap_change
            else:
                return 0.0
    
    def clear_gap_history(self):
        """清除所有 gap 歷史記錄（賽事切換時調用）"""
        self._gap_history.clear()

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
        
        # 發送插值信號（使用顯示時間）
        display_time = self._get_display_time(self._playback_time)
        self.interpolation_updated.emit(current_snap, next_snap, alpha, display_time)
        
        # 只有索引變化時才發送完整快照更新
        if new_index != self._current_index:
            self._current_index = new_index
            
            # 取得快照並更新追蹤數據
            snapshot = self._snapshots[self._current_index]
            self._update_tire_saving_scores(snapshot)
            self._update_top_speed_tracking(snapshot)
            
            # ✅ 策略 A：將 OT%/CC% 預測移到背景執行緒
            if self._prediction_worker:
                drivers = snapshot.get('drivers', {})
                
                # 步驟 1：先計算 gap_trend（主執行緒快速計算）
                current_lap = max((d.get('lap', 0) for d in drivers.values()), default=0)
                
                # 檢查是否在 Lap 1-2（數據不穩定期）
                if current_lap <= 2:
                    # Lap 1-2：所有預測設為 0
                    for driver_num in drivers:
                        drivers[driver_num]['gap_trend'] = 0.0
                        drivers[driver_num]['overtake_probability'] = 0
                        drivers[driver_num]['close_combat_probability'] = 0
                else:
                    # Lap 3+：計算預測
                    # 按位置排序
                    sorted_drivers = []
                    for driver_num, driver_data in drivers.items():
                        pos = driver_data.get('position', 99)
                        sorted_drivers.append((driver_num, driver_data, pos))
                    sorted_drivers.sort(key=lambda x: x[2])
                    
                    for i, (driver_num, driver_data, position) in enumerate(sorted_drivers):
                        if position == 1 or i == 0:
                            drivers[driver_num]['gap_trend'] = 0.0
                            drivers[driver_num]['overtake_probability'] = 0
                            drivers[driver_num]['close_combat_probability'] = 0
                            continue
                        
                        # 計算 gap_trend
                        gap_str = driver_data.get('gap_to_ahead', '') or driver_data.get('gap_to_ahead_display', '')
                        gap_seconds = self._parse_gap_seconds(gap_str)
                        current_lap_num = driver_data.get('lap', 0)
                        gap_trend = self._update_gap_history_and_calc_lap_trend(
                            driver_num, gap_seconds, current_lap_num
                        )
                        drivers[driver_num]['gap_trend'] = gap_trend
                        
                        # 使用緩存值初始化預測（如果有）
                        cache = self._prediction_cache.get(driver_num, {})
                        drivers[driver_num]['overtake_probability'] = cache.get('ot%', 0)
                        drivers[driver_num]['close_combat_probability'] = cache.get('cc%', 0)
                    
                    # 步驟 2：非阻塞發送預測請求到背景執行緒
                    tyre_state = self.get_tyre_state()
                    total_laps = self._race_info.get('total_laps', 60) if self._race_info else 60
                    race_progress = current_lap / total_laps if total_laps > 0 else 0.5
                    track_status_green = True
                    
                    # ❌ 性能優化：禁用背景預測（占用 80% CPU）
                    # self._prediction_worker.queue_prediction(
                    #     snapshot=snapshot,
                    #     tyre_state=tyre_state,
                    #     race_progress=race_progress,
                    #     track_status_green=track_status_green
                    # )
                    pass
            else:
                # ❌ 性能優化：禁用主執行緒預測（占用 80% CPU）
                # self._update_overtake_predictions(snapshot)  # F83 超車預測
                # self._update_close_combat_predictions(snapshot)  # F85 近距離接觸預測
                pass
            
            # 發送快照（添加幀計數器供跳幀渲染使用）
            self._frame_counter += 1
            snapshot['frame_counter'] = self._frame_counter  # 供模組判斷是否需要重繪
            
            self.snapshot_updated.emit(snapshot)
            self.time_changed.emit(self._get_display_time(snapshot['race_time_seconds']))
            
            # 調試輸出：每秒報告一次更新頻率
            self._debug_update_count += 1
            self._debug_updates_since_report += 1
            
            time_since_report = current_time - self._debug_last_report_time
            if time_since_report >= 1.0:
                updates_per_sec = self._debug_updates_since_report / time_since_report
                logger.debug(
                    "[PLAYBACK_DEBUG] 更新頻率: %.1f/秒 | 總更新: %d | 索引: %d/%d | 賽事時間: %s | 播放速度: %.1fx",
                    updates_per_sec,
                    self._debug_update_count,
                    new_index,
                    len(self._snapshots),
                    snapshot['race_time'],
                    self._playback_speed,
                )
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
    
    def _calculate_gap_trend_3lap(self, driver_num: str, gap_seconds: float, current_lap: int) -> float:
        """
        計算過去 3 圈的 gap 趨勢斜率（F85 特有特徵）
        
        使用線性回歸計算 3 圈的趨勢斜率。
        負值表示在追近，正值表示在拉開。
        
        Args:
            driver_num: 車手編號
            gap_seconds: 當前間距（秒）
            current_lap: 當前圈數
        """
        # (原有實現內容)
        pass
    
    def _on_predictions_ready(self, results: Dict[str, Dict[str, int]]):
        """
        策略 A：處理背景執行緒返回的預測結果
        
        Args:
            results: {driver_num: {'ot%': int, 'cc%': int}}
        """
        if not self._snapshots or self._current_index >= len(self._snapshots):
            return
        
        # 更新當前快照的預測結果
        snapshot = self._snapshots[self._current_index]
        drivers = snapshot.get('drivers', {})
        current_time = snapshot.get('race_time_seconds', 0.0)
        
        updated_count = 0
        nonzero_ot_count = 0
        nonzero_cc_count = 0
        
        for driver_num, predictions in results.items():
            if driver_num in drivers:
                ot_prob = predictions.get('ot%', 0)
                cc_prob = predictions.get('cc%', 0)
                
                drivers[driver_num]['overtake_probability'] = ot_prob
                drivers[driver_num]['close_combat_probability'] = cc_prob
                
                if ot_prob > 0:
                    nonzero_ot_count += 1
                if cc_prob > 0:
                    nonzero_cc_count += 1
                
                updated_count += 1
                
                # 更新緩存（策略 B）
                gap_str = drivers[driver_num].get('gap_to_ahead', '') or drivers[driver_num].get('gap_to_ahead_display', '')
                gap_seconds = self._parse_gap_seconds(gap_str)
                current_lap = drivers[driver_num].get('lap', 0)
                
                self._prediction_cache[driver_num] = {
                    'gap': gap_seconds if gap_seconds else 999,
                    'lap': current_lap,
                    'ot%': ot_prob,
                    'cc%': cc_prob,
                    'timestamp': current_time
                }
        
        # 調試日誌（改為 INFO 級別）
        logger.info(
            "[PREDICTION_READY] 更新 %d 車手 | OT>0: %d | CC>0: %d",
            updated_count, nonzero_ot_count, nonzero_cc_count
        )
        
        # 重新發送更新信號（僅包含預測數據變更）
        self.snapshot_updated.emit(snapshot)
    
    def _calculate_gap_trend_3lap_impl(self, driver_num: str, gap_seconds: float, current_lap: int) -> float:
        """
        內部實現：計算過去 3 圈的 gap 趨勢斜率（F85 特有特徵）
        
        使用線性回歸計算 3 圈的趨勢斜率。
        負值表示在追近，正值表示在拉開。
        
        Args:
            driver_num: 車手編號
            gap_seconds: 當前間距（秒）
            current_lap: 當前圈數
            
        Returns:
            gap_trend_3lap: 3 圈趨勢斜率（秒/圈）
        """
        if not hasattr(self, '_gap_history_3lap'):
            self._gap_history_3lap = {}
        
        # 初始化該車手的 3 圈歷史
        if driver_num not in self._gap_history_3lap:
            self._gap_history_3lap[driver_num] = {
                'laps': [],
                'gaps': []
            }
        
        history = self._gap_history_3lap[driver_num]
        
        # 添加當前數據點
        if not history['laps'] or current_lap > history['laps'][-1]:
            history['laps'].append(current_lap)
            history['gaps'].append(gap_seconds)
            
            # 只保留最近 3 圈
            if len(history['laps']) > 3:
                history['laps'].pop(0)
                history['gaps'].pop(0)
        else:
            # 同一圈，更新最新值
            if history['laps']:
                history['gaps'][-1] = gap_seconds
        
        # 至少需要 2 個數據點才能計算趨勢
        if len(history['laps']) < 2:
            return 0.0
        
        # 簡單線性回歸計算斜率
        try:
            import numpy as np
            laps = np.array(history['laps'])
            gaps = np.array(history['gaps'])
            
            # 計算斜率
            slope = np.polyfit(laps, gaps, 1)[0]
            return float(slope)
        except:
            # 降級計算：簡單平均變化率
            total_change = history['gaps'][-1] - history['gaps'][0]
            lap_span = history['laps'][-1] - history['laps'][0]
            if lap_span > 0:
                return total_change / lap_span
            return 0.0
    
    def _calculate_min_gap_last_5lap(self, driver_num: str, gap_seconds: float) -> float:
        """
        計算過去 5 圈的最小 gap（F85 特有特徵）
        
        追蹤過去 5 圈中最接近前車的距離。
        用於判斷車手是否曾經接近過前車。
        
        Args:
            driver_num: 車手編號
            gap_seconds: 當前間距（秒）
            
        Returns:
            min_gap_last_5lap: 過去 5 圈的最小間距（秒）
        """
        if not hasattr(self, '_gap_history_5lap'):
            self._gap_history_5lap = {}
        
        # 初始化該車手的 5 圈歷史
        if driver_num not in self._gap_history_5lap:
            self._gap_history_5lap[driver_num] = []
        
        history = self._gap_history_5lap[driver_num]
        
        # 添加當前值
        history.append(gap_seconds)
        
        # 只保留最近 5 圈
        if len(history) > 5:
            history.pop(0)
        
        # 返回最小值
        return min(history)
    
    def _calculate_consecutive_catching_laps(self, driver_num: str, gap_trend: float) -> int:
        """
        計算連續追近圈數（F85 特有特徵）
        
        統計車手連續多少圈在追近前車（gap_trend < 0）。
        連續性表示持續的追近壓力。
        
        Args:
            driver_num: 車手編號
            gap_trend: 當前圈的 gap 趨勢（秒）
            
        Returns:
            consecutive_catching_laps: 連續追近圈數
        """
        if not hasattr(self, '_catching_streak'):
            self._catching_streak = {}
        
        # 初始化該車手的連續計數
        if driver_num not in self._catching_streak:
            self._catching_streak[driver_num] = 0
        
        # 判斷是否在追近（gap_trend < -0.05）
        is_catching = gap_trend < -0.05
        
        if is_catching:
            # 追近中，增加計數
            self._catching_streak[driver_num] += 1
        else:
            # 沒有追近，重置計數
            self._catching_streak[driver_num] = 0
        
        return self._catching_streak[driver_num]
