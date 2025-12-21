#!/usr/bin/env python3
"""Quick launcher for the championship standings demo widget."""

from __future__ import annotations

import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from modules.gui.championship_standings_demo import ChampionshipStandingsDemoWidget


def main() -> int:
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("F1T Championship Standings Demo")
    widget = ChampionshipStandingsDemoWidget(year=2024, parent=window)
    window.setCentralWidget(widget)
    window.resize(1280, 720)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
