#!/usr/bin/env python3
"""Demo 3: Season Progress Summary - Direct JSON Loading and Display"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QGroupBox,
)

from core.gui_i18n import tr


class SeasonProgressSummary(QWidget):
    """Season Progress Summary Widget"""

    def __init__(self, *, standings_json_path: str, calendar_json_path: str, parent=None):
        super().__init__(parent)
        self.standings_json_path = Path(standings_json_path)
        self.calendar_json_path = Path(calendar_json_path)
        self._init_ui()
        self._load_and_populate()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        self.title_label = QLabel(tr("season_progress_title", "2024 賽季進度"), self)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)

        self.summary_box = QGroupBox(tr("season_summary_group", "賽季摘要"), self)
        summary_layout = QVBoxLayout(self.summary_box)
        summary_layout.setSpacing(8)

        self.completed_label = QLabel("", self.summary_box)
        self.completed_label.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(self.completed_label)

        self.remaining_label = QLabel("", self.summary_box)
        self.remaining_label.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(self.remaining_label)

        self.next_race_label = QLabel("", self.summary_box)
        self.next_race_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0066cc;")
        summary_layout.addWidget(self.next_race_label)

        self.next_race_date_label = QLabel("", self.summary_box)
        self.next_race_date_label.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(self.next_race_date_label)

        layout.addWidget(self.summary_box)

        self.leader_box = QGroupBox(tr("current_leaders_group", "目前領先者"), self)
        leader_layout = QVBoxLayout(self.leader_box)
        leader_layout.setSpacing(8)

        self.driver_leader_label = QLabel("", self.leader_box)
        self.driver_leader_label.setStyleSheet("font-size: 14px;")
        leader_layout.addWidget(self.driver_leader_label)

        self.constructor_leader_label = QLabel("", self.leader_box)
        self.constructor_leader_label.setStyleSheet("font-size: 14px;")
        leader_layout.addWidget(self.constructor_leader_label)

        layout.addWidget(self.leader_box)
        layout.addStretch(1)

    def _load_and_populate(self):
        # 讀取積分數據
        standings_data = self._load_json(self.standings_json_path)
        if not standings_data:
            return

        # 讀取賽程數據
        calendar_data = self._load_json(self.calendar_json_path)
        if not calendar_data:
            return

        # 獲取 2024 賽季資料
        events_2024 = calendar_data.get("data", {}).get("2024", [])
        if not events_2024:
            self.title_label.setText(tr("error_no_2024_data", "錯誤：找不到 2024 賽季資料"))
            return

        # 統計已完成與剩餘賽事
        completed = [e for e in events_2024 if e.get("is_completed")]
        upcoming = [e for e in events_2024 if not e.get("is_completed")]

        completed_count = len(completed)
        remaining_count = len(upcoming)
        total_count = len(events_2024)

        self.completed_label.setText(
            tr("completed_races", "已完成賽事：{count} / {total}").format(
                count=completed_count, total=total_count
            )
        )
        self.remaining_label.setText(
            tr("remaining_races", "剩餘賽事：{count}").format(count=remaining_count)
        )

        # 找出下一場賽事
        next_race = upcoming[0] if upcoming else None
        if next_race:
            self.next_race_label.setText(
                tr("next_race", "下一場賽事：{name}").format(name=next_race.get("event_name", ""))
            )
            race_date_str = next_race.get("race_date_local", "")
            if race_date_str:
                # 解析並格式化日期
                try:
                    race_dt = datetime.fromisoformat(race_date_str.replace("Z", "+00:00"))
                    formatted_date = race_dt.strftime("%Y-%m-%d %H:%M")
                    self.next_race_date_label.setText(
                        tr("race_date", "日期：{date}").format(date=formatted_date)
                    )
                except Exception:
                    self.next_race_date_label.setText(
                        tr("race_date", "日期：{date}").format(date=race_date_str)
                    )
        else:
            self.next_race_label.setText(tr("no_upcoming_races", "本賽季已結束"))
            self.next_race_date_label.setText("")

        # 顯示領先者
        summary = standings_data.get("summary", {})
        top_driver = summary.get("top_driver", {})
        if top_driver:
            self.driver_leader_label.setText(
                tr("driver_leader", "車手領先：{name} ({team}) - {points} 分").format(
                    name=top_driver.get("full_name", ""),
                    team=top_driver.get("constructor", ""),
                    points=top_driver.get("points", 0),
                )
            )

        top_constructor = summary.get("top_constructor", {})
        if top_constructor:
            self.constructor_leader_label.setText(
                tr("constructor_leader", "車隊領先：{name} - {points} 分").format(
                    name=top_constructor.get("name", ""), points=top_constructor.get("points", 0)
                )
            )

    def _load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            self.title_label.setText(
                tr("error_file_not_found", "錯誤：找不到檔案 {path}").format(path=str(path))
            )
            return None

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        if not data.get("success"):
            self.title_label.setText(tr("error_data_invalid", "錯誤：資料無效"))
            return None

        return data


def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle(tr("demo3_window_title", "F1T Demo 3 - Season Progress Summary"))

    standings_json = "json/championship_standings_2024_R24_20251012T155237Z.json"
    calendar_json = "json/season_calendar_multi_year_20251010T105907Z.json"
    widget = SeasonProgressSummary(
        standings_json_path=standings_json, calendar_json_path=calendar_json, parent=window
    )
    window.setCentralWidget(widget)
    window.resize(600, 400)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
