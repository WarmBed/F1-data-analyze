#!/usr/bin/env python3
"""
F101 起跑反應分析 MDI 視窗
Start Reaction Analysis MDI

管理起跑反應分析的 MDI 視窗，整合資料載入和顯示元件

作者: F1T Team
日期: 2025-12-22
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal

import logging

from core.gui_i18n import tr

# 導入基類
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# 導入組件
from .start_reaction_widget import StartReactionWidget
from .start_reaction_loader import StartReactionDataLoader

logger = logging.getLogger(__name__)


class StartReactionWorker(QThread):
    """起跑反應數據載入工作執行緒"""
    
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, year: int, race: str, session: str = "R"):
        super().__init__()
        self.year = year
        self.race = race
        self.session = session
    
    def run(self):
        try:
            self.progress.emit(20)
            
            # 載入數據
            loader = StartReactionDataLoader(self.year, self.race, self.session)
            
            self.progress.emit(50)
            
            data = loader.load_data()
            
            self.progress.emit(90)
            
            if data:
                self.success.emit(data)
            else:
                self.failure.emit(tr("no_data_found", "No data found for this race"))
            
        except Exception as e:
            logger.error(f"[START_REACTION_WORKER] Error: {e}")
            import traceback
            traceback.print_exc()
            self.failure.emit(str(e))
        finally:
            self.progress.emit(100)


class StartReactionAnalysisMDI(UniversalAnalysisMDI):
    """
    起跑反應分析 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理
    """
    
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="start_reaction",
                display_name=tr("start_reaction_analysis", "Start Reaction Analysis"),
                default_size=(1400, 800),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("start_reaction", config)
            cls._REGISTERED = True
            logger.info("[START_REACTION_MDI] Module type registered")
    
    def __init__(self, parent=None):
        """初始化 MDI 視窗"""
        logger.debug("[START_REACTION_MDI] Initializing...")
        
        self.ensure_registered()
        
        super().__init__(analysis_type="start_reaction", parent=parent)
        
        # 初始化參數
        self.year = None
        self.race = None
        self.session = None
        
        # 組件引用
        self.chart_widget = None
        self._worker = None
        
        # 狀態
        self._current_data = None
        self._is_data_loaded = False
        
        logger.debug("[START_REACTION_MDI] Base init complete")
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組"""
        try:
            logger.debug("[START_REACTION_MDI] Starting module initialization...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.error("[START_REACTION_MDI] Missing current_year")
                return False
            
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.error("[START_REACTION_MDI] Missing current_race")
                return False
            
            if not hasattr(self, 'current_session') or not self.current_session:
                logger.error("[START_REACTION_MDI] Missing current_session")
                return False
            
            # 設置參數
            self.year = int(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.info(f"[START_REACTION_MDI] Params: {self.year} {self.race} {self.session}")
            
            # 創建圖表組件
            self.chart_widget = self.create_chart_widget()
            if not self.chart_widget:
                logger.error("[START_REACTION_MDI] Failed to create chart_widget")
                return False
            
            # 設置 UI
            self._setup_ui()
            
            # 註冊到分析管理器
            self._register_to_analysis_manager()
            
            # 標記已初始化
            self._initialized = True
            
            # 載入初始數據
            self.load_initial_data()
            
            logger.info("[START_REACTION_MDI] Module initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"[START_REACTION_MDI] Init failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_data_manager(self):
        """創建資料管理器（此模組使用 Worker）"""
        return None
    
    def create_chart_widget(self) -> StartReactionWidget:
        """創建圖表元件"""
        logger.debug("[START_REACTION_MDI] Creating StartReactionWidget")
        return StartReactionWidget()
    
    def _setup_ui(self):
        """設置 UI 佈局"""
        # 主容器 - 使用 self.main_widget 來與基類保持一致
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 標題列
        header_layout = QHBoxLayout()
        
        title_text = f"F101 - {tr('start_reaction_analysis', 'Start Reaction Analysis')}"
        title_label = QLabel(f"<h3>{title_text}</h3>")
        header_layout.addWidget(title_label)
        
        # 賽事資訊
        race_info = QLabel(f"<b>{self.year} {self.race} - {self.session}</b>")
        header_layout.addWidget(race_info)
        
        header_layout.addStretch()
        
        # 刷新按鈕
        self.refresh_btn = QPushButton(tr("refresh", "Refresh"))
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 圖表區域
        if self.chart_widget:
            main_layout.addWidget(self.chart_widget, 1)
    
    def load_initial_data(self):
        """載入初始數據"""
        logger.debug("[START_REACTION_MDI] Loading initial data...")
        self._load_data()
    
    def _load_data(self):
        """載入數據"""
        if self._worker and self._worker.isRunning():
            logger.warning("[START_REACTION_MDI] Worker already running")
            return
        
        # 顯示進度條
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.refresh_btn.setEnabled(False)
        
        # 創建工作執行緒
        self._worker = StartReactionWorker(self.year, self.race, self.session)
        self._worker.progress.connect(self._on_progress)
        self._worker.success.connect(self._on_data_loaded)
        self._worker.failure.connect(self._on_load_failed)
        self._worker.start()
    
    @pyqtSlot(int)
    def _on_progress(self, value: int):
        """進度更新"""
        self.progress_bar.setValue(value)
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """數據載入成功"""
        logger.info(f"[START_REACTION_MDI] Data loaded: {len(data.get('drivers', []))} drivers")
        
        self._current_data = data
        self._is_data_loaded = True
        
        # 更新顯示
        if self.chart_widget:
            self.chart_widget.update_data(data)
        
        # 隱藏進度條
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
    
    @pyqtSlot(str)
    def _on_load_failed(self, error_msg: str):
        """數據載入失敗"""
        logger.error(f"[START_REACTION_MDI] Load failed: {error_msg}")
        
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        
        QMessageBox.warning(
            self.widget() if hasattr(self, 'widget') else None,
            tr("error", "Error"),
            f"{tr('load_failed', 'Failed to load data')}:\n{error_msg}"
        )
    
    @pyqtSlot()
    def _on_refresh_clicked(self):
        """刷新按鈕點擊"""
        logger.debug("[START_REACTION_MDI] Refresh clicked")
        self._load_data()
    
    def _register_to_analysis_manager(self):
        """註冊到分析模組管理器"""
        try:
            from windows.managers.analysis_module_manager import AnalysisModuleManager
            manager = AnalysisModuleManager.instance()
            if manager:
                manager.register_module(self, "start_reaction")
                logger.debug("[START_REACTION_MDI] Registered to analysis manager")
        except Exception as e:
            logger.warning(f"[START_REACTION_MDI] Failed to register: {e}")
    
    def closeEvent(self, event):
        """關閉事件"""
        # 停止工作執行緒
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(1000)
        
        super().closeEvent(event)
