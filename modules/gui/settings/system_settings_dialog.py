"""System Settings dialog for centralizing GUI configuration."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,  # 新增：用於整數設定
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.gui_i18n import tr
from core.gui_settings_manager import GuiSettingsManager, gui_settings_manager


class SystemSettingsDialog(QDialog):
    """Centralized configuration dialog for GUI modules."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        settings_manager: Optional[GuiSettingsManager] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("system_settings_title", "System Settings"))
        self.setModal(True)
        self.resize(520, 360)

        self._settings_manager = settings_manager or gui_settings_manager

        self._setup_ui()
        self._load_current_settings()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.North)
        main_layout.addWidget(self.tab_widget)

        # Box plot settings tab
        boxplot_tab = QWidget()
        boxplot_layout = QVBoxLayout(boxplot_tab)
        boxplot_layout.setContentsMargins(10, 10, 10, 10)
        boxplot_layout.setSpacing(12)

        boxplot_group = QGroupBox(tr("boxplot_settings_group", "Box Plot Analysis"))
        group_layout = QFormLayout(boxplot_group)
        group_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        group_layout.setHorizontalSpacing(18)
        group_layout.setVerticalSpacing(10)

        self.filter_pit_checkbox = QCheckBox(tr("boxplot_filter_pit", "Filter pit laps"))
        group_layout.addRow(self.filter_pit_checkbox)

        self.filter_outliers_checkbox = QCheckBox(
            tr("boxplot_filter_outliers", "Filter statistical outliers (IQR)")
        )
        group_layout.addRow(self.filter_outliers_checkbox)

        self.filter_yellow_flags_checkbox = QCheckBox(
            tr("boxplot_filter_yellow_flags", "Filter yellow flag laps")
        )
        group_layout.addRow(self.filter_yellow_flags_checkbox)

        self.filter_red_flags_checkbox = QCheckBox(
            tr("boxplot_filter_red_flags", "Filter red flag laps")
        )
        group_layout.addRow(self.filter_red_flags_checkbox)

        self.filter_first_laps_checkbox = QCheckBox(
            tr("boxplot_filter_first_laps", "Filter first 2 laps (Lap 1 & 2)")
        )
        group_layout.addRow(self.filter_first_laps_checkbox)

        self.outlier_threshold_spinbox = QDoubleSpinBox()
        self.outlier_threshold_spinbox.setDecimals(1)
        self.outlier_threshold_spinbox.setRange(0.5, 3.0)
        self.outlier_threshold_spinbox.setSingleStep(0.1)
        self.outlier_threshold_spinbox.setSuffix(" × IQR")
        self.outlier_threshold_spinbox.setToolTip(
            tr(
                "boxplot_outlier_threshold_hint",
                "Interquartile Range multiplier for outlier detection",
            )
        )
        group_layout.addRow(
            QLabel(tr("boxplot_outlier_threshold", "Outlier threshold")),
            self.outlier_threshold_spinbox,
        )

        boxplot_layout.addWidget(boxplot_group)

        info_label = QLabel(
            tr(
                "boxplot_settings_info",
                "Settings apply to both lap time and throttle box plot modules.",
            )
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; font-size: 11px;")
        boxplot_layout.addWidget(info_label)
        boxplot_layout.addStretch(1)

        # Helper actions
        helper_layout = QHBoxLayout()
        helper_layout.setContentsMargins(0, 0, 0, 0)
        helper_layout.setSpacing(8)

        self.reset_defaults_button = QPushButton(tr("reset_defaults", "Reset Defaults"))
        self.reset_defaults_button.clicked.connect(self._reset_defaults)
        helper_layout.addWidget(self.reset_defaults_button)
        helper_layout.addStretch(1)

        boxplot_layout.addLayout(helper_layout)

        self.tab_widget.addTab(boxplot_tab, tr("boxplot_settings_tab", "Box Plot Analysis"))

        # ========== 新增：Throttle Line Chart 分頁 ==========
        throttle_tab = QWidget()
        throttle_layout = QVBoxLayout(throttle_tab)
        throttle_layout.setContentsMargins(10, 10, 10, 10)
        throttle_layout.setSpacing(12)

        # 顯示選項群組
        display_group = QGroupBox(tr("throttle_display_group", "Display Options"))
        display_layout = QFormLayout(display_group)
        display_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        display_layout.setHorizontalSpacing(18)
        display_layout.setVerticalSpacing(10)

        self.throttle_show_full_duration_checkbox = QCheckBox(
            tr("throttle_show_full_duration", "Show Full Throttle Duration (s)")
        )
        display_layout.addRow(self.throttle_show_full_duration_checkbox)

        self.throttle_show_ratio_checkbox = QCheckBox(
            tr("throttle_show_ratio", "Show Full Throttle %")
        )
        display_layout.addRow(self.throttle_show_ratio_checkbox)

        self.throttle_show_average_checkbox = QCheckBox(
            tr("throttle_show_average", "Show Average Throttle %")
        )
        display_layout.addRow(self.throttle_show_average_checkbox)

        self.throttle_show_delta_checkbox = QCheckBox(
            tr("throttle_show_delta", "Show Lap Time Δ vs Best")
        )
        display_layout.addRow(self.throttle_show_delta_checkbox)

        throttle_layout.addWidget(display_group)

        # 圈速分析群組
        laptime_group = QGroupBox(tr("throttle_laptime_group", "Lap Time Analysis"))
        laptime_layout = QFormLayout(laptime_group)
        laptime_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        laptime_layout.setHorizontalSpacing(18)
        laptime_layout.setVerticalSpacing(10)

        self.throttle_rolling_average_checkbox = QCheckBox(
            tr("throttle_rolling_average", "Enable Rolling Average")
        )
        laptime_layout.addRow(self.throttle_rolling_average_checkbox)

        self.throttle_rolling_window_spinbox = QSpinBox()
        self.throttle_rolling_window_spinbox.setRange(2, 12)
        self.throttle_rolling_window_spinbox.setSingleStep(1)
        self.throttle_rolling_window_spinbox.setSuffix(" laps")
        self.throttle_rolling_window_spinbox.setToolTip(
            tr("throttle_rolling_window_hint", "Number of laps for moving average calculation")
        )
        laptime_layout.addRow(
            QLabel(tr("throttle_rolling_window", "Rolling Window")),
            self.throttle_rolling_window_spinbox,
        )

        throttle_layout.addWidget(laptime_group)

        # 門檻值群組
        threshold_group = QGroupBox(tr("throttle_threshold_group", "Threshold Highlighting"))
        threshold_layout = QFormLayout(threshold_group)
        threshold_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        threshold_layout.setHorizontalSpacing(18)
        threshold_layout.setVerticalSpacing(10)

        self.throttle_highlight_threshold_checkbox = QCheckBox(
            tr("throttle_highlight_threshold", "Highlight laps ≥ threshold")
        )
        threshold_layout.addRow(self.throttle_highlight_threshold_checkbox)

        self.throttle_threshold_percent_spinbox = QSpinBox()
        self.throttle_threshold_percent_spinbox.setRange(50, 100)
        self.throttle_threshold_percent_spinbox.setSingleStep(5)
        self.throttle_threshold_percent_spinbox.setSuffix(" %")
        self.throttle_threshold_percent_spinbox.setToolTip(
            tr("throttle_threshold_percent_hint", "Full Throttle % threshold for highlighting")
        )
        threshold_layout.addRow(
            QLabel(tr("throttle_threshold_percent", "Threshold Percent")),
            self.throttle_threshold_percent_spinbox,
        )

        throttle_layout.addWidget(threshold_group)

        # 說明文字
        throttle_info_label = QLabel(
            tr(
                "throttle_settings_info",
                "Default settings for Throttle Line Chart module. Driver selection remains in the module window.",
            )
        )
        throttle_info_label.setWordWrap(True)
        throttle_info_label.setStyleSheet("color: #666666; font-size: 11px;")
        throttle_layout.addWidget(throttle_info_label)
        throttle_layout.addStretch(1)

        # 重置預設值按鈕
        throttle_helper_layout = QHBoxLayout()
        throttle_helper_layout.setContentsMargins(0, 0, 0, 0)
        throttle_helper_layout.setSpacing(8)

        self.throttle_reset_defaults_button = QPushButton(tr("reset_defaults", "Reset Defaults"))
        self.throttle_reset_defaults_button.clicked.connect(self._reset_throttle_defaults)
        throttle_helper_layout.addWidget(self.throttle_reset_defaults_button)
        throttle_helper_layout.addStretch(1)

        throttle_layout.addLayout(throttle_helper_layout)

        self.tab_widget.addTab(throttle_tab, tr("throttle_settings_tab", "Throttle Line Chart"))
        # ========== Throttle Line Chart 分頁結束 ==========

        # ========== 新增：Straight Speed Analysis 分頁 ==========
        speed_analysis_tab = QWidget()
        speed_analysis_layout = QVBoxLayout(speed_analysis_tab)
        speed_analysis_layout.setContentsMargins(10, 10, 10, 10)
        speed_analysis_layout.setSpacing(12)

        # All Drivers Speed 群組
        speed_group = QGroupBox(tr("speed_display_group", "All Drivers Speed"))
        speed_layout = QFormLayout(speed_group)
        speed_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        speed_layout.setHorizontalSpacing(18)
        speed_layout.setVerticalSpacing(10)

        self.speed_show_max_speed_checkbox = QCheckBox(
            tr("speed_show_max_speed", "Show Max Speed (km/h)")
        )
        speed_layout.addRow(self.speed_show_max_speed_checkbox)

        self.speed_show_start_speed_checkbox = QCheckBox(
            tr("speed_show_start_speed", "Show Start Speed (km/h)")
        )
        speed_layout.addRow(self.speed_show_start_speed_checkbox)

        self.speed_show_max_speed_time_checkbox = QCheckBox(
            tr("speed_show_max_speed_time", "Show Max Speed Time (s)")
        )
        speed_layout.addRow(self.speed_show_max_speed_time_checkbox)

        self.speed_show_performance_bar_checkbox = QCheckBox(
            tr("speed_show_performance_bar", "Show Performance Bar")
        )
        speed_layout.addRow(self.speed_show_performance_bar_checkbox)

        speed_analysis_layout.addWidget(speed_group)

        # All Drivers Brake 群組
        brake_group = QGroupBox(tr("brake_display_group", "All Drivers Brake"))
        brake_layout = QFormLayout(brake_group)
        brake_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        brake_layout.setHorizontalSpacing(18)
        brake_layout.setVerticalSpacing(10)

        self.brake_show_max_decel_checkbox = QCheckBox(
            tr("brake_show_max_decel", "Show Max Decel (G)")
        )
        brake_layout.addRow(self.brake_show_max_decel_checkbox)

        self.brake_show_start_speed_checkbox = QCheckBox(
            tr("brake_show_start_speed", "Show Start Speed (km/h)")
        )
        brake_layout.addRow(self.brake_show_start_speed_checkbox)

        self.brake_show_performance_bar_checkbox = QCheckBox(
            tr("brake_show_performance_bar", "Show Performance Bar")
        )
        brake_layout.addRow(self.brake_show_performance_bar_checkbox)

        speed_analysis_layout.addWidget(brake_group)

        # 說明文字
        speed_analysis_info_label = QLabel(
            tr(
                "speed_analysis_settings_info",
                "Driver, Team, Accel Time, Avg Accel, Brake Time, and Avg Decel columns are always visible.",
            )
        )
        speed_analysis_info_label.setWordWrap(True)
        speed_analysis_info_label.setStyleSheet("color: #666666; font-size: 11px;")
        speed_analysis_layout.addWidget(speed_analysis_info_label)
        speed_analysis_layout.addStretch(1)

        # 重置預設值按鈕
        speed_analysis_helper_layout = QHBoxLayout()
        speed_analysis_helper_layout.setContentsMargins(0, 0, 0, 0)
        speed_analysis_helper_layout.setSpacing(8)

        self.speed_analysis_reset_defaults_button = QPushButton(tr("reset_defaults", "Reset Defaults"))
        self.speed_analysis_reset_defaults_button.clicked.connect(self._reset_speed_analysis_defaults)
        speed_analysis_helper_layout.addWidget(self.speed_analysis_reset_defaults_button)
        speed_analysis_helper_layout.addStretch(1)

        speed_analysis_layout.addLayout(speed_analysis_helper_layout)

        self.tab_widget.addTab(speed_analysis_tab, tr("speed_analysis_settings_tab", "Straight Speed Analysis"))
        # ========== Straight Speed Analysis 分頁結束 ==========

        # ========== 新增：Logger 設定分頁 ==========
        logger_tab = QWidget()
        logger_layout = QVBoxLayout(logger_tab)
        logger_layout.setContentsMargins(10, 10, 10, 10)
        logger_layout.setSpacing(12)

        # Logger 啟用/禁用群組
        logger_group = QGroupBox(tr("logger_settings_group", "Logger Configuration"))
        logger_group_layout = QFormLayout(logger_group)
        logger_group_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        logger_group_layout.setHorizontalSpacing(18)
        logger_group_layout.setVerticalSpacing(10)

        self.logger_enabled_checkbox = QCheckBox(
            tr("logger_enabled", "Enable Logging System")
        )
        self.logger_enabled_checkbox.setToolTip(
            tr("logger_enabled_hint", "Disable logging to improve performance")
        )
        logger_group_layout.addRow(self.logger_enabled_checkbox)

        # 日誌等級選擇
        self.logger_level_combo = QComboBox()
        self.logger_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.logger_level_combo.setToolTip(
            tr("logger_level_hint", "Higher levels = less logging = better performance")
        )
        logger_group_layout.addRow(
            QLabel(tr("logger_level", "Log Level")),
            self.logger_level_combo,
        )

        # 控制台日誌等級
        self.logger_console_level_combo = QComboBox()
        self.logger_console_level_combo.addItems(["NONE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.logger_console_level_combo.setToolTip(
            tr("logger_console_level_hint", "Console output level (NONE = no console output)")
        )
        logger_group_layout.addRow(
            QLabel(tr("logger_console_level", "Console Level")),
            self.logger_console_level_combo,
        )

        # Patch Print 選項
        self.logger_patch_print_checkbox = QCheckBox(
            tr("logger_patch_print", "Redirect print() to Logger")
        )
        self.logger_patch_print_checkbox.setToolTip(
            tr("logger_patch_print_hint", "Route print() calls through the logging system")
        )
        logger_group_layout.addRow(self.logger_patch_print_checkbox)

        logger_layout.addWidget(logger_group)

        # 效能影響說明
        performance_info = QLabel(
            tr(
                "logger_performance_info",
                "<b>Performance Impact:</b><br>"
                "<font color='#FF5555'>• Enabled (INFO/DEBUG): High CPU/Memory usage</font><br>"
                "<font color='#FFAA00'>• Enabled (WARNING/ERROR): Medium usage</font><br>"
                "<font color='#55FF55'>• Disabled: No logging overhead</font><br><br>"
                "<b>Note:</b> Changes require restart to take effect.",
            )
        )
        performance_info.setWordWrap(True)
        performance_info.setStyleSheet("color: #CCCCCC; font-size: 11px; padding: 10px; background-color: #2b2b2b; border-radius: 5px;")
        logger_layout.addWidget(performance_info)

        # 快速操作按鈕
        quick_actions_group = QGroupBox(tr("logger_quick_actions", "Quick Actions"))
        quick_actions_layout = QVBoxLayout(quick_actions_group)

        quick_actions_help = QLabel(
            tr("logger_quick_actions_help", "Common configurations:")
        )
        quick_actions_help.setStyleSheet("color: #888888; font-size: 10px;")
        quick_actions_layout.addWidget(quick_actions_help)

        quick_buttons_layout = QHBoxLayout()

        self.logger_preset_disabled_btn = QPushButton("⚡ Disabled (Best Performance)")
        self.logger_preset_disabled_btn.clicked.connect(self._apply_logger_preset_disabled)
        self.logger_preset_disabled_btn.setToolTip("Disable all logging")
        quick_buttons_layout.addWidget(self.logger_preset_disabled_btn)

        self.logger_preset_error_btn = QPushButton("⚠️ ERROR Only")
        self.logger_preset_error_btn.clicked.connect(self._apply_logger_preset_error)
        self.logger_preset_error_btn.setToolTip("Only log errors (good balance)")
        quick_buttons_layout.addWidget(self.logger_preset_error_btn)

        self.logger_preset_debug_btn = QPushButton("🔍 DEBUG (Full Logging)")
        self.logger_preset_debug_btn.clicked.connect(self._apply_logger_preset_debug)
        self.logger_preset_debug_btn.setToolTip("Enable all logging for debugging")
        quick_buttons_layout.addWidget(self.logger_preset_debug_btn)

        quick_actions_layout.addLayout(quick_buttons_layout)
        logger_layout.addWidget(quick_actions_group)

        logger_layout.addStretch(1)

        self.tab_widget.addTab(logger_tab, tr("logger_settings_tab", "Logger"))
        # ========== Logger 分頁結束 ==========

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    # ------------------------------------------------------------------
    # Settings handling
    # ------------------------------------------------------------------
    def _load_current_settings(self) -> None:
        settings = self._settings_manager.get_boxplot_settings()
        self.filter_pit_checkbox.setChecked(settings.get("filter_pit_laps", True))
        self.filter_outliers_checkbox.setChecked(settings.get("filter_outliers", True))
        self.filter_yellow_flags_checkbox.setChecked(settings.get("filter_yellow_flags", True))
        self.filter_red_flags_checkbox.setChecked(settings.get("filter_red_flags", True))
        self.filter_first_laps_checkbox.setChecked(settings.get("filter_first_laps", True))
        self.outlier_threshold_spinbox.setValue(settings.get("outlier_threshold", 1.5))

        # 載入 Throttle Line Chart 設定
        throttle_settings = self._settings_manager.get_throttle_line_chart_settings()
        self.throttle_show_full_duration_checkbox.setChecked(
            throttle_settings.get("show_full_duration", False)
        )
        self.throttle_show_ratio_checkbox.setChecked(throttle_settings.get("show_ratio", True))
        self.throttle_show_average_checkbox.setChecked(throttle_settings.get("show_average", True))
        self.throttle_show_delta_checkbox.setChecked(throttle_settings.get("show_delta", False))
        self.throttle_rolling_average_checkbox.setChecked(
            throttle_settings.get("rolling_average", False)
        )
        self.throttle_rolling_window_spinbox.setValue(
            int(throttle_settings.get("rolling_window", 3))
        )
        self.throttle_highlight_threshold_checkbox.setChecked(
            throttle_settings.get("highlight_threshold", True)
        )
        self.throttle_threshold_percent_spinbox.setValue(
            int(throttle_settings.get("threshold_percent", 90))
        )

        # 載入 Straight Speed Analysis 設定
        speed_analysis_settings = self._settings_manager.get_straight_speed_analysis_settings()
        self.speed_show_max_speed_checkbox.setChecked(
            speed_analysis_settings.get("speed_show_max_speed", True)  # ✅ 預設顯示最高速度
        )
        self.speed_show_start_speed_checkbox.setChecked(
            speed_analysis_settings.get("speed_show_start_speed", False)
        )
        self.speed_show_max_speed_time_checkbox.setChecked(
            speed_analysis_settings.get("speed_show_max_speed_time", False)
        )
        self.speed_show_performance_bar_checkbox.setChecked(
            speed_analysis_settings.get("speed_show_performance_bar", True)
        )
        self.brake_show_max_decel_checkbox.setChecked(
            speed_analysis_settings.get("brake_show_max_decel", False)
        )
        self.brake_show_start_speed_checkbox.setChecked(
            speed_analysis_settings.get("brake_show_start_speed", False)
        )
        self.brake_show_performance_bar_checkbox.setChecked(
            speed_analysis_settings.get("brake_show_performance_bar", True)
        )

        # ✅ 載入 Logger 設定
        logger_settings = self._load_logger_config()
        self.logger_enabled_checkbox.setChecked(logger_settings.get("enabled", True))
        
        level = logger_settings.get("level", "INFO")
        level_index = self.logger_level_combo.findText(level)
        if level_index >= 0:
            self.logger_level_combo.setCurrentIndex(level_index)
        
        console_level = logger_settings.get("console_level", None)
        if console_level is None:
            console_level = "NONE"
        console_level_index = self.logger_console_level_combo.findText(console_level)
        if console_level_index >= 0:
            self.logger_console_level_combo.setCurrentIndex(console_level_index)
        
        self.logger_patch_print_checkbox.setChecked(logger_settings.get("patch_print", True))

    def _reset_defaults(self) -> None:
        self.filter_pit_checkbox.setChecked(True)
        self.filter_outliers_checkbox.setChecked(True)
        self.filter_yellow_flags_checkbox.setChecked(True)
        self.filter_red_flags_checkbox.setChecked(True)
        self.filter_first_laps_checkbox.setChecked(True)
        self.outlier_threshold_spinbox.setValue(1.5)

    def _reset_throttle_defaults(self) -> None:
        """重置 Throttle Line Chart 預設值"""
        self.throttle_show_full_duration_checkbox.setChecked(False)
        self.throttle_show_ratio_checkbox.setChecked(True)
        self.throttle_show_average_checkbox.setChecked(True)
        self.throttle_show_delta_checkbox.setChecked(False)
        self.throttle_rolling_average_checkbox.setChecked(False)
        self.throttle_rolling_window_spinbox.setValue(3)
        self.throttle_highlight_threshold_checkbox.setChecked(True)
        self.throttle_threshold_percent_spinbox.setValue(90)

    def _reset_speed_analysis_defaults(self) -> None:
        """重置 Straight Speed Analysis 預設值"""
        self.speed_show_max_speed_checkbox.setChecked(True)  # ✅ 預設顯示最高速度
        self.speed_show_start_speed_checkbox.setChecked(False)
        self.speed_show_max_speed_time_checkbox.setChecked(False)
        self.speed_show_performance_bar_checkbox.setChecked(True)
        self.brake_show_max_decel_checkbox.setChecked(False)
        self.brake_show_start_speed_checkbox.setChecked(False)
        self.brake_show_performance_bar_checkbox.setChecked(True)

    def _load_logger_config(self) -> dict:
        """載入 Logger 設定檔"""
        import json
        from pathlib import Path
        
        try:
            config_file = Path(__file__).parent.parent.parent.parent / "config" / "logging_config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[SETTINGS] Failed to load logger config: {e}")
        
        return {
            "enabled": True,
            "level": "INFO",
            "console_level": None,
            "patch_print": True
        }

    def _save_logger_config(self, config: dict) -> None:
        """儲存 Logger 設定檔"""
        import json
        from pathlib import Path
        
        try:
            config_file = Path(__file__).parent.parent.parent.parent / "config" / "logging_config.json"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[SETTINGS] Failed to save logger config: {e}")

    def _apply_logger_preset_disabled(self) -> None:
        """應用預設：禁用 Logger"""
        self.logger_enabled_checkbox.setChecked(False)
        self.logger_level_combo.setCurrentText("INFO")
        self.logger_console_level_combo.setCurrentText("NONE")
        self.logger_patch_print_checkbox.setChecked(False)

    def _apply_logger_preset_error(self) -> None:
        """應用預設：只記錄錯誤"""
        self.logger_enabled_checkbox.setChecked(True)
        self.logger_level_combo.setCurrentText("ERROR")
        self.logger_console_level_combo.setCurrentText("ERROR")
        self.logger_patch_print_checkbox.setChecked(True)

    def _apply_logger_preset_debug(self) -> None:
        """應用預設：完整除錯"""
        self.logger_enabled_checkbox.setChecked(True)
        self.logger_level_combo.setCurrentText("DEBUG")
        self.logger_console_level_combo.setCurrentText("INFO")
        self.logger_patch_print_checkbox.setChecked(True)

    def _on_accept(self) -> None:
        self._settings_manager.update_boxplot_settings(
            filter_pit_laps=self.filter_pit_checkbox.isChecked(),
            filter_outliers=self.filter_outliers_checkbox.isChecked(),
            filter_yellow_flags=self.filter_yellow_flags_checkbox.isChecked(),
            filter_red_flags=self.filter_red_flags_checkbox.isChecked(),
            filter_first_laps=self.filter_first_laps_checkbox.isChecked(),
            outlier_threshold=float(self.outlier_threshold_spinbox.value()),
        )
        
        # 儲存 Throttle Line Chart 設定
        self._settings_manager.update_throttle_line_chart_settings(
            show_full_duration=self.throttle_show_full_duration_checkbox.isChecked(),
            show_ratio=self.throttle_show_ratio_checkbox.isChecked(),
            show_average=self.throttle_show_average_checkbox.isChecked(),
            show_delta=self.throttle_show_delta_checkbox.isChecked(),
            rolling_average=self.throttle_rolling_average_checkbox.isChecked(),
            rolling_window=int(self.throttle_rolling_window_spinbox.value()),
            highlight_threshold=self.throttle_highlight_threshold_checkbox.isChecked(),
            threshold_percent=float(self.throttle_threshold_percent_spinbox.value()),
        )
        
        # 儲存 Straight Speed Analysis 設定
        self._settings_manager.update_straight_speed_analysis_settings(
            speed_show_max_speed=self.speed_show_max_speed_checkbox.isChecked(),
            speed_show_start_speed=self.speed_show_start_speed_checkbox.isChecked(),
            speed_show_max_speed_time=self.speed_show_max_speed_time_checkbox.isChecked(),
            speed_show_performance_bar=self.speed_show_performance_bar_checkbox.isChecked(),
            brake_show_max_decel=self.brake_show_max_decel_checkbox.isChecked(),
            brake_show_start_speed=self.brake_show_start_speed_checkbox.isChecked(),
            brake_show_performance_bar=self.brake_show_performance_bar_checkbox.isChecked(),
        )
        
        # ✅ 儲存 Logger 設定
        console_level_text = self.logger_console_level_combo.currentText()
        console_level = None if console_level_text == "NONE" else console_level_text
        
        logger_config = {
            "enabled": self.logger_enabled_checkbox.isChecked(),
            "level": self.logger_level_combo.currentText(),
            "console_level": console_level,
            "patch_print": self.logger_patch_print_checkbox.isChecked(),
            "comment": "Logger settings - Changes require restart"
        }
        self._save_logger_config(logger_config)
        
        self.accept()
