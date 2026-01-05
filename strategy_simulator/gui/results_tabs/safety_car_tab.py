#!/usr/bin/env python3
"""
Safety Car Scenarios Tab

Analyzes SC timing impact and bail-out tire recommendations.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class SafetyCarTab(QWidget):
    """
    Safety Car scenarios analysis tab.
    
    Features:
    - SC timing impact analysis
    - Optimal pit windows during SC
    - Bail-out tire recommendations
    - Pit vs Stay-out decision analysis with position changes
    - Field tire state comparison
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: List = []
        self._params = None
        self._fp2_predictions: List = []  # Store FP2 predictions for field comparison
        self._opponent_strategies: Dict = {}  # Store opponent strategies
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Splitter for sections
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Top: SC Window Analysis
        sc_group = QGroupBox("SC/VSC 進站窗口分析")
        sc_layout = QVBoxLayout(sc_group)
        
        # Strategy selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("策略:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_changed)
        selector_layout.addWidget(self.strategy_combo)
        selector_layout.addStretch()
        sc_layout.addLayout(selector_layout)
        
        # SC windows table
        self.sc_table = QTableWidget()
        self.sc_table.setColumnCount(5)
        self.sc_table.setHorizontalHeaderLabels([
            "進站圈", "最佳 SC 窗口", "節省 (綠旗→SC)", 
            "節省 (綠旗→VSC)", "建議"
        ])
        
        header = self.sc_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.sc_table.setAlternatingRowColors(True)
        sc_layout.addWidget(self.sc_table)
        
        splitter.addWidget(sc_group)
        
        # Middle: SC Scenario Analysis (new feature)
        scenario_group = QGroupBox("SC 場景分析")
        scenario_layout = QVBoxLayout(scenario_group)
        
        # Use QScrollArea for potentially long content
        from PyQt5.QtWidgets import QScrollArea
        self.scenario_scroll = QScrollArea()
        self.scenario_scroll.setWidgetResizable(True)
        self.scenario_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.scenario_content = QWidget()
        self.scenario_content_layout = QVBoxLayout(self.scenario_content)
        self.scenario_content_layout.setContentsMargins(5, 5, 5, 5)
        
        self.scenario_label = QLabel("啟用「模擬 SC 場景」後執行模擬，將在此顯示分析結果。")
        self.scenario_label.setWordWrap(True)
        self.scenario_label.setTextFormat(Qt.RichText)
        self.scenario_label.setStyleSheet("padding: 10px; background-color: #f8f8f8; border-radius: 5px;")
        self.scenario_content_layout.addWidget(self.scenario_label)
        
        # Position change table (hidden initially)
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(6)
        self.position_table.setHorizontalHeaderLabels([
            "策略", "原始位置", "SC後位置", "變化", "時間差", "建議"
        ])
        self.position_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.position_table.setVisible(False)
        self.scenario_content_layout.addWidget(self.position_table)
        
        self.scenario_scroll.setWidget(self.scenario_content)
        scenario_layout.addWidget(self.scenario_scroll)
        
        splitter.addWidget(scenario_group)
        
        # Bottom: Bail-out Recommendations
        bailout_group = QGroupBox("備用輪胎建議")
        bailout_layout = QVBoxLayout(bailout_group)
        
        self.bailout_frame = QFrame()
        self.bailout_layout = QGridLayout(self.bailout_frame)
        bailout_layout.addWidget(self.bailout_frame)
        
        splitter.addWidget(bailout_group)
        
        # Set splitter sizes: SC窗口(150) : 場景分析(400) : 備用輪胎(120)
        splitter.setSizes([150, 400, 120])
    
    def update_results(self, results: List, params):
        """Update with simulation results."""
        self._results = results
        self._params = params
        
        # Populate strategy combo
        self.strategy_combo.clear()
        for result in results:
            notation = result.get_stint_notation()
            self.strategy_combo.addItem(
                f"{result.strategy_name}: {notation}"
            )
        
        # Update bail-out recommendations
        self._update_bailout_recommendations(0)
        
        # Update SC windows for first strategy
        if results:
            self._update_sc_windows(0)
        
        # If we have scenario analyses cached, refresh them for new selection
        if hasattr(self, '_cached_scenario_analyses') and self._cached_scenario_analyses:
            self.update_scenario_analysis(self._cached_scenario_analyses, self._cached_summary)
    
    def _on_strategy_changed(self, index: int):
        """Handle strategy selection change."""
        if 0 <= index < len(self._results):
            self._update_sc_windows(index)
            self._update_bailout_recommendations(index)
            
            # Refresh scenario analysis with new selected strategy
            if hasattr(self, '_cached_scenario_analyses') and self._cached_scenario_analyses:
                self.update_scenario_analysis(self._cached_scenario_analyses, self._cached_summary)
    
    def _update_sc_windows(self, strategy_idx: int):
        """Update SC windows table for selected strategy."""
        if strategy_idx >= len(self._results):
            return
        
        result = self._results[strategy_idx]
        pit_laps = result.pit_laps
        
        self.sc_table.setRowCount(len(pit_laps))
        
        green_loss = self._params.pit_loss_green if self._params else 24.0
        sc_loss = self._params.pit_loss_sc if self._params else 12.0
        vsc_loss = self._params.pit_loss_vsc if self._params else 9.0
        
        for row, pit_lap in enumerate(pit_laps):
            # Pit lap
            pit_item = QTableWidgetItem(f"Lap {pit_lap}")
            pit_item.setTextAlignment(Qt.AlignCenter)
            self.sc_table.setItem(row, 0, pit_item)
            
            # Optimal window (3 laps before to pit lap)
            window_start = max(1, pit_lap - 3)
            window_item = QTableWidgetItem(f"L{window_start} - L{pit_lap}")
            window_item.setTextAlignment(Qt.AlignCenter)
            self.sc_table.setItem(row, 1, window_item)
            
            # SC saving
            sc_saving = green_loss - sc_loss
            sc_item = QTableWidgetItem(f"{sc_saving:.1f}s")
            sc_item.setTextAlignment(Qt.AlignCenter)
            sc_item.setForeground(QColor(0, 150, 0))
            self.sc_table.setItem(row, 2, sc_item)
            
            # VSC saving
            vsc_saving = green_loss - vsc_loss
            vsc_item = QTableWidgetItem(f"{vsc_saving:.1f}s")
            vsc_item.setTextAlignment(Qt.AlignCenter)
            vsc_item.setForeground(QColor(0, 150, 0))
            self.sc_table.setItem(row, 3, vsc_item)
            
            # Recommendation
            rec = "強烈推薦" if sc_saving > 10 else "良好機會" if sc_saving > 5 else "普通機會"
            rec_item = QTableWidgetItem(rec)
            rec_item.setTextAlignment(Qt.AlignCenter)
            self.sc_table.setItem(row, 4, rec_item)
    
    def _update_bailout_recommendations(self, strategy_idx: int = 0):
        """
        Update bail-out tire recommendations based on selected strategy.
        
        Analyzes what tire the driver would be on during each SC window,
        and recommends the best tire change option.
        """
        # Clear previous
        while self.bailout_layout.count():
            item = self.bailout_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self._params or not self._results:
            return
        
        if strategy_idx >= len(self._results):
            strategy_idx = 0
        
        result = self._results[strategy_idx]
        race_laps = self._params.race_laps
        
        # Get strategy stint info (Stint objects have: compound, laps, start_lap, end_lap)
        stints = result.stints
        pit_laps = result.pit_laps
        
        # Build lap-to-compound mapping
        lap_compound = {}
        for stint in stints:
            for lap in range(stint.start_lap, stint.end_lap + 1):
                # Compound is an enum, get the value string
                compound_str = stint.compound.value if hasattr(stint.compound, 'value') else str(stint.compound)
                lap_compound[lap] = compound_str
        
        # Define SC windows based on race length
        third = race_laps // 3
        windows = [
            ("早期 SC (L1-{})".format(third), 1, third),
            ("中期 SC (L{}-{})".format(third+1, 2*third), third+1, 2*third),
            ("晚期 SC (L{}+)".format(2*third+1), 2*third+1, race_laps),
        ]
        
        # Get all available compounds (used in strategy)
        used_compounds = set()
        for s in stints:
            compound_str = s.compound.value if hasattr(s.compound, 'value') else str(s.compound)
            used_compounds.add(compound_str)
        all_compounds = ['SOFT', 'MEDIUM', 'HARD']
        
        # Add header row
        header_labels = ["SC 時段", "圈數範圍", "目前輪胎", "更換輪胎", "建議說明"]
        for col, header_text in enumerate(header_labels):
            header_label = QLabel(header_text)
            header_label.setFont(QFont("Arial", 9, QFont.Bold))
            header_label.setStyleSheet("color: #444; border-bottom: 1px solid #ccc; padding-bottom: 3px;")
            self.bailout_layout.addWidget(header_label, 0, col)
        
        for row, (name, start_lap, end_lap) in enumerate(windows):
            data_row = row + 1  # Offset by 1 for header
            
            # Determine what tire we'd be on in the middle of this window
            mid_lap = (start_lap + end_lap) // 2
            
            # Get current compound at mid lap
            if stints:
                last_compound = stints[-1].compound
                last_compound_str = last_compound.value if hasattr(last_compound, 'value') else str(last_compound)
            else:
                last_compound_str = 'MEDIUM'
            current_compound = lap_compound.get(mid_lap, last_compound_str)
            
            # Remaining laps from window midpoint
            remaining_laps = race_laps - mid_lap
            
            # Calculate optimal bailout compound
            bailout_compound, reason = self._calculate_bailout_recommendation(
                current_compound, remaining_laps, pit_laps, mid_lap, all_compounds
            )
            
            # Window name
            name_label = QLabel(name)
            name_label.setFont(QFont("Arial", 10, QFont.Bold))
            self.bailout_layout.addWidget(name_label, data_row, 0)
            
            # Lap range
            range_label = QLabel(f"(Lap {start_lap}-{end_lap})")
            range_label.setStyleSheet("color: #666;")
            self.bailout_layout.addWidget(range_label, data_row, 1)
            
            # Current tire indicator
            current_label = QLabel(current_compound)
            current_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {self._get_compound_color(current_compound)};
                    padding: 3px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
            """)
            self.bailout_layout.addWidget(current_label, data_row, 2)
            
            # Recommended compound
            compound_label = QLabel(bailout_compound)
            compound_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {self._get_compound_color(bailout_compound)};
                    padding: 3px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
            """)
            self.bailout_layout.addWidget(compound_label, data_row, 3)
            
            # Reason
            reason_label = QLabel(reason)
            reason_label.setStyleSheet("color: #444;")
            self.bailout_layout.addWidget(reason_label, data_row, 4)
    
    def _calculate_bailout_recommendation(
        self, 
        current_compound: str, 
        remaining_laps: int,
        pit_laps: List[int],
        current_lap: int,
        available_compounds: List[str]
    ) -> tuple:
        """
        Calculate the best bailout tire based on current situation.
        
        Args:
            current_compound: Tire currently on car
            remaining_laps: Laps remaining in race
            pit_laps: Planned pit stop laps
            current_lap: Current lap number
            available_compounds: List of available compounds
            
        Returns:
            (compound, reason) tuple
        """
        # Compound durability estimates (max laps at good pace)
        durability = {
            'SOFT': 18,
            'MEDIUM': 28,
            'HARD': 40,
        }
        
        # Check if we have another planned stop ahead
        future_stops = [p for p in pit_laps if p > current_lap]
        
        if remaining_laps <= durability['SOFT']:
            # Can finish on softs - sprint to end
            if current_compound == 'SOFT':
                return ('SOFT', '繼續 SOFT 衝刺至終點')
            return ('SOFT', f'剩餘 {remaining_laps} 圈，換 SOFT 衝刺')
        
        elif remaining_laps <= durability['MEDIUM']:
            # Medium can handle it
            if current_compound == 'SOFT':
                return ('MEDIUM', f'剩餘 {remaining_laps} 圈過長，換 MEDIUM 確保完賽')
            elif current_compound == 'MEDIUM':
                return ('MEDIUM', '繼續 MEDIUM 完賽')
            else:  # HARD
                return ('MEDIUM', '可換 MEDIUM 增加速度')
        
        else:
            # Long stint remaining
            if current_compound == 'HARD':
                if future_stops:
                    return ('HARD', '維持 HARD，按計畫進站')
                else:
                    return ('MEDIUM', '額外進站，換 MEDIUM 保持競爭力')
            elif current_compound == 'MEDIUM':
                return ('HARD', f'剩餘 {remaining_laps} 圈，換 HARD 以安全完賽')
            else:  # SOFT
                if remaining_laps > durability['HARD']:
                    return ('HARD', f'剩餘 {remaining_laps} 圈，換 HARD 並計畫額外進站')
                return ('HARD', f'剩餘 {remaining_laps} 圈，換 HARD 確保完賽')
    
    def _get_compound_color(self, compound: str) -> str:
        """Get background color for compound."""
        colors = {
            'SOFT': '#FFB0B0',
            'MEDIUM': '#FFFF90',
            'HARD': '#D0D0D0',
        }
        return colors.get(compound.upper(), '#F0F0F0')
    
    def update_sc_scenario(self, analysis_html: str, sc_lap: int, 
                           sc_duration: int, is_vsc: bool,
                           sc_results: list = None):
        """
        Update with SC scenario analysis results.
        
        Args:
            analysis_html: HTML formatted analysis text
            sc_lap: Lap number when SC appears
            sc_duration: Duration of SC in laps
            is_vsc: True if VSC, False if full SC
            sc_results: List of recalculated strategy results (optional)
        """
        sc_type = "VSC" if is_vsc else "SC"
        
        # Update the scenario label with rich text
        self.scenario_label.setText(analysis_html)
        self.scenario_label.setStyleSheet(
            "padding: 10px; background-color: #e8f4e8; border-radius: 5px; "
            "border: 1px solid #90c090;"
        )
        
        # Store SC results for potential future use
        self._sc_scenario_results = sc_results
        
        # Update position change table if we have SC results
        if sc_results:
            self._update_position_table(sc_results)
            self.position_table.setVisible(True)
        else:
            self.position_table.setVisible(False)
    
    def _update_position_table(self, sc_results: list):
        """
        Update position change table with SC scenario results.
        
        Args:
            sc_results: List of recalculated strategy results with position info
        """
        self.position_table.setRowCount(len(sc_results))
        
        for row, result in enumerate(sc_results):
            # Strategy notation
            notation = getattr(result, 'notation', result.get_stint_notation() if hasattr(result, 'get_stint_notation') else 'N/A')
            notation_item = QTableWidgetItem(notation)
            notation_item.setTextAlignment(Qt.AlignCenter)
            self.position_table.setItem(row, 0, notation_item)
            
            # Original position (rank)
            orig_rank = getattr(result, 'original_rank', row + 1)
            orig_item = QTableWidgetItem(f"P{orig_rank}")
            orig_item.setTextAlignment(Qt.AlignCenter)
            self.position_table.setItem(row, 1, orig_item)
            
            # New position after SC
            new_rank = getattr(result, 'new_rank', row + 1)
            new_item = QTableWidgetItem(f"P{new_rank}")
            new_item.setTextAlignment(Qt.AlignCenter)
            self.position_table.setItem(row, 2, new_item)
            
            # Position change
            rank_change = getattr(result, 'rank_change', 0)
            if rank_change > 0:
                change_text = f"+{rank_change}"
                change_color = QColor(0, 150, 0)  # Green for improvement
            elif rank_change < 0:
                change_text = str(rank_change)
                change_color = QColor(200, 0, 0)  # Red for drop
            else:
                change_text = "-"
                change_color = QColor(100, 100, 100)  # Gray for no change
            
            change_item = QTableWidgetItem(change_text)
            change_item.setTextAlignment(Qt.AlignCenter)
            change_item.setForeground(change_color)
            change_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.position_table.setItem(row, 3, change_item)
            
            # Time saved/lost
            time_saved = getattr(result, 'time_saved', 0)
            if time_saved > 0.5:
                time_text = f"+{time_saved:.1f}s"
                time_color = QColor(0, 150, 0)
            elif time_saved < -0.5:
                time_text = f"{time_saved:.1f}s"
                time_color = QColor(200, 0, 0)
            else:
                time_text = f"{time_saved:+.1f}s"
                time_color = QColor(100, 100, 100)
            
            time_item = QTableWidgetItem(time_text)
            time_item.setTextAlignment(Qt.AlignCenter)
            time_item.setForeground(time_color)
            self.position_table.setItem(row, 4, time_item)
            
            # Recommendation
            sc_pits = getattr(result, 'sc_pits', 0)
            if rank_change > 0 and sc_pits > 0:
                advice = "建議進站"
                advice_color = QColor(0, 150, 0)
            elif rank_change < 0:
                advice = "避開SC進站"
                advice_color = QColor(200, 100, 0)
            else:
                advice = "視情況決定"
                advice_color = QColor(100, 100, 100)
            
            advice_item = QTableWidgetItem(advice)
            advice_item.setTextAlignment(Qt.AlignCenter)
            advice_item.setForeground(advice_color)
            self.position_table.setItem(row, 5, advice_item)

    def update_scenario_analysis(self, scenario_analyses: dict, summary=None):
        """
        Update with Monte Carlo scenario analysis results.
        
        Shows how ALL TOP STRATEGIES perform under different SC scenarios.
        Updates when user changes strategy selection in dropdown.
        
        Args:
            scenario_analyses: Dict[str, ScenarioAnalysis] from MonteCarloSummary
            summary: Optional MonteCarloSummary for additional context
        """
        # Cache for when user changes strategy selection
        self._cached_scenario_analyses = scenario_analyses
        self._cached_summary = summary
        
        if not scenario_analyses:
            self.scenario_label.setText(
                "<p style='color: #666;'>尚無場景分析結果。"
                "請執行 Monte Carlo 模擬。</p>"
            )
            return
        
        # Get currently selected strategy from combo box
        selected_idx = self.strategy_combo.currentIndex()
        selected_strategy = None
        if self._results and 0 <= selected_idx < len(self._results):
            selected_strategy = self._results[selected_idx]
        
        selected_name = selected_strategy.strategy_name if selected_strategy else "Plan A"
        
        # Build rich HTML content
        html_parts = []
        html_parts.append("<div style='font-family: Arial, sans-serif;'>")
        
        # Header - Show TOP 5 strategies comparison
        html_parts.append(
            f"<h3 style='margin: 0 0 10px 0; color: #1976d2;'>SC 場景分析 - 策略勝率對比</h3>"
            f"<p style='margin: 0 0 10px 0; color: #666; font-size: 0.9em;'>"
            f"當前選擇: <b style='color: #d32f2f;'>{selected_name}</b> - 查看各場景下前5策略的勝率</p>"
        )
        
        # Get top 5 strategies from results (or all if less than 5)
        top_strategies = self._results[:5] if self._results else []
        top_names = [r.strategy_name for r in top_strategies]
        
        # Scenario comparison table
        html_parts.append("<table style='width: 100%; border-collapse: collapse; margin-bottom: 15px;'>")
        html_parts.append("<tr style='background: #1976d2; color: white;'>")
        html_parts.append("<th style='padding: 8px; text-align: left;'>SC 場景</th>")
        for name in top_names:
            is_selected = (name == selected_name)
            header_style = "background: #d32f2f;" if is_selected else ""
            html_parts.append(f"<th style='padding: 8px; text-align: center; {header_style}'>{name}</th>")
        html_parts.append("<th style='padding: 8px; text-align: left;'>最佳策略</th>")
        html_parts.append("</tr>")
        
        scenario_order = ["no_sc", "early_sc", "mid_sc", "late_sc"]
        scenario_colors = {
            "no_sc": "#4CAF50",
            "early_sc": "#FF9800",
            "mid_sc": "#FF5722",
            "late_sc": "#f44336"
        }
        
        for scenario_type in scenario_order:
            if scenario_type not in scenario_analyses:
                continue
            
            scenario = scenario_analyses[scenario_type]
            color = scenario_colors.get(scenario_type, "#666")
            
            html_parts.append("<tr style='border-bottom: 1px solid #ddd;'>")
            
            # Scenario name
            html_parts.append(
                f"<td style='padding: 8px;'>"
                f"<span style='color: {color}; font-weight: bold;'>●</span> "
                f"{scenario.scenario_name}</td>"
            )
            
            # Win rates for each top strategy
            max_rate = 0
            for name in top_names:
                rate = scenario.strategy_win_rates.get(name, 0)
                if rate > max_rate:
                    max_rate = rate
            
            for name in top_names:
                rate = scenario.strategy_win_rates.get(name, 0)
                is_selected = (name == selected_name)
                is_best = (rate >= max_rate * 0.95 and rate > 0)  # Within 95% of best
                
                cell_style = ""
                if is_selected:
                    cell_style = "background: #ffebee;" if not is_best else "background: #e8f5e9;"
                elif is_best:
                    cell_style = "background: #f0f4c3;"
                
                rate_color = "#4CAF50" if is_best else "#FF5722" if rate < max_rate * 0.5 else "#666"
                html_parts.append(
                    f"<td style='padding: 8px; text-align: center; {cell_style}'>"
                    f"<span style='color: {rate_color}; font-weight: bold;'>{rate:.0f}%</span></td>"
                )
            
            # Best strategy column
            html_parts.append(
                f"<td style='padding: 8px;'>{scenario.best_strategy} "
                f"<span style='color: #666;'>({scenario.best_strategy_win_rate:.0f}%)</span></td>"
            )
            
            html_parts.append("</tr>")
        
        html_parts.append("</table>")
        
        # Selected strategy detailed analysis
        html_parts.append(
            f"<h4 style='margin: 15px 0 10px 0; color: #1976d2;'>"
            f"{selected_name} 詳細分析</h4>"
        )
        
        # Pit adjustment table for selected strategy
        html_parts.append("<table style='width: 100%; border-collapse: collapse; margin-bottom: 15px;'>")
        html_parts.append("<tr style='background: #f0f0f0;'>")
        html_parts.append("<th style='padding: 8px; text-align: left;'>SC 場景</th>")
        html_parts.append("<th style='padding: 8px; text-align: left;'>進站調整建議</th>")
        html_parts.append("</tr>")
        
        # Get pit laps for adjustment recommendations
        pit_laps = selected_strategy.pit_laps if selected_strategy else []
        race_laps = self._params.race_laps if self._params else 58
        scenario_order = ["no_sc", "early_sc", "mid_sc", "late_sc"]
        scenario_colors = {
            "no_sc": "#4CAF50",
            "early_sc": "#FF9800",
            "mid_sc": "#FF5722",
            "late_sc": "#f44336"
        }
        
        for scenario_type in scenario_order:
            if scenario_type not in scenario_analyses:
                continue
            
            scenario = scenario_analyses[scenario_type]
            color = scenario_colors.get(scenario_type, "#666")
            
            html_parts.append("<tr style='border-bottom: 1px solid #ddd;'>")
            
            # Scenario name
            html_parts.append(
                f"<td style='padding: 8px;'>"
                f"<span style='color: {color}; font-weight: bold;'>●</span> "
                f"{scenario.scenario_name}</td>"
            )
            
            # Pit adjustment recommendation for this SC scenario
            adjustment = self._get_pit_adjustment_for_sc(
                scenario_type, pit_laps, race_laps, selected_strategy
            )
            html_parts.append(f"<td style='padding: 8px;'>{adjustment}</td>")
            
            html_parts.append("</tr>")
        
        html_parts.append("</table>")
        
        # Detailed SC Pit vs Stay-Out comparison with position changes
        html_parts.append(
            "<div style='margin-top: 15px; padding: 10px; "
            "background: #e3f2fd; border-radius: 5px;'>"
        )
        html_parts.append("<h4 style='margin: 0 0 10px 0;'>SC 進站 vs 不進站決策分析</h4>")
        
        # Detailed comparison table
        html_parts.append("<table style='width: 100%; border-collapse: collapse; font-size: 0.9em;'>")
        html_parts.append("<tr style='background: #1976d2; color: white;'>")
        html_parts.append("<th style='padding: 8px; text-align: left;'>SC 時機</th>")
        html_parts.append("<th style='padding: 8px; text-align: center;'>目前輪胎</th>")
        html_parts.append("<th style='padding: 8px; text-align: center;'>進站</th>")
        html_parts.append("<th style='padding: 8px; text-align: center;'>不進站</th>")
        html_parts.append("<th style='padding: 8px; text-align: center;'>建議</th>")
        html_parts.append("</tr>")
        
        for scenario_type in ["early_sc", "mid_sc", "late_sc"]:
            if scenario_type not in scenario_analyses:
                continue
            
            scenario = scenario_analyses[scenario_type]
            pit_vs_stay = self._analyze_pit_vs_stay_out(
                scenario_type, pit_laps, race_laps, selected_strategy
            )
            
            pit_better = pit_vs_stay.get('pit_better', True)
            pit_color = "#4CAF50" if pit_better else "#999"
            stay_color = "#4CAF50" if not pit_better else "#999"
            
            # Current tire info
            current_tire = pit_vs_stay.get('current_tire', 'MEDIUM')
            tire_age = pit_vs_stay.get('current_tire_age', 0)
            pit_tire = pit_vs_stay.get('pit_tire', 'HARD')
            remaining = pit_vs_stay.get('remaining_laps', 30)
            
            tire_color = self._get_compound_color(current_tire)
            pit_tire_color = self._get_compound_color(pit_tire)
            
            html_parts.append("<tr style='border-bottom: 1px solid #ddd;'>")
            
            # Scenario name with lap range
            sc_window = pit_vs_stay.get('sc_window', '')
            html_parts.append(
                f"<td style='padding: 8px;'>"
                f"<b>{scenario.scenario_name}</b><br/>"
                f"<span style='color: #666; font-size: 0.85em;'>{sc_window}</span></td>"
            )
            
            # Current tire with age
            html_parts.append(
                f"<td style='padding: 8px; text-align: center;'>"
                f"<span style='background: {tire_color}; padding: 2px 8px; border-radius: 3px; "
                f"font-weight: bold;'>{current_tire}</span><br/>"
                f"<span style='color: #666; font-size: 0.85em;'>{tire_age} 圈</span></td>"
            )
            
            # Pit option
            pit_pos_change = pit_vs_stay.get('pit_position_change', '')
            html_parts.append(
                f"<td style='padding: 8px; text-align: center; background: #e3f2fd;'>"
                f"<span style='background: {pit_tire_color}; padding: 2px 8px; border-radius: 3px; "
                f"font-weight: bold;'>{pit_tire}</span><br/>"
                f"<span style='color: {pit_color}; font-size: 0.85em;'>{pit_pos_change}</span><br/>"
                f"<span style='color: #666; font-size: 0.8em;'>{pit_vs_stay.get('pit_benefit', '')}</span></td>"
            )
            
            # Stay out option
            stay_pos_change = pit_vs_stay.get('stay_position_change', '')
            html_parts.append(
                f"<td style='padding: 8px; text-align: center; background: #fff8e1;'>"
                f"<span style='background: {tire_color}; padding: 2px 8px; border-radius: 3px; "
                f"font-weight: bold;'>{current_tire}</span><br/>"
                f"<span style='color: {stay_color}; font-size: 0.85em;'>{stay_pos_change}</span><br/>"
                f"<span style='color: #666; font-size: 0.8em;'>{pit_vs_stay.get('stay_benefit', '')}</span></td>"
            )
            
            # Recommendation
            rec = pit_vs_stay.get('recommendation', '')
            rec_color = "#2e7d32" if pit_better else "#f57c00"
            rec_icon = "進站" if pit_better else "不進站"
            html_parts.append(
                f"<td style='padding: 8px; text-align: center;'>"
                f"<span style='color: {rec_color}; font-weight: bold;'>{rec_icon}</span><br/>"
                f"<span style='color: #333; font-size: 0.85em;'>{rec}</span></td>"
            )
            
            html_parts.append("</tr>")
        
        html_parts.append("</table>")
        html_parts.append("</div>")
        
        # Field tire state comparison section
        if self._fp2_predictions or summary:
            html_parts.append(
                "<div style='margin-top: 15px; padding: 10px; "
                "background: #f3e5f5; border-radius: 5px;'>"
            )
            html_parts.append("<h4 style='margin: 0 0 10px 0;'>全場輪胎狀態對比 (SC 時)</h4>")
            
            # Generate field comparison for mid-race SC as representative
            field_html = self._generate_field_tire_comparison(race_laps, selected_strategy, summary)
            html_parts.append(field_html)
            html_parts.append("</div>")
        
        # Pit Lane Traffic Warning section
        html_parts.append(
            "<div style='margin-top: 15px; padding: 10px; "
            "background: #ffebee; border-radius: 5px; border: 1px solid #ef9a9a;'>"
        )
        html_parts.append("<h4 style='margin: 0 0 8px 0; color: #c62828;'>Pit Lane Traffic 風險</h4>")
        html_parts.append(
            "<p style='margin: 0 0 8px 0; color: #333; font-size: 0.9em;'>"
            "SC 期間多車同時進站會造成 pit lane 擁堵，影響進站時間：</p>"
        )
        html_parts.append("<table style='width: 100%; border-collapse: collapse; font-size: 0.85em;'>")
        html_parts.append("<tr style='background: #ffcdd2;'>")
        html_parts.append("<th style='padding: 5px; text-align: left;'>情況</th>")
        html_parts.append("<th style='padding: 5px; text-align: center;'>額外時間</th>")
        html_parts.append("<th style='padding: 5px; text-align: left;'>說明</th>")
        html_parts.append("</tr>")
        
        traffic_scenarios = [
            ("同隊 Double Stack", "+2~4s", "隊友先進站，需等待換胎完成"),
            ("3-4 車同時進站", "+1~2s", "Pit lane 入口擁擠"),
            ("5+ 車同時進站", "+2~4s", "高度擁堵，建議錯開進站時機"),
            ("Unsafe Release 風險", "+1~2s", "5% 機率被裁判延遲放行"),
        ]
        
        for situation, delay, desc in traffic_scenarios:
            html_parts.append("<tr style='border-bottom: 1px solid #ddd;'>")
            html_parts.append(f"<td style='padding: 5px;'>{situation}</td>")
            html_parts.append(f"<td style='padding: 5px; text-align: center; color: #d32f2f; font-weight: bold;'>{delay}</td>")
            html_parts.append(f"<td style='padding: 5px; color: #666;'>{desc}</td>")
            html_parts.append("</tr>")
        
        html_parts.append("</table>")
        html_parts.append(
            "<p style='margin: 8px 0 0 0; color: #666; font-size: 0.85em; font-style: italic;'>"
            "提示：蒙地卡羅模擬已包含 pit traffic 效應，結果反映了這些延遲的統計影響。</p>"
        )
        html_parts.append("</div>")
        
        # Decision advice section
        html_parts.append(
            "<div style='margin-top: 15px; padding: 10px; "
            "background: #fff3e0; border-radius: 5px;'>"
        )
        html_parts.append("<h4 style='margin: 0 0 5px 0;'>決策建議</h4>")
        
        for scenario_type in scenario_order:
            if scenario_type not in scenario_analyses:
                continue
            scenario = scenario_analyses[scenario_type]
            if scenario.decision_advice:
                html_parts.append(
                    f"<p style='margin: 3px 0;'><b>{scenario.scenario_name}:</b></p>"
                    "<ul style='margin: 0 0 5px 20px; padding: 0;'>"
                )
                for advice in scenario.decision_advice[:2]:
                    html_parts.append(f"<li style='margin: 2px 0;'>{advice}</li>")
                html_parts.append("</ul>")
        
        html_parts.append("</div>")
        html_parts.append("</div>")
        
        # Set the HTML content
        self.scenario_label.setText("".join(html_parts))
        self.scenario_label.setStyleSheet(
            "padding: 10px; background-color: white; border-radius: 5px; "
            "border: 1px solid #ddd;"
        )
    
    def _analyze_pit_vs_stay_out(self, scenario_type: str, pit_laps: list, 
                                  race_laps: int, strategy, 
                                  fp2_predictions: list = None) -> Dict[str, Any]:
        """
        Analyze pit vs stay-out decision for a given SC scenario.
        
        Args:
            scenario_type: "early_sc", "mid_sc", "late_sc"
            pit_laps: List of planned pit stop laps
            race_laps: Total race laps
            strategy: The selected strategy
            fp2_predictions: FP2 data for field comparison
            
        Returns:
            Dict with detailed pit vs stay-out comparison including:
            - Position changes
            - Tire compound recommendations
            - Comparison with field tire states
        """
        third = race_laps // 3
        
        # Get current stint info
        stints = strategy.stints if strategy else []
        
        # Determine SC window details
        if scenario_type == "early_sc":
            sc_lap = third // 2  # Around lap 10
            sc_window = f"L1-L{third}"
        elif scenario_type == "mid_sc":
            sc_lap = third + (third // 2)  # Around lap 30
            sc_window = f"L{third+1}-L{2*third}"
        else:  # late_sc
            sc_lap = 2 * third + (third // 2)  # Around lap 45
            sc_window = f"L{2*third+1}+"
        
        remaining_laps = race_laps - sc_lap
        
        # Determine current tire at SC time
        current_tire = "MEDIUM"
        current_tire_age = sc_lap
        for stint in stints:
            if hasattr(stint, 'start_lap') and hasattr(stint, 'end_lap'):
                if stint.start_lap <= sc_lap <= stint.end_lap:
                    current_tire = stint.compound.value if hasattr(stint.compound, 'value') else str(stint.compound)
                    current_tire_age = sc_lap - stint.start_lap + 1
                    break
        
        # Calculate pit stop time loss
        normal_pit_loss = self._params.pit_loss_green if self._params else 22.0
        sc_pit_loss = self._params.pit_loss_sc if self._params else 11.0
        time_saved = normal_pit_loss - sc_pit_loss
        
        # Tire durability estimates
        durability = {'SOFT': 18, 'MEDIUM': 28, 'HARD': 40}
        current_tire_remaining = max(0, durability.get(current_tire.upper(), 28) - current_tire_age)
        
        # Pit decision analysis
        result = {
            'pit_benefit': '',
            'stay_benefit': '',
            'pit_better': True,
            'recommendation': '',
            'sc_window': sc_window,
            'sc_lap': sc_lap,
            'remaining_laps': remaining_laps,
            'current_tire': current_tire,
            'current_tire_age': current_tire_age,
            'pit_tire': '',
            'pit_position_change': '',
            'stay_position_change': '',
            'field_comparison': []
        }
        
        # Determine best tire for pit stop
        if remaining_laps <= durability['SOFT']:
            result['pit_tire'] = 'SOFT'
            pit_reasoning = f"剩 {remaining_laps} 圈可用 SOFT 衝刺"
        elif remaining_laps <= durability['MEDIUM']:
            result['pit_tire'] = 'MEDIUM'
            pit_reasoning = f"剩 {remaining_laps} 圈適合 MEDIUM"
        else:
            result['pit_tire'] = 'HARD'
            pit_reasoning = f"剩 {remaining_laps} 圈需 HARD 確保耐久"
        
        if scenario_type == "early_sc":
            # Early SC analysis
            if current_tire_remaining < remaining_laps:
                result['pit_benefit'] = f"節省 {time_saved:.0f}s + {result['pit_tire']} 新胎"
                result['stay_benefit'] = "保持位置但需額外進站"
                result['pit_better'] = True
                result['pit_position_change'] = "掉 2-4 位 (進站)"
                result['stay_position_change'] = "維持位置但輪胎老化"
                result['recommendation'] = f"建議進站換 {result['pit_tire']}"
            else:
                result['pit_benefit'] = f"節省 {time_saved:.0f}s"
                result['stay_benefit'] = "輪胎足夠不需進站"
                result['pit_better'] = False
                result['pit_position_change'] = "掉 2-4 位"
                result['stay_position_change'] = "維持位置"
                result['recommendation'] = "可不進站，維持策略"
                
        elif scenario_type == "mid_sc":
            # Mid-race SC - critical decision point
            can_finish_on_current = current_tire_remaining >= remaining_laps
            
            if can_finish_on_current:
                result['pit_benefit'] = f"新 {result['pit_tire']} + 節省 {time_saved:.0f}s"
                result['stay_benefit'] = f"{current_tire} 剩餘 {current_tire_remaining} 圈壽命足夠"
                result['pit_better'] = remaining_laps > 25  # Only pit if long remaining
                result['pit_position_change'] = "掉 2-3 位出 pit"
                result['stay_position_change'] = "維持位置到終點"
                result['recommendation'] = "可不進站" if can_finish_on_current and remaining_laps <= 25 else f"建議換 {result['pit_tire']}"
            else:
                result['pit_benefit'] = f"免費進站 + {result['pit_tire']} 完賽"
                result['stay_benefit'] = "需額外進站，時間損失大"
                result['pit_better'] = True
                result['pit_position_change'] = "掉 2-3 位但輪胎新"
                result['stay_position_change'] = "需稍後進站掉更多位"
                result['recommendation'] = f"強烈建議進站換 {result['pit_tire']}"
                
        elif scenario_type == "late_sc":
            # Late SC - position vs fresh rubber trade-off
            if remaining_laps <= 8:
                result['pit_benefit'] = f"新 SOFT 衝刺 {remaining_laps} 圈"
                result['stay_benefit'] = "保持位置優勢"
                result['pit_better'] = False  # Usually stay out
                result['pit_tire'] = 'SOFT'
                result['pit_position_change'] = "掉 3-5 位"
                result['stay_position_change'] = "維持位置"
                result['recommendation'] = "通常不進站，除非輪胎極差"
            elif remaining_laps <= 15:
                result['pit_benefit'] = f"新 SOFT + 節省 {time_saved:.0f}s"
                result['stay_benefit'] = f"{current_tire} 可撐完"
                result['pit_tire'] = 'SOFT'
                result['pit_better'] = current_tire_remaining < remaining_laps
                result['pit_position_change'] = "掉 2-4 位出 pit"
                result['stay_position_change'] = "維持但防守壓力大"
                result['recommendation'] = "視輪胎狀態與前後差距" if current_tire_remaining >= remaining_laps else "建議換 SOFT 衝刺"
            else:
                result['pit_benefit'] = f"新胎 {remaining_laps} 圈優勢"
                result['stay_benefit'] = "需額外進站"
                result['pit_better'] = True
                result['pit_position_change'] = "掉 2-3 位"
                result['stay_position_change'] = "需額外進站掉更多"
                result['recommendation'] = f"建議進站換 {result['pit_tire']}"
        
        return result
    
    def _generate_field_tire_comparison(self, race_laps: int, our_strategy, summary=None) -> str:
        """
        Generate HTML table comparing our tire state vs field at SC time.
        
        Args:
            race_laps: Total race laps
            our_strategy: Our selected strategy
            summary: MonteCarloSummary for field info
            
        Returns:
            HTML string with field comparison table
        """
        html = []
        third = race_laps // 3
        mid_lap = third + (third // 2)  # Use mid-race SC as representative
        
        # Get our tire info at mid-race SC
        our_tire = "MEDIUM"
        our_tire_age = mid_lap
        our_stints = our_strategy.stints if our_strategy else []
        for stint in our_stints:
            if hasattr(stint, 'start_lap') and hasattr(stint, 'end_lap'):
                if stint.start_lap <= mid_lap <= stint.end_lap:
                    our_tire = stint.compound.value if hasattr(stint.compound, 'value') else str(stint.compound)
                    our_tire_age = mid_lap - stint.start_lap + 1
                    break
        
        # Tire durability
        durability = {'SOFT': 18, 'MEDIUM': 28, 'HARD': 40}
        our_tire_remaining = max(0, durability.get(our_tire.upper(), 28) - our_tire_age)
        
        html.append("<p style='margin-bottom: 8px; color: #666;'>")
        html.append(f"中段 SC (L{mid_lap}) 時的輪胎狀態比較：")
        html.append("</p>")
        
        html.append("<table style='width: 100%; border-collapse: collapse; font-size: 0.85em;'>")
        html.append("<tr style='background: #9c27b0; color: white;'>")
        html.append("<th style='padding: 6px; text-align: left;'>車手/情況</th>")
        html.append("<th style='padding: 6px; text-align: center;'>輪胎</th>")
        html.append("<th style='padding: 6px; text-align: center;'>已使用</th>")
        html.append("<th style='padding: 6px; text-align: center;'>剩餘壽命</th>")
        html.append("<th style='padding: 6px; text-align: center;'>建議</th>")
        html.append("</tr>")
        
        # Our current state
        our_color = self._get_compound_color(our_tire)
        html.append("<tr style='background: #e1bee7; font-weight: bold;'>")
        html.append("<td style='padding: 6px;'>我方 (不進站)</td>")
        html.append(
            f"<td style='padding: 6px; text-align: center;'>"
            f"<span style='background: {our_color}; padding: 2px 6px; border-radius: 3px;'>"
            f"{our_tire}</span></td>"
        )
        html.append(f"<td style='padding: 6px; text-align: center;'>{our_tire_age} 圈</td>")
        remaining_color = "#4CAF50" if our_tire_remaining >= 10 else "#FF9800" if our_tire_remaining >= 5 else "#f44336"
        html.append(
            f"<td style='padding: 6px; text-align: center; color: {remaining_color};'>"
            f"~{our_tire_remaining} 圈</td>"
        )
        html.append("<td style='padding: 6px; text-align: center;'>-</td>")
        html.append("</tr>")
        
        # Our state if we pit
        remaining_laps = race_laps - mid_lap
        if remaining_laps <= 18:
            pit_tire = 'SOFT'
        elif remaining_laps <= 28:
            pit_tire = 'MEDIUM'
        else:
            pit_tire = 'HARD'
        pit_color = self._get_compound_color(pit_tire)
        pit_remaining = durability.get(pit_tire.upper(), 28)
        
        html.append("<tr style='background: #e3f2fd;'>")
        html.append("<td style='padding: 6px;'>我方 (進站後)</td>")
        html.append(
            f"<td style='padding: 6px; text-align: center;'>"
            f"<span style='background: {pit_color}; padding: 2px 6px; border-radius: 3px;'>"
            f"{pit_tire}</span></td>"
        )
        html.append("<td style='padding: 6px; text-align: center;'>0 圈</td>")
        html.append(
            f"<td style='padding: 6px; text-align: center; color: #4CAF50;'>"
            f"~{pit_remaining} 圈</td>"
        )
        html.append(f"<td style='padding: 6px; text-align: center;'>掉 2-3 位出 pit</td>")
        html.append("</tr>")
        
        # Estimated field tire states (based on typical strategies)
        field_scenarios = [
            ("多數 1 停車手", "HARD", mid_lap - 20, "已完成進站"),
            ("多數 1 停車手", "MEDIUM", mid_lap, "尚未進站"),
            ("2 停激進車手", "MEDIUM", mid_lap - 15, "第一段跑完"),
            ("領先集團", "HARD", mid_lap - 18, "提前進站"),
        ]
        
        for driver_type, tire, age, note in field_scenarios:
            field_color = self._get_compound_color(tire)
            field_remaining = max(0, durability.get(tire.upper(), 28) - age)
            remaining_color = "#4CAF50" if field_remaining >= 10 else "#FF9800" if field_remaining >= 5 else "#f44336"
            
            html.append("<tr style='border-bottom: 1px solid #ddd;'>")
            html.append(f"<td style='padding: 6px; color: #666;'>{driver_type}</td>")
            html.append(
                f"<td style='padding: 6px; text-align: center;'>"
                f"<span style='background: {field_color}; padding: 2px 6px; border-radius: 3px;'>"
                f"{tire}</span></td>"
            )
            html.append(f"<td style='padding: 6px; text-align: center;'>{age} 圈</td>")
            html.append(
                f"<td style='padding: 6px; text-align: center; color: {remaining_color};'>"
                f"~{field_remaining} 圈</td>"
            )
            html.append(f"<td style='padding: 6px; text-align: center; color: #666;'>{note}</td>")
            html.append("</tr>")
        
        html.append("</table>")
        
        # Analysis summary
        html.append("<p style='margin-top: 10px; color: #333; font-size: 0.9em;'>")
        if our_tire_remaining < 15:
            html.append(
                f"<b>分析：</b>您的 {our_tire} 輪胎剩餘壽命較短 ({our_tire_remaining} 圈)，"
                f"SC 期間進站換 {pit_tire} 可獲得新胎優勢，建議積極考慮進站。"
            )
        else:
            html.append(
                f"<b>分析：</b>您的 {our_tire} 輪胎壽命尚充足 ({our_tire_remaining} 圈)，"
                f"可考慮不進站維持位置，但須注意進站車手出站後的攻擊。"
            )
        html.append("</p>")
        
        return "".join(html)
    
    def set_field_data(self, fp2_predictions: list, opponent_strategies: dict = None):
        """
        Set field data for tire comparison analysis.
        
        Args:
            fp2_predictions: FP2->Q predictions for all drivers
            opponent_strategies: Opponent strategy settings
        """
        self._fp2_predictions = fp2_predictions or []
        self._opponent_strategies = opponent_strategies or {}
    
    def _get_pit_adjustment_for_sc(self, scenario_type: str, pit_laps: list, 
                                    race_laps: int, strategy) -> str:
        """
        Get pit timing adjustment recommendation for a specific SC scenario.
        
        Args:
            scenario_type: "no_sc", "early_sc", "mid_sc", "late_sc"
            pit_laps: List of planned pit stop laps
            race_laps: Total race laps
            strategy: The selected strategy
            
        Returns:
            HTML string with recommendation
        """
        if not pit_laps:
            return "無進站計畫"
        
        third = race_laps // 3
        
        if scenario_type == "no_sc":
            return "按原計畫執行進站"
        
        elif scenario_type == "early_sc":
            # Early SC (Lap 1 to race_laps/3)
            first_pit = pit_laps[0]
            if first_pit > third:
                return f"若 SC 出動，考慮提前至 L{max(1, third-3)}-L{third} 進站"
            else:
                return f"原進站圈 L{first_pit} 在早期 SC 範圍內，可利用 SC 進站"
        
        elif scenario_type == "mid_sc":
            # Mid-race SC
            mid_start = third + 1
            mid_end = 2 * third
            relevant_pit = None
            for p in pit_laps:
                if mid_start <= p <= mid_end + 5:
                    relevant_pit = p
                    break
            if relevant_pit:
                return f"原進站 L{relevant_pit} 接近中段 SC 窗口，注意抓住 SC 進站時機"
            else:
                return f"若中段 SC，考慮在 L{mid_start}-L{mid_end} 額外進站換新胎"
        
        elif scenario_type == "late_sc":
            # Late SC
            late_start = 2 * third + 1
            last_pit = pit_laps[-1] if pit_laps else 0
            remaining_after_last = race_laps - last_pit
            
            if remaining_after_last > 15:
                return f"晚期 SC 時可在 L{late_start}+ 進站換 SOFT 衝刺終點"
            else:
                return f"最後進站 L{last_pit} 後剩餘 {remaining_after_last} 圈，晚期 SC 可不進站"
        
        return "視情況調整"

    def get_dynamic_strategy_advice(
        self,
        current_lap: int,
        current_position: int,
        current_tire: str,
        tire_age: int,
        remaining_stops: int,
        sc_active: bool = False,
        gap_to_ahead: float = 0.0,
        gap_to_behind: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate dynamic strategy adjustment advice based on current race state.
        
        This method provides real-time strategy recommendations during a race,
        considering SC events, tire state, and position battles.
        
        Args:
            current_lap: Current lap number
            current_position: Current race position
            current_tire: Current tire compound (S/M/H)
            tire_age: Age of current tires in laps
            remaining_stops: Number of planned stops remaining
            sc_active: Whether SC is currently active
            gap_to_ahead: Gap to car ahead in seconds
            gap_to_behind: Gap to car behind in seconds
            
        Returns:
            Dict with 'action', 'reason', 'urgency' (high/medium/low), 'alternatives'
        """
        result = {
            'action': 'STAY_OUT',
            'reason': '繼續執行當前策略',
            'urgency': 'low',
            'alternatives': [],
            'pit_recommendation': None
        }
        
        race_laps = self._params.race_laps if self._params else 53
        remaining_laps = race_laps - current_lap
        
        # Tire durability estimates
        tire_limits = {'S': 18, 'M': 28, 'H': 40}
        tire_limit = tire_limits.get(current_tire.upper(), 25)
        tire_remaining_life = max(0, tire_limit - tire_age)
        
        # SC Active - Opportunistic pit decision
        if sc_active:
            pit_loss_saved = (self._params.pit_loss_green if self._params else 22.0) - \
                            (self._params.pit_loss_sc if self._params else 12.0)
            
            if remaining_stops > 0:
                # We have planned stops - should we pit now?
                if tire_age > tire_limit * 0.6:  # Tires over 60% used
                    result['action'] = 'PIT_NOW'
                    result['reason'] = f'SC進站可節省 {pit_loss_saved:.1f}s，輪胎已使用 {tire_age} 圈'
                    result['urgency'] = 'high'
                    result['pit_recommendation'] = self._recommend_compound(remaining_laps, remaining_stops - 1)
                elif tire_age > tire_limit * 0.4:
                    result['action'] = 'CONSIDER_PIT'
                    result['reason'] = f'SC進站機會良好，但輪胎狀態尚可 ({tire_age} 圈)'
                    result['urgency'] = 'medium'
                    result['pit_recommendation'] = self._recommend_compound(remaining_laps, remaining_stops - 1)
                else:
                    result['action'] = 'STAY_OUT'
                    result['reason'] = '輪胎狀態良好，保留進站機會'
                    result['urgency'] = 'low'
            else:
                # No planned stops - should we take an unplanned stop?
                if tire_remaining_life < remaining_laps * 0.3:
                    result['action'] = 'EMERGENCY_PIT'
                    result['reason'] = f'輪胎無法完賽，建議緊急進站'
                    result['urgency'] = 'high'
                    result['pit_recommendation'] = self._recommend_compound(remaining_laps, 0)
                else:
                    result['action'] = 'STAY_OUT'
                    result['reason'] = '無需額外進站，維持策略'
                    result['urgency'] = 'low'
        
        # Green flag - position battle considerations
        else:
            # Check if we need to defend
            if gap_to_behind < 1.0 and remaining_stops > 0:
                result['alternatives'].append({
                    'action': 'UNDERCUT_DEFENSE',
                    'reason': f'後車距離僅 {gap_to_behind:.1f}s，考慮防守性進站'
                })
            
            # Check if we can attack
            if gap_to_ahead < 2.0 and remaining_stops > 0:
                result['alternatives'].append({
                    'action': 'UNDERCUT_ATTACK',
                    'reason': f'前車距離 {gap_to_ahead:.1f}s，可嘗試undercut進攻'
                })
            
            # Tire life warning
            if tire_remaining_life <= 3 and remaining_stops > 0:
                result['action'] = 'PIT_SOON'
                result['reason'] = f'輪胎剩餘壽命約 {tire_remaining_life} 圈，建議盡快進站'
                result['urgency'] = 'high'
                result['pit_recommendation'] = self._recommend_compound(remaining_laps, remaining_stops - 1)
            elif tire_remaining_life <= 8 and remaining_stops > 0:
                result['action'] = 'PREPARE_PIT'
                result['reason'] = f'輪胎剩餘壽命約 {tire_remaining_life} 圈，準備進站窗口'
                result['urgency'] = 'medium'
        
        return result
    
    def _recommend_compound(self, remaining_laps: int, remaining_stops: int) -> str:
        """
        Recommend tire compound based on remaining race distance.
        
        Args:
            remaining_laps: Laps remaining in race
            remaining_stops: Stops remaining after this one
            
        Returns:
            Recommended compound ('SOFT', 'MEDIUM', 'HARD')
        """
        if remaining_stops == 0:
            # Last stint - choose based on distance
            if remaining_laps <= 18:
                return 'SOFT'
            elif remaining_laps <= 28:
                return 'MEDIUM'
            else:
                return 'HARD'
        else:
            # More stops to come - can be more aggressive
            laps_this_stint = remaining_laps // (remaining_stops + 1)
            if laps_this_stint <= 15:
                return 'SOFT'
            elif laps_this_stint <= 25:
                return 'MEDIUM'
            else:
                return 'HARD'
