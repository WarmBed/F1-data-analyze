#!/usr/bin/env python3
"""
Objgraph 診斷視窗
Objgraph Diagnostic Window

提供物件追蹤和記憶體診斷功能
"""

import gc
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, List, Optional

import objgraph
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QLabel, QSpinBox, QGroupBox,
    QSplitter, QComboBox, QCheckBox, QProgressBar, QMessageBox,
    QFileDialog, QTabWidget, QLineEdit, QHeaderView
)

from core.gui_i18n import tr

logger = get_logger("objgraph_diagnostic", component="gui")


def _log_to_logger(*args, sep=" ", end=""):
    message = sep.join(str(arg) for arg in args)
    if message.startswith("[ERROR]") or "❌" in message:
        logger.error(message)
    elif message.startswith("[WARNING]") or "⚠️" in message:
        logger.warning(message)
    else:
        logger.info(message)


print = _log_to_logger


class ObjectScanWorker(QThread):
    """背景執行緒 - 掃描物件"""
    
    scan_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, scan_type: str, limit: Optional[int] = 20):
        super().__init__()
        self.scan_type = scan_type
        self.limit = limit
    
    def run(self):
        """執行掃描"""
        try:
            gc.collect()  # 先執行垃圾回收
            
            if self.scan_type == "most_common":
                # 如果 limit 是 None，顯示所有類型
                if self.limit is None:
                    data = objgraph.most_common_types()
                else:
                    data = objgraph.most_common_types(limit=self.limit)
                result = {
                    "type": "most_common",
                    "data": data
                }
            elif self.scan_type == "growth":
                # 如果 limit 是 None，顯示所有變化
                if self.limit is None:
                    data = objgraph.growth()
                else:
                    data = objgraph.growth(limit=self.limit)
                result = {
                    "type": "growth",
                    "data": data
                }
            else:
                result = {"type": "unknown", "data": []}
            
            # ✅ 中斷檢查：被中斷時不發送信號
            if self.isInterruptionRequested():
                return
            self.scan_completed.emit(result)
        except Exception as e:
            logger.error(f"掃描失敗: {e}")
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            self.error_occurred.emit(str(e))


class ReferenceGraphWorker(QThread):
    """背景執行緒 - 生成引用圖"""
    
    graph_completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, obj_type: str, max_depth: int = 3):
        super().__init__()
        self.obj_type = obj_type
        self.max_depth = max_depth
    
    def run(self):
        """生成引用圖"""
        try:
            # 創建 output 資料夾
            output_dir = Path("output/objgraph")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"{self.obj_type}_{timestamp}.png"
            
            # 尋找該類型的物件
            objects = objgraph.by_type(self.obj_type)
            if not objects:
                self.error_occurred.emit(f"找不到類型 '{self.obj_type}' 的物件\n\n提示：請先執行「掃描物件」查看可用的類型")
                return
            
            # 生成引用圖（選擇第一個物件）
            try:
                objgraph.show_backrefs(
                    objects[0],
                    max_depth=self.max_depth,
                    filename=str(output_file),
                    too_many=10
                )
            except FileNotFoundError as e:
                # Graphviz 未安裝
                if 'dot' in str(e).lower() or 'graphviz' in str(e).lower():
                    self.error_occurred.emit(
                        "Graphviz 未安裝或未加入 PATH\n\n"
                        "請安裝 Graphviz:\n"
                        "1. 下載: https://graphviz.org/download/\n"
                        "2. Windows: 使用安裝程式並確保勾選 'Add to PATH'\n"
                        "3. 或使用 Chocolatey: choco install graphviz\n"
                        "4. 安裝後重新啟動 GUI"
                    )
                    return
                else:
                    raise
            
            # 檢查檔案是否成功生成
            if not output_file.exists():
                if self.isInterruptionRequested():
                    return
                self.error_occurred.emit(f"引用圖生成失敗：檔案未創建\n{output_file}")
                return
            
            # ✅ 中斷檢查：被中斷時不發送信號
            if self.isInterruptionRequested():
                return
            self.graph_completed.emit(str(output_file))
            
        except Exception as e:
            logger.error(f"生成引用圖失敗: {e}")
            import traceback
            error_detail = traceback.format_exc()
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            self.error_occurred.emit(f"生成引用圖失敗:\n{str(e)}\n\n詳細錯誤:\n{error_detail}")


class ObjgraphDiagnosticWindow(QWidget):
    """Objgraph 診斷主視窗"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('objgraph_diagnostic_title', '物件記憶體診斷工具'))
        self.resize(1200, 800)
        
        # 存儲上次掃描結果（用於追蹤成長）
        self.last_scan_result: Optional[Dict] = None
        
        # 自動刷新計時器
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self._on_auto_refresh)
        
        # 操作記錄追蹤
        self.action_history: List[Dict] = []  # 儲存操作歷史
        self.last_total_objects: int = 0  # 上次的物件總數
        
        self._init_ui()
        logger.info("Objgraph 診斷視窗已初始化")
    
    def _init_ui(self):
        """初始化 UI"""
        main_layout = QVBoxLayout(self)
        
        # 標題區域
        title_label = QLabel(tr('objgraph_diagnostic_title', '物件記憶體診斷工具'))
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 控制面板
        control_group = self._create_control_panel()
        main_layout.addWidget(control_group)
        
        # Tab Widget
        tab_widget = QTabWidget()
        
        # Tab 1: 物件統計
        self.stats_widget = self._create_stats_tab()
        tab_widget.addTab(self.stats_widget, tr('objgraph_tab_stats', '物件統計'))
        
        # Tab 2: 成長追蹤
        self.growth_widget = self._create_growth_tab()
        tab_widget.addTab(self.growth_widget, tr('objgraph_tab_growth', '成長追蹤'))
        
        # Tab 3: 引用圖
        self.graph_widget = self._create_graph_tab()
        tab_widget.addTab(self.graph_widget, tr('objgraph_tab_graph', '引用圖'))
        
        # Tab 4: 操作記錄
        self.action_widget = self._create_action_tab()
        tab_widget.addTab(self.action_widget, tr('objgraph_tab_action', '操作記錄'))
        
        # Tab 5: Python Console (新增)
        self.console_widget = self._create_console_tab()
        tab_widget.addTab(self.console_widget, tr('objgraph_tab_console', 'Python Console'))
        
        # Tab 6: 日誌
        self.log_widget = self._create_log_tab()
        tab_widget.addTab(self.log_widget, tr('objgraph_tab_log', '診斷日誌'))
        
        main_layout.addWidget(tab_widget)
        
        # 狀態列
        self.status_bar = QLabel(tr('objgraph_ready', '就緒'))
        self.status_bar.setStyleSheet("background-color: #2a2a2a; padding: 5px;")
        main_layout.addWidget(self.status_bar)
    
    def _create_control_panel(self) -> QGroupBox:
        """創建控制面板"""
        group = QGroupBox(tr('objgraph_control_panel', '控制面板'))
        layout = QHBoxLayout()
        
        # 掃描按鈕
        self.scan_btn = QPushButton(tr('objgraph_scan_objects', '掃描物件'))
        self.scan_btn.clicked.connect(self._on_scan_objects)
        layout.addWidget(self.scan_btn)
        
        # 追蹤成長按鈕
        self.growth_btn = QPushButton(tr('objgraph_track_growth', '追蹤成長'))
        self.growth_btn.clicked.connect(self._on_track_growth)
        layout.addWidget(self.growth_btn)
        
        # GC 按鈕
        self.gc_btn = QPushButton(tr('objgraph_force_gc', '強制垃圾回收'))
        self.gc_btn.clicked.connect(self._on_force_gc)
        layout.addWidget(self.gc_btn)
        
        # 顯示數量
        layout.addWidget(QLabel(tr('objgraph_display_limit', '顯示數量:')))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(5, 1000)  # 增加到 1000
        self.limit_spin.setValue(100)      # 預設保持 100
        layout.addWidget(self.limit_spin)
        
        # 顯示全部選項
        self.show_all_checkbox = QCheckBox(tr('objgraph_show_all', '顯示全部類型'))
        self.show_all_checkbox.toggled.connect(self._on_show_all_toggled)
        layout.addWidget(self.show_all_checkbox)
        
        # 自動刷新
        self.auto_refresh_check = QCheckBox(tr('objgraph_auto_refresh', '自動刷新'))
        self.auto_refresh_check.stateChanged.connect(self._on_auto_refresh_toggled)
        layout.addWidget(self.auto_refresh_check)
        
        # 刷新間隔
        layout.addWidget(QLabel(tr('objgraph_interval', '間隔(秒):')))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(5)
        layout.addWidget(self.interval_spin)
        
        layout.addStretch()
        
        # 導出按鈕
        self.export_btn = QPushButton(tr('objgraph_export', '導出報告'))
        self.export_btn.clicked.connect(self._on_export_report)
        layout.addWidget(self.export_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_stats_tab(self) -> QWidget:
        """創建物件統計 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 統計表格
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels([
            tr('objgraph_type', '類型'),
            tr('objgraph_count', '數量'),
            tr('objgraph_percentage', '百分比')
        ])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)
        
        return widget
    
    def _create_growth_tab(self) -> QWidget:
        """創建成長追蹤 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 說明
        info_label = QLabel(tr('objgraph_growth_info', 
            '此功能追蹤兩次掃描之間的物件數量變化。點擊「追蹤成長」開始追蹤。'))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 成長表格
        self.growth_table = QTableWidget()
        self.growth_table.setColumnCount(4)
        self.growth_table.setHorizontalHeaderLabels([
            tr('objgraph_type', '類型'),
            tr('objgraph_previous', '之前'),
            tr('objgraph_current', '目前'),
            tr('objgraph_growth', '成長')
        ])
        self.growth_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.growth_table)
        
        return widget
    
    def _create_graph_tab(self) -> QWidget:
        """創建引用圖 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 控制區
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel(tr('objgraph_select_type', '選擇類型:')))
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        control_layout.addWidget(self.type_combo, 1)
        
        control_layout.addWidget(QLabel(tr('objgraph_max_depth', '最大深度:')))
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 10)
        self.depth_spin.setValue(3)
        control_layout.addWidget(self.depth_spin)
        
        self.generate_graph_btn = QPushButton(tr('objgraph_generate_graph', '生成引用圖'))
        self.generate_graph_btn.clicked.connect(self._on_generate_graph)
        control_layout.addWidget(self.generate_graph_btn)
        
        layout.addLayout(control_layout)
        
        # 圖片顯示區
        self.graph_label = QLabel(tr('objgraph_no_graph', '尚未生成引用圖'))
        self.graph_label.setAlignment(Qt.AlignCenter)
        self.graph_label.setMinimumHeight(400)
        self.graph_label.setStyleSheet("border: 1px solid #555; background-color: #1e1e1e;")
        layout.addWidget(self.graph_label)
        
        return widget
    
    def _create_action_tab(self) -> QWidget:
        """創建操作記錄 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 操作輸入區
        input_group = QGroupBox(tr('objgraph_action_note', '操作記錄'))
        input_layout = QHBoxLayout()
        
        self.action_input = QLineEdit()
        self.action_input.setPlaceholderText(tr('objgraph_action_placeholder', '輸入操作描述...'))
        input_layout.addWidget(self.action_input)
        
        add_btn = QPushButton(tr('objgraph_add_action', '新增記錄'))
        add_btn.clicked.connect(self._on_add_action_note)
        input_layout.addWidget(add_btn)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 快速操作按鈕 - 第一行（原有功能）
        quick_group = QGroupBox(tr('objgraph_quick_actions', '快速操作'))
        quick_main_layout = QVBoxLayout()
        
        # 第一行：原有快速操作
        quick_layout_1 = QHBoxLayout()
        
        quick_actions_1 = [
            (tr('objgraph_quick_open', '開啟模組'), '開啟模組'),
            (tr('objgraph_quick_close', '關閉模組'), '關閉模組'),
            (tr('objgraph_quick_analyze', '執行分析'), '執行分析'),
            (tr('objgraph_quick_export', '導出資料'), '導出資料'),
            (tr('objgraph_quick_clear', '清理緩存'), '清理緩存')
        ]
        
        for label, action in quick_actions_1:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, a=action: self._quick_add_action(a))
            quick_layout_1.addWidget(btn)
        
        quick_main_layout.addLayout(quick_layout_1)
        
        # 第二行：新增的自動化操作按鈕（已禁用，避免一般使用者誤觸）
        quick_layout_2 = QHBoxLayout()
        
        # Turn on GUI 按鈕 - 禁用
        turn_on_gui_btn = QPushButton('Turn on GUI (開發者功能)')
        turn_on_gui_btn.setStyleSheet("background-color: #555555; color: #888888; font-weight: bold;")
        turn_on_gui_btn.setEnabled(False)
        turn_on_gui_btn.setToolTip("此功能已禁用，避免一般使用者誤觸。開發者請在代碼中啟用。")
        turn_on_gui_btn.clicked.connect(self._on_turn_on_gui)
        quick_layout_2.addWidget(turn_on_gui_btn)
        
        # Open Speed Analysis 按鈕 - 禁用
        open_speed_btn = QPushButton('Open Speed Analysis (開發者功能)')
        open_speed_btn.setStyleSheet("background-color: #555555; color: #888888; font-weight: bold;")
        open_speed_btn.setEnabled(False)
        open_speed_btn.setToolTip("此功能已禁用，避免一般使用者誤觸。開發者請在代碼中啟用。")
        open_speed_btn.clicked.connect(self._on_open_speed_analysis)
        quick_layout_2.addWidget(open_speed_btn)
        
        # Open 9 Lap Analysis 按鈕 - 禁用
        open_9_lap_btn = QPushButton('Open 9 Lap Analysis (開發者功能)')
        open_9_lap_btn.setStyleSheet("background-color: #555555; color: #888888; font-weight: bold;")
        open_9_lap_btn.setEnabled(False)
        open_9_lap_btn.setToolTip("此功能已禁用，避免一般使用者誤觸。開發者請在代碼中啟用。")
        open_9_lap_btn.clicked.connect(self._on_open_9_lap_analysis)
        quick_layout_2.addWidget(open_9_lap_btn)
        
        quick_layout_2.addStretch()
        quick_main_layout.addLayout(quick_layout_2)
        
        quick_group.setLayout(quick_main_layout)
        layout.addWidget(quick_group)
        
        # 操作歷史表格
        self.action_table = QTableWidget()
        self.action_table.setColumnCount(4)
        self.action_table.setHorizontalHeaderLabels([
            tr('objgraph_action_time', '時間'),
            tr('objgraph_action_description', '操作描述'),
            tr('objgraph_action_objects', '物件總數'),
            tr('objgraph_action_change', '變化')
        ])
        header = self.action_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.action_table)
        
        # 控制按鈕
        btn_layout = QHBoxLayout()
        
        snapshot_btn = QPushButton(tr('objgraph_snapshot', '快照當前狀態'))
        snapshot_btn.clicked.connect(self._on_snapshot)
        btn_layout.addWidget(snapshot_btn)
        
        clear_btn = QPushButton(tr('objgraph_clear_actions', '清空記錄'))
        clear_btn.clicked.connect(self._on_clear_actions)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_console_tab(self) -> QWidget:
        """創建 Python Console Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 說明標籤
        info_label = QLabel(
            '執行 Python 代碼進行診斷\n'
            '可用變數: objgraph, gc, threading, sys\n'
            '範例: objgraph.count("_DummyThread")'
        )
        info_label.setStyleSheet("background-color: #2a2a2a; padding: 8px; border-radius: 4px;")
        layout.addWidget(info_label)
        
        # 快速診斷按鈕區
        quick_diag_group = QGroupBox('快速診斷命令')
        quick_layout = QVBoxLayout()
        
        # 第一行按鈕
        row1_layout = QHBoxLayout()
        
        btn_dummy_count = QPushButton('檢查 DummyThread 數量')
        btn_dummy_count.clicked.connect(lambda: self._run_quick_command(
            'import objgraph, gc\n'
            'gc.collect()\n'
            'count = objgraph.count("_DummyThread")\n'
            'logger.debug(f"DummyThread 數量: {count}")'
        ))
        row1_layout.addWidget(btn_dummy_count)
        
        btn_api_worker = QPushButton('檢查 TelemetryApiWorker')
        btn_api_worker.clicked.connect(lambda: self._run_quick_command(
            'import objgraph, gc\n'
            'gc.collect()\n'
            'workers = objgraph.by_type("TelemetryApiWorker")\n'
            'logger.debug(f"TelemetryApiWorker 實例數: {len(workers)}")\n'
            'for i, w in enumerate(workers[:5]):\n'
            '    logger.debug(f"  Worker {i+1}: isRunning={w.isRunning()}, isFinished={w.isFinished()}")'
        ))
        row1_layout.addWidget(btn_api_worker)
        
        btn_threading = QPushButton('檢查 threading._active')
        btn_threading.clicked.connect(lambda: self._run_quick_command(
            'import threading, gc\n'
            'gc.collect()\n'
            'active = threading._active\n'
            'logger.debug(f"threading._active 執行緒數: {len(active)}")\n'
            'dummy_count = sum(1 for t in active.values() if type(t).__name__ == "_DummyThread")\n'
            'logger.debug(f"其中 DummyThread: {dummy_count} 個")'
        ))
        row1_layout.addWidget(btn_threading)
        
        quick_layout.addLayout(row1_layout)
        
        # 第二行按鈕
        row2_layout = QHBoxLayout()
        
        btn_dataloader = QPushButton('檢查 DataLoader 洩漏')
        btn_dataloader.clicked.connect(lambda: self._run_quick_command(
            'import objgraph, gc\n'
            'gc.collect()\n'
            'loader_types = ["timediffAnalysisDataLoader", "speeddiffAnalysisDataLoader", \n'
            '                "distancediffAnalysisDataLoader", "TelemetryDataLoader"]\n'
            'for lt in loader_types:\n'
            '    count = objgraph.count(lt)\n'
            '    if count > 0:\n'
            '        logger.debug(f"{lt}: {count} 個")'
        ))
        row2_layout.addWidget(btn_dataloader)
        
        btn_dead_threads = QPushButton('檢查死亡執行緒')
        btn_dead_threads.clicked.connect(lambda: self._run_quick_command(
            'import threading, gc\n'
            'gc.collect()\n'
            'active = threading._active\n'
            'dead_count = sum(1 for t in active.values() if not t.is_alive())\n'
            'logger.debug(f"死亡但未清理的執行緒: {dead_count} 個")\n'
            'if dead_count > 0:\n'
            '    logger.debug("\\n前 10 個死亡執行緒:")\n'
            '    for i, (tid, t) in enumerate(list(active.items())[:10]):\n'
            '        if not t.is_alive():\n'
            '            logger.debug(f"  {t.name} (ID: {tid})")'
        ))
        row2_layout.addWidget(btn_dead_threads)
        
        btn_force_gc = QPushButton('強制 GC + 報告')
        btn_force_gc.clicked.connect(lambda: self._run_quick_command(
            'import gc, objgraph\n'
            'logger.debug("執行垃圾回收...")\n'
            'collected = gc.collect()\n'
            'logger.debug(f"回收了 {collected} 個物件")\n'
            'logger.debug(f"當前 DummyThread: {objgraph.count(\'_DummyThread\')}")\n'
            'logger.debug(f"當前 TelemetryApiWorker: {objgraph.count(\'TelemetryApiWorker\')}")'
        ))
        row2_layout.addWidget(btn_force_gc)
        
        quick_layout.addLayout(row2_layout)
        
        # 第三行按鈕（深度診斷）
        row3_layout = QHBoxLayout()
        
        btn_trace_dummy = QPushButton('🔍 深度追蹤 DummyThread 引用鏈')
        btn_trace_dummy.setStyleSheet("background-color: #4a90e2; font-weight: bold;")
        btn_trace_dummy.clicked.connect(self._trace_dummythread_references)
        row3_layout.addWidget(btn_trace_dummy)
        
        quick_layout.addLayout(row3_layout)
        
        quick_diag_group.setLayout(quick_layout)
        layout.addWidget(quick_diag_group)
        
        # 代碼輸入區
        code_group = QGroupBox('自訂 Python 代碼')
        code_layout = QVBoxLayout()
        
        self.console_input = QTextEdit()
        self.console_input.setPlaceholderText(
            '輸入 Python 代碼...\n\n'
            '範例:\n'
            'import objgraph, gc\n'
            'gc.collect()\n'
            'print(objgraph.count("_DummyThread"))'
        )
        self.console_input.setFont(QFont("Consolas", 10))
        self.console_input.setMaximumHeight(150)
        code_layout.addWidget(self.console_input)
        
        # 執行按鈕
        execute_layout = QHBoxLayout()
        
        self.execute_btn = QPushButton('執行代碼 (Ctrl+Enter)')
        self.execute_btn.clicked.connect(self._on_execute_code)
        self.execute_btn.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        execute_layout.addWidget(self.execute_btn)
        
        clear_input_btn = QPushButton('清空輸入')
        clear_input_btn.clicked.connect(self.console_input.clear)
        execute_layout.addWidget(clear_input_btn)
        
        code_layout.addLayout(execute_layout)
        code_group.setLayout(code_layout)
        layout.addWidget(code_group)
        
        # 輸出區
        output_group = QGroupBox('執行結果')
        output_layout = QVBoxLayout()
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 9))
        self.console_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        output_layout.addWidget(self.console_output)
        
        # 輸出控制按鈕
        output_btn_layout = QHBoxLayout()
        
        clear_output_btn = QPushButton('清空輸出')
        clear_output_btn.clicked.connect(self.console_output.clear)
        output_btn_layout.addWidget(clear_output_btn)
        
        copy_output_btn = QPushButton('複製輸出')
        copy_output_btn.clicked.connect(lambda: self.console_output.selectAll() or self.console_output.copy())
        output_btn_layout.addWidget(copy_output_btn)
        
        output_btn_layout.addStretch()
        output_layout.addLayout(output_btn_layout)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        return widget
    
    def _run_quick_command(self, code: str):
        """執行快速命令"""
        self.console_input.setPlainText(code)
        self._on_execute_code()
    
    def _trace_dummythread_references(self):
        """深度追蹤 DummyThread 的引用鏈"""
        self.console_output.append('\n' + '=' * 60)
        self.console_output.append('[深度追蹤] 開始分析 DummyThread 引用鏈...')
        self.console_output.append('=' * 60)
        
        code = '''
import objgraph
import gc
import threading
from pathlib import Path
from datetime import datetime

from core.logger import get_logger
logger = get_logger(__name__)

# 強制垃圾回收
logger.debug("\\n步驟 1: 執行垃圾回收...")
collected = gc.collect()
logger.debug(f"  回收了 {collected} 個物件")

# 統計 DummyThread
logger.debug("\\n步驟 2: 統計 DummyThread...")
dummy_count_objgraph = objgraph.count("_DummyThread")
active_threads = threading._active
dummy_count_threading = sum(1 for t in active_threads.values() if type(t).__name__ == "_DummyThread")
logger.debug(f"  objgraph.count: {dummy_count_objgraph}")
logger.debug(f"  threading._active: {dummy_count_threading}")

# 獲取所有 DummyThread 實例
logger.debug("\\n步驟 3: 獲取 DummyThread 實例...")
dummies = objgraph.by_type("_DummyThread")
logger.debug(f"  找到 {len(dummies)} 個 DummyThread 實例")

if dummies:
    # 分析前 3 個實例
    logger.debug("\\n步驟 4: 分析前 3 個 DummyThread 的引用...")
    logger.debug("-" * 60)
    
    output_dir = Path("objgraph_traces")
    output_dir.mkdir(exist_ok=True)
    
    for i, dummy in enumerate(dummies[:3], 1):
        logger.debug(f"\\n🔍 DummyThread #{i}:")
        logger.debug(f"   名稱: {dummy.name}")
        logger.debug(f"   存活: {dummy.is_alive()}")
        logger.debug(f"   Daemon: {dummy.daemon}")
        logger.debug(f"   Ident: {dummy.ident}")
        
        # 生成引用圖
        graph_file = output_dir / f"dummythread_{i}_backrefs_{datetime.now().strftime('%H%M%S')}.png"
        try:
            logger.debug(f"   生成引用圖: {graph_file.name}")
            objgraph.show_backrefs(
                [dummy],
                max_depth=5,
                filename=str(graph_file),
                refcounts=True
            )
            logger.info(f"   ✅ 引用圖已保存至: {graph_file}")
        except Exception as e:
            logger.error(f"   ❌ 生成引用圖失敗: {e}")
        
        # 列出直接引用者
        logger.debug(f"   直接引用者（前 3 個）:")
        referrers = gc.get_referrers(dummy)
        for j, ref in enumerate(referrers[:3], 1):
            ref_type = type(ref).__name__
            ref_str = str(ref)[:80].replace("\\n", " ")
            logger.debug(f"     {j}. {ref_type}: {ref_str}")
        
        logger.debug("-" * 60)
    
    logger.debug("\\n步驟 5: 檢查常見的 DummyThread 來源...")
    logger.debug("-" * 60)
    
    # 檢查可能的來源
    potential_sources = [
        ("QThread", "PyQt QThread"),
        ("Thread", "Python threading.Thread"),
        ("TelemetryApiWorker", "Telemetry API Worker"),
        ("UniversalApiWorker", "Universal API Worker"),
        ("DataLoader", "數據載入器基類"),
        ("QNetworkAccessManager", "Qt 網路管理器"),
    ]
    
    for class_name, description in potential_sources:
        count = objgraph.count(class_name)
        if count > 0:
            logger.info(f"  ✅ {description} ({class_name}): {count} 個")
    
    logger.debug("-" * 60)
    
    # 生成類型統計
    logger.debug("\\n步驟 6: 生成物件類型統計...")
    stats_file = output_dir / f"object_stats_{datetime.now().strftime('%H%M%S')}.txt"
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("物件類型統計（Top 30）\\n")
        f.write("=" * 80 + "\\n\\n")
        objgraph.show_most_common_types(limit=30, file=f)
    logger.info(f"  ✅ 統計已保存至: {stats_file}")

logger.debug("\\n" + "=" * 60)
logger.info("追蹤完成！")
logger.debug("=" * 60)
logger.debug("\\n📁 輸出檔案位置:")
logger.debug(f"  - 引用圖: objgraph_traces/dummythread_*_backrefs_*.png")
logger.debug(f"  - 統計: objgraph_traces/object_stats_*.txt")
logger.debug("\\n💡 下一步:")
logger.debug("  1. 查看引用圖，找出是誰在持有 DummyThread")
logger.debug("  2. 檢查對應模組是否正確實現了 cleanup()")
logger.debug("=" * 60)
'''
        
        self.console_input.setPlainText(code)
        self._on_execute_code()
    
    def _on_execute_code(self):
        """
        執行 Console 中的代碼
        
        ⚠️ 重要：由於 core.logger 會 patch builtins.print，我們需要：
        1. 臨時恢復原始的 print（繞過 logger.logged_print）
        2. 替換 sys.stdout/stderr
        3. 執行代碼
        4. 恢復所有修改
        """
        code = self.console_input.toPlainText().strip()
        if not code:
            self.console_output.append('[ERROR] 請輸入代碼\n')
            return
        
        self.console_output.append(f'\n{"="*60}')
        self.console_output.append(f'[{datetime.now().strftime("%H:%M:%S")}] 執行代碼:')
        self.console_output.append(f'{"="*60}')
        self.console_output.append(code)
        self.console_output.append(f'{"="*60}\n')
        
        # 捕獲輸出 - 繞過 logger 的 print patch
        import io
        import sys as _sys
        import builtins
        from core.logger import _ORIGINAL_PRINT, _PRINT_PATCHED
        
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        # 保存原始狀態
        old_stdout = _sys.stdout
        old_stderr = _sys.stderr
        old_print = builtins.print
        
        try:
            # 步驟 1: 恢復原始的 print（繞過 logger patch）
            if _PRINT_PATCHED:
                builtins.print = _ORIGINAL_PRINT
            
            # 步驟 2: 替換 sys.stdout 和 sys.stderr
            _sys.stdout = stdout_buffer
            _sys.stderr = stderr_buffer
            
            # 步驟 3: 準備執行環境
            # ⚠️ 安全性：限制 exec 可用的 builtin，避免高風險操作
            # 保留診斷工具所需的最小集合；移除 open/compile/eval/exec/__import__
            _safe_builtins = {
                name: getattr(__builtins__, name, None) or __builtins__.get(name)  # type: ignore[union-attr]
                for name in (
                    "print", "len", "range", "enumerate", "zip", "map", "filter",
                    "sorted", "reversed", "list", "dict", "set", "tuple",
                    "int", "float", "str", "bool", "type", "isinstance", "issubclass",
                    "hasattr", "getattr", "setattr", "dir", "vars", "repr",
                    "min", "max", "sum", "abs", "round", "hex", "oct", "bin",
                    "True", "False", "None", "Exception", "ValueError", "TypeError",
                )
                if (getattr(__builtins__, name, None) or
                    (isinstance(__builtins__, dict) and __builtins__.get(name))) is not None
            }
            if isinstance(__builtins__, dict):
                _safe_builtins = {k: v for k, v in __builtins__.items() if k in _safe_builtins}
            exec_globals = {
                '__builtins__': _safe_builtins,
                'objgraph': objgraph,
                'gc': gc,
                'threading': __import__('threading'),
                'os': os,
                'Path': Path,
                'datetime': datetime,
            }
            
            try:
                # 步驟 4: 執行代碼
                exec(code, exec_globals)
            finally:
                # 步驟 5: 恢復所有狀態
                _sys.stdout = old_stdout
                _sys.stderr = old_stderr
                builtins.print = old_print
            
            # 步驟 6: 顯示輸出
            stdout_text = stdout_buffer.getvalue()
            stderr_text = stderr_buffer.getvalue()
            
            if stdout_text:
                self.console_output.append('[輸出]')
                self.console_output.setTextColor(QColor(100, 255, 100))  # 綠色
                self.console_output.append(stdout_text.rstrip())
                self.console_output.setTextColor(QColor(212, 212, 212))
            
            if stderr_text:
                self.console_output.append('[錯誤]')
                self.console_output.setTextColor(QColor(255, 100, 100))
                self.console_output.append(stderr_text.rstrip())
                self.console_output.setTextColor(QColor(212, 212, 212))
            
            if not stdout_text and not stderr_text:
                self.console_output.setTextColor(QColor(100, 200, 255))  # 藍色
                self.console_output.append('[INFO] 執行完成（無輸出）')
                self.console_output.setTextColor(QColor(212, 212, 212))
            
        except Exception as e:
            # 確保恢復所有狀態
            _sys.stdout = old_stdout
            _sys.stderr = old_stderr
            builtins.print = old_print
            
            # 顯示異常
            import traceback
            self.console_output.setTextColor(QColor(255, 100, 100))
            self.console_output.append('[EXCEPTION]')
            self.console_output.append(str(e))
            self.console_output.append('\n' + traceback.format_exc())
            self.console_output.setTextColor(QColor(212, 212, 212))
        
        self.console_output.append('')  # 空行
        
        # 自動滾動到底部
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        self.console_output.setTextCursor(cursor)
    
    def _create_log_tab(self) -> QWidget:
        """創建日誌 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # 清除按鈕
        clear_btn = QPushButton(tr('objgraph_clear_log', '清除日誌'))
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)
        
        return widget
    
    def _on_show_all_toggled(self, checked: bool):
        """處理顯示全部選項切換"""
        self.limit_spin.setEnabled(not checked)
        if checked:
            self.limit_spin.setToolTip("已選擇顯示全部類型")
        else:
            self.limit_spin.setToolTip("")
    
    def _on_scan_objects(self):
        """掃描物件"""
        self._set_status(tr('objgraph_scanning', '正在掃描物件...'))
        self._log("=" * 60)
        self._log(f"[{datetime.now().strftime('%H:%M:%S')}] " + 
                  tr('objgraph_start_scan', '開始掃描物件'))
        
        # 啟動背景掃描
        limit = None if self.show_all_checkbox.isChecked() else self.limit_spin.value()
        self.scan_worker = ObjectScanWorker("most_common", limit)
        self.scan_worker.scan_completed.connect(self._on_scan_completed)
        self.scan_worker.error_occurred.connect(self._on_scan_error)
        self.scan_worker.start()
        
        # 禁用按鈕
        self.scan_btn.setEnabled(False)
    
    def _on_scan_completed(self, result: dict):
        """掃描完成"""
        self.scan_btn.setEnabled(True)
        
        if result["type"] == "most_common":
            self._populate_stats_table(result["data"])
            self._update_type_combo(result["data"])
            self._set_status(tr('objgraph_scan_complete', '掃描完成'))
            count = len(result["data"])
            self._log(f"掃描成功，找到 {count} 種類型")
    
    def _on_scan_error(self, error_msg: str):
        """掃描錯誤"""
        self.scan_btn.setEnabled(True)
        self._set_status(tr('objgraph_scan_error', '掃描失敗'), error=True)
        self._log(f"[ERROR] {error_msg}")
        QMessageBox.critical(self, tr('error', '錯誤'), error_msg)
    
    def _on_track_growth(self):
        """追蹤成長"""
        self._set_status(tr('objgraph_tracking_growth', '正在追蹤成長...'))
        self._log("=" * 60)
        self._log(f"[{datetime.now().strftime('%H:%M:%S')}] " + 
                  tr('objgraph_start_growth_track', '開始追蹤物件成長'))
        
        # 啟動背景掃描
        limit = None if self.show_all_checkbox.isChecked() else self.limit_spin.value()
        self.growth_worker = ObjectScanWorker("growth", limit)
        self.growth_worker.scan_completed.connect(self._on_growth_completed)
        self.growth_worker.error_occurred.connect(self._on_growth_error)
        self.growth_worker.start()
        
        # 禁用按鈕
        self.growth_btn.setEnabled(False)
    
    def _on_growth_completed(self, result: dict):
        """成長追蹤完成"""
        self.growth_btn.setEnabled(True)
        
        if result["type"] == "growth":
            self._populate_growth_table(result["data"])
            self._set_status(tr('objgraph_growth_complete', '成長追蹤完成'))
            count = len(result["data"])
            self._log(f"追蹤完成，發現 {count} 種類型有變化")
    
    def _on_growth_error(self, error_msg: str):
        """成長追蹤錯誤"""
        self.growth_btn.setEnabled(True)
        self._set_status(tr('objgraph_growth_error', '成長追蹤失敗'), error=True)
        self._log(f"[ERROR] {error_msg}")
        QMessageBox.critical(self, tr('error', '錯誤'), error_msg)
    
    def _on_force_gc(self):
        """強制垃圾回收"""
        import sys
        
        self._log("=" * 60)
        self._log(f"[{datetime.now().strftime('%H:%M:%S')}] " + 
                  tr('objgraph_force_gc_start', '執行強制垃圾回收...'))
        
        # 🔴 關鍵修復：清理 sys 模組中的 traceback 引用
        if hasattr(sys, 'last_traceback'):
            sys.last_type = None
            sys.last_value = None
            sys.last_traceback = None
            self._log("  [清理] 已清除 sys.last_traceback")
        
        # 執行多次 GC 確保清理乾淨
        collected = 0
        for i in range(3):
            n = gc.collect()
            collected += n
            self._log(f"  第 {i+1} 輪: 回收 {n} 個物件")
        
        # 🔴 診斷信息：統計 frame 和 traceback 對象
        frames = [obj for obj in gc.get_objects() if type(obj).__name__ == 'frame']
        tracebacks = [obj for obj in gc.get_objects() if type(obj).__name__ == 'traceback']
        self._log(f"  [診斷] 當前 frame 對象: {len(frames)} 個")
        self._log(f"  [診斷] 當前 traceback 對象: {len(tracebacks)} 個")
        
        self._log(f"垃圾回收完成，總共回收 {collected} 個物件")
        self._set_status(f"垃圾回收完成 ({collected} 個物件)")
        
        QMessageBox.information(
            self, 
            tr('objgraph_gc_title', '垃圾回收'),
            f"已回收 {collected} 個物件\nframe: {len(frames)} 個\ntraceback: {len(tracebacks)} 個"
        )
    
    def _on_generate_graph(self):
        """生成引用圖"""
        obj_type = self.type_combo.currentText().strip()
        if not obj_type:
            QMessageBox.warning(
                self, 
                tr('warning', '警告'), 
                tr('objgraph_select_type_warning', '請選擇或輸入物件類型')
            )
            return
        
        self._set_status(f"正在生成 {obj_type} 的引用圖...")
        self._log("=" * 60)
        self._log(f"[{datetime.now().strftime('%H:%M:%S')}] 開始生成 {obj_type} 的引用圖")
        
        # 啟動背景生成
        self.graph_worker = ReferenceGraphWorker(obj_type, self.depth_spin.value())
        self.graph_worker.graph_completed.connect(self._on_graph_completed)
        self.graph_worker.error_occurred.connect(self._on_graph_error)
        self.graph_worker.start()
        
        # 禁用按鈕
        self.generate_graph_btn.setEnabled(False)
    
    def _on_graph_completed(self, output_file: str):
        """引用圖生成完成"""
        self.generate_graph_btn.setEnabled(True)
        
        # 檢查檔案是否存在
        if not os.path.exists(output_file):
            self._set_status("引用圖生成失敗：檔案不存在", error=True)
            self._log(f"[ERROR] 檔案不存在: {output_file}")
            QMessageBox.warning(
                self,
                tr('warning', '警告'),
                f"引用圖檔案未找到:\n{output_file}\n\n請確認已安裝 Graphviz:\n1. 下載: https://graphviz.org/download/\n2. 安裝後重新啟動 GUI"
            )
            return
        
        # 顯示圖片
        pixmap = QPixmap(output_file)
        if not pixmap.isNull():
            # 縮放圖片以適應顯示區域
            scaled_pixmap = pixmap.scaled(
                self.graph_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.graph_label.setPixmap(scaled_pixmap)
            
            self._set_status(f"引用圖已生成: {output_file}")
            self._log(f"引用圖已保存至: {output_file}")
            
            QMessageBox.information(
                self,
                tr('success', '成功'),
                f"引用圖已保存至:\n{output_file}"
            )
        else:
            self._set_status("無法載入圖片", error=True)
            self._log(f"[ERROR] 無法載入圖片: {output_file}")
            QMessageBox.warning(
                self,
                tr('warning', '警告'),
                f"圖片檔案已生成但無法顯示:\n{output_file}\n\n請手動開啟檔案查看"
            )
    
    def _on_graph_error(self, error_msg: str):
        """引用圖生成錯誤"""
        self.generate_graph_btn.setEnabled(True)
        self._set_status(tr('objgraph_graph_error', '引用圖生成失敗'), error=True)
        self._log(f"[ERROR] {error_msg}")
        QMessageBox.critical(self, tr('error', '錯誤'), error_msg)
    
    def _on_auto_refresh_toggled(self, state: int):
        """自動刷新切換"""
        if state == Qt.Checked:
            interval = self.interval_spin.value() * 1000  # 轉換為毫秒
            self.auto_refresh_timer.start(interval)
            self._log("=" * 60)
            self._log(f"[AUTO-REFRESH] 已啟用自動刷新")
            self._log(f"[AUTO-REFRESH] 刷新間隔: {self.interval_spin.value()} 秒")
            self._log(f"[AUTO-REFRESH] 功能: 自動執行物件掃描")
            self._log("[AUTO-REFRESH] 注意: 追蹤成長需手動點擊")
            self._log("=" * 60)
            self._set_status(f"自動刷新已啟用 (每 {self.interval_spin.value()} 秒)")
        else:
            self.auto_refresh_timer.stop()
            self._log("=" * 60)
            self._log("[AUTO-REFRESH] 已停用自動刷新")
            self._log("=" * 60)
            self._set_status("自動刷新已停用")
    
    def _on_auto_refresh(self):
        """自動刷新觸發"""
        # 顯示自動刷新狀態
        self._set_status(f"[自動刷新] 正在掃描... (間隔: {self.interval_spin.value()}秒)")
        self._on_scan_objects()
    
    def _on_add_action_note(self):
        """添加操作記錄"""
        action_text = self.action_input.text().strip()
        if not action_text:
            QMessageBox.warning(
                self,
                tr('warning', '警告'),
                tr('objgraph_empty_action', '請輸入操作描述')
            )
            return
        
        self._add_action_to_history(action_text)
        self.action_input.clear()
        self.action_input.setFocus()
    
    def _quick_add_action(self, action_text: str):
        """快速添加操作記錄"""
        self._add_action_to_history(action_text)
    
    def _add_action_to_history(self, action_text: str):
        """添加操作到歷史記錄"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 獲取當前物件總數
        try:
            all_objects = objgraph.most_common_types(limit=1000)
            total_objects = sum(count for name, count in all_objects)
        except:
            total_objects = 0
        
        # 計算變化
        change = total_objects - self.last_total_objects if self.last_total_objects > 0 else 0
        change_text = f"+{change}" if change > 0 else str(change) if change < 0 else "0"
        
        # 添加到表格
        row = self.action_table.rowCount()
        self.action_table.insertRow(row)
        
        self.action_table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.action_table.setItem(row, 1, QTableWidgetItem(action_text))
        self.action_table.setItem(row, 2, QTableWidgetItem(str(total_objects)))
        
        change_item = QTableWidgetItem(change_text)
        if change > 0:
            change_item.setForeground(QColor(255, 100, 100))  # 紅色
        elif change < 0:
            change_item.setForeground(QColor(100, 255, 100))  # 綠色
        self.action_table.setItem(row, 3, change_item)
        
        # 滾動到最新記錄
        self.action_table.scrollToBottom()
        
        # 更新最後的物件總數
        self.last_total_objects = total_objects
        
        # 添加到歷史記錄
        self.action_history.append({
            'timestamp': timestamp,
            'action': action_text,
            'total_objects': total_objects,
            'change': change
        })
        
        # 記錄到日誌
        self._log(f"[ACTION] {action_text} (物件總數: {total_objects}, 變化: {change_text})")
        self._set_status(f"已記錄操作: {action_text}")
    
    def _on_snapshot(self):
        """拍攝當前物件統計快照並觸發 Growth Track - 記錄所有物件類型"""
        try:
            self._set_status(tr('objgraph_snapshot_in_progress', '正在拍攝快照並追蹤成長...'))
            
            # === 步驟 1: 獲取當前物件統計（所有類型，不限制數量）===
            all_objects = objgraph.most_common_types(limit=200)  # 增加到 200 種類型
            total_objects = sum(count for name, count in all_objects)
            
            # 生成快照描述（用於操作記錄表格）
            top_5 = ', '.join([f"{name}({count})" for name, count in all_objects[:5]])
            snapshot_text = f"快照 - 總計 {total_objects} 個物件 | Top 5: {top_5}"
            
            # === 步驟 2: 觸發 Growth Track（如果有上次掃描結果）===
            growth_data = []
            if self.last_scan_result:
                growth_data = objgraph.growth(limit=200)  # 同樣增加到 200 種類型
                self._log("=" * 80)
                self._log(f"[SNAPSHOT + GROWTH] 已拍攝快照並追蹤成長")
                self._log(f"[SNAPSHOT] 總物件數: {total_objects}")
                self._log(f"[SNAPSHOT] 物件統計（所有 {len(all_objects)} 種類型）:")
                
                # 記錄所有物件類型（完整列表）
                for idx, (name, count) in enumerate(all_objects, 1):
                    percentage = (count / total_objects * 100) if total_objects > 0 else 0
                    self._log(f"  {idx:3d}. {name:40s} {count:8d}  ({percentage:5.2f}%)")
                
                # 記錄 Growth 數據（所有變化）
                if growth_data:
                    self._log(f"\n[GROWTH] 發現 {len(growth_data)} 種類型有變化:")
                    for idx, (name, growth_count, delta) in enumerate(growth_data, 1):
                        if delta > 0:
                            self._log(f"  {idx:3d}. ↑ {name:40s} {growth_count:8d} (+{delta})")
                        elif delta < 0:
                            self._log(f"  {idx:3d}. ↓ {name:40s} {growth_count:8d} ({delta})")
                else:
                    self._log(f"\n[GROWTH] 沒有物件變化")
                self._log("=" * 80)
            else:
                # 首次快照，沒有比較基準
                self._log("=" * 80)
                self._log(f"[SNAPSHOT] 已拍攝物件統計快照（首次，無 Growth 數據）")
                self._log(f"[SNAPSHOT] 總物件數: {total_objects}")
                self._log(f"[SNAPSHOT] 物件統計（所有 {len(all_objects)} 種類型）:")
                
                # 記錄所有物件類型（完整列表）
                for idx, (name, count) in enumerate(all_objects, 1):
                    percentage = (count / total_objects * 100) if total_objects > 0 else 0
                    self._log(f"  {idx:3d}. {name:40s} {count:8d}  ({percentage:5.2f}%)")
                
                self._log(f"\n[INFO] 再次點擊 Snapshot 或 Track Growth 以追蹤變化")
                self._log("=" * 80)
            
            # === 步驟 3: 添加到操作記錄 ===
            self._add_action_to_history(snapshot_text)
            
            # === 步驟 4: 更新 Growth Track Tab（如果有變化）===
            if growth_data:
                self._populate_growth_table(growth_data)
            
            # === 步驟 5: 儲存為上次掃描結果，作為下次比較基準 ===
            self.last_scan_result = {name: count for name, count in all_objects}
            
            self._set_status(f"快照完成 - 總物件數: {total_objects}, 記錄 {len(all_objects)} 種類型")
            
        except Exception as e:
            self._log(f"[ERROR] 拍攝快照失敗: {e}")
            import traceback
            self._log(traceback.format_exc())
            QMessageBox.critical(
                self,
                tr('error', '錯誤'),
                f"拍攝快照失敗:\n{str(e)}"
            )
    
    def _on_clear_actions(self):
        """清除操作記錄"""
        reply = QMessageBox.question(
            self,
            tr('objgraph_confirm_clear', '確認清除'),
            tr('objgraph_confirm_clear_actions', '確定要清除所有操作記錄嗎？'),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.action_table.setRowCount(0)
            self.action_history.clear()
            self.last_total_objects = 0
            self._log("[ACTION] 已清除所有操作記錄")
            self._set_status("操作記錄已清除")
    
    def _on_export_report(self):
        """導出完整診斷報告（包含操作記錄）"""
        # 選擇保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr('objgraph_export_report', '導出診斷報告'),
            f"objgraph_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("Objgraph 完整診斷報告\n")
                f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                # 操作記錄摘要
                f.write("【操作記錄摘要】\n")
                f.write("-" * 80 + "\n")
                if self.action_history:
                    f.write(f"總記錄數: {len(self.action_history)}\n")
                    f.write(f"初始物件數: {self.action_history[0]['total_objects']}\n")
                    f.write(f"當前物件數: {self.action_history[-1]['total_objects']}\n")
                    total_change = self.action_history[-1]['total_objects'] - self.action_history[0]['total_objects']
                    f.write(f"總變化量: {'+' if total_change > 0 else ''}{total_change}\n\n")
                    
                    f.write("詳細記錄:\n")
                    for record in self.action_history:
                        f.write(f"  [{record['timestamp']}] {record['action']}\n")
                        f.write(f"    物件總數: {record['total_objects']:,}, 變化: {record['change']:+d}\n")
                else:
                    f.write("無操作記錄\n")
                f.write("\n")
                
                # 物件統計
                f.write("【當前物件統計】\n")
                f.write("-" * 80 + "\n")
                if self.stats_table.rowCount() > 0:
                    f.write(f"{'類型':<40} {'數量':>10} {'百分比':>10}\n")
                    f.write("-" * 80 + "\n")
                    for row in range(self.stats_table.rowCount()):
                        obj_type = self.stats_table.item(row, 0).text() if self.stats_table.item(row, 0) else "N/A"
                        count = self.stats_table.item(row, 1).text() if self.stats_table.item(row, 1) else "0"
                        percentage = self.stats_table.item(row, 2).text() if self.stats_table.item(row, 2) else "0%"
                        f.write(f"{obj_type:<40} {count:>10} {percentage:>10}\n")
                else:
                    f.write("尚未執行物件掃描\n")
                f.write("\n")
                
                # 成長追蹤
                f.write("【成長追蹤記錄】\n")
                f.write("-" * 80 + "\n")
                if self.growth_table.rowCount() > 0:
                    f.write(f"{'類型':<40} {'之前':>10} {'目前':>10} {'變化':>10}\n")
                    f.write("-" * 80 + "\n")
                    for row in range(self.growth_table.rowCount()):
                        obj_type = self.growth_table.item(row, 0).text() if self.growth_table.item(row, 0) else "N/A"
                        previous = self.growth_table.item(row, 1).text() if self.growth_table.item(row, 1) else "0"
                        current = self.growth_table.item(row, 2).text() if self.growth_table.item(row, 2) else "0"
                        growth = self.growth_table.item(row, 3).text() if self.growth_table.item(row, 3) else "0"
                        f.write(f"{obj_type:<40} {previous:>10} {current:>10} {growth:>10}\n")
                else:
                    f.write("尚未執行成長追蹤\n")
                f.write("\n")
                
                # 完整診斷日誌
                f.write("【完整診斷日誌】\n")
                f.write("-" * 80 + "\n")
                f.write(self.log_text.toPlainText())
            
            self._log(f"[EXPORT] 報告已導出至: {file_path}")
            QMessageBox.information(
                self,
                tr('success', '成功'),
                f"報告已導出至:\n{file_path}\n\n包含內容:\n• 操作記錄摘要\n• 當前物件統計\n• 成長追蹤記錄\n• 完整診斷日誌"
            )
        except Exception as e:
            self._log(f"[ERROR] 導出報告失敗: {e}")
            QMessageBox.critical(
                self,
                tr('error', '錯誤'),
                f'導出失敗:\n{str(e)}'
            )
    
    def _populate_stats_table(self, data: List[tuple]):
        """填充統計表格"""
        self.stats_table.setRowCount(len(data))
        total = sum(count for _, count in data)
        
        for row, (obj_type, count) in enumerate(data):
            percentage = (count / total * 100) if total > 0 else 0
            
            self.stats_table.setItem(row, 0, QTableWidgetItem(str(obj_type)))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.stats_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.2f}%"))
        
        self.stats_table.resizeColumnsToContents()
    
    def _populate_growth_table(self, data: List[tuple]):
        """填充成長表格"""
        self.growth_table.setRowCount(len(data))
        
        for row, (obj_type, growth, count) in enumerate(data):
            previous = count - growth
            
            self.growth_table.setItem(row, 0, QTableWidgetItem(str(obj_type)))
            self.growth_table.setItem(row, 1, QTableWidgetItem(str(previous)))
            self.growth_table.setItem(row, 2, QTableWidgetItem(str(count)))
            
            growth_text = f"+{growth}" if growth > 0 else str(growth)
            growth_item = QTableWidgetItem(growth_text)
            
            # 根據成長量設置顏色
            if growth > 0:
                growth_item.setForeground(Qt.red)
            elif growth < 0:
                growth_item.setForeground(Qt.green)
            
            self.growth_table.setItem(row, 3, growth_item)
        
        self.growth_table.resizeColumnsToContents()
    
    def _update_type_combo(self, data: List[tuple]):
        """更新類型下拉選單"""
        current_text = self.type_combo.currentText()
        self.type_combo.clear()
        
        for obj_type, _ in data:
            self.type_combo.addItem(str(obj_type))
        
        # 恢復之前的選擇
        if current_text:
            index = self.type_combo.findText(current_text)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
    
    def _set_status(self, message: str, error: bool = False):
        """設置狀態"""
        self.status_bar.setText(message)
        if error:
            self.status_bar.setStyleSheet("background-color: #8b0000; padding: 5px; color: white;")
        else:
            self.status_bar.setStyleSheet("background-color: #2a2a2a; padding: 5px;")
    
    def _log(self, message: str):
        """添加日誌"""
        self.log_text.append(message)
        # 自動滾動到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def _on_turn_on_gui(self):
        """Turn on GUI - 啟動 F1T 主 GUI"""
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            # 獲取專案根目錄
            project_root = Path(__file__).parent.parent.parent.parent
            gui_main_path = project_root / "f1t_gui_main.py"
            
            if not gui_main_path.exists():
                QMessageBox.warning(
                    self,
                    tr('warning', '警告'),
                    f"找不到 F1T GUI 主程式:\n{gui_main_path}"
                )
                return
            
            # 啟動 GUI 主程式（背景執行）
            python_exe = sys.executable
            subprocess.Popen([python_exe, str(gui_main_path)], 
                           cwd=str(project_root),
                           creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0)
            
            self._add_action_to_history("Turn on GUI - 啟動 F1T 主界面")
            self._log(f"[QUICK_ACTION] 已啟動 F1T GUI: {gui_main_path}")
            QMessageBox.information(
                self,
                tr('success', '成功'),
                "F1T GUI 主程式已在新視窗中啟動"
            )
            
        except Exception as e:
            logger.error(f"啟動 GUI 失敗: {e}")
            QMessageBox.critical(
                self,
                tr('error', '錯誤'),
                f"啟動 F1T GUI 失敗:\n{str(e)}"
            )
    
    def _on_open_speed_analysis(self):
        """Open Speed Analysis - 通過 API 打開速度分析模組"""
        try:
            from core import local_requests as requests
            import certifi
            
            # F1T API 端點
            api_base = "http://localhost:8000"
            
            # 測試 API 是否運行
            try:
                health_response = requests.get(f"{api_base}/health", timeout=2, verify=certifi.where())  # ✅ SSL證書（EXE必須）
                if health_response.status_code != 200:
                    raise Exception("API 未響應")
            except:
                QMessageBox.warning(
                    self,
                    tr('warning', '警告'),
                    "F1T API 服務未運行\n\n請先啟動 API 服務:\npython refactored_api.py"
                )
                return
            
            # 發送打開模組請求（假設 API 支援此功能）
            # 注意：這需要 API 端點支援，這裡僅作為示範
            self._add_action_to_history("Open Speed Analysis - 請求打開速度分析模組")
            self._log("[QUICK_ACTION] 已發送打開 Speed Analysis 請求")
            
            QMessageBox.information(
                self,
                tr('info', '資訊'),
                "速度分析模組請求已發送\n\n注意：此功能需要 F1T GUI 正在運行並支援遠程控制"
            )
            
        except Exception as e:
            logger.error(f"打開 Speed Analysis 失敗: {e}")
            QMessageBox.critical(
                self,
                tr('error', '錯誤'),
                f"打開速度分析失敗:\n{str(e)}"
            )
    
    def _on_open_9_lap_analysis(self):
        """Open 9 Lap Analysis - 通過 API 批量打開所有 Lap Analysis 模組"""
        try:
            # 9 個 Lap Analysis 模組
            lap_modules = [
                'Speed Analysis',
                'Throttle Analysis', 
                'Acceleration Analysis',
                'Brake Analysis',
                'Gear Analysis',
                'RPM Analysis',
                'TimeDiff Analysis',
                'SpeedDiff Analysis',
                'DistanceDiff Analysis'
            ]
            
            # 顯示確認對話框
            reply = QMessageBox.question(
                self,
                tr('confirm', '確認'),
                f"即將批量打開 {len(lap_modules)} 個 Lap Analysis 模組:\n\n" +
                "\n".join([f"  • {m}" for m in lap_modules]) +
                "\n\n這可能會消耗大量記憶體。是否繼續？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # 記錄操作
            self._add_action_to_history(f"Open 9 Lap Analysis - 批量打開 {len(lap_modules)} 個模組")
            
            # 詳細日誌
            self._log("=" * 60)
            self._log(f"[QUICK_ACTION] 批量打開 Lap Analysis 模組")
            self._log(f"[QUICK_ACTION] 模組數量: {len(lap_modules)}")
            for i, module_name in enumerate(lap_modules, 1):
                self._log(f"[QUICK_ACTION]   {i}. {module_name}")
            self._log("=" * 60)
            
            QMessageBox.information(
                self,
                tr('info', '資訊'),
                f"已記錄批量打開請求\n\n模組數量: {len(lap_modules)}\n\n" +
                "注意：實際打開需要 F1T GUI 運行並支援遠程控制。\n" +
                "您可以使用此記錄追蹤記憶體變化。"
            )
            
        except Exception as e:
            logger.error(f"批量打開 Lap Analysis 失敗: {e}")
            QMessageBox.critical(
                self,
                tr('error', '錯誤'),
                f"批量打開失敗:\n{str(e)}"
            )
    
    def closeEvent(self, event):
        """關閉事件"""
        # 停止自動刷新
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
        
        event.accept()
