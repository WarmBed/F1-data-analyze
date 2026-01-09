#!/usr/bin/env python3
"""
Race Result Analysis Tab

Comprehensive analysis tab for full race simulation results:
- Position History Chart
- Our Driver Summary
- Strategy Statistics Table
- Traffic Analysis Heatmap

Author: F1T Team
Date: 2026-01-07
"""

from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QPushButton, QGridLayout, QTabWidget, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
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


class RaceResultAnalysisTab(QWidget):
    """
    Race Result Analysis Tab.
    
    Displays comprehensive analysis after full race simulation:
    - Position History Chart
    - Our Driver Summary
    - Strategy Statistics Table
    - Traffic Analysis Heatmap
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._simulation_result = None
        self._statistics = None
        self._our_driver = None
        
        # Cache for data
        self._cached_mc_summary = None
        self._cached_results = []
        self._cached_params = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Vertical layout: Position History (top) → Strategy Performance (bottom)
        # Position History Chart
        position_group = QGroupBox(tr("POSITION_HISTORY", "Position History"))
        position_layout = QVBoxLayout(position_group)
        position_layout.setContentsMargins(5, 5, 5, 5)
        
        if HAS_PYQTGRAPH:
            self.position_plot = pg.PlotWidget()
            self.position_plot.setBackground('w')
            self.position_plot.setLabel('left', tr("POSITION", "Position"))
            self.position_plot.setLabel('bottom', tr("LAP", "Lap"))
            self.position_plot.showGrid(x=True, y=True, alpha=0.3)
            self.position_plot.invertY(True)  # P1 at top
            # Enable mouse interaction for curve highlighting
            self.position_plot.scene().sigMouseClicked.connect(self._on_chart_clicked)
            position_layout.addWidget(self.position_plot)
        else:
            position_layout.addWidget(QLabel(tr("PYQTGRAPH_REQUIRED", "pyqtgraph required for charts")))
        
        layout.addWidget(position_group, 2)  # 66% for position chart
        
        # Strategy Performance Table (below Position History)
        self.strategy_perf_group = QGroupBox(tr("STRATEGY_PERFORMANCE", "策略表現統計"))
        strategy_perf_layout = QVBoxLayout(self.strategy_perf_group)
        self.strategy_perf_table = QTableWidget()
        self.strategy_perf_table.setColumnCount(7)  # Removed "平均" column
        self.strategy_perf_table.setHorizontalHeaderLabels([
            tr("STRATEGY", "策略"),
            tr("WIN_RATE", "勝率%"),
            tr("MOST_LIKELY", "最可能"),
            tr("PROBABILITY", "機率%"),
            tr("BEST_POS", "最高"),
            tr("WORST_POS", "最低"),
            tr("REPORT", "報告")
        ])
        self.strategy_perf_table.setAlternatingRowColors(True)
        header = self.strategy_perf_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        strategy_perf_layout.addWidget(self.strategy_perf_table)
        layout.addWidget(self.strategy_perf_group, 1)  # 33% for strategy table
        
        # Track report buttons for cleanup
        self._report_buttons = []
        
        # Traffic Analysis Heatmap
        self.traffic_group = QGroupBox(tr("TRAFFIC_ANALYSIS", "車流分析"))
        self.traffic_group.setVisible(False)  # Hidden until data available
        traffic_layout = QVBoxLayout(self.traffic_group)
        
        # Import TrafficHeatmapWidget
        from strategy_simulator.gui.widgets.traffic_heatmap_widget import TrafficHeatmapWidget
        
        # Traffic Heatmap Widget
        self.traffic_heatmap = TrafficHeatmapWidget()
        self.traffic_heatmap.setMinimumHeight(200)
        traffic_layout.addWidget(self.traffic_heatmap)
        
        # Add traffic_group to main layout
        layout.addWidget(self.traffic_group, 1)
        
        # Track highlighted driver for chart interaction
        self._highlighted_driver = None
        self._plot_items = {}  # {driver_code: PlotDataItem}
        
        # Placeholder message
        self.placeholder = QLabel(
            "執行完整賽事模擬後可查看詳細結果分析。\n\n"
            "1. 在左側配置賽事參數\n"
            "2. 執行「總時間最短策略」分析\n"
            "3. 執行「完整賽事」模擬\n"
            "4. 結果將顯示於此"
        )
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 50px;
                background-color: #f8f8f8;
                border-radius: 10px;
            }
        """)
        
    def _setup_summary_labels(self):
        """Setup summary labels."""
        summary_data = [
            ("final_pos", tr("FINAL_POSITION", "Final Position")),
            ("avg_pos", tr("AVG_POSITION", "Avg Position")),
            ("best_lap", tr("BEST_LAP", "Best Lap")),
            ("avg_lap", tr("AVG_LAP", "Avg Lap")),
            ("stops", tr("PIT_STOPS", "Pit Stops")),
            ("total_time", tr("TOTAL_TIME", "Total Time")),
            ("gap_to_leader", tr("GAP_TO_LEADER", "Gap to Leader")),
            ("gap_to_ahead", tr("GAP_TO_AHEAD", "Gap to Ahead"))
        ]
        
        for row, (key, label_text) in enumerate(summary_data):
            label = QLabel(label_text + ":")
            label.setStyleSheet("font-weight: bold;")
            
            value_label = QLabel("--")
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            setattr(self, f"{key}_label", value_label)
            
            col = 0 if row < 4 else 2
            row_offset = row if row < 4 else row - 4
            
            self.summary_layout.addWidget(label, row_offset, col)
            self.summary_layout.addWidget(value_label, row_offset, col + 1)
    
    def update_simulation_result(self, result: Dict[str, Any]):
        """
        Update tab with full race simulation results.
        
        Args:
            result: Dict with 'single' (RaceResult), 'statistics' (Dict), 
                    and 'strategy_results' (List) keys
        """
        print(f"[RACE_RESULT_TAB] Updating with simulation results...")
        
        self._simulation_result = result.get('single')
        self._statistics = result.get('statistics')
        self._cached_results = result.get('strategy_results', [])
        
        print(f"[RACE_RESULT_TAB] Received {len(self._cached_results)} strategy results")
        
        # Update position chart
        if self._simulation_result and HAS_PYQTGRAPH:
            self._update_position_chart()
        
        # Update our driver summary
        if self._simulation_result and self._our_driver:
            self._update_summary()
        
        # Update strategy statistics table
        if self._statistics:
            self._update_strategy_statistics()
        
        # Update traffic heatmap
        if self._simulation_result:
            self._update_traffic_analysis()
        
        print(f"[RACE_RESULT_TAB] Results updated successfully")
    
    def _update_position_chart(self):
        """Update position history chart with interactive curve highlighting and SC events."""
        if not HAS_PYQTGRAPH or not self._simulation_result:
            return
        
        self.position_plot.clear()
        self._plot_items.clear()  # Clear cached plot items
        
        # Get all drivers from final standings
        if not hasattr(self._simulation_result, 'final_standings') or not self._simulation_result.final_standings:
            print("[RACE_RESULT_TAB] No final_standings available")
            return
        
        # RaceResult uses driver_code, not driver
        drivers = [result.driver_code for result in self._simulation_result.final_standings]
        if not drivers:
            print("[RACE_RESULT_TAB] No drivers in final_standings")
            return
        
        # Add SC event regions (if available)
        sc_events = getattr(self._simulation_result, 'sc_events', [])
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
        
        # Generate colors
        colors = self._generate_colors(len(drivers))
        
        # Plot each driver's position history
        for i, driver in enumerate(drivers):
            try:
                # Use get_position_history() method
                positions = self._simulation_result.get_position_history(driver)
                if not positions:
                    continue
                
                laps = list(range(len(positions)))
                
                # Highlight our driver or highlighted driver
                is_highlighted = (driver == self._our_driver) or (driver == self._highlighted_driver)
                width = 4 if is_highlighted else 1
                alpha = 255 if is_highlighted else 120
                
                color = colors[i]
                if len(color) == 3:
                    color = (*color, alpha)
                
                pen = pg.mkPen(color=color, width=width)
                
                plot_item = self.position_plot.plot(
                    laps, positions,
                    pen=pen,
                    name=driver
                )
                
                # Store plot item for later highlighting
                self._plot_items[driver] = {
                    'item': plot_item,
                    'color': colors[i],
                    'positions': positions,
                    'laps': laps
                }
            except Exception as e:
                print(f"[RACE_RESULT_TAB] Error plotting {driver}: {e}")
                continue
        
        # Add overtake markers (triangles) from OvertakeAttempt data
        self._add_overtake_markers()
        
        self.position_plot.addLegend()
        print(f"[RACE_RESULT_TAB] Position chart updated for {len(drivers)} drivers")
    
    def _on_chart_clicked(self, event):
        """Handle chart click to highlight driver curve."""
        if not HAS_PYQTGRAPH or not self._plot_items:
            return
        
        # Get click position
        pos = event.scenePos()
        vb = self.position_plot.getViewBox()
        mouse_point = vb.mapSceneToView(pos)
        
        clicked_lap = int(round(mouse_point.x()))
        clicked_pos = int(round(mouse_point.y()))
        
        # Find closest driver at this position
        closest_driver = None
        min_distance = float('inf')
        
        for driver, data in self._plot_items.items():
            positions = data['positions']
            if 0 <= clicked_lap < len(positions):
                distance = abs(positions[clicked_lap] - clicked_pos)
                if distance < min_distance and distance < 2:  # Within 2 positions
                    min_distance = distance
                    closest_driver = driver
        
        if closest_driver:
            self._highlight_driver(closest_driver)
    
    def _add_overtake_markers(self):
        """Add overtake attempt markers (triangles) to position chart."""
        if not HAS_PYQTGRAPH or not self._simulation_result:
            return
        
        # Get overtake attempts from simulation result
        overtake_attempts = getattr(self._simulation_result, 'overtake_attempts', [])
        if not overtake_attempts:
            print("[RACE_RESULT_TAB] No overtake attempts to display")
            return
        
        print(f"[RACE_RESULT_TAB] Adding {len(overtake_attempts)} overtake markers")
        
        # Group overtakes by driver for efficiency
        successful_overtakes = {}  # driver -> [(lap, position), ...]
        failed_overtakes = {}      # driver -> [(lap, position), ...]
        
        for attempt in overtake_attempts:
            driver = attempt.attacker
            lap = attempt.lap
            
            # Get position at this lap
            if driver in self._plot_items:
                positions = self._plot_items[driver]['positions']
                if 0 <= lap < len(positions):
                    position = positions[lap]
                    
                    if attempt.success:
                        if driver not in successful_overtakes:
                            successful_overtakes[driver] = []
                        successful_overtakes[driver].append((lap, position))
                    else:
                        if driver not in failed_overtakes:
                            failed_overtakes[driver] = []
                        failed_overtakes[driver].append((lap, position))
        
        # Plot successful overtakes (green upward triangles)
        for driver, points in successful_overtakes.items():
            if points:
                laps = [p[0] for p in points]
                positions = [p[1] for p in points]
                scatter = pg.ScatterPlotItem(
                    x=laps,
                    y=positions,
                    symbol='t',  # Triangle up
                    size=12,
                    pen=pg.mkPen(color=(0, 200, 0), width=2),
                    brush=pg.mkBrush(0, 255, 0, 200),
                    name=f"{driver} 成功超車"
                )
                self.position_plot.addItem(scatter)
        
        # Plot failed overtakes (red downward triangles)
        for driver, points in failed_overtakes.items():
            if points:
                laps = [p[0] for p in points]
                positions = [p[1] for p in points]
                scatter = pg.ScatterPlotItem(
                    x=laps,
                    y=positions,
                    symbol='t1',  # Triangle down
                    size=12,
                    pen=pg.mkPen(color=(200, 0, 0), width=2),
                    brush=pg.mkBrush(255, 0, 0, 200),
                    name=f"{driver} 失敗嘗試"
                )
                self.position_plot.addItem(scatter)
        
        total_success = sum(len(v) for v in successful_overtakes.values())
        total_failed = sum(len(v) for v in failed_overtakes.values())
        print(f"[RACE_RESULT_TAB] Overtake markers added: {total_success} successful (▲), {total_failed} failed (▼)")
    
    def _highlight_driver(self, driver_code: str):
        """Highlight a specific driver's curve."""
        if not HAS_PYQTGRAPH or not self._plot_items:
            return
        
        # Toggle highlight
        if self._highlighted_driver == driver_code:
            self._highlighted_driver = None
        else:
            self._highlighted_driver = driver_code
        
        # Redraw chart with new highlighting
        self._update_position_chart()
        print(f"[RACE_RESULT_TAB] Highlighted driver: {self._highlighted_driver}")
    
    def _update_summary(self):
        """Update our driver summary."""
        # Check if summary labels exist (they may not be created in current UI layout)
        if not hasattr(self, 'final_pos_label'):
            print("[RACE_RESULT_TAB] Summary labels not created, skipping _update_summary")
            return
            
        if not self._simulation_result or not self._our_driver:
            print("[RACE_RESULT_TAB] No simulation result or our_driver not set")
            return
        
        # Find our driver in final_standings (RaceResult uses driver_code)
        driver_result = None
        for result in self._simulation_result.final_standings:
            if result.driver_code == self._our_driver:
                driver_result = result
                break
        
        if not driver_result:
            print(f"[RACE_RESULT_TAB] Driver {self._our_driver} not found in final_standings")
            return
        
        # Update labels with RaceResult data
        self.final_pos_label.setText(f"P{driver_result.final_position}")
        
        # Calculate average position from position history
        position_history = self._simulation_result.get_position_history(self._our_driver)
        if position_history:
            avg_pos = sum(position_history) / len(position_history)
            self.avg_pos_label.setText(f"P{avg_pos:.1f}")
        else:
            self.avg_pos_label.setText("--")
        
        # Lap time stats (if available)
        self.best_lap_label.setText("--")  # FullRaceSimulation doesn't track lap times
        self.avg_lap_label.setText("--")
        
        # Pit stops
        self.stops_label.setText(str(driver_result.pit_stops))
        
        # Total time
        self.total_time_label.setText(f"{driver_result.total_time:.3f}s")
        
        # Gap to leader
        self.gap_to_leader_label.setText(f"+{driver_result.gap_to_winner:.3f}s")
        
        # Gap to ahead - calculate from final standings
        if driver_result.final_position > 1:
            for r in self._simulation_result.final_standings:
                if r.final_position == driver_result.final_position - 1:
                    gap = driver_result.total_time - r.total_time
                    self.gap_to_ahead_label.setText(f"+{gap:.3f}s")
                    break
            else:
                self.gap_to_ahead_label.setText("--")
        else:
            self.gap_to_ahead_label.setText("LEADER")
        
        print(f"[RACE_RESULT_TAB] Summary updated for {self._our_driver}")
    
    def _update_strategy_statistics(self):
        """Update strategy performance table."""
        if not self._statistics:
            return
        
        strategy_stats = self._statistics.get('strategy_performance', {})
        if not strategy_stats:
            return
        
        # Sort by win rate
        sorted_stats = sorted(
            strategy_stats.items(),
            key=lambda x: x[1].get('win_rate', 0),
            reverse=True
        )[:5]  # Top 5
        
        self.strategy_perf_table.setRowCount(len(sorted_stats))
        
        # Clear old report buttons
        for btn in self._report_buttons:
            btn.deleteLater()
        self._report_buttons.clear()
        
        for row, (strategy_name, stats) in enumerate(sorted_stats):
            # Column 0: Strategy name
            self.strategy_perf_table.setItem(row, 0, QTableWidgetItem(strategy_name))
            
            # Column 1: Win rate
            win_rate = stats.get('win_rate', 0)
            item = QTableWidgetItem(f"{win_rate:.1f}%")
            item.setTextAlignment(Qt.AlignCenter)
            if win_rate >= 50:
                item.setBackground(QBrush(QColor(200, 255, 200)))
            self.strategy_perf_table.setItem(row, 1, item)
            
            # Column 2: Most likely position (removed avg_pos column)
            most_likely = stats.get('most_likely_position', '--')
            item = QTableWidgetItem(f"P{most_likely}")
            item.setTextAlignment(Qt.AlignCenter)
            self.strategy_perf_table.setItem(row, 2, item)
            
            # Column 3: Probability (出現該名次的百分比)
            # 注意：race_simulator 輸出的鍵名是 'most_likely_position_pct'
            probability = stats.get('most_likely_position_pct', stats.get('most_likely_probability', 0))
            item = QTableWidgetItem(f"{probability:.1f}%")
            item.setTextAlignment(Qt.AlignCenter)
            self.strategy_perf_table.setItem(row, 3, item)
            
            # Column 4: Best position
            best = stats.get('best_position', '--')
            item = QTableWidgetItem(f"P{best}")
            item.setTextAlignment(Qt.AlignCenter)
            self.strategy_perf_table.setItem(row, 4, item)
            
            # Column 5: Worst position
            worst = stats.get('worst_position', '--')
            item = QTableWidgetItem(f"P{worst}")
            item.setTextAlignment(Qt.AlignCenter)
            self.strategy_perf_table.setItem(row, 5, item)
            
            # Column 6: Report button
            report_btn = QPushButton(tr("VIEW_REPORT", "查看"))
            report_btn.setMaximumWidth(60)
            # Store strategy info for report generation
            report_btn.clicked.connect(lambda checked, name=strategy_name: self._show_strategy_report(name))
            self.strategy_perf_table.setCellWidget(row, 6, report_btn)
            self._report_buttons.append(report_btn)
        
        self.strategy_perf_group.show()
    
    def _update_traffic_analysis(self):
        """Update traffic analysis heatmap (只在 Simple/Complete 模式時執行)."""
        if not self._simulation_result:
            print("[RACE_RESULT_TAB] No simulation result for traffic analysis")
            return
        
        # 檢查是否來自 Simple/Complete 模式
        # 這些模式的結果會有特定標記或來源
        is_simple_or_complete = hasattr(self._simulation_result, '_mode') and \
                                self._simulation_result._mode in ['simple', 'complete']
        
        if not is_simple_or_complete:
            # 不是 Simple/Complete 模式，跳過 Traffic Analysis
            print("[RACE_RESULT_TAB] Skipping traffic analysis (not Simple/Complete mode)")
            self.traffic_group.hide()
            return
        
        # Get traffic data from simulation result
        traffic_data = getattr(self._simulation_result, 'traffic_data', None)
        
        # ⚡ 延遲載入優化：如果 traffic_data 是空字典，表示尚未分析
        if traffic_data is not None and len(traffic_data) == 0:
            print("[RACE_RESULT_TAB] Running traffic analysis for Simple/Complete mode...")
            
            # 直接調用內部方法，不需要創建模擬器
            try:
                # 從 race_simulator 模組導入分析函數
                # 避免創建完整的模擬器實例（需要太多參數）
                from strategy_simulator.core import race_simulator
                
                # 創建一個臨時的 FullRaceSimulator 來調用分析方法
                # 但我們只需要 _analyze_all_drivers_traffic 方法
                # 這個方法是靜態的，不需要完整初始化
                
                # 直接實例化並調用
                dummy_sim = race_simulator.FullRaceSimulator(
                    self._cached_params,
                    sc_probability=0.3,
                    overtaking_difficulty=0.5,
                    simple_mode=True
                )
                
                traffic_data = dummy_sim._analyze_all_drivers_traffic(self._simulation_result.lap_states)
                self._simulation_result.traffic_data = traffic_data
                print(f"[RACE_RESULT_TAB] ✅ Traffic analysis complete: {len(traffic_data)} drivers")
            except Exception as e:
                print(f"[RACE_RESULT_TAB] ⚠️ Traffic analysis failed: {e}")
                import traceback
                traceback.print_exc()
                self.traffic_group.hide()
                return
        
        if not traffic_data or not isinstance(traffic_data, dict) or len(traffic_data) == 0:
            print("[RACE_RESULT_TAB] No traffic_data available")
            self.traffic_group.hide()
            return
        
        try:
            # Prepare drivers_data for TrafficHeatmapWidget
            drivers_data = self._prepare_traffic_heatmap_data()
            
            if not drivers_data:
                print("[RACE_RESULT_TAB] No traffic data prepared")
                self.traffic_group.hide()
                return
            
            # Get max lap from simulation result
            max_lap = getattr(self._simulation_result, 'race_laps', 0)
            
            # Get race info
            race_info = f"{self._cached_params.race if self._cached_params else ''} {self._cached_params.session if self._cached_params else ''}"
            
            # Update heatmap widget
            self.traffic_heatmap.update_data(drivers_data, max_lap, race_info)
            self.traffic_group.show()
            print(f"[RACE_RESULT_TAB] Traffic analysis updated: {len(drivers_data)} drivers, {max_lap} laps")
        except Exception as e:
            import traceback
            print(f"[RACE_RESULT_TAB] Error updating traffic heatmap: {e}")
            traceback.print_exc()
            self.traffic_group.hide()
    
    def _prepare_traffic_heatmap_data(self) -> List[Dict[str, Any]]:
        """
        準備 Traffic Heatmap 所需的數據格式。
        
        Returns:
            List[Dict]: 車手數據列表，包含 driver_code, final_position, lap_states, traffic_stats
        """
        if not self._simulation_result:
            return []
        
        drivers_data = []
        
        # 從 final_standings 獲取所有車手
        for result in self._simulation_result.final_standings:
            driver_code = result.driver_code
            
            # 從 traffic_data 獲取該車手的 traffic 狀態
            traffic_info = self._simulation_result.traffic_data.get(driver_code, {})
            
            # 準備 lap_states：每一圈的狀態
            lap_states = {}
            lap_details = traffic_info.get('lap_details', {})
            
            for lap_num, lap_info in lap_details.items():
                # 判斷狀態：0=clean, 1=traffic, 2=sc_vsc, -1=no_data
                if lap_info.get('sc_active', False) or lap_info.get('vsc_active', False):
                    state = 2  # SC/VSC
                elif lap_info.get('blocked', False):
                    state = 1  # Traffic (gap < threshold)
                elif lap_info.get('clean', True):
                    state = 0  # Clean
                else:
                    state = -1  # No data
                
                lap_states[int(lap_num)] = state
            
            # 統計數據
            traffic_stats = {
                "blocked_laps": traffic_info.get('total_blocked_laps', 0),
                "clean_laps": traffic_info.get('clean_laps', 0),
                "sc_vsc_laps": traffic_info.get('sc_vsc_laps', 0)
            }
            
            drivers_data.append({
                "driver_code": driver_code,
                "final_position": result.final_position,
                "lap_states": lap_states,
                "traffic_stats": traffic_stats
            })
        
        return drivers_data
    
    def _show_strategy_report(self, strategy_name: str):
        """Show detailed report for a strategy."""
        print(f"[RACE_RESULT_TAB] Generating report for {strategy_name}...")
        
        # Get win rate from statistics (the source of truth for win rates)
        win_rate_from_stats = 0.0
        if self._statistics and 'strategy_performance' in self._statistics:
            stats = self._statistics['strategy_performance'].get(strategy_name, {})
            win_rate_from_stats = stats.get('win_rate', 0.0)
            print(f"[RACE_RESULT_TAB] Win rate from statistics: {win_rate_from_stats:.1f}%")
        
        # Find the strategy result from cached results
        # Strategy names in table are like "H-S", "S-M-H" (tire notation using '-')
        # But get_stint_notation() returns "H→S", "S→M→H" (using '→')
        strategy_result = None
        
        # Normalize strategy name for comparison (H-S -> HS, H→S -> HS)
        def normalize_name(name: str) -> str:
            return name.replace('-', '').replace('→', '').replace(' ', '').upper()
        
        target_normalized = normalize_name(strategy_name)
        
        for result in self._cached_results:
            # Try exact match first
            if result.strategy_name == strategy_name:
                strategy_result = result
                break
            # Try matching by normalized tire notation
            if hasattr(result, 'get_stint_notation'):
                notation = result.get_stint_notation()
                if normalize_name(notation) == target_normalized:
                    strategy_result = result
                    print(f"[RACE_RESULT_TAB] Matched {strategy_name} to {result.strategy_name} ({notation})")
                    break
            # Try if normalized names match
            if normalize_name(result.strategy_name) == target_normalized:
                strategy_result = result
                break
        
        if not strategy_result:
            # Fallback: use first result if available
            if self._cached_results:
                strategy_result = self._cached_results[0]
                print(f"[RACE_RESULT_TAB] Using fallback strategy: {strategy_result.strategy_name}")
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "策略報告",
                    f"找不到策略 {strategy_name} 的數據"
                )
                return
        
        # ✅ Inject win_probability into strategy_result if not present
        if not hasattr(strategy_result, 'win_probability') or strategy_result.win_probability == 0:
            # Try to add it dynamically
            try:
                strategy_result.win_probability = win_rate_from_stats
                print(f"[RACE_RESULT_TAB] Injected win_probability: {win_rate_from_stats:.1f}%")
            except AttributeError:
                # If the object doesn't allow new attributes, wrap it
                pass
        
        # Get simulation data from cached results
        simulation_data = {
            'final_standings': getattr(self._simulation_result, 'final_standings', []) if self._simulation_result else [],
            'position_history': {},
            'sc_events': getattr(self._simulation_result, 'sc_events', []) if self._simulation_result else [],
        }
        
        # Get position history if available
        if self._simulation_result:
            for driver in ['VER', 'NOR', 'LEC', 'HAM', 'RUS', 'SAI', 'PIA', 'ALO', 'STR', 'OCO']:
                history = self._simulation_result.get_position_history(driver) if hasattr(self._simulation_result, 'get_position_history') else []
                if history:
                    simulation_data['position_history'][driver] = history
        
        # Get traffic data from simulation result
        traffic_data = getattr(self._simulation_result, 'traffic_data', None) if self._simulation_result else None
        
        # Get our driver and grid position
        our_driver = self._our_driver or 'VER'
        grid_position = 1
        track_name = 'Unknown'
        
        # Try to get track name from main window first (most reliable)
        main_window = self.window()
        if main_window and hasattr(main_window, 'input_panel'):
            track_name = main_window.input_panel.track_combo.currentText()
        
        # Try to get from cached params
        if self._cached_params:
            grid_position = self._cached_params.get('driver_start_position', 1) or 1
            # Only use cached track if we didn't get it from main window
            if track_name == 'Unknown':
                if hasattr(self._cached_params, 'race'):
                    track_name = self._cached_params.race
                elif isinstance(self._cached_params, dict):
                    track_name = self._cached_params.get('track', 'Unknown')
        
        # Generate report using StrategyReportGenerator
        generator = StrategyReportGenerator()
        report_text = generator.generate_report(
            strategy_result=strategy_result,
            mc_summary=self._cached_mc_summary,
            simulation_data=simulation_data,
            traffic_data=traffic_data,
            competitors_data=None,
            scenario_analyses=None,
            our_driver=our_driver,
            grid_position=grid_position,
            track_name=track_name,
            display_strategy_name=strategy_name,
            display_win_rate=win_rate_from_stats,
        )
        
        # Show dialog
        dialog = StrategyReportDialog(report_text, strategy_name, self)
        dialog.exec_()
    
    def _generate_colors(self, count: int) -> list:
        """Generate distinct colors for plotting."""
        import colorsys
        colors = []
        for i in range(count):
            hue = i / count
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
            colors.append([int(c * 255) for c in rgb])
        return colors
    
    def set_our_driver(self, driver: str):
        """Set our driver code."""
        self._our_driver = driver
        print(f"[RACE_RESULT_TAB] Our driver set to: {driver}")
    
    def clear(self):
        """Clear all data and reset UI."""
        self._simulation_result = None
        self._statistics = None
        
        if HAS_PYQTGRAPH:
            self.position_plot.clear()
        
        # Clear summary labels
        for key in ['final_pos', 'avg_pos', 'best_lap', 'avg_lap', 
                    'stops', 'total_time', 'gap_to_leader', 'gap_to_ahead']:
            label = getattr(self, f"{key}_label", None)
            if label:
                label.setText("--")
        
        # Clear tables
        self.strategy_perf_table.setRowCount(0)
        self.strategy_perf_group.hide()
        
        # Clear traffic heatmap
        self.traffic_heatmap.clear()
        self.traffic_group.hide()
        
        print(f"[RACE_RESULT_TAB] Cleared all data")
