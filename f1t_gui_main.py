#!/usr/bin/env python3
"""
F1T GUI 主程式 - 專業賽車分析工作站
F1T GUI Main - Professional Racing Analysis Workstation
集成的F1分析GUI系統，提供完整的賽車數據分析功能
"""

import sys
import os
import math
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMdiArea, QMdiSubWindow, QTableWidget, QTableWidgetItem,
    QSplitter, QLineEdit, QStatusBar, QLabel, QProgressBar, QGroupBox,
    QFrame, QToolBar, QAction, QMenuBar, QMenu, QGridLayout, QLCDNumber,
    QTextEdit, QScrollArea, QHeaderView, QDialog, QDialogButtonBox, QMessageBox,
    QListWidget, QListWidgetItem, QSpinBox, QSizePolicy, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPointF, QPoint, QObject, QRect, QThread
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPainter, QPen, QBrush, QMouseEvent
import json
import datetime
import traceback
import subprocess
import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

import core.dependency_guard  # noqa: F401  # 確保可選依賴存在

from core.logger import setup_logging, get_logger

# 🔧 日誌系統配置：
# - level="INFO" : 降低日誌等級（不再顯示 DEBUG 訊息）
# - console_level=None : 已停用終端機輸出（在 logger.py 中移除 console handler）
# - 日誌檔案：logs/f1_gui_2025-10-06.log（依日期自動切換）
setup_logging(component="gui", level="INFO", console_level=None)
logger = get_logger("main", component="gui")
logger.info("F1T GUI 控制台初始化完成 - 日誌系統已啟用 (INFO level, 僅檔案輸出)")

# 導入連動管理器
from modules.gui.lap_analysis.linkage import linkage_manager

# 導入 GUI 國際化模組
from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr, set_gui_language, get_gui_language, get_telemetry_option_text
from core.gui_help_catalog import get_gui_help_message
from core.gui_settings_manager import gui_settings_manager
from core.runtime_status_resolver import (
    RuntimeStatusResolver,
    RuntimeStatusState,
    RuntimeStatusView,
)
from modules.gui.shared.season_calendar_provider import (
    SeasonCalendarError,
    SeasonCalendarProvider,
    SeasonEvent,
)
from modules.gui.themes import ColorPaletteError, color_palette_provider

# 自定義QMdiArea類 - 強制執行子視窗最小尺寸
class CustomMdiArea(QMdiArea):
    """自定義MDI區域，強制執行子視窗最小尺寸限制並啟用內建功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 啟用MDI的內建功能
        self.setActivationOrder(QMdiArea.CreationOrder)  # 設置視窗激活順序
        self.setViewMode(QMdiArea.SubWindowView)  # 確保使用子視窗模式
        
        # 啟用右鍵選單和視窗管理功能
        self.setContextMenuPolicy(Qt.DefaultContextMenu)  # 啟用預設右鍵選單
        
        # 允許拖拉視窗
        self.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True)  # 不自動最大化
        
        #print(f"[LOCK] CustomMdiArea: 初始化完成，已啟用內建右鍵選單和視窗管理功能")
        
    def contextMenuEvent(self, event):
        """處理右鍵選單事件"""
        # 獲取滑鼠位置下的子視窗
        widget_at_pos = self.childAt(event.pos())
        subwindow = None
        
        # 向上查找，尋找 QMdiSubWindow
        current_widget = widget_at_pos
        while current_widget and subwindow is None:
            if isinstance(current_widget, QMdiSubWindow):
                subwindow = current_widget
                break
            # 檢查父元件是否為 QMdiSubWindow
            parent = current_widget.parent()
            if isinstance(parent, QMdiSubWindow):
                subwindow = parent
                break
            current_widget = parent
        
        if subwindow:
            # 如果在子視窗上右鍵，顯示視窗管理選單
            menu = QMenu(self)
            
            # 添加視窗管理選項
            cascade_action = menu.addAction("層疊視窗 (&C)")
            cascade_action.triggered.connect(self.cascadeSubWindows)
            
            tile_action = menu.addAction("平舖視窗 (&T)")
            tile_action.triggered.connect(self.tileSubWindows)
            
            menu.addSeparator()
            
            close_action = menu.addAction("關閉視窗 (&X)")
            close_action.triggered.connect(subwindow.close)
            
            close_all_action = menu.addAction(tr("close_all_windows", "Close All Windows (&A)"))
            close_all_action.triggered.connect(self.closeAllSubWindows)
            
            menu.addSeparator()
            
            # 視窗狀態選項
            if subwindow.isMaximized():
                restore_action = menu.addAction("還原視窗 (&R)")
                restore_action.triggered.connect(subwindow.showNormal)
            else:
                maximize_action = menu.addAction("最大化視窗 (&M)")
                maximize_action.triggered.connect(subwindow.showMaximized)
            
            minimize_action = menu.addAction("最小化視窗 (&N)")
            minimize_action.triggered.connect(subwindow.showMinimized)
            
            # 顯示選單
            menu.exec_(event.globalPos())
        else:
            # 如果在空白區域右鍵，顯示區域管理選單
            menu = QMenu(self)
            
            cascade_action = menu.addAction("層疊所有視窗 (&C)")
            cascade_action.triggered.connect(self.cascadeSubWindows)
            
            tile_action = menu.addAction("平舖所有視窗 (&T)")
            tile_action.triggered.connect(self.tileSubWindows)
            
            menu.addSeparator()
            
            close_all_action = menu.addAction(tr("close_all_windows", "Close All Windows (&A)"))
            close_all_action.triggered.connect(self.closeAllSubWindows)
            
            # 顯示選單
            menu.exec_(event.globalPos())
        
    def addSubWindow(self, widget, flags=None):
        """添加子視窗並強制執行最小尺寸 - 簡化版本"""
        #print(f"[LOCK] CustomMdiArea: addSubWindow 被調用，widget 類型: {type(widget)}")
        
        if flags is not None:
            subwindow = super().addSubWindow(widget, flags)
        else:
            subwindow = super().addSubWindow(widget)
            
        #print(f"[LOCK] CustomMdiArea: 創建的子視窗類型: {type(subwindow)}")
        
        # 移除最小尺寸限制，允許完全自由縮放
        if isinstance(subwindow, PopoutSubWindow):
            # 不設置最小尺寸限制
            #print(f"[LOCK] CustomMdiArea: 子視窗無尺寸限制")
            pass
        
        # [修改] 保留邊框，使用CSS隱藏標題列
        if subwindow:
            # 不再設置 FramelessWindowHint，以保留邊框
            # subwindow.setWindowFlags(subwindow.windowFlags() | Qt.FramelessWindowHint)
            
            # 使用樣式表隱藏標題列但保留邊框
            subwindow.setStyleSheet("""
                QMdiSubWindow::title {
                    height: 0px;
                    margin: 0px;
                    padding: 0px;
                    background: transparent;
                    border: none;
                }
                QMdiSubWindow {
                    border: 2px solid #666666;
                    border-radius: 2px;
                    background-color: #FFFFFF;
                }
            """)
            #print(f"[LOCK] CustomMdiArea: 已隱藏標題列但保留邊框")
        
        return subwindow

# CLI 分析工作執行緒
class CliAnalysisWorker(QThread):
    """背景執行 CLI 分析的工作執行緒"""
    
    # 定義信號
    progress_updated = pyqtSignal(str)  # 進度更新信號
    analysis_completed = pyqtSignal(bool, str)  # 分析完成信號 (成功/失敗, 訊息)
    output_received = pyqtSignal(str)  # 輸出信號
    
    def __init__(self, year, race, session, force_mode=1, parent=None):
        super().__init__(parent)
        self.year = year
        self.race = race
        self.session = session
        self.force_mode = force_mode
        self.process = None
        self.should_stop = False
        
    def run(self):
        """執行 CLI 分析"""
        try:
            # 構建CLI命令
            cmd = [
                sys.executable,
                "f1_analysis_modular_main.py",
                "-f", str(self.force_mode),  # 使用指定的 force_mode
                "-y", str(self.year),
                "-r", self.race,
                "-s", self.session
            ]
            
            print(f"[DEBUG] [CLI_WORKER] 準備執行命令: {' '.join(cmd)}")
            print(f"[DEBUG] [CLI_WORKER] 工作目錄: {os.getcwd()}")
            
            self.progress_updated.emit(f"啟動 CLI 分析: {self.year} {self.race} {self.session}")
            
            # 設置環境變數以確保正確的編碼
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSFS'] = '0'
            
            print(f"[DEBUG] [CLI_WORKER] 環境變數已設置: PYTHONIOENCODING=utf-8")
            
            # 啟動進程，使用 UTF-8 編碼避免編碼問題
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # 遇到無法解碼的字符時替換為 ?
                env=env,  # 使用自定義環境變數
                cwd=os.getcwd(),
                bufsize=1,
                universal_newlines=True
            )
            
            print(f"[DEBUG] [CLI_WORKER] 進程已啟動，PID: {self.process.pid}")
            self.progress_updated.emit(f"CLI 分析已啟動 (PID: {self.process.pid})")
            
            # 即時讀取輸出
            while True:
                if self.should_stop:
                    if self.process:
                        self.process.terminate()
                    break
                    
                # 檢查進程是否完成
                if self.process.poll() is not None:
                    break
                    
                # 讀取輸出，處理編碼問題
                try:
                    output = self.process.stdout.readline()
                    if output:
                        self.output_received.emit(output.strip())
                except UnicodeDecodeError as e:
                    # 如果遇到編碼錯誤，記錄但不中斷
                    self.output_received.emit(f"[編碼錯誤] 無法解碼部分輸出: {str(e)}")
                    
                # 短暫休息避免CPU占用過高
                self.msleep(100)
            
            # 獲取最終結果
            if not self.should_stop:
                return_code = self.process.wait()
                print(f"[DEBUG] [CLI_WORKER] 進程結束，返回碼: {return_code}")
                
                if return_code == 0:
                    print(f"[DEBUG] [CLI_WORKER] CLI 分析成功完成")
                    self.analysis_completed.emit(True, "CLI 分析成功完成")
                else:
                    print(f"[DEBUG] [CLI_WORKER] CLI 分析失敗，返回碼: {return_code}")
                    try:
                        stderr_output = self.process.stderr.read()
                        print(f"[DEBUG] [CLI_WORKER] 錯誤輸出: {stderr_output}")
                        self.analysis_completed.emit(False, f"CLI 分析失敗: {stderr_output}")
                    except UnicodeDecodeError as e:
                        print(f"[DEBUG] [CLI_WORKER] 錯誤輸出編碼問題: {str(e)}")
                        self.analysis_completed.emit(False, f"CLI 分析失敗 (編碼錯誤): {str(e)}")
            else:
                print(f"[DEBUG] [CLI_WORKER] 分析被用戶取消")
                self.analysis_completed.emit(False, "分析被用戶取消")
                
        except Exception as e:
            self.analysis_completed.emit(False, f"CLI 分析錯誤: {str(e)}")
    
    def stop(self):
        """停止分析"""
        self.should_stop = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                # 等待進程結束，如果沒有回應則強制終止
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

# 全域信號管理器
class GlobalSignalManager(QObject):
    """全域信號管理器 - 用於跨視窗同步"""
    sync_x_position = pyqtSignal(int)  # X軸位置同步信號 (滑鼠位置)
    sync_x_range = pyqtSignal(float, float)  # X軸範圍同步信號 (偏移, 縮放)
    
    # 新增：遙測分析模組連動信號 (獨立於同步功能)
    lap_analysis_x_linkage = pyqtSignal(float, float)  # 遙測分析X軸連動信號 (距離值, Y軸相對位置)
    lap_analysis_x_clear = pyqtSignal()  # 遙測分析X軸清除信號
    
    # 新增：遙測分析點擊連動信號
    lap_analysis_click_linkage = pyqtSignal(float)  # 遙測分析點擊連動信號 (距離值)
    lap_analysis_click_clear = pyqtSignal()  # 遙測分析點擊清除信號
    
    # 新增：遙測分析連動控制信號
    lap_analysis_master_linkage_changed = pyqtSignal(bool)  # 總開關狀態變更信號
    
    def __init__(self):
        super().__init__()
        # 遙測分析連動總開關狀態
        self.lap_analysis_linkage_master_enabled = True
        
    def set_lap_linkage_enabled(self, enabled: bool):
        """設置遙測分析連動總開關狀態"""
        self.lap_analysis_linkage_master_enabled = enabled
        self.lap_analysis_master_linkage_changed.emit(enabled)
        print(f"[GLOBAL_SIGNALS] 遙測分析連動總開關: {'啟用' if enabled else '停用'}")
    
    def is_lap_linkage_enabled(self) -> bool:
        """檢查遙測分析連動總開關是否啟用"""
        return self.lap_analysis_linkage_master_enabled
        
# 創建全域信號管理器實例
global_signals = GlobalSignalManager()

# CLI 分析管理器
class CliAnalysisManager(QObject):
    """統一的 CLI 分析管理器 - 業務服務層"""
    
    # 定義信號
    analysis_started = pyqtSignal(str, str, str, str)  # (request_id, year, race, session)
    analysis_progress = pyqtSignal(str, str)  # (request_id, message)
    analysis_output = pyqtSignal(str, str)  # (request_id, output)
    analysis_completed = pyqtSignal(str, bool, str)  # (request_id, success, message)
    json_ready = pyqtSignal(str, dict)  # (request_id, json_data)
    
    def __init__(self):
        super().__init__()
        self.active_requests = {}  # 存儲活動的請求
        self.worker_threads = {}   # 存儲工作線程
        
    def request_analysis(self, year, race, session, force_mode=1, requester_id=None):
        """請求 CLI 分析"""
        import uuid
        request_id = str(uuid.uuid4())
        
        # 記錄請求者
        self.active_requests[request_id] = {
            'year': year,
            'race': race, 
            'session': session,
            'requester_id': requester_id,
            'status': 'starting'
        }
        
        # 創建工作線程
        worker = CliAnalysisWorker(year, race, session, force_mode)
        worker.progress_updated.connect(lambda msg: self.analysis_progress.emit(request_id, msg))
        worker.output_received.connect(lambda output: self.analysis_output.emit(request_id, output))
        worker.analysis_completed.connect(lambda success, msg: self._on_analysis_completed(request_id, success, msg))
        
        # 存儲並啟動線程
        self.worker_threads[request_id] = worker
        worker.start()
        
        # 發送開始信號
        self.analysis_started.emit(request_id, year, race, session)
        
        # 開始監控 JSON 文件
        self._start_json_monitoring(request_id, year, race, session)
        
        print(f"[START] CLI分析請求已創建: {request_id} ({year} {race} {session})")
        return request_id
    
    def cancel_analysis(self, request_id):
        """取消分析"""
        if request_id in self.worker_threads:
            worker = self.worker_threads[request_id]
            if worker.isRunning():
                worker.stop()
                worker.wait(5000)
            del self.worker_threads[request_id]
            
        if request_id in self.active_requests:
            del self.active_requests[request_id]
            
        print(f"[STOP] CLI分析已取消: {request_id}")
    
    def _on_analysis_completed(self, request_id, success, message):
        """處理分析完成"""
        self.analysis_completed.emit(request_id, success, message)
        
        # 清理線程
        if request_id in self.worker_threads:
            del self.worker_threads[request_id]
            
        print(f"[OK] CLI分析完成: {request_id}, 成功: {success}")
    
    def _start_json_monitoring(self, request_id, year, race, session):
        """開始監控 JSON 文件產生"""
        if request_id not in self.active_requests:
            return
            
        # 創建計時器監控 JSON 文件
        timer = QTimer()
        timer.timeout.connect(lambda: self._check_json_ready(request_id, year, race, session, timer))
        timer.start(3000)  # 每3秒檢查一次
        
        # 保存計時器引用
        self.active_requests[request_id]['json_timer'] = timer
        
        # 設置超時 (120秒)
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(lambda: self._on_json_timeout(request_id, timer, timeout_timer))
        timeout_timer.start(120000)
        
        self.active_requests[request_id]['timeout_timer'] = timeout_timer
    
    def _check_json_ready(self, request_id, year, race, session, timer):
        """檢查 JSON 是否準備好"""
        if request_id not in self.active_requests:
            timer.stop()
            return
            
        # 嘗試載入 JSON
        json_data = self._try_load_json(year, race, session)
        if json_data:
            # JSON 已產生
            timer.stop()
            if 'timeout_timer' in self.active_requests[request_id]:
                self.active_requests[request_id]['timeout_timer'].stop()
            
            self.json_ready.emit(request_id, json_data)
            print(f"📄 JSON已準備好: {request_id}")
            
            # 清理請求
            if request_id in self.active_requests:
                del self.active_requests[request_id]
    
    def _on_json_timeout(self, request_id, timer, timeout_timer):
        """JSON 等待超時"""
        timer.stop()
        timeout_timer.stop()
        
        self.analysis_completed.emit(request_id, False, "JSON等待超時")
        
        if request_id in self.active_requests:
            del self.active_requests[request_id]
        
        print(f"[TIME] JSON等待超時: {request_id}")
    
    def _try_load_json(self, year, race, session):
        """嘗試載入 JSON 檔案"""
        import glob
        import os
        import json
        
        # 搜尋模式與原有邏輯保持一致
        json_patterns = [
            f"json/rain_analysis_{year}_{race}_{session}.json",
            f"json/*{year}*{race}*{session}*.json",
            f"json_exports/*{year}*{race}*{session}*.json", 
            f"cache/*{year}*{race}*{session}*.json"
        ]
        
        for pattern in json_patterns:
            if '*' in pattern:
                json_files = glob.glob(pattern)
                if json_files:
                    pattern = json_files[0]  # 使用第一個匹配的文件
            
            if os.path.exists(pattern):
                try:
                    with open(pattern, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"[ERROR] JSON載入錯誤 {pattern}: {e}")
        
        return None
    
    def cleanup_all(self):
        """清理所有活動的分析"""
        print(f"[CLEANUP] 🔍 檢查活動的分析請求: {len(self.active_requests)} 個")
        
        if not self.active_requests:
            print("[CLEANUP] ℹ️ 沒有活動的分析請求需要清理")
        else:
            print(f"[CLEANUP] 🧹 開始清理 {len(self.active_requests)} 個活動請求...")
            
        for i, request_id in enumerate(list(self.active_requests.keys())):
            print(f"[CLEANUP] 🛑 正在取消分析請求 {i+1}/{len(self.active_requests)}: {request_id}")
            self.cancel_analysis(request_id)
            print(f"[CLEANUP] ✅ 分析請求已取消: {request_id}")
            
        print("[CLEANUP] 🧹 CLI分析管理器已清理所有資源")

# 創建全域 CLI 分析管理器實例
cli_analysis_manager = CliAnalysisManager()

class MainWindowParameterProvider:
    """主視窗參數提供者 - 實現 IParameterProvider 介面"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def get_current_year(self) -> str:
        """從主視窗獲取當前年份"""
        try:
            if hasattr(self.main_window, 'get_selected_year'):
                return str(self.main_window.get_selected_year())
            if hasattr(self.main_window, 'year_combo') and self.main_window.year_combo:
                return self.main_window.year_combo.currentText()
        except Exception as e:
            print(f"[WARNING] [PARAM_PROVIDER] 獲取年份失敗: {e}")
        return "2025"  # 預設值
    
    def get_current_race(self) -> str:
        """從主視窗獲取當前賽事"""
        try:
            if hasattr(self.main_window, 'get_selected_race_key'):
                return self.main_window.get_selected_race_key()
            if hasattr(self.main_window, 'race_combo') and self.main_window.race_combo:
                return self.main_window.race_combo.currentText()
        except Exception as e:
            print(f"[WARNING] [PARAM_PROVIDER] 獲取賽事失敗: {e}")
        return "Japan"  # 預設值
    
    def get_current_session(self) -> str:
        """從主視窗獲取當前賽段"""
        try:
            if hasattr(self.main_window, 'get_selected_session_code'):
                return self.main_window.get_selected_session_code()
            if hasattr(self.main_window, 'session_combo') and self.main_window.session_combo:
                return self.main_window.session_combo.currentText()
        except Exception as e:
            print(f"[WARNING] [PARAM_PROVIDER] 獲取賽段失敗: {e}")
        return "R"  # 預設值

class LapAnalysisOptionsDialog(QDialog):
    """遙測分析選項對話框 - 讓使用者選擇要顯示的遙測圖表和車手"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 保留用戶當前語言設定，不強制切換
        # set_gui_language('en')  # 已移除強制設定
        
        self.setWindowTitle(tr("telemetry_options_title"))
        self.setModal(True)
        self.setFixedSize(420, 520)
        
        # 設置字體 - 與主程式保持一致
        font = QFont("Arial", 8)  # 與主程式app.setFont(font)一致
        self.setFont(font)
        
        # 設置視窗樣式 - 採用主程式風格
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                color: #333333;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
            }
            QListWidget {
                background-color: #f9f9f9;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                padding: 2px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
                alternate-background-color: #f0f0f0;
            }
            QListWidget::item {
                padding: 3px 8px;
                border-bottom: 1px solid #e8e8e8;
                min-height: 16px;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
            }
            QListWidget::item:selected {
                background-color: #d1e7dd;
                color: #333333;
                border: 1px solid #a3cfbb;
            }
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 8pt;
                padding: 4px 12px;
                min-height: 18px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
            QLabel {
                color: #333333;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
            }
            QComboBox {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                padding: 2px 5px;
                font-size: 8pt;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                min-height: 18px;
            }
            QComboBox:hover {
                border: 1px solid #999999;
            }
            QComboBox::drop-down {
                border: none;
                width: 15px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid #999999;
                width: 3px;
                height: 3px;
                border-top: none;
                border-left: none;
                margin-right: 3px;
            }
            QLineEdit {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                padding: 2px 5px;
                font-size: 8pt;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                min-height: 18px;
            }
            QLineEdit:hover {
                border: 1px solid #999999;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
            QCheckBox {
                color: #333333;
                font-size: 8pt;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #999999;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
            }
            QCheckBox::indicator:checked:before {
                content: "✓";
                color: white;
                font-weight: bold;
                text-align: center;
            }
            QGroupBox {
                color: #333333;
                font-weight: bold;
                font-size: 8pt;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 5px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
                background: #f0f0f0;
            }
        """)
        
        self.init_ui()
        self.selected_charts = []
        
    def init_ui(self):
        """初始化使用者介面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 標題
        title_label = QLabel(tr("select_telemetry_charts"))
        title_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #333333; margin-bottom: 5px; font-family: 'Arial', 'Microsoft JhengHei', sans-serif;")
        layout.addWidget(title_label)
        
        # 車手選擇區域
        driver_group = QGroupBox(tr("driver_lap_selection"))
        driver_layout = QGridLayout(driver_group)
        driver_layout.setSpacing(8)
        
        # 車手1 (必選)
        driver1_label = QLabel(tr("driver1_required"))
        self.driver1_combo = QComboBox()
        self.driver1_combo.setFixedWidth(100)
        driver_layout.addWidget(driver1_label, 0, 0)
        driver_layout.addWidget(self.driver1_combo, 0, 1)
        
        # 車手1圈數
        lap1_label = QLabel(tr("lap_number"))
        self.lap1_input = QLineEdit()
        self.lap1_input.setText("1")
        self.lap1_input.setFixedWidth(50)
        self.lap1_input.setPlaceholderText(tr("lap", "Lap"))
        driver_layout.addWidget(lap1_label, 0, 2)
        driver_layout.addWidget(self.lap1_input, 0, 3)
        
        # 車手2 (選用)
        driver2_label = QLabel(tr("driver2_optional"))
        self.driver2_combo = QComboBox()
        self.driver2_combo.setFixedWidth(100)
        self.driver2_combo.addItem(tr("none_option", "None"), None)  # 第一個選項為無
        driver_layout.addWidget(driver2_label, 1, 0)
        driver_layout.addWidget(self.driver2_combo, 1, 1)
        
        # 車手2圈數
        lap2_label = QLabel(tr("lap_number"))
        self.lap2_input = QLineEdit()
        self.lap2_input.setText("1")
        self.lap2_input.setFixedWidth(50)
        self.lap2_input.setPlaceholderText(tr("lap", "Lap"))
        driver_layout.addWidget(lap2_label, 1, 2)
        driver_layout.addWidget(self.lap2_input, 1, 3)
        
        # 最速圈勾選框
        self.fastest_lap_checkbox = QCheckBox(tr("fastest_lap_option", "Fastest Lap"))
        self.fastest_lap_checkbox.setMinimumWidth(110)
        self.fastest_lap_checkbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.fastest_lap_checkbox.setChecked(False)
        self.fastest_lap_checkbox.stateChanged.connect(self._on_fastest_lap_changed)
        driver_layout.addWidget(self.fastest_lap_checkbox, 0, 4, 2, 1)  # 跨兩行放在右邊
        
        # 設置列寬度比例
        driver_layout.setColumnStretch(4, 1)  # 添加彈性空間
        
        layout.addWidget(driver_group)
        
        # 載入可用車手
        self._load_available_drivers()
        
        # 創建列表控件 - 更緊湊的設計
        telemetry_group = QGroupBox(tr("telemetry_options"))
        telemetry_layout = QVBoxLayout(telemetry_group)
        
        self.telemetry_list = QListWidget()
        self.telemetry_list.setSelectionMode(QListWidget.MultiSelection)
        self.telemetry_list.setAlternatingRowColors(True)
        
        # 定義遙測選項
        self.telemetry_options = {
            "speed_analysis": ("⚡", "speed_analysis", True),
            "brake": ("🛑", "brake_analysis", True),
            "throttle": ("⚡", "throttle_analysis", True),
            "gear": ("⚙️", "gear_analysis", True),
            "rpm": ("🔄", "rpm_analysis", True),
            "acceleration": ("📈", "acceleration_analysis", True),
            "speed_diff": ("📊", "speeddiff_analysis", True),
            "distancediff": ("📏", "distancediff_analysis", True),
        }

        # 添加選項到列表
        for key, (emoji, label_key, default_checked) in self.telemetry_options.items():
            label_text = tr(label_key, label_key.replace("_", " ").title())
            item = QListWidgetItem(f"{emoji} {label_text}")
            item.setData(Qt.UserRole, key)  # 存儲鍵值
            self.telemetry_list.addItem(item)
            if default_checked:
                item.setSelected(True)
        
        telemetry_layout.addWidget(self.telemetry_list)
        layout.addWidget(telemetry_group)
        
        # 快速選擇按鈕 - 更緊湊的布局
        quick_select_layout = QHBoxLayout()
        quick_select_layout.setSpacing(8)
        
        select_all_btn = QPushButton(tr("select_all"))
        select_all_btn.setFixedHeight(28)
        select_all_btn.clicked.connect(self.select_all)
        quick_select_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton(tr("select_none"))
        select_none_btn.setFixedHeight(28)
        select_none_btn.clicked.connect(self.select_none)
        quick_select_layout.addWidget(select_none_btn)
        
        default_btn = QPushButton(tr("restore_default"))
        default_btn.setFixedHeight(28)
        default_btn.clicked.connect(self.set_default)
        quick_select_layout.addWidget(default_btn)
        
        quick_select_layout.addStretch()
        layout.addLayout(quick_select_layout)
        
        # 對話框按鈕
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()
        
        ok_btn = QPushButton(tr("ok"))
        ok_btn.setFixedSize(60, 26)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.setFixedSize(60, 26)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def _load_available_drivers(self):
        """載入可用的車手列表 - 從進站分析JSON獲取"""
        try:
            import json
            import glob
            import os
            
            # 獲取當前年份和賽事 - 從父視窗獲取
            year = "2025"
            race = "Japan"
            
            # 嘗試從父視窗獲取參數
            try:
                if self.parent() and hasattr(self.parent(), 'get_current_parameters'):
                    params = self.parent().get_current_parameters()
                    year = params.get('year', '2025')
                    race = params.get('race', 'Japan')
                    print(f"[DRIVERS] 從父視窗獲取參數: {year} {race}")
            except Exception as param_error:
                print(f"[DRIVERS] 無法從父視窗獲取參數 ({param_error})，使用預設值: {year} {race}")
            
            if hasattr(self, 'year_combo'):
                year = self.year_combo.currentText()
                race = self.race_combo.currentText()
            
            print(f"[DRIVERS] 從進站分析JSON載入車手列表: {year} {race}")
            
            # 搜尋進站分析JSON檔案
            pitstop_patterns = [
                f"json/pitstop_analysis_{year}_{race}*.json",
                f"json_exports/pitstop_analysis_{year}_{race}*.json",
                f"cache/driver_fastest_pitstop_{year}_{race}*.pkl",  # 如果有PKL檔案也可以嘗試
                f"json/driver_pitstop_summary_{year}*.json"
            ]
            
            drivers = []
            found_file = None
            
            # 嘗試找到進站分析檔案
            for pattern in pitstop_patterns:
                files = glob.glob(pattern)
                if files:
                    found_file = files[0]  # 取第一個找到的檔案
                    print(f"[DRIVERS] 找到進站分析檔案: {found_file}")
                    break
            
            if found_file and found_file.endswith('.json'):
                # 從JSON檔案中提取車手代碼
                with open(found_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 嘗試從不同的JSON結構中提取車手代碼
                if 'drivers' in data:
                    drivers = data['drivers']
                elif 'data' in data and isinstance(data['data'], dict):
                    # 檢查是否有車手相關的鍵值
                    for key, value in data['data'].items():
                        if 'drivers' in key.lower():
                            if isinstance(value, list):
                                drivers = value
                            elif isinstance(value, dict):
                                drivers = list(value.keys())
                            break
                    
                    # 如果還沒找到，嘗試從進站數據中提取
                    if not drivers and 'pitstop_data' in data['data']:
                        pitstop_data = data['data']['pitstop_data']
                        if isinstance(pitstop_data, dict):
                            drivers = list(pitstop_data.keys())
                        elif isinstance(pitstop_data, list) and pitstop_data:
                            # 從進站記錄中提取唯一的車手代碼
                            driver_set = set()
                            for record in pitstop_data:
                                if isinstance(record, dict) and 'driver' in record:
                                    driver_set.add(record['driver'])
                                elif isinstance(record, dict) and 'Driver' in record:
                                    driver_set.add(record['Driver'])
                            drivers = sorted(list(driver_set))
                
                print(f"[DRIVERS] 從JSON提取到 {len(drivers)} 個車手: {drivers}")
            
            # 如果沒有從JSON獲取到車手，使用預設車手列表
            if not drivers:
                print(f"[DRIVERS] 使用預設車手列表")
                drivers = ["VER", "LEC", "HAM", "RUS", "NOR", "PIA", "SAI", "PER", "ALO", "STR", 
                          "TSU", "GAS", "OCO", "ALB", "SAR", "HUL", "MAG", "BOT", "ZHO", "COL"]
            
            # 添加車手到下拉式選單
            self.driver1_combo.clear()
            self.driver2_combo.clear()

            # 車手2先加入"無"選項
            none_label = tr("none_option", "None")
            self.driver2_combo.addItem(none_label, None)
            
            for driver in drivers:
                self.driver1_combo.addItem(driver, driver)
                self.driver2_combo.addItem(driver, driver)
            
            # 預設選擇
            if len(drivers) > 0:
                self.driver1_combo.setCurrentIndex(0)  # 車手1選擇第一個車手
                self.driver2_combo.setCurrentIndex(0)  # 車手2預設選擇"無"
                print(f"[DRIVERS] ✅ 成功載入 {len(drivers)} 個車手，預設選擇: 車手1={drivers[0]}, 車手2={none_label}")
            
        except Exception as e:
            print(f"[ERROR] [DRIVERS] 載入車手列表失敗: {e}")
            # 發生錯誤時使用預設車手列表
            default_drivers = ["VER", "LEC", "HAM", "RUS", "NOR", "PIA", "SAI", "PER", "ALO", "STR", 
                             "TSU", "GAS", "OCO", "ALB", "SAR", "HUL", "MAG", "BOT", "ZHO", "COL"]
            
            self.driver1_combo.clear()
            self.driver2_combo.clear()

            none_label = tr("none_option", "None")
            self.driver2_combo.addItem(none_label, None)
            
            for driver in default_drivers:
                self.driver1_combo.addItem(driver, driver)
                self.driver2_combo.addItem(driver, driver)
            
            # 預設選擇
            if len(default_drivers) > 0:
                self.driver1_combo.setCurrentIndex(0)  # 車手1選擇第一個車手
                self.driver2_combo.setCurrentIndex(0)  # 車手2預設選擇"無"
                print(f"[DRIVERS] 使用預設車手列表: 車手1={default_drivers[0]}, 車手2={none_label}")
        
    def _on_fastest_lap_changed(self, state):
        """當最速圈勾選框變更時的處理"""
        if state == 2:  # 勾選時 (Qt.Checked)
            # 最速圈被選中，禁用兩個圈數輸入並顯示99
            self.lap1_input.setEnabled(False)
            self.lap1_input.setText("99")  # 顯示99代表最速圈
            self.lap1_input.setStyleSheet("color: #666666;")
            
            self.lap2_input.setEnabled(False)
            self.lap2_input.setText("99")  # 顯示99代表最速圈
            self.lap2_input.setStyleSheet("color: #666666;")
        else:
            # 最速圈未選中，啟用兩個圈數輸入
            self.lap1_input.setEnabled(True)
            self.lap1_input.setText("1")
            self.lap1_input.setStyleSheet("")
            
            self.lap2_input.setEnabled(True)
            self.lap2_input.setText("1")
            self.lap2_input.setStyleSheet("")
    
    def get_selected_drivers(self):
        """獲取選擇的車手和圈數資訊"""
        driver1_data = self.driver1_combo.currentData()
        driver1 = driver1_data if driver1_data else self.driver1_combo.currentText()

        driver2_data = self.driver2_combo.currentData()
        driver2 = driver2_data if driver2_data else self.driver2_combo.currentText()
        
        # 判斷是否選擇最速圈
        is_fastest_lap = self.fastest_lap_checkbox.isChecked()
        
        if is_fastest_lap:
            # 🏁 最速圈邏輯：使用圈數99代表最速圈
            # 這與CLI命令 python f1_analysis_modular_main.py -f 13 --lap1 99 --lap2 99 一致
            lap1_number = 99
            lap2_number = 99
            lap_type = tr("fastest_lap_type", "Fastest Lap")
        else:
            # 嘗試解析車手1圈數輸入
            try:
                lap1_number = int(self.lap1_input.text())
            except ValueError:
                lap1_number = 1  # 預設值
            
            # 嘗試解析車手2圈數輸入
            try:
                lap2_number = int(self.lap2_input.text())
            except ValueError:
                lap2_number = 1  # 預設值
                
            lap_type = tr("specific_lap", "Specific Lap")
        
        # 如果車手2選擇了"無"，則返回None
        if driver2_data is None:
            driver2 = None
            lap2_number = None
            
        return {
            'driver1': driver1,
            'driver2': driver2,
            'lap1_number': lap1_number,
            'lap2_number': lap2_number,
            'lap_type': lap_type,
            'is_fastest_lap': is_fastest_lap
        }
        
    def select_all(self):
        """全選所有選項"""
        for i in range(self.telemetry_list.count()):
            item = self.telemetry_list.item(i)
            item.setSelected(True)
            
    def select_none(self):
        """取消所有選項"""
        self.telemetry_list.clearSelection()
            
    def set_default(self):
        """恢復預設選項"""
        self.telemetry_list.clearSelection()
        for i in range(self.telemetry_list.count()):
            item = self.telemetry_list.item(i)
            key = item.data(Qt.UserRole)
            option_config = self.telemetry_options.get(key)
            default_checked = option_config[2] if option_config else False
            if default_checked:
                item.setSelected(True)
    
    def get_selected_charts(self):
        """獲取使用者選擇的圖表類型"""
        selected = []
        for item in self.telemetry_list.selectedItems():
            key = item.data(Qt.UserRole)
            selected.append(key)
        return selected

class TelemetryChartWidget(QWidget):
    """遙測曲線圖表小部件 - 支援縮放、拖拉、X軸同步"""
    
    def __init__(self, chart_type="speed"):
        super().__init__()
        self.chart_type = chart_type
        # 移除最小尺寸限制，允許完全自由縮放
        # self.setMinimumSize(400, 200) - 已移除
        self.setObjectName("TelemetryChart")
        
        # 滑鼠追蹤和虛線控制
        self.setMouseTracking(True)
        self.mouse_x = -1  # 滑鼠X位置
        self.mouse_y = -1  # 滑鼠Y位置
        self.sync_enabled = True  # 同步啟用狀態
        
        # 固定虛線控制
        self.fixed_line_x = -1  # 固定虛線X位置 (-1表示未設定)
        self.show_fixed_line = False  # 是否顯示固定虛線
        
        # 縮放和拖拉參數
        self.y_scale = 1.0  # Y軸縮放倍率
        self.y_offset = 0   # Y軸偏移
        self.x_offset = 0   # X軸偏移
        self.x_scale = 1.0  # X軸縮放倍率
        
        # 視圖範圍參數 (參照Speed/Brake分析)
        self.view_min_x = None
        self.view_max_x = None
        self.view_min_y = None
        self.view_max_y = None
        
        # 拖拉狀態
        self.dragging = False
        self.last_drag_pos = QPoint()
        
        # 圖表邊距 (為坐標軸預留空間)
        self.margin_left = 50   # 左邊距 (Y軸標籤)
        self.margin_bottom = 30 # 下邊距 (X軸標籤)
        self.margin_top = 10    # 上邊距
        self.margin_right = 10  # 右邊距
        
        # 連接全域同步信號
        global_signals.sync_x_position.connect(self.on_sync_x_position)
        global_signals.sync_x_range.connect(self.on_sync_x_range)
        
    def on_sync_x_position(self, x):
        """接收來自其他圖表的X軸位置同步信號"""
        if self.sync_enabled and x != self.mouse_x:
            self.mouse_x = x
            # 計算對應的 Y 位置 (圖表中心，用於 Y 值計算)
            chart_area = self.get_chart_area()
            if chart_area:
                self.mouse_y = chart_area.center().y()
            self.update()
        
    def on_sync_x_range(self, x_offset, x_scale):
        """接收來自其他圖表的X軸範圍同步信號"""
        if self.sync_enabled:
            self.x_offset = x_offset
            self.x_scale = x_scale
            self.update()
        
    def set_sync_enabled(self, enabled):
        """設定是否啟用同步"""
        self.sync_enabled = enabled
        
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 更新垂直虛線位置、拖拉X軸"""
        # 更新滑鼠X和Y位置（用於虛線和數值顯示）
        chart_area = self.get_chart_area()
        if chart_area.contains(event.pos()):
            self.mouse_x = event.x()
            self.mouse_y = event.y()
            self.update()
            
            # 發送同步信號到其他圖表 (只在有勾選連動時)
            if self.sync_enabled:
                global_signals.sync_x_position.emit(self.mouse_x)
        
        # 處理X軸拖拉
        if self.dragging and event.buttons() == Qt.LeftButton:
            delta_x = event.x() - self.last_drag_pos.x()
            # 調整X軸偏移 (拖拉方向相反)
            self.x_offset -= delta_x / self.x_scale
            self.last_drag_pos = event.pos()
            self.update()
            
            # 如果啟用X軸同步，同步拖拉位置
            if self.sync_enabled:
                global_signals.sync_x_range.emit(self.x_offset, self.x_scale)
        
        super().mouseMoveEvent(event)
        
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 處理固定虛線和拖拉"""
        if event.button() == Qt.LeftButton:
            chart_area = self.get_chart_area()
            if chart_area.contains(event.pos()):
                # 檢查是否按下 Ctrl 鍵來固定虛線
                if event.modifiers() & Qt.ControlModifier:
                    # Ctrl + 左鍵：固定虛線位置
                    self.fixed_line_x = event.x()
                    self.show_fixed_line = True
                    
                    # 計算並保存固定位置的真實數據值
                    self._calculate_and_save_fixed_value()
                    
                    #print(f"[LOCK] 固定虛線位置：X = {self.fixed_line_x}")
                    self.update()
                else:
                    # 普通左鍵：開始拖拉
                    self.dragging = True
                    self.last_drag_pos = event.pos()
                    self.setCursor(Qt.ClosedHandCursor)
        
        # 右鍵：清除固定虛線
        elif event.button() == Qt.RightButton:
            chart_area = self.get_chart_area()
            if chart_area.contains(event.pos()):
                self.show_fixed_line = False
                self.fixed_line_x = -1
                #print("🔓 清除固定虛線")
                self.update()
        
        super().mousePressEvent(event)
        
    def _calculate_and_save_fixed_value(self):
        """計算並保存固定虛線位置的真實數據值"""
        if not hasattr(self, 'fixed_line_x') or self.fixed_line_x < 0:
            return
            
        chart_area = self.get_chart_area()
        if not chart_area.contains(QPoint(self.fixed_line_x, chart_area.center().y())):
            return
            
        # 計算實際的X軸數值
        if abs(self.x_scale) > 0.001:
            i = self.fixed_line_x - chart_area.left()
            x_start = int(self.x_offset)
            actual_x = x_start + i / self.x_scale
        else:
            return
            
        # 使用數據插值計算真實Y值
        if hasattr(self, 'x_data') and hasattr(self, 'y_data') and self.x_data and self.y_data:
            import numpy as np
            try:
                # 使用線性插值獲取精確的真實Y值
                fixed_y_value = np.interp(actual_x, self.x_data, self.y_data)
                
                # 保存固定值和單位
                self.fixed_y_value = fixed_y_value
                self.fixed_actual_x = actual_x
                
                # 根據圖表類型設置單位
                if self.chart_type == "speed":
                    self.fixed_unit = "km/h"
                elif self.chart_type == "brake":
                    self.fixed_unit = "%"
                elif self.chart_type == "throttle":
                    self.fixed_unit = "%"
                elif self.chart_type == "steering":
                    self.fixed_unit = "°"
                
                #print(f"[LOCK] 保存固定值: X={actual_x:.1f}, Y={fixed_y_value:.1f}{self.fixed_unit}")
                return
            except Exception as e:
                #print(f"[WARNING] 固定值計算失敗: {e}")
                pass
        
        # 如果插值失敗，設置為未知狀態
        self.fixed_y_value = None
        self.fixed_unit = ""
        #print(f"[WARNING] 無法計算固定值 - 沒有可用數據")
        
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖拉"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
        
        super().mouseReleaseEvent(event)
        
    def wheelEvent(self, event):
        """滑鼠滾輪事件 - 參照Speed/Brake分析的視圖範圍縮放"""
        chart_area = self.get_chart_area()
        if chart_area.contains(event.pos()):
            # 獲取滾輪方向（統一使用1.1縮放因子）
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 1.0 / 1.1
            
            # 計算滑鼠在圖表中的相對位置
            mouse_rel_x = (event.x() - chart_area.left()) / chart_area.width()
            mouse_rel_y = (chart_area.bottom() - event.y()) / chart_area.height()
            
            # 初始化視圖範圍（如果尚未設定）
            if not hasattr(self, 'view_min_x') or self.view_min_x is None:
                self.view_min_x = 0
                self.view_max_x = len(self.chart_data) if hasattr(self, 'chart_data') and self.chart_data else 1000
            if not hasattr(self, 'view_min_y') or self.view_min_y is None:
                # 根據圖表類型設定Y軸範圍
                if self.chart_type == "speed":
                    self.view_min_y = 0
                    self.view_max_y = 350
                elif self.chart_type == "brake":
                    self.view_min_y = 0
                    self.view_max_y = 1.2
                elif self.chart_type == "throttle":
                    self.view_min_y = 0
                    self.view_max_y = 1.2
                elif self.chart_type == "steering":
                    self.view_min_y = -180
                    self.view_max_y = 180
                else:
                    self.view_min_y = -100
                    self.view_max_y = 100
            
            # 計算當前滑鼠對應的數據值
            x_range = self.view_max_x - self.view_min_x
            y_range = self.view_max_y - self.view_min_y
            
            mouse_x = self.view_min_x + mouse_rel_x * x_range
            mouse_y = self.view_min_y + mouse_rel_y * y_range
            
            # 計算新的範圍
            new_x_range = x_range / zoom_factor
            new_y_range = y_range / zoom_factor
            
            # 更新視圖範圍，保持滑鼠位置不變
            new_min_x = mouse_x - new_x_range * mouse_rel_x
            new_max_x = mouse_x + new_x_range * (1 - mouse_rel_x)
            new_min_y = mouse_y - new_y_range * mouse_rel_y
            new_max_y = mouse_y + new_y_range * (1 - mouse_rel_y)
            
            # 確保X軸範圍不超出數據範圍
            data_max_x = len(self.chart_data) if hasattr(self, 'chart_data') and self.chart_data else 1000
            if new_min_x < 0:
                offset = 0 - new_min_x
                new_min_x = 0
                new_max_x = min(data_max_x, new_max_x + offset)
            elif new_max_x > data_max_x:
                offset = new_max_x - data_max_x
                new_max_x = data_max_x
                new_min_x = max(0, new_min_x - offset)
            
            # 應用新的視圖範圍
            self.view_min_x = new_min_x
            self.view_max_x = new_max_x
            self.view_min_y = new_min_y
            self.view_max_y = new_max_y
            
            self.update()
            event.accept()
            return
        
        super().wheelEvent(event)
        
    def leaveEvent(self, event):
        """滑鼠離開事件 - 隱藏動態虛線"""
        self.mouse_x = -1
        self.update()
        
        # 發送隱藏信號到其他圖表
        if self.sync_enabled:
            global_signals.sync_x_position.emit(-1)
        
        super().leaveEvent(event)
        
    def get_chart_area(self):
        """獲取圖表繪製區域 (排除坐標軸邊距)"""
        return QRect(
            self.margin_left,
            self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 黑色背景
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        # 獲取圖表繪製區域
        chart_area = self.get_chart_area()
        
        # 繪製坐標軸
        self.draw_axes(painter, chart_area)
        
        # 設定裁切區域為圖表區域
        painter.setClipRect(chart_area)
        
        # 繪製網格 (在圖表區域內)
        self.draw_grid(painter, chart_area)
        
        # 繪製滑鼠位置的動態垂直線 
        if self.mouse_x >= 0 and chart_area.contains(QPoint(self.mouse_x, chart_area.center().y())):
            if self.sync_enabled:
                # 連動模式：白色虛線
                painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
            else:
                # 非連動模式：黃色虛線
                painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))
            
            painter.drawLine(self.mouse_x, chart_area.top(), self.mouse_x, chart_area.bottom())
            
            # 在虛線上方顯示Y軸數值
            self.draw_y_value_at_mouse(painter, chart_area)
        
        # 繪製固定位置的垂直線（如果已設定）
        if self.show_fixed_line and self.fixed_line_x >= 0 and chart_area.contains(QPoint(self.fixed_line_x, chart_area.center().y())):
            # 固定虛線：紅色實線
            painter.setPen(QPen(QColor(255, 0, 0), 3, Qt.SolidLine))
            painter.drawLine(self.fixed_line_x, chart_area.top(), self.fixed_line_x, chart_area.bottom())
            
            # 在固定虛線上方顯示Y軸數值
            self.draw_y_value_at_fixed_line(painter, chart_area)
        
        # 繪製曲線數據
        if self.chart_type == "speed":
            self.draw_speed_curve(painter, chart_area)
        elif self.chart_type == "brake":
            self.draw_brake_curve(painter, chart_area)
        elif self.chart_type == "throttle":
            self.draw_throttle_curve(painter, chart_area)
        elif self.chart_type == "steering":
            self.draw_steering_curve(painter, chart_area)
            
        # 取消裁切
        painter.setClipping(False)
        
    def draw_axes(self, painter, chart_area):
        """繪製X和Y軸"""
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        
        # Y軸 (左邊)
        painter.drawLine(chart_area.left(), chart_area.top(), chart_area.left(), chart_area.bottom())
        
        # X軸 (底部)
        painter.drawLine(chart_area.left(), chart_area.bottom(), chart_area.right(), chart_area.bottom())
        
        # Y軸標籤
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 8))
        
        # 根據圖表類型設定Y軸範圍和標籤
        if self.chart_type == "speed":
            y_min, y_max = 0, 350  # 速度範圍 (km/h)
            unit = "km/h"
        elif self.chart_type == "brake":
            y_min, y_max = 0, 100  # 煞車壓力 (%)
            unit = "%"
        elif self.chart_type == "throttle":
            y_min, y_max = 0, 100  # 節流閥開度 (%)
            unit = "%"
        elif self.chart_type == "steering":
            y_min, y_max = -100, 100  # 轉向角度 (度)
            unit = "°"
        else:
            y_min, y_max = 0, 100
            unit = ""
        
        # 繪製Y軸刻度
        steps = 5
        for i in range(steps + 1):
            value = y_min + (y_max - y_min) * i / steps
            # 應用縮放和偏移
            y_pos = int(chart_area.bottom() - (i / steps) * chart_area.height())
            
            # 刻度線
            painter.drawLine(chart_area.left() - 5, y_pos, chart_area.left(), y_pos)
            
            # 標籤
            label = f"{value:.0f}"
            if i == 0:  # 在底部標籤添加單位
                label += f" {unit}"
            painter.drawText(5, y_pos + 4, label)
        
        # X軸標籤 (時間)
        x_steps = 5
        for i in range(x_steps + 1):
            x_pos = int(chart_area.left() + (i / x_steps) * chart_area.width())
            
            # 刻度線
            painter.drawLine(x_pos, chart_area.bottom(), x_pos, chart_area.bottom() + 5)
            
            # 時間標籤 (假設每個單位是1秒)
            time_value = i * (chart_area.width() / x_steps) / 50  # 每50像素 = 1秒
            painter.drawText(x_pos - 10, chart_area.bottom() + 20, f"{time_value:.1f}s")
    
    def draw_grid(self, painter, chart_area):
        """繪製網格線"""
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        
        # 垂直網格線
        grid_spacing_x = 50
        for i in range(chart_area.left(), chart_area.right(), grid_spacing_x):
            painter.drawLine(i, chart_area.top(), i, chart_area.bottom())
            
        # 水平網格線
        grid_spacing_y = 30
        for i in range(chart_area.top(), chart_area.bottom(), grid_spacing_y):
            painter.drawLine(chart_area.left(), i, chart_area.right(), i)
            
    def draw_speed_curve(self, painter, chart_area):
        """繪製速度曲線"""
        painter.setPen(QPen(QColor(0, 255, 0), 2))  # 綠色
        points = []
        
        # 存儲數據點以供重置功能和Y值計算使用
        self.x_data = []
        self.y_data = []
        self.speed_data = []  # 專門為Y值計算存儲速度數據
        
        # 計算X軸範圍 (考慮偏移和縮放)
        x_start = int(self.x_offset)
        x_range = int(chart_area.width() / self.x_scale)
        
        for i in range(0, chart_area.width(), 2):
            # 計算實際的X位置 (考慮偏移和縮放)
            real_x = x_start + i / self.x_scale
            
            # 等待真實速度資料載入
            speed = 0  # 預設值，等待真實數據
            
            # 存儲原始數據
            self.x_data.append(real_x)
            self.y_data.append(speed)
            self.speed_data.append(speed)  # 為Y值計算存儲速度數據
            
            # 轉換為圖表座標 (支援負數Y軸縮放)
            x_pos = chart_area.left() + i
            normalized_speed = speed / 350  # 0-1 範圍
            
            if self.y_scale >= 0:
                # 正常縮放：底部為0，向上增長
                y_pos = chart_area.bottom() - (normalized_speed * chart_area.height() * self.y_scale) + self.y_offset
            else:
                # 負數縮放：翻轉Y軸，頂部為0，向下增長
                y_pos = chart_area.top() + (normalized_speed * chart_area.height() * abs(self.y_scale)) + self.y_offset
            
            points.append(QPointF(x_pos, y_pos))
        
        # 繪製曲線
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
    def draw_brake_curve(self, painter, chart_area):
        """繪製煞車曲線"""
        painter.setPen(QPen(QColor(255, 0, 0), 2))  # 紅色
        points = []
        
        # 存儲數據點以供重置功能和Y值計算使用
        self.x_data = []
        self.y_data = []
        self.brake_data = []  # 專門為Y值計算存儲煞車數據
        
        x_start = int(self.x_offset)
        
        for i in range(0, chart_area.width(), 2):
            real_x = x_start + i / self.x_scale
            
            # 等待真實煞車壓力資料載入
            brake = 0  # 預設值，等待真實數據
            
            # 存儲原始數據
            self.x_data.append(real_x)
            self.y_data.append(brake)
            self.brake_data.append(brake)  # 為Y值計算存儲煞車數據
            
            x_pos = chart_area.left() + i
            normalized_brake = brake / 100 if brake > 0 else 0  # 0-1 範圍
            
            if self.y_scale >= 0:
                # 正常縮放：底部為0，向上增長
                y_pos = chart_area.bottom() - (normalized_brake * chart_area.height() * self.y_scale) + self.y_offset
            else:
                # 負數縮放：翻轉Y軸，頂部為0，向下增長
                y_pos = chart_area.top() + (normalized_brake * chart_area.height() * abs(self.y_scale)) + self.y_offset
            
            points.append(QPointF(x_pos, y_pos))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
    def draw_throttle_curve(self, painter, chart_area):
        """繪製節流閥曲線"""
        painter.setPen(QPen(QColor(255, 255, 0), 2))  # 黃色
        points = []
        
        # 存儲數據點以供重置功能和Y值計算使用
        self.x_data = []
        self.y_data = []
        self.throttle_data = []  # 專門為Y值計算存儲節流閥數據
        
        x_start = int(self.x_offset)
        
        for i in range(0, chart_area.width(), 2):
            real_x = x_start + i / self.x_scale
            
            # 等待真實節流閥位置資料載入
            throttle = 0  # 預設值，等待真實數據
            
            # 存儲原始數據
            self.x_data.append(real_x)
            self.y_data.append(throttle)
            self.throttle_data.append(throttle)  # 為Y值計算存儲節流閥數據
            
            x_pos = chart_area.left() + i
            normalized_throttle = throttle / 100 if throttle > 0 else 0  # 0-1 範圍
            
            if self.y_scale >= 0:
                # 正常縮放：底部為0，向上增長
                y_pos = chart_area.bottom() - (normalized_throttle * chart_area.height() * self.y_scale) + self.y_offset
            else:
                # 負數縮放：翻轉Y軸，頂部為0，向下增長
                y_pos = chart_area.top() + (normalized_throttle * chart_area.height() * abs(self.y_scale)) + self.y_offset
            points.append(QPointF(x_pos, y_pos))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
    def draw_steering_curve(self, painter, chart_area):
        """繪製方向盤曲線"""
        painter.setPen(QPen(QColor(0, 255, 255), 2))  # 青色
        points = []
        
        # 存儲數據點以供重置功能和Y值計算使用
        self.x_data = []
        self.y_data = []
        self.steering_data = []  # 專門為Y值計算存儲方向盤數據
        
        x_start = int(self.x_offset)
        
        for i in range(0, chart_area.width(), 2):
            real_x = x_start + i / self.x_scale
            
            # 等待真實方向盤轉角資料載入
            steering = 0  # 預設值，等待真實數據
            
            # 存儲原始數據
            self.x_data.append(real_x)
            self.y_data.append(steering)
            self.steering_data.append(steering)  # 為Y值計算存儲方向盤數據
            
            x_pos = chart_area.left() + i
            # 改進的轉向角度處理 - 支援負數Y軸縮放
            # 將 -100~+100 映射到圖表高度，中心線在圖表中央
            normalized_steering = steering / 100.0  # -1.0 到 +1.0
            y_pos = chart_area.center().y() - (normalized_steering * chart_area.height() * 0.4 * abs(self.y_scale))
            
            # 如果Y軸縮放是負數，翻轉Y軸
            if self.y_scale < 0:
                y_pos = chart_area.center().y() + (normalized_steering * chart_area.height() * 0.4 * abs(self.y_scale))
            
            y_pos += self.y_offset
            points.append(QPointF(x_pos, y_pos))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
    def draw_y_value_at_mouse(self, painter, chart_area):
        """在滑鼠位置的虛線上方顯示Y軸數值 - 基於滑鼠位置反向計算Y值"""
        # 確保滑鼠X位置有效且在圖表區域內
        if not hasattr(self, 'mouse_x') or self.mouse_x < 0:
            return
        if not chart_area.contains(QPoint(self.mouse_x, chart_area.center().y())):
            return
            
        # 計算實際的X軸數值 - 匹配繪圖邏輯
        if abs(self.x_scale) > 0.001:
            i = self.mouse_x - chart_area.left()
            x_start = int(self.x_offset)
            actual_x = x_start + i / self.x_scale
        else:
            return
            
        # 方法1：如果有存儲的數據，使用插值計算Y值
        y_value = None
        unit = ""
        
        if hasattr(self, 'x_data') and hasattr(self, 'y_data') and self.x_data and self.y_data:
            import numpy as np
            try:
                # 使用線性插值獲取精確的Y值
                y_value = np.interp(actual_x, self.x_data, self.y_data)
                
                # 根據圖表類型設置單位
                if self.chart_type == "speed":
                    unit = "km/h"
                elif self.chart_type == "brake":
                    unit = "%"
                elif self.chart_type == "throttle":
                    unit = "%"
                elif self.chart_type == "steering":
                    unit = "°"
                else:
                    return
            except Exception:
                y_value = None
        
        # 方法2：如果插值失敗或沒有數據，使用滑鼠Y位置反向計算
        if y_value is None:
            # 從滑鼠Y位置反向計算對應的數值
            mouse_y_in_chart = self.mouse_y
            
            # 反向計算Y值 - 匹配繪圖邏輯
            if self.chart_type == "speed":
                # 速度範圍 0-350 km/h
                if abs(self.y_scale) > 0.001:
                    if self.y_scale >= 0:
                        # 正常縮放：底部為0，向上增長
                        normalized_y = (chart_area.bottom() - mouse_y_in_chart + self.y_offset) / (chart_area.height() * self.y_scale)
                    else:
                        # 負數縮放：頂部為0，向下增長
                        normalized_y = (mouse_y_in_chart - chart_area.top() - self.y_offset) / (chart_area.height() * abs(self.y_scale))
                    y_value = max(0, min(350, normalized_y * 350))
                else:
                    y_value = 175  # 中間值
                unit = "km/h"
            elif self.chart_type == "brake":
                # 煞車範圍 0-100%
                if abs(self.y_scale) > 0.001:
                    if self.y_scale >= 0:
                        normalized_y = (chart_area.bottom() - mouse_y_in_chart + self.y_offset) / (chart_area.height() * self.y_scale)
                    else:
                        normalized_y = (mouse_y_in_chart - chart_area.top() - self.y_offset) / (chart_area.height() * abs(self.y_scale))
                    y_value = max(0, min(100, normalized_y * 100))
                else:
                    y_value = 50
                unit = "%"
            elif self.chart_type == "throttle":
                # 油門範圍 0-100%
                if abs(self.y_scale) > 0.001:
                    if self.y_scale >= 0:
                        normalized_y = (chart_area.bottom() - mouse_y_in_chart + self.y_offset) / (chart_area.height() * self.y_scale)
                    else:
                        normalized_y = (mouse_y_in_chart - chart_area.top() - self.y_offset) / (chart_area.height() * abs(self.y_scale))
                    y_value = max(0, min(100, normalized_y * 100))
                else:
                    y_value = 50
                unit = "%"
            elif self.chart_type == "steering":
                # 轉向範圍 -100° to +100°，使用圖表中心為基準
                if abs(self.y_scale) > 0.001:
                    # 計算相對於圖表中心的偏移
                    center_offset = mouse_y_in_chart - chart_area.center().y() - self.y_offset
                    
                    if self.y_scale >= 0:
                        # 正常縮放：負值向上，正值向下
                        normalized_steering = -center_offset / (chart_area.height() * 0.4 * abs(self.y_scale))
                    else:
                        # 負數縮放：翻轉Y軸
                        normalized_steering = center_offset / (chart_area.height() * 0.4 * abs(self.y_scale))
                    
                    y_value = max(-100, min(100, normalized_steering * 100))
                else:
                    y_value = 0
                unit = "°"
            else:
                return
        
        # 繪製數值標籤
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        
        # 格式化數值顯示
        if self.chart_type == "steering":
            value_text = f"{y_value:+.1f}{unit}"
        else:
            value_text = f"{y_value:.1f}{unit}"
        
        # 計算標籤位置（虛線上方，在滑鼠Y位置上方）
        label_x = self.mouse_x + 5
        label_y = max(chart_area.top() + 20, self.mouse_y - 15)  # 在滑鼠位置上方顯示
        
        # 確保標籤不超出左右邊界
        text_metrics = painter.fontMetrics()
        text_width = text_metrics.horizontalAdvance(value_text)
        if label_x + text_width > chart_area.right():
            label_x = self.mouse_x - text_width - 5
        if label_x < chart_area.left():
            label_x = chart_area.left() + 5
        
        # 繪製背景框
        text_rect = text_metrics.boundingRect(value_text)
        bg_rect = text_rect.adjusted(-4, -2, 4, 2)
        bg_rect.moveTopLeft(QPoint(label_x - 4, label_y - text_rect.height() - 2))
        
        # 根據同步狀態選擇顏色
        if self.sync_enabled:
            painter.fillRect(bg_rect, QColor(0, 0, 0, 200))  # 黑色半透明背景
            text_color = QColor(255, 255, 255)  # 白色文字
            border_color = QColor(255, 255, 255)  # 白色邊框
        else:
            painter.fillRect(bg_rect, QColor(80, 80, 0, 200))  # 深黃色半透明背景
            text_color = QColor(255, 255, 0)  # 黃色文字
            border_color = QColor(255, 255, 0)  # 黃色邊框
        
        painter.setPen(QPen(border_color, 1))
        painter.drawRect(bg_rect)
        
        # 繪製文字
        painter.setPen(QPen(text_color, 1))
        painter.drawText(label_x, label_y, value_text)
        
    def draw_y_value_at_fixed_line(self, painter, chart_area):
        """在固定虛線位置顯示固定Y值 - 使用已保存的值，不會變動"""
        # 確保固定線有效
        if not hasattr(self, 'show_fixed_line') or not self.show_fixed_line:
            return
        if not hasattr(self, 'fixed_line_x') or self.fixed_line_x < 0:
            return
        if not chart_area.contains(QPoint(self.fixed_line_x, chart_area.center().y())):
            return
            
        # 使用已保存的固定值（在點擊時保存，之後不會變動）
        if hasattr(self, 'fixed_y_value') and self.fixed_y_value is not None:
            y_value = self.fixed_y_value
            unit = getattr(self, 'fixed_unit', '')
            #print(f"[LOCK] 使用已保存的固定值: {y_value:.1f}{unit}")
        else:
            #print(f"[WARNING] 沒有已保存的固定值")
            return
        
        # 繪製數值標籤
        painter.setPen(QPen(QColor(255, 0, 0), 1))  # 紅色文字
        painter.setFont(QFont("Arial", 12, QFont.Bold))  # 稍大字體
        
        # 格式化數值顯示 (包含鎖孔圖標)
        if self.chart_type == "steering":
            value_text = f"[LOCK]{y_value:+.1f}{unit}"
        else:
            value_text = f"[LOCK]{y_value:.1f}{unit}"
        
        # 計算標籤位置（固定線右側，頂部）
        label_x = self.fixed_line_x + 8
        label_y = chart_area.top() + 20
        
        # 確保標籤不超出右邊界
        text_metrics = painter.fontMetrics()
        text_width = text_metrics.horizontalAdvance(value_text)
        if label_x + text_width > chart_area.right():
            label_x = self.fixed_line_x - text_width - 8
        if label_x < chart_area.left():
            label_x = chart_area.left() + 5
        
        # 繪製背景框
        text_rect = text_metrics.boundingRect(value_text)
        bg_rect = text_rect.adjusted(-4, -2, 4, 2)
        bg_rect.moveTopLeft(QPoint(label_x - 4, label_y - text_rect.height() - 2))
        
        # 紅色背景和邊框（固定線樣式）
        painter.fillRect(bg_rect, QColor(100, 0, 0, 200))  # 深紅色半透明背景
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawRect(bg_rect)
        
        # 繪製文字
        painter.setPen(QPen(QColor(255, 255, 255), 1))  # 白色文字
        painter.drawText(label_x, label_y, value_text)
        
        #print(f"[STATS] 顯示固定值標籤: {value_text} at ({label_x}, {label_y})")  # Debug

class DraggableTitleBar(QWidget):
    """可拖拽的自定義標題欄"""
    
    def __init__(self, parent_window, title=""):
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("CustomTitleBar")
        self.setFixedHeight(20)
        self.dragging = False
        self.drag_position = QPoint()
        
        # 調試資訊：確認 CustomTitleBar 創建
        #print(f"[DESIGN] DEBUG: Creating CustomTitleBar with title: '{title}'")
        #print(f"[INFO] ObjectName set to: {self.objectName()}")
        #print(f"📏 Fixed height set to: {self.height()}")
        
        # 創建標題欄布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        
        # 標題標籤
        self.title_label = QLabel(title)
        self.title_label.setObjectName("SubWindowTitle")
        layout.addWidget(self.title_label)
        
        # [LINK] 接收同步控制按鈕
        self.sync_btn = QPushButton("[LINK]")
        self.sync_btn.setObjectName("SyncButton")
        self.sync_btn.setFixedSize(16, 16)
        self.sync_btn.setToolTip("接收主程式同步：啟用 (綠色) / 停用 (紅色)")
        self.sync_btn.setCheckable(True)
        self.sync_btn.setChecked(True)  # 預設啟用
        self.sync_btn.clicked.connect(self.toggle_x_sync)
        layout.addWidget(self.sync_btn)
        
        # [LINKAGE] 個別連動控制按鈕
        self.linkage_btn = QPushButton("🔗")
        self.linkage_btn.setObjectName("LinkageButton")
        self.linkage_btn.setFixedSize(16, 16)
        self.linkage_btn.setToolTip("個別連動：啟用 / 停用")
        self.linkage_btn.setCheckable(True)
        self.linkage_btn.setChecked(True)  # 預設啟用
        self.linkage_btn.clicked.connect(self.toggle_individual_linkage)
        layout.addWidget(self.linkage_btn)
        
        # 初始化顏色狀態 - 確保預設綠色正確顯示
        print(f"[GREEN] 接收同步初始化為啟動狀態")
        
        layout.addStretch()
        
        # [HOT] 恢復按鈕（針對極小視窗）
        restore_btn = QPushButton("⟲")
        restore_btn.setObjectName("RestoreButton")
        restore_btn.setFixedSize(16, 16)
        restore_btn.setToolTip("恢復正常大小")
        restore_btn.clicked.connect(self.restore_normal_size)
        layout.addWidget(restore_btn)
        
        # 設定按鈕（放在最小化按鈕左邊）
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("SettingsButton")
        settings_btn.setFixedSize(16, 16)
        settings_btn.setToolTip("視窗設定")
        settings_btn.clicked.connect(self.parent_window.show_settings_dialog)
        layout.addWidget(settings_btn)
        
        # 標準視窗控制按鈕
        minimize_btn = QPushButton("─")
        minimize_btn.setObjectName("WindowControlButton")
        minimize_btn.setFixedSize(16, 16)
        minimize_btn.setToolTip("最小化")
        minimize_btn.clicked.connect(self.parent_window.custom_minimize)
        layout.addWidget(minimize_btn)
        
        maximize_btn = QPushButton("□")
        maximize_btn.setObjectName("WindowControlButton")
        maximize_btn.setFixedSize(16, 16)
        maximize_btn.setToolTip("最大化/還原")
        maximize_btn.clicked.connect(self.parent_window.toggle_maximize)
        layout.addWidget(maximize_btn)
        
        # 彈出按鈕
        self.popout_btn = QPushButton("⧉")
        self.popout_btn.setObjectName("PopoutButton")
        self.popout_btn.setFixedSize(16, 16)
        self.popout_btn.setToolTip("彈出為獨立視窗")
        self.popout_btn.clicked.connect(self.parent_window.toggle_popout)
        layout.addWidget(self.popout_btn)
        
        # 關閉按鈕
        close_btn = QPushButton("✕")
        close_btn.setObjectName("WindowControlButton")
        close_btn.setFixedSize(16, 16)
        close_btn.setToolTip("關閉")
        close_btn.clicked.connect(self.parent_window.close)
        layout.addWidget(close_btn)
        
    def restore_normal_size(self):
        """恢復視窗到正常大小"""
        #print(f"[REFRESH] 恢復視窗 '{self.parent_window.windowTitle()}' 到正常大小")
        if hasattr(self.parent_window, 'content_widget') and self.parent_window.content_widget:
            # 根據內容類型設置合適的大小
            if hasattr(self.parent_window.content_widget, 'chart_type'):
                # 圖表視窗
                self.parent_window.resize(500, 350)
            else:
                # 其他視窗
                self.parent_window.resize(400, 300)
        else:
            # 默認大小
            self.parent_window.resize(400, 300)
        
        # 確保視窗在可見區域內
        if self.parent_window.parent():
            parent_rect = self.parent_window.parent().rect()
            current_pos = self.parent_window.pos()
            new_x = max(10, min(current_pos.x(), parent_rect.width() - 420))
            new_y = max(10, min(current_pos.y(), parent_rect.height() - 320))
            self.parent_window.move(new_x, new_y)
        
    def mouseDoubleClickEvent(self, event):
        """雙擊恢復視窗大小"""
        if event.button() == Qt.LeftButton:
            #print(f"[CLICK] 雙擊標題欄恢復視窗大小")
            self.restore_normal_size()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event):
        """右鍵選單"""
        menu = QMenu(self)
        restore_action = menu.addAction("[REFRESH] 恢復正常大小")
        restore_action.triggered.connect(self.restore_normal_size)
        
        maximize_action = menu.addAction("🔳 最大化")
        maximize_action.triggered.connect(self.parent_window.toggle_maximize)
        
        menu.exec_(event.globalPos())
        
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 開始拖拽，但不干擾調整大小"""
        if event.button() == Qt.LeftButton:
            # 檢查是否在父視窗的調整邊緣區域
            parent_pos = self.parent_window.mapFromGlobal(event.globalPos())
            if self.parent_window.get_resize_direction(parent_pos):
                # 如果在調整區域，讓父視窗處理
                event.ignore()
                return
                
            self.dragging = True
            self.drag_position = event.globalPos() - self.parent_window.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 執行拖拽，但不干擾調整大小"""
        # 檢查是否在調整模式
        if hasattr(self.parent_window, 'resizing') and self.parent_window.resizing:
            event.ignore()
            return
            
        # 檢查是否在調整區域，如果是就讓父視窗處理游標
        parent_pos = self.parent_window.mapFromGlobal(event.globalPos())
        if hasattr(self.parent_window, 'get_resize_direction') and self.parent_window.get_resize_direction(parent_pos):
            event.ignore()
            return
            
        if event.buttons() == Qt.LeftButton and self.dragging:
            new_pos = event.globalPos() - self.drag_position
            self.parent_window.move(new_pos)
            event.accept()
        else:
            # 沒有拖拽時，讓父視窗處理事件
            event.ignore()
            
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖拽"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
    
    def paintEvent(self, event):
        """繪製事件 - 手動繪製背景色以確保顯示"""
        #print(f"[DESIGN] DEBUG: CustomTitleBar paintEvent called")
        #print(f"[INFO] ObjectName: {self.objectName()}")
        #print(f"📐 Widget size: {self.width()}x{self.height()}")
        #print(f"[DESIGN] Current QSS length: {len(self.styleSheet())}")
        if self.styleSheet():
            #print(f"[DESIGN] QSS content (first 100 chars): {self.styleSheet()[:100]}...")
            pass
        else:
            #print("[WARNING] No QSS applied to CustomTitleBar")
            pass
        
        # 手動繪製 #F0F0F0 背景色以確保顯示
        painter = QPainter(self)
        # 繪製稍微大一點的矩形，確保填滿所有可能的間隙
        extended_rect = self.rect()
        extended_rect.setTop(extended_rect.top() - 5)  # 向上延伸5像素
        extended_rect.setLeft(extended_rect.left() - 5)  # 向左延伸5像素 
        extended_rect.setRight(extended_rect.right() + 5)  # 向右延伸5像素
        painter.fillRect(extended_rect, QColor("#F0F0F0"))
        #print(f"[DESIGN] Manually painted background with #F0F0F0 (extended rect)")
        
        super().paintEvent(event)
    
    def update_title(self, title):
        """更新標題"""
        self.title_label.setText(title)
    
    def toggle_x_sync(self):
        """切換接收同步狀態 - 綠色=接收主程式同步，紅色=獨立運作"""
        is_enabled = self.sync_btn.isChecked()
        
        # 更新按鈕外觀和提示
        if is_enabled:
            self.sync_btn.setText("[LINK]")
            self.sync_btn.setToolTip("接收主程式同步：啟用 (綠色)")
            # 強制更新為綠色樣式
            print(f"[GREEN] 接收同步已啟動 - 將接收主程式參數")
        else:
            self.sync_btn.setText("[LINK]̸")  # 帶斜線的連結圖示
            self.sync_btn.setToolTip("接收主程式同步：停用 (紅色)")
            # 強制更新為紅色樣式
            print(f"🔴 接收同步已停用 - 獨立運作模式")
        
        # 強制重新應用樣式確保顏色更新
        self.sync_btn.style().unpolish(self.sync_btn)
        self.sync_btn.style().polish(self.sync_btn)
        self.sync_btn.update()
        
        # 更新父視窗的同步狀態
        if hasattr(self.parent_window, 'sync_enabled'):
            self.parent_window.sync_enabled = is_enabled
            print(f"[REFRESH] 視窗 '{self.parent_window.windowTitle()}' 同步接收狀態已更新: {is_enabled}")
            
            # [TOOL] 新增：立即更新標題（同步狀態改變時）
            if hasattr(self.parent_window, 'update_window_title'):
                self.parent_window.update_window_title()
    
    def toggle_individual_linkage(self):
        """切換個別連動狀態"""
        is_enabled = self.linkage_btn.isChecked()
        
        # 更新按鈕外觀和提示
        if is_enabled:
            self.linkage_btn.setText("🔗")
            self.linkage_btn.setToolTip("個別連動：啟用")
            print(f"[LINKAGE] 個別連動已啟用")
        else:
            self.linkage_btn.setText("🔗❌")
            self.linkage_btn.setToolTip("個別連動：停用")
            print(f"[LINKAGE] 個別連動已停用")
        
        # 強制重新應用樣式確保顏色更新
        self.linkage_btn.style().unpolish(self.linkage_btn)
        self.linkage_btn.style().polish(self.linkage_btn)
        self.linkage_btn.update()
        
        # 通知分析模組更新連動狀態
        if hasattr(self.parent_window, 'set_linkage_enabled'):
            self.parent_window.set_linkage_enabled(is_enabled)
            print(f"[LINKAGE] 視窗 '{self.parent_window.windowTitle()}' 個別連動狀態已更新: {is_enabled}")
    
    def set_linkage_button_state(self, enabled: bool):
        """設置連動按鈕狀態（由主視窗總開關調用）"""
        self.linkage_btn.setChecked(enabled)
        self.toggle_individual_linkage()  # 觸發狀態更新
    
    def get_sync_status(self):
        """取得當前X軸連動狀態"""
        return self.sync_btn.isChecked()

class PopoutSubWindow(QMdiSubWindow):
    """支援彈出功能和調整大小的MDI子視窗 - 升級為通用模組容器"""
    
    # 添加自定義信號
    resized = pyqtSignal()  # 尺寸調整信號
    window_closed = pyqtSignal()  # 視窗關閉信號
    
    def __init__(self, title="", parent_mdi=None, analysis_module=None, 
                 sync_enabled=True, parameter_provider=None, global_signal_manager=None, **kwargs):
        super().__init__()
        #print(f"[START] DEBUG: Creating PopoutSubWindow '{title}'")
        self.parent_mdi = parent_mdi
        self.is_popped_out = False
        self.original_widget = None
        self.content_widget = None
        
        # [TOOL] 新增：模組支援
        self.analysis_module = analysis_module
        self._parameter_provider = parameter_provider
        
        # [TOOL] 新增：本地參數存儲 (用於非同步狀態)
        self.local_year = "2025"
        self.local_race = "Japan"
        self.local_session = "R"
        self._season_event_lookup: Dict[str, SeasonEvent] = {}
        self._display_to_race_key: Dict[str, str] = {}
        
        # [TOOL] 修正：正確提取模組名稱
        self.module_name = self._extract_module_name_from_title(title)
        
        self.setWindowTitle(title)
        self.setObjectName("ProfessionalSubWindow")
        
        # 初始化同步設定狀態
        self.sync_enabled = sync_enabled  # 使用傳入的同步設定
        
        # 嘗試獲取主視窗引用
        self.main_window = None
        if parent_mdi:
            # 向上查找主視窗
            current_parent = parent_mdi.parent()
            while current_parent:
                if hasattr(current_parent, 'year_combo') and hasattr(current_parent, 'race_combo'):
                    self.main_window = current_parent
                    # [TOOL] 新增：設置參數提供者（如果沒有傳入的話）
                    if not self._parameter_provider:
                        self._parameter_provider = MainWindowParameterProvider(current_parent)
                    print(f"[LINK] [INIT] {title} 已找到主視窗引用")
                    break
                current_parent = current_parent.parent()
        
        # [TOOL] 新增：如果有模組，進行初始化
        if self.analysis_module and self._parameter_provider:
            self.analysis_module.parameter_provider = self._parameter_provider
            # 連接模組信號 - 修正：信號直接在模組上，不在 signals 屬性下
            if hasattr(self.analysis_module, 'module_error'):
                self.analysis_module.module_error.connect(self._handle_module_error)
            if hasattr(self.analysis_module, 'parameters_updated'):
                self.analysis_module.parameters_updated.connect(self._handle_parameters_updated)
                
            print(f"[SYNC] [INIT] {title} 已連接模組同步信號")
            
            # [FIX] 立即進行一次初始同步，確保模組獲得當前參數
            try:
                if hasattr(self.analysis_module, 'update_parameters'):
                    year = int(self._parameter_provider.get_current_year())
                    race = self._parameter_provider.get_current_race()
                    session = self._parameter_provider.get_current_session()
                    print(f"[SYNC] [INIT] 進行初始參數同步: {year} {race} {session}")
                    self.analysis_module.update_parameters(year, race, session)
            except Exception as e:
                print(f"[WARNING] [INIT] 初始同步失敗: {e}")
        
        # 初始化最小化狀態
        self.is_minimized = False
        self.original_geometry = None
        
        # [TOOL] [FIX] 確保調整大小相關屬性被初始化
        self.resize_margin = 3  # 視覺邊框寬度 (3像素，與QSS邊框一致)
        self.resize_detection_margin = 10  # 實際可操作區域 (10像素)
        self.resizing = False
        self.resize_direction = None
        
        # [TOOL] [FIX] 強制啟用滑鼠追蹤
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_MouseTracking, True)
        
        print(f"[OK] [INIT] PopoutSubWindow '{title}' 初始化完成 - 包含調整大小支援")
    
    def _extract_module_name_from_title(self, title):
        """從標題中提取模組名稱"""
        try:
            # 處理各種可能的標題格式
            if title.startswith("[RAIN]"):
                return "Rain Analysis"
            elif title.startswith("[LAP]"):
                return "Lap Analysis" 
            elif title.startswith("[COMPARE]"):
                return "Comparison Analysis"
            elif title.startswith("[TELEMETRY]"):
                return "Race Overview"
            elif "_" in title:
                # 新格式：模組名稱_年份_賽事_賽段
                module_part = title.split('_')[0]
                # 處理帶圖標的模組名稱，如 "⚡ 速度分析" -> "速度分析"
                if " " in module_part and not module_part.startswith("["):
                    parts = module_part.split(" ")
                    if len(parts) >= 2:
                        return " ".join(parts[1:])  # 移除圖標，保留模組名稱
                return module_part
            elif " - " in title:
                # 舊格式：[TAG] 模組名稱 - 詳細資訊
                if "]" in title:
                    # 移除標籤部分
                    without_tag = title.split("]", 1)[1].strip()
                    # 取 " - " 之前的部分
                    return without_tag.split(" - ")[0].strip()
                else:
                    return title.split(" - ")[0].strip()
            else:
                # 純模組名稱
                return title.strip()
                
        except Exception as e:
            print(f"[WARNING] [TITLE] 提取模組名稱失敗: {e}, 使用原標題: {title}")
            return title
        
    def _handle_module_error(self, error_message):
        """處理模組錯誤"""
        print(f"[ERROR] [MODULE] {self.windowTitle()} 模組錯誤: {error_message}")
    
    def _handle_parameters_updated(self, params):
        """處理模組參數更新"""
        print(f"[REFRESH] [MODULE] {self.windowTitle()} 參數已更新: {params}")
    
    def update_current_window(self):
        """更新當前視窗 - 委託給模組處理"""
        print(f"[UPDATE_DEBUG] ========== 視窗更新請求 ==========")
        print(f"[UPDATE_DEBUG] 視窗標題: {self.windowTitle()}")
        print(f"[UPDATE_DEBUG] 是否有 analysis_module: {self.analysis_module is not None}")
        
        if self.analysis_module:
            print(f"[UPDATE_DEBUG] 🎯 使用新版模組更新邏輯")
            # 如果有模組，委託給模組處理
            try:
                params = {}
                if self.sync_enabled and self._parameter_provider:
                    # 同步模式：使用主視窗參數
                    params = {
                        'year': int(self._parameter_provider.get_current_year()),  # 轉換為int
                        'race': self._parameter_provider.get_current_race(),
                        'session': self._parameter_provider.get_current_session()
                    }
                    # 更新本地參數
                    self.local_year = str(params['year'])  # 本地參數保持字符串
                    self.local_race = params['race'] 
                    self.local_session = params['session']
                else:
                    # 非同步模式：使用本地參數
                    params = {
                        'year': int(self.local_year),  # 轉換為int
                        'race': self.local_race,
                        'session': self.local_session
                    }
                
                # 更新標題
                self.update_window_title()
                
                print(f"[REFRESH] [{self.windowTitle()}] 更新視窗數據: {params['year']} {params['race']} {params['session']}")
                
                # [TOOL] 重新載入模組而不是委託更新
                success = self.analysis_module.update_parameters(**params)
                if success:
                    print(f"[OK] [MODULE] {self.windowTitle()} 模組更新成功")
                else:
                    print(f"[WARNING] [MODULE] {self.windowTitle()} 模組更新失敗")
                return success
                
            except Exception as e:
                print(f"[ERROR] [MODULE] {self.windowTitle()} 更新異常: {e}")
                return False
        else:
            # 舊版模式：直接調用原有邏輯
            print(f"[UPDATE_DEBUG] ⚠️ 使用舊版更新邏輯")
            print(f"[UPDATE_DEBUG] 原因: analysis_module 為 None")
            print(f"[WARNING] [LEGACY] {self.windowTitle()} 使用舊版更新模式")
            return self._legacy_update_current_window()
    
    def update_window_title(self):
        """更新視窗標題"""
        try:
            # 如果有 analysis_module，使用模組的 get_window_title 方法
            if self.analysis_module and hasattr(self.analysis_module, 'get_window_title'):
                # 傳遞當前參數給模組的 get_window_title 方法
                new_title = self.analysis_module.get_window_title(
                    year=str(self.local_year), 
                    race=self.local_race, 
                    session=self.local_session
                )
                print(f"[TITLE] [MODULE] 使用模組標題: {new_title}")
            else:
                # 舊版邏輯：保持原始格式，只更新參數部分
                if hasattr(self, 'original_title') and self.original_title:
                    # 保持原始標題格式，只添加參數後綴
                    new_title = f"{self.original_title}_{self.local_year}_{self.local_race}_{self.local_session}"
                else:
                    # 最後備選方案
                    new_title = f"{self.module_name}_{self.local_year}_{self.local_race}_{self.local_session}"
                print(f"[TITLE] [LEGACY] 使用舊版標題格式: {new_title}")
            
            self.setWindowTitle(new_title)
            
            # 同時更新自定義標題欄
            if hasattr(self, 'title_bar') and self.title_bar:
                self.title_bar.update_title(new_title)
                
            print(f"[LABEL] [TITLE] 標題已更新: {new_title}")
            
        except Exception as e:
            print(f"[ERROR] [TITLE] 標題更新失敗: {e}")
    
    def toggle_x_sync(self, enabled: Optional[bool] = None) -> bool:
        """切換或設定 X 軸同步狀態，支援還原快照時直接指定狀態。"""
        if not hasattr(self, 'title_bar') or not self.title_bar:
            if enabled is None:
                self.sync_enabled = not getattr(self, 'sync_enabled', True)
            else:
                self.sync_enabled = bool(enabled)
            return self.sync_enabled

        if enabled is None:
            self.title_bar.sync_btn.toggle()
        else:
            desired_state = bool(enabled)
            if self.title_bar.sync_btn.isChecked() != desired_state:
                self.title_bar.sync_btn.setChecked(desired_state)
            self.title_bar.toggle_x_sync()

        if hasattr(self.title_bar, 'get_sync_status'):
            self.sync_enabled = self.title_bar.get_sync_status()
        else:
            self.sync_enabled = getattr(self, 'sync_enabled', True)
        return self.sync_enabled

    def update_local_parameters(self, year=None, race=None, session=None):
        """更新本地參數（用於非同步模式）"""
        if year is not None:
            self.local_year = year
        if race is not None:
            self.local_race = race
        if session is not None:
            self.local_session = session
            
        # 立即更新標題
        self.update_window_title()
        
        print(f"[REFRESH] [LOCAL] {self.windowTitle()} 本地參數已更新: {self.local_year} {self.local_race} {self.local_session}")
    
    def _get_calendar_events_for_year(self, year: int) -> List[SeasonEvent]:
        if self.main_window and hasattr(self.main_window, "_get_calendar_events"):
            return self.main_window._get_calendar_events(year)
        if self.main_window and hasattr(self.main_window, "_season_provider"):
            try:
                return self.main_window._season_provider.get_completed_events(year)
            except SeasonCalendarError as exc:
                print(f"[CALENDAR] 子視窗取得日曆失敗: {exc}")
        return []

    def _format_race_display(self, event: SeasonEvent) -> str:
        if self.main_window and hasattr(self.main_window, "_format_race_display"):
            return self.main_window._format_race_display(event)
        if event.is_completed:
            return event.display_label
        suffix = tr("season_calendar_upcoming_suffix", "[未開賽]")
        if suffix and suffix in event.display_label:
            return event.display_label
        return f"{event.display_label} {suffix}" if suffix else event.display_label

    def _rebuild_race_mapping(self, events: List[SeasonEvent]) -> None:
        self._season_event_lookup.clear()
        self._display_to_race_key.clear()
        for event in events:
            self._season_event_lookup[event.race_key] = event
            formatted_label = self._format_race_display(event)
            candidate_labels = {event.display_label, formatted_label}
            for label in candidate_labels:
                self._display_to_race_key[label] = event.race_key
                plain_label = self.main_window._strip_race_display(label) if self.main_window else label
                if plain_label and plain_label not in self._display_to_race_key:
                    self._display_to_race_key[plain_label] = event.race_key

    def _select_race_by_key(self, race_key: Optional[str]) -> None:
        if not hasattr(self, 'race_combo') or not self.race_combo or race_key is None:
            return
        for index in range(self.race_combo.count()):
            data = self.race_combo.itemData(index)
            if isinstance(data, SeasonEvent) and data.race_key == race_key:
                self.race_combo.setCurrentIndex(index)
                return

    def get_selected_event(self) -> Optional[SeasonEvent]:
        if not hasattr(self, 'race_combo') or not self.race_combo:
            return None
        data = self.race_combo.currentData()
        if isinstance(data, SeasonEvent):
            return data
        display_text = self.race_combo.currentText()
        race_key = self._display_to_race_key.get(display_text)
        if not race_key and self.main_window:
            race_key = self.main_window._strip_race_display(display_text)
            race_key = self._display_to_race_key.get(race_key, race_key)
        return self._season_event_lookup.get(race_key)

    def get_selected_race_key(self) -> str:
        event = self.get_selected_event()
        if event:
            return event.race_key
        display_text = self.race_combo.currentText() if hasattr(self, 'race_combo') else ''
        race_key = self._display_to_race_key.get(display_text)
        if not race_key and self.main_window:
            race_key = self.main_window._strip_race_display(display_text)
        return race_key or self.local_race or "Unknown"

    def get_selected_session_code(self) -> str:
        if not hasattr(self, 'session_combo') or not self.session_combo:
            return self.local_session or "R"
        data = self.session_combo.currentData()
        if data and hasattr(data, "code"):
            return getattr(data, "code")
        text = self.session_combo.currentText()
        return text if text else (self.local_session or "R")

    def _update_session_combo(self, event: Optional[SeasonEvent] = None, preserve_session_code: Optional[str] = None) -> None:
        if not hasattr(self, 'session_combo') or not self.session_combo:
            return

        event = event or self.get_selected_event()
        self.session_combo.blockSignals(True)
        self.session_combo.clear()

        if isinstance(event, SeasonEvent) and event.sessions:
            codes = []
            for session in event.sessions:
                self.session_combo.addItem(session.code, session)
                codes.append(session.code)

            target_code = preserve_session_code or self.local_session or ("R" if "R" in codes else (codes[0] if codes else None))
            if target_code:
                index = self.session_combo.findText(target_code)
                if index < 0:
                    index = self.session_combo.findText(target_code.upper())
                if index >= 0:
                    self.session_combo.setCurrentIndex(index)
                elif self.session_combo.count() > 0:
                    self.session_combo.setCurrentIndex(0)
        else:
            for code in ["FP1", "FP2", "FP3", "SQ", "Q", "R"]:
                self.session_combo.addItem(code)
            target_code = preserve_session_code or self.local_session
            if target_code:
                index = self.session_combo.findText(target_code)
                if index >= 0:
                    self.session_combo.setCurrentIndex(index)

        self.session_combo.blockSignals(False)



    def get_current_parameters(self):
        """獲取當前參數"""
        if self.sync_enabled and self._parameter_provider:
            # 同步模式：返回主視窗參數
            return {
                'year': self._parameter_provider.get_current_year(),
                'race': self._parameter_provider.get_current_race(), 
                'session': self._parameter_provider.get_current_session()
            }
        else:
            # 非同步模式：返回本地參數
            return {
                'year': self.local_year,
                'race': self.local_race,
                'session': self.local_session
            }
    
    def _legacy_update_current_window(self):
        """舊版視窗更新邏輯 - 保持向後相容性"""
        try:
            # 嘗試從主視窗獲取參數（舊版方式）
            year = "2025"
            race = "Japan" 
            session = "R"
            
            if self._parameter_provider:
                year = self._parameter_provider.get_current_year()
                race = self._parameter_provider.get_current_race()
                session = self._parameter_provider.get_current_session()
            
            print(f"[REFRESH] [LEGACY] {self.windowTitle()} 舊版更新: {year} {race} {session}")
            
            # 如果內容widget有更新方法，調用它
            if self.content_widget and hasattr(self.content_widget, 'update'):
                self.content_widget.update()
                return True
            
            return True
            
        except Exception as e:
            print(f"[ERROR] [LEGACY] 舊版更新失敗: {e}")
            return False
        
        # [TEST][HOT] 設置最小尺寸防止縮小到無法使用 - 已取消限制
        # self.setMinimumSize(250, 150)  # 移除最小尺寸限制
        #print(f"[LOCK] 最小尺寸限制已取消")
        
        # [HOT] 隱藏所有 MDI 子窗口的標題列
        # [修改] 保留邊框，只隱藏標題列
        # 使用自定義方式隱藏標題列但保留邊框
        self.setWindowFlags(Qt.SubWindow)  # 移除 FramelessWindowHint 以保留邊框
        #print(f"[LABEL] MDI子窗口 - 保留邊框，隱藏標題列")
        
        # 設置邊距以適應邊框
        self.setContentsMargins(2, 2, 2, 2)  # 為邊框留出空間
        
        # [HOT] 強化邊框樣式設置 - 確保邊框可見
        subwindow_qss = """
            PopoutSubWindow {
                background-color: #FFFFFF;
                border: 2px solid #666666;  /* 加粗邊框以確保可見 */
                border-radius: 2px;
            }
            QMdiSubWindow {
                background-color: #FFFFFF;
                border: 2px solid #666666;
                margin: 0px;
                padding: 2px;
                border-radius: 2px;
            }
            QMdiSubWindow[objectName="ProfessionalSubWindow"] {
                background-color: #FFFFFF;
                border: 2px solid #666666;  /* 強化邊框 */
                border-radius: 2px;
            }
            
            /* 隱藏標題列但保留邊框 */
            QMdiSubWindow::title {
                height: 0px;
                margin: 0px;
                padding: 0px;
                background: transparent;
                border: none;
            }
            
            /* 接收同步按鈕 - 紅綠狀態指示 (子窗口專用) */
            #SyncButton {
                background-color: #FF4444;  /* 預設紅色 - 獨立模式 */
                color: #FFFFFF;
                border: 1px solid #CC0000;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #SyncButton:hover {
                background-color: #FF6666;  /* 紅色懸停 */
            }
            #SyncButton:pressed {
                background-color: #CC0000;  /* 紅色按下 */
            }
            #SyncButton:checked {
                background-color: #00CC00;  /* 綠色 - 接收同步 */
                border: 1px solid #009900;
            }
            #SyncButton:checked:hover {
                background-color: #00FF00;  /* 綠色懸停 */
            }
            
            /* 個別連動按鈕 - 藍色主題 */
            #LinkageButton {
                background-color: #2196F3;  /* 藍色 - 連動啟用 */
                color: white;
                border: 1px solid #1976D2;
                border-radius: 3px;
                font-size: 8px;
                font-weight: bold;
                text-align: center;
            }
            #LinkageButton:hover {
                background-color: #42A5F5;  /* 藍色懸停 */
            }
            #LinkageButton:pressed {
                background-color: #1565C0;  /* 藍色按下 */
            }
            #LinkageButton:!checked {
                background-color: #9E9E9E;  /* 灰色 - 連動停用 */
                border: 1px solid #757575;
            }
            #LinkageButton:!checked:hover {
                background-color: #BDBDBD;  /* 灰色懸停 */
            }
            
            /* 視窗控制按鈕 - 與主視窗保持一致 */
            #WindowControlButton {
                background-color: #F0F0F0;
                color: #000000;
                border: 1px solid #D0D0D0;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #WindowControlButton:hover {
                background-color: #E0E0E0;
            }
            #WindowControlButton:pressed {
                background-color: #D0D0D0;
            }
            
            /* 設定按鈕 */
            #SettingsButton {
                background-color: #F0F0F0;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #SettingsButton:hover {
                background-color: #E8E8E8;
            }
            #SettingsButton:pressed {
                background-color: #D8D8D8;
            }
        """
        self.setStyleSheet(subwindow_qss)
        #print(f"[OK] Direct QSS applied to subwindow: {len(subwindow_qss)} characters")
        #print(f"[DESIGN] QSS content: {subwindow_qss[:100]}...")
        
        # 調整大小相關屬性
        self.resize_margin = 3  # 視覺邊框寬度 (3像素，與QSS邊框一致)
        self.resize_detection_margin = 10  # 實際可操作區域 (10像素)
        self.resizing = False
        self.resize_direction = None
        
        #print(f"📏 Resize margins - Visual: {self.resize_margin}px, Detection: {self.resize_detection_margin}px")
        
        # 強制啟用滑鼠追蹤
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_MouseTracking, True)
        
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 處理調整大小"""
        if event.button() == Qt.LeftButton:
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 處理調整大小和游標"""
        if self.resizing and self.resize_direction:
            self.perform_resize(event.globalPos())
            event.accept()
            return
            
        # 更新游標 - 即使沒有在調整也要檢查
        direction = self.get_resize_direction(event.pos())
        
        if direction:
            # 取消上方調整大小功能，移除 'top' 相關游標
            if direction in ['bottom']:  # 只保留 bottom，移除 top
                self.setCursor(Qt.SizeVerCursor)
            elif direction in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            elif direction in ['bottom-right']:  # 移除 top-left
                self.setCursor(Qt.SizeFDiagCursor)
            elif direction in ['bottom-left']:  # 移除 top-right
                self.setCursor(Qt.SizeBDiagCursor)
            event.accept()  # 接受事件，防止被覆蓋
        else:
            self.setCursor(Qt.ArrowCursor)
            
        # [HOT] 重要：讓事件傳遞給父類以保持拖動功能
        super().mouseMoveEvent(event)
        
    def enterEvent(self, event):
        """滑鼠進入事件"""
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """滑鼠離開事件 - 恢復箭頭游標"""
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束調整大小"""
        if event.button() == Qt.LeftButton:
            self.resizing = False
            self.resize_direction = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
        
    def get_resize_direction(self, pos):
        """判斷調整方向 - 使用10像素檢測區域（取消上方調整大小）"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        detection_margin = self.resize_detection_margin  # 10像素檢測區域
        
        # 角落區域 (優先判斷) - 取消上方相關的角落調整
        # if x <= detection_margin and y <= detection_margin:
        #     return 'top-left'
        # elif x >= w - detection_margin and y <= detection_margin:
        #     return 'top-right'
        if x <= detection_margin and y >= h - detection_margin:
            return 'bottom-left'
        elif x >= w - detection_margin and y >= h - detection_margin:
            return 'bottom-right'
        # 邊緣區域 - 取消上方調整，保留左、右、下
        # elif y <= detection_margin:
        #     return 'top'
        elif y >= h - detection_margin:
            return 'bottom'
        elif x <= detection_margin:
            return 'left'
        elif x >= w - detection_margin:
            return 'right'
        
        return None
        
    def perform_resize(self, global_pos):
        """執行調整大小"""
        if not self.resize_direction:
            return
            
        delta = global_pos - self.resize_start_pos
        old_geometry = self.resize_start_geometry
        
        new_x = old_geometry.x()
        new_y = old_geometry.y()
        new_width = old_geometry.width()
        new_height = old_geometry.height()
        
        # 根據方向調整
        if 'left' in self.resize_direction:
            new_x = old_geometry.x() + delta.x()
            new_width = old_geometry.width() - delta.x()
        elif 'right' in self.resize_direction:
            new_width = old_geometry.width() + delta.x()
            
        # 取消 top 調整，只保留 bottom
        # if 'top' in self.resize_direction:
        #     new_y = old_geometry.y() + delta.y()
        #     new_height = old_geometry.height() - delta.y()
        if 'bottom' in self.resize_direction:
            new_height = old_geometry.height() + delta.y()
            
        # 限制最小大小
        min_width, min_height = 200, 150
        if new_width < min_width:
            if 'left' in self.resize_direction:
                new_x = old_geometry.x() + old_geometry.width() - min_width
            new_width = min_width
            
        if new_height < min_height:
            # 取消 top 調整功能
            # if 'top' in self.resize_direction:
            #     new_y = old_geometry.y() + old_geometry.height() - min_height
            new_height = min_height
            
        # 限制在MDI區域內
        if self.parent_mdi:
            mdi_rect = self.parent_mdi.rect()
            if new_x < 0:
                new_x = 0
            if new_y < 0:
                new_y = 0
            if new_x + new_width > mdi_rect.width():
                if 'right' in self.resize_direction:
                    new_width = mdi_rect.width() - new_x
                else:
                    new_x = mdi_rect.width() - new_width
            if new_y + new_height > mdi_rect.height():
                if 'bottom' in self.resize_direction:
                    new_height = mdi_rect.height() - new_y
                else:
                    new_y = mdi_rect.height() - new_height
            
        # 應用新的幾何形狀
        self.setGeometry(new_x, new_y, new_width, new_height)
        
    def paintEvent(self, event):
        """繪製事件 - 使用QSS邊框，只繪製右下角提示"""
        #print(f"[DESIGN] DEBUG: PopoutSubWindow paintEvent called for {self.windowTitle()}")
        #print(f"📐 Window size: {self.width()}x{self.height()}")
        #print(f"[PIN] Window position: ({self.x()}, {self.y()})")
        #print(f"🔲 Window rect: {self.rect()}")
        #print(f"[THEATER] Window frameless: {self.windowFlags() & Qt.FramelessWindowHint}")
        #print(f"[DESIGN] Self QSS length: {len(self.styleSheet())}")
        #print(f"🏠 Parent QSS length: {len(self.parent().styleSheet()) if self.parent() else 'No parent'}")
        
        # 調用父類方法繪製基本內容
        super().paintEvent(event)
        
        # 只繪製右下角調整提示
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 右下角調整提示 (白色)
        corner_size = 8
        corner_color = QColor(255, 255, 255, 120)
        painter.fillRect(
            w - corner_size, 
            h - corner_size, 
            corner_size, 
            corner_size, 
            corner_color
        )
        
        # 繪製右下角調整線條 (白色)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        for i in range(3):
            offset = 2 + i * 2
            painter.drawLine(
                w - offset, h - 2,
                w - 2, h - offset
            )
            
        # 在四個角落添加小的調整提示 (2像素白色方塊)
        corner_indicator_size = 2
        corner_indicator_color = QColor(255, 255, 255, 150)
        
        # 左上角
        painter.fillRect(0, 0, corner_indicator_size, corner_indicator_size, corner_indicator_color)
        # 右上角  
        painter.fillRect(w - corner_indicator_size, 0, corner_indicator_size, corner_indicator_size, corner_indicator_color)
        # 左下角
        painter.fillRect(0, h - corner_indicator_size, corner_indicator_size, corner_indicator_size, corner_indicator_color)
        # 右下角已經有了更明顯的提示
        
    def setWidget(self, widget):
        """設置內容小部件並添加彈出按鈕"""
        #print(f"[TOOL] DEBUG: PopoutSubWindow.setWidget called for {self.windowTitle()}")
        
        # 創建包裝容器
        wrapper = QWidget()
        wrapper.setObjectName("SubWindowWrapper")
        wrapper_layout = QVBoxLayout(wrapper)
        
        # 標題欄不需要邊距，應該延伸到邊緣
        wrapper_layout.setContentsMargins(0, 0, 0, 0)  # 移除所有邊距
        wrapper_layout.setSpacing(0)
        
        # 確保wrapper本身也沒有邊距
        wrapper.setStyleSheet("""
            #SubWindowWrapper {
                margin: 0px;
                padding: 0px;
                border: none;
                background-color: transparent;
            }
        """)
        
        #print(f"[PACKAGE] Wrapper margins set to: 0px (標題欄延伸到邊緣)")
        #print(f"[DESIGN] Wrapper ObjectName: {wrapper.objectName()}")
        
        # 創建可拖拽的自定義標題欄
        self.title_bar = DraggableTitleBar(self, self.windowTitle())
        wrapper_layout.addWidget(self.title_bar)
        
        # 確保標題欄使用正確的 QSS
        self.title_bar.setStyleSheet(self.styleSheet())
        #print(f"[DESIGN] DEBUG: Applied QSS to CustomTitleBar: {len(self.styleSheet())} characters")
        
        # 創建內容容器，為內容添加邊距
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        margin = getattr(self, 'resize_margin', 3)  # 安全訪問，預設3像素
        content_layout.setContentsMargins(margin, margin, margin, margin)
        content_layout.setSpacing(0)
        content_layout.addWidget(widget)
        
        # 添加內容容器到主layout
        wrapper_layout.addWidget(content_container)
        
        # 保存內容widget引用
        self.content_widget = widget
        
        # 確保包裝器不攔截滑鼠事件
        wrapper.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        wrapper.setMouseTracking(True)
        
        # 設置包裝器為主widget
        super().setWidget(wrapper)
        
        # [移除] 不再設置最小尺寸限制，允許完全自由縮放
        # self.setMinimumSize(250, 150) - 已移除
        #print(f"[LOCK] 移除尺寸限制，允許自由縮放")
        
        # [移除] 不再計算標題欄最小高度限制
        # title_height = self.title_bar.height() if hasattr(self, 'title_bar') else 20
        # min_height = max(150, title_height + 100) - 已移除
        #print(f"[LOCK] 無尺寸限制")
        
    def setMinimumSize(self, *args):
        """覆寫 setMinimumSize 來追蹤誰在修改最小尺寸"""
        if len(args) == 1:  # QSize 參數
            size = args[0]
            #print(f"[ALERT] setMinimumSize 被調用: {size.width()}x{size.height()}")
        elif len(args) == 2:  # width, height 參數
            width, height = args
            #print(f"[ALERT] setMinimumSize 被調用: {width}x{height}")
            
        # 強制確保最小尺寸不小於我們的限制
        if len(args) == 2:
            width, height = args
            width = max(width, 250)
            height = max(height, 150)
            args = (width, height)
            #print(f"[LOCK] 強制調整最小尺寸至: {width}x{height}")
        elif len(args) == 1:
            size = args[0]
            width = max(size.width(), 250)
            height = max(size.height(), 150)
            from PyQt5.QtCore import QSize
            args = (QSize(width, height),)
            #print(f"[LOCK] 強制調整最小尺寸至: {width}x{height}")
            
        super().setMinimumSize(*args)
        
    def minimumSize(self):
        """移除強制最小尺寸，返回系統預設"""
        # 不再強制返回固定尺寸，讓系統自然處理
        return super().minimumSize()
        
    def minimumSizeHint(self):
        """移除強制最小尺寸提示，返回系統預設"""
        # 不再強制返回固定尺寸提示，讓系統自然處理
        return super().minimumSizeHint()
        
    def resizeEvent(self, event):
        """處理窗口縮放事件，確保不會小於最小尺寸"""
        #print(f"[TOOL] PopoutSubWindow: resizeEvent 被調用，新尺寸: {event.size().width()}x{event.size().height()}")
        super().resizeEvent(event)
        
        # [HOT] 強制檢查最小尺寸限制（不依賴 minimumSize()）
        MIN_WIDTH = 250
        MIN_HEIGHT = 150
        
        current_size = self.size()
        
        #print(f"[LOCK] PopoutSubWindow: 強制最小尺寸: {MIN_WIDTH}x{MIN_HEIGHT}")
        #print(f"[LOCK] PopoutSubWindow: 當前尺寸: {current_size.width()}x{current_size.height()}")
        
        needs_resize = False
        new_width = current_size.width()
        new_height = current_size.height()
        
        if current_size.width() < MIN_WIDTH:
            new_width = MIN_WIDTH
            needs_resize = True
            #print(f"[WARNING] 寬度低於最小值，調整: {current_size.width()} -> {new_width}")
            
        if current_size.height() < MIN_HEIGHT:
            new_height = MIN_HEIGHT
            needs_resize = True
            #print(f"[WARNING] 高度低於最小值，調整: {current_size.height()} -> {new_height}")
        
        if needs_resize:
            #print(f"[LOCK] 即將強制調整至最小尺寸: {new_width}x{new_height}")
            # 使用 QTimer 延遲調整，避免與Qt內部的調整衝突
            QTimer.singleShot(0, lambda: self._force_resize(new_width, new_height))
        
        # 發射調整大小信號
        self.resized.emit()
        #print(f"📡 PopoutSubWindow: 發射 resized 信號")
        
    def _force_resize(self, width, height):
        """強制調整尺寸"""
        #print(f"💥 強制調整視窗尺寸至: {width}x{height}")
        self.resize(width, height)
        # 也嘗試更新幾何形狀
        current_pos = self.pos()
        self.setGeometry(current_pos.x(), current_pos.y(), width, height)
    
    def showEvent(self, event):
        """窗口顯示時確保最小尺寸"""
        super().showEvent(event)
        min_size = self.minimumSize()
        if self.size().width() < min_size.width() or self.size().height() < min_size.height():
            self.resize(min_size)
            #print(f"[LOCK] showEvent 強制調整至最小尺寸: {min_size.width()}x{min_size.height()}")

    def create_window_control_panel(self):
        """創建視窗控制面板"""
        control_panel = QWidget()
        control_panel.setObjectName("WindowControlPanel")
        control_panel.setFixedHeight(35)
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 3, 5, 3)
        control_layout.setSpacing(10)
        
        # 視窗同步名稱勾選框
        self.sync_windows_checkbox = QCheckBox("[LINK] Sync Other Windows")
        self.sync_windows_checkbox.setObjectName("SyncWindowsCheckbox")
        self.sync_windows_checkbox.setChecked(True)
        self.sync_windows_checkbox.setToolTip("Sync other windows (Race/Session/Year sync)")
        self.sync_windows_checkbox.toggled.connect(self.on_sync_windows_toggled)
        control_layout.addWidget(self.sync_windows_checkbox)
        
        control_layout.addStretch()
        
        # 年份選擇器
        year_label = QLabel(tr("year"))
        year_label.setObjectName("ControlLabel")
        control_layout.addWidget(year_label)
        
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("AnalysisComboBox")
        self.year_combo.addItems([str(year) for year in range(2020, 2026)])
        self.year_combo.setCurrentText("2025")
        self.year_combo.setFixedWidth(70)
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        control_layout.addWidget(self.year_combo)
        
        # 賽事選擇器
        race_label = QLabel(tr("race"))
        race_label.setObjectName("ControlLabel")
        control_layout.addWidget(race_label)
        
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("AnalysisComboBox")
        # [TOOL] 修復: 使用動態賽事列表而非硬編碼
        current_year = self.year_combo.currentText()
        self.update_races_for_year(current_year)
        self._select_race_by_key(self.local_race)
        self.race_combo.setFixedWidth(250)
        self.race_combo.currentTextChanged.connect(self.on_race_changed)
        control_layout.addWidget(self.race_combo)
        
        # 賽段選擇器
        session_label = QLabel(tr("session"))
        session_label.setObjectName("ControlLabel")
        control_layout.addWidget(session_label)
        
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("AnalysisComboBox")
        self._update_session_combo(preserve_session_code=self.local_session)
        self.session_combo.setFixedWidth(70)
        self.session_combo.currentTextChanged.connect(self.on_session_changed)
        control_layout.addWidget(self.session_combo)
        
        # 重新分析按鈕
        reanalyze_btn = QPushButton("R")
        reanalyze_btn.setObjectName("ReanalyzeButton")
        reanalyze_btn.setFixedSize(25, 25)
        reanalyze_btn.setToolTip("Reanalyze")
        reanalyze_btn.clicked.connect(self.perform_reanalysis)
        control_layout.addWidget(reanalyze_btn)
        
        return control_panel
        
    def on_sync_windows_toggled(self, checked):
        """處理視窗連動開關"""
        window_title = self.windowTitle()
        status = "啟用" if checked else "停用"
        #print(f"[LINK] [{window_title}] 視窗連動已{status}")
        
        # 如果啟用連動，同步當前參數到其他視窗
        if checked:
            self.sync_to_other_windows()
        
    def on_year_changed(self, year):
        """處理年份變更"""
        window_title = self.windowTitle()
        #print(f"[CALENDAR] [{window_title}] 年份變更為: {year}")
        
        # [TOOL] 新增: 動態更新賽事列表
        self.update_races_for_year(year)

        self.local_year = str(year)
        
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
        else:
            self.update_current_window()
            
    def on_race_changed(self, race):
        """處理賽事變更"""
        window_title = self.windowTitle()
        #print(f"[FINISH] [{window_title}] 賽事變更為: {race}")
        
        event = self.get_selected_event()
        if event:
            self.local_race = event.race_key
        else:
            canonical = self._display_to_race_key.get(race)
            if canonical:
                self.local_race = canonical

        self._update_session_combo()

        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
        else:
            self.update_current_window()
            
    def on_session_changed(self, session):
        """處理賽段變更"""
        window_title = self.windowTitle()
        #print(f"[F1] [{window_title}] 賽段變更為: {session}")
        
        self.local_session = self.get_selected_session_code()

        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
        else:
            self.update_current_window()
            
    def perform_reanalysis(self):
        """執行重新分析 - 使用安全的參數獲取"""
        window_title = self.windowTitle()
        
        # [TOOL] 使用安全的參數獲取方法
        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
        
        #print(f"[REFRESH] [{window_title}] 開始重新分析")
        #print(f"   參數: {year} {race} {session}")
        #print(f"   視窗連動: {'是' if self.sync_windows_checkbox.isChecked() else '否'}")
        
        # 重新分析當前視窗
        self.update_current_window()
        
        # 如果啟用連動，也更新其他視窗
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
            
    def sync_to_other_windows(self):
        """同步參數到其他視窗 - 使用安全的參數獲取"""
        window_title = self.windowTitle()
        
        # [TOOL] 使用安全的參數獲取方法
        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
        
        print(f"[REFRESH] [{window_title}] 同步參數到其他視窗: {year} {race} {session}")
        
        # 同步到同一MDI區域中的其他子視窗
        synced_count = 0
        if self.parent_mdi:
            for subwindow in self.parent_mdi.subWindowList():
                if subwindow != self and hasattr(subwindow, 'set_analysis_parameters'):
                    # 檢查其他子視窗是否啟用同步
                    if hasattr(subwindow, 'sync_windows_checkbox') and \
                       subwindow.sync_windows_checkbox.isChecked():
                        
                        params = {
                            'year': year,
                            'race': race,
                            'session': session
                        }
                        subwindow.set_analysis_parameters(params, skip_sync=True)
                        synced_count += 1
                        print(f"[REFRESH] 同步到子視窗: {subwindow.windowTitle()}")
        
        print(f"[OK] 完成子視窗同步，共更新 {synced_count} 個視窗")
            
    def _legacy_update_current_window(self):
        """舊版更新當前視窗的分析數據 - 使用安全的參數獲取"""
        window_title = self.windowTitle()
        
        # [TOOL] 使用安全的參數獲取方法
        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
        
        print(f"[REFRESH] [{window_title}] 舊版更新視窗數據: {year} {race} {session}")
        
        # 啟動資料載入流程
        self.load_race_data(year, race, session)
    
    def load_race_data(self, year, race, session):
        """載入比賽資料 - 完整的JSON載入流程"""
        # Step 1: 載入JSON
        json_data = self.try_load_json(year, race, session)
        
        if json_data:
            # JSON存在，直接使用
            print(f"[OK] 找到JSON檔案，直接載入資料")
            self.update_charts_and_analysis(json_data)
        else:
            # Step 2: 無JSON則進行CLI參數呼叫
            print(f"[ERROR] 未找到JSON檔案，啟動CLI分析...")
            self.call_cli_analysis(year, race, session)
            # 注意：JSON監控已在 call_cli_analysis 中啟動
    
    def try_load_json(self, year, race, session):
        """嘗試載入JSON檔案 - 與RainAnalysisCache保持一致"""
        import glob
        import os
        
        # 嘗試與 RainAnalysisCache 相同的搜尋邏輯
        # 1. 先嘗試降雨分析的標準格式
        rain_analysis_file = f"json/rain_analysis_{year}_{race}_{session}.json"
        if os.path.exists(rain_analysis_file):
            try:
                with open(rain_analysis_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] JSON載入錯誤: {e}")
        
        # 2. 備用搜尋 - 構建JSON檔案搜尋模式
        json_patterns = [
            f"json/*{year}*{race}*{session}*.json",
            f"json_exports/*{year}*{race}*{session}*.json", 
            f"cache/*{year}*{race}*{session}*.json"
        ]
        
        for pattern in json_patterns:
            json_files = glob.glob(pattern)
            if json_files:
                # 過濾掉非JSON檔案
                json_files = [f for f in json_files if f.lower().endswith('.json')]
                if json_files:
                    json_file = json_files[0]  # 取第一個符合的檔案
                    print(f"[FILES] 找到JSON檔案: {json_file}")
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception as e:
                        print(f"[ERROR] JSON載入錯誤: {e}")
                        continue
        
        print(f"[WARNING] 未找到適合的JSON檔案: {year}/{race}/{session}")
        return None
    
    def get_races_for_year_in_subwindow(self, year):
        """子視窗中根據年份獲取賽事列表（與主視窗保持一致）"""
        try:
            year_int = int(year)
            events = self._get_calendar_events_for_year(year_int)
            self._rebuild_race_mapping(events)
            race_labels = [self._format_race_display(event) for event in events]
            print(f"[SUBWINDOW] 載入 {year_int} 年的賽事列表: {len(race_labels)} 個賽事")
            return race_labels
        except Exception as e:
            print(f"[SUBWINDOW ERROR] 獲取賽事列表時出錯: {e}")
            return ["Japan", "Great Britain", "Monaco"]  # 回退列表
    
    def update_races_for_year(self, year):
        """為指定年份更新賽事列表"""
        if not hasattr(self, 'race_combo') or not self.race_combo:
            return

        try:
            year_int = int(year)
        except Exception:
            year_int = int(self.local_year) if self.local_year else 2025

        previous_race_key = self.get_selected_race_key()
        if not previous_race_key or previous_race_key == "Unknown":
            previous_race_key = self.local_race

        events = self._get_calendar_events_for_year(year_int)
        self._rebuild_race_mapping(events)

        self.race_combo.blockSignals(True)
        self.race_combo.clear()

        completed_events = [event for event in events if event.is_completed]
        upcoming_events = [event for event in events if not event.is_completed]

        def add_event(event: SeasonEvent) -> None:
            label = self._format_race_display(event)
            self._display_to_race_key[label] = event.race_key
            self.race_combo.addItem(label, event)

        for event in completed_events:
            add_event(event)

        if completed_events and upcoming_events:
            self.race_combo.insertSeparator(self.race_combo.count())

        for event in upcoming_events:
            add_event(event)

        if previous_race_key:
            self._select_race_by_key(previous_race_key)

        if self.race_combo.currentIndex() < 0:
            preferred_event = completed_events[0] if completed_events else (upcoming_events[0] if upcoming_events else None)
            if preferred_event is not None:
                index = self.race_combo.findData(preferred_event)
                if index >= 0:
                    self.race_combo.setCurrentIndex(index)
        if self.race_combo.currentIndex() < 0 and self.race_combo.count() > 0:
            self.race_combo.setCurrentIndex(0)

        self.race_combo.blockSignals(False)

        selected_event = self.get_selected_event()
        if selected_event:
            self.local_race = selected_event.race_key

        self._update_session_combo(preserve_session_code=self.local_session)

        print(f"[SUBWINDOW] 已更新賽事列表，當前選擇: {self.get_selected_race_key()}")
    
    def call_cli_analysis(self, year, race, session):
        """呼叫CLI參數進行分析 - 使用背景執行緒避免GUI凍結"""
        
        # 如果已有分析在執行，先停止
        if hasattr(self, 'cli_worker') and self.cli_worker and self.cli_worker.isRunning():
            self.stop_cli_analysis()
        
        # 創建進度顯示
        self.show_analysis_progress()
        
        # 創建並啟動工作執行緒 - 速度分析使用函數 13
        self.cli_worker = CliAnalysisWorker(year, race, session, 13)
        
        # 連接信號
        self.cli_worker.progress_updated.connect(self.on_analysis_progress)
        self.cli_worker.analysis_completed.connect(self.on_analysis_completed)
        self.cli_worker.output_received.connect(self.on_analysis_output)
        
        # 啟動執行緒
        self.cli_worker.start()
        
        # 開始等待 JSON 產生
        self.start_json_monitoring(year, race, session)
        
        print(f"[START] CLI 分析執行緒已啟動: {year} {race} {session}")
    
    def stop_cli_analysis(self):
        """停止 CLI 分析"""
        if hasattr(self, 'cli_worker') and self.cli_worker and self.cli_worker.isRunning():
            self.cli_worker.stop()
            self.cli_worker.wait(5000)  # 等待最多 5 秒
            print("[TEST] CLI 分析已停止")
        
        # 停止 JSON 監控
        self.stop_json_monitoring()
        
        # 隱藏進度顯示
        self.hide_analysis_progress()
    
    def show_analysis_progress(self):
        """顯示分析進度"""
        if not hasattr(self, 'progress_dialog'):
            from PyQt5.QtWidgets import QProgressDialog
            self.progress_dialog = QProgressDialog("Executing F1 Data Analysis...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.canceled.connect(self.stop_cli_analysis)
        
        self.progress_dialog.setLabelText(tr("starting_cli_analysis"))
        self.progress_dialog.show()
    
    def hide_analysis_progress(self):
        """隱藏分析進度"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.hide()
    
    def on_analysis_progress(self, message):
        """處理分析進度更新"""
        print(f"[STATS] {message}")
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setLabelText(message)
    
    def on_analysis_output(self, output):
        """處理分析輸出"""
        print(f"[UPLOAD] CLI 輸出: {output}")
        # 可以在這裡處理特定的輸出訊息來更新進度
        if "下載" in output or "Download" in output.lower():
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.setLabelText(f"{tr('downloading_data')} {output[:50]}...")
        elif "分析" in output or "Analysis" in output.lower():
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.setLabelText(f"正在分析數據... {output[:50]}...")
    
    def on_analysis_completed(self, success, message):
        """處理分析完成"""
        print(f"[OK] CLI 分析完成: {success}, {message}")
        
        if success:
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.setLabelText("分析完成，正在載入結果...")
        else:
            print(f"[ERROR] CLI 分析失敗: {message}")
            from core.gui_i18n import tr
            QMessageBox.warning(self, tr('analysis_failed', 'Analysis Failed'), f"{tr('cli_error', 'Error occurred during CLI analysis')}:\n{message}")
            self.hide_analysis_progress()
            self.stop_json_monitoring()
    
    def start_json_monitoring(self, year, race, session):
        """開始監控 JSON 檔案產生"""
        # 停止任何現有的監控
        self.stop_json_monitoring()
        
        # 設置JSON檢查計時器
        self.json_check_timer = QTimer()
        self.json_check_timer.timeout.connect(
            lambda: self.check_json_ready(year, race, session)
        )
        self.json_check_timer.start(3000)  # 每3秒檢查一次
        
        # 設置最大等待時間 (120秒)，給數據下載更多時間
        self.max_wait_timer = QTimer()
        self.max_wait_timer.setSingleShot(True)
        self.max_wait_timer.timeout.connect(self.on_json_wait_timeout)
        self.max_wait_timer.start(120000)  # 120秒超時
        
        print(f"⏳ 開始監控 JSON 檔案產生... (最多等待120秒)")
    
    def stop_json_monitoring(self):
        """停止 JSON 監控"""
        if hasattr(self, 'json_check_timer') and self.json_check_timer:
            self.json_check_timer.stop()
        if hasattr(self, 'max_wait_timer') and self.max_wait_timer:
            self.max_wait_timer.stop()
    
    def check_json_ready(self, year, race, session):
        """檢查JSON是否已準備好"""
        # 檢查 JSON 檔案
        json_data = self.try_load_json(year, race, session)
        
        if json_data:
            # JSON已產生，停止監控
            self.stop_json_monitoring()
            
            print(f"[OK] JSON檔案已產生，開始載入資料")
            
            # 更新進度顯示
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.setLabelText("正在載入分析結果...")
            
            # 載入並顯示數據
            self.update_charts_and_analysis(json_data)
            
            # 隱藏進度顯示
            self.hide_analysis_progress()
        else:
            print(f"⏳ 繼續等待JSON檔案產生...")
    
    def on_json_wait_timeout(self):
        """JSON等待超時處理"""
        self.stop_json_monitoring()
        self.hide_analysis_progress()
        
        print(f"[TIME] JSON等待超時，分析可能失敗或仍在進行中")
        
        # 顯示超時警告
        QMessageBox.warning(
            self, 
            "分析超時", 
            "數據分析超時。\n\n可能原因：\n1. 網路連線緩慢\n2. 數據量過大\n3. 伺服器回應慢\n\n請稍後再試，或檢查網路連線。"
        )
    
    def update_charts_and_analysis(self, json_data):
        """更新圖表和分析結果"""
        print(f"[STATS] 開始更新圖表和分析結果...")
        
        try:
            # 檢查當前視窗是否為速度分析視窗
            window_title = self.windowTitle()
            print(f"[CHART UPDATE] 更新視窗: {window_title}")
            
            if '速度分析' in window_title or 'Speed Analysis' in window_title:
                print(f"[SPEED UPDATE] 檢測到速度分析視窗，使用專用更新邏輯")
                self._update_speed_analysis_chart(json_data)
            elif '油門分析' in window_title or 'Throttle Analysis' in window_title:
                print(f"[THROTTLE UPDATE] 檢測到油門分析視窗，使用專用更新邏輯")
                self._update_throttle_analysis_chart(json_data)
            elif 'RPM分析' in window_title or 'RPM Analysis' in window_title:
                print(f"[RPM UPDATE] 檢測到RPM分析視窗，使用專用更新邏輯")
                self._update_rpm_analysis_chart(json_data)
            elif '檔位分析' in window_title or 'Gear Analysis' in window_title:
                print(f"[GEAR UPDATE] 檢測到檔位分析視窗，使用專用更新邏輯")
                self._update_gear_analysis_chart(json_data)
            else:
                # 更新遙測圖表
                if 'telemetry' in json_data:
                    self.update_telemetry_chart(json_data['telemetry'])
                    
                # 更新軌道地圖
                if 'track_data' in json_data:
                    self.update_track_map(json_data['track_data'])
                    
                # 更新分析數據
                if 'analysis_results' in json_data:
                    self.update_analysis_data(json_data['analysis_results'])
                
            print(f"[OK] 圖表和分析結果更新完成")
            
        except Exception as e:
            print(f"[ERROR] 圖表更新錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_speed_analysis_chart(self, json_data):
        """更新速度分析圖表的專用方法"""
        print(f"[SPEED UPDATE] ========== 開始更新速度分析圖表 ==========")
        
        try:
            # 尋找速度分析圖表組件
            from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedAnalysisChartWidget
            
            def find_speed_widgets(widget):
                """遞歸查找 SpeedAnalysisChartWidget"""
                widgets = []
                if isinstance(widget, SpeedAnalysisChartWidget):
                    widgets.append(widget)
                
                # 遞歸檢查子組件
                if hasattr(widget, 'findChildren'):
                    for child in widget.findChildren(SpeedAnalysisChartWidget):
                        widgets.append(child)
                elif hasattr(widget, 'children'):
                    for child in widget.children():
                        widgets.extend(find_speed_widgets(child))
                        
                return widgets
            
            speed_widgets = find_speed_widgets(self)
            print(f"[SPEED UPDATE] 找到 {len(speed_widgets)} 個速度分析圖表組件")
            
            if speed_widgets:
                for i, widget in enumerate(speed_widgets):
                    print(f"[SPEED UPDATE] 更新第 {i+1} 個速度分析圖表")
                    
                    # 檢查是否有數據載入器
                    if hasattr(widget, 'speed_loader'):
                        print(f"[SPEED UPDATE] 找到數據載入器，觸發重新載入")
                        
                        # 獲取當前參數
                        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
                        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
                        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
                        
                        # 獲取當前選擇的車手和圈數（而不是硬編碼）
                        driver1 = self.driver1_combo.currentText()
                        # 🔧 修復：使用 currentData() 判斷是否為 "無" 選項（支援多語言）
                        driver2_data = self.driver2_combo.currentData()
                        driver2 = self.driver2_combo.currentText() if driver2_data is not None else driver1
                        lap1 = self.lap1_spinbox.value()
                        lap2 = self.lap2_spinbox.value()
                        is_fastest = self.fastest_lap_checkbox.isChecked()
                        
                        print(f"[SPEED UPDATE] 🎯 使用實際選擇的參數: {driver1} vs {driver2}, 第{lap1}圈 vs 第{lap2}圈, 最速圈: {is_fastest}")
                        print(f"[SPEED UPDATE] 🎯 車手1 combo 值: '{driver1}' (索引: {self.driver1_combo.currentIndex()})")
                        print(f"[SPEED UPDATE] 🎯 車手2 combo 值: '{driver2}' (索引: {self.driver2_combo.currentIndex()}, data: {driver2_data})")
                        
                        # 重新載入數據（使用實際選擇的車手）
                        widget.speed_loader.load_speed_data(
                            year=year,
                            race=race,
                            session=session,
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1,
                            lap2=lap2,
                            is_fastest_lap=is_fastest
                        )
                        print(f"[SPEED UPDATE] ✅ 已觸發數據重新載入")
                    else:
                        print(f"[SPEED UPDATE] ⚠️ 未找到數據載入器")
                        
                        # 嘗試直接更新數據（使用JSON數據）
                        if json_data:
                            print(f"[SPEED UPDATE] 嘗試直接使用JSON數據更新")
                            widget.update_speed_data(json_data)
            else:
                print(f"[SPEED UPDATE] ⚠️ 未找到速度分析圖表組件")
                
            print(f"[SPEED UPDATE] ========== 速度分析圖表更新完成 ==========")
            
        except Exception as e:
            print(f"[ERROR] [SPEED UPDATE] 速度分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_throttle_analysis_chart(self, json_data):
        """更新油門分析圖表的專用方法"""
        print(f"[THROTTLE UPDATE] ========== 開始更新油門分析圖表 ==========")
        
        try:
            # 尋找油門分析圖表組件
            from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
            
            def find_throttle_widgets(widget):
                """遞歸查找 ThrottleAnalysisChartWidget"""
                widgets = []
                if isinstance(widget, ThrottleAnalysisChartWidget):
                    widgets.append(widget)
                
                # 遞歸檢查子組件
                if hasattr(widget, 'findChildren'):
                    for child in widget.findChildren(ThrottleAnalysisChartWidget):
                        widgets.append(child)
                elif hasattr(widget, 'children'):
                    for child in widget.children():
                        widgets.extend(find_throttle_widgets(child))
                        
                return widgets
            
            throttle_widgets = find_throttle_widgets(self)
            print(f"[THROTTLE UPDATE] 找到 {len(throttle_widgets)} 個油門分析圖表組件")
            
            if throttle_widgets:
                for i, widget in enumerate(throttle_widgets):
                    print(f"[THROTTLE UPDATE] 更新第 {i+1} 個油門分析圖表")
                    
                    # 檢查是否有數據載入器
                    if hasattr(widget, 'throttle_loader'):
                        print(f"[THROTTLE UPDATE] 找到數據載入器，觸發重新載入")
                        
                        # 獲取當前參數
                        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
                        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
                        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
                        
                        # 獲取當前選擇的車手和圈數（而不是硬編碼）
                        driver1 = self.driver1_combo.currentText()
                        # 🔧 修復：使用 currentData() 判斷是否為 "無" 選項（支援多語言）
                        driver2_data = self.driver2_combo.currentData()
                        driver2 = self.driver2_combo.currentText() if driver2_data is not None else driver1
                        lap1 = self.lap1_spinbox.value()
                        lap2 = self.lap2_spinbox.value()
                        is_fastest = self.fastest_lap_checkbox.isChecked()
                        
                        print(f"[THROTTLE UPDATE] 🎯 使用實際選擇的參數: {driver1} vs {driver2}, 第{lap1}圈 vs 第{lap2}圈, 最速圈: {is_fastest}")
                        print(f"[THROTTLE UPDATE] 🎯 車手1 combo 值: '{driver1}' (索引: {self.driver1_combo.currentIndex()})")
                        print(f"[THROTTLE UPDATE] 🎯 車手2 combo 值: '{driver2}' (索引: {self.driver2_combo.currentIndex()})")
                        
                        # 重新載入數據（使用實際選擇的車手）
                        widget.throttle_loader.load_throttle_data(
                            year=year,
                            race=race,
                            session=session,
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1,
                            lap2=lap2,
                            is_fastest_lap=is_fastest
                        )
                        print(f"[THROTTLE UPDATE] ✅ 已觸發數據重新載入")
                    else:
                        print(f"[THROTTLE UPDATE] ⚠️ 未找到數據載入器")
                        
                        # 嘗試直接更新數據（使用JSON數據）
                        if json_data:
                            print(f"[THROTTLE UPDATE] 嘗試直接使用JSON數據更新")
                            widget.update_throttle_data(json_data)
            else:
                print(f"[THROTTLE UPDATE] ⚠️ 未找到油門分析圖表組件")
                
            print(f"[THROTTLE UPDATE] ========== 油門分析圖表更新完成 ==========")
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE UPDATE] 油門分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_rpm_analysis_chart(self, json_data):
        """更新RPM分析圖表的專用方法"""
        print(f"[RPM UPDATE] ========== 開始更新RPM分析圖表 ==========")
        
        try:
            # 尋找RPM分析圖表組件
            from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget import RPMAnalysisChartWidget
            
            def find_rpm_widgets(widget):
                """遞歸查找 RPMAnalysisChartWidget"""
                widgets = []
                if isinstance(widget, RPMAnalysisChartWidget):
                    widgets.append(widget)
                
                # 遞歸檢查子組件
                if hasattr(widget, 'findChildren'):
                    for child in widget.findChildren(RPMAnalysisChartWidget):
                        widgets.append(child)
                elif hasattr(widget, 'children'):
                    for child in widget.children():
                        widgets.extend(find_rpm_widgets(child))
                        
                return widgets
            
            rpm_widgets = find_rpm_widgets(self)
            print(f"[RPM UPDATE] 找到 {len(rpm_widgets)} 個RPM分析圖表組件")
            
            if rpm_widgets:
                for i, widget in enumerate(rpm_widgets):
                    print(f"[RPM UPDATE] 更新第 {i+1} 個RPM分析圖表")
                    
                    # 檢查是否有數據載入器
                    if hasattr(widget, 'rpm_loader'):
                        print(f"[RPM UPDATE] 找到數據載入器，觸發重新載入")
                        
                        # 獲取當前參數
                        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
                        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
                        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
                        
                        # 獲取當前選擇的車手和圈數（而不是硬編碼）
                        driver1 = self.driver1_combo.currentText()
                        # 🔧 修復：使用 currentData() 判斷是否為 "無" 選項（支援多語言）
                        driver2_data = self.driver2_combo.currentData()
                        driver2 = self.driver2_combo.currentText() if driver2_data is not None else driver1
                        lap1 = self.lap1_spinbox.value()
                        lap2 = self.lap2_spinbox.value()
                        is_fastest = self.fastest_lap_checkbox.isChecked()
                        
                        print(f"[RPM UPDATE] 🎯 使用實際選擇的參數: {driver1} vs {driver2}, 第{lap1}圈 vs 第{lap2}圈, 最速圈: {is_fastest}")
                        
                        # 重新載入數據（使用實際選擇的車手）
                        widget.rpm_loader.load_rpm_data(
                            year=int(year),
                            race=race,
                            session=session,
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1,
                            lap2=lap2,
                            is_fastest_lap=is_fastest
                        )
                        print(f"[RPM UPDATE] ✅ 已觸發數據重新載入")
                    else:
                        print(f"[RPM UPDATE] ⚠️ 未找到數據載入器")
                        
                        # 嘗試直接更新數據（使用JSON數據）
                        if json_data:
                            print(f"[RPM UPDATE] 嘗試直接使用JSON數據更新")
                            widget.update_rpm_data(json_data)
            else:
                print(f"[RPM UPDATE] ⚠️ 未找到RPM分析圖表組件")
                
            print(f"[RPM UPDATE] ========== RPM分析圖表更新完成 ==========")
            
        except Exception as e:
            print(f"[ERROR] [RPM UPDATE] RPM分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_gear_analysis_chart(self, json_data):
        """更新檔位分析圖表的專用方法"""
        print(f"[GEAR UPDATE] ========== 開始更新檔位分析圖表 ==========")
        
        try:
            # 尋找檔位分析圖表組件
            from modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget import GearAnalysisChartWidget
            
            def find_gear_widgets(widget):
                """遞歸查找 GearAnalysisChartWidget"""
                widgets = []
                if isinstance(widget, GearAnalysisChartWidget):
                    widgets.append(widget)
                
                # 遞歸檢查子組件
                if hasattr(widget, 'findChildren'):
                    for child in widget.findChildren(GearAnalysisChartWidget):
                        widgets.append(child)
                elif hasattr(widget, 'children'):
                    for child in widget.children():
                        widgets.extend(find_gear_widgets(child))
                        
                return widgets
            
            gear_widgets = find_gear_widgets(self)
            print(f"[GEAR UPDATE] 找到 {len(gear_widgets)} 個檔位分析圖表組件")
            
            if gear_widgets:
                for i, widget in enumerate(gear_widgets):
                    print(f"[GEAR UPDATE] 更新第 {i+1} 個檔位分析圖表")
                    
                    # 檢查是否有數據載入器
                    if hasattr(widget, 'gear_loader'):
                        print(f"[GEAR UPDATE] 找到數據載入器，觸發重新載入")
                        
                        # 獲取當前參數
                        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
                        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
                        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
                        
                        # 獲取當前選擇的車手和圈數（而不是硬編碼）
                        driver1 = self.driver1_combo.currentText()
                        # 🔧 修復：使用 currentData() 判斷是否為 "無" 選項（支援多語言）
                        driver2_data = self.driver2_combo.currentData()
                        driver2 = self.driver2_combo.currentText() if driver2_data is not None else driver1
                        lap1 = self.lap1_spinbox.value()
                        lap2 = self.lap2_spinbox.value()
                        is_fastest = self.fastest_lap_checkbox.isChecked()
                        
                        print(f"[GEAR UPDATE] 🎯 使用實際選擇的參數: {driver1} vs {driver2}, 第{lap1}圈 vs 第{lap2}圈, 最速圈: {is_fastest}")
                        
                        # 重新載入數據（使用實際選擇的車手）
                        widget.gear_loader.load_gear_data(
                            year=int(year),
                            race=race,
                            session=session,
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1,
                            lap2=lap2,
                            is_fastest_lap=is_fastest
                        )
                        print(f"[GEAR UPDATE] ✅ 已觸發數據重新載入")
                    else:
                        print(f"[GEAR UPDATE] ⚠️ 未找到數據載入器")
                        
                        # 嘗試直接更新數據（使用JSON數據）
                        if json_data:
                            print(f"[GEAR UPDATE] 嘗試直接使用JSON數據更新")
                            widget.update_gear_data(json_data)
            else:
                print(f"[GEAR UPDATE] ⚠️ 未找到檔位分析圖表組件")
                
            print(f"[GEAR UPDATE] ========== 檔位分析圖表更新完成 ==========")
            
        except Exception as e:
            print(f"[ERROR] [GEAR UPDATE] 檔位分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()

    def _update_acceleration_analysis_chart(self, json_data):
        """更新加速度分析圖表的專用方法"""
        print(f"[ACCELERATION UPDATE] ========== 開始更新加速度分析圖表 ==========")
        
        try:
            # 尋找加速度分析圖表組件
            from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget import accelerationAnalysisChartWidget
            
            def find_acceleration_widgets(widget):
                """遞歸查找 accelerationAnalysisChartWidget"""
                widgets = []
                if isinstance(widget, accelerationAnalysisChartWidget):
                    widgets.append(widget)
                
                # 遞歸檢查子組件
                if hasattr(widget, 'findChildren'):
                    for child in widget.findChildren(accelerationAnalysisChartWidget):
                        widgets.append(child)
                elif hasattr(widget, 'children'):
                    for child in widget.children():
                        widgets.extend(find_acceleration_widgets(child))
                        
                return widgets
            
            acceleration_widgets = find_acceleration_widgets(self)
            print(f"[ACCELERATION UPDATE] 找到 {len(acceleration_widgets)} 個加速度分析圖表組件")
            
            if acceleration_widgets:
                for i, widget in enumerate(acceleration_widgets):
                    print(f"[ACCELERATION UPDATE] 更新第 {i+1} 個加速度分析圖表")
                    
                    # 檢查是否有數據載入器
                    if hasattr(widget, 'acceleration_loader'):
                        print(f"[ACCELERATION UPDATE] 找到數據載入器，觸發重新載入")
                        
                        # 獲取當前參數
                        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
                        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
                        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
                        
                        # 獲取當前選擇的車手和圈數
                        driver1 = getattr(self, 'local_driver1', None) or self.get_current_driver1_from_main_window()
                        driver2 = getattr(self, 'local_driver2', None) or self.get_current_driver2_from_main_window()
                        lap1 = getattr(self, 'local_lap1', None) or self.get_current_lap1_from_main_window()
                        lap2 = getattr(self, 'local_lap2', None) or self.get_current_lap2_from_main_window()
                        is_fastest = getattr(self, 'local_is_fastest', False) or self.get_current_fastest_from_main_window()
                        
                        print(f"[ACCELERATION UPDATE] 使用參數: {year} {race} {session}")
                        print(f"[ACCELERATION UPDATE] 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}, 最速圈: {is_fastest}")
                        
                        # 觸發數據重新載入
                        widget.acceleration_loader.load_acceleration_data(
                            year=int(year),
                            race=race,
                            session=session,
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1,
                            lap2=lap2,
                            is_fastest_lap=is_fastest
                        )
                        print(f"[ACCELERATION UPDATE] ✅ 已觸發數據重新載入")
                    else:
                        print(f"[ACCELERATION UPDATE] ⚠️ 未找到數據載入器")
                        
                        # 嘗試直接更新數據（使用JSON數據）
                        if json_data:
                            print(f"[ACCELERATION UPDATE] 嘗試直接使用JSON數據更新")
                            widget.update_acceleration_data(json_data)
            else:
                print(f"[ACCELERATION UPDATE] ⚠️ 未找到加速度分析圖表組件")
                
            print(f"[ACCELERATION UPDATE] ========== 加速度分析圖表更新完成 ==========")
            
        except Exception as e:
            print(f"[ERROR] [ACCELERATION UPDATE] 加速度分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()

    def update_telemetry_chart(self, telemetry_data):
        """更新遙測圖表"""
        print(f"[CHART] 更新遙測圖表資料")
        # 實現具體的遙測圖表更新邏輯
        pass
    
    def update_track_map(self, track_data):
        """更新軌道地圖"""
        print(f"🗺️ 更新軌道地圖資料")
        # 實現具體的軌道地圖更新邏輯
        pass
    
    def update_analysis_data(self, analysis_data):
        """更新分析數據"""
        print(f"[STATS] 更新分析數據")
        # 實現具體的分析數據更新邏輯
        pass
        
    def get_analysis_parameters(self):
        """獲取當前分析參數"""
        if hasattr(self, 'year_combo'):
            return {
                'year': self.year_combo.currentText(),
                'race': self.race_combo.currentText(),
                'session': self.session_combo.currentText(),
                'sync_windows': self.sync_windows_checkbox.isChecked()
            }
        return None
        
    def set_analysis_parameters(self, params, skip_sync=False):
        """設置分析參數，支援跳過同步"""
        if hasattr(self, 'year_combo') and params:
            # 暫時斷開信號連接避免循環同步
            self.year_combo.blockSignals(True)
            self.race_combo.blockSignals(True)
            self.session_combo.blockSignals(True)
            
            # 更新參數
            self.year_combo.setCurrentText(params.get('year', '2025'))
            self.race_combo.setCurrentText(params.get('race', 'Japan'))
            self.session_combo.setCurrentText(params.get('session', 'R'))
            
            # 恢復信號連接
            self.year_combo.blockSignals(False)
            self.race_combo.blockSignals(False)
            self.session_combo.blockSignals(False)
            
            # 更新資料（如果不是跳過同步）
            if not skip_sync:
                self.update_current_window()
            
            # 注意：不同步連動和遙測設定，保持各視窗獨立
        
    def toggle_maximize(self):
        """切換最大化狀態"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def custom_minimize(self):
        """自定義最小化：隱藏內容，只保留標題欄，移動到底部"""
        if hasattr(self, 'is_minimized') and self.is_minimized:
            # 如果已經最小化，則恢復
            self.restore_from_minimize()
        else:
            # 執行最小化
            self.minimize_to_bottom()
    
    def minimize_to_bottom(self):
        """最小化到底部，只顯示標題欄"""
        #print(f"🔽 最小化視窗 '{self.windowTitle()}' 到底部")
        
        # 保存當前狀態
        if self.original_geometry is None:
            self.original_geometry = self.geometry()
        
        # 隱藏內容區域
        if self.content_widget:
            self.content_widget.hide()
            #print(f"[PACKAGE] 隱藏內容區域")
        
        # 設置最小化狀態
        self.is_minimized = True
        
        # 調整視窗大小為只有標題欄高度
        title_height = 25  # 標題欄高度
        current_width = self.width()
        
        # 獲取MDI區域大小
        if self.parent():
            mdi_area = self.parent()
            mdi_height = mdi_area.height()
            mdi_width = mdi_area.width()
            
            # 移動到底部
            bottom_y = mdi_height - title_height - 5
            new_x = max(0, min(self.x(), mdi_width - current_width))
            
            # 設置新的幾何形狀
            self.setGeometry(new_x, bottom_y, current_width, title_height)
            #print(f"[PIN] 移動到底部位置: ({new_x}, {bottom_y}, {current_width}, {title_height})")
        else:
            # 如果沒有父視窗，只調整高度
            self.resize(current_width, title_height)
            #print(f"📏 調整大小為: {current_width}x{title_height}")
    
    def restore_from_minimize(self):
        """從最小化狀態恢復"""
        #print(f"🔼 恢復視窗 '{self.windowTitle()}' 從最小化狀態")
        
        # 恢復幾何形狀
        if self.original_geometry is not None:
            self.setGeometry(self.original_geometry)
            #print(f"[PIN] 恢復到原始位置: {self.original_geometry}")
        else:
            #print(f"[WARNING] 無法恢復：原始幾何形狀未保存")
            pass
        
        # 顯示內容區域
        if self.content_widget:
            self.content_widget.show()
            #print(f"[PACKAGE] 顯示內容區域")
        
        # 清除最小化狀態
        self.is_minimized = False
        
    def toggle_popout(self):
        """切換彈出狀態"""
        if not self.is_popped_out:
            self.pop_out()
        else:
            self.pop_back_in()
            
    def pop_out(self):
        """彈出為獨立視窗"""
        if self.parent_mdi and not self.is_popped_out and self.content_widget:
            # 保存原始widget
            self.original_widget = self.content_widget
            
            # 創建可調整大小的獨立視窗
            self.standalone_window = ResizableStandaloneWindow()
            self.standalone_window.setWindowTitle(f"[Standalone] {self.windowTitle()}")
            self.standalone_window.setObjectName("StandaloneWindow")
            self.standalone_window.setCentralWidget(self.original_widget)
            self.standalone_window.resize(800, 600)  # 調整預設大小更大
            
            # 設置視窗最小大小
            # self.standalone_window.setMinimumSize(400, 300) - 尺寸限制已移除
            
            # 添加返回按鈕
            toolbar = self.standalone_window.addToolBar("控制")
            toolbar.setObjectName("StandaloneToolbar")
            return_action = toolbar.addAction("⌂ 返回主畫面")
            return_action.triggered.connect(self.pop_back_in)
            
            self.standalone_window.show()
            
            # 在MDI中隱藏
            self.hide()
            self.is_popped_out = True
            self.title_bar.popout_btn.setText("⌂")
            self.title_bar.popout_btn.setToolTip("返回主畫面")
            
    def pop_back_in(self):
        """返回主畫面"""
        if self.is_popped_out and self.content_widget:
            # 重新包裝widget
            wrapper = QWidget()
            wrapper.setObjectName("SubWindowWrapper")
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.setSpacing(0)
            
            # 重新創建可拖拽標題欄
            self.title_bar = DraggableTitleBar(self, self.windowTitle())
            wrapper_layout.addWidget(self.title_bar)
            wrapper_layout.addWidget(self.content_widget)
            
            # 恢復到MDI
            super().setWidget(wrapper)
            
            if hasattr(self, 'standalone_window'):
                self.standalone_window.close()
                delattr(self, 'standalone_window')
            
            # 在MDI中顯示
            self.show()
            self.is_popped_out = False
            self.title_bar.popout_btn.setText("⧉")
            self.title_bar.popout_btn.setToolTip("彈出為獨立視窗")
            
    def resizeEvent(self, event):
        """處理視窗大小調整事件 - 簡化版本，避免重複處理"""
        super().resizeEvent(event)
        
        # 只處理內容組件的基本更新，避免多重縮放處理
        if hasattr(self, 'content_widget') and self.content_widget:
            try:
                # 簡化處理：只調用基本的update，讓Qt的佈局系統自動處理
                self.content_widget.update()
                #print(f"[RESIZE] 子視窗內容已更新: {event.size().width()}x{event.size().height()}")
            except Exception as e:
                #print(f"[RESIZE_ERROR] 內容更新失敗: {e}")
                pass


        # 發射resize信號
        self.resized.emit()
            
    def show_settings_dialog(self):
        """顯示設定對話框"""
        dialog = WindowSettingsDialog(self)
        dialog.exec_()

    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數變更通知"""
        window_title = self.windowTitle()
        print(f"[ANNOUNCE] [NOTIFICATION] {window_title} 收到主視窗更新通知: {param_type}={value}")
        
        # 檢查同步狀態 - 支援多種同步狀態檢查方式
        sync_enabled = False
        
        # 方法1: 檢查 sync_windows_checkbox (用於有控制面板的子視窗)
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox:
            sync_enabled = self.sync_windows_checkbox.isChecked()
            print(f"[SEARCH] [NOTIFICATION] {window_title} 使用 checkbox 檢查同步狀態: {sync_enabled}")
        
        # 方法2: 檢查 sync_enabled 屬性 (用於 PopoutSubWindow 等)
        elif hasattr(self, 'sync_enabled'):
            sync_enabled = self.sync_enabled
            print(f"[SEARCH] [NOTIFICATION] {window_title} 使用屬性檢查同步狀態: {sync_enabled}")
        
        # 如果未啟用同步，直接返回
        if not sync_enabled:
            print(f"🔴 [NOTIFICATION] {window_title} 同步已停用，忽略更新通知")
            return
        
        print(f"[GREEN] [NOTIFICATION] {window_title} 同步已啟用，處理參數更新")
        
        # [TOOL] 更新本地參數（同步模式）
        if param_type == 'year':
            self.local_year = value
        elif param_type == 'race':
            self.local_race = value
        elif param_type == 'session':
            self.local_session = value
        
        # [TOOL] 立即更新標題
        self.update_window_title()
        
        # 使用統一的方法更新視窗內容
        try:
            success = self.update_current_window()
            if success:
                print(f"[OK] [NOTIFICATION] {window_title} 內容更新成功")
            else:
                print(f"[WARNING] [NOTIFICATION] {window_title} 內容更新完成但可能有問題")
        except Exception as e:
            print(f"[ERROR] [NOTIFICATION] {window_title} 內容更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def get_current_year_from_main_window(self):
        """從主視窗獲取當前年份 - 安全版本"""
        try:
            # 優先使用本地參數
            if hasattr(self, 'local_year') and self.local_year:
                return self.local_year
                
            # 如果有main_window引用
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'get_selected_year'):
                    return str(self.main_window.get_selected_year())
                if hasattr(self.main_window, 'year_combo') and self.main_window.year_combo:
                    return self.main_window.year_combo.currentText()
            
            # [TOOL] 移除不安全的parent遍歷邏輯，避免AttributeError
                    
        except Exception as e:
            print(f"[WARNING] [GET_YEAR] 獲取主視窗年份失敗: {e}")
        return "2025"  # 預設值
    
    def get_current_race_from_main_window(self):
        """從主視窗獲取當前賽事 - 安全版本"""
        try:
            # 優先使用本地參數
            if hasattr(self, 'local_race') and self.local_race:
                return self.local_race
                
            # 如果有main_window引用
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'get_selected_race_key'):
                    return self.main_window.get_selected_race_key()
                if hasattr(self.main_window, 'race_combo') and self.main_window.race_combo:
                    return self.main_window.race_combo.currentText()
            
            # [TOOL] 移除不安全的parent遍歷邏輯，避免AttributeError
                    
        except Exception as e:
            print(f"[WARNING] [GET_RACE] 獲取主視窗賽事失敗: {e}")
        return "Japan"  # 預設值
    
    def get_current_session_from_main_window(self):
        """從主視窗獲取當前賽段 - 安全版本"""
        try:
            # 優先使用本地參數
            if hasattr(self, 'local_session') and self.local_session:
                return self.local_session
                
            # 如果有main_window引用
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'get_selected_session_code'):
                    return self.main_window.get_selected_session_code()
                if hasattr(self.main_window, 'session_combo') and self.main_window.session_combo:
                    return self.main_window.session_combo.currentText()
            
            # [TOOL] 移除不安全的parent遍歷邏輯，避免AttributeError
                    
        except Exception as e:
            print(f"[WARNING] [GET_SESSION] 獲取主視窗賽段失敗: {e}")
        return "R"  # 預設值
    
    def closeEvent(self, event):
        """子視窗關閉事件處理"""
        try:
            window_title = self.windowTitle()
            
            # 發出關閉信號
            self.window_closed.emit()
            
            # 停止任何正在執行的 CLI 分析
            if hasattr(self, 'stop_cli_analysis'):
                self.stop_cli_analysis()
            
            # 如果內容widget有 CLI 分析功能，也要停止
            if self.content_widget and hasattr(self.content_widget, 'stop_cli_analysis'):
                self.content_widget.stop_cli_analysis()
            
            # 接受關閉事件，讓 PyQt 自動處理移除
            event.accept()
            
        except Exception as e:
            event.accept()  # 即使出錯也要關閉

class ContextMenuTreeWidget(QTreeWidget):
    """支援右鍵選單和多選功能的功能樹"""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        
        # 啟用多選功能
        self.setSelectionMode(QTreeWidget.ExtendedSelection)  # 支援 Ctrl 和 Shift 多選
        
        # 設置右鍵選單
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # 連接項目點擊事件
        self.itemClicked.connect(self.on_item_clicked)
        
    def on_item_clicked(self, item, column):
        """處理項目點擊事件 - 僅用於選擇，不觸發分析"""
        # 檢查是否為葉節點（可分析的項目）
        if item.childCount() == 0:
            # 檢查是否為多選狀態
            selected_items = self.selectedItems()
            
            if len(selected_items) > 1:
                # 多選模式：顯示選中的項目數量
                print(f"[MULTI_SELECT] 已選擇 {len(selected_items)} 個分析模組")
                for selected_item in selected_items:
                    if selected_item.childCount() == 0:  # 確保是葉節點
                        print(f"  - {selected_item.text(0)}")
                print(f"[MULTI_SELECT] 💡 提示：右鍵點擊可執行批量分析")
            else:
                # 單選模式：僅顯示選中項目，不直接執行分析
                print(f"[SINGLE_SELECT] 已選擇分析模組: {item.text(0)}")
                print(f"[SINGLE_SELECT] 💡 提示：右鍵點擊可執行分析")
    
    def show_context_menu(self, position):
        """顯示右鍵選單"""
        item = self.itemAt(position)
        if item is None:
            return
        
        selected_items = self.selectedItems()
        
        # 過濾出葉節點（可分析的項目）- 排除父項目和禁用項目
        analyzable_items = [
            item for item in selected_items 
            if item.childCount() == 0 and (item.flags() & Qt.ItemIsEnabled)
        ]
        
        # 檢查是否有頂層項目（父項目）
        has_parent_items = any(item.childCount() > 0 for item in selected_items)
        
        menu = QMenu(self)
        menu.setObjectName("ContextMenu")
        
        if len(analyzable_items) == 1:
            # 單選選單（葉節點）
            analyze_action = menu.addAction(f"{tr('execute_analysis', '執行分析')} - {analyzable_items[0].text(0).strip()}")
            analyze_action.triggered.connect(lambda: self.analyze_function(analyzable_items[0].text(0)))
            
            menu.addSeparator()
            
            # 全展開樹狀圖
            expand_action = menu.addAction(tr('expand_all_tree', '全展開樹狀圖'))
            expand_action.triggered.connect(self.expandAll)
            
            # 全關閉樹狀圖
            collapse_action = menu.addAction(tr('collapse_all_tree', '全關閉樹狀圖'))
            collapse_action.triggered.connect(self.collapseAll)
            
            menu.addSeparator()
            
            help_action = menu.addAction(f"{tr('help', '說明')} - {analyzable_items[0].text(0).strip()}")
            help_action.triggered.connect(lambda: self.show_help(analyzable_items[0].text(0)))
            
        elif len(analyzable_items) > 1:
            # 多選選單（多個葉節點）
            analyze_action = menu.addAction(f"{tr('batch_execute_analysis', '批量執行分析')} ({len(analyzable_items)} {tr('modules', '個模組')})")
            analyze_action.triggered.connect(lambda: self.analyze_multiple_functions(analyzable_items))
            
            menu.addSeparator()
            
            # 全展開樹狀圖
            expand_action = menu.addAction(tr('expand_all_tree', '全展開樹狀圖'))
            expand_action.triggered.connect(self.expandAll)
            
            # 全關閉樹狀圖
            collapse_action = menu.addAction(tr('collapse_all_tree', '全關閉樹狀圖'))
            collapse_action.triggered.connect(self.collapseAll)
            
            menu.addSeparator()
            
            # 顯示選中的項目列表
            selected_submenu = menu.addMenu(f"{tr('selected_modules', '已選擇的模組')} ({len(analyzable_items)} {tr('items', '個')})")
            for item in analyzable_items:
                clean_name = item.text(0).strip()
                item_action = selected_submenu.addAction(f"{clean_name}")
                item_action.setEnabled(False)  # 僅用於顯示，不可點擊
        
        else:
            # 只選中了父項目或禁用項目
            # 顯示灰色的執行分析選項
            if len(selected_items) == 1:
                item_name = selected_items[0].text(0).strip()
                analyze_action = menu.addAction(f"{tr('execute_analysis', '執行分析')} - {item_name}")
                analyze_action.setEnabled(False)  # 設為灰色不可點擊
            else:
                analyze_action = menu.addAction(tr('select_specific_module', '請選擇具體的分析模組'))
                analyze_action.setEnabled(False)
            
            menu.addSeparator()
            
            # 全展開樹狀圖（可用）
            expand_action = menu.addAction(tr('expand_all_tree', '全展開樹狀圖'))
            expand_action.triggered.connect(self.expandAll)
            
            # 全關閉樹狀圖（可用）
            collapse_action = menu.addAction(tr('collapse_all_tree', '全關閉樹狀圖'))
            collapse_action.triggered.connect(self.collapseAll)
            
            menu.addSeparator()
            
            # 說明（灰色）
            if len(selected_items) == 1:
                help_action = menu.addAction(f"{tr('help', '說明')} - {selected_items[0].text(0).strip()}")
                help_action.setEnabled(False)
        
        menu.exec_(self.mapToGlobal(position))
    
    def analyze_multiple_functions(self, items):
        """批量分析多個功能（智能過濾父項目）"""
        # 二次過濾：確保只處理葉節點（沒有子項目的項目）
        leaf_items = [item for item in items if item.childCount() == 0]
        
        if not leaf_items:
            print(f"[BATCH_ANALYSIS] 沒有可執行的葉節點")
            return
        
        # 計算被過濾掉的父項目數量
        filtered_count = len(items) - len(leaf_items)
        if filtered_count > 0:
            print(f"[BATCH_ANALYSIS] 已過濾掉 {filtered_count} 個父項目")
        
        print(f"[BATCH_ANALYSIS] 開始批量分析 {len(leaf_items)} 個模組")
        
        for item in leaf_items:
            function_name = item.text(0).strip()
            print(f"[BATCH_ANALYSIS] 正在創建: {function_name}")
            # 傳遞 batch_mode=True 防止彈出對話框
            self.analyze_function(function_name, batch_mode=True)
            
        print(f"[BATCH_ANALYSIS] 批量分析完成，共創建了 {len(leaf_items)} 個分析視窗")
    
    def export_multiple_functions(self, items):
        """批量匯出多個功能的數據"""
        # 只處理葉節點
        leaf_items = [item for item in items if item.childCount() == 0]
        
        print(f"[BATCH_EXPORT] 開始批量匯出 {len(leaf_items)} 個模組的數據")
        
        for item in leaf_items:
            function_name = item.text(0).strip()
            print(f"[BATCH_EXPORT] 正在匯出: {function_name}")
            self.export_function(function_name)
            
        print(f"[BATCH_EXPORT] 批量匯出完成")
    
    def analyze_function(self, function_name, batch_mode=False):
        """分析單個功能（支援批量模式）
        
        ⚠️ 父項目政策 (2025-10-03):
        - 父項目是路標（導航元素），不應觸發任何分析模組
        - 只有葉節點（子項目）才會開啟實際的分析視窗
        - 批量操作已通過 childCount() == 0 過濾掉父項目
        """
        if not self.main_window:
            return
        
        # 清理項目名稱（移除前綴和多餘空白）
        clean_name = function_name.strip()
        
        # 移除前綴標記: (L), (D), (T)
        for prefix in ["(L) ", "(D) ", "(T) "]:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):]
                break
        
        print(f"[TREE_CLICK] 項目: {clean_name} (原始: {function_name}), 批量模式: {batch_mode}")
        
        # ========== 父項目禁用政策 ==========
        # 父項目清單（這些項目只作為導航，不觸發任何操作）
        parent_items = [
            "Lap Analysis", "Lap Analysis (Telemetry)", "圈速分析", "圈速分析（遙測）",
            "Detailed Lap Analysis", "詳細圈速分析",
            "Throttle Analysis", "油門分析",
            "Ideal Lap Analysis", "理想圈分析"
        ]
        
        if not batch_mode and clean_name in parent_items:
            print(f"[TREE_CLICK] ⚠️ 父項目 '{clean_name}' 不執行任何操作（僅作為路標）")
            return
        
        # ========== 子項目處理（直接開啟對應模組）==========
        params = self.main_window.get_current_parameters()
        
        # Lap Analysis 子模組 - 使用預設車手
        if clean_name in ["Speed Analysis", "速度分析"]:
            self.main_window.create_telemetry_window(
                "speed_analysis", params, 
                driver1="VER", driver2="LEC", lap1_number=1, lap2_number=1
            )
        
        elif clean_name in ["Brake Analysis", "煞車分析"]:
            self.main_window.create_telemetry_window(
                "brake", params,
                driver1="VER", driver2="LEC", lap1_number=1, lap2_number=1
            )
        
        elif clean_name in ["Gear Analysis", "檔位分析"]:
            self.main_window.create_telemetry_window(
                "gear", params,
                driver1="VER", driver2="LEC", lap1_number=1, lap2_number=1
            )
        
        elif clean_name in ["RPM Analysis", "轉速分析"]:
            self.main_window.create_telemetry_window(
                "rpm", params,
                driver1="VER", driver2="LEC", lap1_number=1, lap2_number=1
            )
        
        elif clean_name in ["Acceleration Analysis", "加速度分析"]:
            self.main_window.create_telemetry_window(
                "acceleration", params,
                driver1="VER", driver2="LEC", lap1_number=1, lap2_number=1
            )
        
        elif clean_name in ["Speed Diff Analysis", "速度差分析"]:
            self.main_window.create_telemetry_window(
                "speed_diff", params,
                driver1="VER", driver2="LEC", lap1_number=1, lap2_number=1
            )
        
        elif clean_name in ["Distance Diff Analysis", "距離差分析"]:
            self.main_window.create_telemetry_window(
                "distancediff", params,
                driver1="VER", driver2="LEC", lap1_number=1, lap2_number=1
            )
        
        elif clean_name in ["Throttle Analysis", "油門分析"]:
            # Lap Analysis 下的 Throttle Analysis 子模組（不是父項目）
            print(f"[TREE_CLICK] 開啟油門遙測分析（Lap Analysis 子模組）")
            self.main_window.create_telemetry_window(
                "throttle", params,
                driver1="VER", driver2="LEC", lap1_number=1, lap2_number=1
            )
        
        # Detailed Lap Analysis 子模組
        elif clean_name in ["Detailed Lap Table", "詳細圈速表格"]:
            print(f"[TREE_CLICK] 開啟詳細圈速表格（模組工廠模式）")
            # ✅ 使用統一的 create_analysis_window 入口（支援模組工廠）
            self.main_window.create_analysis_window(clean_name)
        
        elif clean_name in ["Lap Time Box Plot", "圈速箱線圖", "圈速箱型圖"]:
            print(f"[TREE_CLICK] 開啟圈速箱線圖（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # Throttle Analysis 子模組（父項目的子視圖）
        elif clean_name in ["Throttle Box Plot", "油門箱線圖", "油門箱型圖"]:
            print(f"[TREE_CLICK] 開啟油門箱線圖（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        elif clean_name in ["Throttle Line Chart", "油門折線圖"]:
            print(f"[TREE_CLICK] 開啟油門折線圖（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # Ideal Lap Analysis 子模組
        elif clean_name in ["Ranking Table", "排名表格", "理想圈排名"]:
            print(f"[TREE_CLICK] 開啟理想圈排名表格（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # Track Analysis 特殊處理
        elif clean_name in ["Track Analysis", "賽道分析"]:
            print(f"[TRACK] 檢測到賽道分析請求，使用專門的開啟方法")
            self.main_window.open_track_analysis_window()
        
        else:
            # 未知模組，使用原有邏輯
            print(f"[TREE_CLICK] 使用原有邏輯處理: {clean_name}")
            self.main_window.create_analysis_window(function_name)
        
    def export_function(self, function_name):
        """匯出單個功能的數據"""
        #print(f"[匯出] 匯出功能數據: {function_name}")
        pass
        
    def show_help(self, function_name):
        """顯示功能說明"""
        #print(f"[說明] 顯示功能說明: {function_name}")
        pass

class ResizableStandaloneWindow(QMainWindow):
    """可調整大小的獨立視窗"""
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.resize_margin = 10  # 調整邊框的寬度
        self.resizing = False
        self.resize_direction = None
        
        # 創建可視的調整邊框
        self.setStyleSheet("""
            QMainWindow {
                border: 2px solid #CCCCCC;
                background-color: #FFFFFF;
            }
            QMainWindow:hover {
                border: 2px solid #999999;
            }
        """)
        
    def mousePressEvent(self, event):
        """滑鼠按下事件"""
        if event.button() == Qt.LeftButton:
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        if self.resizing and self.resize_direction:
            self.perform_resize(event.globalPos())
            event.accept()
            return
            
        # 更新游標
        direction = self.get_resize_direction(event.pos())
        if direction:
            # 取消上方調整大小功能，移除 'top' 相關游標
            if direction in ['bottom']:  # 只保留 bottom，移除 top
                self.setCursor(Qt.SizeVerCursor)
            elif direction in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            elif direction in ['bottom-right']:  # 移除 top-left
                self.setCursor(Qt.SizeFDiagCursor)
            elif direction in ['bottom-left']:  # 移除 top-right
                self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件"""
        if event.button() == Qt.LeftButton:
            self.resizing = False
            self.resize_direction = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
        
    def get_resize_direction(self, pos):
        """判斷調整方向 (取消上方調整) - ResizableStandaloneWindow"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        margin = self.resize_margin
        
        # 角落區域 (優先判斷) - 取消上方相關的角落調整
        # if x <= margin and y <= margin:
        #     return 'top-left'
        # elif x >= w - margin and y <= margin:
        #     return 'top-right'
        if x <= margin and y >= h - margin:
            return 'bottom-left'
        elif x >= w - margin and y >= h - margin:
            return 'bottom-right'
        # 邊緣區域 - 取消上方調整，保留左、右、下
        # elif y <= margin:
        #     return 'top'
        elif y >= h - margin:
            return 'bottom'
        elif x <= margin:
            return 'left'
        elif x >= w - margin:
            return 'right'
        
        return None
        
    def perform_resize(self, global_pos):
        """執行調整大小"""
        if not self.resize_direction:
            return
            
        delta = global_pos - self.resize_start_pos
        old_geometry = self.resize_start_geometry
        
        new_x = old_geometry.x()
        new_y = old_geometry.y()
        new_width = old_geometry.width()
        new_height = old_geometry.height()
        
        # 根據方向調整
        if 'left' in self.resize_direction:
            new_x = old_geometry.x() + delta.x()
            new_width = old_geometry.width() - delta.x()
        elif 'right' in self.resize_direction:
            new_width = old_geometry.width() + delta.x()
            
        # 取消 top 調整，只保留 bottom (ResizableStandaloneWindow)
        # if 'top' in self.resize_direction:
        #     new_y = old_geometry.y() + delta.y()
        #     new_height = old_geometry.height() - delta.y()
        if 'bottom' in self.resize_direction:
            new_height = old_geometry.height() + delta.y()
            
        # 限制最小大小
        min_size = self.minimumSize()
        if new_width < min_size.width():
            if 'left' in self.resize_direction:
                new_x = old_geometry.x() + old_geometry.width() - min_size.width()
            new_width = min_size.width()
            
        if new_height < min_size.height():
            # 取消 top 調整功能 (ResizableStandaloneWindow)
            # if 'top' in self.resize_direction:
            #     new_y = old_geometry.y() + old_geometry.height() - min_size.height()
            new_height = min_size.height()
            
        # 應用新的幾何形狀
        self.setGeometry(new_x, new_y, new_width, new_height)
        
    def paintEvent(self, event):
        """繪製事件 - 添加可視邊框提示"""
        super().paintEvent(event)
        
        # 在視窗邊緣繪製調整提示
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 右下角調整提示
        corner_size = 15
        corner_color = QColor(100, 100, 100, 150)
        painter.fillRect(
            self.width() - corner_size, 
            self.height() - corner_size, 
            corner_size, 
            corner_size, 
            corner_color
        )
        
        # 繪製調整線條
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        for i in range(3):
            offset = 3 + i * 3
            painter.drawLine(
                self.width() - offset, self.height() - 3,
                self.width() - 3, self.height() - offset
            )

class WindowSettingsDialog(QDialog):
    """視窗設定對話框"""
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.main_window = parent_window.main_window if hasattr(parent_window, 'main_window') else parent_window
        self._season_event_lookup: Dict[str, SeasonEvent] = {}
        self._display_to_race_key: Dict[str, str] = {}
        self.setWindowTitle("Window Settings")
        self.setObjectName("SettingsDialog")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # 設置對話框佈局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 標題
        title_label = QLabel("[TOOL] 視窗分析設定")
        title_label.setObjectName("DialogTitle")
        layout.addWidget(title_label)
        
        # 連動控制區域
        sync_group = QGroupBox("視窗同步控制")
        sync_group.setObjectName("SettingsGroup")
        sync_layout = QVBoxLayout(sync_group)
        
        # 連動控制勾選框
        self.sync_windows_checkbox = QCheckBox(tr("sync_checkbox_main", "[LINK] Receive Main Window Sync (Year/Race/Session)"))
        self.sync_windows_checkbox.setObjectName("SyncWindowsCheckbox")
        # [TOOL] 修復: 從父視窗獲取當前同步狀態
        current_sync_state = getattr(parent_window, 'sync_enabled', True)
        self.sync_windows_checkbox.setChecked(current_sync_state)
        self.sync_windows_checkbox.setToolTip(tr("sync_checkbox_tooltip_main", "When checked, receive parameters from main window and lock analysis controls"))
        # [TOOL] 新增: 當同步狀態改變時，切換分析參數的可編輯性
        self.sync_windows_checkbox.toggled.connect(self.on_sync_checkbox_toggled)
        sync_layout.addWidget(self.sync_windows_checkbox)
        
        layout.addWidget(sync_group)
        
        # 分析參數區域
        params_group = QGroupBox("分析參數")
        params_group.setObjectName("SettingsGroup")
        params_layout = QGridLayout(params_group)
        
        # 年份選擇器
        params_layout.addWidget(QLabel("年份:"), 0, 0)
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("AnalysisComboBox")
        self.year_combo.addItems([str(year) for year in range(2020, 2026)])
        # [TOOL] 修復: 優先從子視窗本地參數獲取，其次從主視窗獲取
        if hasattr(parent_window, 'local_year') and parent_window.local_year:
            current_year = parent_window.local_year
        else:
            current_year = self.get_current_year_from_main_window()
        self.year_combo.setCurrentText(current_year)
        # [TOOL] 新增: 年份變更時動態更新賽事列表
        self.year_combo.currentTextChanged.connect(self.on_year_changed_in_dialog)
        params_layout.addWidget(self.year_combo, 0, 1)
        
        # 賽事選擇器
        params_layout.addWidget(QLabel("賽事:"), 1, 0)
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("AnalysisComboBox")
        # [TOOL] 修復: 使用動態賽事列表而非硬編碼
        self.populate_races_for_year(current_year)
        # [TOOL] 修復: 優先從子視窗本地參數獲取，其次從主視窗獲取
        if hasattr(parent_window, 'local_race') and parent_window.local_race:
            current_race = parent_window.local_race
        else:
            current_race = self.get_current_race_from_main_window()
        self._select_race_by_key(current_race)
        self.race_combo.currentIndexChanged.connect(self._on_race_combo_changed)
        params_layout.addWidget(self.race_combo, 1, 1)
        
        # 賽段選擇器
        params_layout.addWidget(QLabel("賽段:"), 2, 0)
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("AnalysisComboBox")
        # [TOOL] 修復: 優先從子視窗本地參數獲取，其次從主視窗獲取
        if hasattr(parent_window, 'local_session') and parent_window.local_session:
            current_session = parent_window.local_session
        else:
            current_session = self.get_current_session_from_main_window()
        self._update_session_combo(preserve_session_code=current_session)
        params_layout.addWidget(self.session_combo, 2, 1)
        
        layout.addWidget(params_group)
        
        # [TOOL] 新增: 根據同步狀態設置分析參數的可編輯性
        self.update_analysis_params_editability()
        
        layout.addStretch()
        
        # 對話框按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setObjectName("DialogButtonBox")
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_sync_checkbox_toggled(self, checked):
        """處理同步勾選框狀態變化"""
        print(f"[LINK] [SETTING] 同步接收狀態變更為: {'啟用' if checked else '停用'}")
        self.update_analysis_params_editability()
        
        # [TOOL] 移除錯誤的同步調用 - 不需要從主程式同步，保持當前設定
        # if checked:
        #     self.sync_params_from_main_window()  # 這個調用會產生錯誤
    
    def update_analysis_params_editability(self):
        """根據同步狀態更新分析參數的可編輯性"""
        is_sync_enabled = self.sync_windows_checkbox.isChecked()
        
        # 設置分析參數控件的可編輯性（同步時不可編輯）
        self.year_combo.setEnabled(not is_sync_enabled)
        self.race_combo.setEnabled(not is_sync_enabled)
        self.session_combo.setEnabled(not is_sync_enabled)
        
        # 更新提示文字
        if is_sync_enabled:
            self.year_combo.setToolTip("已啟用同步接收，參數由主程式控制")
            self.race_combo.setToolTip("已啟用同步接收，參數由主程式控制")
            self.session_combo.setToolTip("已啟用同步接收，參數由主程式控制")
            print(f"[LOCK] [SETTING] 分析參數已鎖定 - 接收主程式同步")
        else:
            self.year_combo.setToolTip(tr("year_tooltip", "Set year manually"))
            self.race_combo.setToolTip(tr("race_tooltip", "Set race manually"))
            self.session_combo.setToolTip(tr("session_tooltip", "Set session manually"))
            print(f"🔓 [SETTING] 分析參數已解鎖 - 可手動編輯")
    
    def sync_params_from_main_window(self):
        """從主程式同步參數到設定對話框"""
        try:
            current_year = self.get_current_year_from_main_window()
            current_race = self.get_current_race_from_main_window()
            current_session = self.get_current_session_from_main_window()
            
            print(f"📥 [SETTING] 從主程式同步參數: {current_year} {current_race} {current_session}")
            
            # 更新對話框中的參數
            self.year_combo.blockSignals(True)
            self.race_combo.blockSignals(True)
            self.session_combo.blockSignals(True)
            
            self.year_combo.setCurrentText(current_year)
            # 需要先更新賽事列表
            self.populate_races_for_year(current_year)
            self._select_race_by_key(current_race)
            self._update_session_combo(preserve_session_code=current_session)
            
            self.year_combo.blockSignals(False)
            self.race_combo.blockSignals(False)
            self.session_combo.blockSignals(False)
            
            print(f"[OK] [SETTING] 參數同步完成")
            
        except Exception as e:
            print(f"[ERROR] [SETTING] 從主程式同步參數失敗: {e}")
    
    def get_current_year_from_main_window(self):
        """從主視窗獲取當前年份"""
        try:
            # 如果父視窗有main_window屬性（子視窗情況）
            if hasattr(self.parent_window, 'main_window'):
                main_window = self.parent_window.main_window
                if hasattr(main_window, 'year_combo') and main_window.year_combo:
                    return main_window.year_combo.currentText()
            # [TOOL] 移除不安全的直接訪問，避免 AttributeError
            # elif hasattr(self.parent_window, 'year_combo') and self.parent_window.year_combo:
            #     return self.parent_window.year_combo.currentText()
        except Exception as e:
            print(f"[WARNING] [SETTING] 獲取年份失敗: {e}")
        return "2025"  # 預設值
    
    def get_current_race_from_main_window(self):
        """從主視窗獲取當前賽事"""
        try:
            # 如果父視窗有main_window屬性（子視窗情況）
            if hasattr(self.parent_window, 'main_window'):
                main_window = self.parent_window.main_window
                if hasattr(main_window, 'race_combo') and main_window.race_combo:
                    return main_window.race_combo.currentText()
            # [TOOL] 移除不安全的直接訪問，避免 AttributeError
            # elif hasattr(self.parent_window, 'race_combo') and self.parent_window.race_combo:
            #     return self.parent_window.race_combo.currentText()
        except Exception as e:
            print(f"[WARNING] [SETTING] 獲取賽事失敗: {e}")
        return "Japan"  # 預設值
    
    def get_current_session_from_main_window(self):
        """從主視窗獲取當前賽段"""
        try:
            # 如果父視窗有main_window屬性（子視窗情況）
            if hasattr(self.parent_window, 'main_window'):
                main_window = self.parent_window.main_window
                if hasattr(main_window, 'get_selected_session_code'):
                    return main_window.get_selected_session_code()
                if hasattr(main_window, 'session_combo') and main_window.session_combo:
                    return main_window.session_combo.currentText()
            # [TOOL] 移除不安全的直接訪問，避免 AttributeError
            # elif hasattr(self.parent_window, 'session_combo') and self.parent_window.session_combo:
            #     return self.parent_window.session_combo.currentText()
        except Exception as e:
            print(f"[WARNING] [SETTING] 獲取賽段失敗: {e}")
        return "R"  # 預設值

    # --- Season calendar helpers ---

    def _get_calendar_events_for_year(self, year: int) -> List[SeasonEvent]:
        if self.main_window and hasattr(self.main_window, "_get_calendar_events"):
            return self.main_window._get_calendar_events(year)
        if self.main_window and hasattr(self.main_window, "_season_provider"):
            try:
                return self.main_window._season_provider.get_completed_events(year)
            except SeasonCalendarError as exc:
                print(f"[DIALOG] 取得賽事日曆失敗: {exc}")
        return []

    def _format_race_display(self, event: SeasonEvent) -> str:
        if self.main_window and hasattr(self.main_window, "_format_race_display"):
            return self.main_window._format_race_display(event)
        if event.is_completed:
            return event.display_label
        suffix = tr("season_calendar_upcoming_suffix", "[未開賽]")
        if suffix and suffix in event.display_label:
            return event.display_label
        return f"{event.display_label} {suffix}" if suffix else event.display_label

    def _rebuild_race_mapping(self, events: List[SeasonEvent]) -> None:
        self._season_event_lookup.clear()
        self._display_to_race_key.clear()
        for event in events:
            self._season_event_lookup[event.race_key] = event
            formatted_label = self._format_race_display(event)
            candidate_labels = {event.display_label, formatted_label}
            for label in candidate_labels:
                self._display_to_race_key[label] = event.race_key
                if self.main_window:
                    plain = self.main_window._strip_race_display(label)
                else:
                    plain = label
                if plain and plain not in self._display_to_race_key:
                    self._display_to_race_key[plain] = event.race_key

    def _select_race_by_key(self, race_key: Optional[str]) -> None:
        if race_key is None or not self.race_combo:
            return
        for index in range(self.race_combo.count()):
            data = self.race_combo.itemData(index)
            if isinstance(data, SeasonEvent) and data.race_key == race_key:
                self.race_combo.setCurrentIndex(index)
                return

    def get_selected_event(self) -> Optional[SeasonEvent]:
        data = self.race_combo.currentData() if self.race_combo else None
        if isinstance(data, SeasonEvent):
            return data
        display_text = self.race_combo.currentText() if self.race_combo else ""
        race_key = self._display_to_race_key.get(display_text)
        if not race_key and self.main_window:
            race_key = self.main_window._strip_race_display(display_text)
            race_key = self._display_to_race_key.get(race_key, race_key)
        return self._season_event_lookup.get(race_key)

    def get_selected_race_key(self) -> str:
        event = self.get_selected_event()
        if event:
            return event.race_key
        display_text = self.race_combo.currentText() if self.race_combo else ""
        race_key = self._display_to_race_key.get(display_text)
        if not race_key and self.main_window:
            race_key = self.main_window._strip_race_display(display_text)
        return race_key or "Unknown"

    def get_selected_session_code(self) -> str:
        data = self.session_combo.currentData() if self.session_combo else None
        if data and hasattr(data, "code"):
            return getattr(data, "code")
        text = self.session_combo.currentText() if self.session_combo else ""
        return text or "R"

    def _update_session_combo(self, preserve_session_code: Optional[str] = None) -> None:
        if not self.session_combo:
            return

        event = self.get_selected_event()
        current_code = preserve_session_code or self.get_selected_session_code()
        self.session_combo.blockSignals(True)
        self.session_combo.clear()

        if isinstance(event, SeasonEvent) and event.sessions:
            codes = []
            for session in event.sessions:
                self.session_combo.addItem(session.code, session)
                codes.append(session.code)

            target_code = current_code or ("R" if "R" in codes else (codes[0] if codes else None))
            if target_code:
                index = self.session_combo.findText(target_code)
                if index < 0:
                    index = self.session_combo.findText(target_code.upper())
                if index >= 0:
                    self.session_combo.setCurrentIndex(index)
                elif self.session_combo.count() > 0:
                    self.session_combo.setCurrentIndex(0)
        else:
            for code in ["FP1", "FP2", "FP3", "SQ", "Q", "R"]:
                self.session_combo.addItem(code)
            if current_code:
                index = self.session_combo.findText(current_code)
                if index >= 0:
                    self.session_combo.setCurrentIndex(index)

        self.session_combo.blockSignals(False)

    def _on_race_combo_changed(self):
        self._update_session_combo()

    
    def get_races_for_year_in_dialog(self, year):
        """在設定對話框中根據年份獲取賽事列表（與主視窗保持一致）"""
        try:
            year_int = int(year)
            events = self._get_calendar_events_for_year(year_int)
            self._rebuild_race_mapping(events)
            print(f"[DIALOG] 載入 {year_int} 年的賽事列表: {len(events)} 個賽事")
            return events
        except Exception as e:
            print(f"[DIALOG ERROR] 獲取賽事列表時出錯: {e}")
            return []
    
    def populate_races_for_year(self, year):
        """為指定年份填充賽事列表"""
        events = self.get_races_for_year_in_dialog(year)
        self.race_combo.clear()
        if events:
            completed_events = [event for event in events if event.is_completed]
            upcoming_events = [event for event in events if not event.is_completed]

            def add_event(event: SeasonEvent) -> None:
                label = self._format_race_display(event)
                self._display_to_race_key[label] = event.race_key
                self.race_combo.addItem(label, event)

            for event in completed_events:
                add_event(event)

            if completed_events and upcoming_events:
                self.race_combo.insertSeparator(self.race_combo.count())

            for event in upcoming_events:
                add_event(event)

            if self.race_combo.currentIndex() < 0:
                preferred_event = completed_events[0] if completed_events else (upcoming_events[0] if upcoming_events else None)
                if preferred_event is not None:
                    index = self.race_combo.findData(preferred_event)
                    if index >= 0:
                        self.race_combo.setCurrentIndex(index)
            if self.race_combo.currentIndex() < 0 and self.race_combo.count() > 0:
                self.race_combo.setCurrentIndex(0)
        else:
            placeholder = tr("season_calendar_placeholder", "[無已完成賽事]")
            self.race_combo.addItem(placeholder, None)
        
    def on_year_changed_in_dialog(self, year):
        """處理設定對話框中的年份變更"""
        print(f"[DIALOG] 年份變更為: {year}")
        
        # 記住當前選擇的賽事
        current_event = self.get_selected_event()
        current_race_key = current_event.race_key if current_event else None
        
        # 更新賽事列表
        self.populate_races_for_year(year)
        
        if current_race_key:
            self._select_race_by_key(current_race_key)
        if self.race_combo.currentIndex() < 0 and self.race_combo.count() > 0:
            self.race_combo.setCurrentIndex(0)

        self._update_session_combo()
        
    def accept_settings(self):
        """確認設定"""
        window_title = self.parent_window.windowTitle()
        year = self.year_combo.currentText()
        race = self.get_selected_race_key()
        session = self.get_selected_session_code()
        sync_windows = self.sync_windows_checkbox.isChecked()
        
        print(f"[TOOL] [SETTING] [{window_title}] 設定已更新:")
        print(f"   參數: {year} {race} {session}")
        print(f"   同步接收狀態: {'啟用' if sync_windows else '停用'}")
        
        # 保存同步狀態到父視窗
        self.parent_window.sync_enabled = sync_windows
        
        # [TOOL] 修改邏輯：根據同步狀態決定行為
        if sync_windows:
            # 當啟用同步時，只接收不發送，確保與主程式一致
            print(f"[REFRESH] [SETTING] [{window_title}] 同步接收模式 - 僅更新當前視窗")
            self.update_current_window_only()
        else:
            # 當停用同步時，允許手動設定並應用到當前視窗
            print(f"[TOOL] [SETTING] [{window_title}] 手動設定模式 - 應用自定義參數")
            self.apply_manual_settings(year, race, session)
        
        self.accept()
        
    def update_current_window_only(self):
        """僅更新當前視窗（同步接收模式）"""
        window_title = self.parent_window.windowTitle()
        print(f"[REFRESH] [SETTING] [{window_title}] 更新視窗數據（同步模式）")
        
        try:
            # 如果當前視窗有update_current_window方法，調用它
            if hasattr(self.parent_window, 'update_current_window'):
                self.parent_window.update_current_window()
                print(f"[OK] [SETTING] 當前視窗數據更新完成（同步模式）")
        except Exception as e:
            print(f"[ERROR] [SETTING] 更新當前視窗失敗: {e}")
    
    def apply_manual_settings(self, year, race, session):
        """應用手動設定（獨立模式）"""
        window_title = self.parent_window.windowTitle()
        print(f"[TOOL] [SETTING] [{window_title}] 應用手動設定: {year} {race} {session}")
        
        try:
            # 更新當前視窗的內容（使用手動設定的參數）
            self.update_current_window_with_params(year, race, session)
            print(f"[OK] [SETTING] 手動設定應用完成")
        except Exception as e:
            print(f"[ERROR] [SETTING] 應用手動設定失敗: {e}")
    
    def update_current_window_with_params(self, year, race, session):
        """使用指定參數更新當前視窗"""
        window_title = self.parent_window.windowTitle()
        print(f"[REFRESH] [SETTING] [{window_title}] 使用參數更新視窗: {year} {race} {session}")
        
        try:
            # [TOOL] 新方法：直接更新子視窗的本地參數
            if hasattr(self.parent_window, 'update_local_parameters'):
                # 更新本地參數（這會自動更新標題）
                self.parent_window.update_local_parameters(year, race, session)
                
                # 調用視窗更新
                if hasattr(self.parent_window, 'update_current_window'):
                    self.parent_window.update_current_window()
                    
                print(f"[OK] [SETTING] 參數更新完成（新方法）: {year} {race} {session}")
                return
            
            # [TOOL] 舊方法向後兼容：直接調用更新
            print(f"[WARNING] [SETTING] 使用舊方法向後兼容模式")
            if hasattr(self.parent_window, 'update_current_window'):
                self.parent_window.update_current_window()
                print(f"[OK] [SETTING] 當前視窗數據更新完成（向後兼容模式）")
            else:
                print(f"[WARNING] [SETTING] 視窗沒有 update_current_window 方法")
                
        except Exception as e:
            print(f"[ERROR] [SETTING] 更新當前視窗失敗: {e}")
            print(f"[INFO] [SETTING] 錯誤詳情: {type(e).__name__}: {str(e)}")
    
    def apply_settings(self, year, race, session, sync_windows):
        """應用設定到父視窗（已棄用，由新方法取代）"""
        # [TOOL] 此方法已被 update_current_window_only 和 apply_manual_settings 取代
        print(f"[WARNING] [SETTING] apply_settings 方法已棄用")
        pass
        
    def sync_to_other_windows(self, year, race, session):
        """同步參數到其他視窗（已棄用，避免命令混亂）"""
        # [TOOL] 移除此功能，避免MDI子視窗向主程式發送控制命令
        print(f"[WARNING] [SETTING] sync_to_other_windows 方法已停用 - 避免多視窗命令混亂")
        print(f"[TEST] [SETTING] 子視窗應僅接收主程式同步，不應發送控制命令")
        pass
        
    def update_current_window(self, year, race, session):
        """更新當前視窗的分析數據（已棄用，由新方法取代）"""
        # [TOOL] 此方法已被 update_current_window_only 取代
        print(f"[WARNING] [SETTING] update_current_window 方法已棄用")
        pass


class ApiHealthWorker(QThread):
    """Background worker to probe API health endpoints without blocking the UI thread."""

    result_ready = pyqtSignal(dict)

    def __init__(self, base_url: str, timeout: float = 5.0, manual: bool = False, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.manual = manual

    def run(self):
        summary = {
            "state": "offline",
            "details": [],
            "errors": [],
            "latency_ms": None,
            "checked_at": datetime.datetime.now().isoformat(timespec='seconds'),
            "base_url": self.base_url,
            "manual": self.manual,
        }

        endpoints = [
            ("system", f"{self.base_url}/api/v2/system/health"),
            ("analysis", f"{self.base_url}/api/v2/analysis/status"),
        ]

        success_count = 0
        latencies = []
        degrade_flag = False

        for name, url in endpoints:
            try:
                start = time.perf_counter()
                response = requests.get(url, timeout=self.timeout)
                latency = (time.perf_counter() - start) * 1000.0
                latencies.append(latency)

                if response.status_code == 200:
                    success_count += 1
                    try:
                        payload = response.json()
                    except ValueError:
                        summary["errors"].append(f"{name}: invalid JSON payload from API")
                        degrade_flag = True
                        continue

                    message = payload.get('message') or payload.get('status') or 'OK'
                    summary["details"].append(f"{name}: {message}")
                    if not payload.get('success', True):
                        degrade_flag = True
                        summary["errors"].append(f"{name}: API reported success=False")
                else:
                    summary["errors"].append(f"{name}: HTTP {response.status_code}")
            except requests.exceptions.RequestException as exc:
                summary["errors"].append(f"{name}: {exc}")
            except Exception as exc:
                summary["errors"].append(f"{name}: {type(exc).__name__} - {exc}")

        if latencies:
            summary["latency_ms"] = round(sum(latencies) / len(latencies), 1)

        if success_count == len(endpoints) and not degrade_flag and not summary["errors"]:
            summary["state"] = "online"
        elif success_count > 0:
            summary["state"] = "degraded"
        else:
            summary["state"] = "offline"
            if not summary["errors"]:
                summary["errors"].append('API did not respond')

        if not summary["details"]:
            summary["details"].append('No API response received')

        self.result_ready.emit(summary)


class ApiRuntimeWorker(QThread):
    """Background worker that polls the analysis runtime endpoint."""

    result_ready = pyqtSignal(dict)

    def __init__(self, base_url: str, timeout: float = 5.0, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def run(self):
        endpoint = f"{self.base_url}/api/v2/analysis/status"
        summary = {
            "ok": False,
            "payload": None,
            "error": None,
            "endpoint": endpoint,
        }

        try:
            response = requests.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            summary["payload"] = payload
            summary["ok"] = True
        except requests.exceptions.RequestException as exc:
            summary["error"] = str(exc)
        except ValueError as exc:
            summary["error"] = f"JSON decode error: {exc}"
        except Exception as exc:  # pragma: no cover - defensive
            summary["error"] = f"{type(exc).__name__}: {exc}"

        self.result_ready.emit(summary)

class StyleHMainWindow(QMainWindow):
    """風格H: 專業賽車分析工作站主視窗"""
    
    def __init__(self):
        super().__init__()
        print("[INIT] 🚀 開始初始化 F1 TelemetryStation Pro 主視窗...")
        # API health monitor attributes
        self.ready_label = None
        self.api_status_label = None
        self.time_label = None
        self.api_health_timer = None
        self._api_health_worker = None
        self._api_health_worker_active = False
        self._api_last_state = "unknown"
        self._api_status_details = []
        self._api_health_manual_request = False
        self.api_mode_enabled = False
        self.api_base_url = None
        self.check_api_action = None
        self.cli_status_label = None
        self.api_runtime_timer = None
        self._api_runtime_worker = None
        self._api_runtime_worker_active = False
        self._runtime_status_resolver = RuntimeStatusResolver()
        self._last_cli_status_signature = None

        
        # GUI 語言會自動從設定檔載入，不需要強制設定
        # set_gui_language('en')  # 已移除強制設定
        
        self.setWindowTitle("F1 TelemetryStation Pro V0.2.1")
        print("[INIT] ✅ 視窗標題已設定")
        # self.setMinimumSize(1600, 900) - 主視窗尺寸限制已移除
        
        # 初始化分析追蹤屬性
        self.active_analysis_tabs = []
        print("[INIT] ✅ 分析追蹤屬性已初始化")
        
        # 初始化子視窗追蹤列表
        self.active_subwindows = []
        print("[INIT] ✅ 子視窗追蹤列表已初始化")
        
        # 初始化MDI區域引用（用於同步功能）
        self.mdi_areas = []  # 存儲所有MDI區域的引用
        print("[INIT] ✅ MDI區域引用已初始化")

        # 工作區快照紀錄
        self._last_workspace_path: Optional[str] = None
        print("[INIT] ✅ 工作區儲存紀錄已初始化")
        
        # 初始化遙測分析狀態追蹤
        self.lap_analysis_active = False  # 是否有遙測分析活動
        self.lap_analysis_windows = set()  # 活動的遙測分析視窗集合
        self.lap_controls_visible = False  # 遙測控件是否可見
        self._lap_controls_added = False  # 追蹤控件是否已添加到工具欄
        print("[INIT] ✅ 遙測分析狀態追蹤已初始化")

        # 賽季日曆支援
        self._season_provider = SeasonCalendarProvider()
        self._season_events_cache: Dict[int, List[SeasonEvent]] = {}
        self._season_error_message: Optional[str] = None
        self._race_event_lookup: Dict[str, SeasonEvent] = {}
        self._display_to_race_key: Dict[str, str] = {}
        self._fastf1_overrides: Dict[str, str] = {
            "Great Britain": "British",
            "United States": "United States",
            "Emilia Romagna": "Emilia Romagna",
            "Saudi Arabia": "Saudi Arabia",
            "Las Vegas": "Las Vegas",
            "Abu Dhabi": "Abu Dhabi",
        }
        self._color_palette_provider = color_palette_provider
        self._initialize_color_palette()

        print("[INIT] 🔧 開始初始化用戶界面...")
        self.init_ui()
        print("[INIT] 🎨 開始應用樣式...")
        self.apply_style_h()
        
        # 整合連動管理器
        print("[INIT] 🔗 開始整合連動管理器...")
        self.integrate_linkage_manager()
        print("[INIT] [API] Initialising health monitor...")
        self.setup_api_health_monitor()
        print("[INIT] [API] Health monitor active")

        print("[INIT] ✅ 連動管理器整合完成")
        
        print("[INIT] ✅ 主視窗初始化完成！")
        
        # 延遲檢查標籤欄隱藏狀態和圈速控件狀態
        from PyQt5.QtCore import QTimer
        print("[INIT] ⏰ 設置延遲檢查機制 (1秒後執行)...")
        
        # 設置延遲檢查機制，確保標籤隱藏狀態正確
        QTimer.singleShot(1000, self.check_and_hide_tabs)
        
        # 延遲檢查遙測分析控件狀態 (2秒後執行，確保所有視窗都已初始化)
        QTimer.singleShot(2000, self.check_and_show_lap_controls_if_needed)

    def _initialize_color_palette(self) -> None:
        """Fetch the colour palette from the API (or fall back to defaults)."""
        target_year = datetime.datetime.now().year
        try:
            self._color_palette_provider.ensure_loaded(year=target_year)
        except ColorPaletteError as exc:
            print(f"[INIT] ❌ 顏色配置載入失敗 (已禁用預設色票): {exc}")
            self._show_palette_error_message(str(exc))
            return
        except Exception as exc:
            print(f"[INIT] ❌ 顏色配置載入失敗: {exc}")
            self._show_palette_error_message(str(exc))
            return

        error = self._color_palette_provider.last_error()
        if error:
            print(f"[INIT] ⚠️ 顏色配置載入失敗，使用內建顏色: {error}")
        else:
            print(f"[INIT] 🎨 顏色配置載入完成 (year={target_year})")

    def _show_palette_error_message(self, message: str) -> None:
        try:
            QMessageBox.warning(self, "Color Palette Error", message)
        except Exception:
            print(f"[INIT] ⚠️ 顏色錯誤提示失敗: {message}")

    def init_ui(self):
        """初始化用戶界面"""
        # 創建菜單欄
        self.create_professional_menubar()
        
        # 創建工具欄
        print("[INIT] 🔧 開始創建專業工具欄...")
        self.create_professional_toolbar()
        print("[INIT] ✅ 專業工具欄創建完成")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 移除參數面板
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(1)
        
        # 主要分析區域
        analysis_splitter = QSplitter(Qt.Horizontal)
        analysis_splitter.setChildrenCollapsible(False)
        
        # 左側功能樹
        left_panel = self.create_left_panel()
        analysis_splitter.addWidget(left_panel)
        
        # 中央工作區域 - MDI多視窗
        center_panel = self.create_professional_workspace()
        analysis_splitter.addWidget(center_panel)
        
        # 設置分割比例 - 移除右側面板
        analysis_splitter.setSizes([200, 1400])
        main_layout.addWidget(analysis_splitter)
        
        # 專業狀態列
        self.create_professional_status_bar()
        
    def create_professional_menubar(self):
        """創建專業菜單欄"""
        menubar = self.menuBar()
        
        # 檔案菜單
        file_menu = menubar.addMenu(tr('file_menu'))
        file_menu.addAction(tr('load_workspace_dev', 'Load Workspace… (In Development)'), self.load_workspace)
        file_menu.addAction(tr('save_workspace_dev', 'Save Workspace (In Development)'), self.save_workspace)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        
        # 檢視菜單
        view_menu = menubar.addMenu(tr('view_menu'))
        view_menu.addAction('Tile Windows', self.tile_windows)
        view_menu.addAction('Cascade Windows', self.cascade_windows)
        view_menu.addSeparator()
        view_menu.addAction('Minimize All Windows', self.minimize_all_windows)
        view_menu.addAction('Maximize All Windows', self.maximize_all_windows)
        view_menu.addAction('Restore All Windows', self.restore_all_windows)
        view_menu.addSeparator()
        view_menu.addAction('Close All Windows', self.close_all_windows)
        view_menu.addSeparator()
        view_menu.addAction('Full Screen', self.toggle_fullscreen)
        
        # 工具菜單
        tools_menu = menubar.addMenu(tr('tools_menu'))
        tools_menu.addAction('System Settings', self.system_settings)
        self.check_api_action = QAction('Check API Status', self)
        self.check_api_action.setStatusTip('Run an API health check immediately')
        self.check_api_action.triggered.connect(self.manual_api_health_check)
        tools_menu.addAction(self.check_api_action)

        tools_menu.addSeparator()
        
        # 語言切換功能
        language_menu = tools_menu.addMenu('🌐 Language')
        
        # 英文選項
        self.english_action = QAction('🇺🇸 English', self)
        self.english_action.setCheckable(True)
        self.english_action.triggered.connect(lambda: self.set_interface_language('en'))
        language_menu.addAction(self.english_action)
        
        # 中文選項
        self.chinese_action = QAction('🇹🇼 中文', self)
        self.chinese_action.setCheckable(True)
        self.chinese_action.triggered.connect(lambda: self.set_interface_language('zh'))
        language_menu.addAction(self.chinese_action)
        
        # 日文選項
        self.japanese_action = QAction('🇯🇵 日本語', self)
        self.japanese_action.setCheckable(True)
        self.japanese_action.triggered.connect(lambda: self.set_interface_language('ja'))
        language_menu.addAction(self.japanese_action)
        
        # 設定當前語言狀態
        current_lang = get_gui_language()
        if current_lang == 'en':
            self.english_action.setChecked(True)
        elif current_lang == 'ja':
            self.japanese_action.setChecked(True)
        else:
            self.chinese_action.setChecked(True)
        
        tools_menu.addSeparator()
        
        # X軸連動功能控制
        self.linkage_action = QAction('🔗 Telemetry X-Axis Linkage', self)
        self.linkage_action.setCheckable(True)
        self.linkage_action.setChecked(True)  # 預設啟用
        self.linkage_action.triggered.connect(self.toggle_lap_analysis_linkage)
        tools_menu.addAction(self.linkage_action)

        # 說明菜單
        help_menu = menubar.addMenu(tr('help_menu', '說明'))
        help_menu.addAction(tr('about_action', '關於 F1T'), self.show_about_dialog)

    def show_about_dialog(self):
        """顯示關於對話框"""
        about_message = tr(
            'about_message',
            (
                "F1 TelemetryStation Pro\n"
                "版本：0.0 (API-ONLY 模式)\n\n"
                "本系統整合 FastF1 與 OpenF1 API，提供專業賽車遙測分析。\n"
                "GUI 模組僅透過 REST API 或既有 JSON 讀取資料，遵守 2025-10-03 API-ONLY 政策。\n\n"
                "專案維護：Telemetry Station 核心團隊\n"
                "GitHub：WarmBed / F1-data-analyze"
            ),
        )
        QMessageBox.information(self, tr('about_action', '關於 F1T'), about_message)
        
    def create_professional_toolbar(self):
        """創建專業工具欄"""
        toolbar = QToolBar()
        toolbar.setObjectName("ProfessionalToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        # 修改：增加工具欄高度以容納遙測分析控件
        toolbar.setFixedHeight(35)  # 從35增加到50像素
        self.addToolBar(toolbar)
        
        # 參數輸入區域
        toolbar.addWidget(QLabel(tr("year_label", "Year:")))
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("ParameterCombo")
        self.year_combo.addItems([str(year) for year in range(2020, 2026)])
        self.year_combo.setCurrentText("2025")
        self.year_combo.setFixedWidth(70)
        toolbar.addWidget(self.year_combo)
        
        toolbar.addWidget(QLabel(tr("race_label", "Race:")))
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("ParameterCombo")
        # 賽事項目將由 on_year_changed 方法動態填充
        self.race_combo.setFixedWidth(250)  # 增加寬度以容納較長的賽事名稱
        toolbar.addWidget(self.race_combo)
        
        toolbar.addWidget(QLabel(tr("session_label", "Session:")))
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("ParameterCombo")
        self.session_combo.addItems(["FP1", "FP2", "FP3", "Q", "SQ", "R"])  # [TOOL] 修復: 與子視窗一致
        self.session_combo.setCurrentText("R")
        self.session_combo.setFixedWidth(50)
        toolbar.addWidget(self.session_combo)
        
        # 保存工具欄引用以便動態添加/移除控件
        self.main_toolbar = toolbar
        
        # 建立遙測分析控件但不添加到工具欄（將在需要時動態添加）
        self._create_lap_analysis_controls()
        
        toolbar.addSeparator()
        
        # 檢視控制
        toolbar.addAction(tr("tile_windows_action", "Tile Windows"), self.tile_windows)
        toolbar.addAction(tr("cascade_windows_action", "Cascade Windows"), self.cascade_windows)
        
        # 連接年份變更事件
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        
        # 連接賽事和會話變更事件 - 添加同步功能
        self.race_combo.currentTextChanged.connect(self.on_main_race_changed)
        self.session_combo.currentTextChanged.connect(self.on_main_session_changed)
        
        # 初始化賽事列表
        initial_year = int(self.year_combo.currentText())
        self._refresh_calendar_for_year(initial_year)

    # ------------------------------------------------------------------
    # 賽季日曆支援
    # ------------------------------------------------------------------
    def _get_calendar_events(self, year: int) -> List[SeasonEvent]:
        """Fetch completed events for the given year with basic caching."""
        if year in self._season_events_cache and self._season_events_cache[year]:
            return self._season_events_cache[year]

        try:
            events = self._season_provider.get_completed_events(year)
            if events:
                self._season_events_cache[year] = events
            self._season_error_message = None
            return events
        except SeasonCalendarError as exc:
            self._season_error_message = str(exc)
            print(f"[CALENDAR] {self._season_error_message}")
            return self._season_events_cache.get(year, [])

    def _refresh_calendar_for_year(
        self,
        year: int,
        *,
        preserve_race_key: Optional[str] = None,
        preserve_session_code: Optional[str] = None,
    ) -> None:
        events = self._get_calendar_events(year)

        self.race_combo.blockSignals(True)
        self.race_combo.clear()
        self._race_event_lookup.clear()
        self._display_to_race_key.clear()

        if events:
            completed_events = [event for event in events if event.is_completed]
            upcoming_events = [event for event in events if not event.is_completed]

            def add_event_to_combo(event: SeasonEvent) -> None:
                label = self._format_race_display(event)
                self._race_event_lookup[event.race_key] = event
                self._display_to_race_key[label] = event.race_key
                self._display_to_race_key[event.display_label] = event.race_key
                plain_label = self._strip_race_display(label)
                if plain_label:
                    self._display_to_race_key.setdefault(plain_label, event.race_key)
                self.race_combo.addItem(label, event)

            for event in completed_events:
                add_event_to_combo(event)

            if completed_events and upcoming_events:
                self.race_combo.insertSeparator(self.race_combo.count())

            for event in upcoming_events:
                add_event_to_combo(event)

            if preserve_race_key and preserve_race_key in self._race_event_lookup:
                target_event = self._race_event_lookup[preserve_race_key]
                index = self.race_combo.findData(target_event)
                if index >= 0:
                    self.race_combo.setCurrentIndex(index)

            if self.race_combo.currentIndex() < 0:
                preferred_event = completed_events[0] if completed_events else (upcoming_events[0] if upcoming_events else None)
                if preferred_event is not None:
                    index = self.race_combo.findData(preferred_event)
                    if index >= 0:
                        self.race_combo.setCurrentIndex(index)
            if self.race_combo.currentIndex() < 0 and self.race_combo.count() > 0:
                self.race_combo.setCurrentIndex(0)
        else:
            placeholder = tr("season_calendar_placeholder", "[無已完成賽事]")
            self.race_combo.addItem(placeholder, None)

        self.race_combo.blockSignals(False)

        self._update_session_combo(preserve_session_code=preserve_session_code)

        if self._season_error_message and self.statusBar():
            self.statusBar().showMessage(self._season_error_message, 10000)

    def _select_race_by_key(self, race_key: Optional[str]) -> None:
        """Select a race in the main race combo using its canonical key."""
        if not race_key or not self.race_combo:
            return

        # Preferred path: direct lookup from cached events
        event = self._race_event_lookup.get(race_key)
        if event is not None:
            index = self.race_combo.findData(event)
            if index >= 0:
                self.race_combo.setCurrentIndex(index)
                return

        # Fallback: resolve through display mapping or iterate items
        canonical_key = self._display_to_race_key.get(race_key, race_key)
        for index in range(self.race_combo.count()):
            data = self.race_combo.itemData(index)
            if isinstance(data, SeasonEvent) and data.race_key == canonical_key:
                self.race_combo.setCurrentIndex(index)
                return

            text = self.race_combo.itemText(index)
            mapped = self._display_to_race_key.get(text)
            if mapped == canonical_key:
                self.race_combo.setCurrentIndex(index)
                return

            if self._strip_race_display(text) == canonical_key:
                self.race_combo.setCurrentIndex(index)
                return

    def _update_session_combo(
        self,
        event: Optional[SeasonEvent] = None,
        *,
        preserve_session_code: Optional[str] = None,
    ) -> None:
        event = event or self.race_combo.currentData()
        self.session_combo.blockSignals(True)
        self.session_combo.clear()

        if isinstance(event, SeasonEvent) and event.sessions:
            codes_in_order = []
            for session in event.sessions:
                self.session_combo.addItem(session.code, session)
                codes_in_order.append(session.code)

            target_code = preserve_session_code or ("R" if "R" in codes_in_order else codes_in_order[0])
            index = self.session_combo.findText(target_code)
            if index < 0:
                index = self.session_combo.findText(target_code.upper())
            if index >= 0:
                self.session_combo.setCurrentIndex(index)
            elif self.session_combo.count() > 0:
                self.session_combo.setCurrentIndex(0)
        else:
            for code in ["FP1", "FP2", "FP3", "SQ", "Q", "R"]:
                self.session_combo.addItem(code)
            if preserve_session_code:
                index = self.session_combo.findText(preserve_session_code)
                if index >= 0:
                    self.session_combo.setCurrentIndex(index)

        self.session_combo.blockSignals(False)

    def get_selected_year(self) -> int:
        try:
            return int(self.year_combo.currentText())
        except Exception:
            return 2025

    def get_selected_event(self) -> Optional[SeasonEvent]:
        data = self.race_combo.currentData()
        if isinstance(data, SeasonEvent):
            return data
        display_text = self.race_combo.currentText()
        race_key = self._strip_race_display(display_text)
        mapped_key = self._display_to_race_key.get(display_text) or self._display_to_race_key.get(race_key)
        if mapped_key:
            return self._race_event_lookup.get(mapped_key)
        return self._race_event_lookup.get(race_key)

    def get_selected_race_key(self) -> str:
        event = self.get_selected_event()
        if event:
            return event.race_key
        display_text = self.race_combo.currentText()
        race_key = self._strip_race_display(display_text)
        return self._display_to_race_key.get(display_text) or self._display_to_race_key.get(race_key) or race_key or "Unknown"

    def get_selected_session_code(self) -> str:
        data = self.session_combo.currentData()
        if data and hasattr(data, "code"):
            return getattr(data, "code")
        text = self.session_combo.currentText()
        return text.strip() if text else "R"

    @staticmethod
    def _strip_race_display(text: str) -> str:
        if not text:
            return ""
        if "(" in text:
            return text.split("(")[0].strip()
        return text.strip()

    def _format_race_display(self, event: SeasonEvent) -> str:
        if not isinstance(event, SeasonEvent):
            return ""
        if event.is_completed:
            return event.display_label
        suffix = tr("season_calendar_upcoming_suffix", "[未開賽]")
        if suffix and suffix in event.display_label:
            return event.display_label
        return f"{event.display_label} {suffix}" if suffix else event.display_label
    
    def _create_lap_analysis_controls(self):
        """創建遙測分析控件（不添加到工具欄）"""
        print("[LAP_CONTROL] 🏗️ 創建遙測分析控件...")
        
        # 動態遙測分析控件
        self.lap_separator = None
        
        # 車手1控件
        self.driver1_label = QLabel(tr("driver1_label", "Driver 1:"))
        self.driver1_label.setVisible(False)  # 初始隱藏
        self.driver1_combo = QComboBox()
        self.driver1_combo.setObjectName("ParameterCombo")
        self.driver1_combo.setFixedWidth(60)
        self.driver1_combo.setVisible(False)  # 初始隱藏
        
        # 圈數1控件
        self.lap1_label = QLabel(tr("lap_label", "Lap:"))
        self.lap1_label.setVisible(False)  # 初始隱藏
        self.lap1_spinbox = QSpinBox()
        self.lap1_spinbox.setRange(1, 100)
        self.lap1_spinbox.setValue(1)
        self.lap1_spinbox.setFixedWidth(50)
        self.lap1_spinbox.setVisible(False)  # 初始隱藏
        
        # 車手2控件
        self.driver2_label = QLabel(tr("driver2_label", "Driver 2:"))
        self.driver2_label.setVisible(False)  # 初始隱藏
        self.driver2_combo = QComboBox()
        self.driver2_combo.setObjectName("ParameterCombo")
        self.driver2_combo.addItem(tr("none_option", "None"))  # 預設選項
        self.driver2_combo.setFixedWidth(60)
        self.driver2_combo.setVisible(False)  # 初始隱藏
        
        # 圈數2控件
        self.lap2_label = QLabel(tr("lap_label", "Lap:"))
        self.lap2_label.setVisible(False)  # 初始隱藏
        self.lap2_spinbox = QSpinBox()
        self.lap2_spinbox.setRange(1, 100)
        self.lap2_spinbox.setValue(1)
        self.lap2_spinbox.setFixedWidth(50)
        self.lap2_spinbox.setVisible(False)  # 初始隱藏
        
        # 最速圈選項
        self.fastest_lap_checkbox = QCheckBox(tr("fastest_lap_option", "Fastest Lap"))
        self.fastest_lap_checkbox.setVisible(False)  # 初始隱藏
        
        # 🏁 連接最速圈checkbox的變更事件，自動設置圈數為99
        self.fastest_lap_checkbox.toggled.connect(self._on_main_fastest_lap_changed)
        
        # 更新按鈕動作（稍後動態添加）
        self.update_all_action = None
        
        # 🔄 手動更新模式：控件變更不會自動觸發更新
        # 用戶必須手動點擊 "Update All Analysis" 按鈕才會更新所有模組
        # 已移除自動連接：
        # self.driver1_combo.currentTextChanged.connect(self.on_lap_parameters_changed)
        # self.driver2_combo.currentTextChanged.connect(self.on_lap_parameters_changed)
        # self.lap1_spinbox.valueChanged.connect(self.on_lap_parameters_changed)
        # self.lap2_spinbox.valueChanged.connect(self.on_lap_parameters_changed)
        # self.fastest_lap_checkbox.toggled.connect(self.on_lap_parameters_changed)
        
        print("[LAP_CONTROL] ✅ 遙測分析控件創建完成（手動更新模式已啟用）")
    
    def get_races_for_year(self, year):
        """根據年份獲取可用的賽事列表（使用與CLI相同的race_options）"""
        try:
            year_int = int(year)
            events = self._get_calendar_events(year_int)
            if events:
                race_keys = [event.race_key for event in events]
                print(f"[RACE_OPTIONS] 從季賽日曆載入 {year_int} 年賽事: {len(race_keys)}")
                return race_keys
            print(f"[RACE_OPTIONS] 無法取得 {year_int} 年的季賽日曆資料")
            return []
        except Exception as e:
            print(f"[ERROR] 獲取賽事列表時出錯: {e}")
            # 回退到基本列表
            return ["Japan", "Great Britain", "Monaco"]
    
    def get_fastf1_race_name(self, display_name):
        """將顯示名稱轉換為 FastF1 API 期望的名稱"""
        if not display_name:
            return "Unknown"

        name = display_name.strip()
        override = self._fastf1_overrides.get(name)
        if override:
            return override

        # 優先使用季賽日曆映射
        mapped_key = self._display_to_race_key.get(name)
        if not mapped_key:
            mapped_key = self._display_to_race_key.get(self._strip_race_display(name))

        return mapped_key or name
    
    def _get_race_key_from_display(self, race_display: str) -> str:
        """
        從顯示文字獲取正規的 race_key，移除日期後綴
        
        範例:
            "Japan (2025-04-06)" → "Japan"
            "Italy" → "Italy"
            "Italian Grand Prix (2025-09-01)" → "Italian Grand Prix"
        
        Args:
            race_display: 從 race_combo 獲取的顯示文字（可能包含日期）
            
        Returns:
            清理後的賽事名稱（移除日期後綴）
        """
        if not race_display:
            return race_display
        
        # 優先使用 _display_to_race_key 映射表（最準確）
        if hasattr(self, '_display_to_race_key') and race_display in self._display_to_race_key:
            race_key = self._display_to_race_key[race_display]
            return race_key
        
        # 後備方案: 使用正則表達式移除 " (YYYY-MM-DD)" 格式的日期後綴
        import re
        clean_name = re.sub(r'\s*\(\d{4}-\d{2}-\d{2}\)\s*$', '', race_display)
        return clean_name.strip()
    
    def on_year_changed(self, year):
        """處理年份變更事件"""
        try:
            previous_race = self.get_selected_race_key()
            previous_session = self.get_selected_session_code()
        except Exception:
            previous_race = None
            previous_session = None

        try:
            year_int = int(year)
        except Exception:
            year_int = self.get_selected_year()

        print(f"[CALENDAR] 切換至 {year_int} 年賽季日曆")

        self._refresh_calendar_for_year(
            year_int,
            preserve_race_key=previous_race,
            preserve_session_code=previous_session,
        )

        self.update_status_bar()
        self.sync_to_all_mdi_subwindows('year', str(year_int))
    
    def on_main_race_changed(self, race):
        """主視窗賽事變更處理"""
        event = self.get_selected_event()
        self._update_session_combo(event)
        race_key = self.get_selected_race_key()
        print(f"[FINISH] [MAIN] 主視窗賽事變更為: {race_key}")
        self.update_status_bar()
        # 同步賽事到MDI子視窗
        self.sync_to_all_mdi_subwindows('race', race_key)
    
    def on_main_session_changed(self, session):
        """主視窗賽段變更處理"""
        session_code = self.get_selected_session_code()
        print(f"[F1] [MAIN] 主視窗賽段變更為: {session_code}")
        self.update_status_bar()
        # 同步賽段到MDI子視窗
        self.sync_to_all_mdi_subwindows('session', session_code)
    
    # ========== 遙測分析控件管理 ==========
    
    def check_and_show_lap_controls_if_needed(self):
        """檢查是否有遙測分析視窗，如果有就顯示控件"""
        print("[LAP_CONTROL] 🔍 檢查是否需要顯示遙測分析控件...")
        
        # 檢查MDI區域中是否有遙測分析相關的視窗
        current_mdi_area = self.get_current_mdi_area()
        if not current_mdi_area:
            print("[LAP_CONTROL] ❌ 無法獲取當前MDI區域")
            return
        
        lap_analysis_windows_found = []
        for sub_window in current_mdi_area.subWindowList():
            if not sub_window.isVisible():
                continue

            window_title = sub_window.windowTitle()
            
            # ✅ 修復：過濾進站分析視窗，避免誤認為 lap_analysis 模組
            if any(keyword in window_title for keyword in ["進站分析", "Pitstop", "ピットストップ"]):
                print(f"[LAP_CONTROL] ⏭️  跳過非遙測模組 (Pitstop): {window_title}")
                continue
            
            widget = sub_window.widget()

            # 依序檢查可用的模組引用
            candidate_sources = []

            # 優先使用 PopoutSubWindow 上綁定的 analysis_module
            analysis_module = getattr(sub_window, "analysis_module", None)
            if analysis_module:
                candidate_sources.append((analysis_module, "subwindow.analysis_module"))

            # 子視窗的主widget可能就是分析模組本身
            if widget:
                candidate_sources.append((widget, "subwindow.widget"))

                # 某些圖表widget會暴露 parent_module 指向真正的模組
                parent_module = getattr(widget, "parent_module", None)
                if parent_module:
                    candidate_sources.append((parent_module, "widget.parent_module"))

            matched_module = None
            matched_source = None
            for candidate, source_name in candidate_sources:
                if hasattr(candidate, "update_lap_parameters"):
                    matched_module = candidate
                    matched_source = source_name
                    break

            if matched_module:
                lap_analysis_windows_found.append((sub_window, matched_module, window_title, matched_source))
                print(
                    f"[LAP_CONTROL] 🎯 發現遙測分析視窗: {window_title} (source={matched_source})"
                )
                continue

            # 後備：關鍵字判斷（維持舊版相容）
            if any(keyword in window_title for keyword in [
                "Speed Analysis", "RPM Analysis", "⚡", "🔄",
                "Brake Analysis", "煞車分析", "Gear Analysis", "檔位分析",
                "DistanceDiff", "距離差", "Acceleration Analysis", "加速度分析"
            ]):
                lap_analysis_windows_found.append((sub_window, widget, window_title, "title_fallback"))
                print(f"[LAP_CONTROL] 🎯 (fallback) 發現遙測分析視窗: {window_title}")
        
        if lap_analysis_windows_found:
            print(f"[LAP_CONTROL] 📊 找到 {len(lap_analysis_windows_found)} 個遙測分析視窗")
            
            # 🔧 修復：不清空現有追蹤，而是進行智能合併
            # 保留已正確追蹤的模組，只添加新發現的
            existing_modules = set()
            for existing in self.lap_analysis_windows:
                if hasattr(existing, 'update_lap_parameters'):
                    existing_modules.add(existing)
                    print(f"[LAP_CONTROL] ✅ 保留現有模組追蹤: {type(existing).__name__}")
            
            # 清空並重建，但保留正確的模組
            self.lap_analysis_windows.clear()
            self.lap_analysis_windows.update(existing_modules)
            
            for sub_window, analysis_obj, window_title, source in lap_analysis_windows_found:
                # 檢查是否已經通過模組正確追蹤了這個視窗
                already_tracked = False
                for tracked_module in existing_modules:
                    if (hasattr(tracked_module, '_sub_window') and 
                        tracked_module._sub_window == sub_window):
                        already_tracked = True
                        print(f"[LAP_CONTROL] ✅ 視窗已通過模組正確追蹤: {window_title}")
                        break
                
                if already_tracked:
                    continue
                
                # 優先使用已解析出的分析模組
                if analysis_obj and hasattr(analysis_obj, 'update_lap_parameters'):
                    self.lap_analysis_windows.add(analysis_obj)
                    print(
                        f"[LAP_CONTROL] ✅ 已添加模組到追蹤: {window_title} (source={source})"
                    )
                # 🔧 修復：檢查子視窗是否仍然保有分析模組引用
                elif hasattr(sub_window, 'analysis_module') and hasattr(sub_window.analysis_module, 'update_lap_parameters'):
                    self.lap_analysis_windows.add(sub_window.analysis_module)
                    print(
                        f"[LAP_CONTROL] ✅ 已透過子視窗引用添加模組: {window_title}"
                    )
                else:
                    # 如果不是分析模組，最後退回子視窗本身
                    self.lap_analysis_windows.add(sub_window)
                    print(f"[LAP_CONTROL] ✅ 已添加子視窗到追蹤: {window_title}")
            
            # 強制顯示遙測分析控件
            print("[LAP_CONTROL] 🚀 強制顯示遙測分析控件...")
            self.show_lap_controls()
        else:
            print("[LAP_CONTROL] ℹ️ 未發現遙測分析視窗，不顯示控件")
    
    def force_show_lap_controls(self):
        """強制顯示遙測分析控件（測試用）"""
        print("[LAP_CONTROL] 🚨 強制顯示遙測分析控件...")
        self.show_lap_controls()
    
    def initialize_driver_lists(self):
        """初始化車手列表"""
        print("[LAP_CONTROL] 🎮 開始初始化車手列表")
        import traceback
        stack = traceback.format_stack()
        print("[LAP_CONTROL] 📞 調用堆疊:")
        for frame in stack[-3:]:  # 顯示最後3個堆疊框架
            print(f"[LAP_CONTROL]   {frame.strip()}")
            
        try:
            # 檢查控件狀態
            print(f"[LAP_CONTROL] 🔍 檢查控件狀態:")
            print(f"[LAP_CONTROL]   driver1_combo.isVisible(): {self.driver1_combo.isVisible()}")
            print(f"[LAP_CONTROL]   driver1_combo.count(): {self.driver1_combo.count()}")
            print(f"[LAP_CONTROL]   driver2_combo.isVisible(): {self.driver2_combo.isVisible()}")
            print(f"[LAP_CONTROL]   driver2_combo.count(): {self.driver2_combo.count()}")
            
            # 標準車手列表（2025賽季）
            drivers = [
                "VER", "PER", "LEC", "SAI", "HAM", "RUS", "NOR", "PIA", 
                "ALO", "STR", "TSU", "YUK", "ALB", "SAR", "MAG", "HUL",
                "GAS", "OCO", "BOT", "ZHO"
            ]
            
            print("[LAP_CONTROL] 🔄 清空並填充車手列表...")
            # 清空並添加車手到兩個下拉框
            self.driver1_combo.clear()
            # 🔧 修復：使用 addItem 並設定 UserData
            for driver in drivers:
                self.driver1_combo.addItem(driver, driver)
            self.driver1_combo.setCurrentText("VER")  # 預設選擇VER
            print("[LAP_CONTROL] ✅ driver1_combo 設定完成")
            
            self.driver2_combo.clear()
            # 🔧 修復：第一個選項的 UserData 設為 None
            self.driver2_combo.addItem(tr("none_option", "None"), None)
            # 🔧 修復：使用 addItem 並設定 UserData（不使用 addItems）
            for driver in drivers:
                self.driver2_combo.addItem(driver, driver)
            self.driver2_combo.setCurrentText("無")  # 預設無第二車手
            print("[LAP_CONTROL] ✅ driver2_combo 設定完成")
            
            # 驗證設定結果
            print(f"[LAP_CONTROL] 📊 設定後狀態:")
            print(f"[LAP_CONTROL]   driver1_combo當前文字: '{self.driver1_combo.currentText()}'")
            print(f"[LAP_CONTROL]   driver2_combo當前文字: '{self.driver2_combo.currentText()}'")
            print(f"[LAP_CONTROL]   driver1_combo項目數: {self.driver1_combo.count()}")
            print(f"[LAP_CONTROL]   driver2_combo項目數: {self.driver2_combo.count()}")
            
            print(f"[LAP_CONTROL] ✅ 已初始化車手列表，共 {len(drivers)} 位車手")
            
        except Exception as e:
            print(f"[ERROR] [LAP_CONTROL] 初始化車手列表失敗: {e}")
    
    def show_lap_controls(self):
        """顯示遙測分析控件（動態添加到工具欄）"""
        print("[LAP_CONTROL] 📊 開始顯示遙測分析控件（動態添加）")
        
        # 檢查是否已經添加到工具欄
        if hasattr(self, '_lap_controls_added') and self._lap_controls_added:
            print("[LAP_CONTROL] ⚠️ 遙測分析控件已經在工具欄中，跳過重複添加")
            return
        
        try:
            # 強制重新初始化車手列表，確保在重新顯示時車手列表正確
            print("[LAP_CONTROL] 🔄 強制重新初始化車手列表...")
            self.initialize_driver_lists()
            
            # 在賽事會話控件後添加分隔符
            session_action = None
            for action in self.main_toolbar.actions():
                widget = self.main_toolbar.widgetForAction(action)
                if widget == self.session_combo:
                    session_action = action
                    break
            
            if session_action:
                # 找到會話控件的下一個位置
                session_index = self.main_toolbar.actions().index(session_action)
                next_action = None
                if session_index + 1 < len(self.main_toolbar.actions()):
                    next_action = self.main_toolbar.actions()[session_index + 1]
                
                # 添加分隔符
                if next_action:
                    self.lap_separator = self.main_toolbar.insertSeparator(next_action)
                else:
                    self.lap_separator = self.main_toolbar.addSeparator()
                
                # 依序添加遙測分析控件
                controls_to_add = [
                    self.driver1_label, self.driver1_combo,
                    self.lap1_label, self.lap1_spinbox,
                    self.driver2_label, self.driver2_combo,
                    self.lap2_label, self.lap2_spinbox,
                    self.fastest_lap_checkbox
                ]
                
                print(f"[LAP_CONTROL] 🔧 準備添加 {len(controls_to_add)} 個控件到工具欄")
                for i, control in enumerate(controls_to_add):
                    control_name = control.__class__.__name__
                    control_text = getattr(control, 'text', lambda: '')() or getattr(control, 'currentText', lambda: '')()
                    print(f"[LAP_CONTROL] 添加控件 {i+1}: {control_name} - '{control_text}'")
                    
                    # 設置控件的基本屬性
                    control.setParent(self.main_toolbar)
                    control.setVisible(True)
                    control.setEnabled(True)
                    
                    # 添加到工具欄
                    if next_action:
                        self.main_toolbar.insertWidget(next_action, control)
                    else:
                        self.main_toolbar.addWidget(control)
                    
                    print(f"[LAP_CONTROL] 控件 {i+1} 已添加，可見性: {control.isVisible()}, 啟用: {control.isEnabled()}")
                
                # 添加更新按鈕
                update_action = QAction("🔄 Update All Analysis", self)
                update_action.triggered.connect(self.update_all_lap_analysis)
                
                if next_action:
                    self.update_all_action = self.main_toolbar.insertAction(next_action, update_action)
                else:
                    self.update_all_action = self.main_toolbar.addAction(update_action)
                
                # 添加遙測分析連動總開關
                from core.gui_i18n import tr
                self.lap_linkage_action = QAction(f"🔗 {tr('lap_linkage', 'Lap Linkage')}", self)
                self.lap_linkage_action.setCheckable(True)
                self.lap_linkage_action.setChecked(True)  # 預設啟用
                self.lap_linkage_action.triggered.connect(self.toggle_lap_analysis_linkage)
                
                if next_action:
                    self.main_toolbar.insertAction(next_action, self.lap_linkage_action)
                else:
                    self.main_toolbar.addAction(self.lap_linkage_action)
                
                print("[LAP_CONTROL] ✅ 圈速分析控件成功添加到工具欄")
                print(f"[LAP_CONTROL] 📊 工具欄狀態檢查:")
                print(f"[LAP_CONTROL]   - 工具欄可見: {self.main_toolbar.isVisible()}")
                print(f"[LAP_CONTROL]   - 工具欄動作數量: {len(self.main_toolbar.actions())}")
                print(f"[LAP_CONTROL]   - 工具欄尺寸: {self.main_toolbar.size()}")
                
                # 強制更新工具欄顯示
                self.main_toolbar.update()
                self.main_toolbar.repaint()
                
                # 檢查每個控件的狀態
                print(f"[LAP_CONTROL] 🔍 控件狀態最終檢查:")
                for i, control in enumerate(controls_to_add):
                    widget_name = control.__class__.__name__
                    is_visible = control.isVisible()
                    is_enabled = control.isEnabled()
                    size = control.size()
                    print(f"[LAP_CONTROL]   控件{i+1} ({widget_name}): 可見={is_visible}, 啟用={is_enabled}, 尺寸={size}")
                
                self._lap_controls_added = True
                self.lap_controls_visible = True
                
        except Exception as e:
            print(f"[LAP_CONTROL] ❌ 添加圈速分析控件時發生錯誤: {e}")
    
    def hide_lap_controls(self):
        """隱藏遙測分析控件（從工具欄移除）"""
        if len(self.lap_analysis_windows) > 0:
            print("[LAP_CONTROL] ⚠️ 還有圈速分析視窗開啟中，不隱藏控件")
            return
            
        print("[LAP_CONTROL] 🔴 開始隱藏圈速分析控件（從工具欄移除）")
        
        # 檢查是否已經從工具欄移除
        if not hasattr(self, '_lap_controls_added') or not self._lap_controls_added:
            print("[LAP_CONTROL] ⚠️ 圈速分析控件已經不在工具欄中，跳過移除")
            return
        
        try:
            # 移除所有遙測分析控件
            if hasattr(self, 'lap_separator') and self.lap_separator:
                self.main_toolbar.removeAction(self.lap_separator)
                self.lap_separator = None
            
            # 移除控件
            controls_to_remove = [
                self.driver1_label, self.driver1_combo,
                self.lap1_label, self.lap1_spinbox,
                self.driver2_label, self.driver2_combo,
                self.lap2_label, self.lap2_spinbox,
                self.fastest_lap_checkbox
            ]
            
            for control in controls_to_remove:
                # 查找包含這個widget的action並移除
                for action in self.main_toolbar.actions():
                    if action.defaultWidget() == control:
                        self.main_toolbar.removeAction(action)
                        break
            
            # 移除更新按鈕
            if hasattr(self, 'update_all_action') and self.update_all_action:
                self.main_toolbar.removeAction(self.update_all_action)
                self.update_all_action = None
            
            print("[LAP_CONTROL] ✅ 圈速分析控件成功從工具欄移除")
            self._lap_controls_added = False
            self.lap_controls_visible = False
            
        except Exception as e:
            print(f"[LAP_CONTROL] ❌ 移除圈速分析控件時發生錯誤: {e}")


        print("[LAP_CONTROL] 🔍 ========== 調試結束 ==========")
    
    def on_lap_analysis_window_opened(self, window_object, analysis_type):
        """遙測分析視窗開啟時調用"""
        window_title = window_object.windowTitle() if hasattr(window_object, 'windowTitle') else str(window_object)
        print(f"[LAP_CONTROL] 🚨 CRITICAL: on_lap_analysis_window_opened 被調用!")
        print(f"[LAP_CONTROL] 📊 參數: window_title='{window_title}', analysis_type='{analysis_type}'")
        
        import traceback
        stack = traceback.format_stack()
        print("[LAP_CONTROL] 📞 CRITICAL 調用堆疊:")
        for frame in stack[-5:]:  # 顯示最後5個堆疊框架
            print(f"[LAP_CONTROL]   {frame.strip()}")
        
        # 為視窗對象添加分析類型標記（用於後續過濾）
        if not hasattr(window_object, '_analysis_type'):
            window_object._analysis_type = analysis_type
            print(f"[LAP_CONTROL] 🏷️ 為視窗添加類型標記: {analysis_type}")
        
        # 存儲視窗對象而不是標題字符串
        self.lap_analysis_windows.add(window_object)
        print(f"[LAP_CONTROL] 📊 圈速分析視窗已開啟: {window_title} ({analysis_type})")
        print(f"[LAP_CONTROL] 📊 當前活動視窗數: {len(self.lap_analysis_windows)}")
        
        # 顯示圈速控件
        print("[LAP_CONTROL] 🎯 即將調用 show_lap_controls()...")
        self.show_lap_controls()
        
        # 🎯 新增: 統一觸發工具欄狀態更新 - 任何遙測分析模組都會觸發
        print(f"[TOOLBAR_TRIGGER] 🚀 圈速分析模組開啟，觸發工具欄狀態更新: {analysis_type}")
        self._trigger_toolbar_status_for_lap_analysis(analysis_type, window_object)
    
    def on_lap_analysis_window_closed(self, window_object):
        """遙測分析視窗關閉時調用"""
        # 從追蹤集合中移除
        self.lap_analysis_windows.discard(window_object)
        
        # 獲取視窗標題用於日誌
        window_title = window_object.windowTitle() if hasattr(window_object, 'windowTitle') else str(window_object)
        print(f"[LAP_CONTROL] 📊 圈速分析視窗已關閉: {window_title}")
        
        # 如果是分析模組，確保清理相關引用
        if hasattr(window_object, '_sub_window'):
            sub_window = window_object._sub_window
            # 從 MDI 區域中移除子視窗
            if sub_window and sub_window.parent():
                mdi_area = sub_window.parent()
                if hasattr(mdi_area, 'removeSubWindow'):
                    mdi_area.removeSubWindow(sub_window)
                    print(f"[LAP_CONTROL] 🗑️ 已從 MDI 區域移除子視窗: {window_title}")
        
        print(f"[LAP_CONTROL] 📊 當前活動視窗數: {len(self.lap_analysis_windows)}")
        
        # 如果沒有活動視窗，隱藏圈速控件
        if len(self.lap_analysis_windows) == 0:
            self.hide_lap_controls()
    
    def _trigger_toolbar_status_for_lap_analysis(self, analysis_type, window_object):
        """統一觸發工具欄狀態更新 - 任何遙測分析模組都會觸發"""
        try:
            print(f"[TOOLBAR_TRIGGER] 🎯 開始為 {analysis_type} 分析模組觸發工具欄狀態更新")
            
            # 根據分析類型設定模組名稱
            module_name_mapping = {
                "speed_analysis": "Speed Analysis",
                "rpm": "RPM Analysis", 
                "brake": "Brake Analysis",
                "throttle": "Throttle Analysis",
                "steering": "Steering Analysis",
                "gear": "Gear Analysis",
                "acceleration": "Acceleration Analysis",
                "speed_diff": "Speed Difference Analysis",
                "distancediff": "Distance Difference Analysis"
            }
            
            module_name = module_name_mapping.get(analysis_type, f"{analysis_type}分析")
            
            # 獲取當前遙測分析設置
            driver1 = self.driver1_combo.currentText() if hasattr(self, 'driver1_combo') else "VER"
            driver2 = self.driver2_combo.currentText() if hasattr(self, 'driver2_combo') else "LEC"
            lap1 = self.lap1_spinbox.value() if hasattr(self, 'lap1_spinbox') else 1
            lap2 = self.lap2_spinbox.value() if hasattr(self, 'lap2_spinbox') else 1
            
            # 處理單車手模式
            if driver2 == "無":
                driver2 = None
            
            # 構建圈數信息
            if driver2:
                lap_numbers = f"{driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈"
            else:
                lap_numbers = f"{driver1} 第{lap1}圈"
            
            # 構建狀態信息（初始值，等數據載入後會更新更詳細的信息）
            lap_time = "載入中..."
            tyre_compound = "分析中..."
            
            # 觸發工具欄狀態更新
            self.update_toolbar_status(
                module_name=module_name,
                lap_time=lap_time,
                tyre_compound=tyre_compound,
                lap_numbers=lap_numbers
            )
            
            print(f"[TOOLBAR_TRIGGER] ✅ 已觸發工具欄狀態更新: {module_name} | {lap_numbers}")
            
        except Exception as e:
            print(f"[ERROR] [TOOLBAR_TRIGGER] 觸發工具欄狀態更新失敗: {e}")
            import traceback
            traceback.print_exc()

    def update_all_lap_analysis(self):
        """序列化更新所有遙測分析視窗（防止並發衝突）"""
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import Qt
        import time
        
        print("[LAP_CONTROL] 🔄 開始序列化更新所有圈速分析視窗...")
        
        if len(self.lap_analysis_windows) == 0:
            print("[LAP_CONTROL] ⚠️ 沒有活動的圈速分析視窗")
            QMessageBox.information(self, tr('update'), tr('update_progress_no_windows'))
            return
        
        # 定義應該被更新的分析類型（只包含遙測相關的分析）
        telemetry_analysis_types = {
            'speed_analysis',  # 速度分析
            'speed',          # 速度圖表
            'brake',          # 煞車分析
            'throttle',       # 油門分析
            'steering',       # 轉向分析
            'gear',           # 檔位分析
            'rpm',            # RPM分析
            'acceleration',   # 加速度分析
            'speed_diff',     # 速度差分析
            'Speeddiff',      # 速度差分析（大寫變體）
            'distancediff'    # 累積距離差分析
        }
        
        # 獲取當前設置
        driver1 = self.driver1_combo.currentText()
        
        # 🔍 詳細診斷：driver2_combo 狀態
        logger.info(f"[DEBUG] 🔍 driver2_combo 詳細狀態檢查:")
        logger.info(f"  currentIndex: {self.driver2_combo.currentIndex()}")
        logger.info(f"  currentText: '{self.driver2_combo.currentText()}'")
        logger.info(f"  currentData: {self.driver2_combo.currentData()}")
        logger.info(f"  count: {self.driver2_combo.count()}")
        logger.info(f"  所有項目列表:")
        for i in range(min(5, self.driver2_combo.count())):  # 只顯示前5項避免日誌過長
            logger.info(f"    [{i}] text='{self.driver2_combo.itemText(i)}', data={self.driver2_combo.itemData(i)}")
        if self.driver2_combo.count() > 5:
            logger.info(f"    ... (共 {self.driver2_combo.count()} 項)")
        
        # 🔧 修復：使用 currentData() 而不是 currentText() 來判斷是否為 "無"
        # 這樣可以正確處理所有語言（中文 "無"、英文 "None"、日語 "なし"）
        driver2_data = self.driver2_combo.currentData()
        driver2 = self.driver2_combo.currentText() if driver2_data is not None else None
        logger.info(f"  → 最終 driver2 判斷: driver2_data={driver2_data} → driver2={driver2}")
        
        lap1 = self.lap1_spinbox.value()
        lap2 = self.lap2_spinbox.value()
        is_fastest = self.fastest_lap_checkbox.isChecked()
        
        logger.info(f"圈速控制 - 更新參數: {driver1} vs {driver2}, 第{lap1}圈 vs 第{lap2}圈, 最速圈: {is_fastest}")
        
        # 獲取當前基本設置
        year = self.year_combo.currentText()
        race_display = self.race_combo.currentText()
        session = self.session_combo.currentText()
        
        # 🔧 修復: 清理 race 參數，移除日期後綴 (如 "Japan (2025-04-06)" → "Japan")
        race = self._get_race_key_from_display(race_display)
        
        logger.info(f"圈速控制 - 基本設置: year={year}, race={race}, session={session}")
        logger.debug(f"圈速控制 - 原始 race_display: {race_display}")
        if race != race_display:
            logger.info(f"圈速控制 - Race 參數已清理: '{race_display}' → '{race}'")
        
        # 過濾出需要更新的遙測模組
        modules_to_update = []
        skipped_count = 0
        
        for analysis_module in list(self.lap_analysis_windows):
            analysis_type = getattr(analysis_module, '_analysis_type', 'unknown')
            
            if analysis_type not in telemetry_analysis_types:
                skipped_count += 1
                logger.debug(f"圈速控制 - 跳過非遙測分析視窗: 類型={analysis_type}")
                continue
            
            modules_to_update.append((analysis_module, analysis_type))
        
        if not modules_to_update:
            msg = tr('update_progress_no_telemetry').format(skipped_count)
            QMessageBox.information(self, tr('update'), msg)
            logger.info(f"圈速控制 - {msg}")
            return
        
        logger.info(f"圈速控制 - 找到 {len(modules_to_update)} 個遙測模組需要更新")
        
        # 創建進度對話框
        progress = QProgressDialog(
            tr('update_progress_preparing'), 
            tr('cancel'), 
            0, 
            len(modules_to_update), 
            self
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle(tr('update_progress_title'))
        progress.setMinimumDuration(0)
        progress.setValue(0)
        QApplication.processEvents()
        
        # 序列化更新所有模組
        updated_count = 0
        failed_count = 0
        
        for i, (analysis_module, analysis_type) in enumerate(modules_to_update, 1):
            # 檢查用戶是否取消
            if progress.wasCanceled():
                logger.info(f"圈速控制 - 用戶取消更新操作（已完成 {updated_count}/{len(modules_to_update)}）")
                break
            
            try:
                # 獲取視窗標題用於顯示
                window_title = "未知視窗"
                if hasattr(analysis_module, 'get_window_title'):
                    # 傳遞必要的參數給 get_window_title
                    try:
                        window_title = analysis_module.get_window_title(year, race, session)
                    except TypeError:
                        # 如果新版方法需要參數但舊版不需要，使用備用方案
                        window_title = f"{getattr(analysis_module, 'display_name', 'Analysis Module')} - {year} {race} {session}"
                elif hasattr(analysis_module, '_sub_window') and hasattr(analysis_module._sub_window, 'windowTitle'):
                    window_title = analysis_module._sub_window.windowTitle()
                elif hasattr(analysis_module, 'windowTitle'):
                    window_title = analysis_module.windowTitle()
                
                # 更新進度對話框
                progress_text = f"{tr('update_progress_updating')} {analysis_type} ({i}/{len(modules_to_update)})...\n{window_title}"
                progress.setLabelText(progress_text)
                progress.setValue(i)
                QApplication.processEvents()  # 確保UI響應
                
                logger.info(f"圈速控制 - [{i}/{len(modules_to_update)}] 更新視窗: {window_title} (類型: {analysis_type})")
                
                # 檢查是否為速度分析模組
                has_method = hasattr(analysis_module, 'update_lap_parameters')
                logger.debug(f"圈速控制 - 方法檢查: {'有' if has_method else '無'} update_lap_parameters")
                
                if has_method:
                    logger.info(f"圈速控制 - 找到 update_lap_parameters 方法，開始調用...")
                    
                    # 調用更新方法並傳遞詳細參數
                    success = analysis_module.update_lap_parameters(
                        year=year,
                        race=race, 
                        session=session,
                        driver1=driver1,
                        driver2=driver2,
                        lap1=lap1,
                        lap2=lap2,
                        is_fastest=is_fastest
                    )
                    
                    if success:
                        updated_count += 1
                        logger.info(f"圈速控制 - 更新成功")
                    else:
                        logger.warning(f"圈速控制 - 更新返回 False")
                        failed_count += 1
                else:
                    logger.warning(f"圈速控制 - 模組沒有 update_lap_parameters 方法")
                    failed_count += 1

                # 短暫延遲確保載入完成（防止並發衝突）
                QApplication.processEvents()
                time.sleep(0.25)  # 250ms 延遲
            except Exception as e:
                failed_count += 1
                logger.error(f"圈速控制 - 更新時發生錯誤: {e}", exc_info=True)
        
        # 確保進度對話框完成
        progress.setValue(len(modules_to_update))
        
        # 顯示結果摘要
        result_text = f"序列化更新完成！\n\n"
        result_text += f"✅ 成功更新: {updated_count} 個模組\n"
        if failed_count > 0:
            result_text += f"⚠️ 失敗/跳過: {failed_count} 個模組\n"
        if skipped_count > 0:
            result_text += f"⏭️ 跳過非遙測: {skipped_count} 個模組\n"
        result_text += f"\n總共處理: {len(modules_to_update)} 個遙測模組"
        
        logger.info(f"圈速控制 - 序列化更新完成: 成功={updated_count}, 失敗={failed_count}, 跳過={skipped_count}, 總計={len(modules_to_update)}")
        
        # 不再顯示結果對話框（用戶請求取消彈窗）
        # 結果資訊已在終端日誌中顯示，無需額外彈窗
        
        # 額外觸發專用的圖表更新（為了確保chart widget正確更新）
        try:
            logger.debug("圈速控制 - 觸發專用圖表更新邏輯...")
            
            # 檢查當前窗口類型並調用對應的更新方法
            window_title = self.windowTitle()
            if '速度分析' in window_title or 'Speed Analysis' in window_title:
                logger.debug("圈速控制 - 檢測到速度分析視窗，觸發專用更新")
                self._update_speed_analysis_chart({})  # 使用空的json_data，讓方法依賴loader
            elif '油門分析' in window_title or 'Throttle Analysis' in window_title:
                logger.debug("圈速控制 - 檢測到油門分析視窗，觸發專用更新")
                self._update_throttle_analysis_chart({})
            elif 'RPM分析' in window_title or 'RPM Analysis' in window_title:
                logger.debug("圈速控制 - 檢測到RPM分析視窗，觸發專用更新")
                self._update_rpm_analysis_chart({})
            elif '檔位分析' in window_title or 'Gear Analysis' in window_title:
                logger.debug("圈速控制 - 檢測到檔位分析視窗，觸發專用更新")
                self._update_gear_analysis_chart({})
            elif '加速度分析' in window_title or 'Acceleration Analysis' in window_title:
                logger.debug("圈速控制 - 檢測到加速度分析視窗，觸發專用更新")
                self._update_acceleration_analysis_chart({})
            else:
                logger.debug(f"圈速控制 - 未識別的視窗類型: {window_title}")
                
        except Exception as e:
            logger.error(f"圈速控制 - 專用圖表更新失敗: {e}", exc_info=True)

    def _on_main_fastest_lap_changed(self, checked):
        """主頁面最速圈checkbox變更時的處理 - 自動設置圈數為99"""
        print(f"[LAP_CONTROL] 🏁 主頁面最速圈checkbox變更: {checked}")
        
        if checked:
            # 最速圈被勾選，自動設置圈數為99
            print("[LAP_CONTROL] 🏁 最速圈被選中，自動設置圈數1和圈數2為99")
            
            if hasattr(self, 'lap1_spinbox'):
                old_value1 = self.lap1_spinbox.value()
                self.lap1_spinbox.setValue(99)
                print(f"[LAP_CONTROL] 🏁 圈數1: {old_value1} → 99")
                
            if hasattr(self, 'lap2_spinbox'):
                old_value2 = self.lap2_spinbox.value()
                self.lap2_spinbox.setValue(99)
                print(f"[LAP_CONTROL] 🏁 圈數2: {old_value2} → 99")
        else:
            # 最速圈被取消，恢復預設圈數1
            print("[LAP_CONTROL] 🏁 最速圈被取消，恢復預設圈數1")
            
            if hasattr(self, 'lap1_spinbox'):
                self.lap1_spinbox.setValue(1)
                print(f"[LAP_CONTROL] 🏁 圈數1: 恢復為1")
                
            if hasattr(self, 'lap2_spinbox'):
                self.lap2_spinbox.setValue(1)
                print(f"[LAP_CONTROL] 🏁 圈數2: 恢復為1")

    def on_lap_parameters_changed(self):
        """
        圈速參數變更處理器（手動更新模式）
        
        ⚠️ 注意：此方法已停用自動更新功能
        現在僅用於記錄參數變更，不會觸發實際更新
        用戶必須手動點擊 "Update All Analysis" 按鈕才會更新
        """
        print("[LAP_CONTROL] � 圈速參數已變更（手動更新模式，不自動更新）")
        
        # 記錄當前參數值（僅用於調試）
        try:
            driver1 = self.driver1_combo.currentText() if hasattr(self, 'driver1_combo') else "未知"
            driver2 = self.driver2_combo.currentText() if hasattr(self, 'driver2_combo') else "未知"
            lap1 = self.lap1_spinbox.value() if hasattr(self, 'lap1_spinbox') else "未知"
            lap2 = self.lap2_spinbox.value() if hasattr(self, 'lap2_spinbox') else "未知"
            is_fastest = self.fastest_lap_checkbox.isChecked() if hasattr(self, 'fastest_lap_checkbox') else False
            
            print(f"[LAP_CONTROL] 📊 當前參數值:")
            print(f"[LAP_CONTROL]   🏎️ 車手1: '{driver1}'")
            print(f"[LAP_CONTROL]   🏎️ 車手2: '{driver2}'")
            print(f"[LAP_CONTROL]   🏁 圈數1: {lap1}")
            print(f"[LAP_CONTROL]   🏁 圈數2: {lap2}")
            print(f"[LAP_CONTROL]   ⚡ 最速圈: {is_fastest}")
            print(f"[LAP_CONTROL] � 提示: 請點擊 'Update All Analysis' 按鈕以應用更改")
                
        except Exception as e:
            print(f"[LAP_CONTROL] ❌ 參數記錄時發生錯誤: {e}")
        
        # ⚠️ 已移除自動更新邏輯
        # 不再啟動計時器或調用 update_all_lap_analysis()
        # 用戶必須手動點擊更新按鈕
        
    def create_left_panel(self):
        """創建左側面板 (僅包含功能樹)。"""
        widget = QWidget()
        widget.setObjectName("LeftPanel")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)

        function_tree = self.create_professional_function_tree()
        layout.addWidget(function_tree)

        return widget

    def create_professional_function_tree(self):
        """創建專業功能樹"""
        widget = QWidget()
        widget.setObjectName("FunctionTreeWidget")  # 添加對象名稱
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        
        # 標題
        title_frame = QFrame()
        title_frame.setObjectName("FunctionTreeTitle")
        title_frame.setFixedHeight(16)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(2, 1, 2, 1)
        title_layout.addWidget(QLabel(tr("analysis_modules", "Analysis Modules")))
        layout.addWidget(title_frame)
        
        # 支援右鍵選單的功能樹
        tree = ContextMenuTreeWidget(self)
        tree.setObjectName("ProfessionalFunctionTree")
        tree.setHeaderHidden(True)
        tree.setIndentation(12)  # 增加縮排以容納三層結構
        tree.setRootIsDecorated(True)
        
        # ========== Race Overview Analysis ==========
        race_overview_group = QTreeWidgetItem(tree, [tr("race_overview_analysis", "Race Overview Analysis")])
        race_overview_group.setExpanded(True)
        QTreeWidgetItem(race_overview_group, [tr("rain_analysis", "Rain Analysis")])
        QTreeWidgetItem(race_overview_group, [tr("track_analysis", "Track Analysis")])
        QTreeWidgetItem(race_overview_group, [tr("pitstop_analysis", "Pitstop Analysis")])
        QTreeWidgetItem(race_overview_group, [tr("accident_analysis", "Accident Analysis")])
        QTreeWidgetItem(race_overview_group, [tr("tire_strategy_analysis", "Tire Strategy Analysis")])
        
        # ========== Driver Performance Analysis ==========
        driver_performance_group = QTreeWidgetItem(tree, [tr("driver_performance_analysis", "Driver Performance Analysis")])
        driver_performance_group.setExpanded(True)
        
        # Lap Analysis (Telemetry) - 8 個子模組
        lap_analysis = QTreeWidgetItem(driver_performance_group, [tr("lap_analysis", "Lap Analysis (Telemetry)")])
        lap_analysis.setExpanded(False)  # 預設收合
        QTreeWidgetItem(lap_analysis, ["    (L) " + tr("speed_analysis", "Speed Analysis")])
        QTreeWidgetItem(lap_analysis, ["    (L) " + tr("brake_analysis", "Brake Analysis")])
        QTreeWidgetItem(lap_analysis, ["    (L) " + tr("throttle_analysis_sub", "Throttle Analysis")])
        QTreeWidgetItem(lap_analysis, ["    (L) " + tr("gear_analysis", "Gear Analysis")])
        QTreeWidgetItem(lap_analysis, ["    (L) " + tr("rpm_analysis", "RPM Analysis")])
        QTreeWidgetItem(lap_analysis, ["    (L) " + tr("acceleration_analysis", "Acceleration Analysis")])
        QTreeWidgetItem(lap_analysis, ["    (L) " + tr("speed_diff_analysis", "Speed Diff Analysis")])
        QTreeWidgetItem(lap_analysis, ["    (L) " + tr("distance_diff_analysis", "Distance Diff Analysis")])
        
        # Detailed Lap Analysis - 2 個視圖
        detailed_lap = QTreeWidgetItem(driver_performance_group, [tr("detailed_lap_analysis", "Detailed Lap Analysis")])
        detailed_lap.setExpanded(False)
        QTreeWidgetItem(detailed_lap, ["    (D) " + tr("detailed_lap_table", "Detailed Lap Table")])
        QTreeWidgetItem(detailed_lap, ["    (D) " + tr("lap_time_box_plot_sub", "Lap Time Box Plot")])
        
        # Throttle Analysis - 2 個視圖
        throttle_analysis = QTreeWidgetItem(driver_performance_group, [tr("throttle_analysis", "Throttle Analysis")])
        throttle_analysis.setExpanded(False)
        QTreeWidgetItem(throttle_analysis, ["    (T) " + tr("throttle_box_plot", "Throttle Box Plot")])
        QTreeWidgetItem(throttle_analysis, ["    (T) " + tr("throttle_line_chart", "Throttle Line Chart")])
        
        # Ideal Lap Analysis - 3 個子模組
        ideal_lap = QTreeWidgetItem(driver_performance_group, [tr("ideal_lap_analysis", "Ideal Lap Analysis")])
        ideal_lap.setExpanded(False)
        QTreeWidgetItem(ideal_lap, ["    " + tr("ideal_lap_ranking_table", "Ranking Table")])
        
        # Coming Soon 項目（灰色顯示）
        from PyQt5.QtGui import QColor
        heatmap_item = QTreeWidgetItem(ideal_lap, ["    " + tr("ideal_lap_sector_heatmap", "Sector Heat Map (Coming Soon)")])
        heatmap_item.setForeground(0, QColor("#999999"))
        heatmap_item.setFlags(heatmap_item.flags() & ~Qt.ItemIsEnabled)  # 禁用點擊
        
        comparison_item = QTreeWidgetItem(ideal_lap, ["    " + tr("ideal_lap_sector_comparison", "Sector Comparison (Coming Soon)")])
        comparison_item.setForeground(0, QColor("#999999"))
        comparison_item.setFlags(comparison_item.flags() & ~Qt.ItemIsEnabled)  # 禁用點擊
        
        # ========== Multi-Season Analysis ==========
        multi_season_group = QTreeWidgetItem(tree, [tr("multi_season_analysis", "Multi-Season Analysis")])
        multi_season_group.setExpanded(False)
        future_item = QTreeWidgetItem(multi_season_group, ["    " + tr("coming_soon", "Coming Soon...")])
        future_item.setForeground(0, QColor("#999999"))
        future_item.setFlags(future_item.flags() & ~Qt.ItemIsEnabled)  # 禁用點擊
        
        layout.addWidget(tree)
        
        return widget
        
    def create_professional_workspace(self):
        """創建專業工作區 - 分頁式界面"""
        # 創建主容器
        main_container = QWidget()
        main_container.setObjectName("MainTabContainer")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 創建分頁容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("ProfessionalTabWidget")
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabsClosable(True)  # 啟用分頁關閉按鈕
        
        # 隱藏標籤欄
        self.tab_widget.tabBar().setVisible(False)
        print(f"[DEBUG] 標籤欄可見性設為: {self.tab_widget.tabBar().isVisible()}")
        print(f"[DEBUG] 標籤欄高度: {self.tab_widget.tabBar().height()}")
        
        # 強制更新標籤欄設置
        self.tab_widget.tabBar().hide()
        print(f"[DEBUG] 強制隱藏後標籤欄可見性: {self.tab_widget.tabBar().isVisible()}")
        
        # 連接分頁關閉信號
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # 創建分頁右側控制按鈕容器
        tab_buttons_container = QWidget()
        tab_buttons_container.setObjectName("TabButtonsContainer")
        tab_buttons_layout = QHBoxLayout(tab_buttons_container)
        tab_buttons_layout.setContentsMargins(2, 2, 2, 2)
        tab_buttons_layout.setSpacing(2)
        
        # 新增分頁按鈕
        add_tab_btn = QPushButton("+")
        add_tab_btn.setObjectName("AddTabButton")
        add_tab_btn.setFixedSize(25, 25)
        add_tab_btn.setToolTip("新增分頁")
        add_tab_btn.clicked.connect(self.add_new_tab)
        tab_buttons_layout.addWidget(add_tab_btn)
        
        # 關閉當前分頁按鈕
        close_tab_btn = QPushButton("X")
        close_tab_btn.setObjectName("CloseTabButton")
        close_tab_btn.setFixedSize(25, 25)
        close_tab_btn.setToolTip("關閉當前分頁")
        close_tab_btn.clicked.connect(self.close_current_tab)
        tab_buttons_layout.addWidget(close_tab_btn)
        
        # 將按鈕容器設置為分頁小部件的右上角
        self.tab_widget.setCornerWidget(tab_buttons_container, Qt.TopRightCorner)
        
        # [HIDE] 隱藏標籤按鈕容器（這就是用戶看到的"降雨分析 - 分析"）
        tab_buttons_container.setVisible(False)
        tab_buttons_container.hide()
        print(f"[TAB_DEBUG] TabButtonsContainer 已隱藏: {not tab_buttons_container.isVisible()}")
        
        # 隱藏的分頁數量標籤（保留以避免錯誤）
        self.tab_count_label = QLabel("分頁: 0")
        self.tab_count_label.setObjectName("TabCountLabel")
        self.tab_count_label.hide()  # 完全隱藏
        
        # 直接將分頁容器添加到主佈局
        main_layout.addWidget(self.tab_widget)
        
        # 初始化預設分頁
        self.init_default_tabs()
        
        return main_container
        
    def init_default_tabs(self):
        """初始化預設分頁 - 顯示歡迎畫面"""
        # 創建歡迎畫面作為預設主頁 (隱藏標題)
        welcome_tab = self.create_welcome_tab()
        welcome_tab.setObjectName("welcome_tab")  # 添加標識符
        self.tab_widget.addTab(welcome_tab, "")
        
        self.update_tab_count()
        
    def add_new_tab(self):
        """新增分頁"""
        # 獲取當前分頁數量以生成新的標題
        count = self.tab_widget.count() + 1
        tab_types = [
            ("[TELE] 單場賽事總攬", self.create_telemetry_analysis_tab),
            ("[LAP] 圈速比較", self.create_laptime_comparison_tab),
            ("[TRACK] 賽道分析", self.create_track_analysis_tab),
            ("[DATA] 數據總覽", self.create_data_overview_tab)
        ]
        
        # 輪流創建不同類型的分頁
        tab_type_index = (count - 1) % len(tab_types)
        tab_name, tab_creator = tab_types[tab_type_index]
        
        new_tab = tab_creator()
        self.tab_widget.addTab(new_tab, "")  # 隱藏標題
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
        self.update_tab_count()
        
    def close_tab(self, index):
        """關閉指定索引的分頁"""
        # 檢查是否為歡迎分頁（索引0）
        if index == 0:
            #print("[INFO] 歡迎分頁無法關閉")
            return
            
        if self.tab_widget.count() > 1:  # 保留至少一個分頁
            self.tab_widget.removeTab(index)
            self.update_tab_count()
        
    def close_current_tab(self):
        """關閉當前分頁"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)
    
    def _on_tab_changed(self, index):
        """分頁切換事件處理"""
        try:
            # 當切換分頁時，檢查並更新工具欄狀態
            self._check_and_update_toolbar_status()
        except Exception as e:
            print(f"[ERROR] 分頁切換處理失敗: {e}")
    
    def update_tab_count(self):
        """更新分頁數量顯示"""
        count = self.tab_widget.count()
        self.tab_count_label.setText(f"分頁: {count}")
        
    def check_and_hide_tabs(self):
        """檢查並強制隱藏標籤欄 - 簡化版本"""
        print("[TAB_HIDE] ⏰ 延遲檢查機制啟動 - 開始檢查標籤隱藏狀態...")
        print(f"[TAB_HIDE] 檢查標籤隱藏狀態...")
        print(f"[TAB_HIDE] QTabBar 可見性: {self.tab_widget.tabBar().isVisible()}")
        print(f"[TAB_HIDE] QTabBar 高度: {self.tab_widget.tabBar().height()}")
        
        # 確保隱藏
        self.tab_widget.tabBar().setVisible(False)
        self.tab_widget.tabBar().hide()
        self.tab_widget.tabBar().setFixedHeight(0)
        
        print(f"[TAB_HIDE] 隱藏後 QTabBar 高度: {self.tab_widget.tabBar().height()}")
        print(f"[TAB_HIDE] ✅ 標籤隱藏檢查完成")
        
    def second_tab_check(self):
        """第二次標籤檢查（延遲2秒後）- 簡化版本"""
        print(f"[TAB_HIDE] 延遲檢查 - QTabBar 可見性: {self.tab_widget.tabBar().isVisible()}")
        print(f"[TAB_HIDE] 延遲檢查 - QTabBar 高度: {self.tab_widget.tabBar().height()}")
        
    def third_tab_check(self):
        """第三次標籤檢查（延遲5秒後）- 簡化版本"""
        print(f"[TAB_HIDE] 最終檢查 - QTabBar 可見性: {self.tab_widget.tabBar().isVisible()}")
        print(f"[TAB_HIDE] 最終檢查 - QTabBar 高度: {self.tab_widget.tabBar().height()}")
        
        # 檢查 TabButtonsContainer 狀態
        corner_widget = self.tab_widget.cornerWidget(Qt.TopRightCorner)
        if corner_widget:
            print(f"[TAB_HIDE] TabButtonsContainer 可見性: {corner_widget.isVisible()}")
            print(f"[TAB_HIDE] TabButtonsContainer 大小: {corner_widget.size()}")
        print(f"[TAB_HIDE] 所有標籤隱藏檢查完成")
    
    # ==================== 同步功能實現 ====================
    
    def create_and_register_mdi_area(self, object_name):
        """創建MDI區域並自動註冊到主視窗"""
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName(object_name)
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 註冊到主視窗的MDI區域列表
        self.register_mdi_area(mdi_area)
        
        return mdi_area
    
    def register_mdi_area(self, mdi_area):
        """註冊MDI區域到主視窗（用於同步功能）"""
        print(f"[LINK] [DEBUG] 嘗試註冊MDI區域: {mdi_area.objectName() if mdi_area else 'None'}")
        print(f"[LINK] [DEBUG] 當前已註冊的MDI區域數量: {len(self.mdi_areas)}")
        print(f"[LINK] [DEBUG] 主視窗類型: {type(self).__name__}")
        
        if mdi_area not in self.mdi_areas:
            self.mdi_areas.append(mdi_area)
            print(f"[OK] [MDI] MDI區域已註冊: {mdi_area.objectName()}")
            print(f"[OK] [MDI] 註冊後MDI區域總數: {len(self.mdi_areas)}")
        else:
            print(f"[WARNING] [MDI] MDI區域已存在，跳過註冊: {mdi_area.objectName()}")
    
    def sync_to_all_mdi_subwindows(self, param_type, value):
        """同步參數到所有MDI子視窗"""
        print(f"[REFRESH] [SYNC] 開始同步 {param_type} = {value} 到所有MDI子視窗")
        print(f"[LINK] [SYNC] 已註冊的MDI區域數量: {len(self.mdi_areas)}")
        
        synced_count = 0
        for i, mdi_area in enumerate(self.mdi_areas):
            print(f"[SEARCH] [SYNC] 檢查MDI區域 {i+1}/{len(self.mdi_areas)}: {mdi_area.objectName()}")
            synced_count += self.sync_to_mdi_area(mdi_area, param_type, value)
        
        print(f"[OK] [SYNC] 完成同步，共更新 {synced_count} 個子視窗")
    
    def sync_to_mdi_area(self, mdi_area, param_type, value):
        """通知MDI區域內所有子視窗主頁面參數變更"""
        if not mdi_area:
            print(f"[WARNING] [SYNC] MDI區域為空，跳過通知")
            return 0
            
        notified_count = 0
        subwindow_list = mdi_area.subWindowList()
        print(f"[TEST] [SYNC] 向MDI區域 {mdi_area.objectName()} 的 {len(subwindow_list)} 個子視窗發送參數變更通知")
        
        for subwindow in subwindow_list:
            window_title = subwindow.windowTitle() if subwindow else "未知視窗"
            print(f"[TEST] [SYNC] 發送通知到子視窗: {window_title} ({param_type}={value})")
            
            # 總是發送通知，讓子視窗自己決定是否響應
            if hasattr(subwindow, 'receive_main_window_update_notification'):
                try:
                    subwindow.receive_main_window_update_notification(param_type, value)
                    notified_count += 1
                    print(f"[OK] [SYNC] 已發送通知到: {window_title}")
                except Exception as e:
                    print(f"[ERROR] [SYNC] 發送通知失敗: {window_title}, 錯誤: {e}")
            else:
                print(f"[WARNING] [SYNC] 子視窗 {window_title} 不支援通知機制")
        
        print(f"[STATS] [SYNC] MDI區域 {mdi_area.objectName()} 通知完成，共發送 {notified_count} 個通知")
        return notified_count
    
    # ==================== 同步功能實現結束 ====================
    
    def force_white_background(self, mdi_area):
        """深度修復QMdiArea背景問題 - 設定為白色"""
        #print(f"[DESIGN] DEBUG: force_white_background called for {mdi_area.objectName()}")
        
        # 方法1: 設置調色板
        mdi_area.setAutoFillBackground(True)
        palette = mdi_area.palette()
        palette.setColor(QPalette.Background, QColor(245, 245, 245))
        palette.setColor(QPalette.Base, QColor(245, 245, 245))
        palette.setColor(QPalette.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        mdi_area.setPalette(palette)
        #print(f"[OK] Palette set for {mdi_area.objectName()}")
        
        # 方法2: 直接設置背景畫筆
        mdi_area.setBackground(QBrush(QColor(245, 245, 245)))
        #print(f"[OK] Background brush set for {mdi_area.objectName()}")
        
        # 方法3: 設置viewport背景（QMdiArea內部使用QScrollArea）
        def fix_viewport():
            try:
                #print(f"[TOOL] Fixing viewport for {mdi_area.objectName()}")
                # 查找內部的viewport小部件
                child_count = 0
                for child in mdi_area.findChildren(QWidget):
                    if hasattr(child, 'setAutoFillBackground'):
                        child.setAutoFillBackground(True)
                        child_palette = child.palette()
                        child_palette.setColor(QPalette.Background, QColor(245, 245, 245))
                        child_palette.setColor(QPalette.Base, QColor(245, 245, 245))
                        child_palette.setColor(QPalette.Window, QColor(245, 245, 245))
                        child.setPalette(child_palette)
                        child_count += 1
                        
                #print(f"[PACKAGE] Fixed {child_count} child widgets")
                        
                # 特別處理viewport
                if hasattr(mdi_area, 'viewport'):
                    viewport = mdi_area.viewport()
                    if viewport:
                        viewport.setAutoFillBackground(True)
                        viewport_palette = viewport.palette()
                        viewport_palette.setColor(QPalette.Background, QColor(245, 245, 245))
                        viewport_palette.setColor(QPalette.Base, QColor(245, 245, 245))
                        viewport_palette.setColor(QPalette.Window, QColor(245, 245, 245))
                        viewport.setPalette(viewport_palette)
                        
                # 強制重繪整個MDI區域
                mdi_area.repaint()
            except:
                pass  # 忽略任何錯誤，繼續其他修復方法
        
        # 延遲執行viewport修復（等MDI完全初始化）
        QTimer.singleShot(100, fix_viewport)
        QTimer.singleShot(200, fix_viewport)  # 再次執行確保修復
        
        # 方法4: 強制內聯樣式
        mdi_area.setStyleSheet(f"""
            QMdiArea#{mdi_area.objectName()} {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
            QMdiArea#{mdi_area.objectName()} QScrollArea {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
            QMdiArea#{mdi_area.objectName()} QScrollArea QWidget {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
            QMdiArea#{mdi_area.objectName()} > QWidget {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
        """)
        
        # 方法5: 創建白色背景小部件覆蓋（終極方案）
        def create_white_overlay():
            try:
                # 創建一個白色背景小部件作為底層
                overlay = QWidget(mdi_area)
                overlay.setStyleSheet("background-color: #F5F5F5;")
                overlay.setGeometry(mdi_area.rect())
                overlay.lower()  # 放到最底層
                overlay.show()
                
                # 連接resize事件，確保覆蓋層始終填滿MDI區域
                def resize_overlay():
                    if overlay and not overlay.isHidden():
                        overlay.setGeometry(mdi_area.rect())
                
                mdi_area.resizeEvent = lambda event: (
                    QMdiArea.resizeEvent(mdi_area, event),
                    resize_overlay()
                )[-1]
                
            except:
                pass
        
        # 延遲創建覆蓋層
        QTimer.singleShot(300, create_white_overlay)
        
    def create_welcome_tab(self):
        """創建歡迎畫面分頁"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #E8E8E8;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 標題標籤
        title_label = QLabel("🏠 主頁面")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 關閉所有視窗按鈕
        close_all_btn = QPushButton(tr("close_all_windows", "Close All Windows"))
        close_all_btn.setFixedSize(130, 25)
        close_all_btn.setStyleSheet("""
            QPushButton {
                background: #FFE6E6;
                color: #CC0000;
                border: 1px solid #FFAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #FFCCCC;
                border: 1px solid #FF6666;
            }
            QPushButton:pressed {
                background: #FFB3B3;
            }
        """)
        
        # 重置按鈕
        reset_btn = QPushButton(tr("show_all_data", "Show All Data"))
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(close_all_btn)
        toolbar_layout.addWidget(reset_btn)
        
        # 添加工具欄到主布局
        tab_layout.addWidget(toolbar)
        
        # 創建歡迎內容區域和MDI區域的分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 歡迎內容區域
        welcome_widget = QWidget()
        welcome_widget.setFixedHeight(300)  # 固定高度
        welcome_widget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(50, 30, 50, 30)
        welcome_layout.setSpacing(20)
        
        # 主標題
        title_label = QLabel(tr("main_title", "[FINISH] F1 TelemetryStation Pro"))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        welcome_layout.addWidget(title_label)
        
        # 副標題
        subtitle_label = QLabel(tr("subtitle", "Professional F1 Data Analysis Platform"))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                background: transparent;
            }
        """)
        welcome_layout.addWidget(subtitle_label)
        
        # 歡迎信息
        info_label = QLabel(tr("welcome_info", "💡 Left click to select module • Right click to execute analysis • Support Ctrl/Shift multi-select batch analysis • Version 0.0"))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                background: transparent;
                padding: 15px;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
            }
        """)
        welcome_layout.addWidget(info_label)
        
        # 創建MDI工作區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("WelcomeMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 強制設置白色背景
        self.force_white_background(mdi_area)
        
        # 連接關閉所有視窗按鈕到關閉功能
        close_all_btn.clicked.connect(lambda: self.close_all_mdi_windows(mdi_area))
        
        # 連接重置按鈕到重置功能
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 將歡迎區域和MDI區域添加到分割器
        splitter.addWidget(welcome_widget)
        splitter.addWidget(mdi_area)
        splitter.setSizes([300, 600])  # 歡迎區域300px，MDI區域600px
        
        tab_layout.addWidget(splitter)
        return tab_container
        
    def create_data_overview_tab(self):
        """創建數據總覽分頁"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #E8E8E8;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton(tr("show_all_data", "Show All Data"))
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        # 標題標籤
        title_label = QLabel(tr("data_overview", "[STATS] Data Overview"))
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 關閉所有視窗按鈕
        from core.gui_i18n import tr
        close_all_btn = QPushButton(tr('close_all_windows', 'Close All Windows'))
        close_all_btn.setFixedSize(120, 25)
        close_all_btn.setStyleSheet("""
            QPushButton {
                background: #FFE6E6;
                color: #CC0000;
                border: 1px solid #FFAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #FFCCCC;
                border: 1px solid #FF6666;
            }
            QPushButton:pressed {
                background: #FFB3B3;
            }
        """)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton(tr("show_all_data", "Show All Data"))
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(close_all_btn)
        toolbar_layout.addWidget(reset_btn)
        
        # 創建MDI區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("OverviewMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 連接關閉所有視窗按鈕
        close_all_btn.clicked.connect(lambda: self.close_all_mdi_windows(mdi_area))
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 深度修復背景問題 - 多層次設置
        self.force_white_background(mdi_area)
        
        # 添加統計視窗
        stats_window = PopoutSubWindow(tr("statistics_data", "Statistics Data"), mdi_area)
        stats_content = QLabel(tr("season_statistics", "[CHART] Season Statistics\n• Total Laps: 1,247\n• Average Lap Time: 1:18.456\n• Fastest Lap: 1:16.123"))
        stats_content.setObjectName("StatsContent")
        stats_window.setWidget(stats_content)
        stats_window.resize(300, 200)  # 改為resize，允許調整大小
        mdi_area.addSubWindow(stats_window)
        stats_window.move(10, 10)
        stats_window.show()
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
        
    def create_telemetry_analysis_tab(self):
        """創建單場賽事總攬分頁"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #E8E8E8;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton(tr("show_all_data", "Show All Data"))
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("[CHART] 單場賽事總攬")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 關閉所有視窗按鈕
        from core.gui_i18n import tr
        close_all_btn = QPushButton(tr('close_all_windows', 'Close All Windows'))
        close_all_btn.setFixedSize(120, 25)
        close_all_btn.setStyleSheet("""
            QPushButton {
                background: #FFE6E6;
                color: #CC0000;
                border: 1px solid #FFAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #FFCCCC;
                border: 1px solid #FF6666;
            }
            QPushButton:pressed {
                background: #FFB3B3;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(close_all_btn)
        toolbar_layout.addWidget(reset_btn)
        
        # 創建 MDI 區域（使用新的註冊方法）
        mdi_area = self.create_and_register_mdi_area("TelemetryAnalysisMDI")
        
        # 連接關閉所有視窗按鈕
        close_all_btn.clicked.connect(lambda: self.close_all_mdi_windows(mdi_area))
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 深度修復背景問題 - 多層次設置
        self.force_white_background(mdi_area)
        
        # 1. 速度遙測曲線視窗 - 使用新的彈出式視窗
        speed_window = PopoutSubWindow("速度遙測 - VER vs LEC", mdi_area)
        speed_chart = TelemetryChartWidget("speed")
        speed_window.setWidget(speed_chart)
        speed_window.resize(500, 250)  # 改為resize
        mdi_area.addSubWindow(speed_window)
        #print(f"🏠 DEBUG: speed_window added to MDI, parent: {speed_window.parent()}")
        #print(f"[DESIGN] MDI QSS length after addSubWindow: {len(mdi_area.styleSheet())}")
        #print(f"[DESIGN] speed_window QSS length after addSubWindow: {len(speed_window.styleSheet())}")
        speed_window.move(10, 10)
        speed_window.show()
        
        # 2. 煞車遙測曲線視窗
        brake_window = PopoutSubWindow("煞車壓力 - 單場賽事總攬", mdi_area)
        brake_chart = TelemetryChartWidget("brake")
        brake_window.setWidget(brake_chart)
        brake_window.resize(500, 250)  # 改為resize
        mdi_area.addSubWindow(brake_window)
        brake_window.move(520, 10)
        brake_window.show()
        
        # 3. 節流閥遙測曲線視窗
        throttle_window = PopoutSubWindow("節流閥位置 - 油門控制", mdi_area)
        throttle_chart = TelemetryChartWidget("throttle")
        throttle_window.setWidget(throttle_chart)
        throttle_window.resize(400, 180)  # 改為resize
        mdi_area.addSubWindow(throttle_window)
        throttle_window.move(10, 270)
        throttle_window.show()
        
        # 4. 方向盤角度曲線視窗
        steering_window = PopoutSubWindow("方向盤角度 - 轉向分析", mdi_area)
        steering_chart = TelemetryChartWidget("steering")
        steering_window.setWidget(steering_chart)
        steering_window.resize(400, 180)  # 改為resize
        mdi_area.addSubWindow(steering_window)
        steering_window.move(520, 270)
        steering_window.show()
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
        
    def create_laptime_comparison_tab(self):
        """創建圈速比較分頁"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #E8E8E8;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton(tr("show_all_data", "Show All Data"))
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("[FINISH] 圈速比較")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 關閉所有視窗按鈕
        from core.gui_i18n import tr
        close_all_btn = QPushButton(tr('close_all_windows', 'Close All Windows'))
        close_all_btn.setFixedSize(120, 25)
        close_all_btn.setStyleSheet("""
            QPushButton {
                background: #FFE6E6;
                color: #CC0000;
                border: 1px solid #FFAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #FFCCCC;
                border: 1px solid #FF6666;
            }
            QPushButton:pressed {
                background: #FFB3B3;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(close_all_btn)
        toolbar_layout.addWidget(reset_btn)
        
        # 創建 MDI 區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("ProfessionalMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 連接關閉所有視窗按鈕
        close_all_btn.clicked.connect(lambda: self.close_all_mdi_windows(mdi_area))
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 圈速分析表格視窗
        lap_window = PopoutSubWindow("圈速分析 - 前10名", mdi_area)
        lap_content = self.create_lap_analysis_table()
        lap_window.setWidget(lap_content)
        lap_window.resize(500, 350)  # 改為resize
        mdi_area.addSubWindow(lap_window)
        lap_window.move(10, 10)
        lap_window.show()
        
        # 扇區比較圖表
        sector_window = PopoutSubWindow("扇區比較 - VER vs LEC", mdi_area)
        sector_chart = TelemetryChartWidget("speed")  # 重用遙測圖表
        sector_window.setWidget(sector_chart)
        sector_window.resize(500, 300)  # 改為resize
        mdi_area.addSubWindow(sector_window)
        sector_window.move(520, 10)
        sector_window.show()
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
        
    def create_track_analysis_tab(self):
        """創建賽道分析分頁 - 使用通用 TrackAnalysisUniversal 模組"""
        # 直接調用新的賽道分析視窗功能
        self.open_track_analysis_window()
        
        # 返回一個空的容器，以保持分頁結構的兼容性
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顯示提示信息
        info_label = QLabel("[FINISH] 賽道軌跡分析已在新視窗中開啟")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                font-weight: bold;
                padding: 20px;
                background: #F8F8F8;
                border: 2px dashed #CCCCCC;
                border-radius: 8px;
            }
        """)
        tab_layout.addWidget(info_label)
        
        # 添加說明文字
        desc_label = QLabel("""
        新的賽道軌跡分析功能已升級為獨立的 MDI 子視窗：
        
        [OK] 高效能 PyQtGraph 繪圖引擎
        [OK] 互動式賽道軌跡顯示
        [OK] 原點標記與位置點選擇
        [OK] 支援縮放、平移操作
        [OK] 與主視窗參數同步
        
        請在獨立視窗中使用新的分析功能。
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("""
            QLabel {
                color: #555555;
                font-size: 11px;
                padding: 10px;
                background: transparent;
                line-height: 1.4;
            }
        """)
        tab_layout.addWidget(desc_label)
        
        return tab_container
        
    def create_lap_analysis_table(self):
        """創建圈速分析表格"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        table = QTableWidget(10, 4)
        table.setObjectName("ProfessionalDataTable")
        table.setHorizontalHeaderLabels(["位置", "車手", "最佳圈速", "差距"])
        table.verticalHeader().setVisible(False)
        
        # 圈速分析數據
        data = [
            ("1", "VER", "1:29.347", "-"),
            ("2", "LEC", "1:29.534", "+0.187"),
            ("3", "HAM", "1:29.678", "+0.331"),
            ("4", "RUS", "1:29.892", "+0.545"),
            ("5", "NOR", "1:30.125", "+0.778"),
            ("6", "PIA", "1:30.234", "+0.887"),
            ("7", "SAI", "1:30.456", "+1.109"),
            ("8", "ALO", "1:30.567", "+1.220"),
            ("9", "OCO", "1:30.789", "+1.442"),
            ("10", "GAS", "1:30.912", "+1.565")
        ]
        
        for row, (pos, driver, time, gap) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(pos))
            table.setItem(row, 1, QTableWidgetItem(driver))
            table.setItem(row, 2, QTableWidgetItem(time))
            table.setItem(row, 3, QTableWidgetItem(gap))
            
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        return widget
        
    def create_professional_status_bar(self):
        """Create professional status bar."""
        status_bar = QStatusBar()
        status_bar.setFixedHeight(16)
        self.setStatusBar(status_bar)

        # Status indicators
        self.ready_label = QLabel('[READY] INITIALIZING')
        self.ready_label.setObjectName('StatusReady')

        self.api_status_label = QLabel('[API] Pending')
        self.api_status_label.setObjectName('StatusApi')
        self.api_status_label.setStyleSheet('color: #f1c40f; font-weight: bold;')
        self.cli_status_label = QLabel('[CLI] IDLE')
        self.cli_status_label.setObjectName('StatusCli')
        self.cli_status_label.setStyleSheet('color: #95a5a6; font-weight: bold;')
        self.cli_status_label.setToolTip('CLI 閒置，沒有正在執行的分析任務')

        self.time_label = QLabel(f"[TIME] {datetime.datetime.now().strftime('%H:%M:%S')}")
        self.time_label.setObjectName('StatusTime')

        status_bar.addWidget(self.ready_label)
        status_bar.addWidget(QLabel(' | '))
        status_bar.addWidget(self.api_status_label)
        status_bar.addWidget(QLabel(' | '))
        status_bar.addWidget(self.cli_status_label)
        status_bar.addWidget(QLabel(' | '))
        status_bar.addWidget(self.time_label)

        # Version information segment - 已移除右下角版本顯示

        # Refresh status information
        self.update_status_bar()


    def _determine_api_base_url(self) -> str:
        """Resolve the API base URL using the public endpoint enforcement."""

        def _log(message: str) -> None:
            logger.info("[API-URL] %s", message)

        return resolve_api_base_url(event_logger=_log)

    def setup_api_health_monitor(self) -> None:
        """Initialise the periodic API health checks and kick off the first probe."""
        try:
            self.api_base_url = self._determine_api_base_url()
            self._api_last_state = 'unknown'
            self.api_mode_enabled = False
            if self.api_status_label:
                self.api_status_label.setText('[API] CHECKING...')
                self.api_status_label.setStyleSheet('color: #f1c40f; font-weight: bold;')
                self.api_status_label.setToolTip(f'API Base: {self.api_base_url}\nChecking...')
            if self.ready_label:
                self.ready_label.setText('[READY] INITIALIZING')
            if self.api_health_timer:
                self.api_health_timer.stop()
            self.api_health_timer = QTimer(self)
            self.api_health_timer.setInterval(60_000)
            self.api_health_timer.timeout.connect(self.trigger_api_health_check)
            QTimer.singleShot(200, self.trigger_api_health_check)
            self.api_health_timer.start()
            self.setup_api_runtime_monitor()
        except Exception as exc:
            logger.error('Failed to setup API health monitor: %s', exc)
            if self.api_status_label:
                self.api_status_label.setText('[API] ERROR')
                self.api_status_label.setStyleSheet('color: #e74c3c; font-weight: bold;')
                self.api_status_label.setToolTip(str(exc))
            if self.cli_status_label:
                self.cli_status_label.setText('[CLI] UNKNOWN')
                self.cli_status_label.setStyleSheet('color: #c0392b; font-weight: bold;')
                self.cli_status_label.setToolTip(str(exc))

    def trigger_api_health_check(self, manual: bool = False) -> None:
        """Launch a background API health check."""
        if self._api_health_worker_active:
            if manual:
                QMessageBox.information(self, 'API Check', 'API health check is already running. Please wait.')
            return
        if not self.api_base_url:
            self.api_base_url = self._determine_api_base_url()
        self._api_health_worker_active = True
        self._api_health_manual_request = manual
        if self.api_status_label:
            self.api_status_label.setText('[API] CHECKING...')
            self.api_status_label.setStyleSheet('color: #f1c40f; font-weight: bold;')
            self.api_status_label.setToolTip(f'API Base: {self.api_base_url}\nChecking...')
        if self.check_api_action:
            self.check_api_action.setEnabled(False)
        logger.info('Starting API health check (manual=%s, base=%s)', manual, self.api_base_url)
        self._api_health_worker = ApiHealthWorker(self.api_base_url, manual=manual, parent=self)
        self._api_health_worker.result_ready.connect(self.on_api_health_result)
        self._api_health_worker.finished.connect(self.on_api_health_finished)
        self._api_health_worker.start()

    def on_api_health_result(self, result: dict) -> None:
        """Handle health check result coming back from the worker thread."""
        try:
            state = result.get('state', 'offline')
            manual = result.get('manual', False)
            base_url = result.get('base_url', self.api_base_url)
            details = [str(item) for item in result.get('details', [])]
            errors = [str(item) for item in result.get('errors', [])]
            latency = result.get('latency_ms')
            checked_at = result.get('checked_at')
            tooltip_lines = [f'API Base: {base_url}']
            if checked_at:
                tooltip_lines.append(f'Checked: {checked_at}')
            if latency is not None:
                tooltip_lines.append(f'Avg latency: {latency:.1f} ms')
            if details:
                tooltip_lines.extend(details)
            if errors:
                tooltip_lines.append('----')
                tooltip_lines.extend(errors)
            tooltip_text = '\n'.join(tooltip_lines)
            self._api_status_details = details
            if self.api_status_label:
                text_map = {
                    'online': '[API] ONLINE',
                    'degraded': '[API] DEGRADED',
                    'offline': '[API] OFFLINE',
                }
                color_map = {
                    'online': '#2ecc71',
                    'degraded': '#f1c40f',
                    'offline': '#e74c3c',
                }
                self.api_status_label.setText(text_map.get(state, '[API] UNKNOWN'))
                self.api_status_label.setStyleSheet(f"color: {color_map.get(state, '#95a5a6')}; font-weight: bold;")
                self.api_status_label.setToolTip(tooltip_text)
            if self.ready_label:
                if state == 'online':
                    self.ready_label.setText('[READY] API MODE')
                elif state == 'degraded':
                    self.ready_label.setText('[READY] API MODE (DEGRADED)')
                else:
                    self.ready_label.setText('[READY] LOCAL JSON MODE')
            self.api_mode_enabled = state != 'offline'
            previous_state = getattr(self, '_api_last_state', 'unknown')
            self._api_last_state = state
            message_title = {
                'online': 'API Online',
                'degraded': 'API Degraded',
                'offline': 'API Offline',
            }.get(state, 'API Status')
            if manual:
                if state == 'online':
                    QMessageBox.information(self, message_title, tooltip_text)
                elif state == 'degraded':
                    QMessageBox.warning(self, message_title, tooltip_text)
                else:
                    QMessageBox.warning(self, message_title, tooltip_text)
            else:
                if state == 'offline' and previous_state != 'offline':
                    QMessageBox.warning(self, message_title, tooltip_text)
                elif state == 'online' and previous_state in ('offline', 'degraded'):
                    QMessageBox.information(self, 'API Restored', tooltip_text)
                elif state == 'degraded' and previous_state == 'online':
                    QMessageBox.warning(self, message_title, tooltip_text)
            if state == 'offline':
                logger.warning('API health check failed: %s', errors or details)
            elif state == 'degraded':
                logger.warning('API health degraded: %s', errors or details)
            else:
                logger.info('API health online (latency=%s ms)', latency)
        except Exception as exc:
            logger.error('Error processing API health result: %s', exc)
        finally:
            if self.check_api_action:
                self.check_api_action.setEnabled(True)

    def on_api_health_finished(self) -> None:
        self._api_health_worker_active = False
        self._api_health_worker = None
        if self.check_api_action:
            self.check_api_action.setEnabled(True)

    def manual_api_health_check(self) -> None:
        """Slot wired to the Tools menu to trigger manual health checks."""
        self.trigger_api_health_check(manual=True)

    def setup_api_runtime_monitor(self) -> None:
        """Initialise the periodic polling of the CLI runtime status."""
        try:
            if not self.api_base_url:
                return
            if self.api_runtime_timer:
                self.api_runtime_timer.stop()
                self.api_runtime_timer.deleteLater()
            self.api_runtime_timer = QTimer(self)
            self.api_runtime_timer.setInterval(5_000)
            self.api_runtime_timer.timeout.connect(self.trigger_api_runtime_poll)
            QTimer.singleShot(500, self.trigger_api_runtime_poll)
            self.api_runtime_timer.start()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning('Failed to setup API runtime monitor: %s', exc)

    def trigger_api_runtime_poll(self) -> None:
        """Kick off a single runtime poll if no worker is currently running."""
        if self._api_runtime_worker_active or not self.api_base_url:
            return

        try:
            self._api_runtime_worker_active = True
            self._api_runtime_worker = ApiRuntimeWorker(self.api_base_url, parent=self)
            self._api_runtime_worker.result_ready.connect(self.on_api_runtime_result)
            self._api_runtime_worker.finished.connect(self.on_api_runtime_finished)
            self._api_runtime_worker.start()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error('Failed to start API runtime worker: %s', exc)
            self._api_runtime_worker_active = False

    def on_api_runtime_result(self, summary: dict) -> None:
        """Handle runtime status payloads and update the CLI indicator."""
        try:
            if not self.cli_status_label:
                return

            if summary.get('ok'):
                payload = summary.get('payload')
                view = self._runtime_status_resolver.resolve(payload)
            else:
                error_text = summary.get('error') or '無法取得 CLI 狀態'
                view = RuntimeStatusView(
                    state=RuntimeStatusState.UNKNOWN,
                    label='[CLI] UNKNOWN',
                    color='#c0392b',
                    tooltip=error_text,
                    active_task_count=0,
                )

            self._apply_cli_status_view(view)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error('Failed to process runtime summary: %s', exc)
            fallback = RuntimeStatusView(
                state=RuntimeStatusState.UNKNOWN,
                label='[CLI] UNKNOWN',
                color='#c0392b',
                tooltip=str(exc),
                active_task_count=0,
            )
            self._apply_cli_status_view(fallback)

    def _apply_cli_status_view(self, view: RuntimeStatusView) -> None:
        if not self.cli_status_label:
            return

        signature = (view.label, view.color, view.tooltip)
        if signature == self._last_cli_status_signature:
            return

        self.cli_status_label.setText(view.label)
        self.cli_status_label.setStyleSheet(f'color: {view.color}; font-weight: bold;')
        self.cli_status_label.setToolTip(view.tooltip)
        self._last_cli_status_signature = signature

    def on_api_runtime_finished(self) -> None:
        self._api_runtime_worker_active = False
        self._api_runtime_worker = None


    def update_status_bar(self):
        """更新狀態列 (只維護時間與同步視窗標題)。"""
        if hasattr(self, 'time_label') and self.time_label is not None:
            self.time_label.setText(f"[TIME] {datetime.datetime.now().strftime('%H:%M:%S')}")

        if hasattr(self, 'year_combo') and hasattr(self, 'race_combo') and hasattr(self, 'session_combo'):
            try:
                self.update_all_window_titles()
            except Exception as exc:
                logger.debug('update_all_window_titles failed: %s', exc)

    def get_current_parameters(self):
        """獲取當前參數設定"""
        display_race = self.race_combo.currentText() if hasattr(self, 'race_combo') else 'Japan'
        fastf1_race = self.get_fastf1_race_name(display_race)  # 轉換為 FastF1 期望的名稱
        
        return {
            'year': self.year_combo.currentText() if hasattr(self, 'year_combo') else '2025',
            'race': fastf1_race,  # 使用轉換後的名稱
            'session': self.session_combo.currentText() if hasattr(self, 'session_combo') else 'R'
        }
    
    def format_window_title(self, module_name):
        """格式化視窗標題為: 模組名稱_年分_賽事_賽段"""
        params = self.get_current_parameters()
        return f"{module_name}_{params['year']}_{params['race']}_{params['session']}"
    
    def update_all_window_titles(self):
        """更新所有子窗口的標題為新格式"""
        try:
            # 查找所有 MDI 區域
            for child in self.findChildren(CustomMdiArea):
                if child:
                    # 遍歷所有子窗口
                    for subwindow in child.subWindowList():
                        if isinstance(subwindow, PopoutSubWindow):
                            # 從當前標題提取模組名稱 (簡化提取邏輯)
                            current_title = subwindow.windowTitle()
                            if current_title and '_' in current_title:
                                # 如果已經是新格式，提取模組名稱
                                module_name = current_title.split('_')[0]
                            elif current_title:
                                # 如果是舊格式，直接使用
                                module_name = current_title.replace(' - 分析', '')
                            else:
                                # 如果沒有標題，跳過
                                continue
                            
                            # 生成新標題並更新
                            new_title = self.format_window_title(module_name)
                            subwindow.setWindowTitle(new_title)
                            
                            # 如果有自定義標題欄，也更新它
                            if hasattr(subwindow, 'title_bar') and subwindow.title_bar:
                                subwindow.title_bar.update_title(new_title)
                            
                            print(f"[TITLE] 更新子窗口標題: {module_name} -> {new_title}")
        except Exception as e:
            print(f"[ERROR] 更新標題時發生錯誤: {e}")
        
    def check_and_remove_welcome_page(self):
        """檢查並移除歡迎頁面，創建新的分析分頁"""
        # 檢查第一個分頁是否為歡迎頁面 (通過objectName識別)
        if self.tab_widget.count() > 0:
            first_tab_widget = self.tab_widget.widget(0)
            if first_tab_widget and first_tab_widget.objectName() == "welcome_tab":
                #print("[REFRESH] 首次使用分析功能，移除歡迎頁面並創建新分頁")
                
                # 移除歡迎分頁
                self.tab_widget.removeTab(0)
                
                # 創建新的空白分析分頁 (隱藏標題)
                analysis_tab = self.create_empty_analysis_tab()
                self.tab_widget.addTab(analysis_tab, "")
                self.tab_widget.setCurrentIndex(0)
                
                # 更新分頁計數
                self.update_tab_count()
                
                #print("[OK] 已創建新的分析工作區")
                
    def create_empty_analysis_tab(self):
        """創建空白的分析分頁，只包含MDI區域"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #F0F0F0;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 標題標籤
        from core.gui_i18n import tr
        title_label = QLabel(tr('analysis_workspace', 'Analysis Workspace'))
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 關閉所有視窗按鈕
        from core.gui_i18n import tr
        close_all_btn = QPushButton(tr('close_all_windows', 'Close All Windows'))
        close_all_btn.setFixedSize(120, 25)
        close_all_btn.setStyleSheet("""
            QPushButton {
                background: #FFE6E6;
                color: #CC0000;
                border: 1px solid #FFAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #FFCCCC;
                border: 1px solid #FF6666;
            }
            QPushButton:pressed {
                background: #FFB3B3;
            }
        """)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton(tr("show_all_data", "Show All Data"))
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #F8F8F8;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #E8E8E8;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #DDDDDD;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        
        # 添加分隔符
        separator = QLabel("|")
        separator.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        toolbar_layout.addWidget(separator)
        
        # 創建動態狀態信息區域
        self.toolbar_status_widget = self._create_toolbar_status_widget()
        toolbar_layout.addWidget(self.toolbar_status_widget)
        
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(close_all_btn)
        toolbar_layout.addWidget(reset_btn)
        
        # 創建空白的MDI區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("AnalysisMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # [TOOL] 修復: 註冊MDI區域到主視窗
        self.register_mdi_area(mdi_area)
        print(f"[OK] [MDI] 已註冊分析MDI區域: {mdi_area.objectName()}")
        
        # 連接關閉所有視窗按鈕
        close_all_btn.clicked.connect(lambda: self.close_all_mdi_windows(mdi_area))
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 強制設置白色背景
        self.force_white_background(mdi_area)
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
    
    def _create_toolbar_status_widget(self) -> QWidget:
        """創建工具欄狀態信息小部件"""
        status_container = QWidget()
        status_container.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        
        layout = QHBoxLayout(status_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 模組名稱標籤
        self.toolbar_module_label = QLabel("")
        self.toolbar_module_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(self.toolbar_module_label)
        
        # 圈時間標籤
        self.toolbar_lap_time_label = QLabel("")
        self.toolbar_lap_time_label.setStyleSheet("""
            QLabel {
                color: #D84315;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(self.toolbar_lap_time_label)
        
        # 輪胎配方標籤
        self.toolbar_tyre_label = QLabel("")
        self.toolbar_tyre_label.setStyleSheet("""
            QLabel {
                color: #388E3C;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(self.toolbar_tyre_label)
        
        # 圈數標籤
        self.toolbar_lap_numbers_label = QLabel("")
        self.toolbar_lap_numbers_label.setStyleSheet("""
            QLabel {
                color: #7B1FA2;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(self.toolbar_lap_numbers_label)
        
        # 初始隱藏
        status_container.setVisible(False)
        
        return status_container
    
    def update_toolbar_status(self, module_name: str = "", lap_time: str = "", 
                            tyre_compound: str = "", lap_numbers: str = ""):
        """更新工具欄狀態信息"""
        try:
            if hasattr(self, 'toolbar_status_widget'):
                # 如果沒有模組名稱，隱藏狀態區域
                if not module_name:
                    self.toolbar_status_widget.setVisible(False)
                    return
                
                # 更新模組名稱標籤
                self.toolbar_module_label.setText(f"📊 {module_name}")
                
                # 更新圈時間標籤
                if lap_time:
                    self.toolbar_lap_time_label.setText(f"⏱️ {lap_time}")
                    self.toolbar_lap_time_label.setVisible(True)
                else:
                    self.toolbar_lap_time_label.setVisible(False)
                
                # 更新輪胎配方標籤
                if tyre_compound:
                    self.toolbar_tyre_label.setText(f"🏎️ {tyre_compound}")
                    self.toolbar_tyre_label.setVisible(True)
                else:
                    self.toolbar_tyre_label.setVisible(False)
                
                # 更新圈數標籤
                if lap_numbers:
                    self.toolbar_lap_numbers_label.setText(f"🏁 {lap_numbers}")
                    self.toolbar_lap_numbers_label.setVisible(True)
                else:
                    self.toolbar_lap_numbers_label.setVisible(False)
                
                # 顯示狀態區域
                self.toolbar_status_widget.setVisible(True)
                
                print(f"[TOOLBAR_STATUS] 已更新: {module_name} | {lap_time} | {tyre_compound} | {lap_numbers}")
                
        except Exception as e:
            print(f"[ERROR] 更新工具欄狀態失敗: {e}")
    
    def clear_toolbar_status(self):
        """清除工具欄狀態信息"""
        self.update_toolbar_status("")
        
    def create_analysis_window(self, function_name):
        """為功能樹的分析項目創建新視窗 - 升級支援模組化架構"""
        print(f"[DEBUG] [CREATE_WINDOW] =============== 開始創建分析視窗 ===============")
        print(f"[DEBUG] [CREATE_WINDOW] 功能名稱: '{function_name}'")
        print(f"[DEBUG] [CREATE_WINDOW] 將嘗試調用 _create_analysis_module...")
        
        # 檢查是否為首次使用分析功能
        self.check_and_remove_welcome_page()
        
        # ✅ 優先檢查：理想圈分析（避免被 "Lap Analysis" 誤判）
        is_ideal_lap_analysis = (
            ("理想圈分析" in function_name)
            or ("Ideal Lap Analysis" in function_name)
            or ("理想ラップ分析" in function_name)
        )

        if is_ideal_lap_analysis:
            print(f"[IDEAL_LAP] 🏁 檢測到理想圈分析請求: {function_name}")
            
            # 顯示選項對話框
            ideal_lap_selection = self._prompt_ideal_lap_options()
            if ideal_lap_selection is None:
                print("[IDEAL_LAP] 使用者取消理想圈分析選項對話框")
                return
            if not ideal_lap_selection:
                print("[IDEAL_LAP] 未選擇任何理想圈分析模組")
                return

            print(f"[IDEAL_LAP] ✅ 使用者選擇了 {len(ideal_lap_selection)} 個分析類型: {ideal_lap_selection}")
            
            # 查找當前分頁中的 MDI 區域（與 detailed lap 相同方式）
            current_tab = self.tab_widget.currentWidget()
            if not current_tab:
                print("[IDEAL_LAP] ❌ 無法取得當前分頁")
                return
                
            mdi_area = None
            if isinstance(current_tab, CustomMdiArea):
                mdi_area = current_tab
            else:
                for child in current_tab.findChildren(CustomMdiArea):
                    mdi_area = child
                    break
                    
            if mdi_area is None:
                print("[IDEAL_LAP] ❌ 無法找到 MDI 區域")
                return
            
            # 獲取當前參數
            current_year = self.get_selected_year()
            current_race = self.get_selected_race_key()
            current_session = self.get_selected_session_code()
            print(f"[IDEAL_LAP] 📋 賽事參數: {current_year} {current_race} {current_session}")
            
            from modules.gui.ideal_lap_analysis.ideal_lap_options_dialog import IdealLapAnalysisOptionsDialog
            
            # 為每個選擇的分析類型創建視窗
            for analysis_type in ideal_lap_selection:
                print(f"[IDEAL_LAP] 🚀 創建分析視窗: {analysis_type}")
                
                try:
                    if analysis_type == IdealLapAnalysisOptionsDialog.TYPE_RANKING_TABLE:
                        # 創建排名表格模組
                        self._create_ideal_lap_ranking_window(
                            mdi_area,
                            current_year,
                            current_race,
                            current_session
                        )
                    
                    elif analysis_type == IdealLapAnalysisOptionsDialog.TYPE_SECTOR_HEATMAP:
                        print(f"[IDEAL_LAP] ⚠️ 分段熱力圖模組尚未實作")
                        QMessageBox.information(
                            self,
                            "開發中",
                            "分段熱力圖模組尚未實作\n請等待後續版本更新"
                        )
                    
                    elif analysis_type == IdealLapAnalysisOptionsDialog.TYPE_SECTOR_COMPARISON:
                        print(f"[IDEAL_LAP] ⚠️ 分段比較模組尚未實作")
                        QMessageBox.information(
                            self,
                            "開發中",
                            "分段比較模組尚未實作\n請等待後續版本更新"
                        )
                    
                except Exception as e:
                    print(f"[IDEAL_LAP] ❌ 創建分析視窗失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(
                        self,
                        "錯誤",
                        f"創建理想圈分析視窗時發生錯誤:\n{str(e)}"
                    )
            
            return
        
        # 特殊處理：遙測/圈速分析概覽直接調用 lap_analysis 方法（排除詳細圈速分析）
        is_detailed_lap = (
            ("詳細圈速分析" in function_name)
            or ("Detailed Lap Analysis" in function_name)
            or ("詳細ラップ分析" in function_name)
        )
        if (not is_detailed_lap) and (
            ("圈速" in function_name)
            or ("遙測分析" in function_name)
            or ("Telemetry Analysis" in function_name)
            or ("Lap Analysis" in function_name)
            or ("ラップ分析" in function_name)
        ):
            print(f"[遙測分析] 檢測到遙測分析請求: {function_name}")
            self.lap_analysis()
            return

        is_throttle_overview = (
            ("油門分析" in function_name)
            or ("Throttle Analysis" in function_name)
            or ("スロットル分析" in function_name)
        )

        if is_throttle_overview:
            throttle_selection = self._prompt_throttle_analysis_options()

            if throttle_selection is None:
                print("[THROTTLE] 使用者取消油門分析選項對話框")
                return

            if throttle_selection.get("line_chart"):
                self._show_throttle_line_chart_placeholder()

            if throttle_selection.get("box_plot"):
                function_name = tr("throttle_box_plot", "Throttle Box Plot")
            else:
                print("[THROTTLE] 未選擇任何可用的油門分析模組，結束建立流程")
                return

        # 獲取當前活動的分頁
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        
        # 首先檢查當前分頁是否本身就是MDI區域
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            # 否則在分頁的子元件中查找
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
            
        if mdi_area is None:
            #print(f"[警告] 無法找到MDI區域來添加視窗: {function_name}")
            return

        current_year = self.year_combo.currentText()
        current_race = self.race_combo.currentText()
        current_session = self.session_combo.currentText()
        
        # 🔧 [FIX] 重複視窗檢查機制 - 防止創建多個相同視窗
        # 步驟1: 獲取預期的視窗標題模式
        expected_title_patterns = self._get_expected_window_title_pattern(
            function_name, 
            current_year, 
            current_race, 
            current_session
        )
        
        # 步驟2: 檢查MDI區域中是否已存在相同視窗
        existing_window = self._find_existing_window(mdi_area, expected_title_patterns)
        
        if existing_window:
            # 找到已存在的視窗，聚焦而不是創建新視窗
            logger.info(f"[DUPLICATE_CHECK] ✅ 找到已存在視窗: {existing_window.windowTitle()}")
            logger.info(f"[DUPLICATE_CHECK] ⏭️ 跳過創建，將聚焦現有視窗")
            
            # 激活並聚焦現有視窗
            mdi_area.setActiveSubWindow(existing_window)
            existing_window.show()
            existing_window.raise_()
            existing_window.setFocus()
            
            return  # 🚫 不創建新視窗，直接返回
        
        logger.info(f"[DUPLICATE_CHECK] ✅ 未找到重複視窗，繼續創建: {function_name}")

        detailed_lap_selection = {"detail_table": True, "box_plot": False}
        if is_detailed_lap:
            selection = self._prompt_detailed_lap_options()
            if selection is None:
                print("[DETAILED_LAP] 使用者取消了詳細圈速分析選項對話框")
                return
            detailed_lap_selection = selection

            if detailed_lap_selection.get("box_plot"):
                self._create_detailed_lap_boxplot_window(
                    mdi_area,
                    current_year,
                    current_race,
                    current_session,
                )

            if not detailed_lap_selection.get("detail_table"):
                print("[DETAILED_LAP] 僅選擇圈速箱型圖，跳過詳細圈速模組視窗建立")
                return

        # [TOOL] 新增：嘗試使用模組化架構
        analysis_module = self._create_analysis_module(function_name)
        
        if analysis_module:
            # [FIX] 獲取當前參數，類似賽道分析模組
            current_year_value = current_year or self.year_combo.currentText()
            current_race_value = current_race or self.race_combo.currentText()
            current_session_value = current_session or self.session_combo.currentText()
            
            # 🔧 [CRITICAL FIX] 清理 race 名稱，移除日期後綴
            # 例如: "Australia (2025-03-16)" → "Australia"
            clean_race_value = self._get_race_key_from_display(current_race_value)
            print(f"[TITLE] [CLEAN] 清理 race 名稱: '{current_race_value}' → '{clean_race_value}'")
            
            # 使用 get_window_title 方法並傳入當前參數
            if hasattr(analysis_module, 'get_window_title'):
                window_title = analysis_module.get_window_title(
                    current_year_value,
                    clean_race_value,  # 🔧 使用清理後的 race 名稱
                    current_session_value,
                )
                print(f"[TITLE] [FIX] 使用當前參數生成標題: {window_title}")
            else:
                window_title = analysis_module.get_title()
                print(f"[TITLE] [FALLBACK] 使用預設標題: {window_title}")
                
            analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
            
            # 設置模組的widget
            content_widget = analysis_module.get_widget()
            analysis_window.setWidget(content_widget)
            
            # [REMOVED] 不再需要重新設置標題，因為已經使用 get_window_title 設置正確標題
            print(f"[TITLE] [OK] 視窗標題已設置為: {window_title}")
            
            # 使用模組推薦的尺寸
            width, height = analysis_module.get_default_size()
            analysis_window.resize(width, height)
            
            print(f"[OK] [MODULE] 使用模組化架構創建視窗: {analysis_window.windowTitle()}")
            
        else:
            # [TOOL] 保留：舊版相容性邏輯
            window_title = self.format_window_title(self._extract_module_name(function_name))
            analysis_window = PopoutSubWindow(window_title, mdi_area)
            
            # 舊版內容創建邏輯
            legacy_result = self._create_legacy_content(function_name)
            
            # 檢查是否返回了模組實例（進站分析等新版模組）
            if isinstance(legacy_result, tuple) and len(legacy_result) == 2:
                content_widget, analysis_module = legacy_result
                analysis_window.setWidget(content_widget)
                analysis_window.analysis_module = analysis_module  # 設置模組引用
                print(f"[OK] [LEGACY] 設置分析模組到視窗: {analysis_module.__class__.__name__}")
            else:
                content_widget = legacy_result
                analysis_window.setWidget(content_widget)
            
            # 舊版尺寸設定
            if "降雨分析" in function_name:
                analysis_window.resize(800, 600)
            elif "進站分析" in function_name:
                analysis_window.resize(1200, 800)  # 進站分析使用較大尺寸，充分利用MDI區域
            else:
                analysis_window.resize(450, 280)
            
            print(f"[WARNING] [LEGACY] 使用舊版架構創建視窗: {window_title}")

        # 通用視窗設定
        mdi_area.addSubWindow(analysis_window)
        print(f"[OK] [MDI] 已創建MDI子視窗: {analysis_window.windowTitle()}")
        
        # 連接關閉信號 - 確保視窗關閉時從追蹤列表移除
        if hasattr(analysis_window, 'window_closed'):
            analysis_window.window_closed.connect(lambda: self.on_subwindow_closed(analysis_window))
        
        # 添加到追蹤列表
        if hasattr(self, 'active_subwindows'):
            self.active_subwindows.append(analysis_window)
        
        analysis_window.show()
        
        # 計算新視窗位置（避免重疊）
        self._position_subwindow(mdi_area, analysis_window)
    
    def _get_expected_window_title_pattern(self, function_name, year, race, session):
        """
        根據功能名稱和參數生成預期的視窗標題模式
        
        參數:
            function_name: str - 功能名稱（可能是多語言）
            year: str - 年份
            race: str - 賽事名稱
            session: str - 賽段
        
        返回:
            list[str] - 可能的視窗標題模式（支援萬用字元）
        """
        # 清理 race 參數（移除日期後綴）
        race_clean = self._get_race_key_from_display(race)
        
        # 模組名稱映射表（支援多語言）
        module_mapping = {
            "Pitstop Analysis": ["Pitstop Analysis", "ピットストップ分析", "進站分析"],
            "Accident Analysis": ["Accident Analysis", "事故分析"],
            "Track Analysis": ["Track Analysis", "トラック分析", "賽道分析"],
            "Rain Analysis": ["Rain Analysis", "降雨分析", "雨況分析", "Rain Weather Analysis"],
            "Tire Analysis": ["Tire Analysis", "タイヤ分析", "輪胎分析"],
            "Speed Analysis": ["Speed Analysis", "速度分析"],
            "Brake Analysis": ["Brake Analysis", "ブレーキ分析", "煞車分析"],
            "Throttle Analysis": ["Throttle Analysis", "スロットル分析", "油門分析"],
            "Gear Analysis": ["Gear Analysis", "ギア分析", "檔位分析"],
            "RPM Analysis": ["RPM Analysis", "RPM分析"],
            "Acceleration Analysis": ["Acceleration Analysis", "アクセラレーション分析", "加速度分析"],
        }
        
        # 查找匹配的模組類型
        for key, aliases in module_mapping.items():
            for alias in aliases:
                if alias in function_name:
                    # 🔧 [FIX] 生成所有可能的標題格式（使用萬用字元匹配日期變化）
                    patterns = []
                    for name_variant in aliases:
                        # 格式1: "ModuleName_YYYY_Race*_Session" (包含空格和括號的日期)
                        patterns.append(f"{name_variant}_{year}_{race_clean}*_{session}")
                        # 格式2: "ModuleName - YYYY Race*Session" (包含空格)
                        patterns.append(f"{name_variant} - {year} {race_clean}*{session}")
                        # 格式3: "ModuleName_YYYY_Race (YYYY-MM-DD)_Session" (實際格式)
                        patterns.append(f"{name_variant}_{year}_{race_clean} *_{session}")
                        # 格式4: 只匹配核心部分，忽略日期細節
                        patterns.append(f"{name_variant}_{year}_{race_clean}*")
                    
                    logger.debug(f"[PATTERN_GEN] 為 '{function_name}' 生成 {len(patterns)} 個標題模式")
                    logger.debug(f"[PATTERN_GEN] 模式範例: {patterns[0]}")
                    return patterns
        
        # 無法判斷模組類型，返回基於功能名稱的通用模式
        logger.debug(f"[PATTERN_GEN] 無法匹配模組類型，使用通用模式: {function_name}")
        return [f"{function_name}*{year}*{race_clean}*{session}"]
    
    def _find_existing_window(self, mdi_area, title_patterns):
        """
        在MDI區域中查找匹配標題模式的現有視窗
        
        參數:
            mdi_area: CustomMdiArea - MDI區域
            title_patterns: list[str] - 標題模式列表（支援萬用字元 * 和 ?）
        
        返回:
            QMdiSubWindow 或 None - 找到的第一個匹配視窗
        """
        import fnmatch
        
        # 確保 title_patterns 是列表
        if isinstance(title_patterns, str):
            title_patterns = [title_patterns]
        
        # 🔍 [DEBUG] 記錄所有現有視窗
        existing_windows = mdi_area.subWindowList()
        logger.info(f"[DUPLICATE_CHECK] 🔍 當前 MDI 區域有 {len(existing_windows)} 個視窗")
        for i, win in enumerate(existing_windows, 1):
            logger.info(f"[DUPLICATE_CHECK]   視窗{i}: '{win.windowTitle()}'")
        
        # 🔍 [DEBUG] 記錄要匹配的模式
        logger.info(f"[DUPLICATE_CHECK] 🎯 要匹配的模式共 {len(title_patterns)} 個:")
        for i, pattern in enumerate(title_patterns, 1):
            logger.info(f"[DUPLICATE_CHECK]   模式{i}: '{pattern}'")
        
        # 遍歷所有子視窗
        for sub_window in existing_windows:
            window_title = sub_window.windowTitle()
            
            # 檢查是否匹配任一模式
            for pattern in title_patterns:
                if fnmatch.fnmatch(window_title, pattern):
                    logger.info(f"[DUPLICATE_CHECK] ✅ 找到匹配視窗!")
                    logger.info(f"[DUPLICATE_CHECK]   視窗標題: '{window_title}'")
                    logger.info(f"[DUPLICATE_CHECK]   匹配模式: '{pattern}'")
                    return sub_window
        
        logger.info(f"[DUPLICATE_CHECK] ❌ 未找到匹配視窗")
        return None
    
    def _mark_module_factory_type(self, module, module_type):
        """為模組標記工廠類型以支援工作區還原"""
        if module and module_type:
            try:
                setattr(module, "_factory_module_type", module_type)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Unable to tag module with factory type %s: %s", module_type, exc)
        return module

    def _prompt_throttle_analysis_options(self):
        """顯示油門分析選項並回傳使用者選擇。"""
        try:
            from modules.gui.Throttle_analysis.throttle_analysis_options_dialog import (
                ThrottleAnalysisOptionsDialog,
            )
        except ImportError as exc:
            print(f"[THROTTLE] 無法載入油門分析選項對話框: {exc}")
            return {"box_plot": True, "line_chart": False}

        dialog = ThrottleAnalysisOptionsDialog(self)
        result = dialog.exec_()

        if result != QDialog.Accepted:
            return None

        selected_types = dialog.get_selected_types()
        selection = {
            "box_plot": ThrottleAnalysisOptionsDialog.TYPE_BOX_PLOT in selected_types,
            "line_chart": ThrottleAnalysisOptionsDialog.TYPE_LINE_CHART in selected_types,
        }

        if not selection["box_plot"] and not selection["line_chart"]:
            selection["box_plot"] = True

        print(f"[THROTTLE] 選項結果: {selection}")
        return selection

    def _show_throttle_line_chart_placeholder(self):
        """顯示油門折線圖（現已實現）"""
        # 改為直接調用實際的油門折線圖模組
        self._create_throttle_line_chart_window()

    def _create_throttle_line_chart_window(self):
        """創建油門折線圖分析視窗"""
        print("[THROTTLE_LINE] 開始創建油門折線圖視窗...")
        
        # 獲取當前參數
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            print("[THROTTLE_LINE] 錯誤: 無活動分頁")
            QMessageBox.warning(self, "錯誤", "無活動分頁")
            return

        # 🔧 修復：使用 MainWindowParameterProvider 獲取參數（參考其他模組）
        parameter_provider = MainWindowParameterProvider(self)
        current_year = parameter_provider.get_current_year()
        current_race = parameter_provider.get_current_race()
        current_session = parameter_provider.get_current_session()

        if not all([current_year, current_race, current_session]):
            print(f"[THROTTLE_LINE] 錯誤: 參數不完整 Year={current_year}, Race={current_race}, Session={current_session}")
            QMessageBox.warning(
                self,
                "參數錯誤",
                "無法獲取當前年份、賽事或會話資訊\n請先選擇賽事資料"
            )
            return

        print(f"[THROTTLE_LINE] 參數: {current_year} {current_race} {current_session}")

        # 獲取 MDI 區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break

        if mdi_area is None:
            print("[THROTTLE_LINE] 錯誤: 找不到MDI區域")
            QMessageBox.warning(self, "錯誤", "找不到MDI區域")
            return

        print("[THROTTLE_LINE] 開始創建油門折線圖模組...")

        try:
            from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import (
                ThrottleLineChartModule,
            )

            # 設置當前參數
            try:
                year_int = int(current_year)
            except (TypeError, ValueError):
                year_int = current_year

            print(f"[THROTTLE_LINE] 模組參數: {year_int} {current_race} {current_session}")

            # 創建模組實例（直接傳入參數）
            module = ThrottleLineChartModule(
                parent=self,
                year=year_int,
                race=current_race,
                session=current_session
            )
            
            # 設置參數提供者
            module.parameter_provider = parameter_provider

            # 獲取 widget
            widget = module.get_widget()

            if widget:
                print("[THROTTLE_LINE] ✅ 模組初始化成功")
                
                # 獲取視窗標題
                window_title = module.get_window_title()
                
                # 創建 MDI 子視窗
                sub_window = PopoutSubWindow(window_title, mdi_area, module)
                sub_window.setWidget(widget)
                
                # 設置模組的父視窗引用
                module.set_parent_window(sub_window)
                
                # 設置視窗大小
                width, height = module.get_default_size()
                sub_window.resize(width, height)
                
                # 添加到 MDI 區域
                mdi_area.addSubWindow(sub_window)
                sub_window.show()
                
                print(f"[THROTTLE_LINE] ✅ 油門折線圖視窗已創建: {window_title}")
                
            else:
                print("[THROTTLE_LINE] ❌ 模組初始化失敗")
                QMessageBox.warning(
                    self,
                    "初始化失敗",
                    "油門折線圖模組初始化失敗\n請檢查日誌"
                )

        except Exception as e:
            print(f"[THROTTLE_LINE] ❌ 創建失敗: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "創建失敗",
                f"創建油門折線圖視窗時發生錯誤:\n{str(e)}"
            )

    def _prompt_detailed_lap_options(self):
        """顯示詳細圈速分析選項並回傳使用者選擇。"""
        try:
            from modules.gui.driver_race.detailed_lap_analysis.detailed_lap_options_dialog import (
                DetailedLapAnalysisOptionsDialog,
            )
        except ImportError as exc:
            print(f"[DETAILED_LAP] 無法載入選項對話框: {exc}")
            return {"detail_table": True, "box_plot": False}

        dialog = DetailedLapAnalysisOptionsDialog(self)
        result = dialog.exec_()

        if result != QDialog.Accepted:
            return None

        selected_types = dialog.get_selected_types()
        selection = {
            "detail_table": DetailedLapAnalysisOptionsDialog.TYPE_DETAIL_TABLE in selected_types,
            "box_plot": DetailedLapAnalysisOptionsDialog.TYPE_BOX_PLOT in selected_types,
        }

        if not selection["detail_table"] and not selection["box_plot"]:
            selection["detail_table"] = True

        print(f"[DETAILED_LAP] 選項結果: {selection}")
        return selection

    def _prompt_ideal_lap_options(self):
        """
        顯示理想圈分析選項對話框並回傳使用者選擇
        
        Returns:
            list[str] | None: 選中的分析類型列表，取消則返回 None
        """
        try:
            from modules.gui.ideal_lap_analysis import IdealLapAnalysisOptionsDialog
        except ImportError as exc:
            print(f"[IDEAL_LAP] ❌ 無法載入選項對話框: {exc}")
            import traceback
            traceback.print_exc()
            return None

        dialog = IdealLapAnalysisOptionsDialog(self)
        result = dialog.exec_()

        if result != QDialog.Accepted:
            print("[IDEAL_LAP] 使用者取消對話框")
            return None

        selected_types = dialog.get_selected_types()
        
        if not selected_types:
            print("[IDEAL_LAP] ⚠️ 未選擇任何分析類型")
            return None

        print(f"[IDEAL_LAP] ✅ 選項結果: {selected_types}")
        return selected_types

    def _create_detailed_lap_boxplot_window(self, mdi_area, year, race, session):
        """建立圈速箱型圖視窗並加入 MDI (使用新版 API 化模組)。"""
        try:
            print(f"[BOXPLOT] 🚀 啟動新版 API 化圈速箱型圖模組...")
            from modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
                LapTimeBoxPlotAnalysis,
            )
            print(f"[BOXPLOT] ✅ 新版模組導入成功")
        except ImportError as exc:
            message = f"Unable to load Lap Time Box Plot Analysis (API version): {exc}"
            print(f"[BOXPLOT] ❌ {message}")
            self.show_error_message("Lap Time Box Plot", message)
            import traceback
            traceback.print_exc()
            return None

        try:
            print(f"[BOXPLOT] 🔧 創建模組實例...")
            # 創建新版 MDI 模組實例
            analysis_module = LapTimeBoxPlotAnalysis(parent=self)
            print(f"[BOXPLOT] ✅ 模組實例創建成功")
            
            # 創建參數提供者
            parameter_provider = MainWindowParameterProvider(self)
            analysis_module.parameter_provider = parameter_provider
            print(f"[BOXPLOT] ✅ 參數提供者設置完成")
            
            # 設置當前參數
            analysis_module.current_year = str(year)
            analysis_module.current_race = race
            analysis_module.current_session = session
            print(f"[BOXPLOT] ✅ 基本參數設置完成: {year} {race} {session}")
            
            # 初始化模組
            print(f"[BOXPLOT] 🚀 初始化圈速箱型圖模組...")
            if not analysis_module.initialize_module():
                raise RuntimeError("Module initialization failed")
            print(f"[BOXPLOT] ✅ 模組初始化成功！")
            
            # 獲取模組標題
            window_title = analysis_module.get_window_title(
                year=year,
                race=race,
                session=session
            )
            print(f"[BOXPLOT] 📝 視窗標題: {window_title}")
            
            # 創建子視窗
            print(f"[BOXPLOT] 🖼️ 創建 MDI 子視窗...")
            sub_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
            sub_window.setWidget(analysis_module.get_widget())
            
            # 設置模組的父視窗引用
            analysis_module.set_parent_window(sub_window)
            
            # 設置視窗尺寸
            width, height = analysis_module.get_default_size()
            sub_window.resize(width, height)
            print(f"[BOXPLOT] 📐 設置視窗尺寸: {width}x{height}")
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            print(f"[BOXPLOT] ✅ 已添加到 MDI 區域")
            
            # 連接關閉信號
            if hasattr(sub_window, 'window_closed'):
                sub_window.window_closed.connect(lambda: self.on_subwindow_closed(sub_window))
            
            # 添加到追蹤列表
            if hasattr(self, 'active_subwindows'):
                self.active_subwindows.append(sub_window)
            
            # 顯示視窗
            sub_window.show()
            print(f"[BOXPLOT] 🎉 圈速箱型圖視窗創建完成！")
            
            return sub_window
            
        except Exception as exc:
            message = f"建立圈速箱型圖視窗時發生錯誤: {exc}"
            print(f"[BOXPLOT] ❌ {message}")
            self.show_error_message("Lap Time Box Plot", message)
            import traceback
            traceback.print_exc()
            return None
    
    def _create_ideal_lap_ranking_window(self, mdi_area, year, race, session):
        """建立理想圈排名表格視窗並加入 MDI"""
        try:
            print(f"[IDEAL_LAP_RANKING] 🚀 啟動理想圈排名表格模組...")
            from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module import IdealLapRankingTableModule
            print(f"[IDEAL_LAP_RANKING] ✅ 模組導入成功")
        except ImportError as exc:
            message = f"無法載入理想圈排名表格模組: {exc}"
            print(f"[IDEAL_LAP_RANKING] ❌ {message}")
            QMessageBox.critical(self, "模組載入失敗", message)
            import traceback
            traceback.print_exc()
            return None

        try:
            print(f"[IDEAL_LAP_RANKING] 🔧 創建模組實例...")
            # 創建模組實例
            analysis_module = IdealLapRankingTableModule(
                parent=self,
                year=year,
                race=race,
                session=session
            )
            print(f"[IDEAL_LAP_RANKING] ✅ 模組實例創建成功")
            
            # 初始化模組
            print(f"[IDEAL_LAP_RANKING] 🚀 初始化模組...")
            if not analysis_module.initialize_module(parent_widget=self):
                raise RuntimeError("Module initialization failed")
            print(f"[IDEAL_LAP_RANKING] ✅ 模組初始化成功！")
            
            # 獲取模組標題
            window_title = analysis_module.get_title()
            print(f"[IDEAL_LAP_RANKING] 📝 視窗標題: {window_title}")
            
            # 創建子視窗
            print(f"[IDEAL_LAP_RANKING] 🖼️ 創建 MDI 子視窗...")
            sub_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
            sub_window.setWidget(analysis_module.get_widget())
            
            # 設置視窗尺寸
            width, height = analysis_module.get_default_size()
            sub_window.resize(width, height)
            print(f"[IDEAL_LAP_RANKING] 📐 設置視窗尺寸: {width}x{height}")
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            print(f"[IDEAL_LAP_RANKING] ✅ 已添加到 MDI 區域")
            
            # 連接關閉信號
            if hasattr(sub_window, 'window_closed'):
                sub_window.window_closed.connect(lambda: self.on_subwindow_closed(sub_window))
            
            # 添加到追蹤列表
            if hasattr(self, 'active_subwindows'):
                self.active_subwindows.append(sub_window)
            
            # 顯示視窗
            sub_window.show()
            print(f"[IDEAL_LAP_RANKING] 🎉 理想圈排名表格視窗創建完成！")
            
            # 載入資料
            print(f"[IDEAL_LAP_RANKING] 📊 開始載入資料...")
            analysis_module.load_data()
            
            return sub_window
            
        except Exception as exc:
            message = f"建立理想圈排名表格視窗時發生錯誤: {exc}"
            print(f"[IDEAL_LAP_RANKING] ❌ {message}")
            QMessageBox.critical(self, "創建失敗", message)
            import traceback
            traceback.print_exc()
            return None
            
            # 設置模組的父視窗引用
            analysis_module.set_parent_window(sub_window)
            
            # 設置視窗大小
            sub_window.resize(1200, 800)
            print(f"[BOXPLOT] ✅ 子視窗創建成功")
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            if hasattr(sub_window, 'window_closed'):
                sub_window.window_closed.connect(lambda: self.on_subwindow_closed(sub_window))
            if hasattr(self, 'active_subwindows'):
                self.active_subwindows.append(sub_window)
            
            sub_window.show()
            self._position_subwindow(mdi_area, sub_window)
            
            print(f"[BOXPLOT] ✅ 圈速箱型圖視窗已創建: {window_title}")
            
            # 建立分析模組和子視窗的對應關係
            analysis_module._sub_window = sub_window
            
            # 自動載入數據
            print(f"[BOXPLOT] 🚀 自動載入圈速箱型圖數據...")
            success = analysis_module.load_data(
                year=year,
                race=race,
                session=session
            )
            
            if success:
                print(f"[BOXPLOT] ✅ 數據載入成功！")
            else:
                print(f"[BOXPLOT] ⚠️ 數據載入失敗，但視窗已創建")
            
            return sub_window
            
        except Exception as exc:
            message = f"Failed to create Lap Time Box Plot Analysis: {exc}"
            print(f"[BOXPLOT] ❌ {message}")
            self.show_error_message("Lap Time Box Plot", message)
            import traceback
            traceback.print_exc()
            return None

    def _position_subwindow(self, mdi_area, sub_window):
        """根據現有視窗數量調整子視窗位置，避免重疊。"""
        try:
            existing_windows = mdi_area.subWindowList()
            window_count = len(existing_windows)

            offset_x = (window_count % 4) * 30
            offset_y = (window_count // 4) * 30
            base_x = 10 + offset_x
            base_y = 10 + offset_y

            sub_window.move(base_x, base_y)
        except Exception as exc:
            print(f"[WARNING] 無法調整子視窗位置: {exc}")

    def _create_analysis_module(self, function_name, module_type_hint: Optional[str] = None):
        """創建分析模組實例"""
        try:
            # 導入模組工廠和類型定義
            from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
            
            # 確保所有模組都被導入
            import modules.gui.rain_analysis.rain_analysis_module  # 降雨分析模組
            import modules.gui.tire_analysis.tire_analysis_module  # 輪胎策略分析模組
            import modules.gui.accident_analysis.accident_analysis_mdi  # 事故分析模組
            import modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi  # 檔位分析模組
            import modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi  # 煞車分析模組
            import modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module  # 詳細圈速分析模組
            
            # 賽道分析模組導入與註冊
            try:
                from modules.gui.track_analysis import TrackAnalysisUniversal
                TRACK_ANALYSIS_AVAILABLE = True
                print("[OK] [MODULE_IMPORT] TrackAnalysisUniversal 載入完成")
            except ImportError as e:
                TRACK_ANALYSIS_AVAILABLE = False
                print(f"警告: TrackAnalysisUniversal 不可用: {e}")
            
            # 根據功能名稱映射到模組類型，支援多語系顯示文字
            module_alias_groups = {
                "pitstop_analysis": [
                    ("pitstop_analysis", "Pitstop Analysis"),
                    "進站分析",
                    "Pitstop Analysis",
                    "ピットストップ分析",
                ],
                "accident_analysis": [
                    ("accident_analysis", "Accident Analysis"),
                    "事故分析",
                    "Accident Analysis",
                ],
                "speed_analysis": [
                    ("speed_analysis", "Speed Analysis"),
                    "速度分析",
                ],
                "throttle_analysis": [
                    ("throttle_analysis", "Throttle Analysis"),
                    "油門分析",
                    "スロットル分析",
                ],
                "throttle_box_plot": [
                    ("throttle_box_plot", "Throttle Box Plot"),
                    ("throttle_box_plot_analysis", "Throttle Box Plot Analysis"),
                    "油門箱型圖",
                    "油門箱線圖",  # 樹節點別名
                    "Throttle Box Plot",
                    "スロットル箱ひげ図",
                ],
                "throttle_line_chart": [
                    ("throttle_line_chart", "Throttle Line Chart"),
                    "油門折線圖",  # 樹節點別名
                    "スロットル折れ線グラフ",
                ],
                "rpm_analysis": [
                    ("rpm_analysis", "RPM Analysis"),
                    "RPM分析",
                ],
                "gear_analysis": [
                    ("gear_analysis", "Gear Analysis"),
                    "檔位分析",
                    "ギア分析",
                ],
                "brake_analysis": [
                    ("brake_analysis", "Brake Analysis"),
                    "煞車分析",
                    "ブレーキ分析",
                ],
                "rain_analysis": [
                    ("rain_analysis", "Rain Analysis"),
                    "雨況分析",
                    "降雨分析",
                ],
                "telemetry_analysis": [
                    ("telemetry_analysis", "Telemetry Analysis"),
                    ("driver_analysis", "Driver Analysis"),
                    ("driver_ranking", "Driver Ranking"),
                    "車手分析",
                    "車手排名",
                    "單場賽事總攬",
                ],
                "track_analysis": [
                    ("track_analysis", "Track Analysis"),
                    "賽道分析",
                    "トラック分析",
                ],
                "tire_analysis": [
                    ("tire_analysis", "Tire Analysis"),
                    ("tire_strategy_analysis", "Tire Strategy Analysis"),
                    "輪胎分析",
                    "輪胎策略分析",
                    "タイヤ戦略分析",
                ],
                "driverlap_analysis": [
                    ("detailed_lap_analysis", "Detailed Lap Analysis"),
                    ("detailed_lap_table", "Detailed Lap Table"),  # 樹節點別名
                    "詳細圈速分析",
                    "詳細圈速表格",  # 中文樹節點
                    "詳細ラップ分析",
                ],
                "laptime_box_plot": [
                    ("laptime_box_plot", "Lap Time Box Plot"),
                    ("lap_time_boxplot", "Lap Time BoxPlot"),
                    "圈速箱線圖",  # 樹節點別名
                    "圈速箱型圖",
                ],
                "ideal_lap_ranking": [
                    ("ideal_lap_ranking", "Ideal Lap Ranking"),
                    ("ranking_table", "Ranking Table"),
                    "排名表格",  # 樹節點別名
                    "理想圈排名",
                ],
            }

            module_mapping = {}

            def _register_module_alias(alias_value, module_type):
                if isinstance(alias_value, str) and alias_value:
                    module_mapping[alias_value] = module_type

            for module_type, aliases in module_alias_groups.items():
                for alias in aliases:
                    if isinstance(alias, tuple):
                        translated_value = tr(alias[0], alias[1])
                        _register_module_alias(translated_value, module_type)
                    else:
                        _register_module_alias(alias, module_type)
            
            # 尋找匹配的模組類型
            module_type = module_type_hint
            matched_keyword = None
            if module_type:
                print(f"[DEBUG] [MODULE_FACTORY] 使用提供的模組類型提示: {module_type}")
            else:
                normalized_function_name = function_name.casefold() if isinstance(function_name, str) else ""
                print(f"[DEBUG] [MODULE_FACTORY] 開始尋找匹配的模組類型，功能名稱: '{function_name}'")
                for keyword, mod_type in module_mapping.items():
                    normalized_keyword = keyword.casefold() if isinstance(keyword, str) else ""
                    if normalized_keyword and normalized_keyword in normalized_function_name:
                        module_type = mod_type
                        matched_keyword = keyword
                        break
                if module_type and matched_keyword:
                    print(f"[DEBUG] [MODULE_FACTORY] ✅ 找到匹配! 關鍵字: '{matched_keyword}' -> 模組類型: '{module_type}'")
                else:
                    print(f"[DEBUG] [MODULE_FACTORY] ⚠️ 功能 '{function_name}' 未找到對應模組別名，將保持預設流程")
            
            if module_type:
                print(f"[DEBUG] [MODULE_FACTORY] 最終確定的模組類型: {module_type}")
                # 創建參數提供者
                parameter_provider = MainWindowParameterProvider(self)
                print(f"[DEBUG] [MODULE_FACTORY] 開始處理模組類型: {module_type} (來自功能: {function_name})")
                
                # 處理進站分析模組
                if module_type == "pitstop_analysis":
                    try:
                        from modules.gui.pitstop_analysis.pitstop_analysis_mdi import PitstopAnalysisModule
                        print(f"[OK] [MODULE_FACTORY] 創建進站分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = PitstopAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            print(f"[INIT] [MODULE_FACTORY] 進站分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            print(f"[OK] [MODULE_FACTORY] 進站分析模組初始化成功")
                            return self._mark_module_factory_type(module, module_type)
                        else:
                            print(f"[ERROR] [MODULE_FACTORY] 進站分析模組初始化失敗")
                            return None
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 進站分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理事故分析模組
                elif module_type == "accident_analysis":
                    try:
                        from modules.gui.accident_analysis.accident_analysis_mdi import AccidentAnalysisModule
                        print(f"[OK] [MODULE_FACTORY] 創建事故分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = AccidentAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            print(f"[INIT] [MODULE_FACTORY] 事故分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            print(f"[OK] [MODULE_FACTORY] 事故分析模組初始化成功")
                            return self._mark_module_factory_type(module, module_type)
                        else:
                            print(f"[ERROR] [MODULE_FACTORY] 事故分析模組初始化失敗")
                            return None
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 事故分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理單場賽事總攬模組
                elif module_type == "telemetry_analysis":
                    try:
                        from modules.gui.telemetry_analysis_mdi import TelemetryAnalysisModule
                        print(f"[OK] [MODULE_FACTORY] 創建單場賽事總攬模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = TelemetryAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            print(f"[INIT] [MODULE_FACTORY] 單場賽事總攬模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            print(f"[OK] [MODULE_FACTORY] 單場賽事總攬模組初始化成功")
                            return self._mark_module_factory_type(module, module_type)
                        else:
                            print(f"[ERROR] [MODULE_FACTORY] 單場賽事總攬模組初始化失敗")
                            return None
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 單場賽事總攬模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理賽道分析模組
                elif module_type == "track_analysis":
                    if not TRACK_ANALYSIS_AVAILABLE:
                        print(f"[INFO] [MODULE_FACTORY] TrackAnalysisUniversal 不可用，返回舊版流程")
                        return None

                    try:
                        current_year = parameter_provider.get_current_year()
                        current_race = parameter_provider.get_current_race()
                        current_session = parameter_provider.get_current_session()

                        module = TrackAnalysisUniversal(main_window=self)
                        module.parameter_provider = parameter_provider

                        # 轉換年份為整數，失敗時保持原值
                        try:
                            year_value = int(current_year)
                        except (TypeError, ValueError):
                            year_value = current_year

                        module.update_parameters(
                            year=year_value,
                            race=current_race,
                            session=current_session
                        )

                        print(f"[OK] [MODULE_FACTORY] 賽道分析模組初始化成功: {current_year} {current_race} {current_session}")
                        return self._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 賽道分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None

                # 處理油門分析模組
                elif module_type == "throttle_analysis":
                    try:
                        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import ThrottleAnalysisModule
                        print(f"[OK] [MODULE_FACTORY] 創建油門分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = ThrottleAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            print(f"[INIT] [MODULE_FACTORY] 油門分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            print(f"[OK] [MODULE_FACTORY] 油門分析模組初始化成功")
                            return self._mark_module_factory_type(module, module_type)
                        else:
                            print(f"[ERROR] [MODULE_FACTORY] 油門分析模組初始化失敗")
                            return None
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 油門分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None

                # 油門箱型圖分析模組
                elif module_type == "throttle_box_plot":
                    try:
                        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module import (
                            ThrottleBoxPlotAnalysisModule,
                        )

                        print(f"[OK] [MODULE_FACTORY] 創建油門箱型圖分析模組實例")

                        module = ThrottleBoxPlotAnalysisModule(parent=self)
                        module.parameter_provider = parameter_provider

                        current_year_value = None
                        current_race = None
                        current_session = None

                        if parameter_provider:
                            current_year_value = parameter_provider.get_current_year()
                            try:
                                current_year = int(current_year_value)
                            except (TypeError, ValueError):
                                current_year = current_year_value

                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()

                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session

                            print(
                                f"[INIT] [MODULE_FACTORY] 油門箱型圖模組參數預設為: {module.current_year} {module.current_race} {module.current_session}"
                            )

                        if module.initialize_module():
                            print(f"[OK] [MODULE_FACTORY] 油門箱型圖模組初始化成功")
                            if parameter_provider:
                                sync_year = current_year_value
                                try:
                                    sync_year_int = int(sync_year)
                                except (TypeError, ValueError):
                                    sync_year_int = sync_year

                                update_year = sync_year_int if sync_year_int is not None else module.current_year

                                try:
                                    module.update_parameters(update_year, current_race, current_session)
                                except Exception as sync_exc:
                                    print(f"[WARN] [MODULE_FACTORY] 油門箱型圖模組參數同步失敗: {sync_exc}")

                            return self._mark_module_factory_type(module, module_type)
                        else:
                            print(f"[ERROR] [MODULE_FACTORY] 油門箱型圖模組初始化失敗")
                            return None
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 油門箱型圖模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 油門折線圖分析模組
                elif module_type == "throttle_line_chart":
                    try:
                        print(f"[DEBUG] [MODULE_FACTORY] 開始創建油門折線圖模組...")
                        from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi import (
                            ThrottleLineChartMDI
                        )
                        print(f"[OK] [MODULE_FACTORY] 油門折線圖 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = ThrottleLineChartMDI(parent=self)
                        print(f"✅ [MODULE_FACTORY] 油門折線圖 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            print(f"[INIT] [MODULE_FACTORY] 油門折線圖模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            print(f"[ERROR] [MODULE_FACTORY] 油門折線圖模組初始化失敗")
                            return None
                        
                        print(f"[OK] [MODULE_FACTORY] 油門折線圖模組初始化成功")
                        return self._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 油門折線圖模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理檔位分析模組
                elif module_type == "gear_analysis":
                    try:
                        from modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi import GearAnalysisModule
                        print(f"[OK] [MODULE_FACTORY] 創建檔位分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = GearAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            print(f"[INIT] [MODULE_FACTORY] 檔位分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            print(f"[OK] [MODULE_FACTORY] 檔位分析模組初始化成功")
                            return self._mark_module_factory_type(module, module_type)
                        else:
                            print(f"[ERROR] [MODULE_FACTORY] 檔位分析模組初始化失敗")
                            return None
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 檔位分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理煞車分析模組
                elif module_type == "brake_analysis":
                    try:
                        from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeAnalysisModule
                        print(f"[OK] [MODULE_FACTORY] 創建煞車分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = BrakeAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            print(f"[INIT] [MODULE_FACTORY] 煞車分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            print(f"[OK] [MODULE_FACTORY] 煞車分析模組初始化成功")
                            return self._mark_module_factory_type(module, module_type)
                        else:
                            print(f"[ERROR] [MODULE_FACTORY] 煞車分析模組初始化失敗")
                            return None
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 煞車分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理降雨分析模組
                elif module_type == "rain_analysis":
                    try:
                        print(f"[DEBUG] [MODULE_FACTORY] 開始創建降雨分析模組...")
                        from modules.gui.rain_analysis.rain_analysis_module import RainAnalysisModuleAdapter
                        print(f"[OK] [MODULE_FACTORY] 降雨分析適配器導入成功")
                        
                        # 獲取當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            print(f"[INIT] [MODULE_FACTORY] 降雨分析模組參數: {current_year} {current_race} {current_session}")
                            
                            # 創建模組實例
                            module = RainAnalysisModuleAdapter(
                                year=current_year,
                                race=current_race,
                                session=current_session
                            )
                            print(f"[OK] 降雨分析模組初始化成功")
                            return self._mark_module_factory_type(module, module_type)
                        else:
                            print(f"[ERROR] 降雨分析模組創建失敗：無參數")
                            return None
                    except Exception as e:
                        print(f"[ERROR] 降雨分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理輪胎策略分析模組
                elif module_type == "tire_analysis":
                    try:
                        print(f"[DEBUG] [MODULE_FACTORY] 開始創建輪胎策略分析模組...")
                        from modules.gui.tire_analysis.tire_analysis_module import TireAnalysisModuleAdapter
                        print(f"[OK] [MODULE_FACTORY] 輪胎策略分析適配器導入成功")
                        
                        # 獲取當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            print(f"[INIT] [MODULE_FACTORY] 輪胎策略分析模組參數: {current_year} {current_race} {current_session}")
                            
                            # 創建模組實例
                            module = TireAnalysisModuleAdapter(
                                year=current_year,
                                race=current_race,
                                session=current_session
                            )
                            print(f"[OK] 輪胎策略分析模組初始化成功")
                            return self._mark_module_factory_type(module, module_type)
                        else:
                            print(f"[ERROR] 輪胎策略分析模組創建失敗：無參數")
                            return None
                    except Exception as e:
                        print(f"[ERROR] 輪胎策略分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理詳細圈速分析模組
                elif module_type == "driverlap_analysis":
                    try:
                        print(f"[DEBUG] [MODULE_FACTORY] 開始創建詳細圈速分析模組...")
                        from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi import driverLapAnalysisMDI
                        print(f"[OK] [MODULE_FACTORY] 詳細圈速分析 MDI 導入成功")
                        
                        # 直接創建 MDI 實例，不再需要包裝模組
                        module = driverLapAnalysisMDI(parent=self)
                        print(f"✅ [MODULE_FACTORY] 詳細圈速分析 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            print(f"[INIT] [MODULE_FACTORY] 詳細圈速分析模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            # 直接設置參數（與直接模式一致）
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # ✅ 初始化模組（關鍵步驟）
                        if not module.initialize_module():
                            print(f"[ERROR] [MODULE_FACTORY] 詳細圈速分析模組初始化失敗")
                            return None
                        
                        print(f"[OK] [MODULE_FACTORY] 詳細圈速分析模組初始化成功")
                        return self._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 詳細圈速分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理圈速箱線圖模組
                elif module_type == "laptime_box_plot":
                    try:
                        print(f"[DEBUG] [MODULE_FACTORY] 開始創建圈速箱線圖模組...")
                        from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import (
                            LapTimeBoxPlotAnalysis
                        )
                        print(f"[OK] [MODULE_FACTORY] 圈速箱線圖 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = LapTimeBoxPlotAnalysis(parent=self)
                        print(f"✅ [MODULE_FACTORY] 圈速箱線圖 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            print(f"[INIT] [MODULE_FACTORY] 圈速箱線圖模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            print(f"[ERROR] [MODULE_FACTORY] 圈速箱線圖模組初始化失敗")
                            return None
                        
                        print(f"[OK] [MODULE_FACTORY] 圈速箱線圖模組初始化成功")
                        return self._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 圈速箱線圖模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理理想圈排名表格模組
                elif module_type == "ideal_lap_ranking":
                    try:
                        print(f"[DEBUG] [MODULE_FACTORY] 開始創建理想圈排名表格模組...")
                        from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_mdi import (
                            IdealLapRankingTableMDI
                        )
                        print(f"[OK] [MODULE_FACTORY] 理想圈排名表格 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = IdealLapRankingTableMDI(parent=self)
                        print(f"✅ [MODULE_FACTORY] 理想圈排名表格 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            print(f"[INIT] [MODULE_FACTORY] 理想圈排名表格模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            print(f"[ERROR] [MODULE_FACTORY] 理想圈排名表格模組初始化失敗")
                            return None
                        
                        print(f"[OK] [MODULE_FACTORY] 理想圈排名表格模組初始化成功")
                        return self._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        print(f"[ERROR] [MODULE_FACTORY] 理想圈排名表格模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理其他模組類型...
                else:
                    print(f"[INFO] [MODULE_FACTORY] 模組類型 {module_type} 尚未實現")
                    return None
            
            print(f"[INFO] [MODULE_FACTORY] 無法找到匹配的模組類型: {function_name}")
            return None
            
        except Exception as e:
            print(f"[ERROR] [MODULE_FACTORY] 模組創建失敗: {e}")
            return None
        return None
    
    def _extract_module_name(self, function_name):
        """從功能名稱提取模組名稱"""
        return function_name.replace(" - 分析", "").replace("分析", "")
    
    def _create_legacy_content(self, function_name):
        """創建舊版內容 - 保持向後相容性"""
        # 根據功能類型創建相應的內容
        if "降雨分析" in function_name:
            # 使用新的雨量分析模組 (通用圖表系統)
            try:
                from modules.gui.rain_analysis.rain_analysis_module import RainAnalysisModuleAdapter
                params = self.get_current_parameters()
                content = RainAnalysisModuleAdapter(
                    year=params['year'],
                    race=params['race'],
                    session=params['session']
                )
                print(f"[OK] 已載入降雨分析模組 (通用圖表) - {params['year']} {params['race']} {params['session']}")
                return content
                
            except ImportError as e:
                print(f"[ERROR] 模組導入失敗: {e}")
                return TelemetryChartWidget("speed")  # 後備方案
        elif "遙測" in function_name:
            return TelemetryChartWidget("speed")
        elif "煞車" in function_name or "制動" in function_name:
            # 使用新的煞車分析模組
            try:
                from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeAnalysisModule
                
                # 創建參數提供者
                parameter_provider = MainWindowParameterProvider(self)
                
                # 創建模組實例並設置參數提供者
                module = BrakeAnalysisModule()
                module.parameter_provider = parameter_provider
                
                # 在初始化前先設置當前參數
                if parameter_provider:
                    current_year = int(parameter_provider.get_current_year())
                    current_race = parameter_provider.get_current_race() 
                    current_session = parameter_provider.get_current_session()
                    
                    # 直接設置模組參數
                    module.current_year = str(current_year)
                    module.current_race = current_race
                    module.current_session = current_session
                    
                    print(f"[INIT] 煞車分析模組參數預設為: {current_year} {current_race} {current_session}")
                
                # 初始化模組
                if module.initialize_module():
                    print(f"[OK] 煞車分析模組初始化成功")
                    return module
                else:
                    print(f"[ERROR] 煞車分析模組初始化失敗")
                    return TelemetryChartWidget("brake")  # 後備方案
                    
            except ImportError as e:
                print(f"[ERROR] 煞車分析模組導入失敗: {e}")
                return TelemetryChartWidget("brake")  # 後備方案
            except Exception as e:
                print(f"[ERROR] 煞車分析模組創建失敗: {e}")
                return TelemetryChartWidget("brake")  # 後備方案
        elif "油門" in function_name or "節流" in function_name:
            return TelemetryChartWidget("throttle")
        elif "轉向" in function_name or "方向盤" in function_name:
            return TelemetryChartWidget("steering")
        elif "賽道" in function_name:
            params = self.get_current_parameters()
            parameter_provider = MainWindowParameterProvider(self)

            try:
                from modules.gui.track_analysis import TrackAnalysisUniversal

                module = TrackAnalysisUniversal(main_window=self)
                module.parameter_provider = parameter_provider

                try:
                    year_value = int(params['year'])
                except (TypeError, ValueError):
                    year_value = params['year']

                module.update_parameters(
                    year=year_value,
                    race=params['race'],
                    session=params['session']
                )

                print(f"[OK] [LEGACY->UNIVERSAL] 使用 TrackAnalysisUniversal: {params['year']} {params['race']} {params['session']}")
                return module.get_widget(), module

            except ImportError as e:
                print(f"[ERROR] TrackAnalysisUniversal 導入失敗: {e}")
            except Exception as e:
                print(f"[ERROR] TrackAnalysisUniversal 初始化失敗: {e}")
                import traceback
                traceback.print_exc()

            # 如果新模組失敗，退回舊版 Widget 提示
            placeholder = QLabel("[WARNING] 賽道分析模組不可用\n\n請使用菜單中的\n'[FINISH] 賽道軌跡分析'")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 14px;
                    padding: 20px;
                    background: #F8F8F8;
                    border: 2px dashed #CCCCCC;
                    border-radius: 8px;
                }
            """)
            return placeholder
        elif "圈速" in function_name and "詳細圈速分析" not in function_name:
            return self.create_lap_analysis_table()
        elif "進站分析" in function_name:
            # 使用新的進站分析模組
            try:
                from modules.gui.pitstop_analysis import PitstopAnalysisModule
                print(f"[OK] [LEGACY] 創建進站分析模組")
                
                # 創建模組實例
                module = PitstopAnalysisModule()
                
                # 初始化模組
                if module.initialize_module():
                    print(f"[OK] [LEGACY] 進站分析模組初始化成功")
                    return module.get_widget(), module  # 返回 (widget, module) tuple
                else:
                    print(f"[ERROR] [LEGACY] 進站分析模組初始化失敗")
                    raise Exception("模組初始化失敗")
                
            except ImportError as e:
                print(f"[ERROR] 進站分析模組導入失敗: {e}")
                # 後備方案 - 顯示錯誤提示
                placeholder = QLabel("[ERROR] 進站分析模組不可用\n\n請檢查模組是否正確安裝")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("""
                    QLabel {
                        color: #ff6666;
                        font-size: 14px;
                        padding: 20px;
                        background: #fff8f8;
                        border: 2px dashed #ffcccc;
                        border-radius: 8px;
                    }
                """)
                return placeholder
            except Exception as e:
                print(f"[ERROR] 進站分析模組創建失敗: {e}")
                # 後備方案 - 顯示錯誤提示
                placeholder = QLabel(f"[ERROR] 進站分析模組錯誤\n\n{str(e)}")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("""
                    QLabel {
                        color: #ff6666;
                        font-size: 14px;
                        padding: 20px;
                        background: #fff8f8;
                        border: 2px dashed #ffcccc;
                        border-radius: 8px;
                    }
                """)
                return placeholder
        else:
            # 預設創建速度遙測圖表
            return TelemetryChartWidget("speed")
    
    def close_all_mdi_windows(self, mdi_area):
        """關閉指定MDI區域中的所有子視窗並徹底清理所有相關註冊"""
        try:
            print(f"[CLOSE] 開始關閉 MDI 區域中的所有視窗...")
            
            # 獲取所有子視窗
            subwindows = mdi_area.subWindowList()
            window_count = len(subwindows)
            
            print(f"[STATS] MDI區域中共有 {window_count} 個子視窗")
            
            if window_count > 0:
                # 1. 在關閉視窗前，先從連動管理器中取消註冊所有相關模組
                linkage_unregister_count = 0
                
                for subwindow in subwindows[:]:  # 使用切片創建副本
                    if subwindow and subwindow.widget():
                        widget = subwindow.widget()
                        
                        # 遞歸查找所有可能的連動模組並取消註冊
                        modules_to_unregister = self._find_linkage_modules_in_widget(widget)
                        
                        for module in modules_to_unregister:
                            try:
                                linkage_manager.unregister_module(module)
                                linkage_unregister_count += 1
                                print(f"[CLEANUP] 已從連動管理器取消註冊模組: {type(module).__name__}")
                            except Exception as e:
                                print(f"[WARNING] 取消註冊連動模組失敗: {e}")
                
                # 2. 逐一關閉並刪除子視窗
                closed_count = 0
                for subwindow in subwindows[:]:  # 使用切片創建副本
                    try:
                        # 獲取視窗標題以供日誌
                        title = subwindow.windowTitle() if subwindow else "Unknown"
                        
                        # 關閉視窗
                        if subwindow:
                            subwindow.close()
                            # 強制從MDI區域移除
                            mdi_area.removeSubWindow(subwindow)
                            # 刪除對象
                            subwindow.deleteLater()
                            closed_count += 1
                            print(f"[CLEANUP] 已關閉並清理視窗: {title}")
                            
                    except Exception as e:
                        print(f"[WARNING] 關閉視窗時發生錯誤: {e}")
                
                # 3. 強制清理MDI區域
                try:
                    mdi_area.closeAllSubWindows()  # 確保所有視窗都被關閉
                    
                    # 強制刷新MDI區域狀態
                    mdi_area.update()
                    mdi_area.repaint()
                    
                except Exception as e:
                    print(f"[WARNING] MDI區域清理時發生錯誤: {e}")
                
                # 4. 強制Qt事件處理和垃圾回收
                try:
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()  # 處理所有待處理的事件
                    
                    import gc
                    gc.collect()  # 強制垃圾回收
                    
                except Exception as e:
                    print(f"[WARNING] 事件處理和垃圾回收時發生錯誤: {e}")
                
                # 5. 驗證清理結果
                final_subwindows = mdi_area.subWindowList()
                final_count = len(final_subwindows)
                
                print(f"[OK] 關閉完成統計:")
                print(f"    原始視窗數: {window_count}")
                print(f"    已關閉視窗: {closed_count}")
                print(f"    連動模組取消註冊: {linkage_unregister_count}")
                print(f"    清理後剩餘視窗: {final_count}")
                
                if final_count > 0:
                    print(f"[WARNING] 仍有 {final_count} 個視窗未完全清理")
                    for i, remaining in enumerate(final_subwindows):
                        title = remaining.windowTitle() if remaining else "Unknown"
                        print(f"    剩餘視窗 {i+1}: {title}")
                else:
                    print(f"[OK] ✅ 所有視窗已完全清理")
                    
            else:
                print(f"[INFO] 沒有需要關閉的視窗")
                
        except Exception as e:
            print(f"[ERROR] 關閉視窗時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _find_linkage_modules_in_widget(self, widget):
        """遞歸查找 widget 中所有實現了連動功能的模組"""
        linkage_modules = []
        
        # 檢查當前 widget 是否實現了連動功能
        if hasattr(widget, 'on_x_linkage_received') or hasattr(widget, 'on_click_linkage_received'):
            linkage_modules.append(widget)
        
        # 遞歸檢查所有子 widget
        if hasattr(widget, 'children'):
            for child in widget.children():
                if hasattr(child, '__class__') and hasattr(child, 'parent'):
                    linkage_modules.extend(self._find_linkage_modules_in_widget(child))
        
        return linkage_modules

    def reset_all_charts(self, mdi_area):
        """重置MDI區域中所有圖表以顯示完整數據範圍"""
        try:
            print(f"[REFRESH] 開始調整 MDI 區域中的所有圖表以顯示完整數據...")
            
            # 獲取所有子視窗
            subwindows = mdi_area.subWindowList()
            reset_count = 0
            
            print(f"[STATS] MDI區域中共有 {len(subwindows)} 個子視窗")
            
            def find_telemetry_widgets(widget):
                """遞歸查找 TelemetryChartWidget"""
                telemetry_widgets = []
                
                # 檢查當前widget
                if isinstance(widget, TelemetryChartWidget):
                    telemetry_widgets.append(widget)
                
                # 遞歸檢查所有子widget
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            telemetry_widgets.extend(find_telemetry_widgets(child))
                
                return telemetry_widgets
            
            def find_universal_chart_widgets(widget):
                """遞歸查找 UniversalChartWidget"""
                from modules.gui.universal_chart_widget import UniversalChartWidget
                universal_widgets = []
                
                # 檢查當前widget
                if isinstance(widget, UniversalChartWidget):
                    universal_widgets.append(widget)
                
                # 遞歸檢查所有子widget
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            universal_widgets.extend(find_universal_chart_widgets(child))
                
                return universal_widgets
            
            def find_speed_analysis_widgets(widget):
                """遞歸查找 SpeedAnalysisChartWidget"""
                from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedAnalysisChartWidget
                speed_widgets = []
                
                # 檢查當前widget
                if isinstance(widget, SpeedAnalysisChartWidget):
                    speed_widgets.append(widget)
                
                # 遞歸檢查所有子widget
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            speed_widgets.extend(find_speed_analysis_widgets(child))
                
                return speed_widgets
            
            def find_brake_analysis_widgets(widget):
                """遞歸查找 BrakeAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.brake_analysis.brake_analysis_chart_widget import BrakeAnalysisChartWidget
                    brake_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, BrakeAnalysisChartWidget):
                        brake_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                brake_widgets.extend(find_brake_analysis_widgets(child))
                    
                    return brake_widgets
                except ImportError:
                    return []
            
            def find_rpm_analysis_widgets(widget):
                """遞歸查找 RPMAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget import RPMAnalysisChartWidget
                    rpm_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, RPMAnalysisChartWidget):
                        rpm_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                rpm_widgets.extend(find_rpm_analysis_widgets(child))
                    
                    return rpm_widgets
                except ImportError:
                    return []
            
            def find_gear_analysis_widgets(widget):
                """遞歸查找 GearAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget import GearAnalysisChartWidget
                    gear_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, GearAnalysisChartWidget):
                        gear_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                gear_widgets.extend(find_gear_analysis_widgets(child))
                    
                    return gear_widgets
                except ImportError:
                    return []
            
            def find_throttle_analysis_widgets(widget):
                """遞歸查找 ThrottleAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
                    throttle_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, ThrottleAnalysisChartWidget):
                        throttle_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                throttle_widgets.extend(find_throttle_analysis_widgets(child))
                    
                    return throttle_widgets
                except ImportError:
                    return []
            
            def find_speeddiff_analysis_widgets(widget):
                """遞歸查找 SpeeddiffAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_chart_widget import SpeeddiffAnalysisChartWidget
                    speeddiff_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, SpeeddiffAnalysisChartWidget):
                        speeddiff_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                speeddiff_widgets.extend(find_speeddiff_analysis_widgets(child))
                    
                    return speeddiff_widgets
                except ImportError:
                    return []
            
            def find_distancediff_analysis_widgets(widget):
                """遞歸查找 distancediffAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_chart_widget import distancediffAnalysisChartWidget
                    distancediff_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, distancediffAnalysisChartWidget):
                        distancediff_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                distancediff_widgets.extend(find_distancediff_analysis_widgets(child))
                    
                    return distancediff_widgets
                except ImportError:
                    return []
            
            def find_acceleration_analysis_widgets(widget):
                """遞歸查找 accelerationAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget import accelerationAnalysisChartWidget
                    acceleration_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, accelerationAnalysisChartWidget):
                        acceleration_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                acceleration_widgets.extend(find_acceleration_analysis_widgets(child))
                    
                    return acceleration_widgets
                except ImportError:
                    return []
            
            for i, subwindow in enumerate(subwindows):
                if subwindow and subwindow.widget():
                    widget = subwindow.widget()
                    widget_type = type(widget).__name__
                    print(f"[SEARCH] 檢查視窗 {i+1}: {widget_type}")
                    
                    # 遞歸查找所有 TelemetryChartWidget
                    telemetry_widgets = find_telemetry_widgets(widget)
                    # 遞歸查找所有 UniversalChartWidget
                    universal_widgets = find_universal_chart_widgets(widget)
                    # 遞歸查找所有分析模組組件
                    speed_widgets = find_speed_analysis_widgets(widget)
                    brake_widgets = find_brake_analysis_widgets(widget)
                    rpm_widgets = find_rpm_analysis_widgets(widget)
                    gear_widgets = find_gear_analysis_widgets(widget)
                    throttle_widgets = find_throttle_analysis_widgets(widget)
                    speeddiff_widgets = find_speeddiff_analysis_widgets(widget)
                    distancediff_widgets = find_distancediff_analysis_widgets(widget)
                    acceleration_widgets = find_acceleration_analysis_widgets(widget)
                    
                    print(f"  找到 {len(telemetry_widgets)} 個遙測圖表, {len(universal_widgets)} 個通用圖表")
                    print(f"  分析模組: 速度={len(speed_widgets)}, 煞車={len(brake_widgets)}, RPM={len(rpm_widgets)}, 檔位={len(gear_widgets)}, 油門={len(throttle_widgets)}")
                    print(f"  差異分析: 速度差={len(speeddiff_widgets)}, 距離差={len(distancediff_widgets)}, 加速度={len(acceleration_widgets)}")
                    
                    if telemetry_widgets:
                        for telemetry_widget in telemetry_widgets:
                            #print(f"[TARGET] 調整遙測圖表以顯示完整數據: {telemetry_widget.chart_type}")
                            
                            # 獲取圖表的實際尺寸
                            chart_width = telemetry_widget.width()
                            chart_height = telemetry_widget.height()
                            
                            if chart_width > 0 and chart_height > 0:
                                # [SEARCH] 根據實際數據範圍動態計算最佳縮放比例
                                
                                # 獲取實際數據範圍
                                x_data = getattr(telemetry_widget, 'x_data', None)
                                y_data = getattr(telemetry_widget, 'y_data', None)
                                
                                if x_data is not None and y_data is not None and len(x_data) > 0 and len(y_data) > 0:
                                    # 計算數據的實際範圍
                                    x_min, x_max = min(x_data), max(x_data)
                                    y_min, y_max = min(y_data), max(y_data)
                                    
                                    x_range = x_max - x_min if x_max != x_min else 1.0
                                    y_range = y_max - y_min if y_max != y_min else 1.0
                                    
                                    # 計算縮放比例，讓數據填滿90%的視窗空間
                                    # 假設視窗的基礎顯示範圍是 X: 0-100, Y: 0-100
                                    base_x_range = 100.0
                                    base_y_range = 100.0
                                    
                                    # 計算縮放比例
                                    optimal_x_scale = (base_x_range * 0.9) / x_range
                                    optimal_y_scale = (base_y_range * 0.9) / y_range
                                    
                                    # 限制縮放範圍，避免過度縮放
                                    optimal_x_scale = max(0.1, min(20.0, optimal_x_scale))
                                    optimal_y_scale = max(0.1, min(20.0, optimal_y_scale))
                                    
                                    # 計算偏移，讓數據居中顯示
                                    data_center_x = (x_min + x_max) / 2
                                    data_center_y = (y_min + y_max) / 2
                                    
                                    # 將數據中心移到視窗中心 (50, 50)
                                    optimal_x_offset = 50.0 - (data_center_x * optimal_x_scale)
                                    optimal_y_offset = 50.0 - (data_center_y * optimal_y_scale)
                                    
                                    # 應用計算出的縮放和偏移
                                    telemetry_widget.x_scale = optimal_x_scale
                                    telemetry_widget.y_scale = optimal_y_scale
                                    telemetry_widget.x_offset = optimal_x_offset
                                    telemetry_widget.y_offset = optimal_y_offset
                                    
                                    #print(f"[STATS] 數據範圍分析 {telemetry_widget.chart_type}:")
                                    #print(f"   X範圍: {x_min:.2f} ~ {x_max:.2f} (差值: {x_range:.2f})")
                                    #print(f"   Y範圍: {y_min:.2f} ~ {y_max:.2f} (差值: {y_range:.2f})")
                                    #print(f"   最佳縮放: X={optimal_x_scale:.2f}, Y={optimal_y_scale:.2f}")
                                    #print(f"   居中偏移: X={optimal_x_offset:.2f}, Y={optimal_y_offset:.2f}")
                                    
                                else:
                                    # 如果沒有數據，使用預設值
                                    telemetry_widget.x_scale = 1.0
                                    telemetry_widget.y_scale = 1.0
                                    telemetry_widget.x_offset = 0.0
                                    telemetry_widget.y_offset = 0.0
                                    #print(f"[WARNING] 無法獲取 {telemetry_widget.chart_type} 的數據範圍，使用預設縮放")
                                
                                # 重置拖拽狀態
                                telemetry_widget.is_dragging = False
                                telemetry_widget.last_mouse_pos = None
                                
                                # 重新繪製圖表
                                telemetry_widget.update()
                                reset_count += 1
                                
                                #print(f"[OK] 調整完成 {telemetry_widget.chart_type} - X縮放: {telemetry_widget.x_scale:.2f}, Y縮放: {telemetry_widget.y_scale:.2f}, X偏移: {telemetry_widget.x_offset:.1f}, Y偏移: {telemetry_widget.y_offset:.1f}")
                            else:
                                #print(f"[WARNING] 圖表 {telemetry_widget.chart_type} 尺寸無效，跳過調整")
                                pass
                    
                    # 處理通用圖表 (UniversalChartWidget)
                    if universal_widgets:
                        for universal_widget in universal_widgets:
                            print(f"[TARGET] 重置通用圖表: {universal_widget.title}")
                            universal_widget.reset_view()
                            reset_count += 1
                            print(f"[OK] 通用圖表重置完成: {universal_widget.title}")
                    
                    # 處理速度分析圖表 (SpeedAnalysisChartWidget)
                    if speed_widgets:
                        for speed_widget in speed_widgets:
                            print(f"[TARGET] 重置速度分析圖表")
                            speed_widget.reset_chart_view()
                            reset_count += 1
                            print(f"[OK] 速度分析圖表重置完成")
                    
                    # 處理煞車分析圖表 (BrakeAnalysisChartWidget) 
                    if brake_widgets:
                        for brake_widget in brake_widgets:
                            print(f"[TARGET] 重置煞車分析圖表")
                            if hasattr(brake_widget, 'reset_chart_view'):
                                brake_widget.reset_chart_view()
                            elif hasattr(brake_widget, 'chart_widget') and hasattr(brake_widget.chart_widget, 'reset_view'):
                                brake_widget.chart_widget.reset_view()
                            reset_count += 1
                            print(f"[OK] 煞車分析圖表重置完成")
                    
                    # 處理RPM分析圖表 (RPMAnalysisChartWidget)
                    if rpm_widgets:
                        for rpm_widget in rpm_widgets:
                            print(f"[TARGET] 重置RPM分析圖表")
                            if hasattr(rpm_widget, 'reset_chart_view'):
                                rpm_widget.reset_chart_view()
                            elif hasattr(rpm_widget, 'chart_widget') and hasattr(rpm_widget.chart_widget, 'reset_view'):
                                rpm_widget.chart_widget.reset_view()
                            reset_count += 1
                            print(f"[OK] RPM分析圖表重置完成")
                    
                    # 處理檔位分析圖表 (GearAnalysisChartWidget)
                    if gear_widgets:
                        for gear_widget in gear_widgets:
                            print(f"[TARGET] 重置檔位分析圖表")
                            if hasattr(gear_widget, 'reset_chart_view'):
                                gear_widget.reset_chart_view()
                            elif hasattr(gear_widget, 'chart_widget') and hasattr(gear_widget.chart_widget, 'reset_view'):
                                gear_widget.chart_widget.reset_view()
                            reset_count += 1
                            print(f"[OK] 檔位分析圖表重置完成")
                    
                    # 處理油門分析圖表 (ThrottleAnalysisChartWidget)
                    if throttle_widgets:
                        for throttle_widget in throttle_widgets:
                            print(f"[TARGET] 重置油門分析圖表")
                            throttle_widget.reset_chart_view()
                            reset_count += 1
                            print(f"[OK] 油門分析圖表重置完成")
                    
                    # 處理速度差異分析圖表 (SpeedDiffAnalysisChartWidget)
                    if speeddiff_widgets:
                        for speeddiff_widget in speeddiff_widgets:
                            print(f"[TARGET] 重置速度差異分析圖表")
                            if hasattr(speeddiff_widget, 'reset_chart_view'):
                                speeddiff_widget.reset_chart_view()
                            elif hasattr(speeddiff_widget, 'chart_widget') and hasattr(speeddiff_widget.chart_widget, 'reset_view'):
                                speeddiff_widget.chart_widget.reset_view()
                            reset_count += 1
                            print(f"[OK] 速度差異分析圖表重置完成")
                    
                    # 處理距離差異分析圖表 (DistanceDiffAnalysisChartWidget)
                    if distancediff_widgets:
                        for distancediff_widget in distancediff_widgets:
                            print(f"[TARGET] 重置距離差異分析圖表")
                            if hasattr(distancediff_widget, 'reset_chart_view'):
                                distancediff_widget.reset_chart_view()
                            elif hasattr(distancediff_widget, 'chart_widget') and hasattr(distancediff_widget.chart_widget, 'reset_view'):
                                distancediff_widget.chart_widget.reset_view()
                            reset_count += 1
                            print(f"[OK] 距離差異分析圖表重置完成")
                    
                    # 處理加速度分析圖表 (AccelerationAnalysisChartWidget)
                    if acceleration_widgets:
                        for acceleration_widget in acceleration_widgets:
                            print(f"[TARGET] 重置加速度分析圖表")
                            if hasattr(acceleration_widget, 'reset_chart_view'):
                                acceleration_widget.reset_chart_view()
                            elif hasattr(acceleration_widget, 'chart_widget') and hasattr(acceleration_widget.chart_widget, 'reset_view'):
                                acceleration_widget.chart_widget.reset_view()
                            reset_count += 1
                            print(f"[OK] 加速度分析圖表重置完成")
                    
                    # 檢查是否為其他類型的圖表或可縮放小部件
                    elif hasattr(widget, 'fit_to_view'):
                        # 如果小部件有適合視圖的方法
                        #print(f"[TOOL] 使用 fit_to_view 方法調整: {widget_type}")
                        widget.fit_to_view()
                        reset_count += 1
                        
                    elif hasattr(widget, 'zoom_to_fit'):
                        # 如果小部件有縮放適應方法
                        #print(f"[TOOL] 使用 zoom_to_fit 方法調整: {widget_type}")
                        widget.zoom_to_fit()
                        reset_count += 1
                    else:
                        #print(f"[WARNING] 視窗 {i+1} 中沒有找到可調整的圖表組件")
                        pass
                else:
                    #print(f"[WARNING] 視窗 {i+1} 沒有有效的widget")
                    pass
            
            print(f"[OK] 調整完成！共調整了 {reset_count} 個圖表以顯示完整數據")
            
        except Exception as e:
            print(f"[ERROR] 調整圖表時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    # 事件處理方法
            
    def open_session(self): 
        params = self.get_current_parameters()
        print(f"[檔案] 開啟會話請求 - {params['year']} {params['race']} {params['session']}")
        QMessageBox.information(
            self,
            tr('open_session_disabled', '開啟會話'),
            tr('open_session_disabled_message', 'API-ONLY 模式下請透過 API 或既有 JSON 載入分析資料。')
        )

    def save_workspace(self, *, default_path: Optional[str] = None):
        """儲存目前的工作區設定"""
        default_dir = Path(default_path).parent if default_path else (Path(self._last_workspace_path).parent if getattr(self, '_last_workspace_path', None) else Path.home() / "Documents")
        default_dir = default_dir.resolve()
        default_dir.mkdir(parents=True, exist_ok=True)
        suggested_name = Path(default_path).name if default_path else "f1t_workspace.json"
        initial_path = str(default_dir / suggested_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr('save_workspace', '儲存工作區'),
            initial_path,
            "F1T Workspace (*.json);;JSON (*.json);;All Files (*.*)"
        )

        if not file_path:
            return

        target_path = Path(file_path)
        if target_path.suffix.lower() != '.json':
            target_path = target_path.with_suffix('.json')

        snapshot = self._build_workspace_snapshot()

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with target_path.open('w', encoding='utf-8') as handle:
                json.dump(snapshot, handle, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.exception("Failed to save workspace snapshot", exc_info=exc)
            QMessageBox.critical(
                self,
                tr('save_workspace_error', '儲存工作區失敗'),
                f"{tr('error_details', '詳細資訊')}: {exc}"
            )
            return

        self._last_workspace_path = str(target_path)
        QMessageBox.information(
            self,
            tr('save_workspace', '儲存工作區'),
            tr('workspace_saved_message', '工作區設定已儲存。')
        )

    def load_workspace(self, *, source_path: Optional[str] = None):
        """載入工作區設定"""
        start_dir = Path(source_path).parent if source_path else (Path(self._last_workspace_path).parent if getattr(self, '_last_workspace_path', None) else Path.home() / "Documents")
        start_dir = start_dir.resolve()
        if not start_dir.exists():
            start_dir = Path.home()

        initial_path = str(Path(source_path)) if source_path else str(start_dir)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr('load_workspace', '載入工作區'),
            initial_path,
            "F1T Workspace (*.json);;JSON (*.json);;All Files (*.*)"
        )

        if not file_path:
            return

        target_path = Path(file_path)

        try:
            with target_path.open('r', encoding='utf-8') as handle:
                snapshot = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.exception("Failed to load workspace snapshot", exc_info=exc)
            QMessageBox.critical(
                self,
                tr('load_workspace_error', '載入工作區失敗'),
                f"{tr('error_details', '詳細資訊')}: {exc}"
            )
            return

        try:
            self._apply_workspace_snapshot(snapshot)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to apply workspace snapshot", exc_info=exc)
            QMessageBox.critical(
                self,
                tr('load_workspace_error', '載入工作區失敗'),
                f"{tr('error_details', '詳細資訊')}: {exc}"
            )
            return

        self._last_workspace_path = str(target_path)
        QMessageBox.information(
            self,
            tr('load_workspace', '載入工作區'),
            tr('workspace_loaded_message', '工作區設定已載入。')
        )

    def _build_workspace_snapshot(self) -> Dict[str, object]:
        """產生目前工作區的序列化快照"""
        selected_event = self.get_selected_event()
        race_key = selected_event.race_key if isinstance(selected_event, SeasonEvent) else self.get_selected_race_key()
        snapshot = {
            "version": 2,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "parameters": {
                "year": self.year_combo.currentText() if hasattr(self, 'year_combo') else None,
                "race_display": self.race_combo.currentText() if hasattr(self, 'race_combo') else None,
                "race_key": race_key,
                "session": self.get_selected_session_code() if hasattr(self, 'session_combo') else None,
            },
            "linkage_enabled": self.linkage_action.isChecked() if hasattr(self, 'linkage_action') else True,
            "lap_controls": {
                "driver1": self.driver1_combo.currentText() if hasattr(self, 'driver1_combo') else None,
                "driver2": self.driver2_combo.currentText() if hasattr(self, 'driver2_combo') else None,
                "lap1": self.lap1_spinbox.value() if hasattr(self, 'lap1_spinbox') else None,
                "lap2": self.lap2_spinbox.value() if hasattr(self, 'lap2_spinbox') else None,
                "fastest_lap": self.fastest_lap_checkbox.isChecked() if hasattr(self, 'fastest_lap_checkbox') else None,
            },
        }
        snapshot["open_windows"] = self._collect_open_windows_state()
        return snapshot

    def _collect_open_windows_state(self) -> List[Dict[str, Any]]:
        """蒐集目前開啟的分析視窗狀態以支援工作區還原"""
        open_windows: List[Dict[str, Any]] = []
        for subwindow in getattr(self, "active_subwindows", []) or []:
            if not isinstance(subwindow, PopoutSubWindow):
                continue
            state = self._collect_subwindow_state(subwindow)
            if state:
                open_windows.append(state)
        return open_windows

    def _collect_subwindow_state(self, subwindow: 'PopoutSubWindow') -> Optional[Dict[str, Any]]:
        """產生單一子視窗的序列化狀態"""
        if getattr(subwindow, "is_popped_out", False):
            # 目前僅支援還原在 MDI 內的視窗
            return None

        module = getattr(subwindow, "analysis_module", None)
        if module is None:
            return None

        mdi_area = subwindow.mdiArea()
        geometry = subwindow.geometry()
        geometry_state = {
            "x": int(geometry.x()),
            "y": int(geometry.y()),
            "width": int(geometry.width()),
            "height": int(geometry.height()),
        }

        window_state = "normal"
        if subwindow.isMaximized():
            window_state = "maximized"
        elif subwindow.isMinimized():
            window_state = "minimized"

        subwindow_state: Dict[str, Any] = {
            "title": subwindow.windowTitle(),
            "mdi_area": mdi_area.objectName() if mdi_area else None,
            "geometry": geometry_state,
            "window_state": window_state,
            "sync_enabled": bool(getattr(subwindow, "sync_enabled", True)),
            "local_parameters": {
                "year": getattr(subwindow, "local_year", None),
                "race": getattr(subwindow, "local_race", None),
                "session": getattr(subwindow, "local_session", None),
            },
            "module": self._collect_module_state(module),
        }

        return subwindow_state

    def _collect_module_state(self, module) -> Optional[Dict[str, Any]]:
        """收集分析模組狀態，便於日後重新建立"""
        try:
            module_state: Dict[str, Any] = {
                "module_path": module.__class__.__module__,
                "class_name": module.__class__.__name__,
            }

            factory_type = getattr(module, "_factory_module_type", None)
            if factory_type:
                module_state["factory_type"] = factory_type

            analysis_type = getattr(module, "analysis_type", None)
            if analysis_type:
                module_state["analysis_type"] = analysis_type

            display_name = getattr(module, "display_name", None)
            if display_name:
                module_state["display_name"] = display_name

            module_name = getattr(module, "module_name", None)
            if module_name:
                module_state["module_name"] = module_name

            parameters: Dict[str, Any] = {}
            for attr in ("current_year", "current_race", "current_session", "driver1", "driver2", "lap1", "lap2"):
                if hasattr(module, attr):
                    value = getattr(module, attr)
                    if value is not None:
                        parameters[attr] = value

            if parameters:
                module_state["parameters"] = parameters

            return module_state
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to collect module state: %s", exc)
            return None

    def _apply_workspace_snapshot(self, snapshot: Dict[str, object]) -> None:
        """根據快照資料套用工作區設定"""
        parameters = snapshot.get("parameters", {}) if isinstance(snapshot, dict) else {}

        year_value = parameters.get("year") if isinstance(parameters, dict) else None
        race_key = parameters.get("race_key") if isinstance(parameters, dict) else None
        race_display = parameters.get("race_display") if isinstance(parameters, dict) else None
        session_code = parameters.get("session") if isinstance(parameters, dict) else None

        if year_value:
            try:
                year_int = int(year_value)
            except (TypeError, ValueError):
                year_int = None
            if year_int:
                if hasattr(self, 'year_combo'):
                    self.year_combo.setCurrentText(str(year_int))
                self._refresh_calendar_for_year(year_int, preserve_race_key=race_key, preserve_session_code=session_code)

        if race_key:
            self._select_race_by_key(race_key)
        elif race_display and hasattr(self, 'race_combo'):
            index = self.race_combo.findText(race_display)
            if index >= 0:
                self.race_combo.setCurrentIndex(index)

        if session_code and hasattr(self, 'session_combo'):
            index = self.session_combo.findText(session_code)
            if index >= 0:
                self.session_combo.setCurrentIndex(index)

        linkage_enabled = snapshot.get("linkage_enabled") if isinstance(snapshot, dict) else None
        if linkage_enabled is not None and hasattr(self, 'linkage_action'):
            self.linkage_action.setChecked(bool(linkage_enabled))

        lap_controls = snapshot.get("lap_controls") if isinstance(snapshot, dict) else {}
        if isinstance(lap_controls, dict) and lap_controls:
            if hasattr(self, 'driver1_combo') and self.driver1_combo.count() == 0:
                self.initialize_driver_lists()

            driver1 = lap_controls.get("driver1")
            if driver1 and hasattr(self, 'driver1_combo'):
                index = self.driver1_combo.findText(driver1)
                if index >= 0:
                    self.driver1_combo.setCurrentIndex(index)

            driver2 = lap_controls.get("driver2")
            if driver2 and hasattr(self, 'driver2_combo'):
                index = self.driver2_combo.findText(driver2)
                if index >= 0:
                    self.driver2_combo.setCurrentIndex(index)

            lap1 = lap_controls.get("lap1")
            if lap1 and hasattr(self, 'lap1_spinbox'):
                try:
                    self.lap1_spinbox.setValue(int(lap1))
                except (TypeError, ValueError):
                    pass

            lap2 = lap_controls.get("lap2")
            if lap2 and hasattr(self, 'lap2_spinbox'):
                try:
                    self.lap2_spinbox.setValue(int(lap2))
                except (TypeError, ValueError):
                    pass

            fastest_lap = lap_controls.get("fastest_lap")
            if fastest_lap is not None and hasattr(self, 'fastest_lap_checkbox'):
                self.fastest_lap_checkbox.setChecked(bool(fastest_lap))

            if hasattr(self, 'on_lap_parameters_changed'):
                self.on_lap_parameters_changed()

        open_windows_state = snapshot.get("open_windows") if isinstance(snapshot, dict) else None
        self._restore_open_windows(open_windows_state)

    def _restore_open_windows(self, windows_state: Optional[List[Dict[str, Any]]]) -> None:
        """依據快照資料還原目前工作區的分析視窗"""
        # 關閉現有活動視窗，避免與快照資料衝突
        for subwindow in list(getattr(self, "active_subwindows", []) or []):
            try:
                subwindow.close()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to close subwindow during restore: %s", exc)

        if hasattr(self, "active_subwindows"):
            self.active_subwindows.clear()

        if not windows_state:
            return

        for window_state in windows_state:
            try:
                self._restore_single_window(window_state)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to restore window state", exc_info=exc)

    def _restore_single_window(self, window_state: Dict[str, Any]) -> None:
        """根據快照資訊重建單一分析視窗"""
        if not isinstance(window_state, dict):
            return

        module_state = window_state.get("module")
        analysis_module = self._instantiate_module_from_state(module_state)
        if not analysis_module:
            return

        mdi_area = self._find_mdi_area_by_name(window_state.get("mdi_area"))
        if mdi_area is None and getattr(self, "mdi_areas", None):
            mdi_area = self.mdi_areas[0]
        if mdi_area is None:
            return

        sync_enabled = bool(window_state.get("sync_enabled", True))
        window_title = window_state.get("title")
        if not window_title and hasattr(analysis_module, "display_name"):
            window_title = getattr(analysis_module, "display_name")
        if not window_title:
            window_title = "Analysis Window"

        sub_window = PopoutSubWindow(window_title, mdi_area, analysis_module, sync_enabled=sync_enabled)
        content_widget = analysis_module.get_widget()
        sub_window.setWidget(content_widget)
        mdi_area.addSubWindow(sub_window)

        geometry = window_state.get("geometry") or {}
        try:
            width = int(geometry.get("width")) if geometry.get("width") is not None else None
            height = int(geometry.get("height")) if geometry.get("height") is not None else None
            pos_x = int(geometry.get("x")) if geometry.get("x") is not None else None
            pos_y = int(geometry.get("y")) if geometry.get("y") is not None else None
        except (TypeError, ValueError):  # noqa: BLE001
            width = height = pos_x = pos_y = None

        if width and height:
            sub_window.resize(width, height)

        if hasattr(sub_window, 'title_bar'):
            sub_window.title_bar.sync_btn.setChecked(sync_enabled)
            sub_window.toggle_x_sync()

        local_params = window_state.get("local_parameters") or {}
        if local_params.get("year") is not None:
            sub_window.local_year = str(local_params.get("year"))
        if local_params.get("race") is not None:
            sub_window.local_race = local_params.get("race")
        if local_params.get("session") is not None:
            sub_window.local_session = local_params.get("session")

        module_params = module_state.get("parameters") if isinstance(module_state, dict) else None
        self._apply_module_parameters(analysis_module, module_params)

        sub_window.update_window_title()
        sub_window.show()

        window_state_flag = window_state.get("window_state")
        if window_state_flag == "maximized":
            sub_window.showMaximized()
        elif window_state_flag == "minimized":
            sub_window.showMinimized()
        else:
            if pos_x is not None and pos_y is not None:
                sub_window.move(pos_x, pos_y)

        if hasattr(self, "active_subwindows"):
            self.active_subwindows.append(sub_window)

    def _instantiate_module_from_state(self, module_state: Optional[Dict[str, Any]]):
        """依據快照資訊建立分析模組實例"""
        if not isinstance(module_state, dict):
            return None

        module = None
        module_type = module_state.get("factory_type")

        if module_type:
            module = self._create_analysis_module(module_type, module_type_hint=module_type)

        if module is None:
            module_path = module_state.get("module_path")
            class_name = module_state.get("class_name")
            if module_path and class_name:
                try:
                    module_cls = getattr(importlib.import_module(module_path), class_name)
                    module = module_cls()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to import module %s.%s: %s", module_path, class_name, exc)
                    module = None

            if module and hasattr(module, "parameter_provider"):
                module.parameter_provider = MainWindowParameterProvider(self)
                initialize_module = getattr(module, "initialize_module", None)
                if callable(initialize_module):
                    try:
                        initialize_module()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Module initialization failed: %s", exc)

        if module and module_type and not getattr(module, "_factory_module_type", None):
            setattr(module, "_factory_module_type", module_type)

        return module

    def _apply_module_parameters(self, module, parameters: Optional[Dict[str, Any]]) -> None:
        """將快照中的參數套用到分析模組"""
        if not module or not isinstance(parameters, dict):
            return

        year_value = parameters.get("current_year") or parameters.get("year")
        race_value = parameters.get("current_race") or parameters.get("race")
        session_value = parameters.get("current_session") or parameters.get("session")

        update_kwargs: Dict[str, Any] = {}
        if year_value is not None:
            try:
                update_kwargs["year"] = int(year_value)
            except (TypeError, ValueError):  # noqa: BLE001
                update_kwargs["year"] = year_value
        if race_value is not None:
            update_kwargs["race"] = race_value
        if session_value is not None:
            update_kwargs["session"] = session_value

        update_parameters = getattr(module, "update_parameters", None)
        if callable(update_parameters) and update_kwargs:
            try:
                update_parameters(**update_kwargs)
            except TypeError:
                try:
                    update_parameters(
                        update_kwargs.get("year"),
                        update_kwargs.get("race"),
                        update_kwargs.get("session"),
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Module parameter update failed: %s", exc)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Module parameter update failed: %s", exc)

        for attr in ("driver1", "driver2", "lap1", "lap2"):
            if attr in parameters and hasattr(module, attr):
                try:
                    setattr(module, attr, parameters[attr])
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Unable to set module attribute %s: %s", attr, exc)

        load_data = getattr(module, "load_data", None)
        if callable(load_data):
            load_kwargs = {k: v for k, v in update_kwargs.items() if v is not None}
            for attr in ("driver1", "driver2", "lap1", "lap2"):
                if attr in parameters and parameters[attr] is not None:
                    load_kwargs[attr] = parameters[attr]
            try:
                load_data(**load_kwargs)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Module data load skipped: %s", exc)

    def _find_mdi_area_by_name(self, object_name: Optional[str]) -> Optional['CustomMdiArea']:
        """根據 objectName 尋找已登錄的 MDI 區域"""
        if not object_name:
            return None
        for mdi_area in getattr(self, "mdi_areas", []) or []:
            if mdi_area.objectName() == object_name:
                return mdi_area
        return None

    def export_report(self): 
        #print("[檔案] 匯出報告")
        pass
        
    def lap_analysis(self): 
        """圈速分析 - 彈出選項對話框讓使用者選擇要顯示的遙測圖表和車手"""
        params = self.get_current_parameters()
        print(f"[分析] 圈速分析 - {params['year']} {params['race']} {params['session']}")
        
        try:
            # 移除歡迎頁面（如果存在）
            self.remove_welcome_tab()
            
            # 彈出選項對話框
            dialog = LapAnalysisOptionsDialog(self)
            
            if dialog.exec_() == QDialog.Accepted:
                selected_charts = dialog.get_selected_charts()
                driver_info = dialog.get_selected_drivers()
                
                driver1 = driver_info['driver1']
                driver2 = driver_info['driver2']
                lap1_number = driver_info['lap1_number']
                lap2_number = driver_info['lap2_number']
                lap_type = driver_info['lap_type']
                is_fastest_lap = driver_info['is_fastest_lap']
                
                if not selected_charts:
                    QMessageBox.information(self, tr('info', 'Information'), tr('no_chart_selected', 'No chart selected. Window will not be opened.'))
                    return
                
                if not driver1:
                    QMessageBox.information(self, tr('info', 'Information'), tr('select_driver', 'Please select at least one driver.'))
                    return
                
                none_display = tr("none_option", "None")
                lap_word = tr("lap", "Lap")
                fastest_label = tr("fastest_lap_type", "Fastest Lap")

                print(f"[圈速分析] 使用者選擇的圖表: {selected_charts}")
                print(f"[圈速分析] 選擇的車手: 車手1={driver1}, 車手2={driver2 if driver2 else none_display}")
                if is_fastest_lap:
                    print(f"[圈速分析] 圈數設定: {fastest_label}")
                else:
                    if driver2:
                        print(f"[圈速分析] 圈數設定: 車手1第{lap1_number}{lap_word}, 車手2第{lap2_number}{lap_word}")
                    else:
                        print(f"[圈速分析] 圈數設定: 車手1第{lap1_number}{lap_word}")
                
                # 🆕 將對話框的選擇同步到主視窗參數欄
                try:
                    # 同步 Driver 1
                    if driver1 and hasattr(self, 'driver1_combo'):
                        index = self.driver1_combo.findText(driver1)
                        if index >= 0:
                            self.driver1_combo.setCurrentIndex(index)
                            print(f"[同步] Driver 1 → {driver1}")
                    
                    # 同步 Driver 2
                    if hasattr(self, 'driver2_combo'):
                        if driver2:
                            index = self.driver2_combo.findText(driver2)
                            if index >= 0:
                                self.driver2_combo.setCurrentIndex(index)
                                print(f"[同步] Driver 2 → {driver2}")
                        else:
                            # Driver 2 為 None，設定為第一個選項（通常是空或 None）
                            self.driver2_combo.setCurrentIndex(0)
                            print(f"[同步] Driver 2 → None")
                    
                    # 同步 Lap 1
                    if lap1_number and hasattr(self, 'lap1_spinbox'):
                        self.lap1_spinbox.setValue(lap1_number)
                        print(f"[同步] Lap 1 → {lap1_number}")
                    
                    # 同步 Lap 2
                    if lap2_number and hasattr(self, 'lap2_spinbox'):
                        self.lap2_spinbox.setValue(lap2_number)
                        print(f"[同步] Lap 2 → {lap2_number}")
                    
                    # 同步 Fastest Lap 選項
                    if hasattr(self, 'fastest_lap_checkbox'):
                        self.fastest_lap_checkbox.setChecked(is_fastest_lap)
                        print(f"[同步] Fastest Lap → {is_fastest_lap}")
                    
                    print(f"[同步] ✅ 主視窗參數已同步")
                except Exception as sync_error:
                    print(f"[同步] ⚠️ 參數同步失敗: {sync_error}")
                
                # 為每個選擇的圖表類型創建視窗
                for chart_type in selected_charts:
                    # 特殊處理：將速度圖表映射到速度分析
                    if chart_type == 'speed':
                        chart_type = 'speed_analysis'
                        print(f"[圈速分析] 映射 'speed' -> 'speed_analysis'")
                    
                    self.create_telemetry_window(chart_type, params, driver1, driver2, lap1_number, lap2_number, lap_type, is_fastest_lap)
                
                driver_summary = f"車手: {driver1}" + (f" vs {driver2}" if driver2 else "")
                if is_fastest_lap:
                    lap_summary = fastest_label
                else:
                    if driver2:
                        lap_summary = f"車手1第{lap1_number}{lap_word}, 車手2第{lap2_number}{lap_word}"
                    else:
                        lap_summary = f"第{lap1_number}{lap_word}"
                print(f"[OK] 圈速分析完成，已開啟 {len(selected_charts)} 個遙測圖表視窗 ({driver_summary}, {lap_summary})")
            else:
                print(f"[圈速分析] 使用者取消了分析")
                
        except Exception as e:
            print(f"[ERROR] 圈速分析失敗: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message("圈速分析錯誤", f"開啟圈速分析時發生錯誤: {e}")
    
    def create_telemetry_window(self, chart_type, params, driver1=None, driver2=None, lap1_number=1, lap2_number=1, lap_type="最快圈", is_fastest_lap=False):
        """創建單個遙測圖表視窗 - 支援速度分析"""
        print(f"[CREATE_DEBUG] ========== 創建遙測視窗 ==========")
        print(f"[CREATE_DEBUG] 圖表類型: {chart_type}")
        print(f"[CREATE_DEBUG] 參數: {params}")
        print(f"[CREATE_DEBUG] 車手: {driver1} vs {driver2}")
        print(f"[CREATE_DEBUG] 圈數: {lap1_number} vs {lap2_number}")
        
        # 檢查並移除歡迎頁面（首次使用分析功能時）
        self.check_and_remove_welcome_page()
        
        # 獲取當前分頁的 MDI 區域 - 提前定義避免變量未定義錯誤
        current_mdi_area = self.get_current_mdi_area()
        if not current_mdi_area:
            print("[ERROR] 無法獲取當前 MDI 區域")
            return
        
        try:
            # 檢查是否為速度分析 - 使用新版模組架構
            if chart_type == 'speed_analysis':
                print(f"[CREATE_DEBUG] 🎯 檢測到速度分析請求，嘗試新版模組架構")
                
                # 使用新版模組化架構創建速度分析
                try:
                    print(f"[CREATE_DEBUG] 📦 正在導入速度分析模組...")
                    from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule
                    
                    print(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = SpeedAnalysisModule()
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self)
                    analysis_module.parameter_provider = parameter_provider
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    print(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    print(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    print(f"[CREATE_DEBUG] 🚀 初始化速度分析模組...")
                    if analysis_module.initialize_module():
                        print(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        print(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        print(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        sub_window.window_closed.connect(lambda: self.on_lap_analysis_window_closed(analysis_module))
                        
                        # 設置視窗大小
                        width, height = analysis_module.get_default_size()
                        sub_window.resize(width, height)
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        print(f"[OK] [NEW_MODULE] 速度分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.on_lap_analysis_window_opened(analysis_module, "speed_analysis")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數）
                        print(f"[CREATE_DEBUG] 🚀 自動載入速度分析數據...")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap
                        )
                        
                        if success:
                            print(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            print(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        print(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        print(f"[ERROR] 速度分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    print(f"[ERROR] 速度分析模組創建失敗: {e}，回退到舊版模式")
                    import traceback
                    traceback.print_exc()
                
                print(f"[CREATE_DEBUG] ⚠️ 回退到舊版速度分析模式")
                
                # 回退：特殊處理速度分析（舊版模式）
                if driver2 is None:
                    driver2 = driver1
                    lap2_number = lap1_number
                    print(f"[SPEED] 速度分析自動設定: 車手2={driver2}, 圈數={lap2_number} (與車手1相同)")
                
                # 創建速度分析組件（舊版）
                try:
                    from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedAnalysisChartWidget
                    from modules.gui.lap_analysis.speed_analysis.speed_analysis_data_loader import SpeedAnalysisDataLoader
                    
                    chart_widget = SpeedAnalysisChartWidget()
                    
                    # 創建數據載入器
                    speed_loader = SpeedAnalysisDataLoader()
                    speed_loader.data_loaded.connect(chart_widget.update_speed_data)
                    speed_loader.load_error.connect(lambda error: print(f"[ERROR] 速度數據載入失敗: {error}"))
                    
                    # 開始載入數據
                    print(f"[SPEED] 開始載入速度數據: {driver1} vs {driver2}")
                    speed_loader.load_speed_data(
                        year=params['year'],
                        race=params['race'], 
                        session=params['session'],
                        driver1=driver1,
                        driver2=driver2,
                        lap1=lap1_number,
                        lap2=lap2_number,
                        is_fastest_lap=is_fastest_lap
                    )
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.speed_loader = speed_loader
                    
                    # 舊版速度分析視窗創建（僅作為回退，應該避免使用）
                    print(f"[WARNING] [LEGACY] 使用舊版速度分析創建模式")
                    
                except ImportError as e:
                    print(f"[ERROR] 無法導入速度分析模組: {e}")
                    chart_widget = self.create_placeholder_telemetry_widget('speed_analysis')
                
            elif chart_type == 'rpm':
                # RPM分析 - 使用新版模組架構
                print(f"[CREATE_DEBUG] 🔄 檢測到RPM分析請求，嘗試新版模組架構")
                
                # 使用新版模組化架構創建RPM分析
                try:
                    print(f"[CREATE_DEBUG] 📦 正在導入RPM分析模組...")
                    from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi import RPMAnalysisModule
                    print(f"[CREATE_DEBUG] ✅ RPM分析模組導入成功")
                    
                    print(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = RPMAnalysisModule()
                    print(f"[CREATE_DEBUG] ✅ RPM模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self)
                    analysis_module.parameter_provider = parameter_provider
                    print(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    print(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    print(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    print(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    print(f"[CREATE_DEBUG] 🚀 初始化RPM分析模組...")
                    if analysis_module.initialize_module():
                        print(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        print(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        print(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        sub_window.window_closed.connect(lambda: self.on_lap_analysis_window_closed(analysis_module))
                        
                        # 設置視窗大小
                        width, height = analysis_module.get_default_size()
                        sub_window.resize(width, height)
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        print(f"[OK] [NEW_MODULE] RPM分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.on_lap_analysis_window_opened(analysis_module, "rpm")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數）
                        print(f"[CREATE_DEBUG] 🚀 自動載入RPM分析數據...")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap
                        )
                        
                        if success:
                            print(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            print(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        print(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        print(f"[ERROR] RPM分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    print(f"[ERROR] ❌ RPM分析模組創建失敗: {e}")
                    print(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    print(f"[ERROR] 回退到舊版模式")
                    import traceback
                    print(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                print(f"[CREATE_DEBUG] ⚠️ 回退到舊版RPM分析模式")
                
                # 回退：舊版RPM分析模式
                
                try:
                    from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget import RPMAnalysisChartWidget
                    from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_data_loader import RPMAnalysisDataLoader
                    
                    print(f"[CREATE_DEBUG] 📦 創建RPM分析組件...")
                    chart_widget = RPMAnalysisChartWidget()
                    
                    # 創建RPM資料載入器
                    print(f"[CREATE_DEBUG] � 創建RPM資料載入器...")
                    rpm_loader = RPMAnalysisDataLoader()
                    rpm_loader.data_loaded.connect(chart_widget.update_rpm_data)
                    rpm_loader.load_error.connect(lambda error: print(f"[ERROR] RPM資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    print(f"[CREATE_DEBUG] 🚀 開始載入RPM資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    rpm_loader.load_rpm_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.rpm_loader = rpm_loader
                    
                    print(f"[OK] RPM分析組件創建成功")
                    
                except ImportError as e:
                    print(f"[ERROR] 無法導入RPM分析模組: {e}")
                    chart_widget = self.create_placeholder_telemetry_widget('rpm')
                except Exception as e:
                    print(f"[ERROR] RPM分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.create_placeholder_telemetry_widget('rpm')
                
            elif chart_type == 'gear':
                # 檔位分析 - 使用新版模組架構
                print(f"[CREATE_DEBUG] 🔄 檢測到檔位分析請求，嘗試新版模組架構")
                
                # 使用新版模組化架構創建檔位分析
                try:
                    print(f"[CREATE_DEBUG] 📦 正在導入檔位分析模組...")
                    from modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi import GearAnalysisModule
                    print(f"[CREATE_DEBUG] ✅ 檔位分析模組導入成功")
                    
                    print(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = GearAnalysisModule()
                    print(f"[CREATE_DEBUG] ✅ 檔位模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self)
                    analysis_module.parameter_provider = parameter_provider
                    print(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    print(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    print(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    print(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    print(f"[CREATE_DEBUG] 🚀 初始化檔位分析模組...")
                    if analysis_module.initialize_module():
                        print(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        print(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        print(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        sub_window.window_closed.connect(lambda: self.on_lap_analysis_window_closed(analysis_module))
                        
                        # 設置視窗大小
                        width, height = analysis_module.get_default_size()
                        sub_window.resize(width, height)
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        print(f"[OK] [NEW_MODULE] 檔位分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.on_lap_analysis_window_opened(analysis_module, "gear")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數）
                        print(f"[CREATE_DEBUG] 🚀 自動載入檔位分析數據...")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap
                        )
                        
                        if success:
                            print(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            print(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        print(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        print(f"[ERROR] 檔位分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    print(f"[ERROR] ❌ 檔位分析模組創建失敗: {e}")
                    print(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    print(f"[ERROR] 回退到舊版模式")
                    import traceback
                    print(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                print(f"[CREATE_DEBUG] ⚠️ 回退到舊版檔位分析模式")
                
                # 回退：舊版檔位分析模式
                try:
                    from modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget import GearAnalysisChartWidget
                    from modules.gui.lap_analysis.gear_analysis.gear_analysis_data_loader import GearAnalysisDataLoader
                    
                    print(f"[CREATE_DEBUG] 📦 創建檔位分析組件...")
                    chart_widget = GearAnalysisChartWidget()
                    
                    # 創建檔位資料載入器
                    print(f"[CREATE_DEBUG] 📊 創建檔位資料載入器...")
                    gear_loader = GearAnalysisDataLoader()
                    gear_loader.data_loaded.connect(chart_widget.update_gear_data)
                    gear_loader.load_error.connect(lambda error: print(f"[ERROR] 檔位資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    print(f"[CREATE_DEBUG] 🚀 開始載入檔位資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    gear_loader.load_gear_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.gear_loader = gear_loader
                    
                    print(f"[OK] 檔位分析組件創建成功")
                    
                except ImportError as e:
                    print(f"[ERROR] 無法導入檔位分析模組: {e}")
                    chart_widget = self.create_placeholder_telemetry_widget('gear')
                except Exception as e:
                    print(f"[ERROR] 檔位分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.create_placeholder_telemetry_widget('gear')

            elif chart_type == 'Speeddiff' or chart_type == 'speeddiff' or chart_type == 'speed_diff':
                # 速度差分析 - 使用新版模組架構
                print(f"[CREATE_DEBUG] 🔄 檢測到速度差分析請求，嘗試新版模組架構")

                # 使用新版模組化架構創建速度差分析
                try:
                    print(f"[CREATE_DEBUG] 📦 正在導入速度差分析模組...")
                    from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi import SpeeddiffAnalysisModule
                    print(f"[CREATE_DEBUG] ✅ 速度差分析模組導入成功")
                    
                    print(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = SpeeddiffAnalysisModule()
                    print(f"[CREATE_DEBUG] ✅ 速度差模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self)
                    analysis_module.parameter_provider = parameter_provider
                    print(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    print(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    print(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    print(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    print(f"[CREATE_DEBUG] 🚀 初始化速度差分析模組...")
                    if analysis_module.initialize_module():
                        print(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=analysis_module.driver1,
                            driver2=analysis_module.driver2,
                            lap1=analysis_module.lap1,
                            lap2=analysis_module.lap2
                        )
                        print(f"[CREATE_DEBUG] 📝 視窗標題: {window_title}")
                        
                        # 創建子視窗並設置標題 - 使用與 RPM 分析相同的模式
                        print(f"[CREATE_DEBUG] 🖼️ 創建MDI子視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 設置視窗大小
                        sub_window.resize(1200, 800)
                        print(f"[CREATE_DEBUG] ✅ 子視窗創建成功")
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        print(f"[OK] [NEW_MODULE] 速度差分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.on_lap_analysis_window_opened(analysis_module, "Speeddiff")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數）
                        print(f"[CREATE_DEBUG] 🚀 自動載入速度差分析數據...")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap
                        )
                        
                        if success:
                            print(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            print(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        print(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        print(f"[ERROR] 速度差分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    print(f"[ERROR] ❌ 速度差分析模組創建失敗: {e}")
                    print(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    print(f"[ERROR] 回退到舊版模式")
                    import traceback
                    print(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                print(f"[CREATE_DEBUG] ⚠️ 回退到舊版速度差分析模式")
                
                # 回退：舊版速度差分析模式
                try:
                    from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_chart_widget import SpeeddiffAnalysisChartWidget
                    from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_data_loader import SpeeddiffAnalysisDataLoader
                    
                    print(f"[CREATE_DEBUG] 📦 創建速度差分析組件...")
                    chart_widget = SpeeddiffAnalysisChartWidget()
                    
                    # 創建速度差資料載入器
                    print(f"[CREATE_DEBUG] 📊 創建速度差資料載入器...")
                    Speeddiff_loader = SpeeddiffAnalysisDataLoader()
                    Speeddiff_loader.data_loaded.connect(chart_widget.update_speeddiff_data)
                    Speeddiff_loader.load_error.connect(lambda error: print(f"[ERROR] 速度差資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    print(f"[CREATE_DEBUG] 🚀 開始載入速度差資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    Speeddiff_loader.load_speeddiff_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.Speeddiff_loader = Speeddiff_loader
                    
                    print(f"[OK] 速度差分析組件創建成功")
                    
                except ImportError as e:
                    print(f"[ERROR] 無法導入速度差分析模組: {e}")
                    chart_widget = self.create_placeholder_telemetry_widget('speeddiff')
                except Exception as e:
                    print(f"[ERROR] 速度差分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.create_placeholder_telemetry_widget('speeddiff')
                
            elif chart_type == 'acceleration':
                # 加速度分析 - 使用新版模組架構
                print(f"[CREATE_DEBUG] 🔄 檢測到加速度分析請求，嘗試新版模組架構")
                
                # 使用新版模組化架構創建加速度分析
                try:
                    print(f"[CREATE_DEBUG] 📦 正在導入加速度分析模組...")
                    from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi import accelerationAnalysisModule
                    print(f"[CREATE_DEBUG] ✅ 加速度分析模組導入成功")
                    
                    print(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = accelerationAnalysisModule()
                    print(f"[CREATE_DEBUG] ✅ 加速度模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self)
                    analysis_module.parameter_provider = parameter_provider
                    print(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    print(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    print(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    print(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    print(f"[CREATE_DEBUG] 🚀 初始化加速度分析模組...")
                    if analysis_module.initialize_module():
                        print(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=analysis_module.driver1,
                            driver2=analysis_module.driver2,
                            lap1=analysis_module.lap1,
                            lap2=analysis_module.lap2
                        )
                        print(f"[CREATE_DEBUG] 📝 視窗標題: {window_title}")
                        
                        # 創建子視窗並設置標題 - 使用與 RPM 分析相同的模式
                        print(f"[CREATE_DEBUG] 🖼️ 創建MDI子視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 設置視窗大小
                        sub_window.resize(1200, 800)
                        print(f"[CREATE_DEBUG] ✅ 子視窗創建成功")
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        print(f"[OK] [NEW_MODULE] 加速度分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.on_lap_analysis_window_opened(analysis_module, "acceleration")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數）
                        print(f"[CREATE_DEBUG] 🚀 自動載入加速度分析數據...")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap
                        )
                        
                        if success:
                            print(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            print(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        print(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        print(f"[ERROR] 加速度分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    print(f"[ERROR] ❌ 加速度分析模組創建失敗: {e}")
                    print(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    print(f"[ERROR] 回退到舊版模式")
                    import traceback
                    print(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                print(f"[CREATE_DEBUG] ⚠️ 回退到舊版加速度分析模式")
                
                # 回退：舊版加速度分析模式
                try:
                    from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget import accelerationAnalysisChartWidget
                    from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_data_loader import accelerationAnalysisDataLoader
                    
                    print(f"[CREATE_DEBUG] 📦 創建加速度分析組件...")
                    chart_widget = accelerationAnalysisChartWidget()
                    
                    # 創建加速度資料載入器
                    print(f"[CREATE_DEBUG] 📊 創建加速度資料載入器...")
                    acceleration_loader = accelerationAnalysisDataLoader()
                    acceleration_loader.data_loaded.connect(chart_widget.update_acceleration_data)
                    acceleration_loader.load_error.connect(lambda error: print(f"[ERROR] 加速度資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    print(f"[CREATE_DEBUG] 🚀 開始載入加速度資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    acceleration_loader.load_acceleration_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.acceleration_loader = acceleration_loader
                    
                    print(f"[OK] 加速度分析組件創建成功")
                    
                except ImportError as e:
                    print(f"[ERROR] 無法導入加速度分析模組: {e}")
                    chart_widget = self.create_placeholder_telemetry_widget('acceleration')
                except Exception as e:
                    print(f"[ERROR] 加速度分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.create_placeholder_telemetry_widget('acceleration')

            elif chart_type == 'throttle':
                # 油門分析 - 使用新版模組架構
                print(f"[CREATE_DEBUG] 🔄 檢測到油門分析請求，使用新版模組架構")
                
                # 使用新版模組化架構創建油門分析
                try:
                    print(f"[CREATE_DEBUG] 📦 正在導入油門分析模組...")
                    from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import ThrottleAnalysisModule
                    print(f"[CREATE_DEBUG] ✅ 油門分析模組導入成功")
                    
                    print(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = ThrottleAnalysisModule()
                    print(f"[CREATE_DEBUG] ✅ 油門模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self)
                    analysis_module.parameter_provider = parameter_provider
                    print(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    print(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    print(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    print(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    print(f"[CREATE_DEBUG] 🚀 初始化油門分析模組...")
                    if analysis_module.initialize_module():
                        print(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        print(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        print(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        sub_window.window_closed.connect(lambda: self.on_lap_analysis_window_closed(analysis_module))
                        
                        # 設置視窗大小
                        sub_window.resize(1200, 800)
                        
                        # *** 關鍵修復：添加視窗到MDI區域 ***
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        print(f"[OK] [NEW_MODULE] 油門分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.on_lap_analysis_window_opened(analysis_module, "throttle")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數）- 與速度分析完全一致
                        print(f"[CREATE_DEBUG] 🚀 自動載入油門分析數據...")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap
                        )
                        
                        if success:
                            print(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            print(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        print(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        print(f"[ERROR] 油門分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    print(f"[ERROR] 油門分析模組創建失敗: {e}，回退到舊版模式")
                    import traceback
                    traceback.print_exc()
                
                print(f"[CREATE_DEBUG] ⚠️ 回退到舊版油門分析模式")
                
                # 回退：特殊處理油門分析（舊版模式）
                if driver2 is None:
                    driver2 = driver1
                    lap2_number = lap1_number
                    print(f"[THROTTLE] 油門分析自動設定: 車手2={driver2}, 圈數={lap2_number} (與車手1相同)")

            elif chart_type == 'distancediff':
                # 距離差分析 - 使用新版模組架構
                print(f"[CREATE_DEBUG] 🔄 檢測到距離差分析請求，嘗試新版模組架構")

                # 使用新版模組化架構創建距離差分析
                try:
                    print(f"[CREATE_DEBUG] 📦 正在導入距離差分析模組...")
                    from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi import distancediffAnalysisModule
                    print(f"[CREATE_DEBUG] ✅ 距離差分析模組導入成功")
                    
                    print(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = distancediffAnalysisModule()
                    print(f"[CREATE_DEBUG] ✅ 距離差模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self)
                    analysis_module.parameter_provider = parameter_provider
                    print(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    print(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    print(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    print(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    print(f"[CREATE_DEBUG] 🚀 初始化距離差分析模組...")
                    if analysis_module.initialize_module():
                        print(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=analysis_module.driver1,
                            driver2=analysis_module.driver2,
                            lap1=analysis_module.lap1,
                            lap2=analysis_module.lap2
                        )
                        print(f"[CREATE_DEBUG] 📝 視窗標題: {window_title}")
                        
                        # 創建子視窗並設置標題 - 使用與 RPM 分析相同的模式
                        print(f"[CREATE_DEBUG] 🖼️ 創建MDI子視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 設置視窗大小
                        sub_window.resize(1200, 800)
                        print(f"[CREATE_DEBUG] ✅ 子視窗創建成功")
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        print(f"[OK] [NEW_MODULE] 距離差分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.on_lap_analysis_window_opened(analysis_module, "distancediff")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數）
                        print(f"[CREATE_DEBUG] 🚀 自動載入距離差分析數據...")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap
                        )
                        
                        if success:
                            print(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            print(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        print(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        print(f"[ERROR] 距離差分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    print(f"[ERROR] ❌ 距離差分析模組創建失敗: {e}")
                    print(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    print(f"[ERROR] 回退到舊版模式")
                    import traceback
                    print(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                print(f"[CREATE_DEBUG] ⚠️ 回退到舊版距離差分析模式")
                
                # 回退：舊版距離差分析模式
                try:
                    from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_chart_widget import distancediffAnalysisChartWidget
                    from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_data_loader import distancediffAnalysisDataLoader
                    
                    print(f"[CREATE_DEBUG] 📦 創建距離差分析組件...")
                    chart_widget = distancediffAnalysisChartWidget()
                    
                    # 創建距離差資料載入器
                    print(f"[CREATE_DEBUG] 📊 創建距離差資料載入器...")
                    distancediff_loader = distancediffAnalysisDataLoader()
                    distancediff_loader.data_loaded.connect(chart_widget.update_distancediff_data)
                    distancediff_loader.load_error.connect(lambda error: print(f"[ERROR] 距離差資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    print(f"[CREATE_DEBUG] 🚀 開始載入距離差資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    distancediff_loader.load_distancediff_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.distancediff_loader = distancediff_loader
                    
                    print(f"[OK] 距離差分析組件創建成功")
                    
                except ImportError as e:
                    print(f"[ERROR] 無法導入距離差分析模組: {e}")
                    chart_widget = self.create_placeholder_telemetry_widget('distancediff')
                except Exception as e:
                    print(f"[ERROR] 距離差分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.create_placeholder_telemetry_widget('distancediff')
                
            elif chart_type == 'brake':
                # 使用新的煞車分析模組
                print(f"[CREATE_DEBUG] 🎯 檢測到煞車分析請求，嘗試新版模組架構")
                
                try:
                    print(f"[CREATE_DEBUG] 📦 正在導入煞車分析模組...")
                    from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeAnalysisModule
                    
                    print(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = BrakeAnalysisModule()
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self)
                    analysis_module.parameter_provider = parameter_provider
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    print(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    print(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    print(f"[CREATE_DEBUG] 🚀 初始化煞車分析模組...")
                    if analysis_module.initialize_module():
                        print(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        print(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        print(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        sub_window.window_closed.connect(lambda: self.on_lap_analysis_window_closed(analysis_module))
                        
                        # 設置視窗大小
                        width, height = analysis_module.get_default_size()
                        sub_window.resize(width, height)
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        print(f"[OK] [NEW_MODULE] 煞車分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.on_lap_analysis_window_opened(analysis_module, "brake")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數）
                        print(f"[CREATE_DEBUG] 🚀 自動載入煞車分析數據...")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap
                        )
                        
                        if success:
                            print(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            print(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        print(f"[CREATE_DEBUG] ========== 新版煞車模組創建完成 ==========")
                        return
                    else:
                        print(f"[ERROR] 煞車分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    print(f"[ERROR] 煞車分析模組創建失敗: {e}，回退到舊版模式")
                    import traceback
                    traceback.print_exc()
                
                print(f"[CREATE_DEBUG] ⚠️ 回退到舊版煞車分析模式")
                # 回退到舊版
                chart_widget = TelemetryChartWidget(chart_type)
                
            elif chart_type in ['speed', 'steering']:
                # 這些是現有的TelemetryChartWidget支援的類型
                chart_widget = TelemetryChartWidget(chart_type)
            else:
                # 對於其他類型，創建佔位符Widget
                chart_widget = self.create_placeholder_telemetry_widget(chart_type)
            
            # 獲取圖表類型的中文名稱和圖示
            chart_info = self.get_chart_info(chart_type)
            
            # 構建視窗標題，包含車手和圈數資訊
            driver_info = ""
            if driver1:
                driver_info = f" - {driver1}"
                if driver2:
                    driver_info += f" vs {driver2}"
            
            # 添加圈數資訊
            lap_info = ""
            if is_fastest_lap:
                lap_info = " (最速圈)"
            else:
                if driver2:
                    lap_info = f" (車手1第{lap1_number}圈, 車手2第{lap2_number}圈)"
                else:
                    lap_info = f" (第{lap1_number}圈)"
            
            window_title = f"{chart_info['icon']} {chart_info['name']}{driver_info}{lap_info} - {params['year']} {params['race']} {params['session']}"
            
            sub_window = PopoutSubWindow(window_title, current_mdi_area)
            sub_window.setWidget(chart_widget)
            
            # 檢查是否為圈速分析相關視窗，如果是則連接關閉信號
            lap_analysis_types = ['speed', 'brake', 'throttle', 'steering', 'gear', 'rpm']
            if chart_type in lap_analysis_types:
                sub_window.window_closed.connect(lambda: self.on_lap_analysis_window_closed(chart_widget))
            
            # 設置視窗大小 - 速度分析需要更大的視窗
            if chart_type == 'speed_analysis':
                sub_window.resize(900, 600)  # 速度分析使用更大尺寸
            else:
                sub_window.resize(600, 400)
            
            # 添加到MDI區域
            current_mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            print(f"[OK] 已創建遙測視窗: {window_title}")
            
            # 檢查是否為圈速分析相關視窗，如果是則通知主視窗
            # 包含所有圈速分析子模組類型
            lap_analysis_types = [
                'speed_analysis',  # 速度分析模組
                'speed',           # 傳統速度圖表
                'brake',           # 煞車分析
                'throttle',        # 油門分析
                'steering',        # 轉向分析
                'gear',            # 檔位分析
                'rpm',             # RPM分析模組
                'acceleration',    # 加速度分析
                'speed_diff',      # 速度差分析
                'distancediff'     # 累積距離差分析
            ]
            if chart_type in lap_analysis_types:
                print(f"[LAP_CONTROL] 🎯 檢測到圈速分析類型: {chart_type} - 觸發工具欄控件")
                self.on_lap_analysis_window_opened(chart_widget, chart_type)
            
        except Exception as e:
            print(f"[ERROR] 創建遙測視窗失敗 ({chart_type}): {e}")
    
    def get_current_mdi_area(self):
        """獲取當前分頁的 MDI 區域"""
        try:
            # 獲取當前分頁
            current_tab = self.tab_widget.currentWidget()
            if not current_tab:
                print("[ERROR] 無法獲取當前分頁")
                return None
            
            # 在當前分頁中查找 CustomMdiArea
            def find_mdi_area(widget):
                if isinstance(widget, CustomMdiArea):
                    return widget
                
                # 遞歸查找子元件
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            result = find_mdi_area(child)
                            if result:
                                return result
                return None
            
            mdi_area = find_mdi_area(current_tab)
            if not mdi_area:
                print("[ERROR] 在當前分頁中未找到 MDI 區域")
                return None
            
            print(f"[OK] 找到當前 MDI 區域: {mdi_area.objectName()}")
            return mdi_area
            
        except Exception as e:
            print(f"[ERROR] 獲取當前 MDI 區域失敗: {e}")
            return None

    def create_placeholder_telemetry_widget(self, chart_type):
        """為尚未實現的圖表類型創建佔位符Widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        chart_info = self.get_chart_info(chart_type)
        
        # 標題
        title_label = QLabel(f"{chart_info['icon']} {chart_info['name']}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078d4; margin: 20px;")
        layout.addWidget(title_label)
        
        # 訊息
        message_label = QLabel("此圖表類型正在開發中...\n請等待後續版本更新")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("font-size: 14px; color: #666; margin: 20px;")
        layout.addWidget(message_label)
        
        # 狀態標籤
        status_label = QLabel("🚧 開發中 🚧")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("font-size: 16px; color: #ff6600; font-weight: bold; margin: 20px;")
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        return widget
    
    def get_chart_info(self, chart_type):
        """獲取圖表類型的資訊"""
        chart_info_map = {
            'speed_analysis': {'name': '速度分析', 'icon': '⚡'},  # 新增速度分析
            # 'speed': {'name': '速度圖表', 'icon': '🏃'},  # 移除速度圖表
            'brake': {'name': '煞車圖表', 'icon': '🛑'},
            'throttle': {'name': '油門圖表', 'icon': '⚡'},
            'steering': {'name': '轉向圖表', 'icon': '🎯'},
            'gear': {'name': '檔位圖表', 'icon': '⚙️'},
            'rpm': {'name': '轉速圖表', 'icon': '🔄'},
            'acceleration': {'name': '加速度圖表', 'icon': '📈'},
            'speed_diff': {'name': '速度差圖表', 'icon': '📊'},
            'distancediff': {'name': '累積距離差圖表', 'icon': '📏'}
        }
        
        return chart_info_map.get(chart_type, {'name': '未知圖表', 'icon': '❓'})
        
    def open_track_analysis_window(self):
        """開啟賽道分析視窗"""
        try:
            # 檢查是否為首次使用分析功能
            self.check_and_remove_welcome_page()
            
            # 檢查模組是否可用並決定使用的實作
            track_module = None
            track_widget = None
            use_universal = False

            try:
                from modules.gui.track_analysis import TrackAnalysisUniversal
                use_universal = True
                print("[OK] TrackAnalysisUniversal 可用")
            except ImportError as universal_error:
                print(f"[WARN] TrackAnalysisUniversal 導入失敗: {universal_error}")
                try:
                    from modules.gui.track_analysis import TrackAnalysisModule
                    print("[WARN] 回退至 legacy TrackAnalysisModule")
                except ImportError:
                    from core.gui_i18n import tr
                    QMessageBox.warning(self, tr('warning', 'Warning'), tr('track_module_unavailable', 'Track analysis module is not available'))
                    return

            # 創建參數提供者
            parameter_provider = MainWindowParameterProvider(self)
            
            # 獲取當前參數
            current_year = parameter_provider.get_current_year()
            current_race = parameter_provider.get_current_race()
            current_session = parameter_provider.get_current_session()
            default_size = None

            if use_universal:
                try:
                    module_instance = TrackAnalysisUniversal(main_window=self)
                    module_instance.parameter_provider = parameter_provider

                    try:
                        year_value = int(current_year)
                    except (TypeError, ValueError):
                        year_value = current_year

                    module_instance.update_parameters(
                        year=year_value,
                        race=current_race,
                        session=current_session
                    )

                    track_module = module_instance
                    track_widget = module_instance.get_widget()
                    window_title = module_instance.get_window_title(current_year, current_race, current_session)
                    default_size = module_instance.get_default_size()
                    print(f"[OK] 使用 TrackAnalysisUniversal 開啟視窗: {window_title}")
                except Exception as exc:
                    print(f"[ERROR] TrackAnalysisUniversal 初始化失敗，回退 Legacy: {exc}")
                    use_universal = False

            if not use_universal:
                # 確保 legacy 類別可用
                from modules.gui.track_analysis import TrackAnalysisModule

                track_module = TrackAnalysisModule(
                    year=current_year,
                    race=current_race,
                    session=current_session
                )
                track_widget = track_module
                window_title = track_module.get_window_title(current_year, current_race, current_session)
                default_size = None
                print(f"[OK] 使用 legacy TrackAnalysisModule 開啟視窗: {window_title}")
            
            # 獲取當前 MDI 區域
            current_mdi_area = self.get_current_mdi_area()
            if not current_mdi_area:
                from core.gui_i18n import tr
                QMessageBox.warning(self, tr('warning', 'Warning'), tr('mdi_area_not_found', 'Cannot find current MDI area'))
                return
            
            # 創建 PopoutSubWindow
            sub_window = PopoutSubWindow(
                title=window_title,
                parent_mdi=current_mdi_area,  # 使用當前 MDI 區域
                analysis_module=track_module,  # 傳遞分析模組
                sync_enabled=True,  # 預設使用同步模式
                parameter_provider=parameter_provider,
                global_signal_manager=getattr(self, 'global_signal_manager', None)
            )
            
            # 設置賽道分析模組為視窗內容
            sub_window.setWidget(track_widget)
            
            # 添加到 MDI 區域
            current_mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            # 連接信號
            sub_window.window_closed.connect(lambda: self.on_subwindow_closed(sub_window))
            if hasattr(track_module, 'module_error'):
                track_module.module_error.connect(lambda msg: self.show_error_message("賽道分析錯誤", msg))
            
            # 記錄視窗
            self.active_subwindows.append(sub_window)
            
            # 更新狀態
            print(f"[STATUS] 已開啟賽道分析視窗: {window_title}")

            # 依模組建議尺寸調整視窗大小
            if default_size and isinstance(default_size, (tuple, list)) and len(default_size) == 2:
                sub_window.resize(default_size[0], default_size[1])
            
        except Exception as e:
            from core.gui_i18n import tr
            QMessageBox.critical(self, tr('error', 'Error'), f"{tr('track_window_error', 'Cannot open track analysis window')}: {str(e)}")
            print(f"[STATUS] 賽道分析視窗開啟失敗: {str(e)}")
    
    def rain_analysis(self):
        """開啟降雨分析 - 使用通用圖表系統"""
        try:
            # 移除歡迎頁面（如果存在）
            self.remove_welcome_tab()
            
            params = self.get_current_parameters()
            print(f"[RAIN] {params['year']} {params['race']} {params['session']}")
            
            # 導入新的雨量分析模組 (使用通用圖表)
            from modules.gui.rain_analysis.rain_analysis_module import RainAnalysisModuleAdapter
            
            # 創建雨量分析模組
            rain_widget = RainAnalysisModuleAdapter(
                year=params['year'],
                race=params['race'], 
                session=params['session']
            )
            
            # [TOOL] 修正：使用新的標題格式
            tab_title = f"Rain Analysis_{params['year']}_{params['race']}_{params['session']}"
            
            # 添加到主分頁控件 (使用空字串隱藏標題)
            tab_index = self.tab_widget.addTab(rain_widget, "")
            self.tab_widget.setCurrentIndex(tab_index)
            
            # 添加到活動分頁列表
            self.active_analysis_tabs.append(tab_title)
            
            print(f"[OK] 降雨分析頁面已開啟: {tab_title} (使用通用圖表系統)")
            
        except ImportError as e:
            print(f"[ERROR] 降雨分析組件導入失敗: {e}")
            self.show_error_message("模組錯誤", f"無法載入降雨分析組件: {e}")
        except Exception as e:
            print(f"[ERROR] 降雨分析開啟失敗: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message("降雨分析錯誤", f"開啟降雨分析時發生錯誤: {e}")
    
    def open_telemetry_analysis(self):
        """開啟單場賽事總攬模組"""
        try:
            # 移除歡迎頁面（如果存在）
            self.remove_welcome_tab()
            
            params = self.get_current_parameters()
            print(f"[分析] [TELEMETRY] 單場賽事總攬 - {params['year']} {params['race']} {params['session']}")
            
            # 導入單場賽事總攬模組
            from modules.gui.telemetry_analysis_mdi import TelemetryAnalysisModule
            
            # 創建模組實例
            telemetry_module = TelemetryAnalysisModule()
            
            # 設置參數提供者
            parameter_provider = MainWindowParameterProvider(self)
            telemetry_module.parameter_provider = parameter_provider
            
            # 設置當前參數
            telemetry_module.current_year = str(params['year'])
            telemetry_module.current_race = params['race']
            telemetry_module.current_session = params['session']
            
            # 初始化模組
            if telemetry_module.initialize_module():
                print(f"[OK] 單場賽事總攬模組初始化成功")
                
                # 創建子視窗
                subwindow = QMdiSubWindow()
                subwindow.setWidget(telemetry_module.get_widget())
                
                # 設置視窗標題
                window_title = telemetry_module.get_window_title(params['year'], params['race'], params['session'])
                subwindow.setWindowTitle(window_title)
                
                # 設置視窗大小
                default_size = telemetry_module.get_default_size()
                subwindow.resize(default_size[0], default_size[1])
                
                # 添加到MDI區域 - 獲取當前活動的 MDI 區域
                current_mdi = self.get_current_mdi_area()
                if current_mdi:
                    current_mdi.addSubWindow(subwindow)
                    subwindow.show()
                    
                    # 觸發參數更新以載入數據
                    telemetry_module.update_parameters(params['year'], params['race'], params['session'])
                    
                    print(f"[OK] 單場賽事總攬視窗已開啟: {window_title}")
                else:
                    print("[ERROR] 無法獲取當前 MDI 區域")
                    self.show_error_message("錯誤", "無法獲取當前 MDI 區域")
                    return
                
            else:
                print(f"[ERROR] 單場賽事總攬模組初始化失敗")
                self.show_error_message("模組錯誤", "單場賽事總攬模組初始化失敗")
            
        except ImportError as e:
            print(f"[ERROR] 單場賽事總攬模組導入失敗: {e}")
            self.show_error_message("模組錯誤", f"無法載入單場賽事總覽模組: {e}")
        except Exception as e:
            print(f"[ERROR] 單場賽事總覽開啟失敗: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message("單場賽事總覽錯誤", f"開啟單場賽事總覽時發生錯誤: {e}")
            
    def telemetry_comparison(self): 
        params = self.get_current_parameters()
        #print(f"[分析] 遙測比較 - {params['year']} {params['race']} {params['session']}")
        pass
        
    def driver_comparison(self): 
        params = self.get_current_parameters()
        #print(f"[分析] 車手比較 - {params['year']} {params['race']} {params['session']}")
        pass
        
    def sector_analysis(self): 
        #print("[分析] 扇區分析")
        pass
    def tile_windows(self):
        """重新排列視窗 - 智能平鋪當前活動MDI區域中的所有子視窗"""
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        
        # 首先檢查當前分頁是否本身就是MDI區域
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            # 否則在分頁的子元件中查找
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            return
            
        # 獲取所有子視窗並過濾出可見的視窗
        all_subwindows = mdi_area.subWindowList()
        # 只包含可見且未關閉的視窗
        subwindows = [sw for sw in all_subwindows if sw.isVisible() and not sw.isWindowModified()]
        print(f"[TILE DEBUG] 找到 {len(all_subwindows)} 個子視窗，其中 {len(subwindows)} 個可見")
        
        if not subwindows:
            print(f"[TILE DEBUG] 沒有可見的子視窗需要排列")
            return
        
        # 移除有問題的清理邏輯 - 直接使用現有的子視窗列表
        print(f"[TILE DEBUG] 準備排列 {len(subwindows)} 個視窗")
        
        # 計算排列配置
        available_width = mdi_area.width() - 20  # 預留邊距
        available_height = mdi_area.height() - 20
        print(f"[TILE DEBUG] MDI區域大小: {mdi_area.width()}x{mdi_area.height()}")
        print(f"[TILE DEBUG] 可用空間: {available_width}x{available_height}")
        
        # 計算最佳的行列配置
        num_windows = len(subwindows)
        print(f"[TILE DEBUG] 視窗數量: {num_windows}")
        
        if num_windows == 0:
            print(f"[TILE DEBUG] 視窗數量為0，退出")
            return  # 沒有視窗需要排列
            
        cols = int(num_windows ** 0.5)
        print(f"[TILE DEBUG] 初始計算 cols: {cols}")
        
        if cols == 0:  # 防止除零錯誤
            cols = 1
            print(f"[TILE DEBUG] cols 修正為 1")
            
        if cols * cols < num_windows:
            cols += 1
            print(f"[TILE DEBUG] cols 調整為: {cols}")
            
        rows = (num_windows + cols - 1) // cols
        print(f"[TILE DEBUG] 計算得到 rows: {rows}")
        
        if rows == 0:  # 額外保護
            rows = 1
            print(f"[TILE DEBUG] rows 修正為 1")
        
        # 計算每個視窗的尺寸
        window_width = available_width // cols if cols > 0 else available_width
        window_height = available_height // rows if rows > 0 else available_height
        print(f"[TILE DEBUG] 每個視窗尺寸: {window_width}x{window_height}")
        
        # 確保最小尺寸
        min_width, min_height = 250, 150
        window_width = max(window_width, min_width)
        window_height = max(window_height, min_height)
        print(f"[TILE DEBUG] 調整後視窗尺寸: {window_width}x{window_height}")
        
        # 排列視窗
        print(f"[TILE DEBUG] 開始排列 {len(subwindows)} 個視窗，配置: {rows}行 x {cols}列")
        
        # 預檢查：確保所有視窗的基本設定一致
        print(f"[TILE DEBUG] ========== 預檢查視窗設定 ==========")
        for i, subwindow in enumerate(subwindows):
            widget = subwindow.widget()
            if widget:
                min_size = widget.minimumSize()
                size_policy = widget.sizePolicy()
                print(f"[TILE CHECK] 視窗 {i}: 最小尺寸({min_size.width()}x{min_size.height()}), 尺寸策略({size_policy.horizontalPolicy()}x{size_policy.verticalPolicy()})")
                
                # 檢查是否有調試方法可以調用
                if hasattr(widget, 'debug_window_status'):
                    print(f"[TILE CHECK] 調用視窗 {i} 的狀態報告:")
                    widget.debug_window_status()
        print(f"[TILE DEBUG] ========== 預檢查完成 ==========")
        
        for i, subwindow in enumerate(subwindows):
            row = i // cols
            col = i % cols
            
            x = col * window_width + 10
            y = row * window_height + 10
            
            print(f"[TILE DEBUG] 視窗 {i}: 位置({x}, {y}) 尺寸({window_width}, {window_height})")
            
            # 設置視窗位置和尺寸
            subwindow.setGeometry(x, y, window_width, window_height)
            
            # 確保視窗可見和正常化
            subwindow.showNormal()
            subwindow.raise_()
            
            # 強制處理事件，確保尺寸更新完成
            QApplication.processEvents()
            
            # 檢查實際尺寸並調試
            actual_size = subwindow.size()
            print(f"[TILE DEBUG] 視窗 {i} 實際尺寸: {actual_size.width()}x{actual_size.height()}")
            
            if actual_size.width() != window_width or actual_size.height() != window_height:
                print(f"[TILE WARNING] 視窗 {i} 尺寸不匹配！目標: {window_width}x{window_height}, 實際: {actual_size.width()}x{actual_size.height()}")
                
                # 嘗試重新設置
                subwindow.resize(window_width, window_height)
                QApplication.processEvents()
                final_size = subwindow.size()
                print(f"[TILE DEBUG] 視窗 {i} 重設後尺寸: {final_size.width()}x{final_size.height()}")
        
        # 最終同步步驟：確保所有視窗尺寸一致
        print(f"[TILE DEBUG] ========== 開始最終尺寸同步 ==========")
        
        # 收集所有視窗的實際尺寸
        actual_sizes = []
        for i, subwindow in enumerate(subwindows):
            size = subwindow.size()
            actual_sizes.append((size.width(), size.height()))
            print(f"[TILE SYNC] 視窗 {i} 當前尺寸: {size.width()}x{size.height()}")
        
        # 找到最小的共同尺寸（確保所有視窗都能適應）
        if actual_sizes:
            min_width = min(size[0] for size in actual_sizes)
            min_height = min(size[1] for size in actual_sizes)
            print(f"[TILE SYNC] 統一目標尺寸: {min_width}x{min_height}")
            
            # 將所有視窗設置為相同尺寸
            for i, subwindow in enumerate(subwindows):
                current_pos = subwindow.pos()
                subwindow.setGeometry(current_pos.x(), current_pos.y(), min_width, min_height)
                QApplication.processEvents()
                
                final_size = subwindow.size()
                print(f"[TILE SYNC] 視窗 {i} 最終尺寸: {final_size.width()}x{final_size.height()}")
        
        print(f"[TILE DEBUG] ========== 尺寸同步完成 ==========")
        
        # 調試：檢查每個子視窗的邊距設定
        print(f"[TILE DEBUG] ========== 子視窗邊距檢查 ==========")
        for i, subwindow in enumerate(subwindows):
            widget = subwindow.widget()
            print(f"[TILE DEBUG] 子視窗 {i}: {subwindow.windowTitle()}")
            
            # 檢查 MDI 子視窗的邊距
            margins = subwindow.contentsMargins()
            print(f"[TILE DEBUG]   MDI邊距: left={margins.left()}, top={margins.top()}, right={margins.right()}, bottom={margins.bottom()}")
            
            # 檢查子視窗的frameGeometry vs geometry
            frame_geo = subwindow.frameGeometry()
            geo = subwindow.geometry()
            print(f"[TILE DEBUG]   frameGeometry: {frame_geo.width()}x{frame_geo.height()}")
            print(f"[TILE DEBUG]   geometry: {geo.width()}x{geo.height()}")
            print(f"[TILE DEBUG]   邊框差異: width={frame_geo.width()-geo.width()}, height={frame_geo.height()-geo.height()}")
            
            if widget:
                widget_size = widget.size()
                print(f"[TILE DEBUG]   內部widget尺寸: {widget_size.width()}x{widget_size.height()}")
                
                # 如果有調試方法，調用之
                if hasattr(widget, 'debug_margin_analysis'):
                    print(f"[TILE DEBUG]   調用 widget 邊距分析...")
                    widget.debug_margin_analysis()
        
        print(f"[TILE DEBUG] ========== 邊距檢查完成 ==========")
        
        # 刷新MDI區域
        mdi_area.update()
    def cascade_windows(self):
        """層疊視窗 - 將當前活動MDI區域中的所有子視窗以階梯式排列"""
        #print("[檢視] 層疊視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        
        # 首先檢查當前分頁是否本身就是MDI區域
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            # 否則在分頁的子元件中查找
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗需要層疊")
            return
            
        #print(f"[STATS] 開始層疊排列 {len(subwindows)} 個子視窗")
        
        # 計算層疊參數
        cascade_offset = 30  # 每個視窗的偏移量
        base_width = 500     # 基礎寬度
        base_height = 350    # 基礎高度
        start_x = 20         # 起始X位置
        start_y = 20         # 起始Y位置
        
        # 確保視窗不會超出MDI區域邊界
        max_windows = min(len(subwindows), 
                         (mdi_area.width() - base_width) // cascade_offset + 1,
                         (mdi_area.height() - base_height) // cascade_offset + 1)
        
        #print(f"📐 層疊配置: 偏移量 {cascade_offset}px, 基礎尺寸 {base_width}x{base_height}")
        
        # 層疊排列視窗
        for i, subwindow in enumerate(subwindows):
            # 計算當前視窗的位置（循環使用偏移量）
            offset_multiplier = i % max_windows
            x = start_x + offset_multiplier * cascade_offset
            y = start_y + offset_multiplier * cascade_offset
            
            # 設置視窗位置和尺寸
            subwindow.setGeometry(x, y, base_width, base_height)
            
            # 確保視窗可見和正常化
            subwindow.showNormal()
            subwindow.raise_()
            
            #print(f"[TOOL] 視窗 {i+1}: '{subwindow.windowTitle()}' 層疊到 ({x}, {y}) 尺寸 {base_width}x{base_height}")
        
        # 將最後一個視窗帶到前面
        if subwindows:
            subwindows[-1].activateWindow()
            subwindows[-1].raise_()
        
        # 刷新MDI區域
        mdi_area.update()
        #print(f"[OK] 成功層疊排列 {len(subwindows)} 個視窗")
        
    def minimize_all_windows(self):
        """最小化所有視窗"""
        #print("[檢視] 最小化所有視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗並最小化
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗")
            return
            
        count = 0
        for subwindow in subwindows:
            subwindow.showMinimized()
            count += 1
            #print(f"[TREND] 最小化視窗: '{subwindow.windowTitle()}'")
            
        #print(f"[OK] 成功最小化 {count} 個視窗")
        
    def maximize_all_windows(self):
        """最大化所有視窗"""
        #print("[檢視] 最大化所有視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗並最大化
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗")
            return
            
        count = 0
        for subwindow in subwindows:
            subwindow.showMaximized()
            count += 1
            #print(f"[CHART] 最大化視窗: '{subwindow.windowTitle()}'")
            
        #print(f"[OK] 成功最大化 {count} 個視窗")
        
    def restore_all_windows(self):
        """還原所有視窗到正常狀態"""
        #print("[檢視] 還原所有視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗並還原
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗")
            return
            
        count = 0
        for subwindow in subwindows:
            subwindow.showNormal()
            count += 1
            #print(f"[REFRESH] 還原視窗: '{subwindow.windowTitle()}'")
            
        #print(f"[OK] 成功還原 {count} 個視窗")
        
    def close_all_windows(self):
        """關閉所有視窗並清理相關註冊"""
        #print("[檢視] 關閉所有視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 使用改進的關閉方法
        self.close_all_mdi_windows(mdi_area)
    def toggle_fullscreen(self):
        """切換全螢幕模式"""
        #print("[檢視] 全螢幕切換")
        
        if self.isFullScreen():
            # 退出全螢幕
            self.showNormal()
            #print("🔲 退出全螢幕模式")
        else:
            # 進入全螢幕
            self.showFullScreen()
            #print("🔳 進入全螢幕模式")
            
        # 強制刷新界面
        self.update()
        
    def data_validation(self): 
        #print("[工具] 數據驗證")
        pass
        
    def system_settings(self): 
        try:
            gui_settings_manager.open_system_settings_dialog(self)
        except Exception as exc:
            print(f"[ERROR] 開啟系統設定時發生錯誤: {exc}")
    
    def set_interface_language(self, language):
        """設定介面語言"""
        try:
            # 設定語言
            set_gui_language(language)
            
            # 更新選單狀態
            if language == 'en':
                self.english_action.setChecked(True)
                self.chinese_action.setChecked(False)
                self.japanese_action.setChecked(False)
                message = "Interface language switched to English. Please restart the application for full effect."
            elif language == 'ja':
                self.english_action.setChecked(False)
                self.chinese_action.setChecked(False)
                self.japanese_action.setChecked(True)
                message = "インターフェース言語が日本語に切り替わりました。完全に有効にするには、アプリケーションを再起動してください。"
            else:
                self.english_action.setChecked(False)
                self.chinese_action.setChecked(True)
                self.japanese_action.setChecked(False)
                message = "介面語言已切換為中文。請重新啟動應用程式以獲得完整效果。"
            
            # 更新功能表文字
            self.refresh_menu_text()
            
            # 顯示提示訊息
            QMessageBox.information(self, "Language / 語言 / 言語", message)
            
            print(f"[LANGUAGE] 介面語言已切換為: {language}")
            
        except Exception as e:
            print(f"[ERROR] 語言切換失敗: {e}")
    
    def refresh_menu_text(self):
        """刷新功能表文字"""
        try:
            # 這裡可以添加即時更新功能表文字的邏輯
            # 目前需要重啟應用程式才能完全生效
            pass
        except Exception as e:
            print(f"[ERROR] 刷新功能表文字失敗: {e}")
        
    def toggle_lap_analysis_linkage(self, checked):
        """切換圈速分析連動功能總開關"""
        try:
            print(f"[LAP_LINKAGE] 圈速分析連動總開關: {'啟用' if checked else '停用'}")
            
            # 優先使用新的連動管理器
            linkage_manager.set_master_linkage_enabled(checked)
            
            # 🔧 修復：獲取連動管理器統計資訊並顯示詳細狀態
            stats = linkage_manager.get_module_stats()
            print(f"[LAP_LINKAGE] 連動管理器統計: {stats['total_modules']} 個模組已註冊")
            print(f"[LAP_LINKAGE] 模組類型分佈: {stats['module_types']}")
            
            # 更新全域信號管理器的連動狀態（向後相容）
            if hasattr(global_signals, 'set_lap_linkage_enabled'):
                global_signals.set_lap_linkage_enabled(checked)
            stats = linkage_manager.get_module_stats()
            print(f"[LAP_LINKAGE] 連動管理器統計: {stats['total_modules']} 個模組已註冊")
            
            # 兼容舊系統：通知現有的分析模組（在它們遷移到新系統之前）
            for analysis_module in self.lap_analysis_windows:
                try:
                    if hasattr(analysis_module, 'speed_chart_widget') and analysis_module.speed_chart_widget:
                        analysis_module.speed_chart_widget.set_master_linkage_enabled(checked)
                    elif hasattr(analysis_module, 'rpm_chart_widget') and analysis_module.rpm_chart_widget:
                        analysis_module.rpm_chart_widget.set_master_linkage_enabled(checked)
                    elif hasattr(analysis_module, 'throttle_chart_widget') and analysis_module.throttle_chart_widget:
                        analysis_module.throttle_chart_widget.set_master_linkage_enabled(checked)
                    
                    print(f"[LAP_LINKAGE] 已通知模組 {type(analysis_module).__name__} 更新連動狀態")
                except Exception as e:
                    print(f"[ERROR] [LAP_LINKAGE] 通知模組時發生錯誤: {e}")
            
            # 通知所有MDI子視窗的個別連動按鈕更新狀態
            current_mdi_area = self.get_current_mdi_area()
            if current_mdi_area:
                mdi_windows = current_mdi_area.subWindowList()
                for window in mdi_windows:
                    # 檢查是否為圈速分析相關的MDI子視窗
                    widget = window.widget()
                    if hasattr(widget, 'windowTitle') and any(analysis_type in widget.windowTitle() 
                        for analysis_type in ['速度分析', 'RPM分析', '油門分析']):
                        # 獲取MDI子視窗的標題欄
                        if hasattr(window, 'title_bar_widget') and hasattr(window.title_bar_widget, 'set_linkage_button_state'):
                            window.title_bar_widget.set_linkage_button_state(checked)
                            print(f"[LAP_LINKAGE] 已通知MDI子視窗 '{widget.windowTitle()}' 更新個別連動按鈕狀態")
            else:
                print(f"[LAP_LINKAGE] ⚠️ 未找到當前MDI區域，跳過MDI視窗連動按鈕更新")
            
        except Exception as e:
            print(f"[ERROR] [LAP_LINKAGE] 切換連動總開關失敗: {e}")
    
    def get_lap_linkage_enabled(self):
        """獲取圈速分析連動總開關狀態"""
        if hasattr(self, 'lap_linkage_action'):
            return self.lap_linkage_action.isChecked()
        return True  # 預設啟用
        print(f"[LINKAGE_MASTER] 🔗 圈速分析連動總開關: {'啟用' if checked else '停用'}")
        
        # 更新全域連動狀態
        if hasattr(global_signals, 'lap_analysis_linkage_master_enabled'):
            global_signals.lap_analysis_linkage_master_enabled = checked
        else:
            # 如果沒有這個屬性，添加它
            global_signals.lap_analysis_linkage_master_enabled = checked
        
        # 通知所有圈速分析模組總開關狀態變更
        updated_count = 0
        for analysis_module in self.lap_analysis_windows:
            try:
                # 檢查模組是否有連動控制方法
                if hasattr(analysis_module, 'set_master_linkage_enabled'):
                    analysis_module.set_master_linkage_enabled(checked)
                    updated_count += 1
                    print(f"[LINKAGE_MASTER] ✅ 已更新 {type(analysis_module).__name__} 總開關狀態")
                elif hasattr(analysis_module, 'speed_chart_widget'):
                    # 速度分析模組
                    if hasattr(analysis_module.speed_chart_widget, 'set_master_linkage_enabled'):
                        analysis_module.speed_chart_widget.set_master_linkage_enabled(checked)
                        updated_count += 1
                        print(f"[LINKAGE_MASTER] ✅ 已更新速度分析模組總開關狀態")
                elif hasattr(analysis_module, 'rpm_chart_widget'):
                    # RPM分析模組
                    if hasattr(analysis_module.rpm_chart_widget, 'set_master_linkage_enabled'):
                        analysis_module.rpm_chart_widget.set_master_linkage_enabled(checked)
                        updated_count += 1
                        print(f"[LINKAGE_MASTER] ✅ 已更新RPM分析模組總開關狀態")
                elif hasattr(analysis_module, 'throttle_chart_widget'):
                    # 油門分析模組
                    if hasattr(analysis_module.throttle_chart_widget, 'set_master_linkage_enabled'):
                        analysis_module.throttle_chart_widget.set_master_linkage_enabled(checked)
                        updated_count += 1
                        print(f"[LINKAGE_MASTER] ✅ 已更新油門分析模組總開關狀態")
                else:
                    print(f"[LINKAGE_MASTER] ⚠️ {type(analysis_module).__name__} 不支援連動控制")
                    
            except Exception as e:
                print(f"[LINKAGE_MASTER] ❌ 更新 {type(analysis_module).__name__} 總開關狀態失敗: {e}")
        
        print(f"[LINKAGE_MASTER] 📊 總開關狀態更新完成: {updated_count}/{len(self.lap_analysis_windows)} 個模組")
    
    def toggle_lap_analysis_x_linkage(self, checked):
        """切換圈速分析X軸連動功能（保留舊版相容性）"""
        print(f"[連動] 圈速分析X軸連動功能: {'啟用' if checked else '停用'}")
        
        # 更新所有活躍的圖表組件的連動狀態
        mdi_windows = self.mdi_area.subWindowList()
        for window in mdi_windows:
            widget = window.widget()
            
            # 檢查是否為速度分析MDI
            if hasattr(widget, 'speed_chart_widget') and widget.speed_chart_widget:
                # 直接訪問SpeedAnalysisChartWidget的chart_widget
                if hasattr(widget.speed_chart_widget, 'chart_widget'):
                    widget.speed_chart_widget.chart_widget.set_linkage_enabled(checked)
            
            # 檢查是否為RPM分析MDI
            elif hasattr(widget, 'rpm_chart_widget') and widget.rpm_chart_widget:
                # 直接訪問RPMAnalysisChartWidget的chart_widget
                if hasattr(widget.rpm_chart_widget, 'chart_widget'):
                    widget.rpm_chart_widget.chart_widget.set_linkage_enabled(checked)
        
        # 如果停用連動，發送清除信號
        if not checked:
            global_signals.lap_analysis_x_clear.emit()
    
    def integrate_linkage_manager(self):
        """整合新的連動管理器到主程式"""
        try:
            # 將現有的全域信號與新連動管理器連接
            if hasattr(global_signals, 'lap_analysis_master_linkage_changed'):
                global_signals.lap_analysis_master_linkage_changed.connect(
                    linkage_manager.set_master_linkage_enabled
                )
                print("[LINKAGE_INTEGRATION] ✅ 全域信號已連接到連動管理器")
            
            # 確保主開關狀態同步
            if hasattr(self, 'lap_linkage_action'):
                current_state = self.lap_linkage_action.isChecked()
                linkage_manager.set_master_linkage_enabled(current_state)
                print(f"[LINKAGE_INTEGRATION] ✅ 主開關狀態已同步: {'啟用' if current_state else '停用'}")
            
            # 設置連動管理器的信號回調
            linkage_manager.master_linkage_changed.connect(self.on_linkage_manager_state_changed)
            
            print("[LINKAGE_INTEGRATION] ✅ 連動管理器整合完成")
            
        except Exception as e:
            print(f"[ERROR] [LINKAGE_INTEGRATION] 連動管理器整合失敗: {e}")
    
    def on_linkage_manager_state_changed(self, enabled: bool):
        """處理連動管理器狀態變更"""
        try:
            # 更新主視窗的連動按鈕狀態
            if hasattr(self, 'lap_linkage_action'):
                self.lap_linkage_action.setChecked(enabled)
            
            # 獲取連動管理器統計
            stats = linkage_manager.get_module_stats()
            print(f"[LINKAGE_MANAGER] 狀態更新: {'啟用' if enabled else '停用'}")
            print(f"[LINKAGE_MANAGER] 已註冊模組: {stats['total_modules']} 個")
            print(f"[LINKAGE_MANAGER] 模組類型: {stats['module_types']}")
            
        except Exception as e:
            print(f"[ERROR] [LINKAGE_MANAGER] 狀態變更處理失敗: {e}")
        
    def apply_style_h(self):
        """應用風格H樣式 - 專業賽車分析工作站 (白色主題)"""
        style = """
        /* 主視窗 - 白色專業主題 */
        QMainWindow {
            background-color: #FFFFFF;
            color: #333333;
            font-family: "Arial", "Helvetica", sans-serif;
            font-size: 8pt;
        }
        
        /* 菜單欄 - 標準白色 */
        QMenuBar {
            background-color: #F8F8F8;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            padding: 1px;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 2px 6px;
            border-radius: 0px;
        }
        QMenuBar::item:selected {
            background-color: #E8E8E8;
        }
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            padding: 1px;
        }
        QMenu::item {
            padding: 2px 8px;
            border-radius: 0px;
        }
        QMenu::item:selected {
            background-color: #E8E8E8;
        }
        
        /* 右鍵選單 */
        #ContextMenu {
            background-color: #FFFFFF;
            border: 1px solid #AAAAAA;
            color: #333333;
            padding: 2px;
        }
        #ContextMenu::item {
            padding: 3px 12px;
            border-radius: 0px;
        }
        #ContextMenu::item:selected {
            background-color: #E8E8E8;
        }
        
        /* 左側面板白色主題 */
        #LeftPanel {
            background-color: #F8F8F8;
            color: #333333;
        }
        #FunctionTreeWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        
        /* 通用工具欄 - 白色主題 */
        QToolBar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            spacing: 1px;
            padding: 1px;
        }
        QToolBar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px;
            margin: 0px;
            color: #333333;
            font-size: 9pt;
            border-radius: 0px;
        }
        QToolBar QToolButton:hover {
            background-color: #E8E8E8;
            border: 1px solid #AAAAAA;
        }
        QToolBar QToolButton:pressed {
            background-color: #D8D8D8;
        }
        
        /* 專業工具欄 */
        #ProfessionalToolbar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            spacing: 1px;
            padding: 1px;
        }
        #ProfessionalToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px;
            margin: 0px;
            color: #333333;
            font-size: 9pt;
            border-radius: 0px;
        }
        #ProfessionalToolbar QToolButton:hover {
            background-color: #E8E8E8;
            border: 1px solid #AAAAAA;
        }
        #ProfessionalToolbar QToolButton:pressed {
            background-color: #D8D8D8;
        }
        #ProfessionalToolbar QLabel {
            color: #666666;
            font-size: 7pt;
            padding: 0px 2px;
        }
        
        /* 通用下拉選單 - 白色主題 */
        QComboBox {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            padding: 2px 4px;
            border-radius: 0px;
        }
        QComboBox::drop-down {
            border: none;
            background-color: #E8E8E8;
            width: 15px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-top: 3px solid #333333;
            width: 0px;
            height: 0px;
        }
        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            selection-background-color: #E8E8E8;
            color: #333333;
        }
        QComboBox:hover {
            border-color: #888888;
        }
        
        /* 通用勾選框 - 白色主題 */
        QCheckBox {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #AAAAAA;
            background-color: #FFFFFF;
        }
        QCheckBox::indicator:checked {
            background-color: #0078D4;
            border-color: #0078D4;
        }
        QCheckBox::indicator:hover {
            border-color: #888888;
        }
        
        /* 通用按鈕 - 白色主題 */
        QPushButton {
            background-color: #F8F8F8;
            border: 1px solid #CCCCCC;
            border-radius: 3px;
            padding: 5px 10px;
            font-size: 8pt;
            color: #333333;
        }
        QPushButton:hover {
            background-color: #E8E8E8;
            border-color: #999999;
        }
        QPushButton:pressed {
            background-color: #D8D8D8;
        }
        QPushButton:disabled {
            background-color: #F0F0F0;
            border-color: #E0E0E0;
            color: #999999;
        }
        
        /* 參數選擇框 */
        #ParameterCombo {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            font-size: 7pt;
            padding: 1px 2px;
            border-radius: 0px;
        }
        #ParameterCombo::drop-down {
            border: none;
            background-color: #E8E8E8;
            width: 12px;
        }
        #ParameterCombo::down-arrow {
            image: none;
            border-left: 2px solid transparent;
            border-right: 2px solid transparent;
            border-top: 2px solid #333333;
            width: 0px;
            height: 0px;
        }
        #ParameterCombo QAbstractItemView {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            selection-background-color: #E8E8E8;
            color: #333333;
        }
        
        /* 功能樹標題 */
        #FunctionTreeTitle {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-weight: bold;
        }
        
        /* 通用樹狀控件 - 白色主題 */
        QTreeWidget {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            outline: none;
            font-size: 8pt;
            alternate-background-color: #F8F8F8;
        }
        QTreeWidget::item {
            height: 14px;
            border: none;
            padding: 1px 1px;
        }
        QTreeWidget::item:hover {
            background-color: #F0F0F0;
        }
        QTreeWidget::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        
        /* 專業功能樹 */
        #ProfessionalFunctionTree {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            outline: none;
            font-size: 8pt;
            alternate-background-color: #F8F8F8;
        }
        #ProfessionalFunctionTree::item {
            height: 14px;
            border: none;
            padding: 1px 1px;
        }
        #ProfessionalFunctionTree::item:hover {
            background-color: #F0F0F0;
        }
        #ProfessionalFunctionTree::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        
        /* MDI工作區 - 白色主題 - 增強版 */
        #ProfessionalMDIArea, #OverviewMDIArea {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
            border: 1px solid #CCCCCC;
        }
        QMdiArea {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea QScrollArea {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea QScrollArea QWidget {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea > QWidget {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea * {
            background-color: #F5F5F5 !important;
        }
        
        /* 通用分頁控件 - 白色主題 */
        QTabWidget {
            background-color: #FFFFFF;
            border: none;
        }
        QTabWidget::pane {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        QTabWidget::tab-bar {
            alignment: left;
            height: 0px !important;  /* 強制隱藏標籤欄 */
            max-height: 0px !important;
            min-height: 0px !important;
        }
        QTabWidget QTabBar {
            height: 0px !important;  /* 完全隱藏標籤欄 */
            max-height: 0px !important;
            min-height: 0px !important;
            background: transparent !important;
            border: none !important;
        }
        QTabWidget QTabBar::tab {
            height: 0px !important;   /* 強制高度為0 */
            max-height: 0px !important;
            min-height: 0px !important;
            padding: 0px !important;  /* 移除內距 */
            margin: 0px !important;   /* 移除邊距 */
            border: none !important;  /* 移除邊框 */
            font-size: 0pt !important; /* 字體大小設為0 */
            background: transparent !important;
            color: transparent !important;
        }
        QTabWidget QTabBar::tab:selected {
            background-color: transparent;
            color: transparent;
            border: none;
            height: 0px;
            max-height: 0px;
            padding: 0px;
            margin: 0px;
        }
        QTabWidget QTabBar::tab:hover {
            background-color: transparent;
            height: 0px;
            max-height: 0px;
            padding: 0px;
            margin: 0px;
        }
        
        /* 專業分頁控件 - 白色主題 (完全隱藏標籤欄) */
        #ProfessionalTabWidget {
            background-color: #FFFFFF;
            border: none;
        }
        #ProfessionalTabWidget::pane {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            border-top: none !important;  /* 移除上方邊框 */
        }
        #ProfessionalTabWidget::tab-bar {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar::tab {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            padding: 0px !important;
            margin: 0px !important;
            border: none !important;
            background: transparent !important;
            color: transparent !important;
            font-size: 0pt !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar::tab:selected {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            color: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar::tab:hover {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            color: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
        }
        
        /* 分頁控制區域 */
        #TabControlArea {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
        }
        
        /* 分頁按鈕容器 - 完全隱藏 */
        #TabButtonsContainer {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
            padding: 0px !important;
            margin: 0px !important;
        }
        
        /* 新增分頁按鈕 */
        #AddTabButton {
            background-color: #FFFFFF;
            color: #006600;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 12pt;
            font-weight: bold;
        }
        #AddTabButton:hover {
            background-color: #F0F0F0;
            border-color: #006600;
        }
        #AddTabButton:pressed {
            background-color: #E8E8E8;
        }
        
        /* 關閉分頁按鈕 */
        #CloseTabButton {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 12pt;
            font-weight: bold;
        }
        #CloseTabButton:hover {
            background-color: #F0F0F0;
            border-color: #333333;
        }
        #CloseTabButton:pressed {
            background-color: #E8E8E8;
        }
        
        /* 分頁數量標籤 */
        #TabCountLabel {
            color: #333333;
            font-size: 8pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 4px 8px;
        }
        
        /* 分析控制面板 */
        #AnalysisControlArea {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            border-top: 1px solid #CCCCCC;
        }
        
        /* 連動控制勾選框 */
        #SyncWindowsCheckbox {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        #SyncWindowsCheckbox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #AAAAAA;
            background-color: #FFFFFF;
        }
        #SyncWindowsCheckbox::indicator:checked {
            background-color: #0078D4;
            border-color: #0078D4;
        }
        #SyncWindowsCheckbox::indicator:hover {
            border-color: #888888;
        }
        
        /* 遙測同步勾選框 */
        #SyncTelemetryCheckbox {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        #SyncTelemetryCheckbox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #AAAAAA;
            background-color: #FFFFFF;
        }
        #SyncTelemetryCheckbox::indicator:checked {
            background-color: #00AA00;
            border-color: #00AA00;
        }
        #SyncTelemetryCheckbox::indicator:hover {
            border-color: #888888;
        }
        
        /* 控制標籤 */
        #ControlLabel {
            color: #333333;
            font-size: 8pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
        }
        
        /* 分析下拉選單 */
        #AnalysisComboBox {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #AAAAAA;
            border-radius: 0px;
            padding: 3px 8px;
            font-size: 8pt;
            min-width: 80px;
        }
        #AnalysisComboBox::drop-down {
            background-color: #E8E8E8;
            border: none;
            width: 20px;
        }
        #AnalysisComboBox::down-arrow {
            border: none;
            width: 0px;
            height: 0px;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #333333;
        }
        #AnalysisComboBox QAbstractItemView {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #AAAAAA;
            selection-background-color: #0078D4;
            font-size: 8pt;
        }
        #AnalysisComboBox:hover {
            border-color: #888888;
        }
        #AnalysisComboBox:focus {
            border-color: #0078D4;
        }
        
        /* 重新分析按鈕 */
        #ReanalyzeButton {
            background-color: #FF6B35;
            color: #FFFFFF;
            border: 1px solid #FF6B35;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #ReanalyzeButton:hover {
            background-color: #E55A2B;
            border-color: #E55A2B;
        }
        #ReanalyzeButton:pressed {
            background-color: #CC4A21;
        }
        
        /* 主分頁容器 */
        #MainTabContainer {
            background-color: #FFFFFF;
            border: none;
        }
        
        /* 數據總覽分頁 */
        #DataOverviewTab {
            background-color: #FFFFFF;
        }
        #TabTitleLabel {
            color: #333333;
            font-size: 10pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 5px;
        }
        #OverviewMDIArea {
            background-color: #F5F5F5;
            border: 1px solid #CCCCCC;
        }
        #StatsContent {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
            padding: 10px;
        }
        
        /* 設定對話框 */
        #SettingsDialog {
            background-color: #FFFFFF;
            color: #333333;
            border: 2px solid #CCCCCC;
        }
        #DialogTitle {
            color: #333333;
            font-size: 12pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 5px;
        }
        #SettingsGroup {
            color: #333333;
            font-size: 9pt;
            font-weight: bold;
            border: 1px solid #CCCCCC;
            border-radius: 3px;
            margin-top: 5px;
            padding-top: 5px;
        }
        #SettingsGroup::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #666666;
        }
        #DialogButtonBox {
            background-color: transparent;
        }
        #DialogButtonBox QPushButton {
            background-color: #0078D4;
            color: #FFFFFF;
            border: 1px solid #0078D4;
            border-radius: 3px;
            padding: 5px 15px;
            font-size: 9pt;
            min-width: 60px;
        }
        #DialogButtonBox QPushButton:hover {
            background-color: #106EBE;
        }
        #DialogButtonBox QPushButton:pressed {
            background-color: #005A9E;
        }
        
        /* 專業MDI子視窗 - 使用自定義paintEvent繪製邊框 */
        #ProfessionalSubWindow {
            background-color: #FFFFFF;
            border: none;  /* 邊框由paintEvent繪製 */
            border-radius: 0px;
        }
        QMdiSubWindow {
            background-color: #FFFFFF;
            border: 2px solid #0078D4;  /* Windows 10/11標準藍色邊框，更明顯 */
            margin: 0px;
            padding: 0px;
        }
        QMdiSubWindow:active {
            border: 2px solid #106EBE;  /* 活動視窗使用更深的藍色 */
        }
        QMdiSubWindow QWidget {
            margin: 0px;
            padding: 0px;
        }
        QMdiSubWindow::title {
            background: #0078D4;  /* Windows 標準藍色標題欄 */
            color: #FFFFFF;  /* 白色文字 */
            height: 22px;
            padding: 2px 5px;
            margin: 0px;
            border: none;
            font-size: 11px;
            font-weight: normal;
            text-align: left;
        }
        
        QMdiSubWindow QWidget {
            border: none;
        }
        
        /* 子視窗包裝器 */
        #SubWindowWrapper {
            background-color: transparent;  /* 改為透明，讓底層調整區域可見 */
            color: #333333;
            border: none;
        }
        
        /* 視窗控制面板 */
        #WindowControlPanel {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            border-top: 1px solid #CCCCCC;
        }
        
        /* 自定義標題欄 */
        #CustomTitleBar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            border-top: none;
            border-left: none;
            border-right: none;
            color: #000000;
        }
        
        /* 視窗控制按鈕 */
        #WindowControlButton {
            background-color: #F0F0F0;  /* Windows 系統按鈕背景 */
            color: #000000;  /* 黑色文字 */
            border: 1px solid #D0D0D0;  /* 淺灰色邊框 */
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #WindowControlButton:hover {
            background-color: #E0E0E0;  /* 滑鼠懸停時稍深 */
        }
        #WindowControlButton:pressed {
            background-color: #D0D0D0;  /* 按下時更深 */
        }
        
        /* 恢復按鈕 */
        #RestoreButton {
            background-color: #2E8B57;
            color: #FFFFFF;
            border: 1px solid #3CB371;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #RestoreButton:hover {
            background-color: #3CB371;
        }
        #RestoreButton:pressed {
            background-color: #228B22;
        }
        
        /* X軸連動按鈕 - 紅綠狀態指示 */
        #SyncButton {
            background-color: #FF4444;  /* 預設紅色 - 未連動 */
            color: #FFFFFF;
            border: 1px solid #CC0000;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #SyncButton:hover {
            background-color: #FF6666;  /* 紅色懸停 */
        }
        #SyncButton:pressed {
            background-color: #CC0000;  /* 紅色按下 */
        }
        #SyncButton:checked {
            background-color: #00CC00;  /* 綠色 - 已連動 */
            border: 1px solid #009900;
        }
        #SyncButton:checked:hover {
            background-color: #00FF00;  /* 綠色懸停 */
        }
        
        /* 個別連動按鈕 - 藍色主題 */
        #LinkageButton {
            background-color: #2196F3;  /* 藍色 - 連動啟用 */
            color: white;
            border: 1px solid #1976D2;
            border-radius: 3px;
            font-size: 8px;
            font-weight: bold;
            text-align: center;
        }
        #LinkageButton:hover {
            background-color: #42A5F5;  /* 藍色懸停 */
        }
        #LinkageButton:pressed {
            background-color: #1565C0;  /* 藍色按下 */
        }
        #LinkageButton:!checked {
            background-color: #9E9E9E;  /* 灰色 - 連動停用 */
            border: 1px solid #757575;
        }
        #LinkageButton:!checked:hover {
            background-color: #BDBDBD;  /* 灰色懸停 */
        }
        
        /* 設定按鈕 */
        #SettingsButton {
            background-color: #F8F8F8;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #SettingsButton:hover {
            background-color: #E8E8E8;
        }
        #SettingsButton:pressed {
            background-color: #D8D8D8;
        }
        
        /* 彈出按鈕 */
        #PopoutButton {
            background-color: #F8F8F8;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #PopoutButton:hover {
            background-color: #E8E8E8;
        }
        #PopoutButton:pressed {
            background-color: #D8D8D8;
        }
        
        /* 子視窗標題 */
        #SubWindowTitle {
            color: #333333;
            font-size: 8pt;
            font-weight: bold;
        }
        
        /* 獨立視窗 */
        #StandaloneWindow {
            background-color: #FFFFFF;
            color: #333333;
        }
        #StandaloneToolbar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
        }
        #StandaloneToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px 6px;
            color: #333333;
            border-radius: 0px;
        }
        #StandaloneToolbar QToolButton:hover {
            background-color: #E8E8E8;
            border: 1px solid #CCCCCC;
        }
        
        /* 遙測圖表 */
        #TelemetryChart {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        
        /* 賽道地圖 */
        #TrackMap {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        
        /* 專業數據表格 */
        #ProfessionalDataTable {
            background-color: #FFFFFF;
            alternate-background-color: #F8F8F8;
            color: #333333;
            gridline-color: #CCCCCC;
            font-size: 8pt;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        #ProfessionalDataTable::item {
            padding: 1px;
            border: none;
        }
        #ProfessionalDataTable::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        #ProfessionalDataTable QHeaderView::section {
            background-color: #F0F0F0;
            color: #333333;
            padding: 1px;
            border: 1px solid #CCCCCC;
            font-weight: bold;
            font-size: 8pt;
            border-radius: 0px;
        }
        
        /* 狀態列 */
        QStatusBar {
            background-color: #F0F0F0;
            border-top: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
        }
        #StatusReady {
            color: #00AA00;
            font-weight: bold;
        }
        #VersionInfo {
            color: #0078D4;
            font-weight: bold;
        }
        
        /* 標籤 */
        QLabel {
            color: #333333;
            font-size: 8pt;
        }
        
        /* 滾動條 */
        QScrollBar:vertical {
            background-color: #F0F0F0;
            width: 6px;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #AAAAAA;
            border-radius: 0px;
            min-height: 10px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #888888;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* 分割器 */
        QSplitter::handle {
            background-color: #CCCCCC;
        }
        QSplitter::handle:horizontal {
            width: 2px;
        }
        QSplitter::handle:vertical {
            height: 2px;
        }
        
        /* 強制所有容器為白底 */
        QWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        QFrame {
            background-color: #FFFFFF;
            color: #333333;
        }
        QSplitter {
            background-color: #F5F5F5;
        }
        QSplitter QWidget {
            background-color: #FFFFFF;
        }
        
        /* 強制所有MDI相關元素為白底 */
        QMdiArea QWidget {
            background-color: #FFFFFF;
        }
        QMdiArea QScrollArea QWidget {
            background-color: #FFFFFF;
        }
        QMdiArea > QWidget {
            background-color: #FFFFFF;
        }
        
        /* 左側面板所有子元素強制白底 */
        QTreeWidget QWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        QTextEdit QWidget {
            background-color: #FFFFFF;
            color: #006600;
        }
        """
        
        #print("[DESIGN] DEBUG: Setting main window QSS styles...")
        #print(f"📄 QSS contains QMdiSubWindow border: {'QMdiSubWindow' in style and 'border:' in style}")
        #print(f"📄 QSS contains CustomTitleBar: {'CustomTitleBar' in style}")
        #print(f"📄 QSS total length: {len(style)} characters")
        # 臨時禁用有問題的樣式表，改用簡化版本
        simple_style = """
        QMainWindow {
            background-color: #FFFFFF;
            color: #333333;
        }
        QWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        """
        self.setStyleSheet(simple_style)
        #print("[OK] 簡化版QSS styles applied successfully")
        
    def show_error_message(self, title, message):
        """顯示錯誤訊息對話框"""
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def closeEvent(self, event):
        """視窗關閉事件處理"""
        try:
            if hasattr(self, 'api_health_timer') and self.api_health_timer:
                self.api_health_timer.stop()
                self.api_health_timer.deleteLater()
                self.api_health_timer = None
            if hasattr(self, '_api_health_worker') and self._api_health_worker:
                try:
                    self._api_health_worker.result_ready.disconnect(self.on_api_health_result)
                except Exception:
                    pass
                try:
                    self._api_health_worker.finished.disconnect(self.on_api_health_finished)
                except Exception:
                    pass
                self._api_health_worker = None
            self._api_health_worker_active = False

            if hasattr(self, 'api_runtime_timer') and self.api_runtime_timer:
                self.api_runtime_timer.stop()
                self.api_runtime_timer.deleteLater()
                self.api_runtime_timer = None
            if hasattr(self, '_api_runtime_worker') and self._api_runtime_worker:
                try:
                    self._api_runtime_worker.result_ready.disconnect(self.on_api_runtime_result)
                except Exception:
                    pass
                try:
                    self._api_runtime_worker.finished.disconnect(self.on_api_runtime_finished)
                except Exception:
                    pass
                if self._api_runtime_worker.isRunning():
                    self._api_runtime_worker.requestInterruption()
                    self._api_runtime_worker.wait(300)
                self._api_runtime_worker.deleteLater()
                self._api_runtime_worker = None
            self._api_runtime_worker_active = False

            print("[MAIN] 🛑 接收到關閉請求，開始清理資源...")
            
            # 顯示關閉確認對話框（可選）
            from core.gui_i18n import tr
            reply = QMessageBox.question(
                self, 
                tr('confirm_exit', 'Confirm Exit'), 
                tr('confirm_exit_message', 'Are you sure you want to exit F1T Professional Racing Analysis Workstation?\n\nAll running analyses will be stopped.'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            # 停止所有正在執行的 CLI 分析
            print("[MAIN] 🔄 停止所有分析進程...")
            self.stop_all_analyses()
            
            # 關閉所有子視窗
            print("[MAIN] 🪟 關閉所有子視窗...")
            self.close_all_subwindows()
            
            # 清理分析模組管理器
            if hasattr(self, 'analysis_module_manager'):
                try:
                    self.analysis_module_manager.cleanup_all()
                    print("[MAIN] 🧹 分析模組管理器已清理")
                except Exception as e:
                    print(f"[MAIN] ⚠️ 分析模組管理器清理警告: {e}")
            
            # 清理全域 CLI 分析管理器
            try:
                cli_analysis_manager.cleanup_all()
                print("[MAIN] 🔧 CLI 分析管理器已清理")
            except Exception as e:
                print(f"[MAIN] ⚠️ CLI 分析管理器清理警告: {e}")
            
            # 強制垃圾回收
            try:
                import gc
                gc.collect()
                print("[MAIN] 🗑️ 垃圾回收完成")
            except Exception as e:
                print(f"[MAIN] ⚠️ 垃圾回收警告: {e}")
            
            print("[MAIN] ✅ 資源清理完成，程序即將退出")
            
            # 接受關閉事件
            event.accept()
            
            # 確保應用程序完全退出
            from PyQt5.QtWidgets import QApplication
            import sys
            
            app = QApplication.instance()
            if app:
                app.quit()
                # 給一點時間讓 Qt 完成清理
                QTimer.singleShot(100, lambda: sys.exit(0))
            
        except Exception as e:
            print(f"[MAIN] ❌ 關閉事件處理錯誤: {e}")
            import traceback
            traceback.print_exc()
            # 即使出錯也要強制關閉
            event.accept()
            try:
                import sys
                sys.exit(1)
            except:
                pass
    
    def stop_all_analyses(self):
        """停止所有正在執行的分析"""
        try:
            # 清理全域 CLI 分析管理器
            cli_analysis_manager.cleanup_all()
            
            # 停止所有子視窗中的 CLI 分析
            for mdi_area in self.mdi_areas:
                subwindows = mdi_area.subWindowList()
                
                for sub_window in subwindows:
                    widget = sub_window.widget()
                    if hasattr(widget, 'stop_cli_analysis'):
                        widget.stop_cli_analysis()
            
            # 清理追蹤列表
            if hasattr(self, 'active_subwindows'):
                self.active_subwindows.clear()
            
            # 停止當前視窗的分析（如果有的話）
            if hasattr(self, 'stop_cli_analysis'):
                self.stop_cli_analysis()
                
        except Exception as e:
            pass
    
    def close_all_subwindows(self):
        """關閉所有子視窗"""
        try:
            # 關閉所有MDI子視窗
            for mdi_area in self.mdi_areas:
                subwindows = mdi_area.subWindowList()
                
                for sub_window in subwindows:
                    try:
                        sub_window.close()
                    except Exception as e:
                        print(f"[MAIN] ⚠️ 關閉子視窗時發生錯誤: {e}")
                        
                # 清除MDI區域
                mdi_area.closeAllSubWindows()
            
            # 清理追蹤列表
            if hasattr(self, 'active_subwindows'):
                self.active_subwindows.clear()
                
        except Exception as e:
            print(f"[MAIN] ⚠️ 關閉子視窗過程中發生錯誤: {e}")
    
    def on_subwindow_closed(self, subwindow):
        """處理子視窗關閉事件 - 從追蹤列表中移除"""
        try:
            window_title = subwindow.windowTitle() if subwindow else "未知視窗"
            
            # 從活動子視窗列表中移除
            if hasattr(self, 'active_subwindows') and subwindow in self.active_subwindows:
                self.active_subwindows.remove(subwindow)
            
            # 檢查是否還有分析模組在運行
            self._check_and_update_toolbar_status()
            
        except Exception as e:
            pass
    
    def _check_and_update_toolbar_status(self):
        """檢查當前活動的分析模組並更新工具欄狀態"""
        try:
            # 查找當前分頁中的MDI區域
            current_tab = self.tab_widget.currentWidget()
            if not current_tab:
                self.clear_toolbar_status()
                return
            
            # 查找MDI區域
            mdi_area = None
            if isinstance(current_tab, CustomMdiArea):
                mdi_area = current_tab
            else:
                for child in current_tab.findChildren(CustomMdiArea):
                    mdi_area = child
                    break
            
            if not mdi_area:
                self.clear_toolbar_status()
                return
            
            # 檢查MDI區域中是否有子視窗
            subwindows = mdi_area.subWindowList()
            if not subwindows:
                # 沒有子視窗，清除工具欄狀態
                self.clear_toolbar_status()
                print(f"[TOOLBAR_STATUS] 沒有活動的分析模組，已清除工具欄狀態")
            else:
                print(f"[TOOLBAR_STATUS] 當前有 {len(subwindows)} 個活動的分析模組")
                
        except Exception as e:
            print(f"[ERROR] 檢查工具欄狀態失敗: {e}")
            self.clear_toolbar_status()
        
    def remove_welcome_tab(self):
        """移除歡迎頁面 - 當使用者開始分析時"""
        try:
            for i in range(self.tab_widget.tabCount()):
                tab_text = self.tab_widget.tabText(i)
                if "歡迎" in tab_text or "Welcome" in tab_text:
                    self.tab_widget.removeTab(i)
                    #print(f"[OK] 已移除歡迎頁面: {tab_text}")
                    break
        except Exception as e:
            #print(f"[WARNING] 移除歡迎頁面時發生錯誤: {e}")
            pass


def main():
    """主函數"""
    print("[MAIN] 🚀 啟動 F1T 專業賽車分析工作站...")
    
    app = QApplication(sys.argv)
    
    app.setApplicationName("F1T Professional Racing Analysis Workstation")
    app.setOrganizationName("F1T Professional Racing Analysis Team")
    
    # 設置應用程式字體
    font = QFont("Arial", 8)
    app.setFont(font)
    
    # 設置應用程序在最後一個視窗關閉時退出
    app.setQuitOnLastWindowClosed(True)
    
    # 創建主視窗
    window = StyleHMainWindow()
    window.show()
    
    # 執行事件循環
    result = app.exec_()
    
    print("[MAIN] 🛑 F1T 程序正常退出")
    sys.exit(result)

if __name__ == "__main__":
    main()
