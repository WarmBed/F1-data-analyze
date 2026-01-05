#!/usr/bin/env python3
"""
Position Analysis Tab

Shows position-based predictions including:
- Podium probability
- Points finish probability
- Expected position gain/loss
- Position distribution visualization

Author: F1T Team
Date: 2025-12-31
"""

from typing import List, Optional, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QFrame, QGridLayout, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

# Import i18n with lazy loading
from strategy_simulator.gui.i18n_helper import tr


class PositionDistributionWidget(QWidget):
    """Widget to visualize position probability distribution."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self._distribution: Dict[int, float] = {}
        self._starting_position: int = 10
        self._expected_position: float = 10.0
        
    def set_data(self, distribution: Dict[int, float], 
                 starting_position: int, expected_position: float):
        """Set the position distribution data."""
        self._distribution = distribution
        self._starting_position = starting_position
        self._expected_position = expected_position
        self.update()
        
    def paintEvent(self, event):
        """Paint the distribution visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width() - 20
        height = self.height() - 30
        
        if not self._distribution:
            painter.drawText(10, height // 2, tr("NO_DATA", "No data available"))
            return
        
        # Calculate bar dimensions
        bar_width = width / 20
        max_prob = max(self._distribution.values()) if self._distribution else 1
        
        # Draw bars for P1-P20
        for pos in range(1, 21):
            prob = self._distribution.get(pos, 0)
            bar_height = (prob / max(max_prob, 1)) * height
            
            x = 10 + (pos - 1) * bar_width
            y = height - bar_height + 15
            
            # Color based on position
            if pos <= 3:  # Podium - gold/silver/bronze
                colors = [QColor(255, 215, 0), QColor(192, 192, 192), QColor(205, 127, 50)]
                color = colors[pos - 1]
            elif pos <= 10:  # Points - green
                color = QColor(100, 200, 100)
            else:  # No points - gray
                color = QColor(150, 150, 150)
            
            # Highlight starting position
            if pos == self._starting_position:
                painter.setPen(QPen(QColor(0, 100, 255), 2))
            else:
                painter.setPen(QPen(color.darker(120), 1))
            
            painter.setBrush(QBrush(color))
            painter.drawRect(int(x), int(y), int(bar_width - 2), int(bar_height))
            
            # Draw position number
            painter.setPen(QColor(100, 100, 100))
            if pos % 2 == 1 or bar_width >= 25:  # Show every position if space allows
                painter.drawText(int(x), height + 25, str(pos))
        
        # Draw expected position marker
        if 1 <= self._expected_position <= 20:
            x = 10 + (self._expected_position - 1) * bar_width + bar_width / 2
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawLine(int(x), 15, int(x), height + 15)


class PositionAnalysisTab(QWidget):
    """
    Position Analysis Tab for strategy recommendations based on grid position.
    
    Features:
    - Position-based probability analysis
    - Podium/Points probability display
    - Position gain expectations
    - Visual distribution chart
    
    Signals:
        strategy_selected: Emitted when user selects a strategy for detailed view
    """
    
    strategy_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mc_summary = None
        self._starting_position: int = 10
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Splitter for sections
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Top: Summary Cards
        summary_group = QGroupBox(tr("POSITION_SUMMARY", "Position Analysis Summary"))
        summary_layout = QVBoxLayout(summary_group)
        
        # Starting position info
        self.position_info = QLabel()
        self.position_info.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 10px;
                background-color: #2d3436;
                color: #dfe6e9;
                border-radius: 5px;
            }
        """)
        summary_layout.addWidget(self.position_info)
        
        # Probability cards grid
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(10)
        
        # Podium probability card
        self.podium_card = self._create_probability_card(
            tr("PODIUM_PROB", "Podium Probability"),
            "0%",
            "#FFD700"  # Gold
        )
        cards_layout.addWidget(self.podium_card, 0, 0)
        
        # Top 5 probability card
        self.top5_card = self._create_probability_card(
            tr("TOP5_PROB", "Top 5 Probability"),
            "0%",
            "#C0C0C0"  # Silver
        )
        cards_layout.addWidget(self.top5_card, 0, 1)
        
        # Points probability card
        self.points_card = self._create_probability_card(
            tr("POINTS_PROB", "Points Probability"),
            "0%",
            "#00b894"  # Green
        )
        cards_layout.addWidget(self.points_card, 0, 2)
        
        # Expected gain card
        self.gain_card = self._create_probability_card(
            tr("EXPECTED_GAIN", "Expected Position Gain"),
            "0",
            "#0984e3"  # Blue
        )
        cards_layout.addWidget(self.gain_card, 0, 3)
        
        summary_layout.addWidget(cards_widget)
        splitter.addWidget(summary_group)
        
        # Middle: Strategy comparison table
        table_group = QGroupBox(tr("STRATEGY_POSITION_COMPARISON", "Strategy Position Comparison"))
        table_layout = QVBoxLayout(table_group)
        
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(9)
        self.comparison_table.setHorizontalHeaderLabels([
            tr("STRATEGY", "Strategy"),
            tr("START_POS", "Start"),
            tr("EXPECTED_POS", "Expected"),
            tr("BEST_CASE", "Best"),
            tr("WORST_CASE", "Worst"),
            tr("GAIN", "Gain"),
            tr("PODIUM", "Podium"),
            tr("TOP5", "Top 5"),
            tr("POINTS", "Points")
        ])
        
        header = self.comparison_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 9):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
            self.comparison_table.setColumnWidth(i, 70)
        
        self.comparison_table.setAlternatingRowColors(True)
        self.comparison_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.comparison_table.currentCellChanged.connect(self._on_selection_changed)
        table_layout.addWidget(self.comparison_table)
        
        splitter.addWidget(table_group)
        
        # Bottom: Position distribution visualization
        dist_group = QGroupBox(tr("POSITION_DISTRIBUTION", "Finish Position Distribution"))
        dist_layout = QVBoxLayout(dist_group)
        
        # Strategy selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(tr("VIEW_STRATEGY", "View Strategy") + ":"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_combo_changed)
        selector_layout.addWidget(self.strategy_combo)
        selector_layout.addStretch()
        
        # Legend
        legend_label = QLabel()
        legend_label.setText(
            f'<span style="color:#FFD700;">■</span> {tr("PODIUM", "Podium")} | '
            f'<span style="color:#00b894;">■</span> {tr("POINTS_ZONE", "Points")} | '
            f'<span style="color:#999;">■</span> {tr("NO_POINTS", "No Points")} | '
            f'<span style="color:#0066FF;">|</span> {tr("START_POS", "Start")}'
        )
        selector_layout.addWidget(legend_label)
        
        dist_layout.addLayout(selector_layout)
        
        # Distribution visualization
        self.distribution_widget = PositionDistributionWidget()
        dist_layout.addWidget(self.distribution_widget)
        
        # Recommendation text
        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                color: #2d3436;
            }
        """)
        dist_layout.addWidget(self.recommendation_label)
        
        splitter.addWidget(dist_group)
        
        # Set splitter sizes
        splitter.setSizes([150, 200, 250])
        
        # Initial state
        self._update_empty_state()
    
    def _create_probability_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a probability display card."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #f8f9fa;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 5px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 11px; color: #636e72;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
        layout.addWidget(value_label)
        
        return card
    
    def _update_card_value(self, card: QFrame, value: str):
        """Update the value displayed on a card."""
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)
    
    def _update_empty_state(self):
        """Show empty state when no data."""
        self.position_info.setText(
            tr("RUN_MC_FOR_POSITION", 
               "Run Monte Carlo simulation with position tracking to see predictions.")
        )
        self._update_card_value(self.podium_card, "-")
        self._update_card_value(self.top5_card, "-")
        self._update_card_value(self.points_card, "-")
        self._update_card_value(self.gain_card, "-")
        self.comparison_table.setRowCount(0)
        self.strategy_combo.clear()
        self.distribution_widget.set_data({}, 10, 10)
        self.recommendation_label.setText("")
    
    def update_results(self, mc_summary, starting_position: int = None):
        """
        Update with Monte Carlo summary containing position predictions.
        
        Args:
            mc_summary: MonteCarloSummary with position_predictions
            starting_position: Override starting position (uses mc_summary.starting_position if None)
        """
        self._mc_summary = mc_summary
        
        if mc_summary is None or not hasattr(mc_summary, 'position_predictions'):
            self._update_empty_state()
            return
        
        self._starting_position = starting_position or mc_summary.starting_position
        
        if not mc_summary.position_predictions:
            self._update_empty_state()
            return
        
        # Update position info
        self.position_info.setText(
            f'{tr("STARTING_POSITION", "Starting Position")}: '
            f'<b style="color:#74b9ff;">P{self._starting_position}</b> | '
            f'{tr("MC_ITERATIONS", "Iterations")}: {mc_summary.iterations}'
        )
        
        # Get best strategy predictions
        predictions = mc_summary.position_predictions
        best_pred = max(predictions.values(), key=lambda p: p.points_probability)
        
        # Update summary cards with best strategy
        self._update_card_value(self.podium_card, f"{best_pred.podium_probability:.1f}%")
        self._update_card_value(self.top5_card, f"{best_pred.top5_probability:.1f}%")
        self._update_card_value(self.points_card, f"{best_pred.points_probability:.1f}%")
        
        gain_text = f"+{best_pred.expected_gain:.1f}" if best_pred.expected_gain >= 0 else f"{best_pred.expected_gain:.1f}"
        self._update_card_value(self.gain_card, gain_text)
        
        # Update comparison table
        self._update_comparison_table(predictions)
        
        # Update strategy combo
        self.strategy_combo.blockSignals(True)
        self.strategy_combo.clear()
        for name in predictions.keys():
            self.strategy_combo.addItem(name)
        self.strategy_combo.blockSignals(False)
        
        # Select best strategy
        best_idx = list(predictions.keys()).index(best_pred.strategy_name)
        if best_idx >= 0:
            self.strategy_combo.setCurrentIndex(best_idx)
        
        # Update distribution widget
        self._update_distribution_view(best_pred)
        
        # Update recommendation
        self._update_recommendation(predictions)
    
    def _update_comparison_table(self, predictions: Dict):
        """Update the strategy comparison table."""
        self.comparison_table.setRowCount(len(predictions))
        
        # Sort by expected position (best first)
        sorted_preds = sorted(predictions.values(), key=lambda p: p.expected_position)
        
        for row, pred in enumerate(sorted_preds):
            # Strategy name
            name_item = QTableWidgetItem(pred.strategy_name)
            name_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.comparison_table.setItem(row, 0, name_item)
            
            # Starting position
            start_item = QTableWidgetItem(f"P{pred.starting_position}")
            start_item.setTextAlignment(Qt.AlignCenter)
            self.comparison_table.setItem(row, 1, start_item)
            
            # Expected position
            exp_item = QTableWidgetItem(f"P{pred.expected_position:.1f}")
            exp_item.setTextAlignment(Qt.AlignCenter)
            self.comparison_table.setItem(row, 2, exp_item)
            
            # Best case
            best_item = QTableWidgetItem(f"P{pred.best_case_position}")
            best_item.setTextAlignment(Qt.AlignCenter)
            best_item.setForeground(QColor(0, 150, 0))
            self.comparison_table.setItem(row, 3, best_item)
            
            # Worst case
            worst_item = QTableWidgetItem(f"P{pred.worst_case_position}")
            worst_item.setTextAlignment(Qt.AlignCenter)
            worst_item.setForeground(QColor(150, 0, 0))
            self.comparison_table.setItem(row, 4, worst_item)
            
            # Gain
            gain = pred.expected_gain
            gain_text = f"+{gain:.1f}" if gain >= 0 else f"{gain:.1f}"
            gain_item = QTableWidgetItem(gain_text)
            gain_item.setTextAlignment(Qt.AlignCenter)
            gain_item.setForeground(QColor(0, 150, 0) if gain > 0 else 
                                   QColor(150, 0, 0) if gain < 0 else 
                                   QColor(100, 100, 100))
            self.comparison_table.setItem(row, 5, gain_item)
            
            # Podium probability
            podium_item = QTableWidgetItem(f"{pred.podium_probability:.1f}%")
            podium_item.setTextAlignment(Qt.AlignCenter)
            if pred.podium_probability >= 50:
                podium_item.setForeground(QColor(255, 215, 0))  # Gold
            self.comparison_table.setItem(row, 6, podium_item)
            
            # Top 5 probability
            top5_item = QTableWidgetItem(f"{pred.top5_probability:.1f}%")
            top5_item.setTextAlignment(Qt.AlignCenter)
            self.comparison_table.setItem(row, 7, top5_item)
            
            # Points probability
            points_item = QTableWidgetItem(f"{pred.points_probability:.1f}%")
            points_item.setTextAlignment(Qt.AlignCenter)
            if pred.points_probability >= 80:
                points_item.setForeground(QColor(0, 180, 100))
            self.comparison_table.setItem(row, 8, points_item)
    
    def _update_distribution_view(self, prediction):
        """Update the distribution visualization."""
        self.distribution_widget.set_data(
            prediction.position_distribution,
            prediction.starting_position,
            prediction.expected_position
        )
    
    def _update_recommendation(self, predictions: Dict):
        """Update the recommendation text based on analysis."""
        if not predictions:
            self.recommendation_label.setText("")
            return
        
        # Find best strategies for different goals
        best_podium = max(predictions.values(), key=lambda p: p.podium_probability)
        best_points = max(predictions.values(), key=lambda p: p.points_probability)
        best_gain = max(predictions.values(), key=lambda p: p.expected_gain)
        most_consistent = min(predictions.values(), 
                             key=lambda p: p.worst_case_position - p.best_case_position)
        
        # Generate recommendation text
        lines = []
        
        if self._starting_position <= 3:
            # Front runner - focus on maintaining
            lines.append(f"<b>{tr('FRONT_RUNNER_ADVICE', 'Front Runner Strategy')}:</b>")
            lines.append(f"  {tr('BEST_FOR_PODIUM', 'Best for podium')}: "
                        f"<b>{best_podium.strategy_name}</b> ({best_podium.podium_probability:.1f}%)")
            lines.append(f"  {tr('MOST_CONSISTENT', 'Most consistent')}: "
                        f"<b>{most_consistent.strategy_name}</b> "
                        f"(P{most_consistent.best_case_position}-P{most_consistent.worst_case_position})")
        elif self._starting_position <= 10:
            # Midfield - balance attack and defense
            lines.append(f"<b>{tr('MIDFIELD_ADVICE', 'Midfield Strategy')}:</b>")
            lines.append(f"  {tr('BEST_FOR_POINTS', 'Best for points')}: "
                        f"<b>{best_points.strategy_name}</b> ({best_points.points_probability:.1f}%)")
            if best_gain.expected_gain > 0:
                lines.append(f"  {tr('BEST_FOR_GAINING', 'Best for gaining positions')}: "
                            f"<b>{best_gain.strategy_name}</b> (+{best_gain.expected_gain:.1f})")
        else:
            # Back of grid - focus on gains
            lines.append(f"<b>{tr('BACKMARKER_ADVICE', 'Back Grid Strategy')}:</b>")
            lines.append(f"  {tr('BEST_FOR_GAINING', 'Best for gaining positions')}: "
                        f"<b>{best_gain.strategy_name}</b> (+{best_gain.expected_gain:.1f})")
            lines.append(f"  {tr('POINTS_CHANCE', 'Points chance')}: "
                        f"<b>{best_points.strategy_name}</b> ({best_points.points_probability:.1f}%)")
        
        self.recommendation_label.setText("<br>".join(lines))
    
    def _on_selection_changed(self, row, col, prev_row, prev_col):
        """Handle table row selection."""
        if row < 0 or not self._mc_summary:
            return
        
        # Get strategy name from table
        name_item = self.comparison_table.item(row, 0)
        if name_item:
            strategy_name = name_item.text()
            # Update combo to match
            idx = self.strategy_combo.findText(strategy_name)
            if idx >= 0:
                self.strategy_combo.blockSignals(True)
                self.strategy_combo.setCurrentIndex(idx)
                self.strategy_combo.blockSignals(False)
            
            # Update distribution
            if strategy_name in self._mc_summary.position_predictions:
                pred = self._mc_summary.position_predictions[strategy_name]
                self._update_distribution_view(pred)
            
            self.strategy_selected.emit(strategy_name)
    
    def _on_strategy_combo_changed(self, index):
        """Handle strategy combo selection."""
        if index < 0 or not self._mc_summary:
            return
        
        strategy_name = self.strategy_combo.currentText()
        if strategy_name in self._mc_summary.position_predictions:
            pred = self._mc_summary.position_predictions[strategy_name]
            self._update_distribution_view(pred)
            self.strategy_selected.emit(strategy_name)
