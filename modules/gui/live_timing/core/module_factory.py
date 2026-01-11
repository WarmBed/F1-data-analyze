"""
Live Timing Module Factory
==========================

統一管理所有 Live Timing 模組的工廠類別。
所有 Live Timing 模組必須在此註冊才能使用。

架構設計：
- MODULE_REGISTRY: 多語言名稱別名 → 模組鍵值
- MODULE_CLASSES: 模組鍵值 → 模組類別（延遲載入）
- 統一的創建入口點，確保所有模組使用相同的 DataManager

Author: F1T Team
Date: 2025-12-03
"""

from typing import Optional, Type, Dict, Any, TYPE_CHECKING

from core.logger import get_logger

if TYPE_CHECKING:
    from .data_manager import LiveTimingDataManager
    from .base_live_mdi import BaseLiveTimingMDI


class LiveTimingModuleFactory:
    """
    Live Timing 模組工廠
    
    所有 Live Timing 模組必須在此註冊：
    1. 在 MODULE_REGISTRY 中添加多語言別名
    2. 在 MODULE_CLASSES 中添加模組鍵值與類別映射
    3. 在 _import_module_class() 中添加延遲導入邏輯
    
    使用方式：
        factory = LiveTimingModuleFactory.get_instance()
        module = factory.create_module("Track Map", parent_widget)
    """
    
    _instance: Optional['LiveTimingModuleFactory'] = None
    _data_manager: Optional['LiveTimingDataManager'] = None
    
    # ========== 模組註冊表 ==========
    # 多語言名稱別名 → 模組鍵值
    MODULE_REGISTRY: Dict[str, str] = {
        # Track Map 賽道地圖
        "Track Map": "track_map",
        "賽道地圖": "track_map",
        "トラックマップ": "track_map",
        "track_map": "track_map",
        
        # Live Ranking 即時排名
        "Live Ranking": "ranking_tower",
        "即時排名": "ranking_tower",
        "ライブランキング": "ranking_tower",
        "ranking_tower": "ranking_tower",
        
        # Control Panel 控制面板
        "Control Panel": "control_panel",
        "控制面板": "control_panel",
        "コントロールパネル": "control_panel",
        "control_panel": "control_panel",
        
        # Pit Window 進站視窗（預留）
        "Pit Window": "pit_window",
        "進站視窗": "pit_window",
        "ピットウィンドウ": "pit_window",
        "pit_window": "pit_window",
        
        # Tyre Strategy 輪胎策略（預留）
        "Tyre Strategy": "tyre_strategy",
        "輪胎策略": "tyre_strategy",
        "タイヤ戦略": "tyre_strategy",
        "tyre_strategy": "tyre_strategy",
        
        # Gap Chart 差距圖表（預留）
        "Gap Chart": "gap_chart",
        "差距圖表": "gap_chart",
        "ギャップチャート": "gap_chart",
        "gap_chart": "gap_chart",
        
        # Battle Tracker 對戰追蹤（預留）
        "Battle Tracker": "battle_tracker",
        "對戰追蹤": "battle_tracker",
        "バトルトラッカー": "battle_tracker",
        "battle_tracker": "battle_tracker",
        
        # Circle Map 圓形賽道地圖
        "Circle Map": "circle_map",
        "圓形地圖": "circle_map",
        "サークルマップ": "circle_map",
        "circle_map": "circle_map",
        
        # Lap Time Distribution 圈速分佈
        "Lap Time Distribution": "lap_time_distribution",
        "圈速分佈": "lap_time_distribution",
        "ラップタイム分布": "lap_time_distribution",
        "lap_time_distribution": "lap_time_distribution",
        
        # Race Control Messages 比賽控制訊息
        "Race Control Messages": "race_control_messages",
        "比賽控制訊息": "race_control_messages",
        "レースコントロール": "race_control_messages",
        "race_control_messages": "race_control_messages",
        
        # Lap History - Lap Time 圈速歷史
        "Lap History - Lap Time": "lap_history_lap_time",
        "圈速歷史": "lap_history_lap_time",
        "圈速歷史 - 完整圈速": "lap_history_lap_time",
        "ラップヒストリー - ラップタイム": "lap_history_lap_time",
        "lap_history_lap_time": "lap_history_lap_time",
        
        # Lap History - S1 第一區間歷史
        "Lap History - S1": "lap_history_s1",
        "S1歷史": "lap_history_s1",
        "圈速歷史 - 第一段": "lap_history_s1",
        "ラップヒストリー - S1": "lap_history_s1",
        "lap_history_s1": "lap_history_s1",
        
        # Lap History - S2 第二區間歷史
        "Lap History - S2": "lap_history_s2",
        "S2歷史": "lap_history_s2",
        "圈速歷史 - 第二段": "lap_history_s2",
        "ラップヒストリー - S2": "lap_history_s2",
        "lap_history_s2": "lap_history_s2",
        
        # Lap History - S3 第三區間歷史
        "Lap History - S3": "lap_history_s3",
        "S3歷史": "lap_history_s3",
        "圈速歷史 - 第三段": "lap_history_s3",
        "ラップヒストリー - S3": "lap_history_s3",
        "lap_history_s3": "lap_history_s3",
        
        # Speed Trace 速度追蹤
        "Speed Trace": "speed_trace",
        "速度追蹤": "speed_trace",
        "スピードトレース": "speed_trace",
        "speed_trace": "speed_trace",
        
        # Throttle Trace 油門追蹤
        "Throttle Trace": "throttle_trace",
        "油門追蹤": "throttle_trace",
        "スロットルトレース": "throttle_trace",
        "throttle_trace": "throttle_trace",
        
        # Brake Trace 煞車追蹤
        "Brake Trace": "brake_trace",
        "煞車追蹤": "brake_trace",
        "ブレーキトレース": "brake_trace",
        "brake_trace": "brake_trace",
        
        # Gear Trace 檔位追蹤
        "Gear Trace": "gear_trace",
        "檔位追蹤": "gear_trace",
        "ギアトレース": "gear_trace",
        "gear_trace": "gear_trace",
        
        # DRS Trace DRS追蹤
        "DRS Trace": "drs_trace",
        "DRS追蹤": "drs_trace",
        "DRSトレース": "drs_trace",
        "drs_trace": "drs_trace",
        
        # RPM Trace 轉速追蹤
        "RPM Trace": "rpm_trace",
        "轉速追蹤": "rpm_trace",
        "回転数トレース": "rpm_trace",
        "rpm_trace": "rpm_trace",
        
        # Driver Strategy 車手策略
        "Driver Strategy": "driver_strategy",
        "車手策略": "driver_strategy",
        "ドライバーストラテジー": "driver_strategy",
        "driver_strategy": "driver_strategy",
        
        # Sector Comparison - S1 第一區段比較
        "Sector Comparison - S1": "sector_comparison_s1",
        "S1 Comparison": "sector_comparison_s1",
        "S1比較": "sector_comparison_s1",
        "第一段比較": "sector_comparison_s1",
        "S1 比較": "sector_comparison_s1",
        "sector_comparison_s1": "sector_comparison_s1",
        
        # Sector Comparison - S2 第二區段比較
        "Sector Comparison - S2": "sector_comparison_s2",
        "S2 Comparison": "sector_comparison_s2",
        "S2比較": "sector_comparison_s2",
        "第二段比較": "sector_comparison_s2",
        "S2 比較": "sector_comparison_s2",
        "sector_comparison_s2": "sector_comparison_s2",
        
        # Sector Comparison - S3 第三區段比較
        "Sector Comparison - S3": "sector_comparison_s3",
        "S3 Comparison": "sector_comparison_s3",
        "S3比較": "sector_comparison_s3",
        "第三段比較": "sector_comparison_s3",
        "S3 比較": "sector_comparison_s3",
        "sector_comparison_s3": "sector_comparison_s3",
        
        # Battle Insight 戰鬥分析
        "Battle Insight": "battle_insight",
        "戰鬥分析": "battle_insight",
        "バトルインサイト": "battle_insight",
        "battle_insight": "battle_insight",
        
        # Chase Strategy 追趕策略
        "Chase Strategy": "chase_strategy",
        "追趕策略": "chase_strategy",
        "追撃戦略": "chase_strategy",
        "chase_strategy": "chase_strategy",
        
        # Track & Weather 賽道與天氣狀態
        "Track & Weather": "track_weather",
        "賽道與天氣": "track_weather",
        "トラック＆ウェザー": "track_weather",
        "track_weather": "track_weather",
        
        # Throttle 95% History 油門歷史
        "Throttle 95% History": "throttle_history",
        "Throttle 95%": "throttle_history",
        "Throttle History": "throttle_history",
        "油門歷史": "throttle_history",
        "油門 95% 歷史": "throttle_history",
        "スロットル履歴": "throttle_history",
        "スロットル 95%": "throttle_history",
        "throttle_history": "throttle_history",
        
        # SF% History 省油百分比歷史
        "SF% History": "sf_percentage_chart",
        "SF% Chart": "sf_percentage_chart",
        "省油百分比": "sf_percentage_chart",
        "省油歷史": "sf_percentage_chart",
        "SF% 歷史": "sf_percentage_chart",
        "SF%履歴": "sf_percentage_chart",
        "SF% ヒストリー": "sf_percentage_chart",
        "sf_percentage_chart": "sf_percentage_chart",
        
        # Traffic Timeline 車流時間線
        "Traffic Timeline": "live_traffic_timeline",
        "車流時間線": "live_traffic_timeline",
        "トラフィックタイムライン": "live_traffic_timeline",
        "live_traffic_timeline": "live_traffic_timeline",
        
        # Top Speed History 每圈最高速歷史
        "Top Speed History": "top_speed_history",
        "Top Speed": "top_speed_history",
        "最高速歷史": "top_speed_history",
        "最高速ヒストリー": "top_speed_history",
        "トップスピード履歴": "top_speed_history",
        "top_speed_history": "top_speed_history",
    }
    
    # 模組鍵值 → 模組元數據
    MODULE_METADATA: Dict[str, Dict[str, Any]] = {
        "track_map": {
            "display_name": "Track Map",
            "description": "Real-time track position visualization",
            "icon": "track_map.png",
            "implemented": True,
        },
        "ranking_tower": {
            "display_name": "Live Ranking",
            "description": "Real-time driver ranking tower",
            "icon": "ranking.png",
            "implemented": True,
        },
        "control_panel": {
            "display_name": "Control Panel",
            "description": "Live Timing control and data source management",
            "icon": "control.png",
            "implemented": True,
        },
        "pit_window": {
            "display_name": "Pit Window",
            "description": "Pit stop window analysis",
            "icon": "pit.png",
            "implemented": True,
        },
        "tyre_strategy": {
            "display_name": "Tyre Strategy",
            "description": "Real-time tyre strategy visualization",
            "icon": "tyre.png",
            "implemented": True,
        },
        "lap_time_distribution": {
            "display_name": "Lap Time Distribution",
            "description": "Lap time gap distribution visualization",
            "icon": "lap_dist.png",
            "implemented": True,
        },
        "gap_chart": {
            "display_name": "Gap Chart",
            "description": "Real-time gap chart between drivers",
            "icon": "gap.png",
            "implemented": False,
        },
        "battle_tracker": {
            "display_name": "Battle Tracker",
            "description": "Track battles between drivers",
            "icon": "battle.png",
            "implemented": False,
        },
        "circle_map": {
            "display_name": "Circle Map",
            "description": "Circular track position visualization",
            "icon": "circle_map.png",
            "implemented": True,
        },
        "race_control_messages": {
            "display_name": "Race Control Messages",
            "description": "Race control messages - flags, penalties, investigations",
            "icon": "race_control.png",
            "implemented": True,
        },
        "lap_history_lap_time": {
            "display_name": "Lap History - Lap Time",
            "description": "Lap time history for all drivers",
            "icon": "lap_history.png",
            "implemented": True,
        },
        "lap_history_s1": {
            "display_name": "Lap History - S1",
            "description": "Sector 1 time history for all drivers",
            "icon": "lap_history.png",
            "implemented": True,
        },
        "lap_history_s2": {
            "display_name": "Lap History - S2",
            "description": "Sector 2 time history for all drivers",
            "icon": "lap_history.png",
            "implemented": True,
        },
        "lap_history_s3": {
            "display_name": "Lap History - S3",
            "description": "Sector 3 time history for all drivers",
            "icon": "lap_history.png",
            "implemented": True,
        },
        "speed_trace": {
            "display_name": "Speed Trace",
            "description": "Real-time speed vs distance trace with delta comparison",
            "icon": "speed_trace.png",
            "implemented": True,
        },
        "throttle_trace": {
            "display_name": "Throttle Trace",
            "description": "Real-time throttle application vs distance trace",
            "icon": "throttle_trace.png",
            "implemented": True,
        },
        "brake_trace": {
            "display_name": "Brake Trace",
            "description": "Real-time brake application vs distance trace (0/1)",
            "icon": "brake_trace.png",
            "implemented": True,
        },
        "gear_trace": {
            "display_name": "Gear Trace",
            "description": "Real-time gear position vs distance trace (1-8)",
            "icon": "gear_trace.png",
            "implemented": True,
        },
        "drs_trace": {
            "display_name": "DRS Trace",
            "description": "Real-time DRS status vs distance trace (0-14)",
            "icon": "drs_trace.png",
            "implemented": True,
        },
        "rpm_trace": {
            "display_name": "RPM Trace",
            "description": "Real-time engine RPM vs distance trace (0-15000)",
            "icon": "rpm_trace.png",
            "implemented": True,
        },
        "driver_strategy": {
            "display_name": "Driver Strategy",
            "description": "Single driver strategy graph with lap time prediction",
            "icon": "driver_strategy.png",
            "implemented": True,
        },
        "sector_comparison_s1": {
            "display_name": "Sector Comparison - S1",
            "description": "Compare Sector 1 times between two drivers",
            "icon": "sector_comparison.png",
            "implemented": True,
        },
        "sector_comparison_s2": {
            "display_name": "Sector Comparison - S2",
            "description": "Compare Sector 2 times between two drivers",
            "icon": "sector_comparison.png",
            "implemented": True,
        },
        "sector_comparison_s3": {
            "display_name": "Sector Comparison - S3",
            "description": "Compare Sector 3 times between two drivers",
            "icon": "sector_comparison.png",
            "implemented": True,
        },
        "battle_insight": {
            "display_name": "Battle Insight",
            "description": "Real-time battle analysis with overtake probability and insights",
            "icon": "battle_insight.png",
            "implemented": True,
        },
        "chase_strategy": {
            "display_name": "Chase Strategy",
            "description": "P2 to P1 chase strategy analysis with 5 strategy scenarios",
            "icon": "chase_strategy.png",
            "implemented": True,
        },
        "track_weather": {
            "display_name": "Track & Weather",
            "description": "Real-time track status and weather conditions display",
            "icon": "track_weather.png",
            "implemented": True,
        },
        "throttle_history": {
            "display_name": "Throttle 95% History",
            "description": "Throttle 95%+ usage history for all drivers per lap",
            "icon": "throttle_history.png",
            "implemented": True,
        },
        "sf_percentage_chart": {
            "display_name": "SF% History",
            "description": "SF% (Stint Fuel Saving) history curve for single driver",
            "icon": "sf_percentage_chart.png",
            "implemented": True,
        },
        "live_traffic_timeline": {
            "display_name": "Traffic Timeline",
            "description": "Real-time traffic heatmap showing lap-by-lap traffic status",
            "icon": "traffic_timeline.png",
            "implemented": True,
        },
        "top_speed_history": {
            "display_name": "Top Speed History",
            "description": "Top speed history for all drivers per lap with personal best highlighting",
            "icon": "top_speed_history.png",
            "implemented": True,
        },
    }
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化工廠"""
        if self._initialized:
            return
        self._initialized = True
        self._module_cache: Dict[str, Type] = {}
        self._logger = get_logger("live_timing.module_factory", component="gui")
        self._logger.debug("LiveTimingModuleFactory initialized")
    
    @classmethod
    def get_instance(cls) -> 'LiveTimingModuleFactory':
        """獲取工廠單例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_data_manager(cls) -> 'LiveTimingDataManager':
        """獲取共享的 DataManager 單例"""
        if cls._data_manager is None:
            from .data_manager import LiveTimingDataManager
            cls._data_manager = LiveTimingDataManager.get_instance()
        return cls._data_manager
    
    @classmethod
    def is_live_timing_module(cls, name: str) -> bool:
        """
        檢查名稱是否為已註冊的 Live Timing 模組
        
        Args:
            name: 模組名稱（支援多語言）
            
        Returns:
            bool: 是否為 Live Timing 模組
        """
        return name in cls.MODULE_REGISTRY
    
    @classmethod
    def get_module_key(cls, name: str) -> Optional[str]:
        """
        獲取模組鍵值
        
        Args:
            name: 模組名稱（支援多語言）
            
        Returns:
            str: 模組鍵值，未找到則返回 None
        """
        return cls.MODULE_REGISTRY.get(name)
    
    @classmethod
    def is_implemented(cls, name: str) -> bool:
        """
        檢查模組是否已實現
        
        Args:
            name: 模組名稱（支援多語言）
            
        Returns:
            bool: 模組是否已實現
        """
        module_key = cls.get_module_key(name)
        if module_key is None:
            return False
        metadata = cls.MODULE_METADATA.get(module_key, {})
        return metadata.get("implemented", False)
    
    @classmethod
    def get_all_modules(cls) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有已註冊模組的元數據
        
        Returns:
            Dict: 模組鍵值 → 元數據
        """
        return cls.MODULE_METADATA.copy()
    
    @classmethod
    def get_implemented_modules(cls) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有已實現的模組
        
        Returns:
            Dict: 已實現模組的鍵值 → 元數據
        """
        return {
            key: meta for key, meta in cls.MODULE_METADATA.items()
            if meta.get("implemented", False)
        }
    
    def _import_module_class(self, module_key: str) -> Optional[Type['BaseLiveTimingMDI']]:
        """
        延遲導入模組類別
        
        Args:
            module_key: 模組鍵值
            
        Returns:
            Type: 模組類別，未找到則返回 None
        """
        # 檢查緩存
        if module_key in self._module_cache:
            return self._module_cache[module_key]
        
        module_class = None
        
        try:
            if module_key == "track_map":
                from ..live_timing_modules.track_map import LiveTimingTrackMap
                module_class = LiveTimingTrackMap
                
            elif module_key == "ranking_tower":
                from ..live_timing_modules.ranking_tower import LiveTimingRankingTower
                module_class = LiveTimingRankingTower
                
            elif module_key == "control_panel":
                from ..live_timing_modules.control_panel import LiveTimingControlPanel
                module_class = LiveTimingControlPanel
                
            elif module_key == "pit_window":
                from ..live_timing_modules.pit_window import LiveTimingPitWindow
                module_class = LiveTimingPitWindow
                
            elif module_key == "tyre_strategy":
                from ..live_timing_modules.tyre_strategy import LiveTimingTyreStrategy
                module_class = LiveTimingTyreStrategy
                
            elif module_key == "lap_time_distribution":
                from ..live_timing_modules.lap_time_distribution import LiveTimingLapDistribution
                module_class = LiveTimingLapDistribution
                
            elif module_key == "gap_chart":
                # TODO: 實現後取消註釋
                self._logger.info("Module '%s' not yet implemented", module_key)
                return None
                
            elif module_key == "battle_tracker":
                # TODO: 實現後取消註釋
                self._logger.info("Module '%s' not yet implemented", module_key)
                return None
                
            elif module_key == "circle_map":
                from ..live_timing_modules.circle_map import LiveTimingCircleMap
                module_class = LiveTimingCircleMap
                
            elif module_key == "race_control_messages":
                from ..live_timing_modules.race_control_messages import LiveTimingRaceControlMessages
                module_class = LiveTimingRaceControlMessages
                
            elif module_key == "lap_history_lap_time":
                from ..live_timing_modules.lap_history import LiveTimingLapHistoryLapTime
                module_class = LiveTimingLapHistoryLapTime
                
            elif module_key == "lap_history_s1":
                from ..live_timing_modules.lap_history import LiveTimingLapHistoryS1
                module_class = LiveTimingLapHistoryS1
                
            elif module_key == "lap_history_s2":
                from ..live_timing_modules.lap_history import LiveTimingLapHistoryS2
                module_class = LiveTimingLapHistoryS2
                
            elif module_key == "lap_history_s3":
                from ..live_timing_modules.lap_history import LiveTimingLapHistoryS3
                module_class = LiveTimingLapHistoryS3
                
            elif module_key == "speed_trace":
                from ..live_timing_modules.speed_trace import LiveTimingSpeedTrace
                module_class = LiveTimingSpeedTrace
                
            elif module_key == "throttle_trace":
                from ..live_timing_modules.throttle_trace import LiveTimingThrottleTrace
                module_class = LiveTimingThrottleTrace
                
            elif module_key == "brake_trace":
                from ..live_timing_modules.brake_trace import LiveTimingBrakeTrace
                module_class = LiveTimingBrakeTrace
                
            elif module_key == "gear_trace":
                from ..live_timing_modules.gear_trace import LiveTimingGearTrace
                module_class = LiveTimingGearTrace
                
            elif module_key == "drs_trace":
                from ..live_timing_modules.drs_trace import LiveTimingDRSTrace
                module_class = LiveTimingDRSTrace
                
            elif module_key == "rpm_trace":
                from ..live_timing_modules.rpm_trace import LiveTimingRPMTrace
                module_class = LiveTimingRPMTrace
                
            elif module_key == "driver_strategy":
                from ..live_timing_modules.driver_strategy import LiveTimingDriverStrategy
                module_class = LiveTimingDriverStrategy
                
            elif module_key == "sector_comparison_s1":
                from ..live_timing_modules.sector_comparison import SectorComparisonS1MDI
                module_class = SectorComparisonS1MDI
                
            elif module_key == "sector_comparison_s2":
                from ..live_timing_modules.sector_comparison import SectorComparisonS2MDI
                module_class = SectorComparisonS2MDI
                
            elif module_key == "sector_comparison_s3":
                from ..live_timing_modules.sector_comparison import SectorComparisonS3MDI
                module_class = SectorComparisonS3MDI
                
            elif module_key == "battle_insight":
                from ..live_timing_modules.battle_insight import BattleInsightMDI
                module_class = BattleInsightMDI
                
            elif module_key == "chase_strategy":
                from ..live_timing_modules.chase_strategy import ChaseStrategyMDI
                module_class = ChaseStrategyMDI
                
            elif module_key == "track_weather":
                from ..live_timing_modules.track_weather import TrackWeatherMDI
                module_class = TrackWeatherMDI
                
            elif module_key == "throttle_history":
                from ..live_timing_modules.throttle_history import LiveTimingThrottleHistory
                module_class = LiveTimingThrottleHistory
                
            elif module_key == "sf_percentage_chart":
                from ..live_timing_modules.sf_percentage_chart import LiveTimingSFPercentageChart
                module_class = LiveTimingSFPercentageChart
                
            elif module_key == "live_traffic_timeline":
                from ..live_timing_modules.live_traffic_timeline import LiveTrafficTimelineMDI
                module_class = LiveTrafficTimelineMDI
                
            elif module_key == "top_speed_history":
                from ..live_timing_modules.top_speed_history import LiveTimingTopSpeedHistory
                module_class = LiveTimingTopSpeedHistory
                
            else:
                self._logger.warning("Unknown module key: %s", module_key)
                return None
            
            # 緩存成功導入的類別
            if module_class is not None:
                self._module_cache[module_key] = module_class
                self._logger.debug("Module class loaded: %s", module_key)
                
        except ImportError as e:
            self._logger.error("Failed to import module '%s': %s", module_key, e)
            return None
        
        return module_class
    
    def create_module(
        self, 
        name: str, 
        parent=None
    ) -> Optional['BaseLiveTimingMDI']:
        """
        創建 Live Timing 模組實例
        
        Args:
            name: 模組名稱（支援多語言）
            parent: 父視窗（通常是 MainWindow）
            
        Returns:
            BaseLiveTimingMDI: 模組實例，失敗則返回 None
        """
        # 查找模組鍵值
        module_key = self.get_module_key(name)
        if module_key is None:
            self._logger.warning("Module not registered: %s", name)
            return None
        
        # 檢查是否已實現
        if not self.is_implemented(name):
            self._logger.info("Module not yet implemented: %s (%s)", name, module_key)
            return None
        
        # 導入模組類別
        module_class = self._import_module_class(module_key)
        if module_class is None:
            return None
        
        # 創建模組實例
        try:
            module_instance = module_class(parent)
            self._logger.debug("Module created: %s (%s)", name, module_key)
            return module_instance
        except Exception as e:
            self._logger.error("Failed to create module '%s': %s", name, e)
            import traceback
            traceback.print_exc()
            return None


# 便捷函數
def is_live_timing_module(name: str) -> bool:
    """檢查是否為 Live Timing 模組"""
    return LiveTimingModuleFactory.is_live_timing_module(name)


def create_live_timing_module(name: str, parent=None):
    """創建 Live Timing 模組"""
    factory = LiveTimingModuleFactory.get_instance()
    return factory.create_module(name, parent)
