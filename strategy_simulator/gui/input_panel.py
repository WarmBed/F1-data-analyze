#!/usr/bin/env python3
"""
Input Panel for Race Strategy Simulator

Contains all input controls for simulation parameters.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Optional, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QPushButton, QLabel, QScrollArea,
    QFrame, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from strategy_simulator.gui.widgets import SCEventInjectorWidget


class InputPanel(QWidget):
    """
    Input panel with race selection and simulation parameters.
    
    Sections:
    1. Race Selection (Year, Track, Session)
    2. Tire Degradation (from Long Run or manual)
    3. Fuel Parameters
    4. Strategy Constraints
    5. Monte Carlo Settings
    6. Run Button
    """
    
    # Signals
    run_simulation = pyqtSignal(dict)  # Emits parameter dict
    track_changed = pyqtSignal(str)
    deg_source_changed = pyqtSignal(str)  # Emits degradation source type
    longrun_settings_requested = pyqtSignal()  # Request to open Long Run dialog
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._track_list: List[str] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the input panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Scroll area for all inputs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(scroll)
        
        # Container widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(10)
        scroll.setWidget(container)
        
        # Section 1: Race Selection
        container_layout.addWidget(self._create_race_selection())
        
        # Section 2: Tire Degradation
        container_layout.addWidget(self._create_degradation_section())
        
        # Section 3: Fuel Parameters
        container_layout.addWidget(self._create_fuel_section())
        
        # Section 4: Opponent Driver Selection (FP2 -> Q)
        container_layout.addWidget(self._create_opponent_selection())
        
        # Section 5: Race Scenario Settings (SC events)
        container_layout.addWidget(self._create_race_conditions_section())
        
        # Section 6: Strategy Constraints
        container_layout.addWidget(self._create_constraints_section())
        
        # Section 6: Monte Carlo
        container_layout.addWidget(self._create_monte_carlo_section())
        
        # Spacer
        container_layout.addStretch()
        
        # Run button
        self.run_button = QPushButton("執行模擬")
        self.run_button.setMinimumHeight(50)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.run_button.clicked.connect(self._on_run_clicked)
        layout.addWidget(self.run_button)
    
    def _create_race_selection(self) -> QGroupBox:
        """Create race selection group."""
        group = QGroupBox("賽事選擇")
        layout = QFormLayout(group)
        
        # Year
        self.year_combo = QComboBox()
        self.year_combo.addItems(['2025', '2024', '2023'])
        layout.addRow("年份:", self.year_combo)
        
        # Track
        self.track_combo = QComboBox()
        self.track_combo.currentTextChanged.connect(self._on_track_changed)
        layout.addRow("賽道:", self.track_combo)
        
        # Race laps
        self.laps_spin = QSpinBox()
        self.laps_spin.setRange(30, 80)
        self.laps_spin.setValue(53)
        layout.addRow("比賽圈數:", self.laps_spin)
        
        # Base lap time
        self.base_time_spin = QDoubleSpinBox()
        self.base_time_spin.setRange(60.0, 130.0)
        self.base_time_spin.setValue(91.5)
        self.base_time_spin.setDecimals(3)
        self.base_time_spin.setSuffix(" 秒")
        layout.addRow("基準圈時:", self.base_time_spin)
        
        return group
    
    def _create_degradation_section(self) -> QGroupBox:
        """Create tire degradation section."""
        group = QGroupBox("輪胎衰退 (秒/圈)")
        layout = QVBoxLayout(group)
        
        # Data source row with Long Run button
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("來源:"))
        
        self.deg_source_combo = QComboBox()
        self.deg_source_combo.addItems(['手動輸入', '從 Long Run 數據', '賽道預設值'])
        self.deg_source_combo.currentTextChanged.connect(self._on_deg_source_changed)
        source_layout.addWidget(self.deg_source_combo)
        
        # Long Run Settings button
        self.longrun_settings_btn = QPushButton("Long Run 設定")
        self.longrun_settings_btn.setToolTip("開啟 Long Run 分析對話框，手動選擇 stint 並計算衰退率")
        self.longrun_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.longrun_settings_btn.clicked.connect(self._on_longrun_settings_clicked)
        source_layout.addWidget(self.longrun_settings_btn)
        
        layout.addLayout(source_layout)
        
        # Manual input fields
        self.deg_manual_widget = QWidget()
        deg_form = QFormLayout(self.deg_manual_widget)
        deg_form.setContentsMargins(0, 10, 0, 0)
        
        # Soft
        self.soft_deg_spin = QDoubleSpinBox()
        self.soft_deg_spin.setRange(0.001, 0.50)
        self.soft_deg_spin.setValue(0.120)
        self.soft_deg_spin.setDecimals(3)
        self.soft_deg_spin.setSingleStep(0.005)
        deg_form.addRow("SOFT:", self.soft_deg_spin)
        
        # Medium
        self.medium_deg_spin = QDoubleSpinBox()
        self.medium_deg_spin.setRange(0.001, 0.50)
        self.medium_deg_spin.setValue(0.080)
        self.medium_deg_spin.setDecimals(3)
        self.medium_deg_spin.setSingleStep(0.005)
        deg_form.addRow("MEDIUM:", self.medium_deg_spin)
        
        # Hard
        self.hard_deg_spin = QDoubleSpinBox()
        self.hard_deg_spin.setRange(0.001, 0.50)
        self.hard_deg_spin.setValue(0.045)
        self.hard_deg_spin.setDecimals(3)
        self.hard_deg_spin.setSingleStep(0.005)
        deg_form.addRow("HARD:", self.hard_deg_spin)
        
        layout.addWidget(self.deg_manual_widget)
        
        # Compound time deltas
        layout.addWidget(QLabel("複合物差異 (相對 MEDIUM):"))
        
        delta_widget = QWidget()
        delta_form = QFormLayout(delta_widget)
        delta_form.setContentsMargins(0, 5, 0, 0)
        
        self.soft_delta_spin = QDoubleSpinBox()
        self.soft_delta_spin.setRange(-3.0, 0.0)
        self.soft_delta_spin.setValue(-0.20)  # Updated: was -0.8, now uses trained value
        self.soft_delta_spin.setDecimals(2)
        self.soft_delta_spin.setSuffix(" 秒")
        delta_form.addRow("SOFT:", self.soft_delta_spin)
        
        self.hard_delta_spin = QDoubleSpinBox()
        self.hard_delta_spin.setRange(0.0, 3.0)
        self.hard_delta_spin.setValue(0.40)  # Updated: was 0.5, now uses Pirelli estimate
        self.hard_delta_spin.setDecimals(2)
        self.hard_delta_spin.setSuffix(" 秒")
        delta_form.addRow("HARD:", self.hard_delta_spin)
        
        layout.addWidget(delta_widget)
        
        return group
    
    def _create_fuel_section(self) -> QGroupBox:
        """Create fuel parameters section."""
        group = QGroupBox("燃油參數")
        layout = QFormLayout(group)
        
        # Start fuel
        self.start_fuel_spin = QDoubleSpinBox()
        self.start_fuel_spin.setRange(80.0, 130.0)
        self.start_fuel_spin.setValue(110.0)
        self.start_fuel_spin.setSuffix(" kg")
        layout.addRow("起始燃油:", self.start_fuel_spin)
        
        # Fuel per lap
        self.fuel_per_lap_spin = QDoubleSpinBox()
        self.fuel_per_lap_spin.setRange(1.0, 3.0)
        self.fuel_per_lap_spin.setValue(1.70)
        self.fuel_per_lap_spin.setDecimals(2)
        self.fuel_per_lap_spin.setSuffix(" kg/圈")
        layout.addRow("消耗量:", self.fuel_per_lap_spin)
        
        # Fuel effect
        self.fuel_effect_spin = QDoubleSpinBox()
        self.fuel_effect_spin.setRange(0.01, 0.10)
        self.fuel_effect_spin.setValue(0.030)
        self.fuel_effect_spin.setDecimals(3)
        self.fuel_effect_spin.setSuffix(" 秒/kg")
        layout.addRow("燃油影響:", self.fuel_effect_spin)
        
        # Pit loss
        pit_layout = QHBoxLayout()
        
        self.pit_green_spin = QDoubleSpinBox()
        self.pit_green_spin.setRange(15.0, 35.0)
        self.pit_green_spin.setValue(24.0)
        self.pit_green_spin.setSuffix("秒")
        pit_layout.addWidget(QLabel("綠旗:"))
        pit_layout.addWidget(self.pit_green_spin)
        
        self.pit_sc_spin = QDoubleSpinBox()
        self.pit_sc_spin.setRange(8.0, 20.0)
        self.pit_sc_spin.setValue(12.0)
        self.pit_sc_spin.setSuffix("秒")
        pit_layout.addWidget(QLabel("SC:"))
        pit_layout.addWidget(self.pit_sc_spin)
        
        layout.addRow("進站損失:", pit_layout)
        
        # Pit congestion (Q17)
        congestion_layout = QHBoxLayout()
        
        self.pit_congestion_check = QCheckBox("考慮 Pit Lane 擁擠")
        self.pit_congestion_check.setChecked(False)
        self.pit_congestion_check.toggled.connect(self._on_pit_congestion_toggled)
        congestion_layout.addWidget(self.pit_congestion_check)
        
        self.pit_congestion_spin = QDoubleSpinBox()
        self.pit_congestion_spin.setRange(0.5, 5.0)
        self.pit_congestion_spin.setValue(2.0)
        self.pit_congestion_spin.setSuffix("秒/車")
        self.pit_congestion_spin.setEnabled(False)
        congestion_layout.addWidget(self.pit_congestion_spin)
        congestion_layout.addStretch()
        
        layout.addRow("", congestion_layout)
        
        return group
    
    def _create_opponent_selection(self) -> QGroupBox:
        """Create driver selection section (FP2 -> Q ranking)."""
        group = QGroupBox("🏎️ 模擬車手選擇 (FP2 → Q 數據)")
        layout = QVBoxLayout(group)
        
        # Driver selection mode (removed warning info label for cleaner UI)
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("選擇模式:"))
        
        self.opponent_mode_combo = QComboBox()
        self.opponent_mode_combo.addItems([
            "使用 FP2 排位 (自動)",
            "使用 Q 排位 (自動)",
            "手動選擇車手"
        ])
        self.opponent_mode_combo.setCurrentIndex(0)
        self.opponent_mode_combo.currentIndexChanged.connect(self._on_opponent_mode_changed)
        mode_layout.addWidget(self.opponent_mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Manual driver selection widget (initially hidden)
        self.manual_driver_widget = QWidget()
        manual_layout = QFormLayout(self.manual_driver_widget)
        manual_layout.setContentsMargins(10, 5, 0, 0)
        
        # Selected driver to simulate
        self.primary_opponent_combo = QComboBox()
        self.primary_opponent_combo.setToolTip("選擇要模擬的車手，或點擊 FP2→Q 表格自動套用")
        manual_layout.addRow("模擬車手:", self.primary_opponent_combo)
        
        # Auto-apply checkbox
        self.auto_apply_fp2_checkbox = QCheckBox("自動使用 FP2→Q 選擇的車手")
        self.auto_apply_fp2_checkbox.setChecked(True)
        self.auto_apply_fp2_checkbox.setToolTip("勾選後，點擊 FP2→Q 表格時會自動套用該車手和排位")
        manual_layout.addRow("", self.auto_apply_fp2_checkbox)
        
        # Starting position for simulation
        self.sim_start_pos_spin = QSpinBox()
        self.sim_start_pos_spin.setRange(1, 20)
        self.sim_start_pos_spin.setValue(1)
        self.sim_start_pos_spin.setSuffix(" 位")
        self.sim_start_pos_spin.setToolTip("模擬車手的起始發車位置")
        manual_layout.addRow("起始位置:", self.sim_start_pos_spin)
        
        self.manual_driver_widget.setVisible(False)
        layout.addWidget(self.manual_driver_widget)
        
        # FP2 data status (must be created before _update_driver_list)
        self.fp2_status_label = QLabel("⚠️ 尚未載入 FP2 數據")
        self.fp2_status_label.setStyleSheet(
            "padding: 4px; background-color: #FFEBEE; "
            "border-radius: 3px; color: #C62828; font-size: 9px;"
        )
        layout.addWidget(self.fp2_status_label)
        
        # Now populate driver list (will call _update_fp2_status)
        self._update_driver_list()
        
        return group
    
    def _update_driver_list(self):
        """Update driver list from default 2025 grid."""
        default_drivers = [
            "VER", "NOR", "LEC", "SAI", "PIA", "RUS", "HAM", "PER",
            "ALO", "STR", "TSU", "HUL", "GAS", "ALB", "OCO", "MAG",
            "BOT", "ZHO", "SAR", "BEA"
        ]
        self.primary_opponent_combo.clear()
        self.primary_opponent_combo.addItems(default_drivers)
        # Connect change signal to update status
        self.primary_opponent_combo.currentTextChanged.connect(self._update_fp2_status)
        # Initial status update
        self._update_fp2_status()
    
    def _on_opponent_mode_changed(self, index: int):
        """Handle opponent mode change."""
        # Show manual selection only for mode index 2
        self.manual_driver_widget.setVisible(index == 2)
        self._update_fp2_status()
    
    def _update_fp2_status(self, has_q_data: bool = None):
        """
        Update FP2 data status label.
        
        Args:
            has_q_data: Whether actual Q results are available (optional)
        """
        mode = self.opponent_mode_combo.currentIndex()
        
        # Store Q data availability for later use
        if has_q_data is not None:
            self._has_q_data = has_q_data
        
        actual_q_available = getattr(self, '_has_q_data', False)
        
        if mode == 0:  # FP2 mode
            selected_driver = self.primary_opponent_combo.currentText()
            self.fp2_status_label.setText(f"✅ 已選擇: {selected_driver} (基於 FP2 排位)")
            self.fp2_status_label.setStyleSheet(
                "padding: 4px; background-color: #E8F5E9; "
                "border-radius: 3px; color: #2E7D32; font-size: 10px;"
            )
        elif mode == 1:  # Q mode
            if actual_q_available:
                self.fp2_status_label.setText("✅ 使用 Q 排位數據 (實際排位)")
                self.fp2_status_label.setStyleSheet(
                    "padding: 4px; background-color: #E3F2FD; "
                    "border-radius: 3px; color: #1565C0; font-size: 10px;"
                )
            else:
                self.fp2_status_label.setText("⚠️ 無實際 Q 數據 (將使用 FP2 預測)")
                self.fp2_status_label.setStyleSheet(
                    "padding: 4px; background-color: #FFF3E0; "
                    "border-radius: 3px; color: #E65100; font-size: 10px;"
                )
        else:  # Manual mode
            selected_driver = self.primary_opponent_combo.currentText()
            self.fp2_status_label.setText(f"✅ 手動選擇: {selected_driver}")
            self.fp2_status_label.setStyleSheet(
                "padding: 4px; background-color: #FFF9C4; "
                "border-radius: 3px; color: #F57F17; font-size: 10px;"
            )
    
    def _create_race_conditions_section(self) -> QGroupBox:
        """Create race conditions section with SC scenario settings."""
        group = QGroupBox("比賽場景設定")
        layout = QVBoxLayout(group)
        
        # SC Event Injector (moved from below)
        self.sc_injector = SCEventInjectorWidget()
        layout.addWidget(self.sc_injector)
        
        # Placeholder widgets for backward compatibility
        # These are now handled by Monte Carlo simulation
        self.first_lap_check = QCheckBox()
        self.first_lap_check.setVisible(False)
        self.first_lap_loss_spin = QDoubleSpinBox()
        self.first_lap_loss_spin.setValue(5.0)
        self.first_lap_loss_spin.setVisible(False)
        self.traffic_check = QCheckBox()
        self.traffic_check.setVisible(False)
        self.traffic_widget = QWidget()
        self.traffic_widget.setVisible(False)
        self.start_position_spin = QSpinBox()
        self.start_position_spin.setValue(10)
        self.start_position_spin.setVisible(False)
        self.traffic_loss_spin = QDoubleSpinBox()
        self.traffic_loss_spin.setValue(0.15)
        self.traffic_loss_spin.setVisible(False)
        self.traffic_decay_spin = QDoubleSpinBox()
        self.traffic_decay_spin.setValue(0.05)
        self.traffic_decay_spin.setDecimals(2)
        self.traffic_decay_spin.setSuffix(" /圈")
        self.traffic_decay_spin.setToolTip("交通影響每圈衰減的比例")
        self.traffic_decay_spin.setVisible(False)
        
        return group
    
    def _create_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator
    
    def _on_pit_congestion_toggled(self, enabled: bool):
        """Handle pit lane congestion checkbox toggle."""
        self.pit_congestion_spin.setEnabled(enabled)
    
    def _create_constraints_section(self) -> QGroupBox:
        """Create strategy constraints section."""
        group = QGroupBox("策略約束")
        layout = QVBoxLayout(group)
        
        # Compound availability
        compound_layout = QHBoxLayout()
        compound_layout.addWidget(QLabel("可用:"))
        
        self.allow_soft_check = QCheckBox("SOFT")
        self.allow_soft_check.setChecked(True)
        compound_layout.addWidget(self.allow_soft_check)
        
        self.allow_medium_check = QCheckBox("MEDIUM")
        self.allow_medium_check.setChecked(True)
        compound_layout.addWidget(self.allow_medium_check)
        
        self.allow_hard_check = QCheckBox("HARD")
        self.allow_hard_check.setChecked(True)
        compound_layout.addWidget(self.allow_hard_check)
        
        layout.addLayout(compound_layout)
        
        # Mandatory compounds
        mandatory_layout = QHBoxLayout()
        mandatory_layout.addWidget(QLabel("必用:"))
        
        self.must_soft_check = QCheckBox("S")
        mandatory_layout.addWidget(self.must_soft_check)
        
        self.must_medium_check = QCheckBox("M")
        mandatory_layout.addWidget(self.must_medium_check)
        
        self.must_hard_check = QCheckBox("H")
        mandatory_layout.addWidget(self.must_hard_check)
        
        layout.addLayout(mandatory_layout)
        
        # Stops
        stops_form = QFormLayout()
        
        stops_layout = QHBoxLayout()
        self.min_stops_spin = QSpinBox()
        self.min_stops_spin.setRange(1, 4)
        self.min_stops_spin.setValue(1)
        stops_layout.addWidget(self.min_stops_spin)
        
        stops_layout.addWidget(QLabel("至"))
        
        self.max_stops_spin = QSpinBox()
        self.max_stops_spin.setRange(1, 4)
        self.max_stops_spin.setValue(2)
        stops_layout.addWidget(self.max_stops_spin)
        
        stops_form.addRow("停站數:", stops_layout)
        
        # Stint length
        stint_layout = QHBoxLayout()
        self.min_stint_spin = QSpinBox()
        self.min_stint_spin.setRange(3, 20)
        self.min_stint_spin.setValue(5)
        stint_layout.addWidget(self.min_stint_spin)
        
        stint_layout.addWidget(QLabel("至"))
        
        self.max_stint_spin = QSpinBox()
        self.max_stint_spin.setRange(20, 60)
        self.max_stint_spin.setValue(45)
        stint_layout.addWidget(self.max_stint_spin)
        
        stops_form.addRow("單節圈數:", stint_layout)
        
        layout.addLayout(stops_form)
        
        return group
    
    def _create_monte_carlo_section(self) -> QGroupBox:
        """Create Monte Carlo settings section."""
        group = QGroupBox("蒙地卡羅模擬")
        layout = QVBoxLayout(group)
        
        # Enable checkbox
        self.mc_enable_check = QCheckBox("啟用蒙地卡羅分析")
        self.mc_enable_check.setChecked(True)
        self.mc_enable_check.toggled.connect(self._on_mc_toggled)
        layout.addWidget(self.mc_enable_check)
        
        # Settings widget
        self.mc_settings_widget = QWidget()
        mc_form = QFormLayout(self.mc_settings_widget)
        mc_form.setContentsMargins(0, 10, 0, 0)
        
        # ✅ 分離參數：單車手策略比較 vs 20車手競爭
        # 策略比較迭代次數（較少，快速測試）
        self.strategy_iterations_spin = QSpinBox()
        self.strategy_iterations_spin.setRange(50, 5000)
        self.strategy_iterations_spin.setValue(100)
        self.strategy_iterations_spin.setSingleStep(50)
        self.strategy_iterations_spin.setToolTip("單車手模式：比較不同策略的時間差異（建議 100-500 次）")
        mc_form.addRow("策略比較次數:", self.strategy_iterations_spin)
        
        # 20車手競爭迭代次數（較多，精確統計）
        self.competitive_iterations_spin = QSpinBox()
        self.competitive_iterations_spin.setRange(100, 10000)
        self.competitive_iterations_spin.setValue(1000)
        self.competitive_iterations_spin.setSingleStep(100)
        self.competitive_iterations_spin.setToolTip("競爭模式：20車手位置統計（建議 1000+ 次以獲得準確的位置機率）")
        mc_form.addRow("競爭模擬次數:", self.competitive_iterations_spin)
        
        # 保留舊參數以向後兼容（指向策略比較）
        self.mc_iterations_spin = self.strategy_iterations_spin
        
        # SC probability
        self.sc_prob_spin = QDoubleSpinBox()
        self.sc_prob_spin.setRange(0.0, 10.0)
        self.sc_prob_spin.setValue(1.5)
        self.sc_prob_spin.setDecimals(1)
        self.sc_prob_spin.setSuffix(" %/圈")
        mc_form.addRow("SC 機率:", self.sc_prob_spin)
        
        # VSC probability
        self.vsc_prob_spin = QDoubleSpinBox()
        self.vsc_prob_spin.setRange(0.0, 10.0)
        self.vsc_prob_spin.setValue(2.0)
        self.vsc_prob_spin.setDecimals(1)
        self.vsc_prob_spin.setSuffix(" %/圈")
        mc_form.addRow("VSC 機率:", self.vsc_prob_spin)
        
        layout.addWidget(self.mc_settings_widget)
        
        return group
    
    def set_track_list(self, tracks: List[str]):
        """Set available tracks in combo box."""
        self._track_list = tracks
        self.track_combo.clear()
        self.track_combo.addItems(tracks)
        
        # Set default to "Yas Marina" if available
        yas_marina_idx = self.track_combo.findText("Yas Marina")
        if yas_marina_idx >= 0:
            self.track_combo.setCurrentIndex(yas_marina_idx)
    
    def update_track_parameters(self, race_laps: int, base_lap_time: float,
                                  pit_loss_green: float = None, pit_loss_sc: float = None,
                                  deg_soft: float = None, deg_medium: float = None, 
                                  deg_hard: float = None,
                                  fuel_per_lap: float = None, fuel_effect: float = None,
                                  start_fuel: float = None,
                                  traffic_decay_rate: float = None,
                                  traffic_loss_per_position: float = None,
                                  first_lap_loss: float = None):
        """
        Update track-specific parameters when track selection changes.
        
        Args:
            race_laps: Number of laps in the race
            base_lap_time: Base lap time in seconds
            pit_loss_green: Pit loss time under green flag (optional)
            pit_loss_sc: Pit loss time under safety car (optional)
            deg_soft: Soft tire degradation rate (optional)
            deg_medium: Medium tire degradation rate (optional)
            deg_hard: Hard tire degradation rate (optional)
            fuel_per_lap: Fuel consumption per lap (optional)
            fuel_effect: Fuel effect coefficient (optional)
            start_fuel: Starting fuel load (optional)
            traffic_decay_rate: Traffic effect decay per lap (optional)
            traffic_loss_per_position: Seconds lost per position behind (optional)
            first_lap_loss: First lap additional time loss (optional)
        """
        # Update race parameters
        self.laps_spin.setValue(race_laps)
        self.base_time_spin.setValue(base_lap_time)
        
        # Update pit loss if provided
        if pit_loss_green is not None:
            self.pit_green_spin.setValue(pit_loss_green)
        if pit_loss_sc is not None:
            self.pit_sc_spin.setValue(pit_loss_sc)
        
        # Update degradation if provided and source is "track default"
        if self.deg_source_combo.currentText() == '賽道預設值':
            if deg_soft is not None:
                self.soft_deg_spin.setValue(deg_soft)
            if deg_medium is not None:
                self.medium_deg_spin.setValue(deg_medium)
            if deg_hard is not None:
                self.hard_deg_spin.setValue(deg_hard)
        
        # Update fuel parameters if provided
        if fuel_per_lap is not None:
            self.fuel_per_lap_spin.setValue(fuel_per_lap)
        if fuel_effect is not None:
            self.fuel_effect_spin.setValue(fuel_effect)
        if start_fuel is not None:
            self.start_fuel_spin.setValue(start_fuel)
        
        # Update traffic parameters if provided (from track features)
        if traffic_decay_rate is not None:
            self.traffic_decay_spin.setValue(traffic_decay_rate)
        if traffic_loss_per_position is not None:
            self.traffic_loss_spin.setValue(traffic_loss_per_position)
        if first_lap_loss is not None:
            self.first_lap_loss_spin.setValue(first_lap_loss)
    
    def _on_track_changed(self, track: str):
        """Handle track selection change."""
        self.track_changed.emit(track)
        # Note: Actual parameter update is handled by main_window via signal
    
    def _on_deg_source_changed(self, source: str):
        """Handle degradation source change."""
        self.deg_manual_widget.setEnabled(source == '手動輸入')
        self.deg_source_changed.emit(source)
    
    def _on_longrun_settings_clicked(self):
        """Handle Long Run settings button click."""
        self.longrun_settings_requested.emit()
    
    def set_degradation(self, compound: str, value: float):
        """
        Set degradation value for a specific compound.
        
        Args:
            compound: 'soft', 'medium', or 'hard'
            value: Degradation rate value (absolute value will be used)
        """
        # Use absolute value - degradation should always be positive in strategy sim
        abs_value = abs(value) if value != 0 else 0.0
        
        # Clamp to valid range (0.001 to 0.50)
        clamped_value = max(0.001, min(0.50, abs_value))
        
        compound_lower = compound.lower()
        if compound_lower == 'soft':
            self.soft_deg_spin.setValue(clamped_value)
        elif compound_lower == 'medium':
            self.medium_deg_spin.setValue(clamped_value)
        elif compound_lower == 'hard':
            self.hard_deg_spin.setValue(clamped_value)
        else:
            print(f"[INPUT_PANEL] Unknown compound: {compound}")
        
        print(f"[INPUT_PANEL] Set {compound}: original={value:.4f}, clamped={clamped_value:.4f}")
    
    def set_base_lap_time(self, value: float):
        """
        Set base lap time value.
        
        Args:
            value: Base lap time in seconds
        """
        self.base_time_spin.setValue(value)
    
    def get_year(self) -> int:
        """Get the currently selected year."""
        return int(self.year_combo.currentText())
    
    def get_track(self) -> str:
        """Get the currently selected track."""
        return self.track_combo.currentText()
    
    def _on_mc_toggled(self, enabled: bool):
        """Handle Monte Carlo enable/disable."""
        self.mc_settings_widget.setEnabled(enabled)
    
    def _on_run_clicked(self):
        """Handle run button click."""
        params = self.get_parameters()
        self.run_simulation.emit(params)
    
    def get_parameters(self) -> dict:
        """Get all current parameters as a dictionary."""
        return {
            # Race
            'year': int(self.year_combo.currentText()),
            'track': self.track_combo.currentText(),
            'race_laps': self.laps_spin.value(),
            'base_lap_time': self.base_time_spin.value(),
            
            # Degradation
            'soft_deg': self.soft_deg_spin.value(),
            'medium_deg': self.medium_deg_spin.value(),
            'hard_deg': self.hard_deg_spin.value(),
            'soft_delta': self.soft_delta_spin.value(),
            'hard_delta': self.hard_delta_spin.value(),
            
            # Fuel
            'start_fuel': self.start_fuel_spin.value(),
            'fuel_per_lap': self.fuel_per_lap_spin.value(),
            'fuel_effect': self.fuel_effect_spin.value(),
            'pit_loss_green': self.pit_green_spin.value(),
            'pit_loss_sc': self.pit_sc_spin.value(),
            
            # Pit lane congestion (Q17)
            'enable_pit_congestion': self.pit_congestion_check.isChecked(),
            'pit_congestion_penalty': self.pit_congestion_spin.value(),
            
            # Race conditions
            'enable_first_lap_loss': self.first_lap_check.isChecked(),
            'first_lap_loss': self.first_lap_loss_spin.value(),
            'enable_traffic_simulation': self.traffic_check.isChecked(),
            'starting_position': self.start_position_spin.value(),
            'traffic_loss_per_position': self.traffic_loss_spin.value(),
            'traffic_decay_rate': self.traffic_decay_spin.value(),
            
            # SC Events (from SCEventInjectorWidget)
            'sc_mode': self.sc_injector.get_mode(),
            'sc_events': self.sc_injector.get_events(),
            
            # Driver Selection (for simulation)
            'driver_selection_mode': self.opponent_mode_combo.currentIndex(),  # 0=FP2, 1=Q, 2=Manual
            'selected_driver': self.primary_opponent_combo.currentText() if hasattr(self, 'primary_opponent_combo') else 'VER',
            'driver_start_position': self.sim_start_pos_spin.value() if hasattr(self, 'sim_start_pos_spin') else 1,
            
            # Constraints
            'allow_soft': self.allow_soft_check.isChecked(),
            'allow_medium': self.allow_medium_check.isChecked(),
            'allow_hard': self.allow_hard_check.isChecked(),
            'must_use_soft': self.must_soft_check.isChecked(),
            'must_use_medium': self.must_medium_check.isChecked(),
            'must_use_hard': self.must_hard_check.isChecked(),
            'min_stops': self.min_stops_spin.value(),
            'max_stops': self.max_stops_spin.value(),
            'min_stint': self.min_stint_spin.value(),
            'max_stint': self.max_stint_spin.value(),
            
            # Monte Carlo
            'run_monte_carlo': self.mc_enable_check.isChecked(),
            'mc_iterations': self.mc_iterations_spin.value(),  # 保留向後兼容
            'strategy_iterations': self.strategy_iterations_spin.value(),  # ✅ 策略比較迭代次數
            'competitive_iterations': self.competitive_iterations_spin.value(),  # ✅ 競爭模擬迭代次數
            'sc_prob': self.sc_prob_spin.value(),
            'vsc_prob': self.vsc_prob_spin.value(),
        }
    
    def set_starting_position(self, position: int):
        """
        Set starting grid position.
        
        Args:
            position: Grid position (1-20)
        """
        self.start_position_spin.setValue(max(1, min(20, position)))
