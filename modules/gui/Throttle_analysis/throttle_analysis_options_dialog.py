"""Throttle Analysis options dialog styled after Lap Analysis dialog."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from core.gui_i18n import tr


class ThrottleAnalysisOptionsDialog(QDialog):
    """Dialog replicating the Lap Analysis options UI for throttle modules."""

    TYPE_BOX_PLOT = "box_plot"
    TYPE_LINE_CHART = "line_chart"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("throttle_analysis_options_title", "Throttle Analysis Options"))
        self.setModal(True)
        self.setFixedSize(420, 320)

        font = QFont("Arial", 8)
        self.setFont(font)

        self._apply_stylesheet()
        self.init_ui()

        print("[THROTTLE_DIALOG] ThrottleAnalysisOptionsDialog 已初始化")

    def _apply_stylesheet(self) -> None:
        """Apply the same stylesheet as LapAnalysisOptionsDialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                color: #333333;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
            }
            QLabel {
                color: #333333;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
            }
            QGroupBox {
                color: #333333;
                font-weight: bold;
                font-size: 8pt;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 5px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
                background: #f0f0f0;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 8pt;
                outline: none;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #EEEEEE;
            }
            QListWidget::item:selected {
                background-color: #d1e7dd;
                color: #0f5132;
            }
            QListWidget::item:hover {
                background-color: #E8F5E9;
            }
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 8pt;
                padding: 4px 12px;
                min-height: 18px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)

    def init_ui(self) -> None:
        """Initialize UI layout mirroring the Lap dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel(tr("select_analysis_type", "Please select analysis type"))
        title_label.setStyleSheet("""
            font-size: 8pt;
            color: #333333;
            margin-bottom: 3px;
            font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
        """)
        layout.addWidget(title_label)

        type_group = QGroupBox(tr("analysis_type", "Analysis Type"))
        type_layout = QVBoxLayout(type_group)
        type_layout.setSpacing(5)
        type_layout.setContentsMargins(10, 12, 10, 10)

        self.analysis_list = QListWidget()
        self.analysis_list.setSelectionMode(QListWidget.MultiSelection)
        self.analysis_list.setFixedHeight(80)

        item1 = QListWidgetItem("📦 " + tr("throttle_analysis_option_box_plot", "Throttle Box Plot"))
        item1.setData(Qt.UserRole, self.TYPE_BOX_PLOT)
        self.analysis_list.addItem(item1)

        # ✅ Throttle Line Chart 已實現！移除 "coming soon" 並啟用
        item2 = QListWidgetItem("📈 " + tr("throttle_analysis_option_line_chart", "Throttle Line Chart"))
        item2.setData(Qt.UserRole, self.TYPE_LINE_CHART)
        # 移除禁用標記，現在可以選擇了！
        # item2.setFlags(item2.flags() & ~Qt.ItemIsEnabled)  # ← 已移除
        self.analysis_list.addItem(item2)

        self.analysis_list.setCurrentRow(0)

        type_layout.addWidget(self.analysis_list)

        quick_select_layout = QHBoxLayout()
        quick_select_layout.setSpacing(8)

        select_all_btn = QPushButton(tr("select_all", "Select All"))
        select_all_btn.setFixedHeight(28)
        select_all_btn.clicked.connect(self.select_all)
        quick_select_layout.addWidget(select_all_btn)

        select_none_btn = QPushButton(tr("select_none", "Select None"))
        select_none_btn.setFixedHeight(28)
        select_none_btn.clicked.connect(self.select_none)
        quick_select_layout.addWidget(select_none_btn)

        quick_select_layout.addStretch()
        type_layout.addLayout(quick_select_layout)

        layout.addWidget(type_group)

        desc_label = QLabel(
            "• " + tr("throttle_box_plot_desc", "Throttle Box Plot: Visualizes throttle usage distribution") + "\n"
            "• " + tr("throttle_line_chart_desc", "Throttle Line Chart: Time-series throttle view with dual synchronized charts")
        )
        desc_label.setStyleSheet("""
            color: #777777;
            font-size: 7pt;
            padding: 5px 8px;
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 2px;
            font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()

        ok_btn = QPushButton(tr("ok", "OK"))
        ok_btn.setFixedSize(60, 26)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton(tr("cancel", "Cancel"))
        cancel_btn.setFixedSize(60, 26)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def get_selected_types(self) -> list[str]:
        """Return selected analysis types (defaults to box plot)."""
        selected_types: list[str] = []
        for item in self.analysis_list.selectedItems():
            if item.flags() & Qt.ItemIsEnabled:
                selected_types.append(item.data(Qt.UserRole))

        if not selected_types:
            print("[THROTTLE_DIALOG] 未選擇任何項目，返回預設值: [box_plot]")
            return [self.TYPE_BOX_PLOT]

        print(f"[THROTTLE_DIALOG] 使用者選擇的分析類型: {selected_types}")
        return selected_types

    def select_all(self) -> None:
        """Select all enabled analysis types."""
        print("[THROTTLE_DIALOG] 選擇所有分析類型")
        for i in range(self.analysis_list.count()):
            item = self.analysis_list.item(i)
            if item.flags() & Qt.ItemIsEnabled:
                item.setSelected(True)

    def select_none(self) -> None:
        """Clear all selections."""
        print("[THROTTLE_DIALOG] 取消選擇所有分析類型")
        self.analysis_list.clearSelection()

    def accept(self) -> None:
        """Handle OK button click."""
        selected_types = self.get_selected_types()
        type_names = []
        for st in selected_types:
            if st == self.TYPE_BOX_PLOT:
                type_names.append("Throttle Box Plot")
            elif st == self.TYPE_LINE_CHART:
                type_names.append("Throttle Line Chart")
        print(f"[THROTTLE_DIALOG] 使用者確認選擇: {', '.join(type_names)}")
        super().accept()

    def reject(self) -> None:
        """Handle Cancel button click."""
        print("[THROTTLE_DIALOG] 使用者取消選擇")
        super().reject()
