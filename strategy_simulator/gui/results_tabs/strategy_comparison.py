#!/usr/bin/env python3
"""
Strategy Comparison Tab

Displays ranked strategies with details and Monte Carlo results.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QLabel, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# Import i18n with lazy loading
from strategy_simulator.gui.i18n_helper import tr


class StrategyComparisonTab(QWidget):
    """
    Strategy comparison tab showing ranked strategies.
    
    Layout:
    ┌───────────────────────────────────────┐
    │ Strategy Ranking Table                │
    │ ┌───┬───────┬────┬─────────┬────────┐ │
    │ │Rank│ Plan │Stops│ Notation │ Delta  │ │
    │ ├───┼───────┼────┼─────────┼────────┤ │
    │ │ 1 │Plan A│  1 │  M→H    │ +0.000 │ │
    │ │ 2 │Plan B│  1 │  M→S    │ +2.345 │ │
    │ └───┴───────┴────┴─────────┴────────┘ │
    ├───────────────────────────────────────┤
    │ Selected Strategy Details             │
    │ Stint 1: MEDIUM (Lap 1-22)           │
    │ Stint 2: HARD (Lap 23-53)            │
    └───────────────────────────────────────┘
    """
    
    strategy_selected = pyqtSignal(int)  # Emits selected row index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: List = []
        self._mc_results = None
        self._blocking_data: dict = {}  # From BlockingAnalyzer
        self._opponent_strategies: dict = {}  # From OpponentStrategyPredictor
        self._track_config = None  # Track configuration with overtaking_difficulty
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Splitter for table and details
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Top: Ranking table
        table_group = QGroupBox(tr("STRATEGY_RANKING", "Strategy Ranking"))
        table_layout = QVBoxLayout(table_group)
        
        self.ranking_table = QTableWidget()
        self.ranking_table.setColumnCount(9)  # Added Position, +/- columns
        self.ranking_table.setHorizontalHeaderLabels([
            tr("RANK", "Rank"), 
            tr("PLAN", "Plan"), 
            tr("STOPS", "Stops"), 
            tr("STRATEGY", "Strategy"), 
            tr("TOTAL_TIME", "Total Time"), 
            tr("GAP", "Gap"), 
            tr("PIT_LOSS", "Pit Loss"),
            tr("POSITION", "Position"),  # Predicted finish position
            tr("CHANGE", "+/-")  # Positions gained/lost
        ])
        
        # Configure table
        header = self.ranking_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Rank
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Plan
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Stops
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Strategy
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Time
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # Delta
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # Pit Loss
        header.setSectionResizeMode(7, QHeaderView.Fixed)  # Position
        header.setSectionResizeMode(8, QHeaderView.Fixed)  # +/-
        
        self.ranking_table.setColumnWidth(0, 50)
        self.ranking_table.setColumnWidth(1, 70)
        self.ranking_table.setColumnWidth(2, 50)
        self.ranking_table.setColumnWidth(4, 100)
        self.ranking_table.setColumnWidth(5, 80)
        self.ranking_table.setColumnWidth(6, 80)
        self.ranking_table.setColumnWidth(7, 70)
        self.ranking_table.setColumnWidth(8, 50)
        
        self.ranking_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ranking_table.setSelectionMode(QTableWidget.SingleSelection)
        self.ranking_table.setAlternatingRowColors(True)
        self.ranking_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        table_layout.addWidget(self.ranking_table)
        splitter.addWidget(table_group)
        
        # Bottom: Strategy details
        details_group = QGroupBox(tr("STRATEGY_DETAILS", "Strategy Details"))
        details_layout = QVBoxLayout(details_group)
        
        self.details_widget = StrategyDetailsWidget()
        details_layout.addWidget(self.details_widget)
        
        splitter.addWidget(details_group)
        
        # Monte Carlo results section
        mc_group = QGroupBox(tr("MC_POSITION_ANALYSIS", "Monte Carlo Position Analysis"))
        mc_group.setToolTip(
            tr("MC_TOOLTIP", "Monte Carlo: Simulates thousands of races with random events.\n"
            "Shows win probability and position improvement potential for each strategy.")
        )
        mc_layout = QVBoxLayout(mc_group)
        
        self.mc_table = QTableWidget()
        self.mc_table.setColumnCount(8)
        self.mc_table.setHorizontalHeaderLabels([
            tr("STRATEGY", "Strategy"), 
            tr("WIN_PCT", "Win%"), 
            tr("MEAN_TIME", "Mean Time"), 
            tr("STD_DEV", "Std Dev"), 
            tr("NO_SC", "No SC"), 
            tr("WITH_SC", "With SC"),
            tr("POS_GAIN", "Pos. Gain"), 
            tr("RISK", "Risk")
        ])
        
        # Add tooltips to header
        self.mc_table.horizontalHeaderItem(0).setToolTip(tr("TOOLTIP_STRATEGY", "Strategy name and tyre compound"))
        self.mc_table.horizontalHeaderItem(1).setToolTip(tr("TOOLTIP_WIN_PCT", "Win probability across all simulations"))
        self.mc_table.horizontalHeaderItem(2).setToolTip(tr("TOOLTIP_MEAN_TIME", "Average finish time across all simulations"))
        self.mc_table.horizontalHeaderItem(3).setToolTip(tr("TOOLTIP_STD_DEV", "Time standard deviation - lower = more consistent"))
        self.mc_table.horizontalHeaderItem(4).setToolTip(
            tr("TOOLTIP_NO_SC", 
               "Number of wins in races WITHOUT Safety Car\n"
               "(Out of total simulations with no SC)\n"
               "High = strategy performs well in normal conditions")
        )
        self.mc_table.horizontalHeaderItem(5).setToolTip(
            tr("TOOLTIP_WITH_SC",
               "Number of wins in races WITH Safety Car\n"
               "(Out of total simulations with SC)\n"
               "High = strategy benefits from SC timing")
        )
        self.mc_table.horizontalHeaderItem(6).setToolTip(
            tr("TOOLTIP_POS_GAIN",
               "Expected position improvement vs baseline\n"
               "Based on strategy aggressiveness")
        )
        self.mc_table.horizontalHeaderItem(7).setToolTip(
            tr("TOOLTIP_RISK",
               "Best case / Worst case position change\n"
               "Shows risk-reward ratio of strategy")
        )
        self.mc_table.horizontalHeaderItem(7).setToolTip(
            tr("TIP_RISK", "Risk Assessment\n"
            "Shows best/worst case position change\n"
            "Format: +Best / -Worst")
        )
        
        mc_header = self.mc_table.horizontalHeader()
        mc_header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.mc_table.setAlternatingRowColors(True)
        mc_layout.addWidget(self.mc_table)
        
        # MC summary
        self.mc_summary_label = QLabel("")
        self.mc_summary_label.setStyleSheet("color: #666; font-style: italic;")
        mc_layout.addWidget(self.mc_summary_label)
        
        splitter.addWidget(mc_group)
        
        # Blocking analysis section
        blocking_group = QGroupBox(tr("PIT_EXIT_BLOCKING", "Pit Exit Blocking Analysis"))
        blocking_layout = QVBoxLayout(blocking_group)
        
        self.blocking_table = QTableWidget()
        self.blocking_table.setColumnCount(5)
        self.blocking_table.setHorizontalHeaderLabels([
            tr("STRATEGY", "Strategy"),
            tr("PIT_LAP", "Pit Lap"),
            tr("BLOCKING_DRIVERS", "Blocking Drivers"),
            tr("TIME_LOSS", "Time Loss"),
            tr("ADVICE", "Advice")
        ])
        
        blocking_header = self.blocking_table.horizontalHeader()
        blocking_header.setSectionResizeMode(0, QHeaderView.Fixed)
        blocking_header.setSectionResizeMode(1, QHeaderView.Fixed)
        blocking_header.setSectionResizeMode(2, QHeaderView.Stretch)
        blocking_header.setSectionResizeMode(3, QHeaderView.Fixed)
        blocking_header.setSectionResizeMode(4, QHeaderView.Stretch)
        
        self.blocking_table.setColumnWidth(0, 100)
        self.blocking_table.setColumnWidth(1, 70)
        self.blocking_table.setColumnWidth(3, 80)
        
        self.blocking_table.setAlternatingRowColors(True)
        blocking_layout.addWidget(self.blocking_table)
        
        # Blocking summary
        self.blocking_summary_label = QLabel(tr("SET_OPPONENT_STRATEGIES", "Set opponent strategies in Opponents tab to see blocking analysis"))
        self.blocking_summary_label.setStyleSheet("color: #666; font-style: italic;")
        blocking_layout.addWidget(self.blocking_summary_label)
        
        splitter.addWidget(blocking_group)
        
        # Set splitter sizes
        splitter.setSizes([300, 150, 250, 200])
    
    def update_results(self, results: List, track_config=None, competitive_results=None):
        """
        Update table with simulation results.
        
        Args:
            results: List of StrategyResult objects
            track_config: Optional TrackConfig with overtaking_difficulty
            competitive_results: Optional list of CompetitiveResult for position predictions
        """
        self._results = results
        self._track_config = track_config  # Store for blocking analysis
        self._competitive_results = competitive_results  # Store for position display
        
        # Clear old Monte Carlo results when strategy changes
        # MC will be recalculated after simulation completes
        self._mc_results = None
        self._update_mc_table()  # Show "waiting for MC" message
        
        self.ranking_table.setRowCount(len(results))
        
        if not results:
            self.details_widget.clear()
            return
        
        best_time = results[0].total_time if results else 0
        
        # Check if we have competitive results with position data
        has_positions = competitive_results and len(competitive_results) == len(results)
        
        for row, result in enumerate(results):
            # Rank
            rank_item = QTableWidgetItem(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.ranking_table.setItem(row, 0, rank_item)
            
            # Plan name
            plan_item = QTableWidgetItem(result.strategy_name)
            plan_item.setTextAlignment(Qt.AlignCenter)
            self.ranking_table.setItem(row, 1, plan_item)
            
            # Stops
            stops_item = QTableWidgetItem(str(result.num_stops))
            stops_item.setTextAlignment(Qt.AlignCenter)
            self.ranking_table.setItem(row, 2, stops_item)
            
            # Strategy notation
            notation = result.get_stint_notation()
            strategy_item = QTableWidgetItem(notation)
            strategy_item.setFont(QFont("Consolas", 10, QFont.Bold))
            self.ranking_table.setItem(row, 3, strategy_item)
            
            # Total time
            time_item = QTableWidgetItem(result.total_time_formatted)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.ranking_table.setItem(row, 4, time_item)
            
            # Delta
            delta = result.total_time - best_time
            if row == 0:
                delta_text = tr("BEST", "Best")
                delta_color = QColor(0, 150, 0)
            else:
                delta_text = f"+{delta:.3f}"
                delta_color = QColor(150, 0, 0) if delta > 5 else QColor(100, 100, 0)
            
            delta_item = QTableWidgetItem(delta_text)
            delta_item.setTextAlignment(Qt.AlignCenter)
            delta_item.setForeground(delta_color)
            self.ranking_table.setItem(row, 5, delta_item)
            
            # Pit loss
            pit_loss_item = QTableWidgetItem(f"{result.total_pit_loss:.1f}s")
            pit_loss_item.setTextAlignment(Qt.AlignCenter)
            self.ranking_table.setItem(row, 6, pit_loss_item)
            
            # Position prediction (from competitive simulation)
            if has_positions:
                comp_result = competitive_results[row]
                
                # Predicted finish position
                pos_text = f"P{comp_result.predicted_finish_position}"
                pos_item = QTableWidgetItem(pos_text)
                pos_item.setTextAlignment(Qt.AlignCenter)
                
                # Color code by position
                if comp_result.predicted_finish_position <= 3:
                    pos_item.setForeground(QColor(0, 150, 0))  # Green for podium
                    pos_item.setFont(QFont("Consolas", 10, QFont.Bold))
                elif comp_result.predicted_finish_position <= 10:
                    pos_item.setForeground(QColor(0, 0, 150))  # Blue for points
                else:
                    pos_item.setForeground(QColor(100, 100, 100))  # Gray
                    
                self.ranking_table.setItem(row, 7, pos_item)
                
                # Positions gained/lost
                change = comp_result.positions_gained
                if change > 0:
                    change_text = f"+{change}"
                    change_color = QColor(0, 150, 0)  # Green
                elif change < 0:
                    change_text = str(change)
                    change_color = QColor(150, 0, 0)  # Red
                else:
                    change_text = "0"
                    change_color = QColor(100, 100, 100)  # Gray
                
                change_item = QTableWidgetItem(change_text)
                change_item.setTextAlignment(Qt.AlignCenter)
                change_item.setForeground(change_color)
                self.ranking_table.setItem(row, 8, change_item)
            else:
                # No competitive data - show placeholder
                pos_item = QTableWidgetItem("-")
                pos_item.setTextAlignment(Qt.AlignCenter)
                self.ranking_table.setItem(row, 7, pos_item)
                
                change_item = QTableWidgetItem("-")
                change_item.setTextAlignment(Qt.AlignCenter)
                self.ranking_table.setItem(row, 8, change_item)
        
        # Select first row
        self.ranking_table.selectRow(0)
        
        # Update blocking analysis with current results
        self._update_blocking_analysis()
    
    def _on_selection_changed(self):
        """Handle row selection change."""
        row = self.ranking_table.currentRow()
        if 0 <= row < len(self._results):
            result = self._results[row]
            self.details_widget.update_details(result)
            self.strategy_selected.emit(row)
    
    def update_monte_carlo(self, mc_results):
        """Update with Monte Carlo results."""
        self._mc_results = mc_results
        self._update_mc_table()
    
    def _update_mc_table(self):
        """Update Monte Carlo results table."""
        if not self._mc_results:
            self.mc_table.setRowCount(0)
            self.mc_summary_label.setText(tr("ENABLE_MC", "Enable Monte Carlo and run simulation"))
            return
        
        mc = self._mc_results
        ranking = mc.get_ranking()
        
        self.mc_table.setRowCount(len(ranking))
        
        for row, (name, win_pct) in enumerate(ranking):
            # Strategy
            name_item = QTableWidgetItem(name)
            name_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.mc_table.setItem(row, 0, name_item)
            
            # Win %
            win_item = QTableWidgetItem(f"{win_pct:.1f}%")
            win_item.setTextAlignment(Qt.AlignCenter)
            if row == 0:
                win_item.setForeground(QColor(0, 150, 0))
            self.mc_table.setItem(row, 1, win_item)
            
            # Mean time
            mean_time = mc.mean_times.get(name, 0)
            mins = int(mean_time // 60)
            secs = mean_time % 60
            mean_item = QTableWidgetItem(f"{mins}:{secs:06.3f}")
            mean_item.setTextAlignment(Qt.AlignCenter)
            self.mc_table.setItem(row, 2, mean_item)
            
            # Std dev
            std = mc.std_times.get(name, 0)
            std_item = QTableWidgetItem(f"{std:.3f}s")
            std_item.setTextAlignment(Qt.AlignCenter)
            std_item.setToolTip(f"Time variance: ±{std:.3f}s\nLower = more consistent")
            self.mc_table.setItem(row, 3, std_item)
            
            # Wins without SC
            sc_analysis = mc.sc_impact_analysis.get(name, {})
            wins_no_sc = sc_analysis.get('wins_without_sc', 0)
            
            # Calculate total no-SC iterations by summing all strategies' no-SC wins
            # This is an approximation, actual total may be higher
            total_no_sc_wins = sum(sc_analysis.get('wins_without_sc', 0) 
                                   for sc_analysis in mc.sc_impact_analysis.values())
            # Use mc.iterations as upper bound
            estimated_no_sc_iters = int(mc.iterations * (1 - mc.sc_occurrence_rate / 100))
            
            no_sc_item = QTableWidgetItem(str(wins_no_sc))
            no_sc_item.setTextAlignment(Qt.AlignCenter)
            no_sc_item.setToolTip(
                tr("WINS_NO_SC_DETAIL", 
                   "Absolute wins: {wins}\n"
                   "Estimated no-SC iterations: ~{total}\n"
                   "Note: 0 wins means this strategy was not optimal in no-SC scenarios").format(
                       wins=wins_no_sc, 
                       total=estimated_no_sc_iters
                   )
            )
            self.mc_table.setItem(row, 4, no_sc_item)
            
            # Wins with SC
            wins_sc = sc_analysis.get('wins_with_sc', 0)
            estimated_sc_iters = int(mc.iterations * (mc.sc_occurrence_rate / 100))
            
            sc_item = QTableWidgetItem(str(wins_sc))
            sc_item.setTextAlignment(Qt.AlignCenter)
            
            sc_benefit = tr("SC_BENEFITS", "SC benefits") if wins_sc > wins_no_sc else tr("SC_HURTS", "SC hurts") if wins_sc < wins_no_sc else tr("SC_NEUTRAL", "SC neutral")
            sc_item.setToolTip(
                tr("WINS_WITH_SC_DETAIL",
                   "Absolute wins: {wins}\n"
                   "Estimated SC iterations: ~{total}\n"
                   "Assessment: {benefit}\n"
                   "Note: 0 wins means this strategy was not optimal in SC scenarios").format(
                       wins=wins_sc,
                       total=estimated_sc_iters,
                       benefit=sc_benefit
                   )
            )
            if wins_sc > wins_no_sc * 1.5:
                sc_item.setForeground(QColor(0, 150, 0))  # Green - SC benefits
            elif wins_sc < wins_no_sc * 0.5:
                sc_item.setForeground(QColor(200, 0, 0))  # Red - SC hurts
            self.mc_table.setItem(row, 5, sc_item)
            
            # Position gain estimate
            # Based on strategy aggressiveness (early stops = more aggressive)
            pos_gain = self._estimate_position_gain(name, win_pct, std)
            pos_item = QTableWidgetItem(f"+{pos_gain['expected']}")
            pos_item.setTextAlignment(Qt.AlignCenter)
            if pos_gain['expected'] >= 3:
                pos_item.setForeground(QColor(0, 150, 0))
            elif pos_gain['expected'] >= 1:
                pos_item.setForeground(QColor(100, 150, 0))
            pos_item.setToolTip(
                tr("EXPECTED_POS_IMPROVEMENT", "Expected position improvement") + f": +{pos_gain['expected']} " + tr("PLACES", "places") + "\n" +
                tr("BASED_ON_PACE", "Based on pace advantage and strategy timing")
            )
            self.mc_table.setItem(row, 6, pos_item)
            
            # Risk assessment
            risk_text = f"+{pos_gain['best']}/-{pos_gain['worst']}"
            risk_item = QTableWidgetItem(risk_text)
            risk_item.setTextAlignment(Qt.AlignCenter)
            
            # Color based on risk/reward ratio
            risk_ratio = pos_gain['best'] / max(1, pos_gain['worst'])
            if risk_ratio >= 2.0:
                risk_item.setForeground(QColor(0, 150, 0))  # Good risk/reward
                risk_item.setToolTip(tr("FAVORABLE_RISK", "Favorable risk/reward ratio"))
            elif risk_ratio >= 1.0:
                risk_item.setForeground(QColor(150, 150, 0))  # Neutral
                risk_item.setToolTip(tr("BALANCED_RISK", "Balanced risk/reward"))
            else:
                risk_item.setForeground(QColor(200, 0, 0))  # Risky
                risk_item.setToolTip(tr("HIGH_RISK", "High risk strategy"))
            self.mc_table.setItem(row, 7, risk_item)
        
        # Summary
        self.mc_summary_label.setText(
            tr("ITERATIONS", "Iterations") + f": {mc.iterations} | " +
            tr("SC_RATE", "SC Rate") + f": {mc.sc_occurrence_rate:.1f}% | " +
            tr("MEAN_SC_COUNT", "Mean SC Count") + f": {mc.mean_sc_count:.2f}"
        )
    
    def _estimate_position_gain(self, strategy_name: str, win_pct: float, std: float) -> dict:
        """
        Estimate position gain based on strategy characteristics.
        
        Uses win percentage and time variance as proxies for pace advantage.
        
        Args:
            strategy_name: Strategy name (e.g., "Plan A: M→H")
            win_pct: Win percentage from Monte Carlo
            std: Standard deviation of finish time
            
        Returns:
            dict with 'expected', 'best', 'worst' position gains
        """
        # Base position gain from win percentage
        # Higher win % = faster strategy = more position gain potential
        if win_pct >= 50:
            base_gain = 4  # Dominant strategy
        elif win_pct >= 30:
            base_gain = 3
        elif win_pct >= 15:
            base_gain = 2
        elif win_pct >= 5:
            base_gain = 1
        else:
            base_gain = 0
            
        # Adjust based on strategy aggressiveness (parsed from name)
        # More stops and softer tyres = more aggressive
        aggressiveness = 0
        name_upper = strategy_name.upper()
        
        if 'S→' in name_upper or '→S' in name_upper:
            aggressiveness += 1  # SOFT compound
        if name_upper.count('→') >= 2:
            aggressiveness += 1  # 2+ stops
            
        # Higher std = higher variance = more risk
        risk_factor = min(3, int(std / 2))  # Every 2s std = 1 risk level
        
        expected = max(0, base_gain + aggressiveness // 2)
        best = expected + aggressiveness + 1
        worst = max(1, risk_factor + aggressiveness)
        
        return {
            'expected': expected,
            'best': min(10, best),  # Cap at 10 positions
            'worst': min(5, worst)   # Cap at 5 positions lost
        }
    
    def set_blocking_data(self, blocking_data: dict):
        """
        Set blocking analysis data for position improvement calculations.
        
        Args:
            blocking_data: Dict from BlockingAnalyzer with blocking analysis
        """
        self._blocking_data = blocking_data
        # Re-update table if MC results exist
        if self._mc_results:
            self._update_mc_table()
    
    def set_opponent_strategies(self, opponent_strategies: dict):
        """
        Set opponent strategy data for blocking analysis.
        
        Args:
            opponent_strategies: Dict from OpponentStrategyPredictor
                Format: {driver_code: OpponentStrategy, ...}
        """
        self._opponent_strategies = opponent_strategies
        self._update_blocking_analysis()
    
    def _update_blocking_analysis(self):
        """Update blocking analysis table based on opponent strategies."""
        if not self._results or not self._opponent_strategies:
            self.blocking_table.setRowCount(0)
            
            if not self._opponent_strategies:
                # No opponent strategies set
                self.blocking_summary_label.setText(
                    "⚠️ " + tr("SET_OPPONENT_STRATEGIES", "请先在 Opponents 标签页设定对手策略") + "\\n" +
                    "💡 " + tr("BLOCKING_HINT", "设定后可查看进站时间窗口冲突分析")
                )
            elif not self._results:
                # No simulation results
                self.blocking_summary_label.setText(
                    "ℹ️ " + tr("RUN_SIMULATION_FIRST", "请先执行模拟以查看阻挡分析")
                )
            return
        
        # Build opponent pit laps dict
        # Calculate estimated pit laps from tire strategy and race laps
        opponent_pit_laps = {}
        race_laps = 58  # Default
        if self._results and self._results[0].stints:
            # Stint has 'laps' attribute, not 'num_laps'
            race_laps = sum(s.laps for s in self._results[0].stints)
        
        for driver_code, strategy in self._opponent_strategies.items():
            # Check if strategy has pit_laps directly
            if isinstance(strategy, dict):
                if 'pit_laps' in strategy and strategy['pit_laps']:
                    opponent_pit_laps[driver_code] = strategy['pit_laps']
                elif 'tire_strategy' in strategy:
                    # Calculate pit laps from tire strategy
                    tire_seq = strategy['tire_strategy']
                    if isinstance(tire_seq, list) and len(tire_seq) > 1:
                        num_stints = len(tire_seq)
                        laps_per_stint = race_laps // num_stints
                        pit_laps = [laps_per_stint * (i + 1) for i in range(num_stints - 1)]
                        opponent_pit_laps[driver_code] = pit_laps
                elif 'tire_sequence' in strategy:
                    # Also check for tire_sequence (from auto-assigned strategies)
                    tire_seq = strategy['tire_sequence']
                    if isinstance(tire_seq, list) and len(tire_seq) > 1:
                        num_stints = len(tire_seq)
                        laps_per_stint = race_laps // num_stints
                        pit_laps = [laps_per_stint * (i + 1) for i in range(num_stints - 1)]
                        opponent_pit_laps[driver_code] = pit_laps
            elif hasattr(strategy, 'pit_laps') and strategy.pit_laps:
                # OpponentStrategy object
                opponent_pit_laps[driver_code] = strategy.pit_laps
            elif hasattr(strategy, 'tire_sequence') and strategy.tire_sequence:
                # OpponentStrategy without pit_laps - calculate from tire_sequence
                tire_seq = strategy.tire_sequence
                if len(tire_seq) > 1:
                    num_stints = len(tire_seq)
                    laps_per_stint = race_laps // num_stints
                    pit_laps = [laps_per_stint * (i + 1) for i in range(num_stints - 1)]
                    opponent_pit_laps[driver_code] = pit_laps
        
        if not opponent_pit_laps:
            self.blocking_table.setRowCount(0)
            self.blocking_summary_label.setText(
                tr("NO_OPPONENT_PITS", "No opponent pit data available") + 
                f" ({len(self._opponent_strategies)} drivers loaded)"
            )
            return
        
        # Get overtaking difficulty from track config
        # Higher difficulty = harder to overtake = more time loss
        overtaking_difficulty = 0.5  # Default (medium difficulty)
        if self._track_config:
            overtaking_difficulty = getattr(self._track_config, 'overtaking_difficulty', 0.5)
        
        # Base time loss per blocking car (increases with overtaking difficulty)
        # Easy track (0.0): 0.8s per car
        # Medium track (0.5): 1.5s per car
        # Hard track (1.0): 3.0s per car (Monaco-like)
        base_time_loss = 0.8 + overtaking_difficulty * 2.2
        
        # Analyze blocking for each strategy
        rows = []
        for result in self._results:
            for pit_lap in result.pit_laps:
                blocking_drivers = []
                for driver, opp_pits in opponent_pit_laps.items():
                    # Check if opponent pits within +/-1 lap
                    for opp_pit in opp_pits:
                        if abs(pit_lap - opp_pit) <= 1:
                            blocking_drivers.append(driver)
                            break
                
                if blocking_drivers:
                    # Time loss calculation with track difficulty
                    time_loss = len(blocking_drivers) * base_time_loss
                    
                    # Additional penalty for multiple blockers (queue effect)
                    if len(blocking_drivers) >= 3:
                        time_loss *= 1.2  # 20% queue penalty
                    
                    # Determine advice based on blocking severity and track difficulty
                    if len(blocking_drivers) >= 3 or (len(blocking_drivers) >= 2 and overtaking_difficulty > 0.7):
                        advice = tr("AVOID_PIT", "Consider different pit window")
                    elif len(blocking_drivers) >= 1:
                        advice = tr("POSSIBLE_TRAFFIC", "Possible traffic")
                    else:
                        advice = tr("CLEAR_AIR", "Clear air expected")
                    
                    rows.append({
                        'strategy': result.strategy_name,
                        'pit_lap': pit_lap,
                        'blocking': blocking_drivers,
                        'time_loss': time_loss,
                        'advice': advice
                    })
        
        # Update table
        self.blocking_table.setRowCount(len(rows))
        
        for row, data in enumerate(rows):
            # Strategy
            strategy_item = QTableWidgetItem(data['strategy'])
            strategy_item.setTextAlignment(Qt.AlignCenter)
            self.blocking_table.setItem(row, 0, strategy_item)
            
            # Pit lap
            pit_item = QTableWidgetItem(f"L{data['pit_lap']}")
            pit_item.setTextAlignment(Qt.AlignCenter)
            self.blocking_table.setItem(row, 1, pit_item)
            
            # Blocking drivers
            blocking_text = ', '.join(data['blocking']) if data['blocking'] else '-'
            blocking_item = QTableWidgetItem(blocking_text)
            blocking_item.setTextAlignment(Qt.AlignCenter)
            if len(data['blocking']) >= 3:
                blocking_item.setForeground(QColor(200, 0, 0))
            elif len(data['blocking']) >= 1:
                blocking_item.setForeground(QColor(180, 150, 0))
            self.blocking_table.setItem(row, 2, blocking_item)
            
            # Time loss
            time_item = QTableWidgetItem(f"+{data['time_loss']:.1f}s")
            time_item.setTextAlignment(Qt.AlignCenter)
            if data['time_loss'] >= 3.0:
                time_item.setForeground(QColor(200, 0, 0))
            self.blocking_table.setItem(row, 3, time_item)
            
            # Advice
            advice_item = QTableWidgetItem(data['advice'])
            self.blocking_table.setItem(row, 4, advice_item)
        
        # Update summary with track difficulty info
        total_conflicts = len([r for r in rows if r['blocking']])
        
        # Show track difficulty in summary
        difficulty_text = ""
        if self._track_config:
            difficulty = getattr(self._track_config, 'overtaking_difficulty', 0.5)
            if difficulty >= 0.8:
                difficulty_text = f" | {tr('TRACK_DIFFICULTY', 'Track difficulty')}: {tr('VERY_HARD', 'Very Hard')} ({difficulty:.0%})"
            elif difficulty >= 0.6:
                difficulty_text = f" | {tr('TRACK_DIFFICULTY', 'Track difficulty')}: {tr('HARD', 'Hard')} ({difficulty:.0%})"
            elif difficulty >= 0.4:
                difficulty_text = f" | {tr('TRACK_DIFFICULTY', 'Track difficulty')}: {tr('MEDIUM', 'Medium')} ({difficulty:.0%})"
            else:
                difficulty_text = f" | {tr('TRACK_DIFFICULTY', 'Track difficulty')}: {tr('EASY', 'Easy')} ({difficulty:.0%})"
        
        self.blocking_summary_label.setText(
            tr("BLOCKING_SUMMARY", "Potential pit conflicts") + f": {total_conflicts}" + difficulty_text
        )


class StrategyDetailsWidget(QWidget):
    """Widget showing detailed stint breakdown."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        self.title_label = QLabel("請選擇策略以查看詳情")
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.title_label)
        
        # Stint details container
        self.stints_layout = QVBoxLayout()
        layout.addLayout(self.stints_layout)
        
        # Summary
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("color: #666;")
        layout.addWidget(self.summary_label)
        
        layout.addStretch()
    
    def update_details(self, result):
        """Update with strategy details."""
        # Clear previous
        while self.stints_layout.count():
            item = self.stints_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Title
        self.title_label.setText(
            f"{result.strategy_name}: {result.get_stint_notation()}"
        )
        
        # Add stint details
        for i, stint in enumerate(result.stints):
            stint_frame = QFrame()
            stint_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._get_compound_color(stint.compound.value)};
                    border-radius: 5px;
                    padding: 5px;
                }}
            """)
            
            stint_layout = QHBoxLayout(stint_frame)
            stint_layout.setContentsMargins(10, 5, 10, 5)
            
            # Stint number
            stint_num = QLabel(f"節段 {i+1}")
            stint_num.setFont(QFont("Arial", 10, QFont.Bold))
            stint_layout.addWidget(stint_num)
            
            # Compound
            compound_label = QLabel(stint.compound.value)
            compound_label.setFont(QFont("Consolas", 11, QFont.Bold))
            stint_layout.addWidget(compound_label)
            
            stint_layout.addStretch()
            
            # Lap range
            lap_range = QLabel(f"圈 {stint.start_lap} - {stint.end_lap}")
            stint_layout.addWidget(lap_range)
            
            # Lap count
            lap_count = QLabel(f"({stint.laps} 圈)")
            lap_count.setStyleSheet("color: #444;")
            stint_layout.addWidget(lap_count)
            
            self.stints_layout.addWidget(stint_frame)
        
        # Pit laps
        if result.pit_laps:
            pit_text = f"進站圈: {', '.join(f'L{p}' for p in result.pit_laps)}"
        else:
            pit_text = "無進站 (無效策略)"
        
        self.summary_label.setText(
            f"總時間: {result.total_time_formatted} | "
            f"進站損失: {result.total_pit_loss:.1f}s | "
            f"{pit_text}"
        )
    
    def _get_compound_color(self, compound: str) -> str:
        """Get background color for compound."""
        colors = {
            'SOFT': '#FFE0E0',    # Light red
            'MEDIUM': '#FFFFD0',  # Light yellow
            'HARD': '#E0E0E0',    # Light gray
        }
        return colors.get(compound.upper(), '#F0F0F0')
    
    def clear(self):
        """Clear the details."""
        self.title_label.setText("請選擇策略以查看詳情")
        self.summary_label.setText("")
        
        while self.stints_layout.count():
            item = self.stints_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
