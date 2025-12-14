"""
F1T NSSM Service Monitor - Main GUI Application
獨立的 NSSM 服務監控工具

功能:
- 即時服務狀態監控
- CPU/記憶體使用率顯示
- 服務快速啟動/停止/重啟
- 日誌即時查看與搜尋
- 歷史狀態圖表
- 自動刷新機制
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QPushButton, QTextEdit, QLineEdit, QComboBox,
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QSplitter, QStatusBar, QMessageBox, QHeaderView
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis

from service_monitor import NSSMServiceMonitor


class ServiceMonitorSingleton:
    """單例模式的服務監控器，避免重複創建實例"""
    _instance = None
    _monitor = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._monitor = NSSMServiceMonitor(debug_enabled=False)
        return cls._instance
    
    def get_monitor(self):
        return self._monitor


class LogLoadWorker(QThread):
    """日誌載入背景執行緒"""
    
    # 信號定義
    loading_started = pyqtSignal(str)  # (service_name)
    logs_loaded = pyqtSignal(list, int, float)  # (logs, line_count, file_size_kb)
    loading_failed = pyqtSignal(str)  # (error_message)
    
    def __init__(self, log_file: Path, tail: int = 500, parent=None):
        super().__init__(parent)
        self.log_file = log_file
        self.tail = tail
    
    def run(self):
        """背景執行緒主函數 - 載入日誌（優化版：反向讀取避免阻塞）"""
        try:
            if not os.path.exists(self.log_file):
                self.loading_failed.emit(f"日誌檔案不存在: {self.log_file}")
                return
            
            # 獲取檔案大小
            file_size_kb = os.path.getsize(self.log_file) / 1024
            print(f"[LOG_WORKER] 日誌檔案大小: {file_size_kb:.2f} KB")
            
            # 智能編碼檢測 - 只檢測前 1KB
            detected_encoding = self._detect_encoding_fast()
            if detected_encoding:
                encodings = [detected_encoding, 'utf-8', 'cp950', 'gbk']
            else:
                encodings = ['utf-8', 'cp950', 'gbk', 'big5', 'latin1']
            
            logs = None
            for encoding in encodings:
                try:
                    print(f"[LOG_WORKER] 嘗試使用編碼: {encoding}")
                    
                    # ✅ 優化：使用反向讀取，只讀取最後 N 行
                    if file_size_kb > 1024:  # 大於 1MB 使用反向讀取
                        logs = self._read_tail_efficient(encoding)
                    else:
                        logs = self._read_all_lines(encoding)
                    
                    if logs is not None:
                        print(f"[LOG_WORKER] ✓ 成功使用 {encoding} 讀取 {len(logs)} 行")
                        break
                        
                except Exception as e:
                    print(f"[LOG_WORKER] ✗ 使用 {encoding} 讀取失敗: {e}")
                    continue
            
            if logs:
                self.logs_loaded.emit(logs, len(logs), file_size_kb)
            else:
                self.loading_failed.emit("無法讀取日誌檔案（所有編碼嘗試均失敗）")
                
        except Exception as e:
            print(f"[LOG_WORKER] 載入日誌時發生異常: {e}")
            import traceback
            print(f"[LOG_WORKER] 詳細錯誤:\n{traceback.format_exc()}")
            self.loading_failed.emit(f"載入日誌時發生錯誤: {str(e)}")
    
    def _detect_encoding_fast(self) -> Optional[str]:
        """快速檢測檔案編碼（只讀前 1KB）"""
        try:
            with open(self.log_file, 'rb') as f:
                sample = f.read(1024)
            
            # 簡單檢測 UTF-8 BOM
            if sample.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            
            # 嘗試解碼為 UTF-8
            try:
                sample.decode('utf-8')
                return 'utf-8'
            except UnicodeDecodeError:
                pass
            
            # Windows 繁體中文
            try:
                sample.decode('cp950')
                return 'cp950'
            except UnicodeDecodeError:
                pass
                
        except Exception as e:
            print(f"[LOG_WORKER] 編碼檢測失敗: {e}")
        
        return None
    
    def _read_tail_efficient(self, encoding: str) -> Optional[list]:
        """高效讀取檔案尾部 N 行（大檔案優化）"""
        try:
            buffer_size = 8192  # 8KB 緩衝區
            lines_found = []
            
            with open(self.log_file, 'rb') as f:
                # 移動到檔案末尾
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                
                if file_size == 0:
                    return []
                
                # 反向讀取
                remaining_bytes = file_size
                buffer = b''
                
                while remaining_bytes > 0 and len(lines_found) < self.tail:
                    # 計算本次讀取位置
                    read_size = min(buffer_size, remaining_bytes)
                    remaining_bytes -= read_size
                    
                    # 移動到讀取位置
                    f.seek(remaining_bytes)
                    chunk = f.read(read_size)
                    
                    # 合併緩衝區
                    buffer = chunk + buffer
                    
                    # 解碼並分割行
                    try:
                        text = buffer.decode(encoding, errors='replace')
                        lines = text.split('\n')
                        
                        # 保留不完整的第一行作為下次的緩衝
                        if remaining_bytes > 0:
                            buffer = lines[0].encode(encoding, errors='replace')
                            lines = lines[1:]
                        else:
                            buffer = b''
                        
                        # 反向添加行
                        for line in reversed(lines):
                            if len(lines_found) >= self.tail:
                                break
                            if line.strip():  # 跳過空行
                                lines_found.insert(0, line.rstrip())
                    
                    except Exception as e:
                        print(f"[LOG_WORKER] 解碼區塊失敗: {e}")
                        raise
            
            return lines_found
            
        except Exception as e:
            print(f"[LOG_WORKER] 反向讀取失敗: {e}")
            return None
    
    def _read_all_lines(self, encoding: str) -> Optional[list]:
        """讀取所有行（小檔案）"""
        try:
            with open(self.log_file, 'r', encoding=encoding, errors='replace') as f:
                lines = f.readlines()
                # 只取最後 N 行
                return [line.rstrip() for line in lines[-self.tail:]]
        except Exception as e:
            print(f"[LOG_WORKER] 讀取所有行失敗: {e}")
            return None


class BatchServiceWorker(QThread):
    """批量服務操作背景執行緒"""
    
    # 信號定義
    progress_updated = pyqtSignal(str, str)  # (operation, service_name)
    operation_completed = pyqtSignal(str, int, int)  # (operation, success_count, total_count)
    error_occurred = pyqtSignal(str, str)  # (operation, error_message)
    
    def __init__(self, operation: str, service_names: list, parent=None):
        super().__init__(parent)
        self.operation = operation  # "start_all", "stop_all", "restart_all"
        self.service_names = service_names
        self.monitor = ServiceMonitorSingleton().get_monitor()
        self.should_stop = False
    
    def stop_operation(self):
        """請求停止操作"""
        self.should_stop = True
    
    def run(self):
        """背景執行緒主函數 - 增強異常處理版本"""
        success_count = 0
        total_count = len(self.service_names)
        
        try:
            if self.operation == "start_all":
                for service_name in self.service_names:
                    if self.should_stop:
                        break
                    
                    try:
                        self.progress_updated.emit("啟動", service_name)
                        if self.monitor.start_service(service_name):
                            success_count += 1
                    except Exception as e:
                        print(f"[ERROR] 啟動服務 {service_name} 時發生異常: {e}")
                        self.error_occurred.emit("start", f"啟動 {service_name} 失敗: {str(e)}")
                    
            elif self.operation == "stop_all":
                for service_name in self.service_names:
                    if self.should_stop:
                        break
                    
                    try:
                        self.progress_updated.emit("停止", service_name)
                        if self.monitor.stop_service(service_name):
                            success_count += 1
                    except Exception as e:
                        print(f"[ERROR] 停止服務 {service_name} 時發生異常: {e}")
                        self.error_occurred.emit("stop", f"停止 {service_name} 失敗: {str(e)}")
                        
            elif self.operation == "restart_all":
                for service_name in self.service_names:
                    if self.should_stop:
                        break
                    
                    try:
                        self.progress_updated.emit("重啟", service_name)
                        # 重啟操作可能需要更長時間，增加超時保護
                        if self.monitor.restart_service(service_name):
                            success_count += 1
                        # 重啟後稍微等待一下讓服務穩定
                        self.msleep(500)  # 等待 0.5 秒
                    except Exception as e:
                        print(f"[ERROR] 重啟服務 {service_name} 時發生異常: {e}")
                        self.error_occurred.emit("restart", f"重啟 {service_name} 失敗: {str(e)}")
            
            # 操作完成
            self.operation_completed.emit(self.operation, success_count, total_count)
            
        except Exception as e:
            print(f"[ERROR] 批量操作執行緒發生嚴重異常: {e}")
            self.error_occurred.emit(self.operation, f"批量操作失敗: {str(e)}")


class ServiceStatusWidget(QGroupBox):
    """單一服務狀態顯示 Widget"""
    
    def __init__(self, service_name: str, parent=None):
        super().__init__(service_name, parent)
        self.service_name = service_name
        self.monitor = ServiceMonitorSingleton().get_monitor()  # 使用單例
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 狀態指示器
        status_layout = QHBoxLayout()
        self.status_label = QLabel("●")
        self.status_label.setFont(QFont("Arial", 24))
        self.status_text = QLabel("檢查中...")
        self.status_text.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 進程資訊
        info_layout = QVBoxLayout()
        self.pid_label = QLabel("PID: --")
        self.cpu_label = QLabel("CPU: --%")
        self.mem_label = QLabel("記憶體: -- MB")
        self.uptime_label = QLabel("運行時間: --")
        
        info_layout.addWidget(self.pid_label)
        info_layout.addWidget(self.cpu_label)
        info_layout.addWidget(self.mem_label)
        info_layout.addWidget(self.uptime_label)
        layout.addLayout(info_layout)
        
        # CPU 進度條
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        layout.addWidget(self.cpu_progress)
        
        # 記憶體進度條
        self.mem_progress = QProgressBar()
        self.mem_progress.setMaximum(500)  # 500 MB
        layout.addWidget(self.mem_progress)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("啟動")
        self.stop_btn = QPushButton("停止")
        self.restart_btn = QPushButton("重啟")
        self.logs_btn = QPushButton("查看日誌")
        
        self.start_btn.clicked.connect(self.start_service)
        self.stop_btn.clicked.connect(self.stop_service)
        self.restart_btn.clicked.connect(self.restart_service)
        self.logs_btn.clicked.connect(self.view_logs)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.restart_btn)
        button_layout.addWidget(self.logs_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def update_status(self):
        """更新服務狀態 - 使用緩存優化性能"""
        try:
            # 檢查主視窗的緩存
            main_window = self._get_main_window()
            cached_status = None
            
            if main_window:
                cached_status = main_window._get_cached_status(self.service_name)
            
            # 如果沒有緩存或緩存過期，則獲取新狀態
            if cached_status is None:
                status = self.monitor.get_service_status(self.service_name)
                if main_window:
                    main_window._cache_status(self.service_name, status)
            else:
                status = cached_status
            
            if status["exists"]:
                # 更新狀態顯示
                if status["state"] == "RUNNING":
                    self.status_label.setStyleSheet("color: #00FF00;")
                    self.status_text.setText("運行中")
                    self.start_btn.setEnabled(False)
                    self.stop_btn.setEnabled(True)
                    self.restart_btn.setEnabled(True)
                elif status["state"] == "STOPPED":
                    self.status_label.setStyleSheet("color: #FF0000;")
                    self.status_text.setText("已停止")
                    self.start_btn.setEnabled(True)
                    self.stop_btn.setEnabled(False)
                    self.restart_btn.setEnabled(False)
                else:
                    self.status_label.setStyleSheet("color: #FFA500;")
                    self.status_text.setText(status["state"])
                
                # 更新進程資訊
                if status["process_info"]:
                    info = status["process_info"]
                    
                    self.pid_label.setText(f"PID: {info['pid']}")
                    self.cpu_label.setText(f"CPU: {info['cpu_percent']:.1f}%")
                    self.mem_label.setText(f"記憶體: {info['memory_mb']:.1f} MB")
                    
                    # 更新進度條
                    self.cpu_progress.setValue(int(info['cpu_percent']))
                    self.mem_progress.setValue(int(info['memory_mb']))
                    
                    # 計算運行時間
                    uptime = datetime.now().timestamp() - info['create_time']
                    hours = int(uptime // 3600)
                    minutes = int((uptime % 3600) // 60)
                    self.uptime_label.setText(f"運行時間: {hours}h {minutes}m")
                else:
                    self.pid_label.setText("PID: --")
                    self.cpu_label.setText("CPU: --%")
                    self.mem_label.setText("記憶體: -- MB")
                    self.uptime_label.setText("運行時間: --")
                    self.cpu_progress.setValue(0)
                    self.mem_progress.setValue(0)
            else:
                self.status_label.setStyleSheet("color: #808080;")
                self.status_text.setText("未安裝")
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)
                self.restart_btn.setEnabled(False)
                
        except Exception as e:
            print(f"[ERROR] 更新 {self.service_name} 狀態時發生異常: {e}")
            # 設置錯誤狀態
            self.status_label.setStyleSheet("color: #FF0000;")
            self.status_text.setText("錯誤")
            self.pid_label.setText(f"錯誤: {str(e)[:20]}...")
            self.cpu_label.setText("CPU: 錯誤")
            self.mem_label.setText("記憶體: 錯誤")
            self.uptime_label.setText("運行時間: 錯誤")
    
    def _get_main_window(self):
        """獲取主視窗實例"""
        widget = self
        while widget and not isinstance(widget, NSSMMonitorGUI):
            widget = widget.parent()
        return widget
    
    def start_service(self):
        """啟動服務"""
        success = self.monitor.start_service(self.service_name)
        if success:
            QMessageBox.information(self, "成功", f"服務 {self.service_name} 已啟動")
        else:
            QMessageBox.critical(self, "錯誤", f"無法啟動服務 {self.service_name}")
        self.update_status()
    
    def stop_service(self):
        """停止服務"""
        try:
            reply = QMessageBox.question(
                self, "確認", 
                f"確定要停止服務 {self.service_name} 嗎？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.monitor.stop_service(self.service_name)
                
                if success:
                    QMessageBox.information(self, "成功", f"服務 {self.service_name} 已停止")
                else:
                    QMessageBox.critical(self, "錯誤", f"無法停止服務 {self.service_name}")
                
                self.update_status()
        except Exception as e:
            print(f"[ERROR] 停止 {self.service_name} 時發生異常: {e}")
            QMessageBox.critical(self, "錯誤", f"停止服務時發生異常: {e}")
    
    def restart_service(self):
        """重啟服務 - 非阻塞版本"""
        try:
            # 顯示重啟中狀態
            self.status_label.setStyleSheet("color: #FFA500;")
            self.status_text.setText("重啟中...")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.restart_btn.setEnabled(False)
            
            # 強制刷新 GUI
            QApplication.processEvents()
            
            success = self.monitor.restart_service(self.service_name)
            
            if success:
                QMessageBox.information(self, "成功", f"服務 {self.service_name} 已重啟")
            else:
                QMessageBox.critical(self, "錯誤", f"無法重啟服務 {self.service_name}")
        
        except Exception as e:
            print(f"[ERROR] 重啟服務 {self.service_name} 時 GUI 發生異常: {e}")
            QMessageBox.critical(self, "錯誤", f"重啟服務時發生異常: {e}")
        
        finally:
            # 恢復狀態並刷新
            self.update_status()
    
    def view_logs(self):
        """查看日誌（發送信號給主視窗）"""
        print(f"[SERVICE_WIDGET] view_logs 被點擊: {self.service_name}")
        
        # 向上找到 NSSMMonitorGUI 主視窗
        widget = self
        while widget and not isinstance(widget, NSSMMonitorGUI):
            widget = widget.parent()
        
        if widget:
            print(f"[SERVICE_WIDGET] 找到主視窗，調用 show_service_logs")
            widget.show_service_logs(self.service_name)
        else:
            print(f"[ERROR] 無法找到主視窗來顯示 {self.service_name} 的日誌")


class LogViewerWidget(QWidget):
    """日誌查看器 Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = ServiceMonitorSingleton().get_monitor()  # 使用單例
        self.current_service = None
        self.log_worker = None  # 日誌載入工作執行緒
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 控制列
        control_layout = QHBoxLayout()
        
        self.service_combo = QComboBox()
        self.service_combo.addItems(["F1T-API", "F1T-PeriodicUpdate", "F1T-CloudflareTunnel"])
        self.service_combo.currentTextChanged.connect(self.load_logs)
        
        self.log_type_combo = QComboBox()
        self.log_type_combo.addItems(["標準輸出", "錯誤輸出"])
        self.log_type_combo.currentTextChanged.connect(self.load_logs)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_logs)
        
        self.clear_btn = QPushButton("清空日誌")
        self.clear_btn.clicked.connect(self.clear_logs)
        
        control_layout.addWidget(QLabel("服務:"))
        control_layout.addWidget(self.service_combo)
        control_layout.addWidget(QLabel("類型:"))
        control_layout.addWidget(self.log_type_combo)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.clear_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 搜尋列
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜尋日誌...")
        self.search_input.textChanged.connect(self.filter_logs)
        
        self.search_btn = QPushButton("搜尋")
        self.search_btn.clicked.connect(self.filter_logs)
        
        search_layout.addWidget(QLabel("搜尋:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        # 日誌顯示區
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # 狀態列
        status_layout = QHBoxLayout()
        self.line_count_label = QLabel("總行數: 0")
        self.file_size_label = QLabel("檔案大小: 0 KB")
        self.loading_label = QLabel("")  # 載入狀態指示
        status_layout.addWidget(self.line_count_label)
        status_layout.addWidget(self.file_size_label)
        status_layout.addWidget(self.loading_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        self.setLayout(layout)
        
        # 初始載入
        self.load_logs()
    
    def load_logs(self):
        """載入日誌 - 非阻塞異步版本（改進版）"""
        # 如果有正在運行的載入任務，直接返回（不等待）
        if self.log_worker and self.log_worker.isRunning():
            print("[LOG_VIEWER] 已有載入任務正在進行中，忽略重複請求")
            return
        
        service_name = self.service_combo.currentText()
        is_error = self.log_type_combo.currentText() == "錯誤輸出"
        
        print(f"[LOG_VIEWER] 正在載入日誌: {service_name} (錯誤日誌: {is_error})")
        
        # 顯示載入中狀態
        self.loading_label.setText("⏳ 載入中...")
        self.loading_label.setStyleSheet("color: #FFA500;")
        self.log_text.setPlainText("正在載入日誌，請稍候...")
        
        # 禁用控制按鈕
        self.refresh_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.service_combo.setEnabled(False)
        self.log_type_combo.setEnabled(False)
        
        # 強制刷新 GUI
        QApplication.processEvents()
        
        # 獲取日誌檔案路徑
        log_file = self.monitor.get_log_file_path(service_name, error_log=is_error)
        print(f"[LOG_VIEWER] 日誌檔案路徑: {log_file}")
        
        if not log_file:
            self._on_loading_failed(f"找不到服務 {service_name} 的日誌檔案配置")
            return
        
        if not os.path.exists(log_file):
            self._on_loading_failed(f"日誌檔案不存在: {log_file}")
            return
        
        # 創建並啟動背景載入執行緒
        self.log_worker = LogLoadWorker(log_file, tail=500, parent=self)
        
        # ✅ 連接信號（使用 Qt.UniqueConnection 避免重複）
        self.log_worker.logs_loaded.connect(self._on_logs_loaded, Qt.UniqueConnection)
        self.log_worker.loading_failed.connect(self._on_loading_failed, Qt.UniqueConnection)
        self.log_worker.finished.connect(self._on_loading_finished, Qt.UniqueConnection)
        
        # 啟動執行緒
        print("[LOG_VIEWER] 啟動日誌載入執行緒")
        self.log_worker.start()
    
    def _on_logs_loaded(self, logs: list, line_count: int, file_size_kb: float):
        """日誌載入成功回調"""
        print(f"[LOG_VIEWER] 日誌載入成功: {line_count} 行")
        
        # 使用分批方式設置文字，避免一次性設置大量文字導致阻塞
        # 限制最多顯示 1000 行
        max_display_lines = 1000
        if len(logs) > max_display_lines:
            logs = logs[-max_display_lines:]
            display_text = f"（日誌過長，僅顯示最後 {max_display_lines} 行）\n\n" + "\n".join(logs)
        else:
            display_text = "\n".join(logs)
        
        self.log_text.setPlainText(display_text)
        self.line_count_label.setText(f"總行數: {line_count}")
        self.file_size_label.setText(f"檔案大小: {file_size_kb:.2f} KB")
        
        # 清除載入中狀態
        self.loading_label.setText("✓ 完成")
        self.loading_label.setStyleSheet("color: #00FF00;")
        
        # 2 秒後清除完成提示
        QTimer.singleShot(2000, lambda: self.loading_label.setText(""))
    
    def _on_loading_failed(self, error_message: str):
        """日誌載入失敗回調"""
        print(f"[LOG_VIEWER] {error_message}")
        self.log_text.setPlainText(error_message)
        self.line_count_label.setText("總行數: 0")
        self.file_size_label.setText("檔案大小: 0 KB")
        
        # 顯示錯誤狀態
        self.loading_label.setText("✗ 失敗")
        self.loading_label.setStyleSheet("color: #FF0000;")
        
        # 2 秒後清除錯誤提示
        QTimer.singleShot(2000, lambda: self.loading_label.setText(""))
    
    def _on_loading_finished(self):
        """日誌載入執行緒結束回調 - 重新啟用控制項"""
        self.refresh_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.service_combo.setEnabled(True)
        self.log_type_combo.setEnabled(True)
        
        # 清理執行緒引用
        if self.log_worker:
            self.log_worker.deleteLater()
            self.log_worker = None
    
    def filter_logs(self):
        """過濾日誌 - 非阻塞版本"""
        search_text = self.search_input.text()
        if not search_text:
            self.load_logs()
            return
        
        print(f"[LOG_VIEWER] 搜尋日誌: '{search_text}'")
        
        # 從當前顯示的文字中搜尋（避免重新讀取檔案）
        current_text = self.log_text.toPlainText()
        
        if not current_text or current_text.startswith("正在載入") or current_text.startswith("找不到"):
            # 如果當前沒有有效日誌，先載入
            self.load_logs()
            return
        
        # 分割成行並過濾
        all_lines = current_text.split('\n')
        filtered = [line for line in all_lines if search_text.lower() in line.lower()]
        
        # 更新顯示
        if filtered:
            self.log_text.setPlainText("\n".join(filtered))
            self.line_count_label.setText(f"符合的行數: {len(filtered)}")
            print(f"[LOG_VIEWER] 找到 {len(filtered)} 行符合搜尋條件")
        else:
            self.log_text.setPlainText(f"找不到包含 '{search_text}' 的日誌行")
            self.line_count_label.setText("符合的行數: 0")
    
    def clear_logs(self):
        """清空日誌檔案"""
        reply = QMessageBox.question(
            self, "確認", 
            "確定要清空日誌檔案嗎？此操作無法復原！",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            service_name = self.service_combo.currentText()
            is_error = self.log_type_combo.currentText() == "錯誤輸出"
            log_file = self.monitor.get_log_file_path(service_name, error_log=is_error)
            
            if log_file and os.path.exists(log_file):
                try:
                    open(log_file, 'w').close()
                    QMessageBox.information(self, "成功", "日誌已清空")
                    self.load_logs()
                except Exception as e:
                    QMessageBox.critical(self, "錯誤", f"清空日誌失敗: {e}")
    
    def show_service_logs(self, service_name: str):
        """顯示指定服務的日誌 - 防止重複調用"""
        print(f"[LOG_VIEWER] show_service_logs 被調用: {service_name}")
        
        # 暫時阻斷信號，避免 setCurrentText 觸發 load_logs
        self.service_combo.blockSignals(True)
        self.service_combo.setCurrentText(service_name)
        self.service_combo.blockSignals(False)
        
        # 手動調用一次 load_logs
        self.load_logs()
    
    def closeEvent(self, event):
        """Widget 關閉事件 - 清理背景執行緒（非阻塞版）"""
        if self.log_worker and self.log_worker.isRunning():
            print("[LOG_VIEWER] 請求停止日誌載入執行緒...")
            # 使用 requestInterruption 而非 terminate（更溫和）
            self.log_worker.requestInterruption()
            # 不等待，直接接受關閉
        event.accept()


class NSSMMonitorGUI(QMainWindow):
    """NSSM 服務監控主視窗"""
    
    def __init__(self):
        super().__init__()
        self.monitor = ServiceMonitorSingleton().get_monitor()  # 使用單例
        self.service_widgets = {}
        self.last_refresh_time = 0
        self.refresh_in_progress = False
        self.batch_worker = None  # 批量操作工作執行緒
        self.status_cache = {}  # 狀態緩存
        self.cache_expiry = 5  # 緩存 5 秒
        self.init_ui()
        
        # 設定自動刷新計時器 - 進一步減少頻率以提升性能
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.smart_refresh)
        self.refresh_timer.start(15000)  # 每 15 秒刷新（優化性能）
        
        # 設定手動刷新按鈕刷新計時器
        self.manual_refresh_timer = QTimer(self)
        self.manual_refresh_timer.setSingleShot(True)
        self.manual_refresh_timer.timeout.connect(self.refresh_all_status)
        
        # 初始刷新
        self.refresh_all_status()
    
    def init_ui(self):
        self.setWindowTitle("F1T NSSM Service Monitor - 服務監控工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主 Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 標題列
        title_layout = QHBoxLayout()
        title_label = QLabel("F1T NSSM 服務監控")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 全局控制按鈕
        self.start_all_btn = QPushButton("啟動所有服務")
        self.stop_all_btn = QPushButton("停止所有服務")
        self.restart_all_btn = QPushButton("重啟所有服務")
        
        self.start_all_btn.clicked.connect(self.start_all_services)
        self.stop_all_btn.clicked.connect(self.stop_all_services)
        self.restart_all_btn.clicked.connect(self.restart_all_services)
        
        title_layout.addWidget(self.start_all_btn)
        title_layout.addWidget(self.stop_all_btn)
        title_layout.addWidget(self.restart_all_btn)
        
        main_layout.addLayout(title_layout)
        
        # 分頁視窗
        self.tabs = QTabWidget()
        
        # Tab 1: 服務狀態
        status_tab = QWidget()
        status_layout = QHBoxLayout(status_tab)
        
        self.service_widgets["F1T-API"] = ServiceStatusWidget("F1T-API")
        self.service_widgets["F1T-PeriodicUpdate"] = ServiceStatusWidget("F1T-PeriodicUpdate")
        self.service_widgets["F1T-CloudflareTunnel"] = ServiceStatusWidget("F1T-CloudflareTunnel")
        
        status_layout.addWidget(self.service_widgets["F1T-API"])
        status_layout.addWidget(self.service_widgets["F1T-PeriodicUpdate"])
        status_layout.addWidget(self.service_widgets["F1T-CloudflareTunnel"])
        
        self.tabs.addTab(status_tab, "服務狀態")
        
        # Tab 2: 日誌查看器
        self.log_viewer = LogViewerWidget()
        self.tabs.addTab(self.log_viewer, "日誌查看")
        
        # Tab 3: 歷史圖表（待實現）
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.addWidget(QLabel("歷史狀態圖表（開發中）"))
        self.tabs.addTab(history_tab, "歷史圖表")
        
        main_layout.addWidget(self.tabs)
        
        # 狀態列
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("準備就緒")
    
    def smart_refresh(self):
        """智能刷新 - 避免重複調用"""
        current_time = datetime.now().timestamp()
        if self.refresh_in_progress:
            return
        
        if current_time - self.last_refresh_time < 12:  # 至少間隔 12 秒
            return
        
        self.refresh_all_status()
    
    def refresh_all_status(self):
        """刷新所有服務狀態 - 優化性能版本"""
        if self.refresh_in_progress:
            return
        
        self.refresh_in_progress = True
        self.last_refresh_time = datetime.now().timestamp()
        
        try:
            # 清理過期緩存
            self._cleanup_expired_cache()
            
            # 批量獲取所有服務狀態（一次性獲取，減少系統調用）
            all_status = {}
            for service_name in self.service_widgets.keys():
                if self._get_cached_status(service_name) is None:
                    status = self.monitor.get_service_status(service_name)
                    self._cache_status(service_name, status)
                    all_status[service_name] = status
            
            # 刷新各個服務 Widget
            for service_name, widget in self.service_widgets.items():
                widget.update_status()
            
            # 更新狀態列 - 使用快取的狀態
            running_count = sum(
                1 for service_name in self.service_widgets.keys()
                if self._get_cached_service_state(service_name) == "RUNNING"
            )
            self.statusBar.showMessage(
                f"最後更新: {datetime.now().strftime('%H:%M:%S')} | "
                f"運行中: {running_count}/3"
            )
            
        except Exception as e:
            print(f"[ERROR] 刷新狀態時發生異常: {e}")
        finally:
            self.refresh_in_progress = False
    
    def _cleanup_expired_cache(self):
        """清理過期的緩存條目"""
        current_time = datetime.now().timestamp()
        expired_keys = [
            key for key, value in self.status_cache.items()
            if current_time - value['timestamp'] > self.cache_expiry
        ]
        for key in expired_keys:
            del self.status_cache[key]
    
    def _get_cached_service_state(self, service_name: str) -> str:
        """獲取快取的服務狀態，避免重複調用"""
        try:
            widget = self.service_widgets.get(service_name)
            if widget and hasattr(widget, 'status_text'):
                status_text = widget.status_text.text()
                if status_text == "運行中":
                    return "RUNNING"
                elif status_text == "已停止":
                    return "STOPPED"
            return "UNKNOWN"
        except Exception:
            return "UNKNOWN"
    
    def _get_cached_status(self, service_name: str):
        """獲取緩存的服務狀態"""
        current_time = datetime.now().timestamp()
        if service_name in self.status_cache:
            cache_entry = self.status_cache[service_name]
            if current_time - cache_entry['timestamp'] < self.cache_expiry:
                return cache_entry['status']
        return None
    
    def _cache_status(self, service_name: str, status: dict):
        """緩存服務狀態"""
        self.status_cache[service_name] = {
            'status': status,
            'timestamp': datetime.now().timestamp()
        }
    
    def start_all_services(self):
        """啟動所有服務 - 背景執行"""
        if self.batch_worker and self.batch_worker.isRunning():
            QMessageBox.warning(self, "警告", "批量操作正在進行中，請稍候...")
            return
        
        self._start_batch_operation("start_all", "啟動所有服務")
    
    def stop_all_services(self):
        """停止所有服務 - 背景執行"""
        if self.batch_worker and self.batch_worker.isRunning():
            QMessageBox.warning(self, "警告", "批量操作正在進行中，請稍候...")
            return
        
        reply = QMessageBox.question(
            self, "確認", 
            "確定要停止所有服務嗎？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._start_batch_operation("stop_all", "停止所有服務")
    
    def restart_all_services(self):
        """重啟所有服務 - 背景執行"""
        if self.batch_worker and self.batch_worker.isRunning():
            QMessageBox.warning(self, "警告", "批量操作正在進行中，請稍候...")
            return
        
        reply = QMessageBox.question(
            self, "確認", 
            "確定要重啟所有服務嗎？此操作可能需要一些時間...",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._start_batch_operation("restart_all", "重啟所有服務")
    
    def _start_batch_operation(self, operation: str, operation_name: str):
        """開始批量操作"""
        # 禁用相關按鈕
        self.start_all_btn.setEnabled(False)
        self.stop_all_btn.setEnabled(False)
        self.restart_all_btn.setEnabled(False)
        
        # 更新狀態列
        self.statusBar.showMessage(f"正在執行: {operation_name}...")
        
        # 創建並啟動背景工作執行緒
        service_names = list(self.service_widgets.keys())
        self.batch_worker = BatchServiceWorker(operation, service_names, self)
        
        # 連接信號
        self.batch_worker.progress_updated.connect(self._on_batch_progress)
        self.batch_worker.operation_completed.connect(self._on_batch_completed)
        self.batch_worker.error_occurred.connect(self._on_batch_error)
        self.batch_worker.finished.connect(self._on_batch_finished)
        
        # 啟動執行緒
        self.batch_worker.start()
    
    def _on_batch_progress(self, operation: str, service_name: str):
        """批量操作進度更新"""
        self.statusBar.showMessage(f"正在{operation}服務: {service_name}...")
    
    def _on_batch_completed(self, operation: str, success_count: int, total_count: int):
        """批量操作完成"""
        operation_names = {
            "start_all": "啟動",
            "stop_all": "停止", 
            "restart_all": "重啟"
        }
        op_name = operation_names.get(operation, operation)
        
        QMessageBox.information(
            self, "完成", 
            f"已{op_name} {success_count}/{total_count} 個服務"
        )
        
        # 刷新狀態顯示
        self.refresh_all_status()
    
    def _on_batch_error(self, operation: str, error_message: str):
        """批量操作發生錯誤"""
        QMessageBox.critical(
            self, "錯誤", 
            f"批量操作失敗: {error_message}"
        )
    
    def _on_batch_finished(self):
        """批量操作執行緒結束 - 重新啟用按鈕"""
        self.start_all_btn.setEnabled(True)
        self.stop_all_btn.setEnabled(True)
        self.restart_all_btn.setEnabled(True)
        
        self.statusBar.showMessage("準備就緒")
        
        # 清理執行緒引用
        if self.batch_worker:
            self.batch_worker.deleteLater()
            self.batch_worker = None
    
    def show_service_logs(self, service_name: str):
        """切換到日誌頁面並顯示指定服務的日誌"""
        print(f"[MAIN_WINDOW] show_service_logs 被調用: {service_name}")
        print(f"[MAIN_WINDOW] 切換到日誌分頁")
        self.tabs.setCurrentIndex(1)  # 切換到日誌頁面
        print(f"[MAIN_WINDOW] 調用 log_viewer.show_service_logs")
        self.log_viewer.show_service_logs(service_name)
    
    def closeEvent(self, event):
        """視窗關閉事件 - 清理背景執行緒"""
        if self.batch_worker and self.batch_worker.isRunning():
            # 請求停止操作
            self.batch_worker.stop_operation()
            
            # 等待執行緒結束（最多等待3秒）
            if not self.batch_worker.wait(3000):
                # 強制終止
                self.batch_worker.terminate()
                self.batch_worker.wait(1000)
        
        # 停止自動刷新計時器
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        
        event.accept()


def main():
    """主程式入口 - 性能優化版本"""
    app = QApplication(sys.argv)
    
    # 性能優化設定
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)
    
    # 設定應用程式樣式
    app.setStyle("Fusion")
    
    # 深色主題
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    # 創建並顯示主視窗
    window = NSSMMonitorGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
