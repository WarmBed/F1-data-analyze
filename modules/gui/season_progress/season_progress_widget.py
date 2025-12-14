#!/usr/bin/env python3
"""
Season Progress Widget

Displays season statistics summary including race progress and championship leaders

Author: F1T Team
Date: 2025-10-13
Version: 1.0.0
"""

import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QApplication
)
from PyQt5.QtCore import Qt

from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)

logger = get_logger("season_progress.widget", component="gui")


class SeasonProgressWidget(QWidget):
    """
    Season Progress Summary Widget
    
    Displays season progress including:
    - Completed and remaining races
    - Next race information
    - Championship leaders (driver and constructor)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress_data: Optional[Dict[str, Any]] = None
        self.season_year: int = 2024
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # Title - 響應式字體
        self.title_label = QLabel(tr("season_progress_title", "Season Progress"), self)
        self.title_label.setObjectName("season_progress_title")  # 用於響應式選擇器
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # Season Summary Group - 響應式標題
        self.summary_box = QGroupBox(tr("season_summary_group", "Season Summary"), self)
        self.summary_box.setObjectName("season_summary_groupbox")  # 用於響應式選擇器
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
        
        # Leaders Group - 響應式標題
        self.leader_box = QGroupBox(tr("current_leaders_group", "Current Leaders"), self)
        self.leader_box.setObjectName("current_leaders_groupbox")  # 用於響應式選擇器
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
    
    def populate_data(self, data: Dict[str, Any]):
        """
        Populate widget with data
        
        Args:
            data: Transformed season progress data from DataLoader
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[SEASON_PROGRESS_WIDGET] populate_data called")
            logger.debug("[SEASON_PROGRESS_WIDGET] Data keys: %s", list(data.keys()))
        
        self.progress_data = data
        self.season_year = data.get("season_year", 2024)
        
        # Update title
        title = tr("season_progress_title", "Season Progress - {year}").format(year=self.season_year)
        self.title_label.setText(title)
        
        # Update calendar summary
        calendar = data.get("calendar", {})
        completed = calendar.get("completed", 0)
        remaining = calendar.get("remaining", 0)
        total = calendar.get("total", 0)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "[SEASON_PROGRESS_WIDGET] Calendar data: completed=%s, remaining=%s, total=%s",
                completed,
                remaining,
                total,
            )
        
        self.completed_label.setText(
            tr("completed_races", "Completed Races: {count} / {total}").format(
                count=completed, total=total
            )
        )
        self.remaining_label.setText(
            tr("remaining_races", "Remaining Races: {count}").format(count=remaining)
        )
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "[SEASON_PROGRESS_WIDGET] Labels updated: completed='%s', remaining='%s'",
                self.completed_label.text(),
                self.remaining_label.text(),
            )
        
        # Update next race
        next_race = calendar.get("next_race")
        if next_race:
            race_name = next_race.get("name", "")
            self.next_race_label.setText(
                tr("next_race", "Next Race: {name}").format(name=race_name)
            )
            
            race_date_str = next_race.get("date", "")
            if race_date_str:
                try:
                    race_dt = datetime.fromisoformat(race_date_str.replace("Z", "+00:00"))
                    formatted_date = race_dt.strftime("%Y-%m-%d %H:%M")
                    self.next_race_date_label.setText(
                        tr("race_date", "Date: {date}").format(date=formatted_date)
                    )
                except Exception:
                    self.next_race_date_label.setText(
                        tr("race_date", "Date: {date}").format(date=race_date_str)
                    )
        else:
            self.next_race_label.setText(tr("no_upcoming_races", "Season Completed"))
            self.next_race_date_label.setText("")
        
        # Update leaders
        leaders = data.get("leaders", {})
        
        # Driver leader
        top_driver = leaders.get("driver")
        if top_driver:
            self.driver_leader_label.setText(
                tr("driver_leader", "Driver Leader: {name} ({team}) - {points} pts").format(
                    name=top_driver.get("full_name", ""),
                    team=top_driver.get("constructor", ""),
                    points=top_driver.get("points", 0)
                )
            )
        else:
            self.driver_leader_label.setText(tr("na", "N/A"))
        
        # Constructor leader
        top_constructor = leaders.get("constructor")
        if top_constructor:
            self.constructor_leader_label.setText(
                tr("constructor_leader", "Constructor Leader: {name} - {points} pts").format(
                    name=top_constructor.get("name", ""),
                    points=top_constructor.get("points", 0)
                )
            )
        else:
            self.constructor_leader_label.setText(tr("na", "N/A"))
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[SEASON_PROGRESS_WIDGET] Data populated successfully")
    
    def resizeEvent(self, event):
        """響應視窗大小變化，自動調整字體大小"""
        super().resizeEvent(event)
        self._adjust_responsive_font()
    
    def _adjust_responsive_font(self):
        """根據視窗寬度調整字體大小"""
        width = self.width()
        
        # 定義響應式字體大小
        if width < 250:
            # 極小視窗: 標題 12px, GroupBox 9px, 內容 10px
            title_size = 12
            groupbox_size = 9
            content_size = 10
        elif width < 350:
            # 小視窗: 標題 14px, GroupBox 10px, 內容 11px
            title_size = 14
            groupbox_size = 10
            content_size = 11
        elif width < 450:
            # 中等視窗: 標題 16px, GroupBox 11px, 內容 12px
            title_size = 16
            groupbox_size = 11
            content_size = 12
        else:
            # 大視窗: 標題 18px, GroupBox 12px, 內容 14px (預設)
            title_size = 18
            groupbox_size = 12
            content_size = 14
        
        # 應用響應式樣式
        self.title_label.setStyleSheet(f"font-size: {title_size}px; font-weight: bold;")
        
        # GroupBox 標題樣式
        groupbox_style = f"QGroupBox {{ font-size: {groupbox_size}px; font-weight: bold; }}"
        self.summary_box.setStyleSheet(groupbox_style)
        self.leader_box.setStyleSheet(groupbox_style)
        
        # 內容標籤樣式
        content_style = f"font-size: {content_size}px;"
        self.completed_label.setStyleSheet(content_style)
        self.remaining_label.setStyleSheet(content_style)
        self.next_race_label.setStyleSheet(f"{content_style} font-weight: bold; color: #0066cc;")
        self.next_race_date_label.setStyleSheet(content_style)
        self.driver_leader_label.setStyleSheet(content_style)
        self.constructor_leader_label.setStyleSheet(content_style)


# Test code
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test Widget
    widget = SeasonProgressWidget()
    widget.setWindowTitle(tr("test_window_title", "Season Progress Test"))
    widget.resize(600, 400)
    
    # Test data (for UI testing only)
    test_data = {
        "season_year": 2025,
        "round": 18,
        "calendar": {
            "completed": 18,
            "remaining": 6,
            "total": 24,
            "next_race": {
                "name": "United States Grand Prix",
                "date": "2025-10-20T19:00:00Z"
            }
        },
        "leaders": {
            "driver": {
                "full_name": "Oscar Piastri",
                "constructor": "McLaren",
                "points": 336.0
            },
            "constructor": {
                "name": "McLaren",
                "points": 650.0
            }
        }
    }
    
    widget.populate_data(test_data)
    widget.show()
    sys.exit(app.exec_())
