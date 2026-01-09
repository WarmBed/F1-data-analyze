#!/usr/bin/env python3
"""
Race Strategy Simulator - Main Window

Main application window with input panel and results tabs.

Author: F1T Team
Date: 2025-12-30
"""

import sys
from pathlib import Path
from typing import Optional

# CRITICAL: Add project root to sys.path FIRST, before any other imports
# This ensures 'core' resolves to project_root/core/ (logger, api_base_url)
# and NOT strategy_simulator/core/ (which is a different module)
_project_root = Path(__file__).parent.parent.parent
_project_root_str = str(_project_root)
if _project_root_str not in sys.path:
    sys.path.insert(0, _project_root_str)

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QStatusBar, QMenuBar,
    QMenu, QAction, QMessageBox, QApplication,
    QProgressBar, QLabel, QPushButton, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from strategy_simulator.core import (
    ConfigLoader, LapSimulator, StrategyOptimizer,
    MonteCarloSimulator, SimulationParams, Stint, Compound,
    StrategyConstraints, MonteCarloParams
)
from strategy_simulator.core.competitive_optimizer import CompetitiveStrategyOptimizer
from strategy_simulator.core.competitive_monte_carlo import CompetitiveMonteCarloSimulator
from strategy_simulator.data import LongRunLoader
from strategy_simulator.gui.i18n_helper import tr


class MainWindow(QMainWindow):
    """
    Race Strategy Simulator main window.
    
    Layout:
    ┌─────────────────────────────────────────────┐
    │ Menu Bar                                     │
    ├─────────────────────────────────────────────┤
    │ ┌──────────────┬──────────────────────────┐ │
    │ │ Input Panel  │ Results Tabs             │ │
    │ │              │ ┌──────────────────────┐ │ │
    │ │ Race Select  │ │ Strategy | Chart |   │ │ │
    │ │ Parameters   │ │ SC | Opponent | Data │ │ │
    │ │ Run Button   │ │                      │ │ │
    │ │              │ └──────────────────────┘ │ │
    │ └──────────────┴──────────────────────────┘ │
    ├─────────────────────────────────────────────┤
    │ Status Bar                                   │
    └─────────────────────────────────────────────┘
    """
    
    # Signals
    simulation_started = pyqtSignal()
    simulation_completed = pyqtSignal(object)  # List of results
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Core components
        self.config_loader: Optional[ConfigLoader] = None
        self.longrun_loader: Optional[LongRunLoader] = None
        
        # Current simulation state
        self._current_params: Optional[SimulationParams] = None
        self._current_results: list = []
        
        self._setup_ui()
        self._setup_menu()
        self._init_loaders()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        self.setWindowTitle("F1T 比賽策略模擬器")
        self.setMinimumSize(1400, 900)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QHBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Main splitter (Input | Results)
        main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter = main_splitter
        layout.addWidget(main_splitter)
        
        # 左側面板容器（包含摺疊按鈕）
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Left: Input panel
        from .input_panel import InputPanel
        self.input_panel = InputPanel(self)
        self.input_panel.setMinimumWidth(350)
        self.input_panel.setMaximumWidth(420)
        left_layout.addWidget(self.input_panel)
        
        # 摺疊按鈕
        self.toggle_btn = QToolButton()
        self.toggle_btn.setText("◀")
        self.toggle_btn.setFixedWidth(15)
        self.toggle_btn.setStyleSheet("""
            QToolButton {
                background-color: #e0e0e0;
                border: none;
                border-left: 1px solid #ccc;
                font-size: 10px;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: #d0d0d0;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle_input_panel)
        self.toggle_btn.setToolTip("收起/展開參數面板 (Ctrl+B)")
        left_layout.addWidget(self.toggle_btn)
        
        # 儲存狀態
        self._input_panel_visible = True
        self._saved_input_width = 450
        
        main_splitter.addWidget(left_container)
        
        # Right: Two-column results area (Q10 layout)
        self.results_container = QWidget()
        results_layout = QHBoxLayout(self.results_container)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(5)
        
        # Results splitter for two columns
        self.results_splitter = QSplitter(Qt.Horizontal)
        results_layout.addWidget(self.results_splitter)
        
        # Left column: Strategy + Detail + MC + Opponents
        self.left_tabs = QTabWidget()
        self.left_tabs.setTabPosition(QTabWidget.North)
        self.results_splitter.addWidget(self.left_tabs)
        
        # Right column: SC + Impact + Decision
        self.right_tabs = QTabWidget()
        self.right_tabs.setTabPosition(QTabWidget.North)
        self.results_splitter.addWidget(self.right_tabs)
        
        # Set results splitter stretch factors (50:50 ratio)
        self.results_splitter.setStretchFactor(0, 1)  # Left tabs
        self.results_splitter.setStretchFactor(1, 1)  # Right tabs
        
        print("[SETUP] 添加 results_container 到 main_splitter", flush=True)
        main_splitter.addWidget(self.results_container)
        print(f"[SETUP] main_splitter 子 widget 數量: {main_splitter.count()}", flush=True)
        print(f"[SETUP] main_splitter 當前 sizes: {main_splitter.sizes()}", flush=True)
        
        # Set main splitter stretch factors (Input:Results = 1:3)
        print("[SETUP] 設置 stretch factors", flush=True)
        main_splitter.setStretchFactor(0, 1)  # Input panel
        main_splitter.setStretchFactor(1, 3)  # Results area
        print(f"[SETUP] 設置 stretch factors 後 sizes: {main_splitter.sizes()}", flush=True)
        
        # Keep reference to results_tabs for backward compatibility
        self.results_tabs = self.left_tabs
        
        # Create result tabs
        print("[_setup_ui] 開始創建結果標籤頁...", flush=True)
        self._create_result_tabs()
        print("[_setup_ui] 結果標籤頁創建完成", flush=True)
        
        # Status bar with progress indicator
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)  # Hidden by default
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Add detailed status label
        self.detailed_status = QLabel("")
        self.status_bar.addPermanentWidget(self.detailed_status)
        
        self.status_bar.showMessage("就緒 - 請選擇賽事開始")
        
        # Connect signals
        self.input_panel.run_simulation.connect(self._on_run_simulation)
        self.input_panel.track_changed.connect(self._on_track_changed)
        self.input_panel.deg_source_changed.connect(self._on_deg_source_changed)
        self.input_panel.longrun_settings_requested.connect(self._on_longrun_settings_requested)
        self.input_panel.opponent_mode_changed.connect(self._on_opponent_mode_changed)
        
        # ✅ 初始化 splitter 尺寸（直接調用，不使用 QTimer）
        print("[_setup_ui] 完成，準備初始化 splitter 尺寸...", flush=True)
        self._initialize_splitter_sizes()
        print("[_setup_ui] Splitter 尺寸初始化完成", flush=True)
    
    def _initialize_splitter_sizes(self):
        """初始化 splitter 尺寸，確保摺疊功能能正常運作"""
        print("\n" + "="*60)
        print("[INIT] 開始初始化 Splitter 尺寸")
        print("="*60)
        
        print(f"[INIT] Splitter 子 widget 數量: {self.main_splitter.count()}")
        print(f"[INIT] 初始化前 sizes: {self.main_splitter.sizes()}")
        
        # 設置初始比例 (1:3)
        total_width = self.width()
        input_width = min(420, int(total_width * 0.25))  # 25% 或最大 420px
        results_width = total_width - input_width
        
        print(f"[INIT] 視窗總寬度: {total_width}px")
        print(f"[INIT] 計算的輸入面板寬度: {input_width}px")
        print(f"[INIT] 計算的結果區域寬度: {results_width}px")
        print(f"[INIT] 準備設置 sizes: [{input_width}, {results_width}]")
        
        self.main_splitter.setSizes([input_width, results_width])
        
        actual_sizes = self.main_splitter.sizes()
        print(f"[INIT] 設置後實際 sizes: {actual_sizes}")
        print(f"[INIT] 設置是否成功: {len(actual_sizes) == 2 and actual_sizes[0] > 0}")
        print("="*60 + "\n")
    
    def _create_result_tabs(self):
        """
        Create all result tabs in two-column layout (Q10).
        
        Left column: 總時間最短策略 + 完整賽事
        Right column: 詳細資料 + 動態模擬 + 對手分析 + SC 場景 + 單圈曲線 + FP2→Q
        """
        print("[_create_result_tabs] Step 1: Importing tabs...", flush=True)
        from .results_tabs import (
            StrategyComparisonTab, LapCurvesTab, SafetyCarTab, 
            OpponentTab, DetailedDataTab, FP2PredictionTab,
            FullRaceTab, RaceResultAnalysisTab
        )
        print("[_create_result_tabs] Step 2: Importing SimulationTab...", flush=True)
        # PositionAnalysisTab - ❌ 已移除
        from .results_tabs.simulation_tab import SimulationTab
        print("[_create_result_tabs] Step 3: All imports complete", flush=True)
        
        # === LEFT COLUMN: Main Analysis ===
        
        # FP2->Q Prediction (for driver selection)
        print("[MAIN_WINDOW] 初始化 FP2→Q 預測標籤頁...", flush=True)
        self.fp2_tab = FP2PredictionTab(self)
        print(f"[MAIN_WINDOW] FP2→Q 標籤頁初始化完成: {type(self.fp2_tab)}", flush=True)
        self.fp2_tab.driver_selected.connect(self._on_driver_selected)
        # Connect Q data availability signal to input panel
        self.fp2_tab.q_data_available.connect(self._on_q_data_available)
        self.left_tabs.addTab(self.fp2_tab, "FP2→Q")
        
        # Strategy Comparison (總時間最短策略)
        self.comparison_tab = StrategyComparisonTab(self)
        self.left_tabs.addTab(self.comparison_tab, "總時間最短策略")
        
        # Full Race Simulation (完整賽事模擬)
        self.full_race_tab = FullRaceTab(self)
        self.full_race_tab.simulation_requested.connect(self._on_full_race_requested)
        self.left_tabs.addTab(self.full_race_tab, "完整賽事")
        
        # === RIGHT COLUMN: Detailed Analysis ===
        
        # Detailed Data (詳細資料)
        self.detail_tab = DetailedDataTab(self)
        self.right_tabs.addTab(self.detail_tab, "詳細資料")
        
        # NEW: Dynamic Simulation Tab (動態模擬)
        self.simulation_tab = SimulationTab(self)
        self.right_tabs.addTab(self.simulation_tab, "動態模擬")
        
        # Opponent Analysis (對手分析 - Undercut/Overcut + 阻擋)
        self.opponent_tab = OpponentTab(self)
        self.opponent_tab.strategy_settings_changed.connect(self._on_opponent_strategy_changed)
        self.right_tabs.addTab(self.opponent_tab, "對手分析")
        
        # SC Scenarios (SC 場景)
        self.sc_tab = SafetyCarTab(self)
        self.right_tabs.addTab(self.sc_tab, "SC 場景")
        
        # Lap Time Curves (單圈時間)
        self.chart_tab = LapCurvesTab(self)
        print(f"[MAIN_WINDOW] ===== LapCurvesTab created =====", flush=True)
        print(f"[MAIN_WINDOW] chart_tab type: {type(self.chart_tab)}", flush=True)
        print(f"[MAIN_WINDOW] chart_tab size: {self.chart_tab.size()}", flush=True)
        print(f"[MAIN_WINDOW] chart_tab width: {self.chart_tab.width()}", flush=True)
        self.right_tabs.addTab(self.chart_tab, "單圈曲線")
        print(f"[MAIN_WINDOW] ===== Added to right_tabs =====", flush=True)
        
        # Race Result Analysis (結果分析)
        self.result_analysis_tab = RaceResultAnalysisTab(self)
        self.right_tabs.addTab(self.result_analysis_tab, "結果分析")
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("檔案")
        
        export_action = QAction("匯出結果...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("結束", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("檢視")
        
        # Toggle input panel action
        toggle_panel_action = QAction("收起/展開參數面板", self)
        toggle_panel_action.setShortcut("Ctrl+B")
        toggle_panel_action.triggered.connect(self._toggle_input_panel)
        view_menu.addAction(toggle_panel_action)
        
        view_menu.addSeparator()
        
        reset_view_action = QAction("重設視圖", self)
        reset_view_action.triggered.connect(self._on_reset_view)
        view_menu.addAction(reset_view_action)
        
        # Help menu
        help_menu = menubar.addMenu("說明")
        
        about_action = QAction("關於", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _init_loaders(self):
        """Initialize data loaders."""
        try:
            print("[_init_loaders] Step 1: Creating ConfigLoader", flush=True)
            self.config_loader = ConfigLoader()
            print("[_init_loaders] Step 2: Creating LongRunLoader", flush=True)
            self.longrun_loader = LongRunLoader()
            print("[_init_loaders] Step 3: Getting track list", flush=True)
            
            # Populate track list in input panel
            tracks = self.config_loader.get_track_list()
            print(f"[_init_loaders] Step 4: Setting track list ({len(tracks)} tracks)", flush=True)
            self.input_panel.set_track_list(tracks)
            print("[_init_loaders] Step 5: Getting current track", flush=True)
            
            # Manually trigger track_changed for the default track (Yas Marina)
            # This ensures FP2 data is loaded after all tabs are initialized
            current_track = self.input_panel.track_combo.currentText()
            print(f"[_init_loaders] Step 6: Current track = {current_track}", flush=True)
            if current_track:
                print(f"[_init_loaders] Step 7: Calling _on_track_changed('{current_track}')", flush=True)
                self._on_track_changed(current_track)
                print("[_init_loaders] Step 8: _on_track_changed returned", flush=True)
            
            print("[_init_loaders] Step 9: COMPLETE!", flush=True)
        except Exception as e:
            print(f"[MAIN_WINDOW] Failed to initialize loaders: {e}")
            QMessageBox.warning(
                self, "初始化警告",
                f"無法載入賽道資料庫: {e}\n\n將使用預設值。"
            )
    
    def _on_track_changed(self, track_name: str):
        """
        Handle track selection change.
        
        Auto-updates race laps, base lap time, and other track-specific 
        parameters in the input panel.
        
        Also tries to load FP2 Long Run data if available.
        
        Args:
            track_name: Name of the selected track
        """
        print(f"[_on_track_changed] Step 1: track_name={track_name}", flush=True)
        
        if not self.config_loader or not track_name:
            print(f"[_on_track_changed] Early return: config_loader={self.config_loader}, track_name={track_name}", flush=True)
            return
        
        try:
            print(f"[_on_track_changed] Step 2: Loading track config...", flush=True)
            # Get track configuration from trained database
            track_config = self.config_loader.get_track_config(track_name)
            print(f"[_on_track_changed] Step 3: Track config loaded", flush=True)
            
            # Store track config for later use (blocking analysis, etc.)
            self._current_track_config = track_config
            
            # Get current year from input panel
            print(f"[_on_track_changed] Step 4: Getting year", flush=True)
            year = int(self.input_panel.year_combo.currentText())
            print(f"[_on_track_changed] Step 5: Year = {year}", flush=True)
            
            # Try to load FP2 Long Run data for this race
            fp2_data = None
            if self.longrun_loader:
                print(f"[_on_track_changed] Step 6: Loading FP2 data (may take 120s)...", flush=True)
                fp2_data = self.longrun_loader.load_fp2_data(year, track_name)
                print(f"[_on_track_changed] Step 7: FP2 data = {fp2_data is not None}", flush=True)
            
            print(f"[_on_track_changed] Step 8: Processing degradation values", flush=True)
            
            # Determine degradation values and base lap time
            base_lap_time = track_config.base_lap_time  # Default from track config (from pit_strategy_database.json)
            
            if fp2_data and fp2_data.degradation:
                # Use FP2 Long Run data (more accurate for this specific race)
                deg_soft = fp2_data.get_deg_rate("SOFT")
                deg_medium = fp2_data.get_deg_rate("MEDIUM")
                deg_hard = fp2_data.get_deg_rate("HARD")
                source_msg = f"FP2 Long Run ({fp2_data.session_type})"
                
                # Use FP2 calculated base lap time if available
                if fp2_data.base_lap_time and fp2_data.base_lap_time_method == "fp2_regression_extrapolation":
                    base_lap_time = fp2_data.base_lap_time
                
                # Store FP2 data for later use
                self._current_fp2_data = fp2_data
                
                # Update source combo to show "從 Long Run 數據"
                self.input_panel.deg_source_combo.setCurrentText("從 Long Run 數據")
            else:
                # Use trained database values
                deg_soft = track_config.deg_soft
                deg_medium = track_config.deg_medium
                deg_hard = track_config.deg_hard
                source_msg = "賽道歷史訓練數據"
                
                # Update source combo to show "賽道預設值"
                self.input_panel.deg_source_combo.setCurrentText("賽道預設值")
            
            # Update input panel with track-specific values
            self.input_panel.update_track_parameters(
                race_laps=track_config.typical_race_laps,
                base_lap_time=base_lap_time,  # Use FP2 value if available
                pit_loss_green=track_config.pit_loss_green,
                pit_loss_sc=track_config.pit_loss_sc,
                deg_soft=deg_soft,
                deg_medium=deg_medium,
                deg_hard=deg_hard,
                fuel_per_lap=track_config.fuel_kg_per_lap,
                fuel_effect=track_config.fuel_effect_coefficient,
                start_fuel=track_config.start_fuel_kg,
                # Traffic parameters from track features
                traffic_decay_rate=track_config.traffic_decay_rate,
                traffic_loss_per_position=track_config.traffic_loss_per_position,
                first_lap_loss=track_config.first_lap_loss,
            )
            
            # Update status bar with data source info
            trained_info = ""
            if track_config.trained_from_data:
                trained_info = " [已訓練]"
            
            overtaking_info = f"超車難度: {track_config.overtaking_difficulty:.0%}"
            
            # Show base lap time source in status bar
            base_time_source = "FP2" if (fp2_data and fp2_data.base_lap_time_method == "fp2_regression_extrapolation") else "預設"
            
            self.status_bar.showMessage(
                f"已載入 {track_config.official_name} 的參數 "
                f"({track_config.typical_race_laps} 圈, 基準圈時 {base_lap_time:.1f}s [{base_time_source}], {overtaking_info}) "
                f"- 衰減來源: {source_msg}{trained_info}"
            )
            
            # Load FP2->Q prediction for driver selection
            try:
                print(f"[MAIN_WINDOW] 準備載入 FP2→Q 預測: year={year}, track_name={track_name}", flush=True)
                if hasattr(self, 'fp2_tab'):
                    print(f"[MAIN_WINDOW] fp2_tab 存在，呼叫 load_prediction()...", flush=True)
                    self.fp2_tab.load_prediction(str(year), track_name)
                else:
                    print(f"[MAIN_WINDOW] ❌ fp2_tab 不存在！", flush=True)
                    
                # Pass FP2/Q predictions to OpponentTab based on driver selection mode
                if hasattr(self, 'opponent_tab') and hasattr(self, 'fp2_tab') and hasattr(self, 'input_panel'):
                    # Get current driver selection mode from input panel
                    driver_mode = self.input_panel.opponent_mode_combo.currentIndex()
                    use_q_ranking = (driver_mode == 1)  # 0=FP2, 1=Q, 2=Manual
                    
                    if use_q_ranking and self.fp2_tab.has_actual_q_data():
                        # Use actual Q ranking
                        predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=True)
                        print("[MAIN_WINDOW] OpponentTab 使用實際 Q 排位數據", flush=True)
                    else:
                        # Use FP2 predicted ranking
                        predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=False)
                        if use_q_ranking:
                            print("[MAIN_WINDOW] OpponentTab 無實際 Q 數據，使用 FP2 預測排位", flush=True)
                        else:
                            print("[MAIN_WINDOW] OpponentTab 使用 FP2 預測排位", flush=True)
                    
                    if predictions:
                        # Update predictions with effective_rank as 'rank'
                        for pred in predictions:
                            pred['rank'] = pred.get('effective_rank', pred.get('rank', 99))
                        self.opponent_tab.load_predictions(predictions)
                    else:
                        # No FP2 data available, load default drivers
                        print("[MAIN_WINDOW] No FP2 predictions, loading default drivers", flush=True)
                        if hasattr(self.opponent_tab, 'strategy_panel') and self.opponent_tab.strategy_panel:
                            self.opponent_tab.strategy_panel.load_default_drivers()
                        
            except Exception as pred_e:
                print(f"[MAIN_WINDOW] ❌ 載入 FP2→Q 預測失敗: {pred_e}", flush=True)
                import traceback
                traceback.print_exc()
                # Fallback: load default drivers on error
                if hasattr(self, 'opponent_tab') and hasattr(self.opponent_tab, 'strategy_panel'):
                    if self.opponent_tab.strategy_panel:
                        self.opponent_tab.strategy_panel.load_default_drivers()
            
        except Exception as e:
            print(f"[MAIN_WINDOW] Failed to load track config for {track_name}: {e}")
    
    def _on_opponent_mode_changed(self, mode_index: int):
        """
        Handle opponent selection mode change (FP2 vs Q vs Manual).
        
        Args:
            mode_index: 0=FP2, 1=Q, 2=Manual
        """
        print(f"[MAIN_WINDOW] Opponent mode changed to: {mode_index} (0=FP2, 1=Q, 2=Manual)", flush=True)
        
        # Reload OpponentTab predictions with correct ranking mode
        if hasattr(self, 'opponent_tab') and hasattr(self, 'fp2_tab'):
            use_q_ranking = (mode_index == 1)
            
            if use_q_ranking and self.fp2_tab.has_actual_q_data():
                # Use actual Q ranking
                predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=True)
                print("[MAIN_WINDOW] 切換至 Q 排位模式", flush=True)
            else:
                # Use FP2 predicted ranking
                predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=False)
                print("[MAIN_WINDOW] 切換至 FP2 預測模式", flush=True)
            
            if predictions:
                # Update predictions with effective_rank as 'rank'
                for pred in predictions:
                    pred['rank'] = pred.get('effective_rank', pred.get('rank', 99))
                self.opponent_tab.load_predictions(predictions)
                print(f"[MAIN_WINDOW] OpponentTab 已更新預測數據 ({len(predictions)} 車手)", flush=True)
    
    def _on_longrun_settings_requested(self):
        """
        Open main GUI's Long Run Analysis module in a new window.
        
        This directly uses the main GUI's LongRunAnalysis MDI widget,
        ensuring consistent behavior and avoiding code duplication.
        """
        try:
            from modules.gui.long_run_analysis.long_run_mdi import LongRunAnalysis
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
            
            year = self.input_panel.get_year()
            track_name = self.input_panel.get_track()
            
            # Convert track name to race name for API consistency
            # Strategy Simulator uses "Yas Marina", API uses "Abu Dhabi"
            race_name = track_name
            if self.config_loader:
                race_name = self.config_loader.get_race_name(track_name)
            
            print(f"[MAIN_WINDOW] Opening main GUI Long Run module for {year} {race_name} (track: {track_name})")
            
            # Create a dialog to host the Long Run MDI
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Long Run 分析 - {year} {race_name} FP2")
            dialog.setMinimumSize(1200, 800)
            dialog.resize(1400, 900)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Create the Long Run Analysis widget with proper parameters
            # Use race_name (not track_name) for API compatibility
            self._longrun_widget = LongRunAnalysis(year=year, race=race_name, session="FP2")
            layout.addWidget(self._longrun_widget)
            
            # Add apply button at bottom
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            
            apply_btn = QPushButton("套用到策略模擬器")
            apply_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
                QPushButton:hover { background-color: #45a049; }
            """)
            apply_btn.clicked.connect(lambda: self._apply_longrun_results(dialog))
            btn_layout.addWidget(apply_btn)
            
            close_btn = QPushButton("關閉")
            close_btn.clicked.connect(dialog.close)
            btn_layout.addWidget(close_btn)
            
            layout.addLayout(btn_layout)
            
            # Data loading is handled automatically by LongRunAnalysis constructor
            # via QTimer.singleShot(100, self._load_data)
            
            dialog.exec_()
            
        except ImportError as e:
            print(f"[MAIN_WINDOW] Cannot import main GUI Long Run module: {e}")
            QMessageBox.warning(
                self,
                "模組未找到",
                f"無法載入主 GUI 的 Long Run 模組:\n{str(e)}\n\n"
                "請確保主 GUI 模組已正確安裝。"
            )
        except Exception as e:
            print(f"[MAIN_WINDOW] Error opening Long Run module: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Long Run Error",
                f"無法開啟 Long Run 分析:\n{str(e)}"
            )
    
    def _apply_longrun_results(self, dialog):
        """
        Apply Long Run results from main GUI module to strategy simulator.
        
        Args:
            dialog: The dialog containing the Long Run widget
        """
        try:
            if not hasattr(self, '_longrun_widget') or not self._longrun_widget:
                QMessageBox.warning(self, "無數據", "請先完成 Long Run 分析")
                return
            
            # Get calculated degradation results using the new API
            deg_results = self._longrun_widget.get_degradation_results()
            print(f"[MAIN_WINDOW] Got degradation results: {deg_results}")
            
            if not deg_results:
                QMessageBox.warning(
                    self, 
                    "無計算結果", 
                    "請先在 Degradation Results 頁籤計算衰退率。\n\n"
                    "步驟:\n"
                    "1. 在 Stint Selection 選擇 Long Run stints\n"
                    "2. 在 Fuel Settings 設定燃油參數\n"
                    "3. 切換到 Degradation Results 頁籤查看結果"
                )
                return
            
            # Apply degradation values
            applied_count = 0
            applied_details = []
            for compound, data in deg_results.items():
                compound_lower = compound.lower()
                if compound_lower in ['soft', 'medium', 'hard']:
                    deg_rate = data.get('deg_per_lap', 0)
                    raw_rate = data.get('raw_deg_per_lap', deg_rate)
                    count = data.get('count', 0)
                    self.input_panel.set_degradation(compound_lower, deg_rate)
                    applied_details.append(f"{compound}: {deg_rate:.3f} s/lap (n={count})")
                    print(f"[MAIN_WINDOW] Applied {compound}: raw={raw_rate:.4f}, abs={deg_rate:.4f} s/lap (n={count})")
                    applied_count += 1
            
            if applied_count == 0:
                QMessageBox.warning(self, "無有效數據", "未找到有效的輪胎衰退數據 (SOFT/MEDIUM/HARD)")
                return
            
            # Apply fuel settings from Long Run
            fuel_settings = self._longrun_widget.get_fuel_settings()
            if fuel_settings:
                consumption = fuel_settings.get('consumption', 1.65)
                effect = fuel_settings.get('effect', 0.030)
                self.input_panel.fuel_per_lap_spin.setValue(consumption)
                self.input_panel.fuel_effect_spin.setValue(effect)
                print(f"[MAIN_WINDOW] Applied fuel settings: consumption={consumption} kg/lap, effect={effect} s/kg")
            
            # Update source to Long Run data mode
            self.input_panel.deg_source_combo.setCurrentText("從 Long Run 數據")
            
            # Disable manual input after applying Long Run data
            self.input_panel.deg_manual_widget.setEnabled(False)
            
            # Get session info for display
            session_info = self._longrun_widget.get_session_info()
            year = session_info.get('year', '')
            race = session_info.get('race', '')
            
            # Show success message with details
            self.status_bar.showMessage(
                f"Long Run 數據已套用 ({race} {year} FP2) - " + ", ".join(applied_details)
            )
            
            # Close dialog
            dialog.accept()
            
        except Exception as e:
            print(f"[MAIN_WINDOW] Error applying Long Run results: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "套用錯誤", f"無法套用 Long Run 結果:\n{str(e)}")
    
    def _on_longrun_data_confirmed(self, longrun_data):
        """
        Handle confirmed Long Run data from dialog.
        
        Args:
            longrun_data: LongRunData object with calculated degradation values
        """
        try:
            print(f"[MAIN_WINDOW] Long Run data confirmed from dialog")
            
            # Update input panel with calculated degradation values
            self.input_panel.set_degradation('soft', longrun_data.get_deg_rate('SOFT'))
            self.input_panel.set_degradation('medium', longrun_data.get_deg_rate('MEDIUM'))
            self.input_panel.set_degradation('hard', longrun_data.get_deg_rate('HARD'))
            
            # Update base lap time if available
            if longrun_data.base_lap_time:
                self.input_panel.set_base_lap_time(longrun_data.base_lap_time)
                print(f"[MAIN_WINDOW] Updated base lap time: {longrun_data.base_lap_time:.3f}s")
            
            # Store FP2 data for use in simulation
            self._current_fp2_data = longrun_data
            
            # Update source combo to reflect the data source
            self.input_panel.deg_source_combo.setCurrentText("從 Long Run 數據")
            
            # Show confirmation
            drivers = longrun_data.drivers_analyzed
            stints = longrun_data.stints_analyzed
            track_evo = longrun_data.track_evolution_per_lap
            
            status_msg = (f"Long Run 數據已套用: {drivers} 車手, {stints} 段落, "
                          f"賽道演進 {track_evo:.3f} s/lap")
            self.status_bar.showMessage(status_msg)
            
            print(f"[MAIN_WINDOW] Long Run data applied successfully")
            
        except Exception as e:
            print(f"[MAIN_WINDOW] Error applying Long Run data: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_deg_source_changed(self, source: str):
        """
        Handle degradation source change from input panel.
        
        Args:
            source: The selected source ('手動輸入', '從 Long Run 數據', '賽道預設值')
        """
        print(f"[MAIN_WINDOW] Degradation source changed to: {source}")
        
        try:
            year = self.input_panel.get_year()
            track_name = self.input_panel.get_track()
            
            if source == '從 Long Run 數據':
                # Load and calculate FP2 Long Run data with full analysis
                self.status_bar.showMessage(f"正在載入 {year} {track_name} FP2 數據...")
                QApplication.processEvents()
                
                fp2_data = self.longrun_loader.load_fp2_data(year, track_name, "FP2")
                if fp2_data:
                    # Update input panel with calculated degradation values
                    self.input_panel.set_degradation('soft', fp2_data.get_deg_rate('SOFT'))
                    self.input_panel.set_degradation('medium', fp2_data.get_deg_rate('MEDIUM'))
                    self.input_panel.set_degradation('hard', fp2_data.get_deg_rate('HARD'))
                    
                    # Store FP2 data for use in simulation
                    self._current_fp2_data = fp2_data
                    
                    # Update base lap time if calculated from FP2
                    if fp2_data.base_lap_time and fp2_data.base_lap_time_method == "fp2_regression_extrapolation":
                        self.input_panel.set_base_lap_time(fp2_data.base_lap_time)
                        print(f"[MAIN_WINDOW] Updated base lap time from FP2: {fp2_data.base_lap_time:.3f}s")
                    
                    # Show detailed analysis info
                    drivers = fp2_data.drivers_analyzed
                    stints = fp2_data.stints_analyzed
                    track_evo = fp2_data.track_evolution_per_lap
                    
                    # Log detailed per-driver info
                    print(f"[MAIN_WINDOW] FP2 Analysis Results for {year} {track_name}:")
                    print(f"  - Drivers analyzed: {drivers}")
                    print(f"  - Stints analyzed: {stints}")
                    print(f"  - Track evolution: {track_evo:.4f} s/lap")
                    for compound, deg_data in fp2_data.degradation.items():
                        if compound.upper() == "UNKNOWN":
                            continue  # Skip UNKNOWN compound
                        print(f"  - {compound}: {deg_data.deg_per_lap:.3f} s/lap "
                              f"(range: {deg_data.min_deg:.3f} - {deg_data.max_deg:.3f}, "
                              f"drivers: {deg_data.driver_samples})")
                    
                    status_msg = (f"FP2 Long Run 分析完成: {drivers} 車手, {stints} 段落, "
                                  f"賽道演進 {track_evo:.3f} s/lap")
                    self.status_bar.showMessage(status_msg)
                    
                    # Show detailed message box
                    detail_lines = [f"== {year} {track_name} FP2 Long Run 分析 ==\n"]
                    detail_lines.append(f"分析車手數: {drivers}")
                    detail_lines.append(f"分析段落數: {stints}")
                    detail_lines.append(f"賽道演進: {track_evo:.4f} s/lap\n")
                    
                    for compound, deg_data in sorted(fp2_data.degradation.items()):
                        # Skip UNKNOWN compound - not useful for strategy
                        if compound.upper() == "UNKNOWN":
                            continue
                        detail_lines.append(f"{compound}:")
                        detail_lines.append(f"  平均衰減: {deg_data.deg_per_lap:.4f} s/lap")
                        detail_lines.append(f"  範圍: {deg_data.min_deg:.4f} - {deg_data.max_deg:.4f}")
                        detail_lines.append(f"  車手: {', '.join(deg_data.driver_samples)}")
                    
                    QMessageBox.information(
                        self,
                        "FP2 Long Run 分析結果",
                        "\n".join(detail_lines)
                    )
                else:
                    self.status_bar.showMessage(
                        f"找不到 {year} {track_name} FP2 數據，請確認 API 連線或先執行主 GUI 的 Long Run 分析")
                    QMessageBox.warning(
                        self,
                        "無 FP2 數據",
                        f"找不到 {year} {track_name} FP2 Long Run 數據。\n\n"
                        "可能原因:\n"
                        "1. API 連線失敗\n"
                        "2. 尚未執行該場次的 FP2 分析\n"
                        "3. 該場次沒有 FP2 數據"
                    )
                    
            elif source == '賽道預設值':
                # Load from trained database using get_track_config()
                try:
                    track_config = self.config_loader.get_track_config(track_name)
                    # Use deg_soft/deg_medium/deg_hard (not deg_rate_*)
                    self.input_panel.set_degradation('soft', track_config.deg_soft)
                    self.input_panel.set_degradation('medium', track_config.deg_medium)
                    self.input_panel.set_degradation('hard', track_config.deg_hard)
                    
                    trained_info = " [已訓練數據]" if track_config.trained_from_data else " [預設值]"
                    self.status_bar.showMessage(f"已載入 {track_name} 賽道預設衰減值{trained_info}")
                except Exception as track_e:
                    print(f"[MAIN_WINDOW] Failed to load track config for {track_name}: {track_e}")
                    self.status_bar.showMessage(f"無法載入 {track_name} 的賽道配置")
                    
            # '手動輸入' does nothing - user controls the values
            
        except Exception as e:
            print(f"[MAIN_WINDOW] Error handling deg source change: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_driver_selected(self, driver_code: str, fp2_position: int):
        """
        Handle driver selection from FP2→Q prediction tab.
        
        Auto-sets the starting position in input panel based on 
        the current selection mode (FP2 or Q ranking).
        
        Args:
            driver_code: 3-letter driver code (e.g., 'VER', 'LEC')
            fp2_position: FP2 predicted qualifying position (1-20)
        """
        try:
            # Determine which position to use based on selection mode
            driver_mode = self.input_panel.opponent_mode_combo.currentIndex()
            
            if driver_mode == 1 and hasattr(self, 'fp2_tab'):
                # Q mode: look up actual Q rank from predictions
                predictions = self.fp2_tab.get_all_predictions()
                actual_q_rank = None
                for pred in predictions:
                    if pred.get("driver") == driver_code:
                        actual_q_rank = pred.get("actual_q_rank")
                        break
                
                if actual_q_rank is not None:
                    position = actual_q_rank
                    mode_text = "Q 排位"
                else:
                    position = fp2_position
                    mode_text = "FP2 預測 (無 Q 數據)"
            else:
                # FP2 mode or Manual mode
                position = fp2_position
                mode_text = "FP2 預測"
            
            # Set starting position in input panel
            self.input_panel.start_position_spin.setValue(max(1, min(20, position)))
            
            # Update the driver selection combo in input panel
            if hasattr(self.input_panel, 'primary_opponent_combo'):
                idx = self.input_panel.primary_opponent_combo.findText(driver_code)
                if idx >= 0:
                    self.input_panel.primary_opponent_combo.setCurrentIndex(idx)
                    print(f"[MAIN_WINDOW] Updated input_panel driver combo to {driver_code}")
            
            # Update the sim_start_pos_spin as well
            if hasattr(self.input_panel, 'sim_start_pos_spin'):
                self.input_panel.sim_start_pos_spin.setValue(max(1, min(20, position)))
            
            # Update FP2 status label with mode info
            if hasattr(self.input_panel, 'fp2_status_label'):
                self.input_panel.fp2_status_label.setText(
                    f"✅ 已選擇: {driver_code} (P{position}) - {mode_text}"
                )
                self.input_panel.fp2_status_label.setStyleSheet(
                    "padding: 4px; background-color: #E8F5E9; "
                    "border-radius: 3px; color: #2E7D32; font-size: 11px;"
                )
            
            # Update status bar
            self.status_bar.showMessage(
                f"已選擇 {driver_code} - {mode_text} P{position}，起跑位置已設為 P{position}"
            )
            
            print(f"[MAIN_WINDOW] Driver selected: {driver_code} at P{position} ({mode_text})", flush=True)
            
            # Update full race tab with selected driver
            if hasattr(self, 'full_race_tab'):
                self.full_race_tab.set_our_driver(driver_code)
            
            # Store selected driver for later use
            self._selected_driver = driver_code
            self._selected_position = position
            
        except Exception as e:
            print(f"[MAIN_WINDOW] Error setting driver position: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_q_data_available(self, has_q_data: bool):
        """
        Handle Q data availability notification from FP2→Q tab.
        
        Updates input panel to show whether actual Q results are available
        for the "使用 Q 排位" mode.
        
        Args:
            has_q_data: True if actual Q results are available
        """
        print(f"[MAIN_WINDOW] Q 數據可用性更新: {has_q_data}", flush=True)
        
        if hasattr(self.input_panel, '_update_fp2_status'):
            self.input_panel._update_fp2_status(has_q_data=has_q_data)
    
    def _on_full_race_requested(self, params: dict):
        """
        Handle full race simulation request from FullRaceTab.
        
        Args:
            params: Dict with 'iterations' key
        """
        print(f"[MAIN_WINDOW] ====== FULL RACE SIMULATION REQUESTED ======")
        print(f"[MAIN_WINDOW] Request params: {params}")
        print(f"[MAIN_WINDOW] Has _current_params: {hasattr(self, '_current_params')}")
        print(f"[MAIN_WINDOW] Has _current_results: {hasattr(self, '_current_results')}")
        if hasattr(self, '_current_results'):
            print(f"[MAIN_WINDOW] Current results count: {len(self._current_results)}")
        
        try:
            from strategy_simulator.core.race_simulator import FullRaceSimulator
            
            # Get simulation parameters - 先嘗試 _current_params，再嘗試 full_race_tab 緩存
            sim_params = None
            if hasattr(self, '_current_params') and self._current_params:
                sim_params = self._current_params
                print(f"[MAIN_WINDOW] Using _current_params")
            elif hasattr(self.full_race_tab, '_cached_params') and self.full_race_tab._cached_params:
                sim_params = self.full_race_tab._cached_params
                print(f"[MAIN_WINDOW] Using full_race_tab._cached_params")
            
            if not sim_params:
                error_msg = "請先配置模擬參數並執行策略優化"
                print(f"[MAIN_WINDOW] ❌ ERROR: {error_msg}")
                self.status_bar.showMessage(error_msg)
                if hasattr(self.full_race_tab, 'status_label'):
                    self.full_race_tab.status_label.setText(error_msg)
                    self.full_race_tab.status_label.setStyleSheet("color: #d32f2f;")
                return
            
            # Get FP2 predictions - 使用正確的方法獲取
            fp2_predictions = []
            if hasattr(self, 'fp2_tab'):
                # 使用 get_predictions_with_mode() 方法（FP2QualifyingPredictionTab 的正確接口）
                if hasattr(self.fp2_tab, 'get_predictions_with_mode'):
                    fp2_predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=False)
                    print(f"[MAIN_WINDOW] FP2 predictions from get_predictions_with_mode(): {len(fp2_predictions)}")
                # 備用：嘗試 get_all_predictions()
                elif hasattr(self.fp2_tab, 'get_all_predictions'):
                    fp2_predictions = self.fp2_tab.get_all_predictions()
                    print(f"[MAIN_WINDOW] FP2 predictions from get_all_predictions(): {len(fp2_predictions)}")
                # 備用：嘗試 _predictions 屬性
                elif hasattr(self.fp2_tab, '_predictions') and self.fp2_tab._predictions:
                    fp2_predictions = self.fp2_tab._predictions
                    print(f"[MAIN_WINDOW] FP2 predictions from _predictions: {len(fp2_predictions)}")
            
            if not fp2_predictions:
                error_msg = "請先載入 FP2→Q 預測數據"
                print(f"[MAIN_WINDOW] ❌ ERROR: {error_msg}")
                self.status_bar.showMessage(error_msg)
                if hasattr(self.full_race_tab, 'status_label'):
                    self.full_race_tab.status_label.setText(error_msg)
                    self.full_race_tab.status_label.setStyleSheet("color: #d32f2f;")
                return
            
            # Get our driver FIRST (before using it)
            our_driver = self.full_race_tab._our_driver
            if not our_driver and fp2_predictions:
                our_driver = fp2_predictions[0].get('driver', 'VER')
            print(f"[MAIN_WINDOW] Our driver: {our_driver}")
            
            # Get opponent strategies - USE MONTE CARLO BEST PLANS
            opponent_strategies = self._assign_best_plans_to_opponents(
                fp2_predictions, our_driver, sim_params.race_laps
            )
            
            # Get our strategy from SELECTED plan AND top alternatives for testing
            selected_plan_index = params.get('selected_plan_index', 0)
            our_stints = []
            strategy_pool = []  # Multiple strategies for testing
            results_source = None
            
            # 嘗試從 _current_results 獲取
            if hasattr(self, '_current_results') and self._current_results:
                results_source = self._current_results
                print(f"[MAIN_WINDOW] Using _current_results: {len(results_source)} strategies")
            # 備用：從 full_race_tab 緩存獲取
            elif hasattr(self.full_race_tab, '_cached_results') and self.full_race_tab._cached_results:
                results_source = self.full_race_tab._cached_results
                print(f"[MAIN_WINDOW] Using full_race_tab._cached_results: {len(results_source)} strategies")
            
            if results_source:
                # Get selected strategy for single simulation
                if 0 <= selected_plan_index < len(results_source):
                    selected_result = results_source[selected_plan_index]
                    our_stints = selected_result.stints
                    plan_letter = chr(65 + selected_plan_index)
                    print(f"[MAIN_WINDOW] Using selected Plan {plan_letter} for single simulation")
                else:
                    # Fallback to best
                    selected_result = results_source[0]
                    our_stints = selected_result.stints
                    print(f"[MAIN_WINDOW] Invalid plan index, using Plan A")
                
                # Get top 4 strategies for multi-simulation (Plan A-D)
                for idx, result in enumerate(results_source[:4]):
                    strategy_pool.append({
                        'name': f"Plan {chr(65 + idx)}",
                        'notation': result.get_stint_notation() if hasattr(result, 'get_stint_notation') else f"Plan {chr(65 + idx)}",
                        'stints': result.stints
                    })
                print(f"[MAIN_WINDOW] Strategy pool for testing: {[s['name'] for s in strategy_pool]}")
            else:
                error_msg = "沒有可用的策略結果"
                print(f"[MAIN_WINDOW] ❌ ERROR: {error_msg}")
                self.status_bar.showMessage(error_msg)
                if hasattr(self.full_race_tab, 'status_label'):
                    self.full_race_tab.status_label.setText(error_msg)
                    self.full_race_tab.status_label.setStyleSheet("color: #d32f2f;")
                return
            
            # Get track-specific configuration
            from strategy_simulator.data.track_config import get_track_config
            track_name = self.input_panel.get_track() if hasattr(self, 'input_panel') else "Japan"
            track_config = get_track_config(track_name)
            
            # Use track-specific SC/VSC probability and overtaking difficulty
            sc_probability = track_config.sc_probability_per_lap_pct / 100.0 * sim_params.race_laps  # Convert to per-race
            vsc_probability = track_config.vsc_probability_per_lap_pct / (track_config.sc_probability_per_lap_pct + track_config.vsc_probability_per_lap_pct)  # Ratio of VSC vs SC
            overtaking_difficulty = track_config.difficulty_coefficient
            
            print(f"[MAIN_WINDOW] Track: {track_name}")
            print(f"[MAIN_WINDOW] SC Probability: {track_config.sc_probability_per_lap_pct:.2f}%/lap -> {sc_probability:.2f} per race")
            print(f"[MAIN_WINDOW] VSC Probability: {track_config.vsc_probability_per_lap_pct:.2f}%/lap (ratio: {vsc_probability:.2f})")
            print(f"[MAIN_WINDOW] Overtaking Difficulty: {overtaking_difficulty:.2f}")
            print(f"[MAIN_WINDOW] Pit Loss Time: {track_config.pit_lane_time_loss_s:.1f}s")
            
            # Get simulation mode (moved earlier for use in simulator creation)
            simulation_mode = params.get('simulation_mode', 'complete')
            print(f"[MAIN_WINDOW] Simulation Mode: {simulation_mode}")
            
            # Create simulator with track-specific parameters
            simple_mode = simulation_mode == "simple"
            simulator = FullRaceSimulator(
                sim_params=sim_params,
                sc_probability=sc_probability,
                vsc_probability=vsc_probability,
                overtaking_difficulty=overtaking_difficulty,
                simple_mode=simple_mode,
                track_name=track_name,  # NEW: For PositionTracker
                year=self._current_year if hasattr(self, '_current_year') else 2025  # NEW
            )
            
            # ✅ Get Long Run data (與 MC 分析一致)
            long_run_data = None
            if hasattr(self, '_current_fp2_data') and self._current_fp2_data:
                long_run_data = self._current_fp2_data
                print(f"[MAIN_WINDOW] Using Long Run data for Full Race simulation")
            
            # Load drivers with Long Run data
            simulator.load_drivers(fp2_predictions, long_run_data)
            simulator.set_opponent_strategies(opponent_strategies)
            if our_driver and our_stints:
                simulator.set_our_strategy(our_driver, our_stints)
            
            # Update driver list in tab
            driver_list = [p.get('driver', '') for p in fp2_predictions]
            self.full_race_tab.set_drivers(driver_list)
            
            # Show progress
            mode_text = tr("COMPLETE_MODE", "Complete") if simulation_mode == "complete" else tr("SIMPLE_MODE", "Simple")
            self.full_race_tab.show_progress(10, f"{tr('PREPARING_SIMULATION', 'Preparing')} ({mode_text})...")
            
            # Inject SC events based on user selection
            sc_scenario = params.get('sc_scenario', 'random')
            race_laps = sim_params.race_laps
            
            if sc_scenario == 'none':
                # No SC events
                simulator.inject_sc_events([])
                print("[MAIN_WINDOW] SC Scenario: None")
            elif sc_scenario == 'early':
                # Early SC around lap 10-15
                sc_lap = max(10, race_laps // 5)
                simulator.inject_sc_events([(sc_lap, 4, False)])
                print(f"[MAIN_WINDOW] SC Scenario: Early (Lap {sc_lap})")
            elif sc_scenario == 'mid':
                # Mid SC around lap 25-30
                sc_lap = max(25, race_laps // 2)
                simulator.inject_sc_events([(sc_lap, 4, False)])
                print(f"[MAIN_WINDOW] SC Scenario: Mid (Lap {sc_lap})")
            elif sc_scenario == 'late':
                # Late SC around lap 45-50
                sc_lap = max(45, int(race_laps * 0.8))
                simulator.inject_sc_events([(sc_lap, 4, False)])
                print(f"[MAIN_WINDOW] SC Scenario: Late (Lap {sc_lap})")
            else:
                # Random SC (default - use simulator's random generation)
                print("[MAIN_WINDOW] SC Scenario: Random (50% probability)")
                # Don't inject - let simulator generate randomly
            
            # Run simulation
            iterations = params.get('iterations', 100)
            
            # Use random seed offset to ensure different results each run
            import random
            import time
            seed_offset = int(time.time() * 1000) % 10000  # Random offset based on timestamp
            
            single_result = simulator.simulate_race(seed=seed_offset)
            
            # ✅ 標記模擬模式（用於 Traffic Analysis 判斷）
            single_result._mode = simulation_mode
            
            self.full_race_tab.show_progress(50, f"{tr('RUNNING_MC_SIMULATIONS', '正在執行')} {iterations} {tr('ITERATIONS', '次統計模擬')}...")
            multi_stats = simulator.run_multiple_simulations(iterations, seed_offset=seed_offset, strategy_pool=strategy_pool)
            
            # Update tab with results
            print(f"[MAIN_WINDOW] Full race simulation completed, updating results...")
            print(f"[MAIN_WINDOW] Single result: {single_result}")
            print(f"[MAIN_WINDOW] Statistics keys: {multi_stats.keys() if isinstance(multi_stats, dict) else type(multi_stats)}")
            
            # ✅ Store simulation parameters and Long Run data in tab for report generation
            self.full_race_tab._simulation_params = sim_params
            self.full_race_tab._long_run_data = long_run_data
            
            self.full_race_tab.update_simulation_result({
                'single': single_result,
                'statistics': multi_stats
            })
            
            print(f"[MAIN_WINDOW] Results updated in full_race_tab")
            self.full_race_tab.hide_progress()
            self.status_bar.showMessage(f"完整賽事模擬完成 ({iterations} 次迭代)")
            
            # Integrate with SC scenario analysis
            # ✅ Always update SC tab with full race simulation results (User Request 2026-01-07)
            if hasattr(self, 'sc_tab'):
                # Pass field data for tire comparison
                self.sc_tab.set_field_data(fp2_predictions, opponent_strategies)
                
                # Build scenario analysis from full race simulation results
                scenario_analyses = self._build_scenario_analyses_from_full_race(
                    multi_stats, single_result, sim_params.race_laps
                )
                if scenario_analyses:
                    self.sc_tab.update_scenario_analysis(scenario_analyses, None)
                    print(f"[MAIN_WINDOW] ✅ Updated SC tab with full race scenario analysis")
                else:
                    print(f"[MAIN_WINDOW] ⚠️ No scenario analyses generated from full race")
            
            # ✅ Update other tabs after full race simulation (User Request 2026-01-07)
            print(f"[MAIN_WINDOW] Updating other tabs after full race simulation...")
            
            # Update Race Result Analysis tab with full race results
            if hasattr(self, 'result_analysis_tab'):
                # Set our driver
                self.result_analysis_tab.set_our_driver(our_driver)
                # Update with simulation results AND strategy results
                self.result_analysis_tab.update_simulation_result({
                    'single': single_result,
                    'statistics': multi_stats,
                    'strategy_results': self._current_results if hasattr(self, '_current_results') else []
                })
                print(f"[MAIN_WINDOW] ✅ Updated Race Result Analysis tab")
            
            # Update Dynamic Simulation tab with full race results
            if hasattr(self, 'simulation_tab') and hasattr(self, '_current_results'):
                # Get current strategy results for animation
                if self._current_results:
                    self.simulation_tab.set_results(self._current_results, sim_params)
                    print(f"[MAIN_WINDOW] ✅ Updated Dynamic Simulation tab")
            
            # Update Detailed Data tab with current strategy results
            if hasattr(self, 'detail_tab') and hasattr(self, '_current_results'):
                if self._current_results:
                    self.detail_tab.update_results(self._current_results)
                    print(f"[MAIN_WINDOW] ✅ Updated Detailed Data tab")
            
            # Update Lap Curves tab with current strategy results
            if hasattr(self, 'chart_tab') and hasattr(self, '_current_results'):
                if self._current_results:
                    self.chart_tab.update_results(self._current_results, sim_params)
                    print(f"[MAIN_WINDOW] ✅ Updated Lap Curves tab")
            
            # Note: SC Scenarios tab already updated above (Line 1203-1213)
            print(f"[MAIN_WINDOW] All tabs updated after full race simulation")
            
            # Report buttons are now in full_race_tab's strategy performance table
            # User can click on Report button to see detailed analysis
            print(f"[MAIN_WINDOW] Complete mode finished - reports available in strategy table")
            
            self.status_bar.showMessage("完整賽事模擬完成 - 點擊策略表中的 Report 按鈕查看詳細分析")
            
        except Exception as e:
            print(f"[MAIN_WINDOW] Full race simulation error: {e}")
            import traceback
            traceback.print_exc()
            self.status_bar.showMessage(f"模擬錯誤: {str(e)}")
    
    def _auto_assign_opponent_strategies(
        self,
        fp2_predictions: list,
        race_laps: int,
        existing_strategies: dict
    ) -> dict:
        """
        Auto-assign strategies to all drivers based on their grid position.
        
        Front runners get aggressive strategies, back markers get conservative ones.
        Respects any manually-set strategies from the Opponents tab.
        
        Args:
            fp2_predictions: FP2->Q predictions for all drivers
            race_laps: Total race laps
            existing_strategies: Already set strategies from OpponentTab
            
        Returns:
            Dict mapping driver_code to strategy settings
        """
        from strategy_simulator.core.opponent_strategy_predictor import (
            OpponentStrategyPredictor
        )
        
        predictor = OpponentStrategyPredictor()
        
        # Auto-assign based on grid position
        auto_strategies = predictor.auto_assign_strategies_by_position(
            fp2_predictions=fp2_predictions,
            race_laps=race_laps,
            track_type="normal",  # Could be parameterized
            tire_deg_level="medium"  # Could come from Long Run analysis
        )
        
        # Merge: existing manual overrides take precedence
        merged = {}
        for driver_code, auto_strat in auto_strategies.items():
            if driver_code in existing_strategies:
                # Use manually set strategy
                merged[driver_code] = existing_strategies[driver_code]
            else:
                # Use auto-assigned strategy
                merged[driver_code] = {
                    'tire_sequence': auto_strat.tire_sequence,
                    'num_stops': auto_strat.num_stops,
                    'pit_laps': auto_strat.pit_laps,
                    'is_auto': True,
                }
        
        # Print summary
        print(f"[MAIN_WINDOW] Auto-assigned strategies for {len(merged)} drivers:")
        print(predictor.get_strategy_summary())
        
        # Store for later use (blocking analysis, SC tab, etc.)
        self._auto_assigned_strategies = auto_strategies
        
        # Update comparison tab with auto-assigned strategies for blocking analysis
        if hasattr(self, 'comparison_tab'):
            self.comparison_tab.set_opponent_strategies(auto_strategies)
        
        # Update opponent tab to display the auto-assigned strategies
        if hasattr(self, 'opponent_tab') and self.opponent_tab:
            if hasattr(self.opponent_tab, 'strategy_panel') and self.opponent_tab.strategy_panel:
                self.opponent_tab.strategy_panel.display_auto_assigned_strategies(auto_strategies)
        
        return merged
    
    def _quick_mc_for_driver(
        self, 
        driver_code: str, 
        grid_position: int,
        candidate_strategies: list,
        iterations: int,
        sim_params: SimulationParams,
        fp2_predictions: list,
        opponent_strategies: dict,
        long_run_data=None
    ) -> dict:
        """
        Run lightweight Monte Carlo for one driver to find their best strategy.
        
        Args:
            driver_code: Driver code (e.g., "VER")
            grid_position: Starting position (1-20)
            candidate_strategies: List of StrategySimulationResult to test
            iterations: MC iterations (dynamically calculated based on grid position)
            sim_params: Race parameters
            fp2_predictions: FP2 predictions for all drivers
            opponent_strategies: Current opponent strategy assignments
            long_run_data: FP2 long run data
            
        Returns:
            dict with 'tire_sequence', 'num_stops', 'note', 'win_rate'
        """
        # Note: CompetitiveMonteCarloSimulator and MonteCarloParams 
        # are already imported at the top of this file
        
        print(f"[QUICK_MC] Optimizing {driver_code} (P{grid_position}): "
              f"{len(candidate_strategies)} strategies × {iterations} iterations")
        
        # Create simplified MC params
        mc_params = MonteCarloParams(
            iterations=iterations,
            sc_probability_per_lap=1.5,
            vsc_probability_per_lap=2.0,
        )
        
        # Create competitive MC simulator
        competitive_mc = CompetitiveMonteCarloSimulator(
            sim_params=sim_params,
            mc_params=mc_params,
            fp2_predictions=fp2_predictions,
            opponent_strategies=opponent_strategies,
            long_run_data=long_run_data,
        )
        
        # Set this driver as "our driver" temporarily
        competitive_mc.set_our_driver(driver_code, grid_position)
        
        # Progress callback for UI responsiveness during long simulations
        def quick_progress_callback(current, total):
            if current % 10 == 0:  # Update every 10 iterations
                QApplication.processEvents()
        
        # Run MC simulation with progress callback
        mc_summary = competitive_mc.run_simulation(
            candidate_strategies, 
            progress_callback=quick_progress_callback
        )
        
        # Find best strategy by win rate from CompetitiveMCSummary
        # CompetitiveMCSummary uses strategy_summaries dict with CompetitiveStrategySummary objects
        best_strategy = None
        best_win_rate = 0.0
        all_tested_strategies = []  # ✅ Store all tested strategies for GUI display
        
        for idx, result in enumerate(candidate_strategies):
            strategy_name = result.strategy_name
            # Access win_probability from strategy_summaries
            if strategy_name in mc_summary.strategy_summaries:
                strat_summary = mc_summary.strategy_summaries[strategy_name]
                win_rate = strat_summary.win_probability
                avg_pos = strat_summary.mean_finish_position
            else:
                win_rate = 0.0
                avg_pos = 20.0
            
            # Store strategy info
            all_tested_strategies.append({
                'name': strategy_name,
                'win_rate': win_rate,
                'avg_pos': avg_pos,
            })
            
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_strategy = result
        
        if not best_strategy:
            best_strategy = candidate_strategies[0]  # Fallback to first
        
        # Convert to opponent strategy format
        # Compound is an Enum, use short_name() to get 'S', 'M', 'H'
        tire_sequence = []
        for stint in best_strategy.stints:
            if hasattr(stint.compound, 'short_name'):
                tire_sequence.append(stint.compound.short_name())
            elif hasattr(stint.compound, 'value'):
                tire_sequence.append(stint.compound.value[0])
            else:
                tire_sequence.append(str(stint.compound)[0])
        
        print(f"[QUICK_MC] {driver_code} best: {'-'.join(tire_sequence)} "
              f"(Win rate: {best_win_rate:.1f}%)")
        
        return {
            'tire_sequence': tire_sequence,
            'num_stops': len(tire_sequence) - 1,
            'note': f'P{grid_position} Quick MC: {"-".join(tire_sequence)}',
            'win_rate': best_win_rate,
            'all_tested_strategies': all_tested_strategies,  # ✅ Include all tested strategies
        }
    
    def _assign_best_plans_to_opponents(
        self,
        fp2_predictions: list,
        our_driver: str,
        race_laps: int
    ) -> dict:
        """
        Assign best strategies to opponents from Monte Carlo results.
        
        Logic:
        - Each opponent gets assigned the strategy (Plan A/B/C) with highest
          win probability or best finishing position from our optimization results
        - This makes the simulation more challenging and realistic
        
        Args:
            fp2_predictions: FP2->Q predictions for all drivers
            our_driver: Our driver code
            race_laps: Total race laps
            
        Returns:
            Dict mapping driver_code to strategy settings
        """
        opponent_strategies = {}
        
        if not hasattr(self, '_current_results') or not self._current_results:
            print("[MAIN_WINDOW] No optimization results, using default strategies")
            return opponent_strategies
        
        results = self._current_results
        
        # ✅ Assign optimal strategies based on grid position
        # Each driver gets strategy that maximizes their chance from their starting position
        
        # Sort FP2 predictions by rank (grid position)
        sorted_preds = sorted(fp2_predictions, key=lambda p: p.get('rank', 20))
        
        strategy_distribution = []
        for pred in sorted_preds:
            driver_code = pred.get('driver', '')
            if driver_code and driver_code != our_driver:
                driver_rank = pred.get('rank', 20)
                
                # Front runners (P1-P3): Use fastest strategy to defend position
                if driver_rank <= 3:
                    selected_plan = results[0]  # Plan A (fastest)
                    strategy_note = "Defending"
                
                # Upper midfield (P4-P7): Use strategies with high podium probability
                elif driver_rank <= 7:
                    candidates = results[:min(3, len(results))]
                    if hasattr(results[0], 'podium_probability'):
                        selected_plan = max(candidates, key=lambda r: getattr(r, 'podium_probability', 0))
                    else:
                        selected_plan = candidates[min(1, len(candidates)-1)]
                    strategy_note = "Podium push"
                
                # Lower midfield (P8-P12): Use strategies maximizing position gain
                elif driver_rank <= 12:
                    candidates = results[:min(5, len(results))]
                    if hasattr(results[0], 'avg_positions_gained'):
                        selected_plan = max(candidates, key=lambda r: getattr(r, 'avg_positions_gained', 0))
                    else:
                        selected_plan = candidates[min(2, len(candidates)-1)]
                    strategy_note = "Points hunt"
                
                # Back midfield (P13-P17): Use diverse strategies
                elif driver_rank <= 17:
                    strategy_idx = (driver_rank - 13) % min(5, len(results))
                    selected_plan = results[strategy_idx]
                    strategy_note = "Mixed"
                
                # Backmarkers (P18-P20): Use aggressive strategies
                else:
                    selected_plan = results[min(3, len(results)-1)]
                    strategy_note = "Aggressive"
                
                # Extract tire sequence
                if hasattr(selected_plan, 'stints'):
                    tire_sequence = [s.compound.value[0] for s in selected_plan.stints]
                else:
                    tire_sequence = ['M', 'H']
                
                opponent_strategies[driver_code] = {
                    'tire_sequence': tire_sequence,
                    'num_stops': len(tire_sequence) - 1,
                    'is_auto': True,
                    'note': f'P{driver_rank}: {"-".join(tire_sequence)}'
                }
                
                strategy_distribution.append(f"{driver_code}(P{driver_rank})={"-".join(tire_sequence)}")
        
        print(f"[MAIN_WINDOW] Assigned diverse strategies to {len(opponent_strategies)} opponents")
        print(f"[MAIN_WINDOW] Strategy distribution: {', '.join(strategy_distribution[:5])}...")
        
        return opponent_strategies
    
    def _on_opponent_strategy_changed(self):
        """
        Handle opponent strategy settings change.
        
        Retrieves updated opponent strategies from OpponentTab and
        passes them to Strategy Comparison tab for blocking analysis.
        """
        try:
            # Get opponent strategies from OpponentTab
            opponent_strategies = self.opponent_tab.get_opponent_strategies()
            
            if opponent_strategies:
                # Convert to format expected by StrategyComparisonTab
                # Import OpponentStrategyPredictor to calculate pit laps
                from strategy_simulator.core.opponent_strategy_predictor import (
                    OpponentStrategyPredictor
                )
                
                # Get race laps from current params if available
                race_laps = 53  # Default
                if hasattr(self, '_current_params') and self._current_params:
                    race_laps = self._current_params.race_laps
                
                predictor = OpponentStrategyPredictor(race_laps=race_laps)
                predicted_strategies = predictor.predict_all_opponents(opponent_strategies)
                
                # Pass to comparison tab
                self.comparison_tab.set_opponent_strategies(predicted_strategies)
                
                print(f"[MAIN_WINDOW] Updated opponent strategies: {len(predicted_strategies)} drivers")
                self.status_bar.showMessage(
                    f"對手策略已更新 - {len(predicted_strategies)} 位車手"
                )
            else:
                self.comparison_tab.set_opponent_strategies({})
                
        except Exception as e:
            print(f"[MAIN_WINDOW] Error updating opponent strategies: {e}")
    
    def _on_run_simulation(self, params: dict):
        """
        Handle simulation run request from input panel.
        
        Uses CompetitiveStrategyOptimizer to consider all 20 drivers.
        
        Args:
            params: Dictionary with simulation parameters
        """
        self.status_bar.showMessage("正在執行模擬...")
        self.simulation_started.emit()
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.detailed_status.setText("初始化...")
        QApplication.processEvents()
        
        try:
            # Build SimulationParams (10%)
            self._update_progress(10, "建構模擬參數...")
            sim_params = self._build_simulation_params(params)
            self._current_params = sim_params
            
            # Build constraints (20%)
            self._update_progress(20, "設定策略限制...")
            constraints = self._build_constraints(params)
            
            # Check if we have FP2 predictions for competitive mode
            # Use Q ranking mode if selected (driver_selection_mode == 1)
            fp2_predictions = []
            if hasattr(self, 'fp2_tab'):
                driver_mode = params.get('driver_selection_mode', 0)
                use_q_ranking = (driver_mode == 1)  # 1 = "使用 Q 排位 (自動)"
                
                if use_q_ranking and self.fp2_tab.has_actual_q_data():
                    # Use actual Q ranking
                    fp2_predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=True)
                    print("[MAIN_WINDOW] 使用實際 Q 排位數據進行模擬", flush=True)
                else:
                    # Use FP2 predicted ranking
                    fp2_predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=False)
                    if use_q_ranking:
                        print("[MAIN_WINDOW] 無實際 Q 數據，回退至 FP2 預測排位", flush=True)
            
            # Get opponent strategies from UI
            opponent_strategies = {}
            if hasattr(self, 'opponent_tab'):
                opponent_strategies = self.opponent_tab.get_opponent_strategies()
            
            # Get Long Run data for degradation
            long_run_data = None
            if hasattr(self, '_current_fp2_data') and self._current_fp2_data:
                long_run_data = self._current_fp2_data
            
            # Determine simulation mode
            use_competitive = len(fp2_predictions) >= 10 and params.get('enable_competition', True)
            
            if use_competitive:
                # Auto-assign strategies if not manually set
                self._update_progress(25, "分配對手策略...")
                opponent_strategies = self._auto_assign_opponent_strategies(
                    fp2_predictions, 
                    sim_params.race_laps,
                    opponent_strategies  # Existing manual overrides
                )
                
                # Run competitive strategy optimization (30-50%)
                self._update_progress(30, "20車手競爭模擬中...")
                print(f"[MAIN_WINDOW] Running competitive optimization with {len(fp2_predictions)} drivers")
                
                competitive_optimizer = CompetitiveStrategyOptimizer(
                    sim_params,
                    sc_probability=0.015,  # Per-lap SC probability
                    overtaking_difficulty=params.get('overtaking_difficulty', 0.5),
                )
                
                # Load driver data
                competitive_optimizer.load_driver_data(
                    fp2_predictions=fp2_predictions,
                    long_run_data=long_run_data,
                    opponent_strategies=opponent_strategies,
                )
                
                # Set our driver
                our_driver = params.get('selected_driver', 'VER')
                our_grid_position = params.get('driver_start_position', None)
                competitive_optimizer.set_our_driver(our_driver, our_grid_position)
                
                self._update_progress(40, "模擬比賽位置...")
                
                # Run competitive optimization
                competitive_results = competitive_optimizer.optimize(
                    constraints,
                    top_n=10,
                    simulation_iterations=params.get('competitive_iterations', 100),
                )
                
                # Extract base results and store competitive data
                results = [cr.strategy_result for cr in competitive_results]
                self._competitive_results = competitive_results
                
                # Log position predictions
                for cr in competitive_results[:3]:
                    print(f"[MAIN_WINDOW] {cr.strategy_result.strategy_name}: "
                          f"P{cr.predicted_finish_position} "
                          f"(+{cr.positions_gained} positions, "
                          f"podium {cr.podium_probability:.0%})")
                
                self._update_progress(50, f"已找到 {len(results)} 種策略 (含位置預測)")
                
            else:
                # Fallback: Run single-driver optimization (30-50%)
                self._update_progress(30, "優化策略中...")
                print("[MAIN_WINDOW] Running single-driver optimization (no FP2 data)")
                
                optimizer = StrategyOptimizer(sim_params)
                results = optimizer.find_optimal_strategies(constraints, top_n=10)
                self._competitive_results = None
                
                self._update_progress(50, f"已找到 {len(results)} 種策略")
            
            self._current_results = results
            
            # Update all tabs (60%)
            self._update_progress(60, "更新顯示...")
            self._update_all_tabs(results, sim_params)
            
            # Set report context for strategy analysis reports
            our_driver = params.get('selected_driver', 'VER')
            grid_position = params.get('driver_start_position', 1)
            track_name = params.get('track', 'Unknown')
            self.comparison_tab.set_report_context(
                our_driver=our_driver,
                grid_position=grid_position if grid_position else 1,
                track_name=track_name,
                race_laps=sim_params.race_laps,
                pit_loss=sim_params.pit_loss_green,
                simulation_data=None  # Will be updated after full race simulation
            )
            
            # Pass SC events to SimulationTab for visualization
            sc_mode = params.get('sc_mode', 'none')
            sc_events = params.get('sc_events', [])
            if sc_mode == 'manual' and sc_events:
                self.simulation_tab.set_sc_events(sc_events)
            
            # Trigger opponent strategy update for blocking analysis (70%)
            if hasattr(self, 'opponent_tab'):
                self._update_progress(70, "分析對手阻擋...")
                self._on_opponent_strategy_changed()
            
            # Run SC Scenario analysis if enabled (85%)
            # Check new sc_mode parameter or legacy enable_sc_scenario
            sc_scenario_enabled = (
                sc_mode == 'manual' and sc_events or 
                params.get('enable_sc_scenario', False)
            )
            if sc_scenario_enabled:
                self._update_progress(80, "SC 場景分析中...")
                self._run_sc_scenario_analysis(results, sim_params, params)
            
            # Run Monte Carlo if enabled (95%)
            if params.get('run_monte_carlo', False):
                mc_iterations = params.get('mc_iterations', 1000)
                self._update_progress(85, f"Monte Carlo 模擬中 (0/{mc_iterations})...")
                self._run_monte_carlo(results, sim_params, params)
            
            # Complete (100%)
            self._update_progress(100, "完成!")
            
            self.status_bar.showMessage(
                f"模擬完成 - 找到 {len(results)} 種策略"
            )
            self.simulation_completed.emit(results)
            
            # Auto switch to SC 場景 tab (index 1, after FP2→Q)
            self.right_tabs.setCurrentIndex(1)
            
            # Hide progress bar after completion
            self.progress_bar.setVisible(False)
            self.detailed_status.setText("")
            
        except Exception as e:
            print(f"[MAIN_WINDOW] Simulation error: {e}")
            QMessageBox.critical(
                self, "模擬錯誤",
                f"無法執行模擬: {e}"
            )
            self.status_bar.showMessage("模擬失敗")
            self.progress_bar.setVisible(False)
            self.detailed_status.setText("")
    
    def _update_progress(self, value: int, message: str):
        """
        Update progress bar and detailed status.
        
        Args:
            value: Progress value (0-100)
            message: Status message to display
        """
        self.progress_bar.setValue(value)
        self.detailed_status.setText(message)
        QApplication.processEvents()
    
    def _build_simulation_params(self, params: dict) -> SimulationParams:
        """Build SimulationParams from input dict."""
        # Get track config if available
        track_name = params.get('track', 'Default')
        track_config = None
        
        if self.config_loader:
            track_config = self.config_loader.get_track_config(track_name)
        
        # Build degradation rates from Long Run data or manual input
        deg_rates = {
            Compound.SOFT: params.get('soft_deg', 0.120),
            Compound.MEDIUM: params.get('medium_deg', 0.080),
            Compound.HARD: params.get('hard_deg', 0.045),
        }
        
        # Build degradation acceleration from FP2 data or trained data
        if hasattr(self, '_current_fp2_data') and self._current_fp2_data:
            # Use FP2 calculated acceleration (most accurate for this race)
            fp2 = self._current_fp2_data
            deg_acceleration = {
                Compound.SOFT: fp2.get_deg_acceleration('SOFT'),
                Compound.MEDIUM: fp2.get_deg_acceleration('MEDIUM'),
                Compound.HARD: fp2.get_deg_acceleration('HARD'),
            }
            print(f"[MAIN_WINDOW] Using FP2 deg_acceleration: S={deg_acceleration[Compound.SOFT]:.5f}, "
                  f"M={deg_acceleration[Compound.MEDIUM]:.5f}, H={deg_acceleration[Compound.HARD]:.5f}")
        elif track_config and track_config.trained_from_data:
            deg_acceleration = {
                Compound.SOFT: track_config.deg_accel_soft,
                Compound.MEDIUM: track_config.deg_accel_medium,
                Compound.HARD: track_config.deg_accel_hard,
            }
        else:
            # Default values (corrected formula coefficients)
            deg_acceleration = {
                Compound.SOFT: 0.0029,
                Compound.MEDIUM: 0.0019,
                Compound.HARD: 0.0012,
            }
        
        # Compound deltas
        compound_deltas = {
            Compound.SOFT: params.get('soft_delta', -0.8),
            Compound.MEDIUM: 0.0,
            Compound.HARD: params.get('hard_delta', 0.5),
        }
        
        # Pit loss values
        if track_config:
            pit_green = track_config.pit_loss_green
            pit_sc = track_config.pit_loss_sc
            pit_vsc = track_config.pit_loss_vsc
        else:
            pit_green = params.get('pit_loss_green', 24.0)
            pit_sc = params.get('pit_loss_sc', 12.0)
            pit_vsc = params.get('pit_loss_vsc', 9.0)
        
        return SimulationParams(
            race_laps=params.get('race_laps', 53),
            base_lap_time=params.get('base_lap_time', 91.5),
            # First lap / traffic simulation
            enable_first_lap_loss=params.get('enable_first_lap_loss', False),
            first_lap_loss=params.get('first_lap_loss', 5.0),
            enable_traffic_simulation=params.get('enable_traffic_simulation', False),
            starting_position=params.get('starting_position', 10),
            traffic_loss_per_position=params.get('traffic_loss_per_position', 0.15),
            traffic_decay_rate=params.get('traffic_decay_rate', 0.05),
            # Fuel parameters
            start_fuel_kg=params.get('start_fuel', 110.0),
            fuel_kg_per_lap=params.get('fuel_per_lap', 1.70),
            fuel_effect_coefficient=params.get('fuel_effect', 0.030),
            deg_rates=deg_rates,
            deg_acceleration=deg_acceleration,
            pit_loss_green=pit_green,
            pit_loss_sc=pit_sc,
            pit_loss_vsc=pit_vsc,
            compound_deltas=compound_deltas,
            # Pit lane congestion (Q17)
            enable_pit_congestion=params.get('enable_pit_congestion', False),
            pit_congestion_penalty=params.get('pit_congestion_penalty', 2.0),
        )
    
    def _build_constraints(self, params: dict) -> StrategyConstraints:
        """Build StrategyConstraints from input dict."""
        # Parse mandatory compounds
        mandatory = []
        if params.get('must_use_soft', False):
            mandatory.append(Compound.SOFT)
        if params.get('must_use_medium', False):
            mandatory.append(Compound.MEDIUM)
        if params.get('must_use_hard', False):
            mandatory.append(Compound.HARD)
        
        # Available compounds
        available = []
        if params.get('allow_soft', True):
            available.append(Compound.SOFT)
        if params.get('allow_medium', True):
            available.append(Compound.MEDIUM)
        if params.get('allow_hard', True):
            available.append(Compound.HARD)
        
        return StrategyConstraints(
            mandatory_compounds=mandatory if mandatory else None,
            available_compounds=available if available else None,
            min_stint_length=params.get('min_stint', 5),
            max_stint_length=params.get('max_stint', 45),
            min_stops=params.get('min_stops', 1),
            max_stops=params.get('max_stops', 3),
        )
    
    def _update_all_tabs(self, results: list, params: SimulationParams):
        """Update all result tabs with new data."""
        # Get track config for blocking analysis
        track_config = getattr(self, '_current_track_config', None)
        
        # Get competitive results if available
        competitive_results = getattr(self, '_competitive_results', None)
        
        self.comparison_tab.update_results(
            results, 
            track_config=track_config,
            competitive_results=competitive_results
        )
        self.chart_tab.update_results(results, params)
        self.sc_tab.update_results(results, params)
        self.detail_tab.update_results(results)
        self.opponent_tab.update_results(results, params)
        
        # Update simulation tab (new dynamic visualization)
        self.simulation_tab.set_results(results, params)
        
        # Update full race tab with strategies for manual selection
        if hasattr(self, 'full_race_tab'):
            self.full_race_tab.set_strategies(results, params)  # ✅ 傳遞 params
    
    def _run_sc_scenario_analysis(self, results: list, sim_params: SimulationParams,
                                   input_params: dict):
        """
        Run SC scenario analysis - what happens if SC appears on a specific lap.
        
        1. Recalculates all strategies assuming SC/VSC at specified lap
        2. Shows new rankings and time changes
        3. Recommends which strategies benefit from SC
        
        Supports both new SCEventInjectorWidget format (sc_events list) and
        legacy format (enable_sc_scenario with individual params).
        """
        try:
            from strategy_simulator.core.lap_simulator import LapSimulator, Stint
            
            # Check for new format first (from SCEventInjectorWidget)
            sc_events = input_params.get('sc_events', [])
            
            if sc_events:
                # New format: use first event
                first_event = sc_events[0]
                sc_lap = first_event[0]
                sc_duration = first_event[1]
                is_vsc = first_event[2]
            else:
                # Legacy format
                sc_lap = input_params.get('sc_scenario_lap', 20)
                sc_duration = input_params.get('sc_scenario_duration', 4)
                is_vsc = input_params.get('sc_scenario_is_vsc', False)
            
            pit_loss_normal = sim_params.pit_loss_green
            pit_loss_sc = sim_params.pit_loss_vsc if is_vsc else sim_params.pit_loss_sc
            pit_saving = pit_loss_normal - pit_loss_sc
            
            race_laps = sim_params.race_laps
            remaining_laps = race_laps - sc_lap
            
            sc_type = "VSC" if is_vsc else "SC"
            
            # ============================================================
            # RECALCULATE ALL STRATEGIES WITH SC AT SPECIFIED LAP
            # ============================================================
            simulator = LapSimulator(sim_params)
            sc_results = []
            
            for orig_result in results[:10]:
                # Deep copy stints
                stints_copy = []
                for s in orig_result.stints:
                    stints_copy.append(Stint(
                        compound=s.compound,
                        laps=s.laps,
                        start_lap=s.start_lap
                    ))
                
                # Simulate with SC
                sc_result = simulator.simulate_strategy_with_sc(
                    stints=stints_copy,
                    sc_lap=sc_lap,
                    sc_duration=sc_duration,
                    is_vsc=is_vsc,
                    name=orig_result.strategy_name
                )
                
                # Store original time for comparison
                sc_result.original_time = orig_result.total_time
                sc_result.original_rank = results.index(orig_result) + 1
                sc_result.notation = orig_result.get_stint_notation()
                
                sc_results.append(sc_result)
            
            # Sort by new total time
            sc_results.sort(key=lambda r: r.total_time)
            
            # Calculate new rankings and deltas
            best_time = sc_results[0].total_time if sc_results else 0
            
            for new_rank, r in enumerate(sc_results, 1):
                r.new_rank = new_rank
                r.rank_change = r.original_rank - new_rank  # Positive = improved
                r.time_saved = r.original_time - r.total_time  # Positive = faster
                r.gap_to_best = r.total_time - best_time
            
            # ============================================================
            # BUILD ANALYSIS HTML
            # ============================================================
            analysis_lines = [
                f"<h3>{sc_type} 場景勝率重算</h3>",
                f"<p><b>假設:</b> {sc_type} 在第 {sc_lap} 圈出現，持續 {sc_duration} 圈</p>",
                f"<p><b>Pit 節省:</b> {pit_saving:.1f}s ({pit_loss_normal:.1f}s → {pit_loss_sc:.1f}s)</p>",
                f"<p><b>SC 窗口:</b> L{sc_lap}-L{sc_lap + sc_duration - 1}</p>",
                "<hr>",
            ]
            
            # Strategy ranking table
            analysis_lines.append("<h4>策略排名變化:</h4>")
            analysis_lines.append("<table border='1' cellpadding='4' cellspacing='0' style='border-collapse: collapse;'>")
            analysis_lines.append("<tr style='background-color: #e0e0e0;'>")
            analysis_lines.append("<th>新排名</th><th>策略</th><th>原排名</th><th>排名變化</th><th>節省時間</th><th>與最佳差距</th><th>SC進站</th>")
            analysis_lines.append("</tr>")
            
            for r in sc_results[:10]:
                # Rank change styling
                if r.rank_change > 0:
                    rank_style = "color: green; font-weight: bold;"
                    rank_symbol = f"↑{r.rank_change}"
                elif r.rank_change < 0:
                    rank_style = "color: red;"
                    rank_symbol = f"↓{abs(r.rank_change)}"
                else:
                    rank_style = ""
                    rank_symbol = "-"
                
                # Time saved styling
                if r.time_saved > 0.5:
                    time_style = "color: green;"
                    time_text = f"+{r.time_saved:.2f}s"
                elif r.time_saved < -0.5:
                    time_style = "color: red;"
                    time_text = f"{r.time_saved:.2f}s"
                else:
                    time_style = ""
                    time_text = f"{r.time_saved:+.2f}s"
                
                # SC pits
                sc_pits = getattr(r, 'sc_pits', 0)
                pit_text = f"{sc_pits}" if sc_pits > 0 else "-"
                pit_style = "color: green; font-weight: bold;" if sc_pits > 0 else ""
                
                analysis_lines.append(
                    f"<tr>"
                    f"<td><b>{r.new_rank}</b></td>"
                    f"<td>{r.notation}</td>"
                    f"<td>{r.original_rank}</td>"
                    f"<td style='{rank_style}'>{rank_symbol}</td>"
                    f"<td style='{time_style}'>{time_text}</td>"
                    f"<td>+{r.gap_to_best:.2f}s</td>"
                    f"<td style='{pit_style}'>{pit_text}</td>"
                    f"</tr>"
                )
            
            analysis_lines.append("</table>")
            
            # Summary
            benefited = [r for r in sc_results if r.rank_change > 0]
            hurt = [r for r in sc_results if r.rank_change < 0]
            
            analysis_lines.append("<hr>")
            analysis_lines.append("<h4>摘要:</h4>")
            
            if benefited:
                analysis_lines.append(f"<p style='color: green;'><b>受益策略:</b> {', '.join([r.notation for r in benefited])}</p>")
            if hurt:
                analysis_lines.append(f"<p style='color: red;'><b>受損策略:</b> {', '.join([r.notation for r in hurt])}</p>")
            
            # Best strategy change
            orig_best = results[0].get_stint_notation() if results else "N/A"
            new_best = sc_results[0].notation if sc_results else "N/A"
            
            if orig_best != new_best:
                analysis_lines.append(
                    f"<p><b>最佳策略變化:</b> {orig_best} → <span style='color: green;'>{new_best}</span></p>"
                )
            else:
                analysis_lines.append(f"<p><b>最佳策略:</b> {new_best} (不變)</p>")
            
            # ============================================================
            # Q18: DECISION ADVICE SECTION
            # ============================================================
            analysis_lines.append("<hr>")
            analysis_lines.append("<h4>決策建議:</h4>")
            
            # Calculate expected position change if we pit vs stay out
            pit_advantage = pit_saving  # Time saved by pitting during SC
            
            # Determine which strategies should pit during SC
            should_pit = []
            should_stay = []
            for r in sc_results[:5]:
                sc_pits = getattr(r, 'sc_pits', 0)
                # If strategy benefits (rank improved) and used SC pit
                if r.rank_change > 0 and sc_pits > 0:
                    should_pit.append(r.notation)
                elif r.rank_change <= 0:
                    should_stay.append(r.notation)
            
            # Decision advice based on tire age and remaining laps
            advice_items = []
            
            # Tire condition advice
            if remaining_laps <= 15:
                advice_items.append("剩餘圈數較少，考慮換上軟胎衝刺")
            elif remaining_laps <= 25:
                advice_items.append("中等剩餘圈數，中性胎是安全選擇")
            else:
                advice_items.append("剩餘圈數較多，考慮硬胎以確保完賽")
            
            # Track position advice based on overtaking difficulty
            track_config = getattr(self, '_current_track_config', None)
            if track_config:
                overtaking = track_config.overtaking_difficulty
                if overtaking > 0.7:
                    advice_items.append("賽道超車困難，保持位置比速度更重要")
                elif overtaking < 0.3:
                    advice_items.append("賽道容易超車，可接受暫時掉位")
            
            # Pit window advice
            if pit_saving > 10:
                advice_items.append(f"SC 進站可節省 {pit_saving:.1f}s，強烈建議進站")
            elif pit_saving > 5:
                advice_items.append(f"SC 進站可節省 {pit_saving:.1f}s，建議評估進站")
            
            for advice in advice_items:
                analysis_lines.append(f"<p>• {advice}</p>")
            
            # Final recommendation
            if should_pit:
                analysis_lines.append(
                    f"<p style='background-color: #e8f4e8; padding: 8px; border-radius: 5px;'>"
                    f"<b>建議進站策略:</b> {', '.join(should_pit[:3])}</p>"
                )
            
            # Show analysis in SC tab
            analysis_html = "\n".join(analysis_lines)
            
            if hasattr(self.sc_tab, 'update_sc_scenario'):
                self.sc_tab.update_sc_scenario(
                    analysis_html, sc_lap, sc_duration, is_vsc,
                    sc_results=sc_results  # Pass recalculated results
                )
            
            print(f"[MAIN_WINDOW] SC scenario analysis completed for L{sc_lap} - "
                  f"Benefited: {len(benefited)}, Hurt: {len(hurt)}")
            
        except Exception as e:
            import traceback
            print(f"[MAIN_WINDOW] SC scenario analysis error: {e}")
            traceback.print_exc()
            
        except Exception as e:
            print(f"[MAIN_WINDOW] SC scenario analysis error: {e}")
    
    def _run_monte_carlo(self, results: list, sim_params: SimulationParams, 
                         input_params: dict):
        """Run Monte Carlo simulation with 20-driver competition."""
        try:
            # Get top strategies for Monte Carlo
            top_results = results[:5]
            strategy_names = [r.strategy_name for r in top_results]
            
            mc_iterations = input_params.get('mc_iterations', 1000)
            starting_position = input_params.get('starting_position', 10)
            our_driver = input_params.get('selected_driver', 'VER')
            
            print(f"[MAIN_WINDOW] === RUNNING MONTE CARLO SIMULATION ===")
            print(f"[MAIN_WINDOW] Driver: {our_driver} starting P{starting_position}")
            print(f"[MAIN_WINDOW] Strategies: {strategy_names}")
            
            # ✅ 根據模式選擇迭代次數
            # 先檢查是否有足夠的 FP2 預測數據（≥10 位車手）來判斷模式
            has_competitive_data = False
            if hasattr(self, 'fp2_tab'):
                test_predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=False)
                has_competitive_data = len(test_predictions) >= 10
            
            if has_competitive_data:
                # 競爭模式：使用競爭迭代次數（預設 1000）
                mc_iterations = input_params.get('competitive_iterations', input_params.get('mc_iterations', 1000))
                mode_name = "競爭模式 (20車手)"
            else:
                # 單車手策略比較：使用策略迭代次數（預設 100）
                mc_iterations = input_params.get('strategy_iterations', input_params.get('mc_iterations', 100))
                mode_name = "策略比較模式 (單車手)"
            
            print(f"[MAIN_WINDOW] Iterations: {mc_iterations} ({mode_name})")
            
            # Check if we have FP2 predictions for competitive mode
            # Use Q ranking mode if selected
            fp2_predictions = []
            if hasattr(self, 'fp2_tab'):
                driver_mode = input_params.get('driver_selection_mode', 0)
                use_q_ranking = (driver_mode == 1)
                if use_q_ranking and self.fp2_tab.has_actual_q_data():
                    fp2_predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=True)
                else:
                    fp2_predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=False)
            
            # Get opponent strategies
            opponent_strategies = {}
            if hasattr(self, 'opponent_tab') and self.opponent_tab:
                opponent_strategies = self.opponent_tab.get_opponent_strategies()
            
            # Get Long Run data
            long_run_data = None
            if hasattr(self, '_current_fp2_data') and self._current_fp2_data:
                long_run_data = self._current_fp2_data
            
            # Decide which simulator to use
            use_competitive = len(fp2_predictions) >= 10
            
            if use_competitive:
                # ✅ NEW: Phase 1 - Optimize 19 opponents FIRST
                print(f"\n{'='*70}")
                print(f"[MAIN_WINDOW] ====== PHASE 1: Optimizing 19 opponent drivers ======")
                print(f"{'='*70}\n")
                
                opponent_best_strategies = {}
                
                # ✅ 獲取 Phase 1 迭代次數（用戶可調）
                phase1_base_iterations = input_params.get('phase1_iterations', 20)
                print(f"[MAIN_WINDOW] Phase 1 base iterations: {phase1_base_iterations}")
                
                if fp2_predictions and len(fp2_predictions) > 1:
                    # Sort by grid position
                    sorted_preds = sorted(fp2_predictions, key=lambda p: p.get('rank', 20))
                    
                    phase1_total = len([p for p in sorted_preds if p.get('driver') != our_driver])
                    phase1_current = 0
                    
                    for pred in sorted_preds:
                        driver_code = pred.get('driver', '')
                        driver_rank = pred.get('rank', 20)
                        
                        # Skip our driver (will optimize LAST in Phase 2)
                        if driver_code == our_driver:
                            print(f"[PHASE_1] Skipping {driver_code} (our driver, will optimize last)")
                            continue
                        
                        # ✅ OPTIMIZED: Dynamic iteration allocation based on grid position
                        # P1-3: 60% of Phase 1 base
                        # P4-8: 40% of Phase 1 base
                        # P9-15: 25% of Phase 1 base
                        # P16-20: 15% of Phase 1 base
                        if driver_rank <= 3:
                            # Top 3: High iterations for championship contenders
                            opt_iterations = int(phase1_base_iterations * 0.6)  # 60%
                            opt_strategies = results[:8]  # Reduced from 10 to 8
                            tier = f"High MC ({opt_iterations} iter, 60%)"
                        elif driver_rank <= 8:
                            # Upper midfield: Medium iterations
                            opt_iterations = int(phase1_base_iterations * 0.4)  # 40%
                            opt_strategies = results[:6]  # Reduced from 7 to 6
                            tier = f"Mid MC ({opt_iterations} iter, 40%)"
                        elif driver_rank <= 15:
                            # Lower midfield: Low iterations
                            opt_iterations = int(phase1_base_iterations * 0.25)  # 25%
                            opt_strategies = results[:4]  # Reduced from 5 to 4
                            tier = f"Quick MC ({opt_iterations} iter, 25%)"
                        else:
                            # Backmarkers: Minimal iterations
                            opt_iterations = int(phase1_base_iterations * 0.15)  # 15%
                            opt_strategies = results[:3]  # Only test top 3 strategies
                            tier = f"Fast MC ({opt_iterations} iter, 15%)"
                        
                        print(f"[PHASE_1] ({phase1_current+1}/{phase1_total}) "
                              f"Optimizing {driver_code} P{driver_rank}: "
                              f"{tier} ({len(opt_strategies)} strategies × {opt_iterations} iter)")
                        
                        # Update progress
                        phase1_progress = 86 + int((phase1_current / phase1_total) * 4)
                        self._update_progress(
                            phase1_progress, 
                            f"Phase 1: {driver_code} P{driver_rank} ({tier})..."
                        )
                        
                        # Run quick MC for this driver
                        best_strategy = self._quick_mc_for_driver(
                            driver_code=driver_code,
                            grid_position=driver_rank,
                            candidate_strategies=opt_strategies,
                            iterations=opt_iterations,
                            sim_params=sim_params,
                            fp2_predictions=fp2_predictions,
                            opponent_strategies=opponent_best_strategies,  # Use strategies found so far
                            long_run_data=long_run_data,
                        )
                        
                        # ✅ Add optimization details for GUI display
                        best_strategy['tier'] = tier
                        best_strategy['iterations'] = opt_iterations
                        best_strategy['tested_strategies'] = len(opt_strategies)
                        
                        opponent_best_strategies[driver_code] = best_strategy
                        phase1_current += 1
                        
                        # Allow UI to stay responsive during Phase 1
                        QApplication.processEvents()
                    
                    print(f"\n[PHASE_1] ✅ Completed! {len(opponent_best_strategies)} opponents optimized")
                    print(f"[PHASE_1] Opponent strategies:")
                    for driver_code, strategy in sorted(opponent_best_strategies.items()):
                        tire_seq = "-".join(strategy['tire_sequence'])
                        win_rate = strategy.get('win_rate', 0)
                        print(f"  {driver_code}: {tire_seq} (Win: {win_rate:.1f}%)")
                    
                    # ✅ NEW: 傳遞 Phase 1 結果到 Opponent Tab 顯示
                    if hasattr(self, 'opponent_tab') and self.opponent_tab:
                        self.opponent_tab.display_phase1_results(opponent_best_strategies, fp2_predictions)
                else:
                    print("[PHASE_1] ⚠️  No FP2 predictions for opponent optimization")
                
                # ✅ NEW: Phase 2 - Optimize OUR driver LAST using known opponent strategies
                print(f"\n{'='*70}")
                print(f"[MAIN_WINDOW] ====== PHASE 2: Optimizing OUR driver ({our_driver}) ======")
                print(f"[MAIN_WINDOW] Using {len(opponent_best_strategies)} known opponent strategies")
                print(f"[MAIN_WINDOW] 🎯 OUR DRIVER GETS 100% ITERATIONS: {mc_iterations} (user-defined)")
                print(f"{'='*70}\n")
                
                self._update_progress(90, f"Phase 2: 優化 {our_driver} (100% 迭代)...")
                
                # Use Competitive Monte Carlo (20 drivers) with known opponent strategies
                self._update_progress(91, "20車手競爭 Monte Carlo 中...")
                
                mc_params = MonteCarloParams(
                    iterations=mc_iterations,  # ✅ Our driver gets FULL iterations (100%)
                    sc_probability_per_lap=input_params.get('sc_prob', 1.5),
                    vsc_probability_per_lap=input_params.get('vsc_prob', 2.0),
                )
                
                competitive_mc = CompetitiveMonteCarloSimulator(
                    sim_params=sim_params,
                    mc_params=mc_params,
                    fp2_predictions=fp2_predictions,
                    opponent_strategies=opponent_best_strategies,  # ✅ Use optimized opponent strategies!
                    long_run_data=long_run_data,
                )
                
                competitive_mc.set_our_driver(our_driver, starting_position)
                
                # Progress callback with UI responsiveness
                def progress_callback(current, total):
                    # Update every 10 iterations (reduced from 20 for better responsiveness)
                    if current % 10 == 0:
                        overall_progress = 86 + int((current / total) * 9)
                        self._update_progress(
                            overall_progress, 
                            f"競爭模擬中 ({current}/{total})..."
                        )
                        # Allow UI to process events and stay responsive
                        QApplication.processEvents()
                
                # Run competitive Monte Carlo
                mc_summary = competitive_mc.run_simulation(
                    top_results,
                    progress_callback=progress_callback
                )
                
                print(f"[MAIN_WINDOW] Competitive MC completed.")
                print(f"[MAIN_WINDOW] Best by position: {mc_summary.best_by_position}")
                
                # Convert to standard format for UI update
                mc_results = self._convert_competitive_mc_to_standard(mc_summary)
                
            else:
                # Fallback: Standard Monte Carlo (time comparison only)
                self._update_progress(86, "標準 Monte Carlo 中...")
                print("[MAIN_WINDOW] Using standard MC (no FP2 data)")
                
                mc_params = MonteCarloParams(
                    iterations=mc_iterations,
                    sc_probability_per_lap=input_params.get('sc_prob', 1.5),
                    vsc_probability_per_lap=input_params.get('vsc_prob', 2.0),
                )
                
                mc_simulator = MonteCarloSimulator(sim_params, mc_params)
                top_strategies = [r.stints for r in top_results]
                mc_results = mc_simulator.run_simulation(top_strategies, strategy_names)
            
            print(f"[MAIN_WINDOW] Monte Carlo completed. Win percentages: {mc_results.win_percentages}")
            
            # Update Strategy Comparison tab with Monte Carlo results
            self.comparison_tab.update_monte_carlo(mc_results)
            
            # Update SimulationTab with Monte Carlo results for visualization
            if hasattr(self, 'simulation_tab') and mc_results:
                self.simulation_tab.set_monte_carlo_summary(mc_results)
            
            # Update Position Analysis tab with position predictions - ❌ 已移除
            # if hasattr(self, 'position_tab') and mc_results:
            #     self.position_tab.update_results(mc_results, starting_position)
            
            # Update Opponent tab with position battle analysis
            if hasattr(self, 'opponent_tab') and mc_results:
                self.opponent_tab.update_position_predictions(mc_results, starting_position)
            
            # Update Safety Car tab with scenario analysis
            if hasattr(self, 'sc_tab') and mc_results:
                # Pass field data for tire comparison (use same ranking mode)
                if hasattr(self, 'fp2_tab'):
                    driver_mode = input_params.get('driver_selection_mode', 0)
                    use_q_ranking = (driver_mode == 1)
                    if use_q_ranking and self.fp2_tab.has_actual_q_data():
                        fp2_predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=True)
                    else:
                        fp2_predictions = self.fp2_tab.get_predictions_with_mode(use_q_ranking=False)
                    opponent_strategies = {}
                    if hasattr(self, 'opponent_tab') and self.opponent_tab:
                        opponent_strategies = self.opponent_tab.get_opponent_strategies()
                    self.sc_tab.set_field_data(fp2_predictions, opponent_strategies)
                
                if hasattr(mc_results, 'scenario_analyses') and mc_results.scenario_analyses:
                    print(f"[MAIN_WINDOW] Updating SC tab with {len(mc_results.scenario_analyses)} scenarios")
                    # Debug: Check that strategy_win_rates uses strategy names
                    for stype, sa in mc_results.scenario_analyses.items():
                        print(f"[MAIN_WINDOW]   {stype}: win_rates keys = {list(sa.strategy_win_rates.keys())}")
                    self.sc_tab.update_scenario_analysis(mc_results.scenario_analyses, mc_results)
                else:
                    print(f"[MAIN_WINDOW] ⚠️ No scenario_analyses in mc_results!")
            
            # ✅ NEW: Push MC results to Full Race Tab for auto-display
            if hasattr(self, 'full_race_tab') and mc_results and results:
                print(f"[MAIN_WINDOW] Pushing MC results to Full Race Tab: {len(results)} strategies")
                self.full_race_tab.receive_monte_carlo_results(
                    mc_summary=mc_results,
                    results=results,
                    params=sim_params
                )
            
        except Exception as e:
            print(f"[MAIN_WINDOW] Monte Carlo error: {e}")
            import traceback
            traceback.print_exc()
    
    def _convert_competitive_mc_to_standard(self, comp_summary):
        """
        Convert CompetitiveMCSummary to MonteCarloSummary format for UI compatibility.
        """
        from strategy_simulator.core.monte_carlo import MonteCarloSummary, PositionPrediction
        
        summary = MonteCarloSummary(iterations=comp_summary.iterations)
        summary.starting_position = comp_summary.grid_position
        
        for name, strat in comp_summary.strategy_summaries.items():
            # Win percentage is now position-based (P1 finish %)
            summary.win_counts[name] = int(strat.win_probability * comp_summary.iterations / 100)
            summary.win_percentages[name] = strat.win_probability
            
            # Time statistics
            summary.mean_times[name] = strat.mean_time
            summary.std_times[name] = strat.time_std
            
            # SC impact - calculate win rates from counts
            wins_with = strat.wins_with_sc
            wins_without = strat.wins_without_sc
            total_with_sc = comp_summary.iterations * comp_summary.sc_occurrence_rate / 100 if comp_summary.sc_occurrence_rate > 0 else 1
            total_without_sc = comp_summary.iterations - total_with_sc if comp_summary.iterations > total_with_sc else 1
            
            no_sc_win_rate = (wins_without / total_without_sc * 100) if total_without_sc > 0 else 0
            with_sc_win_rate = (wins_with / total_with_sc * 100) if total_with_sc > 0 else 0
            benefit = with_sc_win_rate - no_sc_win_rate
            
            summary.sc_impact_analysis[name] = {
                'no_sc_win': no_sc_win_rate,
                'with_sc_win': with_sc_win_rate,
                'benefit': benefit,
                'mean_with_sc': strat.mean_position_with_sc,
                'mean_without_sc': strat.mean_position_without_sc,
            }
            
            # Position prediction
            pos_pred = PositionPrediction(
                strategy_name=name,
                starting_position=comp_summary.grid_position,
                expected_position=strat.mean_finish_position,
                best_case_position=strat.best_finish,
                worst_case_position=strat.worst_finish,
                podium_probability=strat.podium_probability,
                points_probability=strat.points_probability,
                top5_probability=strat.top5_probability,
                expected_gain=strat.mean_positions_gained,
                gain_variance=strat.positions_gained_std,
                position_distribution=strat.position_distribution,
            )
            summary.position_predictions[name] = pos_pred
        
        summary.sc_occurrence_rate = comp_summary.sc_occurrence_rate
        summary.mean_sc_count = comp_summary.mean_sc_count
        
        # Pass through scenario analyses for SC tab
        if hasattr(comp_summary, 'scenario_analyses') and comp_summary.scenario_analyses:
            summary.scenario_analyses = comp_summary.scenario_analyses
            print(f"[MAIN_WINDOW] Converted {len(summary.scenario_analyses)} scenario analyses from CompetitiveMC")
            for stype, sa in summary.scenario_analyses.items():
                print(f"[MAIN_WINDOW]   {stype}: {len(sa.strategy_win_rates)} strategies = {list(sa.strategy_win_rates.keys())[:3]}...")
        else:
            print(f"[MAIN_WINDOW] ⚠️ CompetitiveMCSummary has no scenario_analyses!")
        
        return summary
    
    def _build_scenario_analyses_from_full_race(
        self, 
        multi_stats: dict, 
        single_result, 
        race_laps: int
    ) -> dict:
        """
        Build SC scenario analyses from full race simulation results.
        
        This integrates the full race Monte Carlo results into the SC scenario
        analysis format for display in the Safety Car tab.
        
        Args:
            multi_stats: Statistics from run_multiple_simulations()
            single_result: Single FullRaceSimulation result
            race_laps: Total race laps
            
        Returns:
            Dict of scenario_type -> ScenarioAnalysis
        """
        from strategy_simulator.core.monte_carlo import ScenarioAnalysis
        
        if not multi_stats or not single_result:
            return {}
        
        our_driver = multi_stats.get('our_driver', '')
        our_stats = multi_stats.get('our_stats', {})
        
        # Get strategy name instead of driver code for best_strategy
        # Find our driver's strategy from the result
        our_strategy_name = "Unknown"
        if single_result and hasattr(single_result, 'our_result') and single_result.our_result:
            our_strategy_name = getattr(single_result.our_result, 'strategy_notation', 'Unknown')
        
        # Get all strategy performance stats
        strategy_perf = multi_stats.get('strategy_performance', {})
        
        # Try to build a mapping from tire notation to Plan names
        # Use current simulation results (_current_results) for Plan names
        # Note: strategy_performance uses "-" separator (e.g., "H-S-S")
        #       but get_stint_notation() uses "→" separator (e.g., "H→S→S")
        #       So we need to normalize the format
        plan_mapping = {}  # {normalized_notation: plan_name}
        if hasattr(self, '_current_results') and self._current_results:
            for result in self._current_results:
                if hasattr(result, 'strategy_name'):
                    # Get tire notation from result and normalize to "-" format
                    notation = result.get_stint_notation() if hasattr(result, 'get_stint_notation') else None
                    if notation:
                        # Normalize: "H→S→S" → "H-S-S"
                        normalized_notation = notation.replace("→", "-")
                        plan_mapping[normalized_notation] = result.strategy_name
                        print(f"[SC_SCENARIO] Mapping: {normalized_notation} → {result.strategy_name}")
        
        print(f"[SC_SCENARIO] Plan mapping built: {plan_mapping}")
        print(f"[SC_SCENARIO] Strategy perf keys: {list(strategy_perf.keys())}")
        
        # Build strategy_win_rates using Plan names if available, otherwise tire notation
        strategy_win_rates = {}
        for strategy_key, stats in strategy_perf.items():
            win_rate = stats.get('win_rate', 0)
            # Map tire notation to Plan name if possible
            display_name = plan_mapping.get(strategy_key, strategy_key)
            strategy_win_rates[display_name] = win_rate
        
        # Find the best strategy by win rate
        if strategy_win_rates:
            best_strategy = max(strategy_win_rates.items(), key=lambda x: x[1])[0]
            best_win_rate = strategy_win_rates[best_strategy]
        else:
            # Fallback to our strategy
            best_strategy = plan_mapping.get(our_strategy_name, our_strategy_name)
            best_win_rate = our_stats.get('win_probability', 0)
        
        print(f"[SC_SCENARIO] Best strategy: {best_strategy} ({best_win_rate:.1f}%)")
        print(f"[SC_SCENARIO] All strategy win rates: {strategy_win_rates}")
        
        third = race_laps // 3
        
        # Extract SC events from single result
        sc_events = single_result.sc_events if single_result else []
        has_sc = len(sc_events) > 0
        
        # Classify SC timing if present
        sc_timing = "no_sc"
        if has_sc:
            earliest_lap = min(e.get('lap', race_laps) for e in sc_events)
            if earliest_lap <= third:
                sc_timing = "early_sc"
            elif earliest_lap <= 2 * third:
                sc_timing = "mid_sc"
            else:
                sc_timing = "late_sc"
        
        # Build scenarios based on statistical analysis
        scenarios = {}
        
        # No SC scenario
        scenarios["no_sc"] = ScenarioAnalysis(
            scenario_type="no_sc",
            scenario_name="No Safety Car",
            occurrence_rate=50.0,  # Estimated
            iteration_count=multi_stats.get('iterations', 100) // 2,
            best_strategy=best_strategy,
            best_strategy_win_rate=best_win_rate,
            strategy_win_rates=strategy_win_rates.copy(),
            strategy_avg_times={},
            decision_advice=[
                "標準賽事條件 - 執行最佳配速策略",
                "維持計畫進站圈數"
            ]
        )
        
        # Early SC scenario - adjust win rates slightly
        early_sc_win_rates = {k: v * 1.1 for k, v in strategy_win_rates.items()}
        scenarios["early_sc"] = ScenarioAnalysis(
            scenario_type="early_sc",
            scenario_name=f"Early SC (Lap 1-{third})",
            occurrence_rate=15.0,
            iteration_count=multi_stats.get('iterations', 100) // 6,
            best_strategy=best_strategy,
            best_strategy_win_rate=best_win_rate * 1.1,  # SC generally helps
            strategy_win_rates=early_sc_win_rates,
            strategy_avg_times={},
            decision_advice=[
                "早期 SC 對尚未進站的車手有利",
                "考慮提前進站換 HARD 完賽",
                "注意前方車手進站造成的 pit lane traffic"
            ]
        )
        
        # Mid-race SC scenario
        scenarios["mid_sc"] = ScenarioAnalysis(
            scenario_type="mid_sc",
            scenario_name=f"Mid-Race SC (Lap {third+1}-{2*third})",
            occurrence_rate=20.0,
            iteration_count=multi_stats.get('iterations', 100) // 5,
            best_strategy=best_strategy,
            best_strategy_win_rate=best_win_rate,
            strategy_win_rates=strategy_win_rates.copy(),
            strategy_avg_times={},
            decision_advice=[
                "中段 SC - 進站時機變得關鍵",
                "注意 SC 期間「免費」進站機會",
                "警惕同時進站的 pit lane 擁堵"
            ]
        )
        
        # Late SC scenario - slight penalty
        late_sc_win_rates = {k: v * 0.9 for k, v in strategy_win_rates.items()}
        scenarios["late_sc"] = ScenarioAnalysis(
            scenario_type="late_sc",
            scenario_name=f"Late SC (Lap {2*third+1}+)",
            occurrence_rate=15.0,
            iteration_count=multi_stats.get('iterations', 100) // 6,
            best_strategy=best_strategy,
            best_strategy_win_rate=best_win_rate * 0.9,  # Late SC adds chaos
            strategy_win_rates=late_sc_win_rates,
            strategy_avg_times={},
            decision_advice=[
                "晚期 SC - 最後一段換新胎至關重要",
                "考慮選擇 SOFT 衝刺終點",
                "位置優先 vs 新胎優勢的權衡"
            ]
        )
        
        return scenarios
    
    def _on_export_results(self):
        """Export current results."""
        if not self._current_results:
            QMessageBox.information(
                self, "匯出",
                "沒有可匯出的結果。請先執行模擬。"
            )
            return
        
        # TODO: Implement export dialog
        QMessageBox.information(
            self, "匯出",
            "匯出功能即將推出。"
        )
    
    def _toggle_input_panel(self):
        """Toggle visibility of input panel (collapse/expand)."""
        current_sizes = self.main_splitter.sizes()
        
        if not current_sizes or len(current_sizes) < 2:
            return
        
        total_width = sum(current_sizes)
        
        if self._input_panel_visible:
            # Collapse: Save current width and hide panel
            self._saved_input_width = current_sizes[0]
            self.input_panel.hide()
            
            # Force splitter to reallocate space - left container shrinks to button width only
            self.main_splitter.setSizes([20, total_width - 20])
            
            self.toggle_btn.setText("▶")
            self.toggle_btn.setToolTip("展開參數面板 (Ctrl+B)")
            self._input_panel_visible = False
        else:
            # Expand: Restore panel
            self.input_panel.show()
            
            # Restore saved width
            restore_width = self._saved_input_width if self._saved_input_width > 100 else 400
            self.main_splitter.setSizes([restore_width, total_width - restore_width])
            
            self.toggle_btn.setText("◀")
            self.toggle_btn.setToolTip("收起參數面板 (Ctrl+B)")
            self._input_panel_visible = True
    
    def _on_reset_view(self):
        """Reset all views to default state."""
        self.chart_tab.reset_view()
    
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "關於 F1T 比賽策略模擬器",
            "<h2>F1T 比賽策略模擬器</h2>"
            "<p>版本 1.0.0</p>"
            "<p>專業 F1 比賽策略模擬工具。</p>"
            "<p>功能特點:</p>"
            "<ul>"
            "<li>逐圈比賽模擬</li>"
            "<li>蒙地卡羅信賴分析</li>"
            "<li>安全車情境規劃</li>"
            "<li>Undercut/Overcut 窗口計算</li>"
            "</ul>"
            "<p>&copy; 2025 F1T Team</p>"
        )


def main():
    """Main entry point for Strategy Simulator."""
    # Set GUI language to Chinese
    try:
        from core.gui_i18n import set_gui_language
        set_gui_language('zh')
    except ImportError:
        pass
    
    app = QApplication(sys.argv)
    app.setApplicationName("F1T Race Strategy Simulator")
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
