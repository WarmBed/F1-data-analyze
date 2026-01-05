#!/usr/bin/env python3
"""
TrafficAnalysisMDI - F1T 流量分析 MDI 視窗
==========================================

基於 UniversalAnalysisMDI 的流量分析模組，提供：
1. 超車難度分析
2. DRS Train 風險評估
3. Track Position Loss 分析
4. 全部賽道難度排名

Author: F1T Team
Date: 2025-01-05
Version: 1.0.0
"""

from typing import Optional, Any, Dict

from PyQt5.QtWidgets import QMessageBox, QWidget
from PyQt5.QtCore import pyqtSignal

from modules.gui.base.universal_analysis_mdi_base import (
    UniversalAnalysisMDI,
    AnalysisMDIConfig
)
from .traffic_data_loader import TrafficDataLoader
from .traffic_analysis_widget import TrafficAnalysisWidget

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger("traffic_analysis_mdi", component="gui")


class TrafficAnalysisMDI(UniversalAnalysisMDI):
    """流量分析 MDI 視窗"""
    
    # 額外信號
    circuit_analysis_completed = pyqtSignal(str, dict)
    
    def __init__(self, year: int = 2024, race: str = "Japan", 
                 session: str = "R", parent=None):
        """初始化流量分析 MDI
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽程類型
            parent: 父視窗
        """
        # 創建配置
        config = AnalysisMDIConfig(
            analysis_type="traffic_analysis",
            display_name=tr("流量分析"),
            icon_name="traffic",
            cli_function=100,  # f100 historical flags
            default_width=1200,
            default_height=800,
            requires_driver=False,
            requires_driver2=False,
            api_endpoint="/analyze",
            json_pattern="historical_flags_{race}_{years}.json"
        )
        
        super().__init__(
            config=config,
            year=year,
            race=race,
            session=session,
            parent=parent
        )
        
        self._debug_enabled = True
        self._initialize_traffic_module()
        
    def _initialize_traffic_module(self):
        """初始化流量分析模組"""
        self._debug(f"[INIT] {tr('初始化流量分析模組')}")
        
        # 設置數據載入器到圖表組件
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.chart_widget.set_data_loader(self.data_manager)
            
            # 連接信號
            self.chart_widget.analysis_requested.connect(self._on_analysis_requested)
        
        # 載入所有賽道排名
        self._load_all_circuits_ranking()
        
    def create_data_manager(self) -> TrafficDataLoader:
        """創建數據管理器
        
        Returns:
            TrafficDataLoader 實例
        """
        self._debug(f"[CREATE] {tr('創建 TrafficDataLoader')}")
        return TrafficDataLoader(debug_enabled=self._debug_enabled)
    
    def create_chart_widget(self) -> TrafficAnalysisWidget:
        """創建圖表組件
        
        Returns:
            TrafficAnalysisWidget 實例
        """
        self._debug(f"[CREATE] {tr('創建 TrafficAnalysisWidget')}")
        return TrafficAnalysisWidget()
    
    def _load_all_circuits_ranking(self):
        """載入所有賽道的難度排名"""
        if not self.data_manager:
            return
            
        self._debug(f"[RANKING] {tr('載入全部賽道難度排名')}")
        
        # 獲取所有賽道難度數據
        circuits_data = self.data_manager.get_all_circuits_difficulty()
        
        # 填充排名表
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.chart_widget.populate_ranking_table(circuits_data)
            
        self._debug(f"[RANKING] {tr('載入完成')}: {len(circuits_data)} {tr('個賽道')}")
    
    def _on_analysis_requested(self, race: str):
        """處理分析請求
        
        Args:
            race: 賽事名稱
        """
        self._debug(f"[ANALYSIS] {tr('分析請求')}: {race}")
        
        # 更新當前賽事
        self._race = race
        
        # 執行分析
        if self.data_manager:
            difficulty = self.data_manager.calculate_overtaking_difficulty(race)
            self.circuit_analysis_completed.emit(race, difficulty)
            
            # 記錄結果
            self._debug(f"[ANALYSIS] {tr('分析完成')}: {race} - "
                       f"{tr('難度分數')}: {difficulty.get('difficulty_score', 0):.2f}")
    
    def _on_data_loaded(self, data: Any):
        """數據載入完成回調
        
        Args:
            data: 載入的數據
        """
        self._debug(f"[DATA] {tr('數據載入完成')}")
        
        # 如果有當前賽事，自動分析
        if hasattr(self, '_race') and self._race:
            if hasattr(self, 'chart_widget') and self.chart_widget:
                self.chart_widget.analyze_circuit(self._race)
    
    def _show_error(self, title: str, message: str):
        """顯示錯誤訊息
        
        Args:
            title: 錯誤標題
            message: 錯誤訊息
        """
        parent_widget = self.chart_widget if hasattr(self, 'chart_widget') else None
        QMessageBox.critical(parent_widget, title, message)
    
    def _debug(self, message: str):
        """輸出調試訊息
        
        Args:
            message: 調試訊息
        """
        if self._debug_enabled:
            logger.debug("[TRAFFIC_MDI] %s", message)
    
    def refresh_data(self):
        """刷新數據"""
        self._debug(f"[REFRESH] {tr('刷新數據')}")
        self._load_all_circuits_ranking()
        
        if hasattr(self, 'chart_widget') and self.chart_widget:
            current_race = self.chart_widget.circuit_combo.currentText()
            if current_race:
                self.chart_widget.analyze_circuit(current_race)
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """獲取分析摘要
        
        Returns:
            分析摘要字典
        """
        summary = {
            "module": "traffic_analysis",
            "year": self._year,
            "race": getattr(self, '_race', None),
            "session": self._session
        }
        
        if self.data_manager and hasattr(self, '_race'):
            difficulty = self.data_manager.calculate_overtaking_difficulty(self._race)
            summary["difficulty_score"] = difficulty.get("difficulty_score", 0)
            summary["difficulty_level"] = difficulty.get("difficulty_level", "UNKNOWN")
        
        return summary
