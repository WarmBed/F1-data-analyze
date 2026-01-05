#!/usr/bin/env python3
"""
F1T Race Strategy Simulator - Entry Point

A professional F1 race strategy simulation tool.

Features:
- Lap-by-lap race simulation with tire degradation and fuel effects
- Monte Carlo confidence analysis with SC/VSC probability
- Safety Car scenario planning and bail-out tire recommendations
- Undercut/Overcut window calculation
- Interactive pyqtgraph charts

Usage:
    python strategy_simulator_main.py

Author: F1T Team
Date: 2025-12-30
Version: 1.0.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from strategy_simulator.gui import main


if __name__ == '__main__':
    main()
