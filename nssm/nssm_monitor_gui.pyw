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
        self.monitor = NSSMServiceMonitor(debug_enabled=False)
        self.should_stop = False
    
    def stop_operation(self):
        """請求停止操作"""
        self.should_stop = True
    
    def run(self):
        """背景執行緒主函數"""
        success_count = 0
        total_count = len(self.service_names)
        
        try:
            if self.operation == "start_all":
                for service_name in self.service_names:
                    if self.should_stop:
                        break
                    
                    self.progress_updated.emit("啟動", service_name)
                    if self.monitor.start_service(service_name):
                        success_count += 1
                    
            elif self.operation == "stop_all":
                for service_name in self.service_names:
                    if self.should_stop:
                        break
                    
                    self.progress_updated.emit("停止", service_name)
                    if self.monitor.stop_service(service_name):
                        success_count += 1
                        
            elif self.operation == "restart_all":
                for service_name in self.service_names:
                    if self.should_stop:
                        break
                    
                    self.progress_updated.emit("重啟", service_name)
                    if self.monitor.restart_service(service_name):
                        success_count += 1
            
            # 操作完成
            self.operation_completed.emit(self.operation, success_count, total_count)
            
        except Exception as e:
            self.error_occurred.emit(self.operation, str(e))


class ServiceStatusWidget(QGroupBox):
    """單一服務狀態顯示 Widget"""
    
    def __init__(self, service_name: str, parent=None):
        super().__init__(service_name, parent)
        self.service_name = service_name
        self.monitor = NSSMServiceMonitor(debug_enabled=False)  # 關閉 DEBUG
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
        """更新服務狀態"""
        try:
            status = self.monitor.get_service_status(self.service_name)
            
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
        """重啟服務"""
        success = self.monitor.restart_service(self.service_name)
        if success:
            QMessageBox.information(self, "成功", f"服務 {self.service_name} 已重啟")
        else:
            QMessageBox.critical(self, "錯誤", f"無法重啟服務 {self.service_name}")
        self.update_status()
    
    def view_logs(self):
        """查看日誌（發送信號給主視窗）"""
        # 向上找到 NSSMMonitorGUI 主視窗
        widget = self
        while widget and not isinstance(widget, NSSMMonitorGUI):
            widget = widget.parent()
        
        if widget:
            widget.show_service_logs(self.service_name)
        else:
            print(f"[ERROR] 無法找到主視窗來顯示 {self.service_name} 的日誌")


class LogViewerWidget(QWidget):
    """日誌查看器 Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = NSSMServiceMonitor(debug_enabled=False)  # 關閉 DEBUG
        self.current_service = None
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
        status_layout.addWidget(self.line_count_label)
        status_layout.addWidget(self.file_size_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        self.setLayout(layout)
        
        # 初始載入
        self.load_logs()
    
    def load_logs(self):
        """載入日誌"""
        service_name = self.service_combo.currentText()
        is_error = self.log_type_combo.currentText() == "錯誤輸出"
        
        logs = self.monitor.get_service_logs(service_name, tail=500, error_log=is_error)
        
        if logs:
            self.log_text.setPlainText("\n".join(logs))
            self.line_count_label.setText(f"總行數: {len(logs)}")
            
            # 獲取檔案大小
            log_file = self.monitor.get_log_file_path(service_name, error_log=is_error)
            if log_file and os.path.exists(log_file):
                size_kb = os.path.getsize(log_file) / 1024
                self.file_size_label.setText(f"檔案大小: {size_kb:.2f} KB")
        else:
            self.log_text.setPlainText("找不到日誌檔案或日誌為空")
            self.line_count_label.setText("總行數: 0")
            self.file_size_label.setText("檔案大小: 0 KB")
    
    def filter_logs(self):
        """過濾日誌"""
        search_text = self.search_input.text()
        if not search_text:
            self.load_logs()
            return
        
        service_name = self.service_combo.currentText()
        is_error = self.log_type_combo.currentText() == "錯誤輸出"
        logs = self.monitor.get_service_logs(service_name, tail=500, error_log=is_error)
        
        if logs:
            filtered = [line for line in logs if search_text.lower() in line.lower()]
            self.log_text.setPlainText("\n".join(filtered))
            self.line_count_label.setText(f"符合的行數: {len(filtered)}")
    
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
        """顯示指定服務的日誌"""
        self.service_combo.setCurrentText(service_name)
        self.load_logs()


class NSSMMonitorGUI(QMainWindow):
    """NSSM 服務監控主視窗"""
    
    def __init__(self):
        super().__init__()
        self.monitor = NSSMServiceMonitor(debug_enabled=False)  # 關閉 DEBUG
        self.service_widgets = {}
        self.last_refresh_time = 0
        self.refresh_in_progress = False
        self.batch_worker = None  # 批量操作工作執行緒
        self.init_ui()
        
        # 設定自動刷新計時器 - 改為較慢的刷新間隔
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.smart_refresh)
        self.refresh_timer.start(10000)  # 每 10 秒刷新（減少頻率）
        
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
        
        if current_time - self.last_refresh_time < 8:  # 至少間隔 8 秒
            return
        
        self.refresh_all_status()
    
    def refresh_all_status(self):
        """刷新所有服務狀態"""
        if self.refresh_in_progress:
            return
        
        self.refresh_in_progress = True
        self.last_refresh_time = datetime.now().timestamp()
        
        try:
            # 刷新各個服務 Widget
            for service_name, widget in self.service_widgets.items():
                widget.update_status()
            
            # 更新狀態列 - 使用快取的狀態而非重複查詢
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
        self.tabs.setCurrentIndex(1)  # 切換到日誌頁面
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
    """主程式入口"""
    app = QApplication(sys.argv)
    
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
