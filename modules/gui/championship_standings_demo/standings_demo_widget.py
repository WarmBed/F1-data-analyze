#!/usr/bin/env python3
"""Standalone championship standings demo widget powered by UniversalDataLoader."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QMessageBox,
    QSplitter,
)

from core.gui_i18n import tr
from modules.gui.championship_standings_demo.standings_data_loader import (
    ChampionshipStandingsDataLoader,
)
from modules.gui.universal_chart_widget import UniversalChartWidget, ChartDataSeries


class ChampionshipStandingsDemoWidget(QWidget):
    """PyQt5 demonstration widget rendering championship standings tables."""

    def __init__(self, *, year: int = 2024, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._year = int(year)
        self._data_loader = ChampionshipStandingsDataLoader(year=self._year, parent=self)
        self._current_payload: Optional[Dict[str, Any]] = None

        self._init_ui()
        self._wire_loader_signals()
        self._trigger_initial_load()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _init_ui(self) -> None:
        self.setObjectName("ChampionshipStandingsDemoWidget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.status_label = QLabel(tr("standings_status_idle", "尚未載入資料"), self)
        self.status_label.setObjectName("standingsStatusLabel")

        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)

        year_label = QLabel(tr("standings_select_year", "選擇年份"), self)
        control_layout.addWidget(year_label)

        self.year_combo = QComboBox(self)
        for season_year in range(2020, 2027):
            self.year_combo.addItem(str(season_year), season_year)
        initial_index = max(0, self.year_combo.findData(self._year))
        self.year_combo.setCurrentIndex(initial_index)
        control_layout.addWidget(self.year_combo)

        self.refresh_button = QPushButton(tr("standings_refresh", "重新載入"), self)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        control_layout.addWidget(self.refresh_button)

        control_layout.addStretch(1)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar, alignment=Qt.AlignRight)

        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.status_label)

        self.summary_group = QGroupBox(tr("standings_summary_title", "賽季摘要"), self)
        summary_layout = QVBoxLayout(self.summary_group)
        summary_layout.setContentsMargins(10, 8, 10, 8)
        self.summary_label = QLabel("", self.summary_group)
        self.summary_label.setWordWrap(True)
        summary_layout.addWidget(self.summary_label)
        main_layout.addWidget(self.summary_group)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setChildrenCollapsible(False)

        self.driver_table = self._build_driver_table()
        driver_box = QGroupBox(tr("standings_driver_title", "車手積分"), self)
        driver_layout = QVBoxLayout(driver_box)
        driver_layout.setContentsMargins(6, 6, 6, 6)
        driver_layout.addWidget(self.driver_table)
        splitter.addWidget(driver_box)

        self.constructor_table = self._build_constructor_table()
        constructor_box = QGroupBox(tr("standings_constructor_title", "車隊積分"), self)
        constructor_layout = QVBoxLayout(constructor_box)
        constructor_layout.setContentsMargins(6, 6, 6, 6)
        constructor_layout.addWidget(self.constructor_table)
        splitter.addWidget(constructor_box)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter, stretch=2)

        self.chart_widget = UniversalChartWidget(title=tr("standings_chart_title", "積分概況圖表"), parent=self)
        self.chart_widget.setMinimumHeight(220)
        main_layout.addWidget(self.chart_widget, stretch=1)

    def _build_driver_table(self) -> QTableWidget:
        table = QTableWidget(self)
        columns = [
            tr("standings_col_position", "名次"),
            tr("standings_col_driver_code", "車手代碼"),
            tr("standings_col_driver", "車手"),
            tr("standings_col_team", "車隊"),
            tr("standings_col_points", "積分"),
            tr("standings_col_wins", "勝場"),
            tr("standings_col_delta", "落後差"),
        ]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setFocusPolicy(Qt.NoFocus)
        return table

    def _build_constructor_table(self) -> QTableWidget:
        table = QTableWidget(self)
        columns = [
            tr("standings_col_position", "名次"),
            tr("standings_col_constructor", "車隊"),
            tr("standings_col_points", "積分"),
            tr("standings_col_wins", "勝場"),
            tr("standings_col_delta", "落後差"),
            tr("standings_col_nationality", "國籍"),
        ]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setFocusPolicy(Qt.NoFocus)
        return table

    # ------------------------------------------------------------------
    # Loader integration
    # ------------------------------------------------------------------
    def _wire_loader_signals(self) -> None:
        self._data_loader.data_loaded.connect(self._on_data_loaded)
        self._data_loader.load_error.connect(self._on_load_error)
        self._data_loader.status_changed.connect(self._on_status_changed)
        self._data_loader.load_progress.connect(self._on_progress_changed)

    def _trigger_initial_load(self) -> None:
        self._data_loader.load_data(year=self._year)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_refresh_clicked(self) -> None:
        selected_year = int(self.year_combo.currentData())
        self._year = selected_year
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._data_loader.load_data(year=selected_year, force_refresh=True)

    def _on_status_changed(self, message: str) -> None:
        self.status_label.setText(message)

    def _on_progress_changed(self, value: int) -> None:
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        if value >= 100:
            self.progress_bar.setVisible(False)

    def _on_data_loaded(self, payload: Dict[str, Any]) -> None:
        self._current_payload = payload
        self._populate_driver_table(payload.get("drivers", []))
        self._populate_constructor_table(payload.get("constructors", []))
        self._update_summary(payload)
        self._update_chart(payload.get("drivers", []))
        self.progress_bar.setVisible(False)

    def _on_load_error(self, message: str) -> None:
        self.progress_bar.setVisible(False)
        
        # 🔧 改善：檢測未來賽季錯誤，顯示友善訊息而不是彈窗
        if "Unaccessible" in message or "Entity for url" in message or "尚未開始" in message:
            friendly_msg = tr("standings_future_season", "未來賽季數據尚未發布")
            self.status_label.setText(friendly_msg)
            self.status_label.setStyleSheet("color: #6c757d; padding: 8px;")
            
            # 在表格中顯示友善訊息
            self._show_empty_state_in_tables(friendly_msg)
        else:
            # 其他錯誤仍然彈出對話框
            self._show_error(tr("standings_error_title", "載入失敗"), message)
    
    def _show_empty_state_in_tables(self, message: str):
        """在表格中顯示空狀態訊息"""
        # 車手表格
        self.driver_table.setRowCount(1)
        empty_item = QTableWidgetItem(message)
        empty_item.setTextAlignment(Qt.AlignCenter)
        self.driver_table.setItem(0, 0, empty_item)
        self.driver_table.setSpan(0, 0, 1, self.driver_table.columnCount())
        
        # 車隊表格
        self.constructor_table.setRowCount(1)
        empty_item_2 = QTableWidgetItem(message)
        empty_item_2.setTextAlignment(Qt.AlignCenter)
        self.constructor_table.setItem(0, 0, empty_item_2)
        self.constructor_table.setSpan(0, 0, 1, self.constructor_table.columnCount())

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _populate_driver_table(self, rows: List[Dict[str, Any]]) -> None:
        table = self.driver_table
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self._set_table_item(table, row_index, 0, row.get("position"))
            self._set_table_item(table, row_index, 1, row.get("driver_code"))
            self._set_table_item(table, row_index, 2, row.get("driver_name"))
            team_text = ", ".join(row.get("team_names", []))
            self._set_table_item(table, row_index, 3, team_text)
            self._set_table_item(table, row_index, 4, row.get("points"))
            self._set_table_item(table, row_index, 5, row.get("wins"))
            self._set_table_item(table, row_index, 6, row.get("points_delta"))
        table.resizeColumnsToContents()

    def _populate_constructor_table(self, rows: List[Dict[str, Any]]) -> None:
        table = self.constructor_table
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self._set_table_item(table, row_index, 0, row.get("position"))
            self._set_table_item(table, row_index, 1, row.get("constructor_name"))
            self._set_table_item(table, row_index, 2, row.get("points"))
            self._set_table_item(table, row_index, 3, row.get("wins"))
            self._set_table_item(table, row_index, 4, row.get("points_delta"))
            self._set_table_item(table, row_index, 5, row.get("constructor_nationality"))
        table.resizeColumnsToContents()

    def _update_summary(self, payload: Dict[str, Any]) -> None:
        metadata = payload.get("metadata", {})
        season = payload.get("season", {})
        summary_text = season.get("summary_text")

        if summary_text:
            self.summary_label.setText(summary_text)
        else:
            self.summary_label.setText(tr("standings_summary_missing", "暫無賽季摘要資料"))

        resolved_round = metadata.get("resolved_round")
        if resolved_round:
            self.status_label.setText(
                tr(
                    "standings_status_resolved_round",
                    "資料來源為第 {round} 場之後的最新積分",
                ).format(round=resolved_round)
            )

    def _update_chart(self, rows: List[Dict[str, Any]]) -> None:
        self.chart_widget.clear_data()
        if not rows:
            return
        top_rows = rows[:8]
        x_indices = list(range(1, len(top_rows) + 1))
        points_values = [row.get("points") or 0 for row in top_rows]
        series = ChartDataSeries(
            name=tr("standings_chart_series", "車手積分"),
            x_data=x_indices,
            y_data=points_values,
            color="#1f78b4",
            line_width=3,
            y_axis="left",
        )
        self.chart_widget.add_data_series(series)
        self.chart_widget.set_axis_labels(
            tr("standings_chart_x_label", "順位"),
            tr("standings_chart_y_label", "積分"),
        )
        self.chart_widget.force_refresh()

    def _set_table_item(self, table: QTableWidget, row: int, column: int, value: Any) -> None:
        display_text = "" if value is None else str(value)
        item = QTableWidgetItem(display_text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(row, column, item)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)


__all__ = ["ChampionshipStandingsDemoWidget"]
