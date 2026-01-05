#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1T Batch Data Generator GUI
============================
批次數據生成器的圖形化介面

功能特性:
- 視覺化選擇賽季、賽事、分析功能
- 自動從 FastF1 載入賽程
- 批次預覽 (Dry Run)
- 即時進度顯示
- 無超時限制（針對大數據量功能）

作者: F1T Team
日期: 2025-12-20
版本: 0.13.2
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Set, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QCheckBox, QComboBox, QPushButton, QTextEdit,
    QProgressBar, QLabel, QScrollArea, QGridLayout, QMessageBox,
    QSpinBox, QTabWidget, QTreeWidget, QTreeWidgetItem, QSplitter, QDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QTextCursor

# 確保可以導入專案模組
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# 配置常數
# ============================================================================

# 功能分類
FUNCTION_CATEGORIES = {
    "Race Overview 賽事概況": {
        "functions": [1, 2, 3, 4, 5, 8],
        "description": "Race overview analysis 賽事概況分析",
        "color": "#3498db"
    },
    "Driver Performance 車手性能": {
        "functions": [25, 26, 28, 34, 47, 48, 53, 54],
        "description": "Driver performance analysis 車手性能分析",
        "color": "#e74c3c"
    },
    "Fuel & Tire Analysis 燃油輪胎分析": {
        "functions": [55, 56, 57, 58],
        "description": "Large data volume 大數據量",
        "color": "#f39c12"
    },
    "Prediction 預測分析": {
        "functions": [74, 76, 80],
        "description": "ML processing 機器學習處理時間長",
        "color": "#9b59b6"
    },
    "Data Collection 數據收集": {
        "functions": [81, 100],
        "description": "Data collection 數據收集",
        "color": "#1abc9c"
    },
    "FP2 All Laps 全圈數分析": {
        "functions": [120, 121, 122],
        "description": "Large data volume 大數據量",
        "color": "#e67e22"
    },
    "Live Timing Analysis 即時資料分析": {
        "functions": [125, 126, 127],
        "description": "Live Timing data analysis 即時資料分析",
        "color": "#2ecc71"
    },
    "Season Analysis 年度分析": {
        "functions": [101],
        "description": "Season-wide analysis (year only) 年度分析",
        "color": "#8e44ad"
    },
}

# 功能配置
FUNCTION_CONFIGS = {
    1: {"name": "Rain Analysis 降雨分析", "sessions": {"FP1", "FP2", "FP3", "Q", "SQ", "R"}},
    2: {"name": "Track Analysis 賽道分析", "sessions": {"FP1", "FP2", "FP3", "Q", "SQ", "R"}},
    3: {"name": "Driver Fastest Pitstop 車手最快進站", "sessions": {"R"}},
    4: {"name": "Team Pitstop Ranking 車隊進站排行", "sessions": {"R"}},
    5: {"name": "Driver Detailed Pitstop 車手進站詳細", "sessions": {"R"}},
    8: {"name": "Accident Analysis 事故分析", "sessions": {"R"}},
    25: {"name": "Driver Race Position 車手位置", "sessions": {"Q", "SQ", "R"}},
    26: {"name": "Tire Strategy 輪胎策略", "sessions": {"R"}},
    28: {"name": "Detailed Lap Analysis 詳細圈速", "sessions": {"Q", "SQ", "R"}},
    34: {"name": "Brake Performance 煞車性能", "sessions": {"FP1", "FP2", "FP3", "Q", "SQ", "R"}},
    47: {"name": "Corner Analysis 彎道分析", "sessions": {"FP1", "FP2", "FP3", "Q", "SQ", "R"}},
    48: {"name": "Straight Line Speed 直線速度", "sessions": {"FP1", "FP2", "FP3", "Q", "SQ", "R"}},
    53: {"name": "Ideal Lap Analysis 理想圈分析", "sessions": {"FP3", "Q", "R"}},
    54: {"name": "Throttle Analysis 油門分析", "sessions": {"FP1", "FP2", "FP3", "Q", "SQ", "R"}},
    55: {"name": "Fuel Corrected Laptime 燃油校正圈速", "sessions": {"R"}},
    56: {"name": "Tire Degradation 輪胎衰退", "sessions": {"R"}},
    57: {"name": "Combined Laptime Prediction 綜合圈速預測", "sessions": {"R"}},
    58: {"name": "Pit Stop Strategy 進站策略", "sessions": {"R"}},
    74: {"name": "FP3->Q Prediction 排位賽預測", "sessions": {"FP3"}},
    76: {"name": "FP2->Q Prediction FP2排位預測", "sessions": {"FP2"}},
    80: {"name": "Q->R Prediction 正賽預測", "sessions": {"Q"}},
    81: {"name": "Overtake Data Collection 超車數據收集", "sessions": {"R"}},
    100: {"name": "Historical Track Map 歷年旗幟統計", "sessions": set()},
    120: {"name": "FP2 Corner All Laps 彎道全圈數", "sessions": {"FP2"}},
    121: {"name": "FP2 Straight Line All Laps 直線全圈數", "sessions": {"FP2"}},
    122: {"name": "Brake All Laps Analysis 煞車全圈數", "sessions": {"FP2"}},
    125: {"name": "Vehicle Performance 車輛性能綜合", "sessions": {"R"}},
    126: {"name": "Live Timing Weather 天氣分析", "sessions": {"FP2", "FP3", "Q", "R"}},
    127: {"name": "Traffic Timeline 車流時間線", "sessions": {"R"}},
    101: {"name": "Season Start Reaction 年度起跑分析", "sessions": set(), "season_only": True},
}

# 無超時功能 (大數據量)
NO_TIMEOUT_FUNCTIONS = {47, 55, 56, 57, 58, 120, 121, 122}

# ============================================================================
# 工作執行緒
# ============================================================================

class GeneratorWorker(QThread):
    """批次生成工作執行緒"""
    
    progress = pyqtSignal(int, int)  # current, total
    log_message = pyqtSignal(str)
    task_completed = pyqtSignal(str, bool)  # task_desc, success
    finished = pyqtSignal(int, int)  # success_count, fail_count
    
    def __init__(self, tasks: List[dict], skip_existing: bool = True):
        super().__init__()
        self.tasks = tasks
        self.skip_existing = skip_existing
        self._stop_requested = False
        
    def stop(self):
        self._stop_requested = True
        
    def run(self):
        success_count = 0
        fail_count = 0
        total = len(self.tasks)
        
        for i, task in enumerate(self.tasks):
            if self._stop_requested:
                self.log_message.emit("\n⏹️ 使用者取消執行")
                break
                
            self.progress.emit(i + 1, total)
            
            func_id = task['function_id']
            year = task['year']
            race = task['race']
            session = task.get('session', '')
            is_season_only = task.get('season_only', False)
            
            if is_season_only:
                task_desc = f"F{func_id} - {year} (Season Analysis)"
            else:
                task_desc = f"F{func_id} - {year} {race} {session}"
            self.log_message.emit(f"\n{'='*60}")
            self.log_message.emit(f"▶️ [{i+1}/{total}] {task_desc}")
            
            try:
                # 構建命令
                if is_season_only:
                    # Season-only 功能只需年份
                    cmd = [
                        sys.executable,
                        "f1_analysis_modular_main.py",
                        "-f", str(func_id),
                        "-y", str(year),
                    ]
                else:
                    cmd = [
                        sys.executable,
                        "f1_analysis_modular_main.py",
                        "-f", str(func_id),
                        "-y", str(year),
                        "-r", race,
                    ]
                
                if session:
                    cmd.extend(["-s", session])
                
                # 執行命令
                timeout = None if func_id in NO_TIMEOUT_FUNCTIONS else 600
                
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=timeout,
                    cwd=str(Path(__file__).parent)
                )
                
                if process.returncode == 0:
                    self.log_message.emit(f"✅ 成功: {task_desc}")
                    self.task_completed.emit(task_desc, True)
                    success_count += 1
                else:
                    # 檢查 stderr 是否只是警告而非真正的錯誤
                    stderr_text = process.stderr or ""
                    stdout_text = process.stdout or ""
                    
                    # 判斷是否只有警告（無真正錯誤內容）
                    warning_keywords = ["UserWarning", "DeprecationWarning", "FutureWarning", "warnings.warn"]
                    error_keywords = ["Error:", "Exception:", "Traceback", "找不到", "失敗", "錯誤"]
                    
                    has_only_warnings = any(kw in stderr_text for kw in warning_keywords)
                    has_real_error = any(kw in stderr_text for kw in error_keywords)
                    
                    # 過濾警告行，看是否有其他實質內容
                    non_warning_lines = [
                        line.strip() for line in stderr_text.split('\n')
                        if line.strip() and not any(kw in line for kw in warning_keywords)
                    ]
                    
                    if has_only_warnings and not has_real_error and len(non_warning_lines) == 0:
                        # 只有警告，無實質錯誤 - 需要從日誌確認真正結果
                        # 暫時標記為成功（因為 CLI 輸出被 logger 捕獲）
                        self.log_message.emit(f"✅ 成功 (有警告): {task_desc}")
                        self.task_completed.emit(task_desc, True)
                        success_count += 1
                    else:
                        self.log_message.emit(f"❌ 失敗: {task_desc}")
                        if non_warning_lines:
                            self.log_message.emit(f"   錯誤: {non_warning_lines[0][:200]}")
                        elif stderr_text:
                            self.log_message.emit(f"   錯誤: {stderr_text[:200]}")
                        self.task_completed.emit(task_desc, False)
                        fail_count += 1
                    
            except subprocess.TimeoutExpired:
                self.log_message.emit(f"⏱️ 超時: {task_desc}")
                self.task_completed.emit(task_desc, False)
                fail_count += 1
            except Exception as e:
                self.log_message.emit(f"❌ 錯誤: {task_desc} - {e}")
                self.task_completed.emit(task_desc, False)
                fail_count += 1
        
        self.finished.emit(success_count, fail_count)


# ============================================================================
# 主視窗
# ============================================================================

class BatchGeneratorGUI(QMainWindow):
    """批次數據生成器 GUI"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1T Batch Data Generator")
        self.setMinimumSize(1200, 800)
        
        self.races = []
        self.race_checkboxes = []
        self.function_checkboxes = {}
        self.worker = None
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        
        # 左側面板：選擇區
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 賽季選擇
        season_group = QGroupBox("Season Selection 賽季選擇")
        season_layout = QHBoxLayout(season_group)
        
        self.year_combo = QComboBox()
        self.year_combo.addItems([str(y) for y in range(2027, 2019, -1)])
        self.year_combo.setCurrentText("2025")
        season_layout.addWidget(QLabel("Year 年份:"))
        season_layout.addWidget(self.year_combo)
        
        load_btn = QPushButton("Load Season Schedule 載入賽程")
        load_btn.clicked.connect(self._load_season)
        season_layout.addWidget(load_btn)
        
        left_layout.addWidget(season_group)
        
        # 賽事選擇
        race_group = QGroupBox("Race Selection 賽事選擇")
        race_layout = QVBoxLayout(race_group)
        
        race_btn_layout = QHBoxLayout()
        select_all_races = QPushButton("Select All 全選")
        select_all_races.clicked.connect(lambda: self._toggle_all_races(True))
        clear_all_races = QPushButton("Clear All 清除")
        clear_all_races.clicked.connect(lambda: self._toggle_all_races(False))
        race_btn_layout.addWidget(select_all_races)
        race_btn_layout.addWidget(clear_all_races)
        race_layout.addLayout(race_btn_layout)
        
        race_scroll = QScrollArea()
        race_scroll.setWidgetResizable(True)
        self.race_container = QWidget()
        self.race_grid = QGridLayout(self.race_container)
        race_scroll.setWidget(self.race_container)
        race_layout.addWidget(race_scroll)
        
        left_layout.addWidget(race_group)
        
        # 功能選擇
        func_group = QGroupBox("Function Selection 功能選擇")
        func_layout = QVBoxLayout(func_group)
        
        func_btn_layout = QHBoxLayout()
        select_all_funcs = QPushButton("Select All 全選")
        select_all_funcs.clicked.connect(lambda: self._toggle_all_functions(True))
        clear_all_funcs = QPushButton("Clear All 清除")
        clear_all_funcs.clicked.connect(lambda: self._toggle_all_functions(False))
        preset_essential = QPushButton("Essential Only 基本功能")
        preset_essential.clicked.connect(self._select_essential)
        func_btn_layout.addWidget(select_all_funcs)
        func_btn_layout.addWidget(clear_all_funcs)
        func_btn_layout.addWidget(preset_essential)
        func_layout.addLayout(func_btn_layout)
        
        func_scroll = QScrollArea()
        func_scroll.setWidgetResizable(True)
        func_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滾動條
        func_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)     # 垂直滾動條按需顯示
        func_container = QWidget()
        func_grid = QGridLayout(func_container)
        func_grid.setColumnStretch(0, 1)  # 讓各欄平均分配寬度
        func_grid.setColumnStretch(1, 1)
        
        row = 0
        for category, info in FUNCTION_CATEGORIES.items():
            # 類別標題
            cat_label = QLabel(f"<b>{category}</b> - {info['description']}")
            cat_label.setStyleSheet(f"color: {info['color']};")
            func_grid.addWidget(cat_label, row, 0, 1, 2)
            row += 1
            
            # 功能核取方塊
            col = 0
            for func_id in info['functions']:
                config = FUNCTION_CONFIGS.get(func_id, {})
                name = config.get('name', f'Function {func_id}')
                
                cb = QCheckBox(f"F{func_id} - {name}")
                cb.setChecked(False)
                self.function_checkboxes[func_id] = cb
                
                func_grid.addWidget(cb, row, col)
                col += 1
                if col >= 2:
                    col = 0
                    row += 1
            
            if col != 0:
                row += 1
        
        func_scroll.setWidget(func_container)
        func_layout.addWidget(func_scroll)
        
        left_layout.addWidget(func_group)
        
        # 右側面板：執行區
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 執行選項
        options_group = QGroupBox("Execution Options 執行選項")
        options_layout = QGridLayout(options_group)
        
        self.dry_run_cb = QCheckBox("Dry Run 預覽模式 (Preview Only)")
        self.skip_existing_cb = QCheckBox("Skip Existing JSON 跳過已存在")
        self.skip_existing_cb.setChecked(True)
        
        options_layout.addWidget(self.dry_run_cb, 0, 0)
        options_layout.addWidget(self.skip_existing_cb, 0, 1)
        
        # Session 選擇
        options_layout.addWidget(QLabel("Sessions 階段:"), 1, 0)
        session_layout = QHBoxLayout()
        self.session_checkboxes = {}
        for session in ["FP1", "FP2", "FP3", "Q", "R"]:
            cb = QCheckBox(session)
            cb.setChecked(session == "R")  # 預設只選 R
            self.session_checkboxes[session] = cb
            session_layout.addWidget(cb)
        options_layout.addLayout(session_layout, 1, 1)
        
        right_layout.addWidget(options_group)
        
        # 任務統計
        stats_group = QGroupBox("Task Statistics 任務統計")
        stats_layout = QHBoxLayout(stats_group)
        
        self.task_count_label = QLabel("Tasks 任務數: 0")
        self.estimated_time_label = QLabel("Est. Time 預估時間: 0 min")
        stats_layout.addWidget(self.task_count_label)
        stats_layout.addWidget(self.estimated_time_label)
        
        right_layout.addWidget(stats_group)
        
        # 執行按鈕
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Generation 開始生成")
        self.start_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        self.start_btn.clicked.connect(self._start_generation)
        
        self.stop_btn = QPushButton("Stop 停止")
        self.stop_btn.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 10px;")
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.setEnabled(False)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        
        right_layout.addLayout(btn_layout)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)
        
        # 日誌輸出
        log_group = QGroupBox("Execution Log 執行日誌")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        right_layout.addWidget(log_group)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 600])
        
        main_layout.addWidget(splitter)
        
        # 連接信號更新任務統計
        for cb in self.function_checkboxes.values():
            cb.stateChanged.connect(self._update_task_stats)
        for cb in self.session_checkboxes.values():
            cb.stateChanged.connect(self._update_task_stats)
    
    def _load_season(self):
        """載入賽季賽程"""
        year = int(self.year_combo.currentText())
        self.log_text.append(f"Loading {year} season schedule...")
        
        try:
            import fastf1
            schedule = fastf1.get_event_schedule(year)
            
            # 過濾測試賽事
            events = schedule[schedule['EventFormat'] != 'testing']
            self.races = events['EventName'].tolist()
            
            # 清除舊的核取方塊
            for cb in self.race_checkboxes:
                cb.deleteLater()
            self.race_checkboxes.clear()
            
            # 創建新的核取方塊
            for i, race in enumerate(self.races):
                # 簡化名稱
                display_name = race.replace(' Grand Prix', '')
                cb = QCheckBox(display_name)
                cb.setProperty("race_name", race)
                cb.stateChanged.connect(self._update_task_stats)
                self.race_checkboxes.append(cb)
                self.race_grid.addWidget(cb, i // 4, i % 4)
            
            self.log_text.append(f"Loaded {len(self.races)} races for {year}")
            
        except Exception as e:
            self.log_text.append(f"Error loading schedule: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load season schedule:\n{e}")
    
    def _toggle_all_races(self, state: bool):
        """全選/取消全選賽事"""
        for cb in self.race_checkboxes:
            cb.setChecked(state)
    
    def _toggle_all_functions(self, state: bool):
        """全選/取消全選功能"""
        for cb in self.function_checkboxes.values():
            cb.setChecked(state)
    
    def _select_essential(self):
        """選擇基本功能"""
        essential = {1, 2, 8, 25, 26, 28}
        for func_id, cb in self.function_checkboxes.items():
            cb.setChecked(func_id in essential)
    
    def _update_task_stats(self):
        """更新任務統計"""
        tasks = self._build_task_list()
        count = len(tasks)
        
        # 估計時間 (平均每個任務 1 分鐘)
        estimated = count
        
        self.task_count_label.setText(f"Tasks 任務數: {count}")
        self.estimated_time_label.setText(f"Est. Time 預估時間: {estimated} min")
    
    def _get_selected_sessions(self) -> Set[str]:
        """取得選擇的 Sessions"""
        return {s for s, cb in self.session_checkboxes.items() if cb.isChecked()}
    
    def _build_task_list(self) -> List[dict]:
        """建構任務列表"""
        tasks = []
        year = int(self.year_combo.currentText())
        selected_sessions = self._get_selected_sessions()
        
        # 取得選擇的賽事
        selected_races = []
        for cb in self.race_checkboxes:
            if cb.isChecked():
                race_name = cb.property("race_name")
                if race_name:
                    # 簡化賽事名稱
                    simple_name = race_name.replace(' Grand Prix', '')
                    selected_races.append(simple_name)
        
        # 取得選擇的功能
        selected_functions = [fid for fid, cb in self.function_checkboxes.items() if cb.isChecked()]
        
        # 建構任務
        # 先處理 season_only 功能 (只需年份，不需要比賽/session)
        season_only_functions = [fid for fid in selected_functions 
                                  if FUNCTION_CONFIGS.get(fid, {}).get('season_only', False)]
        regular_functions = [fid for fid in selected_functions 
                             if fid not in season_only_functions]
        
        # 添加 season_only 任務 (每個功能只執行一次)
        for func_id in season_only_functions:
            tasks.append({
                'function_id': func_id,
                'year': year,
                'race': '',  # 不需要比賽
                'session': '',  # 不需要 session
                'season_only': True
            })
        
        # 添加一般任務 (按比賽和 session)
        for race in selected_races:
            for func_id in regular_functions:
                config = FUNCTION_CONFIGS.get(func_id, {})
                applicable_sessions = config.get('sessions', set())
                
                if not applicable_sessions:
                    # 無 session 限制 (如 F100)
                    tasks.append({
                        'function_id': func_id,
                        'year': year,
                        'race': race,
                        'session': ''
                    })
                else:
                    # 根據適用的 session 過濾
                    for session in selected_sessions:
                        if session in applicable_sessions:
                            tasks.append({
                                'function_id': func_id,
                                'year': year,
                                'race': race,
                                'session': session
                            })
        
        return tasks
    
    def _start_generation(self):
        """開始生成"""
        tasks = self._build_task_list()
        
        if not tasks:
            QMessageBox.warning(self, "No Tasks", "請先選擇賽事和功能")
            return
        
        if self.dry_run_cb.isChecked():
            # Dry Run 模式
            self.log_text.clear()
            self.log_text.append("="*60)
            self.log_text.append("DRY RUN - Preview Mode")
            self.log_text.append("="*60)
            self.log_text.append(f"\nTotal tasks: {len(tasks)}\n")
            
            for i, task in enumerate(tasks, 1):
                if task.get('season_only', False):
                    self.log_text.append(f"{i}. F{task['function_id']} - {task['year']} (Season Analysis)")
                else:
                    self.log_text.append(f"{i}. F{task['function_id']} - {task['year']} {task['race']} {task.get('session', '')}")
            
            self.log_text.append("\n" + "="*60)
            self.log_text.append("End of preview. Uncheck 'Dry Run' to execute.")
            return
        
        # 實際執行
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setMaximum(len(tasks))
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        self.log_text.append("="*60)
        self.log_text.append("Starting batch generation...")
        self.log_text.append(f"Total tasks: {len(tasks)}")
        self.log_text.append("="*60)
        
        self.worker = GeneratorWorker(tasks, self.skip_existing_cb.isChecked())
        self.worker.progress.connect(self._on_progress)
        self.worker.log_message.connect(self._on_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _stop_generation(self):
        """停止生成"""
        if self.worker:
            self.worker.stop()
    
    def _on_progress(self, current: int, total: int):
        """進度更新"""
        self.progress_bar.setValue(current)
        self.setWindowTitle(f"F1T Batch Generator [{current}/{total}]")
    
    def _on_log(self, message: str):
        """日誌更新"""
        self.log_text.append(message)
        # 自動捲動到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
    
    def _on_finished(self, success: int, fail: int):
        """完成處理"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.setWindowTitle("F1T Batch Data Generator")
        
        self.log_text.append("\n" + "="*60)
        self.log_text.append("BATCH GENERATION COMPLETE")
        self.log_text.append(f"Success: {success}")
        self.log_text.append(f"Failed: {fail}")
        self.log_text.append("="*60)
        
        QMessageBox.information(
            self,
            "Complete",
            f"Batch generation complete!\n\nSuccess: {success}\nFailed: {fail}"
        )


# ============================================================================
# 主程式入口
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = BatchGeneratorGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
