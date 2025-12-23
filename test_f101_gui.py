#!/usr/bin/env python3
"""
F101 起跑反應分析 GUI 測試
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow

# 導入模組
from modules.gui.race_analysis.start_reaction.start_reaction_widget import StartReactionWidget
from modules.gui.race_analysis.start_reaction.start_reaction_loader import StartReactionDataLoader


def test_widget_standalone():
    """測試獨立 Widget"""
    app = QApplication(sys.argv)
    
    # 載入數據
    print("Loading data for Abu Dhabi 2025 Race...")
    loader = StartReactionDataLoader(2025, "Abu_Dhabi", "R")
    data = loader.load_data()
    
    if not data:
        print("ERROR: No data loaded!")
        return 1
    
    print(f"Loaded {len(data['drivers'])} drivers")
    
    # 創建主視窗
    window = QMainWindow()
    window.setWindowTitle("F101 Start Reaction Analysis Test")
    window.resize(1400, 900)
    
    # 創建 Widget
    widget = StartReactionWidget()
    widget.update_data(data)
    
    window.setCentralWidget(widget)
    window.show()
    
    return app.exec_()


def test_data_loading():
    """測試數據載入"""
    print("=" * 60)
    print("Testing StartReactionDataLoader")
    print("=" * 60)
    
    loader = StartReactionDataLoader(2025, "Abu_Dhabi", "R")
    data = loader.load_data()
    
    if not data:
        print("ERROR: No data loaded!")
        return False
    
    print(f"Year: {data['year']}")
    print(f"Race: {data['race']}")
    print(f"Session: {data['session']}")
    print(f"Race Start: {data['race_start_ts']:.2f}s")
    print(f"Drivers: {len(data['drivers'])}")
    print()
    
    print("=" * 60)
    print("Driver Data (sorted by grid)")
    print("=" * 60)
    
    for drv in data['drivers']:
        name = drv['name']
        t50 = f"{drv['t50']:.3f}s" if drv['t50'] else '-'
        t100 = f"{drv['t100']:.3f}s" if drv['t100'] else '-'
        grid = drv['grid'] or '?'
        lap1 = drv['lap1_pos'] or '?'
        delta = drv['position_delta']
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        
        print(f"{name:<4} | Grid: P{grid:>2} -> P{lap1:>2} ({delta_str:>3}) | 0-50: {t50:>7} | 0-100: {t100:>7}")
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test F101 Start Reaction Analysis')
    parser.add_argument('--gui', action='store_true', help='Run GUI test')
    parser.add_argument('--data', action='store_true', help='Run data loading test only')
    
    args = parser.parse_args()
    
    if args.data:
        success = test_data_loading()
        sys.exit(0 if success else 1)
    elif args.gui:
        sys.exit(test_widget_standalone())
    else:
        # 預設執行數據測試，然後詢問是否執行 GUI
        success = test_data_loading()
        if success:
            print()
            print("Run with --gui to test the PyQt5 widget")
        sys.exit(0 if success else 1)
