"""
LiveTimingManager - Live Timing 模組統一管理器

此管理器取代了 f1t_gui_main.py 中 25 個重複的 _open_live_timing_* 方法，
通過配置驅動的方式統一管理所有 Live Timing 模組的開啟。

重構效果：
- 重構前：25 個重複方法，~600 行代碼
- 重構後：1 個通用方法 + 配置表，~200 行代碼
- 減少：~400 行 (66.7%)

使用方式：
    # 在 StyleHMainWindow.__init__ 中初始化
    from windows.managers import LiveTimingManager
    self.live_timing_manager = LiveTimingManager(self)
    
    # 設置選單
    live_timing_menu = self.menuBar().addMenu("Live Timing")
    self.live_timing_manager.setup_menu(live_timing_menu)

Author: F1T Development Team
Date: 2025-12-16
"""

import logging
from typing import TYPE_CHECKING, Dict, Any, Optional, Callable
from functools import partial

from PyQt5.QtWidgets import QMenu, QAction, QMessageBox
from core.logger import get_logger
from core.gui_i18n import tr
from typing import Dict
from typing import Optional
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QAction
from typing import Any
from typing import Callable

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QMainWindow

logger = logging.getLogger(__name__)


def tr(key: str, default: str) -> str:
    """多語言翻譯函數"""
    # TODO: 整合完整的 i18n 系統
    return default


class LiveTimingManager:
    """
    Live Timing 模組管理器
    
    通過配置表驅動的方式管理所有 Live Timing 模組，
    消除重複的開啟方法，提供統一的介面。
    
    Attributes:
        main_window: 主視窗實例
        MODULES: 模組配置表
    """
    
    # 模組配置表（取代 25 個重複方法）
    MODULES: Dict[str, Dict[str, Any]] = {
        # === 視覺化模組 ===
        'track_map': {
            'name': 'Track Map',
            'menu_key': 'menu_live_timing_track_map',
            'menu_default': 'Track Map',
            'tip_key': 'live_timing_track_map_tip',
            'tip_default': 'Open Track Map',
            'category': 'visualization',
            'enabled': True,
        },
        'circle_map': {
            'name': 'Circle Map',
            'menu_key': 'menu_live_timing_circle_map',
            'menu_default': 'Circle Map',
            'tip_key': 'live_timing_circle_map_tip',
            'tip_default': 'Open Circle Map',
            'category': 'visualization',
            'enabled': True,
        },
        'live_ranking': {
            'name': 'Live Ranking',
            'menu_key': 'menu_live_timing_ranking',
            'menu_default': 'Live Ranking',
            'tip_key': 'live_timing_ranking_tip',
            'tip_default': 'Open Live Ranking Tower',
            'category': 'visualization',
            'enabled': True,
        },
        'pit_window': {
            'name': 'Pit Window',
            'menu_key': 'menu_live_timing_pit_window',
            'menu_default': 'Pit Window',
            'tip_key': 'live_timing_pit_window_tip',
            'tip_default': 'Open Pit Window',
            'category': 'strategy',
            'enabled': True,
        },
        'tyre_strategy': {
            'name': 'Tyre Strategy',
            'menu_key': 'menu_live_timing_tyre_strategy',
            'menu_default': 'Tyre Strategy',
            'tip_key': 'live_timing_tyre_strategy_tip',
            'tip_default': 'Open Tyre Strategy',
            'category': 'strategy',
            'enabled': True,
        },
        'driver_strategy': {
            'name': 'Driver Strategy',
            'menu_key': 'menu_live_timing_driver_strategy',
            'menu_default': 'Driver Strategy',
            'tip_key': 'live_timing_driver_strategy_tip',
            'tip_default': 'Open Driver Strategy Analysis',
            'category': 'strategy',
            'enabled': True,
        },
        'lap_distribution': {
            'name': 'Lap Time Distribution',
            'menu_key': 'menu_live_timing_lap_distribution',
            'menu_default': 'Lap Time Distribution',
            'tip_key': 'live_timing_lap_distribution_tip',
            'tip_default': 'Open Lap Time Distribution',
            'category': 'analysis',
            'enabled': True,
        },
        
        # === Lap History 子選單 ===
        'lap_history_lap_time': {
            'name': 'Lap History - Lap Time',
            'menu_key': 'menu_lap_history_lap_time',
            'menu_default': 'Lap Time',
            'tip_key': 'lap_history_lap_time_tip',
            'tip_default': 'Lap time history for all drivers',
            'category': 'lap_history',
            'enabled': True,
        },
        'lap_history_s1': {
            'name': 'Lap History - S1',
            'menu_key': 'menu_lap_history_s1',
            'menu_default': 'Sector 1',
            'tip_key': 'lap_history_s1_tip',
            'tip_default': 'Sector 1 time history for all drivers',
            'category': 'lap_history',
            'enabled': True,
        },
        'lap_history_s2': {
            'name': 'Lap History - S2',
            'menu_key': 'menu_lap_history_s2',
            'menu_default': 'Sector 2',
            'tip_key': 'lap_history_s2_tip',
            'tip_default': 'Sector 2 time history for all drivers',
            'category': 'lap_history',
            'enabled': True,
        },
        'lap_history_s3': {
            'name': 'Lap History - S3',
            'menu_key': 'menu_lap_history_s3',
            'menu_default': 'Sector 3',
            'tip_key': 'lap_history_s3_tip',
            'tip_default': 'Sector 3 time history for all drivers',
            'category': 'lap_history',
            'enabled': True,
        },
        'throttle_history': {
            'name': 'Throttle 95% History',
            'menu_key': 'menu_lap_history_throttle_95',
            'menu_default': 'Throttle 95%',
            'tip_key': 'lap_history_throttle_95_tip',
            'tip_default': 'Throttle 95% history for fuel-saving detection',
            'category': 'lap_history',
            'enabled': True,
        },
        'sf_percentage_chart': {
            'name': 'SF% History',
            'menu_key': 'menu_lap_history_sf_percentage',
            'menu_default': 'SF% History',
            'tip_key': 'lap_history_sf_percentage_tip',
            'tip_default': 'SF% (Fuel Saving) history curve for single driver',
            'category': 'lap_history',
            'enabled': True,
        },
        
        # === Sector Comparison 子選單 ===
        'sector_s1': {
            'name': 'Sector Comparison - S1',
            'menu_key': 'menu_sector_comparison_s1',
            'menu_default': 'S1 Comparison',
            'tip_key': 'sector_comparison_s1_tip',
            'tip_default': 'Compare Sector 1 times between two drivers',
            'category': 'sector_comparison',
            'enabled': True,
        },
        'sector_s2': {
            'name': 'Sector Comparison - S2',
            'menu_key': 'menu_sector_comparison_s2',
            'menu_default': 'S2 Comparison',
            'tip_key': 'sector_comparison_s2_tip',
            'tip_default': 'Compare Sector 2 times between two drivers',
            'category': 'sector_comparison',
            'enabled': True,
        },
        'sector_s3': {
            'name': 'Sector Comparison - S3',
            'menu_key': 'menu_sector_comparison_s3',
            'menu_default': 'S3 Comparison',
            'tip_key': 'sector_comparison_s3_tip',
            'tip_default': 'Compare Sector 3 times between two drivers',
            'category': 'sector_comparison',
            'enabled': True,
        },
        
        # === Trace 模組 ===
        'speed_trace': {
            'name': 'Speed Trace',
            'menu_key': 'menu_live_timing_speed_trace',
            'menu_default': 'Speed Trace',
            'tip_key': 'speed_trace_tip',
            'tip_default': 'Real-time speed vs distance trace with delta comparison',
            'category': 'trace',
            'enabled': True,
        },
        'throttle_trace': {
            'name': 'Throttle Trace',
            'menu_key': 'menu_live_timing_throttle_trace',
            'menu_default': 'Throttle Trace',
            'tip_key': 'throttle_trace_tip',
            'tip_default': 'Real-time throttle application vs distance trace',
            'category': 'trace',
            'enabled': True,
        },
        'brake_trace': {
            'name': 'Brake Trace',
            'menu_key': 'menu_live_timing_brake_trace',
            'menu_default': 'Brake Trace',
            'tip_key': 'brake_trace_tip',
            'tip_default': 'Real-time brake application vs distance trace (0/1)',
            'category': 'trace',
            'enabled': True,
        },
        'gear_trace': {
            'name': 'Gear Trace',
            'menu_key': 'menu_live_timing_gear_trace',
            'menu_default': 'Gear Trace',
            'tip_key': 'gear_trace_tip',
            'tip_default': 'Real-time gear position vs distance trace (1-8)',
            'category': 'trace',
            'enabled': True,
        },
        'drs_trace': {
            'name': 'DRS Trace',
            'menu_key': 'menu_live_timing_drs_trace',
            'menu_default': 'DRS Trace',
            'tip_key': 'drs_trace_tip',
            'tip_default': 'Real-time DRS status vs distance trace (0-14)',
            'category': 'trace',
            'enabled': True,
        },
        'rpm_trace': {
            'name': 'RPM Trace',
            'menu_key': 'menu_live_timing_rpm_trace',
            'menu_default': 'RPM Trace',
            'tip_key': 'rpm_trace_tip',
            'tip_default': 'Real-time engine RPM vs distance trace (0-15000)',
            'category': 'trace',
            'enabled': True,
        },
        
        # === 進階分析 ===
        'battle_insight': {
            'name': 'Battle Insight',
            'menu_key': 'menu_live_timing_battle_insight',
            'menu_default': 'Battle Insight (Disabled)',
            'tip_key': 'battle_insight_disabled',
            'tip_default': 'Battle Insight has been disabled for performance optimization',
            'category': 'advanced',
            'enabled': False,  # 性能優化：已禁用
            'disabled_reason': (
                "Battle Insight has been disabled for performance optimization.\n\n"
                "This module's OT% (Overtake Probability) and CC% (Close Contact) "
                "predictions consume 80% of CPU resources, causing severe GUI lag.\n\n"
                "Please contact the development team for optimization plans."
            ),
        },
        'chase_strategy': {
            'name': 'Chase Strategy',
            'menu_key': 'menu_live_timing_chase_strategy',
            'menu_default': 'Chase Strategy',
            'tip_key': 'chase_strategy_tip',
            'tip_default': 'Analyze P2 to P1 chase strategy feasibility',
            'category': 'advanced',
            'enabled': True,
        },
        'track_weather': {
            'name': 'Track & Weather',
            'menu_key': 'menu_live_timing_track_weather',
            'menu_default': 'Track & Weather',
            'tip_key': 'track_weather_tip',
            'tip_default': 'Real-time track status and weather conditions',
            'category': 'advanced',
            'enabled': True,
        },
        'live_traffic_timeline': {
            'name': 'Traffic Timeline',
            'menu_key': 'menu_live_timing_traffic_timeline',
            'menu_default': 'Traffic Timeline',
            'tip_key': 'traffic_timeline_tip',
            'tip_default': 'Real-time traffic heatmap showing lap-by-lap traffic status',
            'category': 'advanced',
            'enabled': True,
        },
        
        # === 未實現模組（Coming Soon）===
        'race_control': {
            'name': 'Race Control Messages',
            'menu_key': 'menu_live_timing_race_control',
            'menu_default': 'Race Control Messages',
            'tip_key': 'live_timing_coming_soon',
            'tip_default': 'Coming Soon',
            'category': 'coming_soon',
            'enabled': False,
        },
        'race_insights': {
            'name': 'Race Insights',
            'menu_key': 'menu_live_timing_race_insights',
            'menu_default': 'Race Insights',
            'tip_key': 'live_timing_coming_soon',
            'tip_default': 'Coming Soon',
            'category': 'coming_soon',
            'enabled': False,
        },
        'shap_analysis': {
            'name': 'SHAP Analysis',
            'menu_key': 'menu_live_timing_shap_analysis',
            'menu_default': 'SHAP Analysis',
            'tip_key': 'live_timing_coming_soon',
            'tip_default': 'Coming Soon',
            'category': 'coming_soon',
            'enabled': False,
        },
        'pit_stop_table': {
            'name': 'Pit Stop Statistics',
            'menu_key': 'menu_live_timing_pit_stop_table',
            'menu_default': 'Pit Stop Statistics',
            'tip_key': 'live_timing_coming_soon',
            'tip_default': 'Coming Soon',
            'category': 'coming_soon',
            'enabled': False,
        },
    }
    
    def __init__(self, main_window: 'QMainWindow'):
        """
        初始化 Live Timing 管理器
        
        Args:
            main_window: 主視窗實例（StyleHMainWindow）
        """
        self.main_window = main_window
        self._action_control_panel: Optional[QAction] = None
        logger.debug("[LiveTimingManager] Initialized")
    
    def open_module(self, module_key: str) -> None:
        """
        通用的模組開啟方法（取代 25 個重複方法）
        
        Args:
            module_key: 模組鍵值（如 'track_map', 'circle_map' 等）
        """
        config = self.MODULES.get(module_key)
        if not config:
            logger.warning(f"[LiveTimingManager] Unknown module key: {module_key}")
            return
        
        # 檢查是否已禁用
        if not config.get('enabled', True):
            disabled_reason = config.get('disabled_reason', 'This module is currently disabled.')
            QMessageBox.warning(
                self.main_window,
                tr('module_disabled', 'Module Disabled'),
                disabled_reason
            )
            return
        
        module_name = config['name']
        logger.debug(f"[LiveTimingManager] Opening module: {module_name}")
        
        # 調用主視窗的統一開啟方法
        self.main_window._open_live_timing_module(module_name)
    
    def toggle_control_panel(self, checked: bool) -> None:
        """切換 Live Timing 控制面板 Dock 的顯示狀態"""
        if hasattr(self.main_window, 'live_timing_dock'):
            if checked:
                self.main_window.live_timing_dock.show()
            else:
                self.main_window.live_timing_dock.hide()
    
    def show_control_panel(self) -> None:
        """顯示 Live Timing 控制面板 Dock"""
        if hasattr(self.main_window, 'live_timing_dock'):
            self.main_window.live_timing_dock.show()
            if self._action_control_panel:
                self._action_control_panel.setChecked(True)
    
    def setup_menu(self, live_timing_menu: QMenu) -> None:
        """
        設置 Live Timing 選單項目
        
        通過配置表自動生成選單，取代手動創建 25 個選單項目
        
        Args:
            live_timing_menu: Live Timing 主選單
        """
        # 控制面板 - 可勾選切換
        self._action_control_panel = live_timing_menu.addAction(
            tr('menu_live_timing_control_panel', 'Show Control Panel')
        )
        self._action_control_panel.setCheckable(True)
        self._action_control_panel.setChecked(False)
        self._action_control_panel.setEnabled(True)
        self._action_control_panel.setStatusTip(
            tr('live_timing_control_panel_tip', 'Toggle Live Timing Control Panel')
        )
        self._action_control_panel.triggered.connect(self.toggle_control_panel)
        
        # 將引用保存到主視窗以供其他地方使用
        self.main_window._action_control_panel = self._action_control_panel
        
        live_timing_menu.addSeparator()
        
        # === 視覺化模組 ===
        self._add_module_action(live_timing_menu, 'track_map')
        self._add_module_action(live_timing_menu, 'circle_map')
        self._add_module_action(live_timing_menu, 'live_ranking')
        self._add_module_action(live_timing_menu, 'pit_window')
        self._add_module_action(live_timing_menu, 'tyre_strategy')
        self._add_module_action(live_timing_menu, 'driver_strategy')
        
        # Coming Soon 模組
        self._add_module_action(live_timing_menu, 'race_control')
        self._add_module_action(live_timing_menu, 'race_insights')
        self._add_module_action(live_timing_menu, 'shap_analysis')
        
        self._add_module_action(live_timing_menu, 'lap_distribution')
        
        # === Lap History 子選單 ===
        lap_history_menu = live_timing_menu.addMenu(
            tr('menu_live_timing_lap_history', 'Lap History')
        )
        self._add_module_action(lap_history_menu, 'lap_history_lap_time')
        self._add_module_action(lap_history_menu, 'lap_history_s1')
        self._add_module_action(lap_history_menu, 'lap_history_s2')
        self._add_module_action(lap_history_menu, 'lap_history_s3')
        lap_history_menu.addSeparator()
        logger.debug("[LiveTimingManager] Adding throttle_history to Lap History menu...")
        result = self._add_module_action(lap_history_menu, 'throttle_history')
        logger.debug(f"[LiveTimingManager] throttle_history action created: {result is not None}")
        logger.debug("[LiveTimingManager] Adding sf_percentage_chart to Lap History menu...")
        result_sf = self._add_module_action(lap_history_menu, 'sf_percentage_chart')
        logger.debug(f"[LiveTimingManager] sf_percentage_chart action created: {result_sf is not None}")
        
        # === Sector Comparison 子選單 ===
        sector_menu = live_timing_menu.addMenu(
            tr('menu_live_timing_sector_comparison', 'Sector Comparison')
        )
        self._add_module_action(sector_menu, 'sector_s1')
        self._add_module_action(sector_menu, 'sector_s2')
        self._add_module_action(sector_menu, 'sector_s3')
        
        # === Trace 模組 ===
        self._add_module_action(live_timing_menu, 'speed_trace')
        self._add_module_action(live_timing_menu, 'throttle_trace')
        self._add_module_action(live_timing_menu, 'brake_trace')
        self._add_module_action(live_timing_menu, 'gear_trace')
        self._add_module_action(live_timing_menu, 'drs_trace')
        self._add_module_action(live_timing_menu, 'rpm_trace')
        
        # === 進階分析 ===
        self._add_module_action(live_timing_menu, 'battle_insight')
        self._add_module_action(live_timing_menu, 'chase_strategy')
        self._add_module_action(live_timing_menu, 'track_weather')
        
        # Coming Soon
        self._add_module_action(live_timing_menu, 'pit_stop_table')
        
        live_timing_menu.addSeparator()
        
        # === 預設佈局子選單 ===
        presets_menu = live_timing_menu.addMenu(
            tr('menu_live_timing_presets', 'Preset Layouts')
        )
        
        action_preset_full = presets_menu.addAction(
            tr('menu_live_timing_preset_full', 'Full Layout')
        )
        action_preset_full.setEnabled(False)
        action_preset_full.setStatusTip(tr('live_timing_coming_soon', 'Coming Soon'))
        
        action_preset_compact = presets_menu.addAction(
            tr('menu_live_timing_preset_compact', 'Compact Layout')
        )
        action_preset_compact.setEnabled(False)
        action_preset_compact.setStatusTip(tr('live_timing_coming_soon', 'Coming Soon'))
        
        logger.debug("[LiveTimingManager] Menu setup completed")
    
    def _add_module_action(self, menu: QMenu, module_key: str) -> QAction:
        """
        添加模組選單項目
        
        Args:
            menu: 目標選單
            module_key: 模組鍵值
            
        Returns:
            創建的 QAction
        """
        config = self.MODULES.get(module_key)
        if not config:
            logger.warning(f"[LiveTimingManager] Unknown module key: {module_key}")
            return None
        
        logger.debug(f"[LiveTimingManager] _add_module_action: {module_key}, config: {config}")
        
        # 取得翻譯文字
        menu_text = tr(config['menu_key'], config['menu_default'])
        tip_text = tr(config['tip_key'], config['tip_default'])
        
        logger.debug(f"[LiveTimingManager] Menu text: '{menu_text}', Tip: '{tip_text}'")
        
        # 為禁用的模組添加標記
        if not config.get('enabled', True):
            if 'battle_insight' in module_key:
                menu_text = f"(Disabled) {menu_text}"
        
        action = menu.addAction(menu_text)
        action.setStatusTip(tip_text)
        action.setEnabled(config.get('enabled', True))
        
        # 使用 partial 綁定模組鍵值
        action.triggered.connect(partial(self.open_module, module_key))
        
        return action
    
    def get_modules_by_category(self) -> Dict[str, list]:
        """
        依類別分組取得模組
        
        Returns:
            依類別分組的模組字典
        """
        groups: Dict[str, list] = {}
        for key, config in self.MODULES.items():
            category = config.get('category', 'other')
            if category not in groups:
                groups[category] = []
            groups[category].append((key, config))
        return groups
    
    def get_enabled_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        取得所有已啟用的模組
        
        Returns:
            已啟用模組的配置字典
        """
        return {
            key: config 
            for key, config in self.MODULES.items() 
            if config.get('enabled', True)
        }
    
    def get_module_count(self) -> Dict[str, int]:
        """
        取得模組統計
        
        Returns:
            {'total': int, 'enabled': int, 'disabled': int}
        """
        total = len(self.MODULES)
        enabled = sum(1 for c in self.MODULES.values() if c.get('enabled', True))
        return {
            'total': total,
            'enabled': enabled,
            'disabled': total - enabled,
        }
