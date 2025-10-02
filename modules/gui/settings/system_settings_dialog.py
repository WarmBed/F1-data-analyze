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

        boxplot_group = QGroupBox(tr("boxplot_settings_group", "Lap Time Box Plot"))
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
        self.tab_widget.addTab(boxplot_tab, tr("boxplot_settings_tab", "Lap Time Box Plot"))

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
        self.outlier_threshold_spinbox.setValue(settings.get("outlier_threshold", 1.5))

    def _reset_defaults(self) -> None:
        self.filter_pit_checkbox.setChecked(True)
        self.filter_outliers_checkbox.setChecked(True)
        self.outlier_threshold_spinbox.setValue(1.5)

    def _on_accept(self) -> None:
        self._settings_manager.update_boxplot_settings(
            filter_pit_laps=self.filter_pit_checkbox.isChecked(),
            filter_outliers=self.filter_outliers_checkbox.isChecked(),
            outlier_threshold=float(self.outlier_threshold_spinbox.value()),
        )
        self.accept()
