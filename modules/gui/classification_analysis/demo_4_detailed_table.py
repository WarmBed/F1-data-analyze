#!/usr/bin/env python3
"""Local detailed records widget for FIA parts classification."""

from __future__ import annotations

from typing import Any, Dict, Optional

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QHeaderView,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.gui_i18n import tr
from core.local_analysis_client import execute_analysis_sync


class ClassificationApiWorker(QThread):
    """Background local worker for function 29."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(
        self,
        base_url: str | int | None = None,
        year: int = 2025,
        params: Optional[Dict[str, Any]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        if isinstance(base_url, int):
            year = base_url
            base_url = None
        self.base_url = str(base_url or "local")
        self.year = int(year)
        self.params = dict(params or {})

    def run(self) -> None:
        try:
            self.progress.emit(10)
            payload = {"year": self.year, **self.params}
            result = execute_analysis_sync(29, **payload)
            self.progress.emit(80)
            if not result.get("success"):
                self.failure.emit(result.get("error") or result.get("message") or "Function 29 failed")
                return
            self.success.emit(result.get("data") or result)
            self.progress.emit(100)
        except Exception as exc:
            self.failure.emit(f"{type(exc).__name__}: {exc}")


class ClassificationDetailedTableWidget(QWidget):
    """Detailed records table backed by local function 29 output."""

    def __init__(self, api_base_url: str | int | None = None, year: int = 2025, parent=None):
        super().__init__(parent)
        if isinstance(api_base_url, int):
            year = api_base_url
            api_base_url = None
        self.year = int(year)
        self._api_base_url = str(api_base_url or "local")
        self._api_worker: Optional[ClassificationApiWorker] = None
        self.records_data: list[dict[str, Any]] = []
        self.filtered_data: list[dict[str, Any]] = []

        self._setup_ui()
        self.load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.status_label = QLabel(tr("loading", "Loading..."))
        layout.addWidget(self.status_label)

        self.table_widget = QTableWidget(0, 8)
        self.table_widget.setHorizontalHeaderLabels([
            "Race",
            "Team",
            "Driver",
            "Main Category",
            "Sub Category",
            "Change Type",
            "Confidence",
            "Description",
        ])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_widget)

    def load_data(self) -> None:
        self.status_label.setText(tr("loading", "Loading..."))
        self._api_worker = ClassificationApiWorker(self._api_base_url, self.year, parent=self)
        self._api_worker.success.connect(self.on_data_loaded)
        self._api_worker.failure.connect(self.on_data_error)
        self._api_worker.start()

    def on_data_loaded(self, data: dict) -> None:
        self.records_data = self._extract_records(data)
        self.filtered_data = list(self.records_data)
        self.populate_table()
        self.status_label.setText(f"{len(self.filtered_data)} records")

    def on_data_error(self, error_msg: str) -> None:
        self.status_label.setText(error_msg)
        QMessageBox.warning(self, tr("warning", "Warning"), error_msg)

    def _extract_records(self, data: dict) -> list[dict[str, Any]]:
        candidates = [
            data.get("records"),
            data.get("data", {}).get("records") if isinstance(data.get("data"), dict) else None,
            data.get("classified_records"),
            data.get("parts_changes"),
        ]
        for candidate in candidates:
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]
        return []

    def populate_table(self) -> None:
        self.table_widget.setRowCount(len(self.filtered_data))
        for row, record in enumerate(self.filtered_data):
            values = [
                record.get("race") or record.get("Race") or record.get("event") or "",
                record.get("team") or record.get("Team") or "",
                record.get("driver") or record.get("Driver") or "",
                record.get("main_category") or record.get("Main Category") or "",
                record.get("sub_category") or record.get("Sub Category") or "",
                record.get("change_type") or record.get("Change Type") or "",
                record.get("confidence") or record.get("Confidence") or "",
                record.get("description") or record.get("Description") or "",
            ]
            for col, value in enumerate(values):
                self.table_widget.setItem(row, col, QTableWidgetItem(str(value)))

    def refresh_data(self) -> None:
        self.load_data()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = ClassificationDetailedTableWidget(year=2025)
    window.resize(1200, 700)
    window.show()
    sys.exit(app.exec_())
