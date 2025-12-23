# -*- coding: utf-8 -*-
"""
SignalR Recorder GUI - 主視窗

提供錄製/解析 SignalR 訊號的完整 GUI 介面。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QStatusBar, QSplitter,
    QCheckBox, QSpinBox, QComboBox, QProgressBar,
    QHeaderView, QFrame, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor

from tools.signalr_recorder.core.recorder import SignalRRecorder
from tools.signalr_recorder.core.parser import SignalRParser


class SignalRRecorderWindow(QMainWindow):
    """SignalR 錄製器主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 SignalR Recorder - 2026 Data Collector")
        self.setMinimumSize(1200, 800)
        
        # 核心元件
        self.recorder = SignalRRecorder()
        self.parser = SignalRParser()
        
        # 統計數據
        self._message_counts: Dict[str, int] = {}
        self._total_messages = 0
        self._start_time: Optional[datetime] = None
        
        # 建立 UI
        self._setup_ui()
        self._connect_signals()
        
        # 更新計時器
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_stats_display)
        
    def _setup_ui(self):
        """建立使用者介面"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        
        # ========== 頂部控制區 ==========
        control_group = QGroupBox("Recording Control")
        control_layout = QHBoxLayout(control_group)
        
        # 連線狀態
        self.lbl_status = QLabel("Status: Disconnected")
        self.lbl_status.setStyleSheet("color: #888888; font-weight: bold;")
        control_layout.addWidget(self.lbl_status)
        
        control_layout.addStretch()
        
        # F1TV Token 狀態
        self.lbl_token = QLabel("Token: Not Set")
        self.lbl_token.setStyleSheet("color: #f39c12;")
        control_layout.addWidget(self.lbl_token)
        
        self.btn_login = QPushButton("F1TV Login")
        self.btn_login.setMaximumWidth(100)
        self.btn_login.clicked.connect(self._on_login_clicked)
        control_layout.addWidget(self.btn_login)
        
        control_layout.addSpacing(20)
        
        # 錄製按鈕
        self.btn_record = QPushButton("Start Recording")
        self.btn_record.setMinimumWidth(150)
        self.btn_record.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.btn_record.clicked.connect(self._on_record_clicked)
        control_layout.addWidget(self.btn_record)
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setMinimumWidth(80)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        control_layout.addWidget(self.btn_stop)
        
        layout.addWidget(control_group)
        
        # ========== 主要內容區 (Tabs) ==========
        self.tabs = QTabWidget()
        
        # Tab 1: 即時監控
        self.tabs.addTab(self._create_monitor_tab(), "Live Monitor")
        
        # Tab 2: 訊號統計
        self.tabs.addTab(self._create_stats_tab(), "Signal Statistics")
        
        # Tab 3: 數據解析
        self.tabs.addTab(self._create_parser_tab(), "Data Parser")
        
        # Tab 4: 錄製檔案
        self.tabs.addTab(self._create_files_tab(), "Recordings")
        
        layout.addWidget(self.tabs)
        
        # ========== 狀態列 ==========
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.lbl_msg_count = QLabel("Messages: 0")
        self.lbl_duration = QLabel("Duration: 00:00:00")
        self.lbl_rate = QLabel("Rate: 0 msg/s")
        
        self.statusBar.addPermanentWidget(self.lbl_msg_count)
        self.statusBar.addPermanentWidget(self.lbl_duration)
        self.statusBar.addPermanentWidget(self.lbl_rate)
        
        self.statusBar.showMessage("Ready. Click 'Start Recording' to begin.")
        
    def _create_monitor_tab(self) -> QWidget:
        """建立即時監控 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # 左側: 原始訊息
        left_group = QGroupBox("Raw Messages (Latest 100)")
        left_layout = QVBoxLayout(left_group)
        
        self.txt_raw_messages = QTextEdit()
        self.txt_raw_messages.setReadOnly(True)
        self.txt_raw_messages.setFont(QFont("Consolas", 9))
        self.txt_raw_messages.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
            }
        """)
        left_layout.addWidget(self.txt_raw_messages)
        
        # 篩選選項
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItem("All Messages")
        self.cmb_filter.addItem("TimingData")
        self.cmb_filter.addItem("CarData.z")
        self.cmb_filter.addItem("Position.z")
        self.cmb_filter.addItem("RaceControlMessages")
        self.cmb_filter.addItem("WeatherData")
        self.cmb_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.cmb_filter)
        
        self.chk_auto_scroll = QCheckBox("Auto Scroll")
        self.chk_auto_scroll.setChecked(True)
        filter_layout.addWidget(self.chk_auto_scroll)
        
        filter_layout.addStretch()
        
        self.btn_clear_log = QPushButton("Clear")
        self.btn_clear_log.clicked.connect(self.txt_raw_messages.clear)
        filter_layout.addWidget(self.btn_clear_log)
        
        left_layout.addLayout(filter_layout)
        splitter.addWidget(left_group)
        
        # 右側: 解析後的訊息
        right_group = QGroupBox("Parsed Data")
        right_layout = QVBoxLayout(right_group)
        
        self.txt_parsed = QTextEdit()
        self.txt_parsed.setReadOnly(True)
        self.txt_parsed.setFont(QFont("Consolas", 9))
        self.txt_parsed.setStyleSheet("""
            QTextEdit {
                background-color: #1a2634;
                color: #4fc3f7;
                border: 1px solid #333;
            }
        """)
        right_layout.addWidget(self.txt_parsed)
        splitter.addWidget(right_group)
        
        splitter.setSizes([600, 400])
        layout.addWidget(splitter)
        
        return widget
        
    def _create_stats_tab(self) -> QWidget:
        """建立訊號統計 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 統計表格
        self.tbl_stats = QTableWidget()
        self.tbl_stats.setColumnCount(4)
        self.tbl_stats.setHorizontalHeaderLabels([
            "Topic", "Count", "Rate (msg/s)", "Last Received"
        ])
        self.tbl_stats.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_stats.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_stats.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_stats.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_stats.setAlternatingRowColors(True)
        layout.addWidget(self.tbl_stats)
        
        # 圖表區域 (預留)
        chart_group = QGroupBox("Message Rate Chart (Coming Soon)")
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.addWidget(QLabel("Rate visualization will be added here"))
        layout.addWidget(chart_group)
        
        return widget
        
    def _create_parser_tab(self) -> QWidget:
        """建立數據解析 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 檔案選擇
        file_group = QGroupBox("Load Recording File")
        file_layout = QHBoxLayout(file_group)
        
        self.txt_parse_file = QLineEdit()
        self.txt_parse_file.setPlaceholderText("Select a .jsonl file to parse...")
        file_layout.addWidget(self.txt_parse_file)
        
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self._on_browse_file)
        file_layout.addWidget(self.btn_browse)
        
        self.btn_parse = QPushButton("Parse File")
        self.btn_parse.clicked.connect(self._on_parse_file)
        file_layout.addWidget(self.btn_parse)
        
        layout.addWidget(file_group)
        
        # 解析選項
        options_group = QGroupBox("Parse Options")
        options_layout = QHBoxLayout(options_group)
        
        options_layout.addWidget(QLabel("Extract Topics:"))
        
        self.chk_timing = QCheckBox("TimingData")
        self.chk_timing.setChecked(True)
        options_layout.addWidget(self.chk_timing)
        
        self.chk_cardata = QCheckBox("CarData.z")
        self.chk_cardata.setChecked(True)
        options_layout.addWidget(self.chk_cardata)
        
        self.chk_position = QCheckBox("Position.z")
        self.chk_position.setChecked(True)
        options_layout.addWidget(self.chk_position)
        
        self.chk_weather = QCheckBox("WeatherData")
        self.chk_weather.setChecked(True)
        options_layout.addWidget(self.chk_weather)
        
        self.chk_rcm = QCheckBox("RaceControlMessages")
        self.chk_rcm.setChecked(True)
        options_layout.addWidget(self.chk_rcm)
        
        options_layout.addStretch()
        layout.addWidget(options_group)
        
        # 解析進度
        self.progress_parse = QProgressBar()
        self.progress_parse.setVisible(False)
        layout.addWidget(self.progress_parse)
        
        # 解析結果
        result_group = QGroupBox("Parse Results")
        result_layout = QVBoxLayout(result_group)
        
        self.txt_parse_result = QTextEdit()
        self.txt_parse_result.setReadOnly(True)
        self.txt_parse_result.setFont(QFont("Consolas", 9))
        result_layout.addWidget(self.txt_parse_result)
        
        # 匯出按鈕
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self.btn_export_json = QPushButton("Export as JSON")
        self.btn_export_json.clicked.connect(lambda: self._export_parsed("json"))
        self.btn_export_json.setEnabled(False)
        export_layout.addWidget(self.btn_export_json)
        
        self.btn_export_csv = QPushButton("Export as CSV")
        self.btn_export_csv.clicked.connect(lambda: self._export_parsed("csv"))
        self.btn_export_csv.setEnabled(False)
        export_layout.addWidget(self.btn_export_csv)
        
        result_layout.addLayout(export_layout)
        layout.addWidget(result_group)
        
        return widget
        
    def _create_files_tab(self) -> QWidget:
        """建立錄製檔案 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 錄製目錄
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Recording Directory:"))
        
        self.txt_rec_dir = QLineEdit()
        default_dir = Path.home() / ".f1t" / "signalr_recordings"
        self.txt_rec_dir.setText(str(default_dir))
        dir_layout.addWidget(self.txt_rec_dir)
        
        self.btn_change_dir = QPushButton("Change...")
        self.btn_change_dir.clicked.connect(self._on_change_dir)
        dir_layout.addWidget(self.btn_change_dir)
        
        self.btn_open_dir = QPushButton("Open Folder")
        self.btn_open_dir.clicked.connect(self._on_open_dir)
        dir_layout.addWidget(self.btn_open_dir)
        
        layout.addLayout(dir_layout)
        
        # 檔案列表
        self.tbl_files = QTableWidget()
        self.tbl_files.setColumnCount(5)
        self.tbl_files.setHorizontalHeaderLabels([
            "Filename", "Date", "Duration", "Messages", "Size"
        ])
        self.tbl_files.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_files.setAlternatingRowColors(True)
        self.tbl_files.doubleClicked.connect(self._on_file_double_click)
        layout.addWidget(self.tbl_files)
        
        # 刷新按鈕
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_refresh_files = QPushButton("Refresh List")
        self.btn_refresh_files.clicked.connect(self._refresh_file_list)
        btn_layout.addWidget(self.btn_refresh_files)
        
        layout.addLayout(btn_layout)
        
        # 初始載入
        QTimer.singleShot(100, self._refresh_file_list)
        
        return widget
        
    def _connect_signals(self):
        """連接信號"""
        self.recorder.message_received.connect(self._on_message_received)
        self.recorder.connection_status.connect(self._on_connection_status)
        self.recorder.error_occurred.connect(self._on_error)
        self.recorder.recording_stopped.connect(self._on_recording_stopped)
        
    # ========== Event Handlers ==========
    
    def _on_login_clicked(self):
        """F1TV 登入"""
        try:
            from core.f1tv_auth import F1TVAuthManager
            
            self._auth_manager = F1TVAuthManager()
            
            if self._auth_manager.is_authenticated():
                token_info = self._auth_manager.get_token_info()
                self.lbl_token.setText(f"Token: Valid (expires {token_info.get('exp_str', 'Unknown')})")
                self.lbl_token.setStyleSheet("color: #27ae60;")
                self.recorder.set_access_token(self._auth_manager.get_token())
                QMessageBox.information(self, "F1TV", "Already logged in!")
            else:
                self._auth_manager.auth_success.connect(self._on_auth_success)
                self._auth_manager.auth_failed.connect(self._on_auth_failed)
                self._auth_manager.start_auth_flow()
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to initialize auth: {e}")
            
    def _on_auth_success(self, token: str):
        """認證成功"""
        self.lbl_token.setText("Token: Valid")
        self.lbl_token.setStyleSheet("color: #27ae60;")
        self.recorder.set_access_token(token)
        QMessageBox.information(self, "F1TV", "Login successful!")
        
    def _on_auth_failed(self, error: str):
        """認證失敗"""
        self.lbl_token.setText("Token: Failed")
        self.lbl_token.setStyleSheet("color: #e74c3c;")
        QMessageBox.warning(self, "F1TV Login Failed", error)
        
    def _on_record_clicked(self):
        """開始錄製"""
        # 設置錄製目錄
        rec_dir = Path(self.txt_rec_dir.text())
        rec_dir.mkdir(parents=True, exist_ok=True)
        self.recorder.set_output_dir(rec_dir)
        
        # 開始錄製
        self.recorder.start_recording()
        
        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self._message_counts.clear()
        self._total_messages = 0
        self._start_time = datetime.now()
        
        self._update_timer.start(1000)  # 每秒更新
        
    def _on_stop_clicked(self):
        """停止錄製"""
        self.recorder.stop_recording()
        
    def _on_recording_stopped(self, filepath: str):
        """錄製停止回調"""
        self.btn_record.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._update_timer.stop()
        
        self.lbl_status.setText("Status: Disconnected")
        self.lbl_status.setStyleSheet("color: #888888; font-weight: bold;")
        
        if filepath:
            self.statusBar.showMessage(f"Recording saved: {filepath}")
            self._refresh_file_list()
            QMessageBox.information(
                self, "Recording Complete",
                f"Recording saved to:\n{filepath}\n\n"
                f"Total messages: {self._total_messages}"
            )
        
    def _on_message_received(self, topic: str, data: dict, raw: str):
        """收到訊息"""
        self._total_messages += 1
        self._message_counts[topic] = self._message_counts.get(topic, 0) + 1
        
        # 更新原始訊息顯示
        current_filter = self.cmb_filter.currentText()
        if current_filter == "All Messages" or topic == current_filter:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            display_text = f"[{timestamp}] {topic}: {raw[:200]}...\n" if len(raw) > 200 else f"[{timestamp}] {topic}: {raw}\n"
            
            self.txt_raw_messages.moveCursor(self.txt_raw_messages.textCursor().End)
            self.txt_raw_messages.insertPlainText(display_text)
            
            if self.chk_auto_scroll.isChecked():
                self.txt_raw_messages.verticalScrollBar().setValue(
                    self.txt_raw_messages.verticalScrollBar().maximum()
                )
            
            # 限制顯示行數
            doc = self.txt_raw_messages.document()
            if doc.blockCount() > 100:
                cursor = self.txt_raw_messages.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.movePosition(cursor.Down, cursor.KeepAnchor, doc.blockCount() - 100)
                cursor.removeSelectedText()
                
        # 更新解析數據顯示
        if data:
            try:
                parsed_json = json.dumps(data, indent=2, ensure_ascii=False)
                if len(parsed_json) > 500:
                    parsed_json = parsed_json[:500] + "..."
                self.txt_parsed.setText(f"Topic: {topic}\n\n{parsed_json}")
            except:
                pass
                
    def _on_connection_status(self, status: str):
        """連線狀態變更"""
        self.lbl_status.setText(f"Status: {status}")
        
        if "Connected" in status:
            self.lbl_status.setStyleSheet("color: #27ae60; font-weight: bold;")
        elif "Error" in status or "Disconnected" in status:
            self.lbl_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            self.lbl_status.setStyleSheet("color: #f39c12; font-weight: bold;")
            
        self.statusBar.showMessage(status)
        
    def _on_error(self, error: str):
        """錯誤發生"""
        self.statusBar.showMessage(f"Error: {error}")
        
    def _on_filter_changed(self, filter_text: str):
        """訊息篩選變更"""
        self.txt_raw_messages.clear()
        
    def _update_stats_display(self):
        """更新統計顯示"""
        # 更新狀態列
        self.lbl_msg_count.setText(f"Messages: {self._total_messages:,}")
        
        if self._start_time:
            duration = datetime.now() - self._start_time
            hours, remainder = divmod(int(duration.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.lbl_duration.setText(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            rate = self._total_messages / max(duration.total_seconds(), 1)
            self.lbl_rate.setText(f"Rate: {rate:.1f} msg/s")
            
        # 更新統計表格
        self.tbl_stats.setRowCount(len(self._message_counts))
        for row, (topic, count) in enumerate(sorted(self._message_counts.items(), key=lambda x: -x[1])):
            self.tbl_stats.setItem(row, 0, QTableWidgetItem(topic))
            self.tbl_stats.setItem(row, 1, QTableWidgetItem(str(count)))
            
            if self._start_time:
                duration = (datetime.now() - self._start_time).total_seconds()
                rate = count / max(duration, 1)
                self.tbl_stats.setItem(row, 2, QTableWidgetItem(f"{rate:.2f}"))
            else:
                self.tbl_stats.setItem(row, 2, QTableWidgetItem("-"))
                
            self.tbl_stats.setItem(row, 3, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
            
    def _on_browse_file(self):
        """瀏覽檔案"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Recording File",
            str(Path(self.txt_rec_dir.text())),
            "JSONL Files (*.jsonl);;All Files (*)"
        )
        if filepath:
            self.txt_parse_file.setText(filepath)
            
    def _on_parse_file(self):
        """解析檔案"""
        filepath = self.txt_parse_file.text()
        if not filepath or not Path(filepath).exists():
            QMessageBox.warning(self, "Error", "Please select a valid file")
            return
            
        self.progress_parse.setVisible(True)
        self.progress_parse.setValue(0)
        
        try:
            # 選擇要解析的 topics
            topics = []
            if self.chk_timing.isChecked():
                topics.append("TimingData")
            if self.chk_cardata.isChecked():
                topics.append("CarData.z")
            if self.chk_position.isChecked():
                topics.append("Position.z")
            if self.chk_weather.isChecked():
                topics.append("WeatherData")
            if self.chk_rcm.isChecked():
                topics.append("RaceControlMessages")
                
            # 解析
            result = self.parser.parse_file(filepath, topics)
            
            self.progress_parse.setValue(100)
            
            # 顯示結果
            summary = json.dumps(result.get("summary", {}), indent=2, ensure_ascii=False)
            self.txt_parse_result.setText(f"Parse Summary:\n\n{summary}")
            
            self._parsed_data = result
            self.btn_export_json.setEnabled(True)
            self.btn_export_csv.setEnabled(True)
            
            self.statusBar.showMessage(f"Parsed {result.get('summary', {}).get('total_messages', 0)} messages")
            
        except Exception as e:
            QMessageBox.warning(self, "Parse Error", str(e))
            
        finally:
            self.progress_parse.setVisible(False)
            
    def _export_parsed(self, format_type: str):
        """匯出解析數據"""
        if not hasattr(self, '_parsed_data'):
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, f"Export as {format_type.upper()}",
            str(Path.home()),
            f"{format_type.upper()} Files (*.{format_type})"
        )
        
        if filepath:
            try:
                if format_type == "json":
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(self._parsed_data, f, indent=2, ensure_ascii=False)
                elif format_type == "csv":
                    self.parser.export_to_csv(self._parsed_data, filepath)
                    
                QMessageBox.information(self, "Export Complete", f"Data exported to:\n{filepath}")
            except Exception as e:
                QMessageBox.warning(self, "Export Error", str(e))
                
    def _on_change_dir(self):
        """變更錄製目錄"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Recording Directory",
            self.txt_rec_dir.text()
        )
        if dir_path:
            self.txt_rec_dir.setText(dir_path)
            self._refresh_file_list()
            
    def _on_open_dir(self):
        """開啟錄製目錄"""
        import subprocess
        dir_path = self.txt_rec_dir.text()
        if Path(dir_path).exists():
            subprocess.Popen(f'explorer "{dir_path}"')
        else:
            QMessageBox.warning(self, "Error", "Directory does not exist")
            
    def _refresh_file_list(self):
        """刷新檔案列表"""
        dir_path = Path(self.txt_rec_dir.text())
        if not dir_path.exists():
            return
            
        files = list(dir_path.glob("*.jsonl"))
        self.tbl_files.setRowCount(len(files))
        
        for row, filepath in enumerate(sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)):
            stat = filepath.stat()
            
            self.tbl_files.setItem(row, 0, QTableWidgetItem(filepath.name))
            self.tbl_files.setItem(row, 1, QTableWidgetItem(
                datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            ))
            
            # 嘗試讀取 meta 檔案
            meta_file = filepath.with_suffix('.meta.json')
            if meta_file.exists():
                try:
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                    self.tbl_files.setItem(row, 2, QTableWidgetItem(
                        f"{meta.get('duration_seconds', 0):.1f}s"
                    ))
                    self.tbl_files.setItem(row, 3, QTableWidgetItem(
                        str(meta.get('total_messages', 0))
                    ))
                except:
                    self.tbl_files.setItem(row, 2, QTableWidgetItem("-"))
                    self.tbl_files.setItem(row, 3, QTableWidgetItem("-"))
            else:
                self.tbl_files.setItem(row, 2, QTableWidgetItem("-"))
                self.tbl_files.setItem(row, 3, QTableWidgetItem("-"))
                
            size_kb = stat.st_size / 1024
            if size_kb > 1024:
                size_str = f"{size_kb/1024:.1f} MB"
            else:
                size_str = f"{size_kb:.1f} KB"
            self.tbl_files.setItem(row, 4, QTableWidgetItem(size_str))
            
    def _on_file_double_click(self, index):
        """雙擊檔案"""
        row = index.row()
        filename = self.tbl_files.item(row, 0).text()
        filepath = Path(self.txt_rec_dir.text()) / filename
        
        self.txt_parse_file.setText(str(filepath))
        self.tabs.setCurrentIndex(2)  # 切換到 Parser tab
        
    def closeEvent(self, event):
        """關閉視窗"""
        if self.recorder.is_recording():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Recording is in progress. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.recorder.stop_recording()
            
        self._update_timer.stop()
        event.accept()
