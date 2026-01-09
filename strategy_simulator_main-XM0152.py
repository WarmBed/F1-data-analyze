#!/usr/bin/env python3
"""
Strategy Simulator Main Entry Point

Launches the F1 Strategy Simulator GUI application.

Author: F1T Team
Date: 2025-01-07
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


def main():
    """Main entry point for the strategy simulator."""
    print("[MAIN] ========== 策略模擬器啟動 ==========")
    
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("F1 Strategy Simulator")
    app.setOrganizationName("F1T")
    
    # Import and create main window
    from strategy_simulator.gui.main_window import MainWindow
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
