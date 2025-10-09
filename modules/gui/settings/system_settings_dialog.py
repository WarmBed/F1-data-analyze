"""System Settings dialog for centralizing GUI configuration."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
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

    def _reset_defaults(self) -> None:
        self.filter_pit_checkbox.setChecked(True)
        self.filter_outliers_checkbox.setChecked(True)
        self.filter_yellow_flags_checkbox.setChecked(True)
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

    def _on_accept(self) -> None:
        self._settings_manager.update_boxplot_settings(
            filter_pit_laps=self.filter_pit_checkbox.isChecked(),
            filter_outliers=self.filter_outliers_checkbox.isChecked(),
            filter_yellow_flags=self.filter_yellow_flags_checkbox.isChecked(),
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
        
        self.accept()
