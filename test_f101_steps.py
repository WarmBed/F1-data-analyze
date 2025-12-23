#!/usr/bin/env python3
"""Test F101 GUI modules step by step with file markers"""
import sys
import os

os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

def mark(step, msg):
    with open(f"f101_step{step}.txt", "w") as f:
        f.write(msg)

mark(1, "Start")

try:
    mark(2, "Before loader import")
    from modules.gui.race_analysis.start_reaction.start_reaction_loader import StartReactionDataLoader
    mark(3, "Loader imported OK")
    
    mark(4, "Before widget import")
    from modules.gui.race_analysis.start_reaction.start_reaction_widget import StartReactionWidget
    mark(5, "Widget imported OK")
    
    mark(6, "Before MDI import")
    # 從包導入，而不是直接從模組導入
    from modules.gui.race_analysis.start_reaction import StartReactionMDI, StartReactionAnalysisMDI
    mark(7, "MDI imported OK")
    
    mark(8, "ALL IMPORTS SUCCESSFUL!")
    
except Exception as e:
    import traceback
    mark(99, f"ERROR: {e}\n\n{traceback.format_exc()}")
