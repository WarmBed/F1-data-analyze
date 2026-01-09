#!/usr/bin/env python3
"""
Full Race Simulation Tab

Displays 20-driver race simulation results with:
- Final standings table
- Position chart over laps
- Strategy effectiveness analysis
- Our driver's performance summary

Author: F1T Team
Date: 2025-01-07
"""

from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QPushButton, QSpinBox, QComboBox, QFrame,
    QProgressBar, QGridLayout, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QBrush

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

# Import i18n with lazy loading
from strategy_simulator.gui.i18n_helper import tr

# Import report generator
from strategy_simulator.gui.widgets.strategy_report_generator import StrategyReportGenerator
from strategy_simulator.gui.widgets.strategy_report_dialog import StrategyReportDialog


class SimulationWorker(QThread):
    """Worker thread for running race simulations."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, simulator, iterations: int):
        super().__init__()
        self.simulator = simulator
        self.iterations = iterations
        
    def run(self):
        try:
            # Run single simulation for visualization
            self.progress.emit(10, tr("RUNNING_SINGLE_SIM", "Running single simulation..."))
            single_result = self.simulator.simulate_race()
            
            # Run multiple for statistics
            self.progress.emit(30, tr("RUNNING_MULTI_SIM", "Running statistical simulations..."))
            multi_stats = self.simulator.run_multiple_simulations(self.iterations)
            
            self.progress.emit(100, tr("SIMULATION_COMPLETE", "Simulation complete"))
            self.finished.emit({
                'single': single_result,
                'statistics': multi_stats
            })
        except Exception as e:
            self.error.emit(str(e))


class FullRaceTab(QWidget):
    """
    Full Race Simulation Tab.
    
    Displays 20-driver race simulation with:
    - Interactive standings table
    - Position history chart
    - Statistical analysis
    """
    
    # Signal when simulation is requested
    simulation_requested = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._simulation_result = None
        self._statistics = None
        self._our_driver = None
        
        # Cache Monte Carlo results from main window
        self._cached_mc_summary = None
        self._cached_results = []  # List of OptimizationResult
        self._cached_params = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Explanation banner at top
        explanation = QLabel(
            f"<div style='background: #e8f5e9; padding: 8px; border-radius: 5px; border: 1px solid #81c784;'>"
            f"<b style='color: #2e7d32;'>✅ {tr('FULL_RACE_SMART_TITLE', '完整賽事 - 智能策略分配')}</b><br/>"
            f"<span style='color: #424242; font-size: 0.9em;'>"
            f"{tr('FULL_RACE_SMART_EXPLANATION', '此標籤頁使用主畫面 MC 分析的最佳策略分配，執行 20 車詳細模擬。')}<br/>"
            f"{tr('FULL_RACE_SMART_BENEFIT', '優勢：對手使用最佳策略，模擬更真實；無需重新策略分析，節省時間。')}"
            f"</span>"
            f"</div>"
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Top: Controls
        controls_layout = self._create_controls()
        layout.addLayout(controls_layout)
        
        # Main content: Race Standings (full width)
        standings_group = QGroupBox(tr("RACE_STANDINGS", "Race Standings"))
        standings_layout = QVBoxLayout(standings_group)
        
        self.standings_table = self._create_standings_table()
        standings_layout.addWidget(self.standings_table)
        
        layout.addWidget(standings_group, 1)
        
        # Driver Summary (below Race Standings)
        summary_group = QGroupBox(tr("DRIVER_SUMMARY", "Driver Summary"))
        self.summary_layout = QGridLayout(summary_group)
        self._setup_driver_summary_labels()
        layout.addWidget(summary_group)
        
        # Bottom: Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel(tr("READY_TO_SIMULATE", "Ready to simulate. Load FP2 data and run."))
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
        
    def _create_controls(self) -> QVBoxLayout:
        """Create control buttons in two rows."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        
        # === Row 1: Mode, Strategy, Highlight ===
        row1 = QHBoxLayout()
        
        from PyQt5.QtWidgets import QButtonGroup, QRadioButton
        
        row1.addWidget(QLabel(tr("SIM_MODE", "Mode") + ":"))
        self.mode_group = QButtonGroup(self)
        
        self.simple_mode_radio = QRadioButton(tr("SIMPLE_MODE", "Simple"))
        self.simple_mode_radio.setToolTip(tr("SIMPLE_MODE_TOOLTIP", "Fast lap-time simulation without position tracking"))
        self.mode_group.addButton(self.simple_mode_radio, 0)
        row1.addWidget(self.simple_mode_radio)
        
        self.full_mode_radio = QRadioButton(tr("FULL_MODE", "Complete"))
        self.full_mode_radio.setToolTip(tr("FULL_MODE_TOOLTIP", "Full position tracking with SC/DRS/overtaking (experimental)"))
        self.mode_group.addButton(self.full_mode_radio, 1)
        row1.addWidget(self.full_mode_radio)
        
        self.simple_mode_radio.setChecked(True)
        
        row1.addSpacing(15)
        
        # Our Strategy Selection
        row1.addWidget(QLabel(tr("OUR_STRATEGY", "我方策略") + ":"))
        self.plan_combo = QComboBox()
        self.plan_combo.setMinimumWidth(120)
        self.plan_combo.setToolTip(tr("SELECT_PLAN_TOOLTIP", "Select which plan to test in full race simulation"))
        row1.addWidget(self.plan_combo)
        
        row1.addSpacing(20)
        
        # Driver highlight
        row1.addWidget(QLabel(tr("HIGHLIGHT_DRIVER", "Highlight") + ":"))
        self.driver_combo = QComboBox()
        self.driver_combo.setMinimumWidth(100)
        self.driver_combo.currentTextChanged.connect(self._on_driver_selected)
        row1.addWidget(self.driver_combo)
        
        row1.addStretch()
        main_layout.addLayout(row1)
        
        # === Row 2: SC Scenario, Iterations, Run Button ===
        row2 = QHBoxLayout()
        
        # SC Scenario Selection
        row2.addWidget(QLabel(tr("SC_SCENARIO", "SC Scenario") + ":"))
        self.sc_scenario_combo = QComboBox()
        self.sc_scenario_combo.setMinimumWidth(120)
        self.sc_scenario_combo.addItems([
            tr("SC_RANDOM", "Random (50%)"),
            tr("SC_NONE", "No SC"),
            tr("SC_EARLY", "Early SC (L10-15)"),
            tr("SC_MID", "Mid SC (L25-30)"),
            tr("SC_LATE", "Late SC (L45-50)")
        ])
        self.sc_scenario_combo.setToolTip(tr("SELECT_SC_TOOLTIP", "Choose SC timing scenario for simulation"))
        row2.addWidget(self.sc_scenario_combo)
        
        row2.addSpacing(20)
        
        # Iterations
        row2.addWidget(QLabel(tr("ITERATIONS", "迭代次數") + ":"))
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(10, 1000)
        self.iterations_spin.setValue(10)
        self.iterations_spin.setSingleStep(10)
        row2.addWidget(self.iterations_spin)
        
        row2.addStretch()
        
        # Run Full Race button
        self.run_btn = QPushButton(tr("RUN_FULL_RACE", "執行完整賽事"))
        self.run_btn.setMinimumWidth(200)
        self.run_btn.setToolTip(tr("RUN_FULL_RACE_TOOLTIP", "使用 MC 策略分配執行 20 車完整模擬"))
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self._on_run_full_race_clicked)
        row2.addWidget(self.run_btn)
        
        main_layout.addLayout(row2)
        
        return main_layout
    
    def _create_standings_table(self) -> QTableWidget:
        """Create standings table."""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            tr("POS", "P"),
            tr("DRIVER", "Driver"),
            tr("TEAM", "Team"),
            tr("GRID", "Grid"),
            tr("CHANGE", "+/-"),
            tr("GAP", "Gap"),
            tr("STOPS", "Stops"),
            tr("STRATEGY", "Strategy"),
        ])
        
        # Configure
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        return table
    
    def _setup_driver_summary_labels(self):
        """Setup driver summary labels below Race Standings."""
        # Row 0: Final Position, Pit Stops
        self.summary_layout.addWidget(QLabel(tr("FINAL_POSITION", "Final Position") + ":"), 0, 0)
        self.lbl_final_pos = QLabel("--")
        self.lbl_final_pos.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.summary_layout.addWidget(self.lbl_final_pos, 0, 1)
        
        self.summary_layout.addWidget(QLabel(tr("PIT_STOPS", "Pit Stops") + ":"), 0, 2)
        self.lbl_pit_stops = QLabel("--")
        self.summary_layout.addWidget(self.lbl_pit_stops, 0, 3)
        
        # Row 1: Grid Position, Total Time
        self.summary_layout.addWidget(QLabel(tr("GRID_POSITION", "Grid Position") + ":"), 1, 0)
        self.lbl_grid_pos = QLabel("--")
        self.summary_layout.addWidget(self.lbl_grid_pos, 1, 1)
        
        self.summary_layout.addWidget(QLabel(tr("TOTAL_TIME", "Total Time") + ":"), 1, 2)
        self.lbl_total_time = QLabel("--")
        self.summary_layout.addWidget(self.lbl_total_time, 1, 3)
        
        # Row 2: Positions Gained, Gap to Leader
        self.summary_layout.addWidget(QLabel(tr("POSITIONS_GAINED", "Positions +/-") + ":"), 2, 0)
        self.lbl_pos_gained = QLabel("--")
        self.summary_layout.addWidget(self.lbl_pos_gained, 2, 1)
        
        self.summary_layout.addWidget(QLabel(tr("GAP_TO_LEADER", "Gap to Leader") + ":"), 2, 2)
        self.lbl_gap_leader = QLabel("--")
        self.summary_layout.addWidget(self.lbl_gap_leader, 2, 3)
        
        # Row 3: Strategy
        self.summary_layout.addWidget(QLabel(tr("STRATEGY", "Strategy") + ":"), 3, 0)
        self.lbl_strategy = QLabel("--")
        self.lbl_strategy.setStyleSheet("font-weight: bold; color: #2196F3;")
        self.summary_layout.addWidget(self.lbl_strategy, 3, 1, 1, 3)  # Span 3 columns
    
    def _setup_summary_labels(self):
        """Deprecated: Summary labels removed (moved to Result Analysis tab)"""
        # This method is no longer used
        pass
    
    def _setup_summary_labels_old(self):
        """Setup summary labels."""
        labels = [
            ("lbl_driver", tr("DRIVER", "Driver"), 0, 0),
            ("lbl_position", tr("FINAL_POSITION", "Final Position"), 0, 2),
            ("lbl_grid", tr("GRID_POSITION", "Grid Position"), 1, 0),
            ("lbl_change", tr("POSITIONS_CHANGED", "Positions Changed"), 1, 2),
            ("lbl_gap", tr("GAP_TO_WINNER", "Gap to Winner"), 2, 0),
            ("lbl_win_prob", tr("WIN_PROBABILITY", "冠軍勝率 (P1)"), 2, 2),
            ("lbl_podium_prob", tr("PODIUM_PROBABILITY", "領獎台機率 (P1-P3)"), 3, 0),
            ("lbl_points_prob", tr("POINTS_PROBABILITY", "Points Probability"), 3, 2),
        ]
        
        for attr, text, row, col in labels:
            label = QLabel(f"{text}:")
            label.setStyleSheet("font-weight: bold;")
            self.summary_layout.addWidget(label, row, col)
            
            value_label = QLabel("-")
            value_label.setStyleSheet("font-size: 14px;")
            setattr(self, attr, value_label)
            self.summary_layout.addWidget(value_label, row, col + 1)
    
    def _setup_mc_stats_labels(self):
        """
        Setup Monte Carlo statistics labels.
        
        Shows:
        - Iterations run
        - Average position
        - Win rate
        - Podium rate
        - Points rate
        - Average gain
        """
        labels = [
            ("lbl_mc_iterations", tr("MC_ITERATIONS", "Iterations"), 0, 0),
            ("lbl_mc_avg_pos", tr("MC_AVG_POSITION", "Avg Position"), 0, 2),
            ("lbl_mc_win_rate", tr("MC_WIN_RATE", "Win Rate"), 1, 0),
            ("lbl_mc_podium_rate", tr("MC_PODIUM_RATE", "Podium Rate"), 1, 2),
            ("lbl_mc_points_rate", tr("MC_POINTS_RATE", "Points Rate"), 2, 0),
            ("lbl_mc_avg_gain", tr("MC_AVG_GAIN", "Avg Gain"), 2, 2),
        ]
        
        for attr, text, row, col in labels:
            label = QLabel(f"{text}:")
            label.setStyleSheet("font-weight: bold;")
            self.mc_stats_layout.addWidget(label, row, col)
            
            value_label = QLabel("-")
            value_label.setStyleSheet("font-size: 14px;")
            setattr(self, attr, value_label)
            self.mc_stats_layout.addWidget(value_label, row, col + 1)
    
    def _setup_mc_stats_labels(self):
        """
        Setup Monte Carlo statistics labels.
        
        Shows:
        - Iterations run
        - Average position
        - Win rate
        - Podium rate
        - Points rate
        - Confidence interval
        """
        labels = [
            ("lbl_mc_iterations", tr("MC_ITERATIONS", "Iterations"), 0, 0),
            ("lbl_mc_avg_pos", tr("MC_AVG_POSITION", "Avg Position"), 0, 2),
            ("lbl_mc_win_rate", tr("MC_WIN_RATE", "Win Rate"), 1, 0),
            ("lbl_mc_podium_rate", tr("MC_PODIUM_RATE", "Podium Rate"), 1, 2),
            ("lbl_mc_points_rate", tr("MC_POINTS_RATE", "Points Rate"), 2, 0),
            ("lbl_mc_avg_gain", tr("MC_AVG_GAIN", "Avg Gain"), 2, 2),
        ]
        
        for attr, text, row, col in labels:
            label = QLabel(f"{text}:")
            label.setStyleSheet("font-weight: bold;")
            self.mc_stats_layout.addWidget(label, row, col)
            
            value_label = QLabel("-")
            value_label.setStyleSheet("font-size: 14px;")
            setattr(self, attr, value_label)
            self.mc_stats_layout.addWidget(value_label, row, col + 1)
    
    def set_drivers(self, driver_list: List[str]):
        """Set available drivers for highlighting and comparison."""
        # Preserve current highlight driver selection
        current_highlight = self.driver_combo.currentText() if self.driver_combo.count() > 0 else None
        
        self.driver_combo.clear()
        self.driver_combo.addItems(driver_list)
        
        # Restore previous highlight driver if it exists in new list
        if current_highlight and current_highlight in driver_list:
            index = self.driver_combo.findText(current_highlight)
            if index >= 0:
                self.driver_combo.setCurrentIndex(index)
        # If _our_driver is set, use it as default
        elif hasattr(self, '_our_driver') and self._our_driver in driver_list:
            index = self.driver_combo.findText(self._our_driver)
            if index >= 0:
                self.driver_combo.setCurrentIndex(index)
        # Otherwise default to first driver
        elif len(driver_list) > 0:
            self.driver_combo.setCurrentIndex(0)
        
        # ❌ Comparison dropdowns removed (moved to Result Analysis tab)
        # self.compare_driver1_combo and self.compare_driver2_combo no longer exist
    
    def receive_monte_carlo_results(self, mc_summary, results: list, params):
        """
        Receive and cache Monte Carlo results from main window.
        
        Args:
            mc_summary: MonteCarloSummary or CompetitiveMCSummary
            results: List of OptimizationResult (sorted by expected_position)
            params: SimulationParams
        """
        print(f"[FULL_RACE_TAB] Received MC results: {len(results)} strategies")
        
        self._cached_mc_summary = mc_summary
        self._cached_results = results
        self._cached_params = params
        
        # Update plan combo with strategy names
        self.plan_combo.blockSignals(True)  # Prevent triggering during population
        self.plan_combo.clear()
        for idx, result in enumerate(results[:10]):  # Top 10 plans
            plan_letter = chr(65 + idx)  # A, B, C...
            notation = self._format_strategy_notation(result.stints)
            self.plan_combo.addItem(f"Plan {plan_letter}: {notation}")
        self.plan_combo.blockSignals(False)
        
        # Connect combo change to auto-update (if not already connected)
        try:
            self.plan_combo.currentIndexChanged.disconnect(self._on_strategy_selection_changed)
        except:
            pass
        self.plan_combo.currentIndexChanged.connect(self._on_strategy_selection_changed)
        
        try:
            self.sc_scenario_combo.currentIndexChanged.disconnect(self._on_strategy_selection_changed)
        except:
            pass
        self.sc_scenario_combo.currentIndexChanged.connect(self._on_strategy_selection_changed)
        
        # Enable button
        self.run_btn.setEnabled(True)
        self.status_label.setText(
            f"{tr('MC_RESULTS_READY', 'Monte Carlo 結果已載入')}: "
            f"{len(results)} {tr('STRATEGIES', '策略')}"
        )
        self.status_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        
        # ✅ Auto-display first strategy's MC stats immediately
        if self._cached_results:
            self._display_mc_strategy_stats(self._cached_results[0], 'random')
    
    def _on_strategy_selection_changed(self, index=None):
        """
        Auto-update display when user changes strategy or SC scenario selection.
        """
        if not self._cached_results or not self._cached_mc_summary:
            return
        
        # Get selected strategy
        selected_plan_index = self.plan_combo.currentIndex()
        if selected_plan_index < 0 or selected_plan_index >= len(self._cached_results):
            return
        
        selected_result = self._cached_results[selected_plan_index]
        strategy_name = selected_result.strategy_name
        plan_letter = chr(65 + selected_plan_index)
        
        # Get SC scenario
        sc_scenario_index = self.sc_scenario_combo.currentIndex()
        sc_scenario_map = ["random", "none", "early", "mid", "late"]
        sc_scenario = sc_scenario_map[sc_scenario_index] if sc_scenario_index >= 0 else "random"
        
        print(f"[FULL_RACE_TAB] Selection changed: Plan {plan_letter} ({strategy_name}), SC: {sc_scenario}")
        
        # Update display with MC stats
        self._display_mc_strategy_stats(selected_result, sc_scenario)
        
        # Update status
        self.status_label.setText(
            f"{tr('DISPLAYING', '正在顯示')}: {strategy_name} - "
            f"{tr('SC_SCENARIO', 'SC 場景')}: {sc_scenario.upper()}"
        )
        self.status_label.setStyleSheet("color: #1976d2;")
    
    def _format_strategy_notation(self, stints) -> str:
        """Format strategy as string notation (e.g., 'M15-H')."""
        parts = []
        for stint in stints:
            compound = stint.compound.value[0] if hasattr(stint.compound, 'value') else str(stint.compound)[0]
            if hasattr(stint, 'planned_length'):
                parts.append(f"{compound}{stint.planned_length}")
            else:
                parts.append(compound)
        return "-".join(parts)
        
    def set_our_driver(self, driver_code: str):
        """Set our driver for highlighting."""
        self._our_driver = driver_code
        index = self.driver_combo.findText(driver_code)
        if index >= 0:
            self.driver_combo.setCurrentIndex(index)
            
    def _on_run_full_race_clicked(self):
        """
        Handle run full race button click - Execute 20-driver simulation using MC strategy assignments.
        """
        print(f"[FULL_RACE_TAB] ====== RUN FULL RACE CLICKED ======")
        print(f"[FULL_RACE_TAB] _cached_mc_summary: {self._cached_mc_summary is not None}")
        print(f"[FULL_RACE_TAB] _cached_results: {len(self._cached_results) if self._cached_results else 0}")
        print(f"[FULL_RACE_TAB] _cached_params: {self._cached_params is not None}")
        
        # ✅ 只需要策略結果即可運行（不強制要求 MC summary）
        if not self._cached_results:
            self.status_label.setText(
                tr("NO_RESULTS", "請先在主畫面執行策略優化")
            )
            self.status_label.setStyleSheet("color: #d32f2f;")
            print(f"[FULL_RACE_TAB] ❌ No cached results, aborting")
            return
        
        # Get selected strategy
        selected_plan_index = self.plan_combo.currentIndex()
        if selected_plan_index < 0 or selected_plan_index >= len(self._cached_results):
            self.status_label.setText(tr("INVALID_PLAN", "無效的策略選擇"))
            print(f"[FULL_RACE_TAB] ❌ Invalid plan index: {selected_plan_index}")
            return
        
        # Get SC scenario
        sc_scenario_index = self.sc_scenario_combo.currentIndex()
        sc_scenario_map = ["random", "none", "early", "mid", "late"]
        sc_scenario = sc_scenario_map[sc_scenario_index]
        
        # Get iterations
        iterations = self.iterations_spin.value()
        
        # Get simulation mode (NEW)
        simulation_mode = "complete" if self.full_mode_radio.isChecked() else "simple"
        
        print(f"[FULL_RACE_TAB] Requesting full race simulation: Plan {chr(65 + selected_plan_index)}, SC: {sc_scenario}, Iterations: {iterations}, Mode: {simulation_mode}")
        
        # Emit signal to main window (will use MC strategy assignments)
        self.simulation_requested.emit({
            'iterations': iterations,
            'selected_plan_index': selected_plan_index,
            'sc_scenario': sc_scenario,
            'simulation_mode': simulation_mode  # NEW: simple or complete
        })
    
    def _on_update_view_clicked(self):
        """
        [DEPRECATED] Old method for viewing MC stats only.
        Replaced by _on_run_full_race_clicked() which runs full 20-driver simulation.
        """
        print("[FULL_RACE_TAB] _on_update_view_clicked() is deprecated, redirecting to full race simulation")
        self._on_run_full_race_clicked()
    
    def _display_mc_strategy_stats(self, result, sc_scenario: str):
        """
        Display strategy statistics from MC cache.
        
        Args:
            result: OptimizationResult
            sc_scenario: 'random', 'none', 'early', 'mid', 'late'
        """
        if not self._cached_mc_summary:
            return
        
        mc = self._cached_mc_summary
        strategy_name = result.strategy_name
        
        # Map scenario types
        scenario_map = {
            'none': 'no_sc',
            'early': 'early_sc',
            'mid': 'mid_sc',
            'late': 'late_sc'
        }
        
        # Get scenario-specific win rate
        win_rate = 0
        if sc_scenario in scenario_map and hasattr(mc, 'scenario_analyses'):
            scenario_key = scenario_map[sc_scenario]
            if scenario_key in mc.scenario_analyses:
                scenario_analysis = mc.scenario_analyses[scenario_key]
                win_rate = scenario_analysis.strategy_win_rates.get(strategy_name, 0)
        elif sc_scenario == 'random':
            # Use overall win rate
            win_rate = result.win_rate if hasattr(result, 'win_rate') else 0
        
        # ❌ Summary labels removed (moved to Result Analysis tab)
        # All lbl_* attributes no longer exist in FullRaceTab
        # Data is now displayed in RaceResultAnalysisTab
        
        print(f"[FULL_RACE_TAB] MC strategy stats cached (avg_pos: {result.expected_position if hasattr(result, 'expected_position') else 'N/A'})")
        print(f"[FULL_RACE_TAB] Win rate: {win_rate:.1f}%")
        
        # Store data for potential future use
        self._last_mc_stats = {
            'avg_pos': result.expected_position if hasattr(result, 'expected_position') else 0,
            'win_rate': win_rate,
            'podium_prob': result.podium_probability if hasattr(result, 'podium_probability') else 0,
            'points_prob': result.points_probability if hasattr(result, 'points_probability') else 0
        }
        
        # Display position distribution if available
        if hasattr(result, 'position_distribution') and result.position_distribution:
            self._display_position_distribution(result.position_distribution, strategy_name)
        else:
            # Clear chart and show message
            self._clear_chart_with_message()
        
        # Update standings table with statistical summary
        self._display_statistical_summary(result, sc_scenario, win_rate)
        
        avg_pos = result.expected_position if hasattr(result, 'expected_position') else 0
        print(f"[FULL_RACE_TAB] Displayed MC stats for {strategy_name}: WinRate={win_rate:.1f}%, AvgPos=P{avg_pos:.1f}")
    
    def _display_position_distribution(self, distribution: dict, strategy_name: str):
        """Display position distribution histogram. 
        
        Note: position_plot has been moved to RaceResultAnalysisTab.
        This method is now a no-op for backward compatibility.
        """
        # [2025-01-06] position_plot moved to race_result_analysis_tab
        pass
    
    def _clear_chart_with_message(self):
        """Clear chart and display message about MC-only data.
        
        Note: position_plot has been moved to RaceResultAnalysisTab.
        This method is now a no-op for backward compatibility.
        """
        # [2025-01-06] position_plot moved to race_result_analysis_tab
        pass
    
    def _display_statistical_summary(self, result, sc_scenario: str, win_rate: float):
        """Display statistical summary in standings table."""
        self.standings_table.setRowCount(6)
        
        # Row 0: Strategy info
        self.standings_table.setItem(0, 0, QTableWidgetItem(tr("STRATEGY", "策略")))
        self.standings_table.setItem(0, 1, QTableWidgetItem(result.strategy_name))
        
        # Row 1: SC Scenario
        self.standings_table.setItem(1, 0, QTableWidgetItem(tr("SC_SCENARIO", "SC 場景")))
        self.standings_table.setItem(1, 1, QTableWidgetItem(sc_scenario.upper()))
        
        # Row 2: Win Rate (P1 only)
        win_prob = result.win_probability if hasattr(result, 'win_probability') else win_rate
        self.standings_table.setItem(2, 0, QTableWidgetItem(tr("WIN_RATE", "冠軍勝率 (P1)")))
        self.standings_table.setItem(2, 1, QTableWidgetItem(f"{win_prob:.1f}%"))
        
        # Row 3: Podium Probability (P1-P3)
        podium_prob = result.podium_probability if hasattr(result, 'podium_probability') else 0
        self.standings_table.setItem(3, 0, QTableWidgetItem(tr("PODIUM_RATE", "領獎台機率 (P1-P3)")))
        self.standings_table.setItem(3, 1, QTableWidgetItem(f"{podium_prob:.1f}%"))
        
        # Row 4: Avg Position
        avg_pos = result.expected_position if hasattr(result, 'expected_position') else 0
        self.standings_table.setItem(4, 0, QTableWidgetItem(tr("AVG_POSITION", "平均位置")))
        self.standings_table.setItem(4, 1, QTableWidgetItem(f"P{avg_pos:.1f}"))
        
        # Row 5: Points Probability
        points_prob = result.points_probability if hasattr(result, 'points_probability') else 0
        self.standings_table.setItem(5, 0, QTableWidgetItem(tr("POINTS_RATE", "積分區機率 (P1-P10)")))
        self.standings_table.setItem(5, 1, QTableWidgetItem(f"{points_prob:.1f}%"))
    
    def set_strategies(self, results: List, params=None):
        """
        Set available strategies for our driver selection.
        
        Args:
            results: List of StrategyResult from optimization
            params: Optional SimulationParams to cache
        """
        self.plan_combo.clear()
        
        # ✅ 緩存策略結果，使「執行完整賽事」可用
        self._cached_results = results if results else []
        if params:
            self._cached_params = params
        
        if not results:
            self.plan_combo.addItem(tr("NO_STRATEGIES", "No strategies available"))
            self.plan_combo.setEnabled(False)
            self.run_btn.setEnabled(False)
            return
        
        self.plan_combo.setEnabled(True)
        self.run_btn.setEnabled(True)  # ✅ 啟用按鈕
        
        # Add each plan with descriptive label
        for i, result in enumerate(results):
            plan_letter = chr(65 + i)  # A, B, C...
            
            # Build strategy notation
            notation = "-".join(s.compound.value[0] for s in result.stints) if hasattr(result, 'stints') else "N/A"
            
            # Get win probability if available
            win_prob = ""
            if hasattr(result, 'win_probability'):
                win_prob = f" ({result.win_probability:.0%} win)"
            elif hasattr(result, 'podium_probability'):
                win_prob = f" ({result.podium_probability:.0%} podium)"
            
            label = f"Plan {plan_letter}: {notation}{win_prob}"
            self.plan_combo.addItem(label)
        
        # Select first (best) plan by default
        self.plan_combo.setCurrentIndex(0)
        
        print(f"[FULL_RACE_TAB] Loaded {len(results)} strategies for selection")
        
    def _on_driver_selected(self, driver_code: str):
        """Handle driver selection for highlighting."""
        self._our_driver = driver_code
        self._update_chart_highlight()
        self._update_summary()
        
    def update_simulation_result(self, result: Dict[str, Any]):
        """
        Update with simulation results.
        
        ⚠️ 注意：Position History、Summary、Traffic Analysis 等詳細分析
        已移至「結果分析」tab，此處只更新 Standings Table
        
        Args:
            result: Dict with 'single' (FullRaceSimulation) and 'statistics' (multi-run stats)
        """
        print(f"[FULL_RACE_TAB] ====== UPDATE_SIMULATION_RESULT CALLED ======")
        print(f"[FULL_RACE_TAB] Result keys: {result.keys() if result else 'None'}")
        
        self._simulation_result = result.get('single')
        self._statistics = result.get('statistics')
        
        print(f"[FULL_RACE_TAB] _simulation_result type: {type(self._simulation_result)}")
        
        if self._simulation_result:
            print(f"[FULL_RACE_TAB] Updating standings table...")
            self._update_standings_table()
        else:
            print(f"[FULL_RACE_TAB] ⚠️ No simulation result to display!")
        
        self.status_label.setText(
            tr("SIMULATION_COMPLETE_SEE_RESULTS", 
               "✅ 模擬完成！請切換到「結果分析」tab 查看詳細分析")
        )
        self.status_label.setStyleSheet("color: #2e7d32;")  # Green for success
        print(f"[FULL_RACE_TAB] ====== UPDATE COMPLETE ======")

        
    def _update_standings_table(self):
        """Update standings table with results."""
        if not self._simulation_result:
            return
        
        standings = self._simulation_result.final_standings
        self.standings_table.setRowCount(len(standings))
        
        for row, result in enumerate(standings):
            # Position
            pos_item = QTableWidgetItem(str(result.final_position))
            pos_item.setTextAlignment(Qt.AlignCenter)
            if result.final_position <= 3:
                pos_item.setBackground(QBrush(QColor(255, 215, 0, 100)))  # Gold
            elif result.final_position <= 10:
                pos_item.setBackground(QBrush(QColor(200, 255, 200)))  # Light green
            self.standings_table.setItem(row, 0, pos_item)
            
            # Driver
            driver_item = QTableWidgetItem(result.driver_code)
            driver_item.setTextAlignment(Qt.AlignCenter)
            if result.driver_code == self._our_driver:
                driver_item.setFont(QFont("", -1, QFont.Bold))
                driver_item.setBackground(QBrush(QColor(100, 149, 237, 100)))
            self.standings_table.setItem(row, 1, driver_item)
            
            # Team
            self.standings_table.setItem(row, 2, QTableWidgetItem(result.team))
            
            # Grid
            grid_item = QTableWidgetItem(str(result.grid_position))
            grid_item.setTextAlignment(Qt.AlignCenter)
            self.standings_table.setItem(row, 3, grid_item)
            
            # Change
            change = result.positions_gained
            if change > 0:
                change_text = f"+{change}"
                change_color = QColor(0, 150, 0)
            elif change < 0:
                change_text = str(change)
                change_color = QColor(200, 0, 0)
            else:
                change_text = "-"
                change_color = QColor(100, 100, 100)
            
            change_item = QTableWidgetItem(change_text)
            change_item.setTextAlignment(Qt.AlignCenter)
            change_item.setForeground(QBrush(change_color))
            self.standings_table.setItem(row, 4, change_item)
            
            # Gap
            if result.final_position == 1:
                gap_text = "WINNER"
            else:
                gap_text = f"+{result.gap_to_winner:.1f}s"
            gap_item = QTableWidgetItem(gap_text)
            gap_item.setTextAlignment(Qt.AlignCenter)
            self.standings_table.setItem(row, 5, gap_item)
            
            # Stops
            stops_item = QTableWidgetItem(str(result.pit_stops))
            stops_item.setTextAlignment(Qt.AlignCenter)
            self.standings_table.setItem(row, 6, stops_item)
            
            # Strategy
            self.standings_table.setItem(row, 7, QTableWidgetItem(result.strategy_notation))
            
    def _update_position_chart(self):
        """Update position history chart with SC events and pit stop markers.
        
        Note: position_plot has been moved to RaceResultAnalysisTab.
        This method is now a no-op for backward compatibility.
        """
        # [2025-01-06] position_plot moved to race_result_analysis_tab
        pass
                
    def _update_chart_highlight(self):
        """Update chart to highlight selected driver."""
        self._update_position_chart()
        
    def _update_summary(self):
        """Update driver summary section below Race Standings."""
        if not self._simulation_result or not self._our_driver:
            return
        
        # Find our driver in final_standings
        our_result = None
        if hasattr(self._simulation_result, 'our_result') and self._simulation_result.our_result:
            our_result = self._simulation_result.our_result
        else:
            # Search in final_standings
            for result in self._simulation_result.final_standings:
                if result.driver_code == self._our_driver:
                    our_result = result
                    break
        
        if not our_result:
            print(f"[FULL_RACE_TAB] Driver {self._our_driver} not found in results")
            return
        
        # Update labels
        self.lbl_final_pos.setText(f"P{our_result.final_position}")
        if our_result.final_position == 1:
            self.lbl_final_pos.setStyleSheet("font-size: 16px; font-weight: bold; color: gold;")
        elif our_result.final_position <= 3:
            self.lbl_final_pos.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        else:
            self.lbl_final_pos.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.lbl_pit_stops.setText(str(our_result.pit_stops))
        self.lbl_grid_pos.setText(f"P{our_result.grid_position}")
        self.lbl_total_time.setText(f"{our_result.total_time:.3f}s")
        
        # Positions gained with color
        gained = our_result.positions_gained
        if gained > 0:
            self.lbl_pos_gained.setText(f"+{gained}")
            self.lbl_pos_gained.setStyleSheet("color: green; font-weight: bold;")
        elif gained < 0:
            self.lbl_pos_gained.setText(str(gained))
            self.lbl_pos_gained.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.lbl_pos_gained.setText("0")
            self.lbl_pos_gained.setStyleSheet("")
        
        # Gap to leader
        if our_result.final_position == 1:
            self.lbl_gap_leader.setText("WINNER")
            self.lbl_gap_leader.setStyleSheet("color: gold; font-weight: bold;")
        else:
            self.lbl_gap_leader.setText(f"+{our_result.gap_to_winner:.3f}s")
            self.lbl_gap_leader.setStyleSheet("")
        
        # Strategy
        self.lbl_strategy.setText(our_result.strategy_notation)
        
        print(f"[FULL_RACE_TAB] Summary updated for {self._our_driver}: P{our_result.final_position}")
                
    def show_progress(self, value: int, message: str):
        """Show simulation progress."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.setVisible(False)
    
    def _update_strategy_performance_table(self):
        """
        Display top 5 strategy performance statistics from multiple simulations.
        Shows in Our Driver Summary area, not in Race Standings table.
        """
        # Clear old report buttons
        for btn in getattr(self, '_report_buttons', []):
            try:
                btn.deleteLater()
            except:
                pass
        self._report_buttons = []
        
        if not self._statistics or 'strategy_performance' not in self._statistics:
            self.strategy_perf_group.hide()
            return
        
        strategy_perf = self._statistics['strategy_performance']
        if not strategy_perf:
            self.strategy_perf_group.hide()
            return
        
        print(f"[FULL_RACE_TAB] Strategy performance: {strategy_perf}")
        
        # Sort by win rate and take top 5
        sorted_strategies = sorted(
            strategy_perf.items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )[:5]  # Top 5 only
        
        # Cache for report generation
        self._sorted_strategies = sorted_strategies
        
        # Update strategy performance table
        self.strategy_perf_table.setRowCount(len(sorted_strategies))
        
        for idx, (strategy, stats) in enumerate(sorted_strategies):
            # Strategy name (欄0)
            strat_item = QTableWidgetItem(strategy)
            strat_item.setTextAlignment(Qt.AlignCenter)
            self.strategy_perf_table.setItem(idx, 0, strat_item)
            
            # Win rate (欄1)
            win_rate = stats['win_rate']
            win_item = QTableWidgetItem(f"{win_rate:.1f}")
            win_item.setTextAlignment(Qt.AlignCenter)
            if win_rate > 20:
                win_item.setBackground(QBrush(QColor(144, 238, 144)))  # Light green
            elif win_rate > 10:
                win_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow
            self.strategy_perf_table.setItem(idx, 1, win_item)
            
            # Average position (欄2)
            avg_pos = stats['avg_position']
            avg_item = QTableWidgetItem(f"P{avg_pos:.1f}")
            avg_item.setTextAlignment(Qt.AlignCenter)
            self.strategy_perf_table.setItem(idx, 2, avg_item)
            
            # Most likely position (欄3) - 新增！
            most_likely_pos = stats.get('most_likely_position', round(avg_pos))
            most_likely_item = QTableWidgetItem(f"P{most_likely_pos}")
            most_likely_item.setTextAlignment(Qt.AlignCenter)
            most_likely_item.setFont(QFont("", -1, QFont.Bold))  # 加粗強調
            if most_likely_pos <= 3:
                most_likely_item.setBackground(QBrush(QColor(255, 215, 0, 120)))  # Gold highlight
            elif most_likely_pos <= 6:
                most_likely_item.setBackground(QBrush(QColor(144, 238, 144, 100)))  # Green
            self.strategy_perf_table.setItem(idx, 3, most_likely_item)
            
            # Most likely position probability (欄4) - 新增！
            most_likely_pct = stats.get('most_likely_position_pct', 0)
            prob_item = QTableWidgetItem(f"{most_likely_pct:.1f}")
            prob_item.setTextAlignment(Qt.AlignCenter)
            if most_likely_pct > 30:  # 穩定性高
                prob_item.setBackground(QBrush(QColor(46, 125, 50, 80)))  # Dark green
                prob_item.setForeground(QBrush(QColor(255, 255, 255)))  # White text
            elif most_likely_pct > 20:
                prob_item.setBackground(QBrush(QColor(144, 238, 144, 100)))  # Light green
            self.strategy_perf_table.setItem(idx, 4, prob_item)
            
            # Best position (欄5)
            best_pos = stats.get('best_position', 20)
            best_item = QTableWidgetItem(f"P{best_pos}")
            best_item.setTextAlignment(Qt.AlignCenter)
            if best_pos == 1:
                best_item.setForeground(QBrush(QColor(255, 215, 0)))  # Gold text
            elif best_pos <= 3:
                best_item.setForeground(QBrush(QColor(192, 192, 192)))  # Silver text
            self.strategy_perf_table.setItem(idx, 5, best_item)
            
            # Worst position (欄6)
            worst_pos = stats.get('worst_position', 20)
            worst_item = QTableWidgetItem(f"P{worst_pos}")
            worst_item.setTextAlignment(Qt.AlignCenter)
            if worst_pos > 10:
                worst_item.setForeground(QBrush(QColor(200, 0, 0)))  # Red text
            self.strategy_perf_table.setItem(idx, 6, worst_item)
            
            # Report button (欄7)
            report_btn = QPushButton("Report")
            report_btn.setFixedWidth(60)
            report_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            report_btn.clicked.connect(lambda checked, row=idx: self._show_strategy_report(row))
            self.strategy_perf_table.setCellWidget(idx, 7, report_btn)  # 從第5欄改為第7欄
            self._report_buttons.append(report_btn)
        
        # Show the group
        self.strategy_perf_group.show()
    
    def _show_strategy_report(self, row: int):
        """
        Show detailed strategy report for selected row in strategy performance table.
        Uses complete race simulation data for comprehensive analysis.
        """
        if not hasattr(self, '_sorted_strategies') or row >= len(self._sorted_strategies):
            return
        
        strategy_name, stats = self._sorted_strategies[row]
        
        # Find matching OptimizationResult from cached results
        strategy_result = None
        if self._cached_results:
            for result in self._cached_results:
                result_name = getattr(result, 'strategy_name', '')
                if result_name == strategy_name:
                    strategy_result = result
                    break
        
        if not strategy_result:
            # Create a minimal result object from stats
            class MinimalResult:
                def __init__(self, name, stats):
                    self.strategy_name = name
                    self.win_probability = stats.get('win_rate', 0)
                    self.expected_position = stats.get('avg_position', 10)
                    self.stints = []
            strategy_result = MinimalResult(strategy_name, stats)
        
        # Get context data
        our_driver = self._our_driver or "VER"
        grid_position = 1
        track_name = ""
        
        # Try to get from main window
        main_window = self.window()
        if main_window:
            if hasattr(main_window, 'input_panel'):
                track_name = main_window.input_panel.track_combo.currentText()
            if hasattr(main_window, 'params') and main_window.params:
                grid_position = main_window.params.starting_position
        
        # Get simulation data for complete race analysis
        simulation_data = None
        traffic_data = None
        
        if self._simulation_result:
            simulation_data = {
                'final_standings': self._simulation_result.final_standings,
                'lap_states': getattr(self._simulation_result, 'lap_states', []),
                'race_laps': getattr(self._simulation_result, 'race_laps', 58),
                'our_result': getattr(self._simulation_result, 'our_result', None),
            }
            traffic_data = getattr(self._simulation_result, 'traffic_data', None)
        
        # Get MC summary if available
        mc_summary = self._cached_mc_summary
        
        # Get scenario analyses from SC tab if available
        scenario_analyses = None
        if main_window and hasattr(main_window, 'sc_tab'):
            scenario_analyses = getattr(main_window.sc_tab, '_cached_scenario_analyses', None)
        
        # ✅ Get Long Run data and SimulationParams (與實際模擬一致)
        long_run_data = getattr(self, '_long_run_data', None)
        sim_params = getattr(self, '_simulation_params', None)
        
        if long_run_data:
            print(f"[FULL_RACE_TAB] Report using Long Run data")
        else:
            print(f"[FULL_RACE_TAB] Report using SimulationParams defaults")
        
        # Generate report
        generator = StrategyReportGenerator()
        report_text = generator.generate_report(
            strategy_result=strategy_result,
            mc_summary=mc_summary,
            simulation_data=simulation_data,
            traffic_data=traffic_data,
            competitors_data=None,
            scenario_analyses=scenario_analyses,
            our_driver=our_driver,
            grid_position=grid_position,
            track_name=track_name,
            long_run_data=long_run_data,  # ✅ 新增
            sim_params=sim_params,  # ✅ 新增
        )
        
        # Show dialog
        dialog = StrategyReportDialog(report_text, strategy_name, self)
        dialog.exec_()
    
    def _update_traffic_analysis(self):
        """
        Update traffic analysis display from simulation results using heatmap.
        """
        if not self._simulation_result:
            self.traffic_group.hide()
            return
        
        # Prepare data for heatmap
        drivers_data = self._prepare_traffic_heatmap_data()
        
        if not drivers_data:
            self.traffic_group.hide()
            return
        
        # Update heatmap
        race_laps = self._simulation_result.race_laps
        race_info = f"{race_laps} laps"
        
        # Try to get more detailed race info if available
        if hasattr(self, 'year_edit') and hasattr(self, 'race_combo'):
            try:
                year = self.year_edit.text()
                race = self.race_combo.currentText()
                if year and race:
                    race_info = f"{year} {race} - {race_laps} laps"
            except:
                pass
        
        self.traffic_heatmap.update_data(
            drivers_data=drivers_data,
            max_lap=race_laps,
            race_info=race_info
        )
        
        # Show the group
        self.traffic_group.show()
        print(f"[FULL_RACE_TAB] Traffic heatmap updated with {len(drivers_data)} drivers")
    
    def _prepare_traffic_heatmap_data(self) -> List[Dict[str, Any]]:
        """
        Prepare traffic data for heatmap visualization.
        
        Returns:
            List of driver data dicts with lap-by-lap traffic states
        """
        if not self._simulation_result or not self._simulation_result.lap_states:
            return []
        
        # Build driver data for all drivers
        drivers_data = []
        
        # Get final standings to determine positions
        final_standings = self._simulation_result.final_standings if hasattr(self._simulation_result, 'final_standings') else []
        position_map = {standing.driver_code: standing.final_position for standing in final_standings}
        
        # Collect all unique drivers from lap_states
        all_drivers = set()
        for lap_state in self._simulation_result.lap_states:
            all_drivers.update(lap_state.positions.keys())
        
        for driver_code in sorted(all_drivers):
            lap_states_dict = {}
            blocked_count = 0
            clean_count = 0
            sc_vsc_count = 0
            
            # Analyze each lap
            for lap_state in self._simulation_result.lap_states:
                lap_num = lap_state.lap
                
                # Check if driver is in this lap
                if driver_code not in lap_state.positions:
                    lap_states_dict[lap_num] = -1  # No data
                    continue
                
                # Determine state
                if lap_state.sc_active:
                    # SC/VSC active
                    lap_states_dict[lap_num] = 2
                    sc_vsc_count += 1
                else:
                    # Check if in traffic (gap < 1.5s to car ahead)
                    position = lap_state.positions.get(driver_code, 20)
                    gap = lap_state.gaps.get(driver_code, 99.0)
                    
                    # Find gap to car ahead
                    if position > 1:
                        # Find car ahead
                        car_ahead = None
                        for d, p in lap_state.positions.items():
                            if p == position - 1:
                                car_ahead = d
                                break
                        
                        if car_ahead:
                            gap_ahead = lap_state.gaps.get(driver_code, 99.0) - lap_state.gaps.get(car_ahead, 0.0)
                            
                            if abs(gap_ahead) < 1.5:
                                # In traffic
                                lap_states_dict[lap_num] = 1
                                blocked_count += 1
                            else:
                                # Clean lap
                                lap_states_dict[lap_num] = 0
                                clean_count += 1
                        else:
                            # Clean lap (no car ahead found)
                            lap_states_dict[lap_num] = 0
                            clean_count += 1
                    else:
                        # Leader - always clean
                        lap_states_dict[lap_num] = 0
                        clean_count += 1
            
            # Build driver data
            drivers_data.append({
                "driver_code": driver_code,
                "final_position": position_map.get(driver_code, 20),
                "lap_states": lap_states_dict,
                "traffic_stats": {
                    "blocked_laps": blocked_count,
                    "clean_laps": clean_count,
                    "sc_vsc_laps": sc_vsc_count
                }
            })
        
        return drivers_data
    
    def _update_mc_statistics(self):
        """
        Update Monte Carlo statistics display.
        
        Shows aggregated data from multiple simulation runs.
        """
        if not self._statistics or not self._our_driver:
            if hasattr(self, 'mc_stats_group'):
                self.mc_stats_group.hide()
            return
        
        # Show MC stats group
        if hasattr(self, 'mc_stats_group'):
            self.mc_stats_group.show()
        
        # Get our driver's statistics
        our_stats = self._statistics.get('our_stats', {})
        iterations = self._statistics.get('iterations', 0)
        
        # Update labels if they exist
        if hasattr(self, 'lbl_mc_iterations'):
            self.lbl_mc_iterations.setText(f"{iterations} runs")
        
        if hasattr(self, 'lbl_mc_avg_pos'):
            avg_pos = our_stats.get('avg_position', 0)
            self.lbl_mc_avg_pos.setText(f"P{avg_pos:.1f}")
        
        if hasattr(self, 'lbl_mc_win_rate'):
            win_prob = our_stats.get('win_probability', 0)
            self.lbl_mc_win_rate.setText(f"{win_prob:.1f}%")
            self.lbl_mc_win_rate.setStyleSheet(
                f"font-size: 14px; color: {'green' if win_prob > 20 else 'black'};"
            )
        
        if hasattr(self, 'lbl_mc_podium_rate'):
            podium_prob = our_stats.get('podium_probability', 0)
            self.lbl_mc_podium_rate.setText(f"{podium_prob:.1f}%")
            self.lbl_mc_podium_rate.setStyleSheet(
                f"font-size: 14px; color: {'blue' if podium_prob > 50 else 'black'};"
            )
        
        if hasattr(self, 'lbl_mc_points_rate'):
            points_prob = our_stats.get('points_probability', 0)
            self.lbl_mc_points_rate.setText(f"{points_prob:.1f}%")
        
        if hasattr(self, 'lbl_mc_avg_gain'):
            avg_gain = our_stats.get('avg_gain', 0)
            self.lbl_mc_avg_gain.setText(
                f"{avg_gain:+.1f} pos" if avg_gain != 0 else "0.0 pos"
            )
            self.lbl_mc_avg_gain.setStyleSheet(
                f"font-size: 14px; color: {'green' if avg_gain > 0 else 'red' if avg_gain < 0 else 'black'};"
            )
        
        print(f"[FULL_RACE_TAB] MC Stats updated: {iterations} iterations, "
              f"Avg P{avg_pos if 'avg_pos' in locals() else 0:.1f}, "
              f"Win {win_prob if 'win_prob' in locals() else 0:.1f}%, "
              f"Podium {podium_prob if 'podium_prob' in locals() else 0:.1f}%")

    def _update_laptime_comparison(self):
        """
        Update lap time comparison chart.
        
        Note: laptime_plot and driver comparison combos have been moved to RaceResultAnalysisTab.
        This method is now a no-op for backward compatibility.
        """
        # [2025-01-06] laptime_plot moved to race_result_analysis_tab
        pass
