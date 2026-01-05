#!/usr/bin/env python3
"""
Opponent Analysis Tab

Undercut/Overcut window calculation and gap analysis.
Includes opponent strategy settings for blocking analysis.

Author: F1T Team
Date: 2025-12-31
"""

from typing import List, Optional, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QDoubleSpinBox, QPushButton,
    QFormLayout, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

# Import opponent strategy panel
try:
    from strategy_simulator.gui.panels.opponent_strategy_panel import OpponentStrategyPanel
    HAS_STRATEGY_PANEL = True
except ImportError:
    HAS_STRATEGY_PANEL = False

# Import i18n with lazy loading
from strategy_simulator.gui.i18n_helper import tr


class OpponentTab(QWidget):
    """
    Opponent analysis tab for Undercut/Overcut calculations.
    
    Features:
    - Opponent strategy settings (global and per-driver)
    - Undercut/Overcut window calculation
    - Gap timeline visualization
    - Optimal attack timing recommendations
    
    Signals:
        strategy_settings_changed: Emitted when opponent strategy settings change
    """
    
    strategy_settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: List = []
        self._params = None
        self._current_gap: float = 0.0
        self._predictions: List[Dict] = []
        self._mc_summary = None  # Store MC results with position predictions
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget for different sections
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Opponent Strategy Settings
        if HAS_STRATEGY_PANEL:
            self.strategy_panel = OpponentStrategyPanel()
            self.strategy_panel.settings_changed.connect(self._on_strategy_changed)
            self.tabs.addTab(self.strategy_panel, tr("OPPONENT_STRATEGIES", "Opponent Strategies"))
            # Load default drivers on init
            self.strategy_panel.load_default_drivers()
        else:
            self.strategy_panel = None
            placeholder = QLabel("OpponentStrategyPanel not available")
            self.tabs.addTab(placeholder, tr("OPPONENT_STRATEGIES", "Opponent Strategies"))
        
        # Tab 2: Undercut/Overcut Analysis
        analysis_widget = self._create_analysis_tab()
        self.tabs.addTab(analysis_widget, tr("UNDERCUT_OVERCUT", "Undercut/Overcut"))
        
        # Tab 3: Position Battle Analysis (NEW)
        position_widget = self._create_position_battle_tab()
        self.tabs.addTab(position_widget, tr("POSITION_BATTLE", "Position Battle"))
        
    def _create_analysis_tab(self) -> QWidget:
        """Create the undercut/overcut analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Top: Configuration
        config_group = QGroupBox(tr("OPPONENT_CONFIG", "Opponent Configuration"))
        config_layout = QHBoxLayout(config_group)
        
        # Our strategy
        config_layout.addWidget(QLabel(tr("OUR_STRATEGY", "Our Strategy") + ":"))
        self.our_strategy_combo = QComboBox()
        self.our_strategy_combo.currentIndexChanged.connect(self._on_config_changed)
        config_layout.addWidget(self.our_strategy_combo)
        
        config_layout.addSpacing(20)
        
        # Opponent strategy
        config_layout.addWidget(QLabel(tr("OPPONENT", "Opponent") + ":"))
        self.opp_strategy_combo = QComboBox()
        self.opp_strategy_combo.currentIndexChanged.connect(self._on_config_changed)
        config_layout.addWidget(self.opp_strategy_combo)
        
        config_layout.addSpacing(20)
        
        # Current gap
        config_layout.addWidget(QLabel(tr("CURRENT_GAP", "Current Gap") + ":"))
        self.gap_spin = QDoubleSpinBox()
        self.gap_spin.setRange(-30.0, 30.0)
        self.gap_spin.setValue(0.0)
        self.gap_spin.setSuffix(tr("SECONDS_ABBREV", "s"))
        self.gap_spin.setDecimals(1)
        self.gap_spin.valueChanged.connect(self._on_config_changed)
        config_layout.addWidget(self.gap_spin)
        
        config_layout.addStretch()
        
        # Calculate button
        calc_btn = QPushButton(tr("CALCULATE", "Calculate"))
        calc_btn.clicked.connect(self._calculate_analysis)
        config_layout.addWidget(calc_btn)
        
        layout.addWidget(config_group)
        
        # Splitter for tables and chart
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Undercut/Overcut tables
        tables_widget = QWidget()
        tables_layout = QHBoxLayout(tables_widget)
        tables_layout.setContentsMargins(0, 0, 0, 0)
        
        # Undercut table
        undercut_group = QGroupBox(tr("UNDERCUT_WINDOW", "Undercut Window"))
        undercut_layout = QVBoxLayout(undercut_group)
        
        self.undercut_table = QTableWidget()
        self.undercut_table.setColumnCount(4)
        self.undercut_table.setHorizontalHeaderLabels([
            tr("OPP_PIT", "Opponent Pit"),
            tr("WINDOW", "Window"),
            tr("ESTIMATED_GAIN", "Est. Gain"),
            tr("RECOMMENDATION", "Recommendation")
        ])
        self.undercut_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.undercut_table.setAlternatingRowColors(True)
        undercut_layout.addWidget(self.undercut_table)
        
        tables_layout.addWidget(undercut_group)
        
        # Overcut table
        overcut_group = QGroupBox(tr("OVERCUT_WINDOW", "Overcut Window"))
        overcut_layout = QVBoxLayout(overcut_group)
        
        self.overcut_table = QTableWidget()
        self.overcut_table.setColumnCount(4)
        self.overcut_table.setHorizontalHeaderLabels([
            tr("OPP_PIT", "Opponent Pit"),
            tr("WINDOW", "Window"),
            tr("ESTIMATED_GAIN", "Est. Gain"),
            tr("RECOMMENDATION", "Recommendation")
        ])
        self.overcut_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.overcut_table.setAlternatingRowColors(True)
        overcut_layout.addWidget(self.overcut_table)
        
        tables_layout.addWidget(overcut_group)
        
        splitter.addWidget(tables_widget)
        
        # Gap timeline chart
        chart_group = QGroupBox(tr("GAP_TIMELINE", "Gap Timeline Prediction"))
        chart_layout = QVBoxLayout(chart_group)
        
        if HAS_PYQTGRAPH:
            pg.setConfigOptions(antialias=True)
            
            self.gap_plot = pg.PlotWidget()
            self.gap_plot.setBackground('w')
            self.gap_plot.setLabel('left', tr("GAP", "Gap"), units='s')
            self.gap_plot.setLabel('bottom', tr("LAP", "Lap"))
            self.gap_plot.showGrid(x=True, y=True, alpha=0.3)
            
            # Add zero line
            self.gap_plot.addLine(y=0, pen=pg.mkPen('k', width=1, style=Qt.DashLine))
            
            chart_layout.addWidget(self.gap_plot)
        else:
            chart_layout.addWidget(QLabel(tr("PYQTGRAPH_NOT_INSTALLED", "pyqtgraph not installed")))
        
        splitter.addWidget(chart_group)
        
        # Set splitter sizes
        splitter.setSizes([300, 350])
        
        return widget
    
    def _on_strategy_changed(self):
        """Handle opponent strategy settings change."""
        self.strategy_settings_changed.emit()
    
    def load_predictions(self, predictions: List[Dict]):
        """
        Load FP2 prediction data and update strategy panel.
        
        Args:
            predictions: List of driver prediction dictionaries
        """
        self._predictions = predictions
        if self.strategy_panel:
            self.strategy_panel.load_predictions(predictions)
    
    def get_opponent_strategies(self) -> Dict[str, Dict]:
        """
        Get all opponent strategy settings.
        
        Returns:
            Dictionary mapping driver codes to their strategy settings
        """
        if self.strategy_panel:
            return self.strategy_panel.get_all_driver_settings()
        return {}
    
    def update_results(self, results: List, params):
        """Update with simulation results."""
        self._results = results
        self._params = params
        
        # Populate combos
        self.our_strategy_combo.clear()
        self.opp_strategy_combo.clear()
        
        for result in results:
            notation = result.get_stint_notation()
            item = f"{result.strategy_name}: {notation}"
            self.our_strategy_combo.addItem(item)
            self.opp_strategy_combo.addItem(item)
        
        # Select different strategies by default
        if len(results) >= 2:
            self.our_strategy_combo.setCurrentIndex(0)
            self.opp_strategy_combo.setCurrentIndex(1)
    
    def _on_config_changed(self):
        """Handle configuration change - auto-recalculate."""
        self._calculate_analysis()
    
    def _calculate_analysis(self):
        """Calculate undercut/overcut analysis."""
        our_idx = self.our_strategy_combo.currentIndex()
        opp_idx = self.opp_strategy_combo.currentIndex()
        
        if our_idx < 0 or opp_idx < 0:
            return
        
        if our_idx >= len(self._results) or opp_idx >= len(self._results):
            return
        
        our_result = self._results[our_idx]
        opp_result = self._results[opp_idx]
        current_gap = self.gap_spin.value()
        
        # Calculate undercut/overcut windows
        opp_pit_laps = opp_result.pit_laps
        
        undercut_data = []
        overcut_data = []
        
        for pit_lap in opp_pit_laps:
            # Undercut: pit 1-3 laps before opponent
            undercut_window = (max(1, pit_lap - 3), pit_lap - 1)
            undercut_gain = self._estimate_undercut_gain(pit_lap, our_result, opp_result)
            
            # Get recommendation key based on gain
            if undercut_gain > 1.5:
                rec_key = "STRONG"
            elif undercut_gain > 0.5:
                rec_key = "MODERATE"
            else:
                rec_key = "WEAK"
            
            undercut_data.append({
                'opp_pit': pit_lap,
                'window': undercut_window,
                'gain': undercut_gain,
                'rec': rec_key
            })
            
            # Overcut: stay out 1-3 laps after opponent
            overcut_window = (pit_lap + 1, min(self._params.race_laps, pit_lap + 3))
            overcut_gain = self._estimate_overcut_gain(pit_lap, our_result, opp_result)
            
            # Get recommendation key based on gain
            if overcut_gain > 1.5:
                rec_key = "STRONG"
            elif overcut_gain > 0.5:
                rec_key = "MODERATE"
            else:
                rec_key = "WEAK"
            
            overcut_data.append({
                'opp_pit': pit_lap,
                'window': overcut_window,
                'gain': overcut_gain,
                'rec': rec_key
            })
        
        # Update tables
        self._update_undercut_table(undercut_data)
        self._update_overcut_table(overcut_data)
        
        # Update gap chart
        self._update_gap_chart(our_result, opp_result, current_gap)
    
    def _estimate_undercut_gain(self, opp_pit_lap: int, our_result, opp_result) -> float:
        """Estimate time gained from undercutting."""
        # Simplified estimation
        # Gain comes from fresh tire advantage while opponent is on old tires
        
        our_pit_lap = opp_pit_lap - 1  # We pit one lap earlier
        
        if our_pit_lap < 1 or our_pit_lap > len(our_result.lap_results):
            return 0.0
        
        # Their lap time on old tires
        if opp_pit_lap <= len(opp_result.lap_results):
            their_old_tire = opp_result.lap_results[opp_pit_lap - 1].net_time
        else:
            return 0.0
        
        # Estimated gain from tire advantage (2-3s on outlap)
        tire_advantage = 2.0
        
        # Minus our outlap disadvantage
        outlap_loss = 1.5
        
        return tire_advantage - outlap_loss
    
    def _estimate_overcut_gain(self, opp_pit_lap: int, our_result, opp_result) -> float:
        """Estimate time gained from overcutting."""
        # Gain comes from their slow outlap
        
        if opp_pit_lap >= len(opp_result.lap_results):
            return 0.0
        
        # Their outlap penalty
        outlap_penalty = 2.5
        
        # Our old tire disadvantage
        old_tire_loss = 1.0
        
        return outlap_penalty - old_tire_loss - 0.5
    
    def _update_undercut_table(self, data: List[Dict]):
        """Update undercut table."""
        self.undercut_table.setRowCount(len(data))
        
        # Define recommendation colors and labels
        rec_config = {
            'STRONG': {'color': QColor(0, 150, 0), 'label': tr("STRONG", "Strong")},
            'MODERATE': {'color': QColor(180, 150, 0), 'label': tr("MODERATE", "Moderate")},
            'WEAK': {'color': QColor(150, 0, 0), 'label': tr("WEAK", "Weak")}
        }
        
        for row, item in enumerate(data):
            # Opponent pit
            pit_item = QTableWidgetItem(f"L{item['opp_pit']}")
            pit_item.setTextAlignment(Qt.AlignCenter)
            self.undercut_table.setItem(row, 0, pit_item)
            
            # Window
            window = item['window']
            window_item = QTableWidgetItem(f"L{window[0]}-{window[1]}")
            window_item.setTextAlignment(Qt.AlignCenter)
            self.undercut_table.setItem(row, 1, window_item)
            
            # Gain
            gain = item['gain']
            gain_item = QTableWidgetItem(f"+{gain:.1f}s" if gain > 0 else f"{gain:.1f}s")
            gain_item.setTextAlignment(Qt.AlignCenter)
            gain_item.setForeground(QColor(0, 150, 0) if gain > 0 else QColor(150, 0, 0))
            self.undercut_table.setItem(row, 2, gain_item)
            
            # Recommendation
            rec_key = item['rec']
            config = rec_config.get(rec_key, {'color': QColor(100, 100, 100), 'label': rec_key})
            rec_item = QTableWidgetItem(config['label'])
            rec_item.setTextAlignment(Qt.AlignCenter)
            rec_item.setForeground(config['color'])
            rec_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.undercut_table.setItem(row, 3, rec_item)
    
    def _update_overcut_table(self, data: List[Dict]):
        """Update overcut table."""
        self.overcut_table.setRowCount(len(data))
        
        # Define recommendation colors and labels
        rec_config = {
            'STRONG': {'color': QColor(0, 150, 0), 'label': tr("STRONG", "Strong")},
            'MODERATE': {'color': QColor(180, 150, 0), 'label': tr("MODERATE", "Moderate")},
            'WEAK': {'color': QColor(150, 0, 0), 'label': tr("WEAK", "Weak")}
        }
        
        for row, item in enumerate(data):
            # Opponent pit
            pit_item = QTableWidgetItem(f"L{item['opp_pit']}")
            pit_item.setTextAlignment(Qt.AlignCenter)
            self.overcut_table.setItem(row, 0, pit_item)
            
            # Window
            window = item['window']
            window_item = QTableWidgetItem(f"L{window[0]}-{window[1]}")
            window_item.setTextAlignment(Qt.AlignCenter)
            self.overcut_table.setItem(row, 1, window_item)
            
            # Gain
            gain = item['gain']
            gain_item = QTableWidgetItem(f"+{gain:.1f}s" if gain > 0 else f"{gain:.1f}s")
            gain_item.setTextAlignment(Qt.AlignCenter)
            gain_item.setForeground(QColor(0, 150, 0) if gain > 0 else QColor(150, 0, 0))
            self.overcut_table.setItem(row, 2, gain_item)
            
            # Recommendation
            rec_key = item['rec']
            config = rec_config.get(rec_key, {'color': QColor(100, 100, 100), 'label': rec_key})
            rec_item = QTableWidgetItem(config['label'])
            rec_item.setTextAlignment(Qt.AlignCenter)
            rec_item.setForeground(config['color'])
            rec_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.overcut_table.setItem(row, 3, rec_item)
    
    def _update_gap_chart(self, our_result, opp_result, initial_gap: float):
        """Update gap timeline chart."""
        if not HAS_PYQTGRAPH:
            return
        
        self.gap_plot.clear()
        
        # Add zero line
        self.gap_plot.addLine(y=0, pen=pg.mkPen('k', width=1, style=Qt.DashLine))
        
        # Calculate gap at each lap
        laps = []
        gaps = []
        
        cumulative_gap = initial_gap
        
        num_laps = min(len(our_result.lap_results), len(opp_result.lap_results))
        
        for lap in range(num_laps):
            our_time = our_result.lap_results[lap].net_time
            opp_time = opp_result.lap_results[lap].net_time
            
            # Positive gap = we're behind
            delta = our_time - opp_time
            cumulative_gap += delta
            
            laps.append(lap + 1)
            gaps.append(cumulative_gap)
        
        # Plot gap line
        pen = pg.mkPen((0, 114, 189), width=2)
        self.gap_plot.plot(laps, gaps, pen=pen, name=tr("GAP_TO_OPPONENT", "Gap to Opponent"))
        
        # Add markers for pit laps
        for pit_lap in our_result.pit_laps:
            if pit_lap <= len(gaps):
                self.gap_plot.addLine(
                    x=pit_lap, 
                    pen=pg.mkPen((0, 150, 0), width=1, style=Qt.DashLine)
                )
        
        for pit_lap in opp_result.pit_laps:
            if pit_lap <= len(gaps):
                self.gap_plot.addLine(
                    x=pit_lap,
                    pen=pg.mkPen((200, 0, 0), width=1, style=Qt.DashLine)
                )
        
        # Add labels
        self.gap_plot.setTitle(tr("GAP_EVOLUTION_TITLE", "Gap Evolution (positive = behind)"))

    def _create_position_battle_tab(self) -> QWidget:
        """Create the position battle analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Info label
        info_label = QLabel(
            tr("POSITION_BATTLE_INFO", 
               "This tab shows position battles with nearby opponents based on Monte Carlo predictions.")
        )
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Starting position info
        self.battle_position_label = QLabel()
        self.battle_position_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 10px;
                background-color: #2d3436;
                color: #dfe6e9;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.battle_position_label)
        
        # Nearby opponents table
        battle_group = QGroupBox(tr("NEARBY_OPPONENTS", "Nearby Opponents"))
        battle_layout = QVBoxLayout(battle_group)
        
        self.battle_table = QTableWidget()
        self.battle_table.setColumnCount(7)
        self.battle_table.setHorizontalHeaderLabels([
            tr("DRIVER", "Driver"),
            tr("POSITION", "Position"),
            tr("STRATEGY", "Strategy"),
            tr("THREAT_LEVEL", "Threat"),
            tr("UNDERCUT_RISK", "Undercut Risk"),
            tr("OVERCUT_RISK", "Overcut Risk"),
            tr("RECOMMENDATION", "Action")
        ])
        
        header = self.battle_table.horizontalHeader()
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        self.battle_table.setAlternatingRowColors(True)
        battle_layout.addWidget(self.battle_table)
        
        layout.addWidget(battle_group)
        
        # Position prediction summary
        prediction_group = QGroupBox(tr("POSITION_PREDICTION_SUMMARY", "Position Prediction"))
        prediction_layout = QVBoxLayout(prediction_group)
        
        self.prediction_label = QLabel()
        self.prediction_label.setWordWrap(True)
        self.prediction_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                color: #2d3436;
            }
        """)
        prediction_layout.addWidget(self.prediction_label)
        
        layout.addWidget(prediction_group)
        
        # Initial state
        self._update_position_battle_empty()
        
        return widget
    
    def _update_position_battle_empty(self):
        """Show empty state for position battle tab."""
        self.battle_position_label.setText(
            tr("RUN_MC_FOR_BATTLE", "Run Monte Carlo simulation to see position battle analysis.")
        )
        self.battle_table.setRowCount(0)
        self.prediction_label.setText("")
    
    def update_position_predictions(self, mc_summary, starting_position: int):
        """
        Update position battle analysis with MC results.
        
        Args:
            mc_summary: MonteCarloSummary with position_predictions
            starting_position: Our grid position
        """
        self._mc_summary = mc_summary
        
        if mc_summary is None or not hasattr(mc_summary, 'position_predictions'):
            self._update_position_battle_empty()
            return
        
        # Update position label
        self.battle_position_label.setText(
            f'{tr("OUR_POSITION", "Our Position")}: <b style="color:#74b9ff;">P{starting_position}</b> | '
            f'{tr("ANALYZING_OPPONENTS", "Analyzing nearby opponents...")}'
        )
        
        # Generate battle analysis with nearby opponents
        battle_data = self._analyze_position_battles(starting_position, mc_summary)
        self._update_battle_table(battle_data)
        
        # Update prediction summary
        self._update_prediction_summary(starting_position, mc_summary)
    
    def _analyze_position_battles(self, our_position: int, mc_summary) -> List[Dict]:
        """
        Analyze position battles with nearby opponents.
        
        Args:
            our_position: Our grid position
            mc_summary: Monte Carlo summary with predictions
        
        Returns:
            List of battle analysis dictionaries
        """
        battles = []
        
        # Get opponent strategies from panel
        if self.strategy_panel:
            opponent_settings = self.strategy_panel.get_all_driver_settings()
        else:
            opponent_settings = {}
        
        # Use FP2 predictions for driver order
        for pred in self._predictions:
            driver = pred.get("driver", "")
            rank = pred.get("rank", 20)
            
            # Focus on drivers within 3 positions of us
            if abs(rank - our_position) <= 3 and rank != our_position:
                # Get their strategy settings
                settings = opponent_settings.get(driver, {})
                tire_seq = settings.get('tire_sequence', ['M', 'H'])
                strategy_notation = "-".join(tire_seq)
                
                # Calculate threat level based on position
                if rank < our_position:
                    # They're ahead - potential target
                    threat = tr("TARGET", "Target")
                    threat_color = "green"
                else:
                    # They're behind - potential threat
                    threat = tr("THREAT", "Threat")
                    threat_color = "red"
                
                # Estimate undercut/overcut risks
                undercut_risk = self._estimate_risk_level(our_position, rank, "undercut")
                overcut_risk = self._estimate_risk_level(our_position, rank, "overcut")
                
                # Recommendation
                if rank < our_position:
                    if undercut_risk == "HIGH":
                        action = tr("ATTACK_UNDERCUT", "Attack via undercut")
                    else:
                        action = tr("ATTACK_OVERCUT", "Try overcut")
                else:
                    if undercut_risk == "HIGH":
                        action = tr("DEFEND_UNDERCUT", "Defend undercut")
                    else:
                        action = tr("MAINTAIN_PACE", "Maintain pace")
                
                battles.append({
                    'driver': driver,
                    'position': rank,
                    'strategy': strategy_notation,
                    'threat': threat,
                    'threat_color': threat_color,
                    'undercut_risk': undercut_risk,
                    'overcut_risk': overcut_risk,
                    'action': action
                })
        
        # Sort by position
        battles.sort(key=lambda x: x['position'])
        
        return battles
    
    def _estimate_risk_level(self, our_pos: int, their_pos: int, attack_type: str) -> str:
        """Estimate risk level for undercut/overcut."""
        gap = abs(their_pos - our_pos)
        
        if attack_type == "undercut":
            if gap <= 1:
                return "HIGH"
            elif gap <= 2:
                return "MEDIUM"
            else:
                return "LOW"
        else:  # overcut
            if gap <= 1:
                return "MEDIUM"
            elif gap <= 2:
                return "LOW"
            else:
                return "LOW"
    
    def _update_battle_table(self, battles: List[Dict]):
        """Update the battle analysis table."""
        self.battle_table.setRowCount(len(battles))
        
        risk_colors = {
            'HIGH': QColor(255, 100, 100),
            'MEDIUM': QColor(255, 200, 100),
            'LOW': QColor(100, 200, 100)
        }
        
        for row, battle in enumerate(battles):
            # Driver
            driver_item = QTableWidgetItem(battle['driver'])
            driver_item.setFont(QFont("Consolas", 10, QFont.Bold))
            self.battle_table.setItem(row, 0, driver_item)
            
            # Position
            pos_item = QTableWidgetItem(f"P{battle['position']}")
            pos_item.setTextAlignment(Qt.AlignCenter)
            self.battle_table.setItem(row, 1, pos_item)
            
            # Strategy
            strat_item = QTableWidgetItem(battle['strategy'])
            strat_item.setTextAlignment(Qt.AlignCenter)
            self.battle_table.setItem(row, 2, strat_item)
            
            # Threat level
            threat_item = QTableWidgetItem(battle['threat'])
            threat_item.setTextAlignment(Qt.AlignCenter)
            if battle['threat_color'] == 'green':
                threat_item.setForeground(QColor(0, 150, 0))
            else:
                threat_item.setForeground(QColor(200, 0, 0))
            self.battle_table.setItem(row, 3, threat_item)
            
            # Undercut risk
            under_item = QTableWidgetItem(battle['undercut_risk'])
            under_item.setTextAlignment(Qt.AlignCenter)
            under_item.setForeground(risk_colors.get(battle['undercut_risk'], QColor(100, 100, 100)))
            self.battle_table.setItem(row, 4, under_item)
            
            # Overcut risk
            over_item = QTableWidgetItem(battle['overcut_risk'])
            over_item.setTextAlignment(Qt.AlignCenter)
            over_item.setForeground(risk_colors.get(battle['overcut_risk'], QColor(100, 100, 100)))
            self.battle_table.setItem(row, 5, over_item)
            
            # Action
            action_item = QTableWidgetItem(battle['action'])
            action_item.setTextAlignment(Qt.AlignCenter)
            action_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.battle_table.setItem(row, 6, action_item)
    
    def _update_prediction_summary(self, starting_position: int, mc_summary):
        """Update the position prediction summary."""
        if not mc_summary.position_predictions:
            self.prediction_label.setText(tr("NO_PREDICTIONS", "No position predictions available."))
            return
        
        # Get best prediction
        best_pred = max(mc_summary.position_predictions.values(), 
                       key=lambda p: p.expected_gain)
        
        lines = []
        
        # Overall prediction
        lines.append(f"<b>{tr('RECOMMENDED_STRATEGY', 'Recommended Strategy')}: {best_pred.strategy_name}</b>")
        lines.append("")
        
        # Position change
        gain = best_pred.expected_gain
        if gain > 0:
            lines.append(f"{tr('EXPECTED_RESULT', 'Expected Result')}: "
                        f"P{starting_position} → P{best_pred.expected_position:.1f} "
                        f"(<span style='color:green;'>+{gain:.1f} {tr('POSITIONS', 'positions')}</span>)")
        elif gain < 0:
            lines.append(f"{tr('EXPECTED_RESULT', 'Expected Result')}: "
                        f"P{starting_position} → P{best_pred.expected_position:.1f} "
                        f"(<span style='color:red;'>{gain:.1f} {tr('POSITIONS', 'positions')}</span>)")
        else:
            lines.append(f"{tr('EXPECTED_RESULT', 'Expected Result')}: "
                        f"P{starting_position} → P{best_pred.expected_position:.1f} "
                        f"({tr('NO_CHANGE', 'no change')})")
        
        lines.append("")
        
        # Probabilities
        if starting_position <= 6:
            lines.append(f"{tr('PODIUM_PROBABILITY', 'Podium Probability')}: "
                        f"<b>{best_pred.podium_probability:.1f}%</b>")
        
        lines.append(f"{tr('POINTS_PROBABILITY', 'Points Probability')}: "
                    f"<b>{best_pred.points_probability:.1f}%</b>")
        
        # Best/worst case
        lines.append("")
        lines.append(f"{tr('POSITION_RANGE', 'Position Range')}: "
                    f"P{best_pred.best_case_position} - P{best_pred.worst_case_position}")
        
        self.prediction_label.setText("<br>".join(lines))
