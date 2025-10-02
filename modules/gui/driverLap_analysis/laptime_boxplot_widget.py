#!/usr/bin/env python3
"""
LapTimeBoxPlotWidget - F1T 圈速箱型圖視覺化模組
================================================

基於 detailed_laptime_analysis JSON 數據，使用箱型圖 (Box Plot) 視覺化
所有車手的圈速分佈情況。

功能特性：
- 讀取 detailed_laptime_analysis_*.json 數據
- 按車手分組顯示圈速分佈
- 自動過濾異常值（進站圈、安全車圈）
- 顯示中位數、四分位數、異常值
- 車隊配色支援
- 互動式圖表（縮放、平移、保存）

數據來源：
- JSON 檔案：detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json
- 搜尋目錄：json/, json_exports/, cache/ (與 Rain Analysis 一致)
- CLI 功能：Function 28 (Detailed Lap Time Analysis)

架構說明：
- 當前版本：簡化架構，直接繼承 QWidget
- 未來版本：可重構為完全通用架構（UniversalAnalysisMDI）
- 搜尋路徑：與 Rain Analysis 保持一致

作者: F1T Team
日期: 2025-10-02
版本: 1.0.1 (修正搜尋目錄)
"""

import os
import sys
import json
import numpy as np
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QGroupBox, QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# Matplotlib 導入
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 導入基類和工具
try:
    from ..base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig, CliAnalysisWorker
except ImportError:
    # 獨立運行時添加路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig, CliAnalysisWorker

# 導入 i18n
try:
    from core.gui_i18n import tr, set_gui_language
    I18N_AVAILABLE = True
except ImportError:
    def tr(key, fallback=None):
        return fallback if fallback else key
    I18N_AVAILABLE = False


class LapTimeBoxPlotWidget(QWidget):
    """
    圈速箱型圖視覺化 Widget
    
    架構說明：
    - 採用簡化架構，直接繼承 QWidget
    - 不使用 UniversalDataLoader 繼承（避免複雜性）
    - 搜尋目錄與 Rain Analysis 保持一致: json/, json_exports/, cache/
    - 支援 CLI 生成數據（Function 28）
    
    數據流：
    1. 搜尋 JSON 檔案（優先本地）
    2. 找不到時調用 CLI 生成
    3. 載入並驗證數據
    4. 過濾處理（進站圈、異常值）
    5. 繪製箱型圖
    
    未來可重構為完全通用架構（像 Rain Analysis 一樣使用 UniversalAnalysisMDI）
    """
    
    # 信號定義
    data_loaded = pyqtSignal(bool, str)  # 數據載入完成信號 (成功, 訊息)
    analysis_updated = pyqtSignal()      # 分析更新信號
    
    def __init__(self, parent=None, year=None, race=None, session=None):
        """
        初始化圈速箱型圖 Widget
        
        Args:
            parent: 父 Widget
            year: 賽季年份
            race: 賽事名稱
            session: 賽事階段 (R/Q/FP1/FP2/FP3)
        """
        super().__init__(parent)
        
        # 賽事參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 數據存儲
        self.raw_data = None
        self.processed_data = None
        self.driver_laptimes = {}  # {driver: [lap_times]}
        
        # 過濾設定
        self.filter_pit_laps = True
        self.filter_outliers = True
        self.outlier_threshold = 1.5  # IQR 倍數
        
        # UI 組件
        self.figure = None
        self.canvas = None
        self.toolbar = None
        
        # 初始化 UI
        self.init_ui()
        
        # 如果提供了參數，自動載入數據
        if year and race and session:
            self.load_data(year=year, race=race, session=session)
        
        print(f"[BOXPLOT] LapTimeBoxPlotWidget 已初始化: {year} {race} {session}")
    
    def _debug(self, message: str):
        """除錯輸出"""
        print(f"[BOXPLOT] {message}")
    
    def init_ui(self):
        """初始化使用者介面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 標題區域
        title_layout = QHBoxLayout()
        title_label = QLabel("📦 Lap Time Distribution (Box Plot)")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333333;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 刷新按鈕
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedSize(80, 30)
        refresh_btn.clicked.connect(self.refresh_analysis)
        title_layout.addWidget(refresh_btn)
        
        layout.addLayout(title_layout)
        
        # 控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 圖表區域
        self.create_chart_area(layout)
        
        # 狀態標籤
        self.status_label = QLabel("Ready to load data...")
        self.status_label.setStyleSheet("color: #666666; font-size: 9pt;")
        layout.addWidget(self.status_label)
        
        self._debug("UI 初始化完成")
    
    def create_control_panel(self) -> QGroupBox:
        """創建控制面板"""
        panel = QGroupBox("📊 Display Options")
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        layout.setSpacing(15)
        
        # 過濾進站圈
        self.filter_pit_checkbox = QCheckBox("Filter Pit Laps")
        self.filter_pit_checkbox.setChecked(True)
        self.filter_pit_checkbox.stateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.filter_pit_checkbox)
        
        # 過濾異常值
        self.filter_outlier_checkbox = QCheckBox("Filter Outliers (IQR)")
        self.filter_outlier_checkbox.setChecked(True)
        self.filter_outlier_checkbox.stateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.filter_outlier_checkbox)
        
        # 異常值閾值
        threshold_label = QLabel("Outlier Threshold:")
        layout.addWidget(threshold_label)
        
        self.threshold_spinbox = QSpinBox()
        self.threshold_spinbox.setRange(10, 30)  # 1.0 to 3.0 (顯示為 10-30)
        self.threshold_spinbox.setValue(15)  # 預設 1.5
        self.threshold_spinbox.setSuffix(" x IQR")
        self.threshold_spinbox.setToolTip("IQR (Interquartile Range) multiplier for outlier detection")
        self.threshold_spinbox.valueChanged.connect(self.on_threshold_changed)
        layout.addWidget(self.threshold_spinbox)
        
        layout.addStretch()
        
        # 導出按鈕
        export_btn = QPushButton("💾 Export Chart")
        export_btn.setFixedSize(100, 28)
        export_btn.clicked.connect(self.export_chart)
        layout.addWidget(export_btn)
        
        return panel
    
    def create_chart_area(self, parent_layout):
        """創建圖表區域"""
        # 創建 Matplotlib Figure
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0')
        
        # 創建 Canvas
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #f0f0f0;")
        
        # 創建 Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 添加到佈局
        parent_layout.addWidget(self.toolbar)
        parent_layout.addWidget(self.canvas)
        
        self._debug("圖表區域已創建")
    
    # ===== 數據載入和處理 =====
    
    def load_data(self, year=None, race=None, session=None):
        """載入數據"""
        year = year or self.current_year
        race = race or self.current_race
        session = session or self.current_session
        
        self._debug(f"載入數據: {year} {race} {session}")
        self.status_label.setText(f"⏳ Loading data...")
        
        # 更新參數
        self.current_year = str(year)
        self.current_race = race
        self.current_session = session
        
        # 搜尋 JSON 檔案
        json_file = self._search_json_file(year, race, session)
        
        if json_file:
            self._debug(f"✅ 找到 JSON 檔案: {json_file}")
            self._load_from_json(json_file)
        else:
            self._debug("❌ 找不到 JSON 檔案，需要生成")
            self._generate_via_cli(year, race, session)
    
    def _search_json_file(self, year, race, session) -> Optional[str]:
        """搜尋 JSON 檔案 - 與 Rain Analysis 保持一致的搜尋目錄"""
        filename = f"detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json"
        
        # 與 Rain Analysis 一致的搜尋目錄
        search_directories = ["json", "json_exports", "cache"]
        
        self._debug(f"搜尋檔案: {filename}")
        self._debug(f"搜尋目錄: {search_directories}")
        
        for base_path in search_directories:
            full_path = os.path.join(base_path, filename)
            self._debug(f"  檢查: {full_path}")
            if os.path.exists(full_path):
                self._debug(f"  ✅ 找到: {full_path}")
                return full_path
        
        self._debug(f"❌ 找不到檔案")
        return None
    
    def _load_from_json(self, filepath: str):
        """從 JSON 檔案載入數據"""
        try:
            self._debug(f"讀取 JSON: {filepath}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            
            if not self.raw_data.get('success'):
                self._debug("❌ JSON 標記為不成功")
                self.status_label.setText("❌ Data loading failed")
                return
            
            # 處理數據
            self.processed_data = self._transform_data_for_display(self.raw_data)
            
            # 更新顯示
            self._update_display(self.processed_data)
            
        except Exception as e:
            self._debug(f"❌ 載入 JSON 失敗: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"❌ Failed to load JSON: {e}")
    
    def _generate_via_cli(self, year, race, session):
        """通過 CLI 生成數據"""
        self._debug(f"準備通過 CLI 生成數據: {year} {race} {session}")
        self.status_label.setText(f"⏳ Generating data via CLI...")
        
        # 創建 CLI Worker（使用 Function 28）
        self.cli_worker = CliAnalysisWorker(year, race, session, force_mode=28)
        self.cli_worker.analysis_completed.connect(self._on_cli_completed)
        self.cli_worker.progress_updated.connect(self._on_cli_progress)
        self.cli_worker.start()
    
    def _transform_data_for_display(self, raw_data: Any) -> Any:
        """轉換數據為顯示格式"""
        self._debug("開始轉換數據...")
        
        try:
            all_drivers_data = raw_data.get('all_drivers_detailed_laptime', {})
            
            driver_laptimes = {}
            
            for driver, driver_data in all_drivers_data.items():
                if not driver_data.get('success'):
                    continue
                
                detailed_laps = driver_data.get('detailed_lap_data', [])
                lap_times = []
                
                for lap in detailed_laps:
                    lap_time_seconds = lap.get('lap_time_seconds')
                    
                    # 跳過無效圈速
                    if lap_time_seconds is None or lap_time_seconds <= 0:
                        continue
                    
                    # 過濾進站圈
                    if self.filter_pit_laps:
                        smart_markers = lap.get('smart_markers', {})
                        pit_detection = smart_markers.get('pit_stop_detection', {})
                        if pit_detection.get('is_pit_lap', False):
                            continue
                    
                    lap_times.append(lap_time_seconds)
                
                if lap_times:
                    # 過濾異常值
                    if self.filter_outliers:
                        lap_times = self._filter_outliers(lap_times)
                    
                    driver_laptimes[driver] = lap_times
            
            self._debug(f"✅ 成功轉換 {len(driver_laptimes)} 個車手的數據")
            return driver_laptimes
            
        except Exception as e:
            self._debug(f"❌ 數據轉換失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _filter_outliers(self, data: List[float]) -> List[float]:
        """使用 IQR 方法過濾異常值"""
        if len(data) < 4:
            return data
        
        data_array = np.array(data)
        q1 = np.percentile(data_array, 25)
        q3 = np.percentile(data_array, 75)
        iqr = q3 - q1
        
        threshold = self.outlier_threshold
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        filtered = data_array[(data_array >= lower_bound) & (data_array <= upper_bound)]
        
        removed = len(data) - len(filtered)
        if removed > 0:
            self._debug(f"過濾了 {removed} 個異常值")
        
        return filtered.tolist()
    
    def _update_display(self, processed_data: Any):
        """更新顯示"""
        self._debug("更新顯示...")
        
        if not processed_data or not isinstance(processed_data, dict):
            self._debug("❌ 無有效數據可顯示")
            self.status_label.setText("❌ No valid data to display")
            return
        
        self.driver_laptimes = processed_data
        self.plot_boxplot()
        
        total_drivers = len(processed_data)
        total_laps = sum(len(laps) for laps in processed_data.values())
        
        self.status_label.setText(
            f"✅ Showing {total_drivers} drivers, {total_laps} laps | "
            f"{self.current_year} {self.current_race} {self.current_session}"
        )
        
        self._debug(f"✅ 顯示更新完成: {total_drivers} 車手, {total_laps} 圈")
    
    # ===== 圖表繪製 =====
    
    def plot_boxplot(self):
        """繪製箱型圖"""
        if not self.driver_laptimes:
            self._debug("❌ 無數據可繪製")
            return
        
        self._debug(f"繪製箱型圖: {len(self.driver_laptimes)} 個車手")
        
        # 清除舊圖
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 準備數據
        drivers = sorted(self.driver_laptimes.keys())
        data_to_plot = [self.driver_laptimes[driver] for driver in drivers]
        
        # 繪製箱型圖
        bp = ax.boxplot(
            data_to_plot,
            tick_labels=drivers,  # 使用新的參數名稱
            patch_artist=True,
            notch=False,
            showmeans=True,
            meanline=False,
            widths=0.6
        )
        
        # 設置顏色
        colors = self._get_team_colors(drivers)
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # 設置中位數線顏色
        for median in bp['medians']:
            median.set_color('red')
            median.set_linewidth(2)
        
        # 設置平均值標記
        for mean in bp['means']:
            mean.set_marker('D')
            mean.set_markerfacecolor('green')
            mean.set_markeredgecolor('darkgreen')
            mean.set_markersize(6)
        
        # 設置標題和標籤
        title = f"Lap Time Distribution - {self.current_year} {self.current_race} {self.current_session}"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("Driver", fontsize=12, fontweight='bold')
        ax.set_ylabel("Lap Time (seconds)", fontsize=12, fontweight='bold')
        
        # 旋轉 X 軸標籤
        ax.tick_params(axis='x', rotation=45)
        
        # 添加網格
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # 調整佈局
        self.figure.tight_layout()
        
        # 刷新畫布
        self.canvas.draw()
        
        self._debug("✅ 箱型圖繪製完成")
    
    def _get_team_colors(self, drivers: List[str]) -> List[str]:
        """獲取車隊配色"""
        # 簡化版車隊配色（可以後續擴展）
        team_colors = {
            'VER': '#0600EF',  # Red Bull
            'PER': '#0600EF',
            'LEC': '#DC0000',  # Ferrari
            'SAI': '#DC0000',
            'HAM': '#00D2BE',  # Mercedes
            'RUS': '#00D2BE',
            'NOR': '#FF8700',  # McLaren
            'PIA': '#FF8700',
            'ALO': '#006F62',  # Aston Martin
            'STR': '#006F62',
            'GAS': '#0090FF',  # Alpine
            'OCO': '#0090FF',
            'TSU': '#2B4562',  # AlphaTauri
            'LAW': '#2B4562',
            'HUL': '#FFFFFF',  # Haas
            'MAG': '#FFFFFF',
            'BOT': '#900000',  # Alfa Romeo
            'ZHO': '#900000',
            'ALB': '#005AFF',  # Williams
            'SAR': '#005AFF',
        }
        
        colors = []
        for driver in drivers:
            colors.append(team_colors.get(driver, '#CCCCCC'))
        
        return colors
    
    # ===== 事件處理 =====
    
    def on_filter_changed(self, state):
        """過濾選項變更"""
        self.filter_pit_laps = self.filter_pit_checkbox.isChecked()
        self.filter_outliers = self.filter_outlier_checkbox.isChecked()
        
        self._debug(f"過濾設定變更: 進站圈={self.filter_pit_laps}, 異常值={self.filter_outliers}")
        
        # 重新處理數據
        if self.raw_data:
            self.processed_data = self._transform_data_for_display(self.raw_data)
            self._update_display(self.processed_data)
    
    def on_threshold_changed(self, value):
        """閾值變更"""
        self.outlier_threshold = value / 10.0  # 10 -> 1.0, 15 -> 1.5
        self._debug(f"異常值閾值變更: {self.outlier_threshold}")
        
        # 重新處理數據
        if self.raw_data and self.filter_outliers:
            self.processed_data = self._transform_data_for_display(self.raw_data)
            self._update_display(self.processed_data)
    
    def refresh_analysis(self):
        """刷新分析"""
        if self.current_year and self.current_race and self.current_session:
            self._debug("手動刷新分析...")
            self.load_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session
            )
        else:
            QMessageBox.warning(self, "Warning", "No race parameters set!")
    
    def export_chart(self):
        """導出圖表"""
        if not self.figure:
            QMessageBox.warning(self, "Warning", "No chart to export!")
            return
        
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            f"laptime_boxplot_{self.current_year}_{self.current_race}_{self.current_session}.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg)"
        )
        
        if filename:
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", f"Chart exported to:\n{filename}")
                self._debug(f"✅ 圖表已導出: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export chart:\n{e}")
                self._debug(f"❌ 導出失敗: {e}")
    
    # ===== CLI 回調 =====
    
    def _on_cli_completed(self, success: bool, message: str):
        """CLI 分析完成回調"""
        if success:
            self._debug(f"✅ CLI 分析成功: {message}")
            self.status_label.setText("✅ CLI analysis completed, loading data...")
            
            # 重新嘗試載入數據
            self.load_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session
            )
        else:
            self._debug(f"❌ CLI 分析失敗: {message}")
            self.status_label.setText(f"❌ CLI analysis failed: {message}")
            QMessageBox.critical(self, "CLI Error", f"Analysis failed:\n{message}")
    
    def _on_cli_progress(self, message: str):
        """CLI 進度更新回調"""
        self.status_label.setText(f"⏳ {message}")


# 測試代碼
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 設置字體
    font = QFont("Arial", 9)
    app.setFont(font)
    
    # 創建測試視窗
    widget = LapTimeBoxPlotWidget(year=2025, race="Belgium", session="R")
    widget.setWindowTitle("Lap Time Box Plot - Test")
    widget.resize(1400, 800)
    widget.show()
    
    sys.exit(app.exec_())
