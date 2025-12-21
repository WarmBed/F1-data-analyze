"""
PopoutCliHandler - CLI 分析處理器

從 PopoutSubWindow 中提取的 CLI 分析邏輯。
負責處理 CLI 分析調用、進度顯示和 JSON 監控。

Phase 5.2 重構 - 從 f1t_gui_main.py 提取
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Callable

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from core.logger import get_logger
from typing import Dict
from typing import Optional
from PyQt5.QtCore import QTimer
from typing import Any
from typing import Callable

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class PopoutCliHandler:
    """
    CLI 分析處理器
    
    負責處理 PopoutSubWindow 中的 CLI 分析操作，包括：
    - 啟動/停止 CLI 分析執行緒
    - 顯示分析進度對話框
    - JSON 檔案監控
    - 超時處理
    """
    
    def __init__(self, popout_window: 'QWidget'):
        """
        初始化 CLI 分析處理器
        
        Args:
            popout_window: PopoutSubWindow 實例
        """
        self.window = popout_window
        self.cli_worker = None
        self.progress_dialog: Optional[QProgressDialog] = None
        self.json_check_timer: Optional[QTimer] = None
        self.max_wait_timer: Optional[QTimer] = None
        
    def call_cli_analysis(self, year: int, race: str, session: str, 
                          function_id: int = 13) -> None:
        """
        呼叫 CLI 進行分析 - 使用背景執行緒避免 GUI 凍結
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 場次代碼
            function_id: 功能 ID（預設 13 為速度分析）
        """
        # 如果已有分析在執行，先停止
        if self.cli_worker and self.cli_worker.isRunning():
            self.stop_cli_analysis()
        
        # 創建進度顯示
        self.show_analysis_progress()
        
        # 導入 CliAnalysisWorker
        try:
            # 嘗試從主模組導入
            from f1t_gui_main import CliAnalysisWorker
        except ImportError:
            logger.error("[ERROR] 無法導入 CliAnalysisWorker")
            self._show_error("導入錯誤", "無法載入 CLI 分析模組")
            return
        
        # 創建並啟動工作執行緒
        self.cli_worker = CliAnalysisWorker(year, race, session, function_id)
        
        # 連接信號
        self.cli_worker.progress_updated.connect(self.on_analysis_progress)
        self.cli_worker.analysis_completed.connect(self.on_analysis_completed)
        self.cli_worker.output_received.connect(self.on_analysis_output)
        
        # 啟動執行緒
        self.cli_worker.start()
        
        # 開始等待 JSON 產生
        self.start_json_monitoring(year, race, session)
        
        logger.debug(f"[START] CLI 分析執行緒已啟動: {year} {race} {session}")
    
    def stop_cli_analysis(self) -> None:
        """停止 CLI 分析"""
        if self.cli_worker and self.cli_worker.isRunning():
            self.cli_worker.stop()
            self.cli_worker.wait(5000)  # 等待最多 5 秒
            logger.debug("[TEST] CLI 分析已停止")
        
        # 停止 JSON 監控
        self.stop_json_monitoring()
        
        # 隱藏進度顯示
        self.hide_analysis_progress()
    
    def show_analysis_progress(self) -> None:
        """顯示分析進度對話框"""
        if self.progress_dialog is None:
            self.progress_dialog = QProgressDialog(
                "Executing F1 Data Analysis...", 
                "Cancel", 
                0, 0, 
                self.window
            )
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.canceled.connect(self.stop_cli_analysis)
        
        try:
            from core.gui_i18n import tr
            self.progress_dialog.setLabelText(tr("starting_cli_analysis"))
        except ImportError:
            self.progress_dialog.setLabelText("Starting CLI analysis...")
            
        self.progress_dialog.show()
    
    def hide_analysis_progress(self) -> None:
        """隱藏分析進度對話框"""
        if self.progress_dialog:
            self.progress_dialog.hide()
    
    def on_analysis_progress(self, message: str) -> None:
        """處理分析進度更新"""
        logger.debug(f"[STATS] {message}")
        if self.progress_dialog:
            self.progress_dialog.setLabelText(message)
    
    def on_analysis_output(self, output: str) -> None:
        """處理分析輸出"""
        logger.debug(f"[UPLOAD] CLI 輸出: {output}")
        
        if not self.progress_dialog:
            return
            
        # 根據輸出內容更新進度
        try:
            from core.gui_i18n import tr
            downloading_text = tr('downloading_data')
        except ImportError:
            downloading_text = "Downloading data"
            
        if "下載" in output or "Download" in output.lower():
            self.progress_dialog.setLabelText(f"{downloading_text} {output[:50]}...")
        elif "分析" in output or "Analysis" in output.lower():
            self.progress_dialog.setLabelText(f"正在分析數據... {output[:50]}...")
    
    def on_analysis_completed(self, success: bool, message: str) -> None:
        """處理分析完成"""
        logger.debug(f"[OK] CLI 分析完成: {success}, {message}")
        
        if success:
            if self.progress_dialog:
                self.progress_dialog.setLabelText("分析完成，正在載入結果...")
        else:
            logger.error(f"[ERROR] CLI 分析失敗: {message}")
            self._show_error("Analysis Failed", f"Error occurred during CLI analysis:\n{message}")
            self.hide_analysis_progress()
            self.stop_json_monitoring()
    
    def start_json_monitoring(self, year: int, race: str, session: str) -> None:
        """
        開始監控 JSON 檔案產生
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 場次代碼
        """
        # 停止任何現有的監控
        self.stop_json_monitoring()
        
        # 設置 JSON 檢查計時器
        self.json_check_timer = QTimer()
        self.json_check_timer.timeout.connect(
            lambda: self.check_json_ready(year, race, session)
        )
        self.json_check_timer.start(3000)  # 每 3 秒檢查一次
        
        # 設置最大等待時間 (120秒)
        self.max_wait_timer = QTimer()
        self.max_wait_timer.setSingleShot(True)
        self.max_wait_timer.timeout.connect(self.on_json_wait_timeout)
        self.max_wait_timer.start(120000)  # 120 秒超時
        
        logger.debug("開始監控 JSON 檔案產生... (最多等待120秒)")
    
    def stop_json_monitoring(self) -> None:
        """停止 JSON 監控"""
        if self.json_check_timer:
            self.json_check_timer.stop()
            self.json_check_timer = None
        if self.max_wait_timer:
            self.max_wait_timer.stop()
            self.max_wait_timer = None
    
    def check_json_ready(self, year: int, race: str, session: str) -> None:
        """
        檢查 JSON 是否已準備好
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 場次代碼
        """
        # 使用視窗的 try_load_json 方法
        if not hasattr(self.window, 'try_load_json'):
            logger.warning("[WARNING] 視窗沒有 try_load_json 方法")
            return
            
        json_data = self.window.try_load_json(year, race, session)
        
        if json_data:
            # JSON 已產生，停止監控
            self.stop_json_monitoring()
            
            logger.debug("[OK] JSON檔案已產生，開始載入資料")
            
            # 更新進度顯示
            if self.progress_dialog:
                self.progress_dialog.setLabelText("正在載入分析結果...")
            
            # 載入並顯示數據
            if hasattr(self.window, 'update_charts_and_analysis'):
                self.window.update_charts_and_analysis(json_data)
            
            # 隱藏進度顯示
            self.hide_analysis_progress()
        else:
            logger.debug("繼續等待 JSON 檔案產生...")
    
    def on_json_wait_timeout(self) -> None:
        """JSON 等待超時處理"""
        self.stop_json_monitoring()
        self.hide_analysis_progress()
        
        logger.debug("[TIME] JSON等待超時，分析可能失敗或仍在進行中")
        
        # 顯示超時警告
        self._show_warning(
            "分析超時", 
            "數據分析超時。\n\n可能原因：\n1. 網路連線緩慢\n2. 數據量過大\n3. 伺服器回應慢\n\n請稍後再試，或檢查網路連線。"
        )
    
    def _show_error(self, title: str, message: str) -> None:
        """顯示錯誤訊息"""
        parent = self.window if self.window else None
        QMessageBox.critical(parent, title, message)
    
    def _show_warning(self, title: str, message: str) -> None:
        """顯示警告訊息"""
        parent = self.window if self.window else None
        QMessageBox.warning(parent, title, message)
    
    def cleanup(self) -> None:
        """清理資源"""
        self.stop_cli_analysis()
        
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        self.cli_worker = None
