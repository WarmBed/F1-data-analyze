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
    QProgressBar, QGridLayout
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
        
        # Main content: Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Standings Table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        standings_group = QGroupBox(tr("RACE_STANDINGS", "Race Standings"))
        standings_layout = QVBoxLayout(standings_group)
        
        self.standings_table = self._create_standings_table()
        standings_layout.addWidget(self.standings_table)
        
        left_layout.addWidget(standings_group)
        splitter.addWidget(left_widget)
        
        # Right: Charts and Analysis
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Position Chart
        chart_group = QGroupBox(tr("POSITION_CHART", "Position History"))
        chart_layout = QVBoxLayout(chart_group)
        
        if HAS_PYQTGRAPH:
            self.position_plot = pg.PlotWidget()
            self.position_plot.setBackground('w')
            self.position_plot.setLabel('left', tr("POSITION", "Position"))
            self.position_plot.setLabel('bottom', tr("LAP", "Lap"))
            self.position_plot.showGrid(x=True, y=True, alpha=0.3)
            self.position_plot.invertY(True)  # P1 at top
            chart_layout.addWidget(self.position_plot)
        else:
            chart_layout.addWidget(QLabel(tr("PYQTGRAPH_REQUIRED", "pyqtgraph required for charts")))
        
        right_layout.addWidget(chart_group, 2)
        
        # Our Driver Summary
        summary_group = QGroupBox(tr("OUR_DRIVER_SUMMARY", "Our Driver Summary"))
        self.summary_layout = QGridLayout(summary_group)
        self._setup_summary_labels()
        right_layout.addWidget(summary_group, 1)
        
        # Monte Carlo Statistics (if available)
        self.mc_stats_group = QGroupBox(tr("MONTE_CARLO_STATS", "Monte Carlo Statistics"))
        self.mc_stats_layout = QGridLayout(self.mc_stats_group)
        self._setup_mc_stats_labels()
        right_layout.addWidget(self.mc_stats_group, 1)
        self.mc_stats_group.hide()  # Initially hidden until we have MC data
        
        splitter.addWidget(right_widget)
        
        # Set splitter sizes
        splitter.setSizes([400, 600])
        layout.addWidget(splitter, 1)
        
        # Bottom: Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel(tr("READY_TO_SIMULATE", "Ready to simulate. Load FP2 data and run."))
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
        
    def _create_controls(self) -> QHBoxLayout:
        """Create control buttons."""
        layout = QHBoxLayout()
        
        # Our Strategy Selection
        layout.addWidget(QLabel(tr("OUR_STRATEGY", "Our Strategy") + ":"))
        self.plan_combo = QComboBox()
        self.plan_combo.setMinimumWidth(120)
        self.plan_combo.setToolTip(tr("SELECT_PLAN_TOOLTIP", "Select which plan to test in full race simulation"))
        layout.addWidget(self.plan_combo)
        
        layout.addSpacing(20)
        
        # SC Scenario Selection
        layout.addWidget(QLabel(tr("SC_SCENARIO", "SC Scenario") + ":"))
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
        layout.addWidget(self.sc_scenario_combo)
        
        layout.addSpacing(20)
        
        # Iterations
        layout.addWidget(QLabel(tr("ITERATIONS", "Iterations") + ":"))
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(10, 1000)
        self.iterations_spin.setValue(100)
        self.iterations_spin.setSingleStep(50)
        layout.addWidget(self.iterations_spin)
        
        layout.addSpacing(20)
        
        # Driver highlight
        layout.addWidget(QLabel(tr("HIGHLIGHT_DRIVER", "Highlight") + ":"))
        self.driver_combo = QComboBox()
        self.driver_combo.setMinimumWidth(100)
        self.driver_combo.currentTextChanged.connect(self._on_driver_selected)
        layout.addWidget(self.driver_combo)
        
        layout.addStretch()
        
        # Run Full Race button (uses MC strategy assignments)
        self.run_btn = QPushButton(tr("RUN_FULL_RACE", "執行完整賽事"))
        self.run_btn.setMinimumWidth(200)
        self.run_btn.setToolTip(tr("RUN_FULL_RACE_TOOLTIP", "使用 MC 策略分配執行 20 車完整模擬"))
        self.run_btn.setEnabled(False)  # Disabled until MC results received
        self.run_btn.clicked.connect(self._on_run_full_race_clicked)
        layout.addWidget(self.run_btn)
        
        return layout
    
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
    
    def _setup_summary_labels(self):
        """Setup summary labels."""
        labels = [
            ("lbl_driver", tr("DRIVER", "Driver"), 0, 0),
            ("lbl_position", tr("FINAL_POSITION", "Final Position"), 0, 2),
            ("lbl_grid", tr("GRID_POSITION", "Grid Position"), 1, 0),
            ("lbl_change", tr("POSITIONS_CHANGED", "Positions Changed"), 1, 2),
            ("lbl_gap", tr("GAP_TO_WINNER", "Gap to Winner"), 2, 0),
            ("lbl_win_prob", tr("WIN_PROBABILITY", "Win Probability"), 2, 2),
            ("lbl_podium_prob", tr("PODIUM_PROBABILITY", "Podium Probability"), 3, 0),
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
        """Set available drivers for highlighting."""
        self.driver_combo.clear()
        self.driver_combo.addItems(driver_list)
    
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
        if not self._cached_mc_summary or not self._cached_results or not self._cached_params:
            self.status_label.setText(
                tr("NO_MC_RESULTS", "請先在主畫面執行 Monte Carlo 模擬")
            )
            self.status_label.setStyleSheet("color: #d32f2f;")
            return
        
        # Get selected strategy
        selected_plan_index = self.plan_combo.currentIndex()
        if selected_plan_index < 0 or selected_plan_index >= len(self._cached_results):
            self.status_label.setText(tr("INVALID_PLAN", "無效的策略選擇"))
            return
        
        # Get SC scenario
        sc_scenario_index = self.sc_scenario_combo.currentIndex()
        sc_scenario_map = ["random", "none", "early", "mid", "late"]
        sc_scenario = sc_scenario_map[sc_scenario_index]
        
        # Get iterations
        iterations = self.iterations_spin.value()
        
        print(f"[FULL_RACE_TAB] Requesting full race simulation: Plan {chr(65 + selected_plan_index)}, SC: {sc_scenario}, Iterations: {iterations}")
        
        # Emit signal to main window (will use MC strategy assignments)
        self.simulation_requested.emit({
            'iterations': iterations,
            'selected_plan_index': selected_plan_index,
            'sc_scenario': sc_scenario
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
        
        # Update summary labels
        avg_pos = result.expected_position if hasattr(result, 'expected_position') else 0
        podium_prob = result.podium_probability if hasattr(result, 'podium_probability') else 0
        points_prob = result.points_probability if hasattr(result, 'points_probability') else 0
        
        self.lbl_position.setText(f"P{avg_pos:.1f}")
        self.lbl_win_prob.setText(f"{win_rate:.1f}%")
        self.lbl_podium_prob.setText(f"{podium_prob:.1f}%")
        self.lbl_points_prob.setText(f"{points_prob:.1f}%")
        
        # Update driver label if available
        if hasattr(self, 'lbl_driver') and self._our_driver:
            self.lbl_driver.setText(self._our_driver)
        
        # Update grid position if available
        if hasattr(self, 'lbl_grid') and hasattr(mc, 'starting_position'):
            self.lbl_grid.setText(f"P{mc.starting_position}")
        
        # Calculate positions changed
        if hasattr(mc, 'starting_position'):
            pos_change = mc.starting_position - avg_pos
            if hasattr(self, 'lbl_change'):
                if pos_change > 0:
                    self.lbl_change.setText(f"+{pos_change:.1f}")
                    self.lbl_change.setStyleSheet("color: green; font-weight: bold;")
                elif pos_change < 0:
                    self.lbl_change.setText(f"{pos_change:.1f}")
                    self.lbl_change.setStyleSheet("color: red; font-weight: bold;")
                else:
                    self.lbl_change.setText("0.0")
                    self.lbl_change.setStyleSheet("color: gray;")
        
        # Show MC stats if available
        if hasattr(self, 'mc_stats_group'):
            self.mc_stats_group.show()
            iterations = mc.iterations if hasattr(mc, 'iterations') else 1000
            self.lbl_mc_iterations.setText(str(iterations))
            self.lbl_mc_avg_pos.setText(f"P{avg_pos:.1f}")
            self.lbl_mc_win_rate.setText(f"{win_rate:.1f}%")
            self.lbl_mc_podium_rate.setText(f"{podium_prob:.1f}%")
            self.lbl_mc_points_rate.setText(f"{points_prob:.1f}%")
            
            avg_gain = result.avg_positions_gained if hasattr(result, 'avg_positions_gained') else 0
            self.lbl_mc_avg_gain.setText(f"+{avg_gain:.1f}" if avg_gain > 0 else f"{avg_gain:.1f}")
        
        # Display position distribution if available
        if hasattr(result, 'position_distribution') and result.position_distribution:
            self._display_position_distribution(result.position_distribution, strategy_name)
        else:
            # Clear chart and show message
            self._clear_chart_with_message()
        
        # Update standings table with statistical summary
        self._display_statistical_summary(result, sc_scenario, win_rate)
        
        print(f"[FULL_RACE_TAB] Displayed MC stats for {strategy_name}: WinRate={win_rate:.1f}%, AvgPos=P{avg_pos:.1f}")
    
    def _display_position_distribution(self, distribution: dict, strategy_name: str):
        """Display position distribution histogram."""
        if not HAS_PYQTGRAPH:
            return
        
        self.position_plot.clear()
        
        # Extract positions and frequencies
        positions = sorted(distribution.keys())
        frequencies = [distribution[p] for p in positions]
        
        # Create bar graph
        bargraph = pg.BarGraphItem(
            x=positions,
            height=frequencies,
            width=0.8,
            brush='b'
        )
        self.position_plot.addItem(bargraph)
        
        # Update labels
        self.position_plot.setLabel('left', tr("FREQUENCY", "频率 (%)"))
        self.position_plot.setLabel('bottom', tr("FINISH_POSITION", "完赛位置"))
        self.position_plot.setTitle(f"{strategy_name} - {tr('POSITION_DISTRIBUTION', '位置分布')}")
    
    def _clear_chart_with_message(self):
        """Clear chart and display message about MC-only data."""
        if not HAS_PYQTGRAPH:
            return
        
        self.position_plot.clear()
        
        # Add text item explaining no detailed simulation
        text_item = pg.TextItem(
            text=tr('MC_STATS_ONLY', 
                   'Monte Carlo 統計結果\n'
                   '(無詳細逐圈數據)\n\n'
                   '顯示策略的統計表現\n'
                   '而非單次完整比賽模擬'),
            anchor=(0.5, 0.5),
            color=(100, 100, 100)
        )
        text_item.setPos(30, 10)
        self.position_plot.addItem(text_item)
    
    def _display_statistical_summary(self, result, sc_scenario: str, win_rate: float):
        """Display statistical summary in standings table."""
        self.standings_table.setRowCount(5)
        
        # Row 0: Strategy info
        self.standings_table.setItem(0, 0, QTableWidgetItem(tr("STRATEGY", "策略")))
        self.standings_table.setItem(0, 1, QTableWidgetItem(result.strategy_name))
        
        # Row 1: SC Scenario
        self.standings_table.setItem(1, 0, QTableWidgetItem(tr("SC_SCENARIO", "SC 場景")))
        self.standings_table.setItem(1, 1, QTableWidgetItem(sc_scenario.upper()))
        
        # Row 2: Win Rate
        self.standings_table.setItem(2, 0, QTableWidgetItem(tr("WIN_RATE", "勝率")))
        self.standings_table.setItem(2, 1, QTableWidgetItem(f"{win_rate:.1f}%"))
        
        # Row 3: Avg Position
        avg_pos = result.expected_position if hasattr(result, 'expected_position') else 0
        self.standings_table.setItem(3, 0, QTableWidgetItem(tr("AVG_POSITION", "平均位置")))
        self.standings_table.setItem(3, 1, QTableWidgetItem(f"P{avg_pos:.1f}"))
        
        # Row 4: Podium/Points
        podium_prob = result.podium_probability if hasattr(result, 'podium_probability') else 0
        points_prob = result.points_probability if hasattr(result, 'points_probability') else 0
        self.standings_table.setItem(4, 0, QTableWidgetItem(tr("PODIUM_POINTS", "頒獎台/積分")))
        self.standings_table.setItem(4, 1, QTableWidgetItem(f"{podium_prob:.0f}% / {points_prob:.0f}%"))
    
    def set_strategies(self, results: List):
        """
        Set available strategies for our driver selection.
        
        Args:
            results: List of StrategyResult from optimization
        """
        self.plan_combo.clear()
        
        if not results:
            self.plan_combo.addItem(tr("NO_STRATEGIES", "No strategies available"))
            self.plan_combo.setEnabled(False)
            return
        
        self.plan_combo.setEnabled(True)
        
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
        
        Args:
            result: Dict with 'single' (FullRaceSimulation) and 'statistics' (multi-run stats)
        """
        print(f"[FULL_RACE_TAB] ====== UPDATE_SIMULATION_RESULT CALLED ======")
        print(f"[FULL_RACE_TAB] Result keys: {result.keys() if result else 'None'}")
        print(f"[FULL_RACE_TAB] Has 'single': {'single' in result if result else False}")
        print(f"[FULL_RACE_TAB] Has 'statistics': {'statistics' in result if result else False}")
        
        self._simulation_result = result.get('single')
        self._statistics = result.get('statistics')
        
        print(f"[FULL_RACE_TAB] _simulation_result type: {type(self._simulation_result)}")
        print(f"[FULL_RACE_TAB] _statistics type: {type(self._statistics)}")
        
        if self._simulation_result:
            print(f"[FULL_RACE_TAB] Updating standings table...")
            self._update_standings_table()
            print(f"[FULL_RACE_TAB] Updating position chart...")
            self._update_position_chart()
        else:
            print(f"[FULL_RACE_TAB] ⚠️ No simulation result to display!")
        
        print(f"[FULL_RACE_TAB] Updating summary...")
        self._update_summary()
        
        # Update Monte Carlo statistics if available
        if self._statistics:
            print(f"[FULL_RACE_TAB] Updating MC statistics...")
            self._update_mc_statistics()
        else:
            print(f"[FULL_RACE_TAB] ⚠️ No statistics to display!")
        
        self.status_label.setText(tr("SIMULATION_COMPLETE_MSG", "Simulation complete. Select a driver to highlight."))
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
                gap_text = f"+{result.gap_to_winner:.3f}s"
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
        """Update position history chart with SC events and pit stop markers."""
        if not HAS_PYQTGRAPH or not self._simulation_result:
            return
        
        self.position_plot.clear()
        
        # Get all drivers' position history
        lap_states = self._simulation_result.lap_states
        if not lap_states:
            return
        
        laps = list(range(1, len(lap_states) + 1))
        
        # Add SC event regions
        sc_events = self._simulation_result.sc_events
        for event in sc_events:
            start_lap = event.get('lap', 0)
            duration = event.get('duration', 3)
            is_vsc = event.get('is_vsc', False)
            
            color = (255, 255, 0, 50) if is_vsc else (255, 200, 0, 80)  # Yellow for SC
            region = pg.LinearRegionItem(
                values=[start_lap, start_lap + duration],
                orientation='vertical',
                brush=color,
                movable=False
            )
            self.position_plot.addItem(region)
            
            # Add SC label
            sc_text = pg.TextItem(
                text=f"{'VSC' if is_vsc else 'SC'} L{start_lap}",
                color='#f39c12',
                anchor=(0, 0)
            )
            sc_text.setPos(start_lap, 1)
            self.position_plot.addItem(sc_text)
        
        # Color map for teams (simplified)
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7',
                  '#dfe6e9', '#74b9ff', '#a29bfe', '#fd79a8', '#00b894',
                  '#e17055', '#0984e3', '#6c5ce7', '#2d3436', '#00cec9',
                  '#fab1a0', '#81ecec', '#55efc4', '#ffeaa7', '#b2bec3']
        
        # Draw position lines for all drivers
        driver_positions = {}
        for lap_state in lap_states:
            for driver, pos in lap_state.positions.items():
                if driver not in driver_positions:
                    driver_positions[driver] = []
                driver_positions[driver].append(pos)
        
        for i, (driver_code, positions) in enumerate(driver_positions.items()):
            color = colors[i % len(colors)]
            width = 3 if driver_code == self._our_driver else 1
            alpha = 255 if driver_code == self._our_driver else 150
            
            pen = pg.mkPen(color, width=width)
            self.position_plot.plot(
                laps[:len(positions)], positions,
                pen=pen,
                name=driver_code
            )
        
        # Highlight our driver with thicker line
        if self._our_driver and self._our_driver in driver_positions:
            positions = driver_positions[self._our_driver]
            self.position_plot.plot(
                laps[:len(positions)], positions,
                pen=pg.mkPen('#e74c3c', width=4),
                name=f"{self._our_driver} (You)"
            )
            
            # Add pit stop markers for our driver
            for lap_state in lap_states:
                if self._our_driver in lap_state.pit_stops:
                    pit_lap = lap_state.lap
                    pit_pos = lap_state.positions.get(self._our_driver, 10)
                    
                    # Add pit marker
                    pit_marker = pg.ScatterPlotItem(
                        [pit_lap], [pit_pos],
                        symbol='o',
                        size=12,
                        brush=pg.mkBrush('#e74c3c'),
                        pen=pg.mkPen('w', width=2)
                    )
                    self.position_plot.addItem(pit_marker)
        
        # Set axis limits
        self.position_plot.setYRange(0.5, 20.5)
        self.position_plot.setXRange(1, len(laps))
                
    def _update_chart_highlight(self):
        """Update chart to highlight selected driver."""
        self._update_position_chart()
        
    def _update_summary(self):
        """Update driver summary section."""
        if not self._our_driver:
            return
        
        # Update from single simulation
        if self._simulation_result and self._simulation_result.our_result:
            result = self._simulation_result.our_result
            self.lbl_driver.setText(result.driver_code)
            self.lbl_position.setText(f"P{result.final_position}")
            self.lbl_grid.setText(f"P{result.grid_position}")
            
            change = result.positions_gained
            if change > 0:
                self.lbl_change.setText(f"+{change}")
                self.lbl_change.setStyleSheet("color: green; font-size: 14px;")
            elif change < 0:
                self.lbl_change.setText(str(change))
                self.lbl_change.setStyleSheet("color: red; font-size: 14px;")
            else:
                self.lbl_change.setText("0")
                self.lbl_change.setStyleSheet("font-size: 14px;")
            
            self.lbl_gap.setText(f"+{result.gap_to_winner:.3f}s" if result.final_position > 1 else "WINNER")
        
        # Update from statistics
        if self._statistics:
            our_stats = self._statistics.get('our_stats', {})
            if our_stats:
                self.lbl_win_prob.setText(f"{our_stats.get('win_probability', 0):.1f}%")
                self.lbl_podium_prob.setText(f"{our_stats.get('podium_probability', 0):.1f}%")
                self.lbl_points_prob.setText(f"{our_stats.get('points_probability', 0):.1f}%")
                
    def show_progress(self, value: int, message: str):
        """Show simulation progress."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.setVisible(False)
    
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
