#!/usr/bin/env python3
"""
Strategy Report Dialog

A dialog window to display strategy analysis reports.
Supports copying to clipboard and exporting.

Author: F1T Team
Date: 2025-01-07
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QApplication, QMessageBox,
    QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextOption

from strategy_simulator.gui.i18n_helper import tr


class StrategyReportDialog(QDialog):
    """
    Dialog to display strategy analysis report.
    
    Features:
    - Monospace font for proper alignment
    - Copy to clipboard button
    - Export to file button
    - Scrollable text area
    """
    
    def __init__(
        self, 
        report_text: str, 
        strategy_name: str = "",
        parent=None
    ):
        super().__init__(parent)
        
        self._report_text = report_text
        self._strategy_name = strategy_name
        
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle(
            f"策略分析報告 - {self._strategy_name}" if self._strategy_name 
            else "策略分析報告"
        )
        self.setMinimumSize(800, 700)
        self.resize(900, 800)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 Race Engineer 決策支援報告")
        title_label.setFont(QFont("", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Strategy name badge
        if self._strategy_name:
            badge = QLabel(f"🏎️ {self._strategy_name}")
            badge.setStyleSheet("""
                QLabel {
                    background-color: #E3F2FD;
                    color: #1565C0;
                    padding: 5px 12px;
                    border-radius: 12px;
                    font-weight: bold;
                }
            """)
            header_layout.addWidget(badge)
        
        layout.addLayout(header_layout)
        
        # Report text area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(self._report_text)
        self.text_edit.setWordWrapMode(QTextOption.NoWrap)
        
        # Use monospace font for proper alignment
        mono_font = QFont("Consolas", 10)
        if not mono_font.exactMatch():
            mono_font = QFont("Courier New", 10)
        if not mono_font.exactMatch():
            mono_font = QFont("monospace", 10)
        self.text_edit.setFont(mono_font)
        
        layout.addWidget(self.text_edit, 1)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        # Copy button
        self.copy_btn = QPushButton("📋 複製到剪貼簿")
        self.copy_btn.setMinimumWidth(140)
        self.copy_btn.clicked.connect(self._on_copy_clicked)
        button_layout.addWidget(self.copy_btn)
        
        # Export button
        self.export_btn = QPushButton("💾 匯出報告")
        self.export_btn.setMinimumWidth(120)
        self.export_btn.clicked.connect(self._on_export_clicked)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        # Close button
        self.close_btn = QPushButton("關閉")
        self.close_btn.setMinimumWidth(100)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def _apply_styling(self):
        """Apply dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #FAFAFA;
            }
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
            }
        """)
        
    def _on_copy_clicked(self):
        """Copy report to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._report_text)
        
        # Show brief feedback
        self.copy_btn.setText("✅ 已複製!")
        self.copy_btn.setStyleSheet("background-color: #C8E6C9;")
        
        # Reset after 2 seconds
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(2000, self._reset_copy_button)
        
    def _reset_copy_button(self):
        """Reset copy button to original state."""
        self.copy_btn.setText("📋 複製到剪貼簿")
        self.copy_btn.setStyleSheet("")
        
    def _on_export_clicked(self):
        """Export report to file."""
        # Generate default filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"strategy_report_{self._strategy_name}_{timestamp}.txt"
        default_name = default_name.replace(" ", "_").replace("-", "_")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "匯出策略報告",
            default_name,
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._report_text)
                
                QMessageBox.information(
                    self,
                    "匯出成功",
                    f"報告已成功匯出至:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "匯出失敗",
                    f"無法匯出報告:\n{str(e)}"
                )
    
    def update_report(self, report_text: str, strategy_name: str = ""):
        """Update report content."""
        self._report_text = report_text
        self._strategy_name = strategy_name
        
        self.text_edit.setPlainText(report_text)
        
        if strategy_name:
            self.setWindowTitle(f"策略分析報告 - {strategy_name}")


class QuickReportButton(QPushButton):
    """
    A small button that generates and shows strategy report.
    
    Usage:
        btn = QuickReportButton(strategy_result, parent)
        # Clicking will open report dialog
    """
    
    def __init__(
        self, 
        strategy_result=None,
        mc_summary=None,
        simulation_data=None,
        our_driver: str = "",
        grid_position: int = 1,
        track_name: str = "",
        race_laps: int = 57,
        pit_loss: float = 24.0,
        parent=None
    ):
        super().__init__("📄", parent)
        
        self._strategy_result = strategy_result
        self._mc_summary = mc_summary
        self._simulation_data = simulation_data
        self._our_driver = our_driver
        self._grid_position = grid_position
        self._track_name = track_name
        self._race_laps = race_laps
        self._pit_loss = pit_loss
        
        self.setToolTip("查看策略分析報告")
        self.setFixedSize(30, 24)
        self.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                border: 1px solid #BDBDBD;
                border-radius: 3px;
                background-color: #FAFAFA;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
                border-color: #1976D2;
            }
        """)
        
        self.clicked.connect(self._show_report)
        
    def set_data(
        self,
        strategy_result=None,
        mc_summary=None,
        simulation_data=None,
        our_driver: str = None,
        grid_position: int = None,
        track_name: str = None,
        race_laps: int = None,
        pit_loss: float = None,
    ):
        """Update button data."""
        if strategy_result is not None:
            self._strategy_result = strategy_result
        if mc_summary is not None:
            self._mc_summary = mc_summary
        if simulation_data is not None:
            self._simulation_data = simulation_data
        if our_driver is not None:
            self._our_driver = our_driver
        if grid_position is not None:
            self._grid_position = grid_position
        if track_name is not None:
            self._track_name = track_name
        if race_laps is not None:
            self._race_laps = race_laps
        if pit_loss is not None:
            self._pit_loss = pit_loss
            
    def _show_report(self):
        """Generate and show report dialog."""
        if not self._strategy_result:
            QMessageBox.warning(
                self.window(),
                "無策略資料",
                "沒有策略資料可生成報告"
            )
            return
        
        from strategy_simulator.gui.widgets.strategy_report_generator import StrategyReportGenerator
        
        generator = StrategyReportGenerator()
        
        # Get scenario analyses from MC summary
        scenario_analyses = None
        if self._mc_summary and hasattr(self._mc_summary, 'scenario_analyses'):
            scenario_analyses = self._mc_summary.scenario_analyses
        
        # Get traffic data from simulation
        traffic_data = None
        if self._simulation_data and hasattr(self._simulation_data, 'traffic_data'):
            traffic_data = self._simulation_data.traffic_data
        
        report = generator.generate_report(
            strategy_result=self._strategy_result,
            simulation_data=self._simulation_data,
            mc_summary=self._mc_summary,
            our_driver=self._our_driver,
            grid_position=self._grid_position,
            track_name=self._track_name,
            race_laps=self._race_laps,
            pit_loss_green=self._pit_loss,
            traffic_data=traffic_data,
            scenario_analyses=scenario_analyses,
        )
        
        strategy_name = getattr(self._strategy_result, 'strategy_name', 'Unknown')
        
        dialog = StrategyReportDialog(report, strategy_name, self.window())
        dialog.exec_()
