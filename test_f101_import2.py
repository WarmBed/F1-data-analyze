#!/usr/bin/env python3
"""Test F101 module imports - write to file"""
import sys
import os

# 設定工作目錄
os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

output = []

def log(msg):
    output.append(msg)
    
log("Testing F101 module imports...")

try:
    log("1. Testing StartReactionDataLoader...")
    from modules.gui.race_analysis.start_reaction.start_reaction_loader import StartReactionDataLoader
    log("   StartReactionDataLoader OK")
    
    log("2. Testing StartReactionWidget...")
    from modules.gui.race_analysis.start_reaction.start_reaction_widget import StartReactionWidget  
    log("   StartReactionWidget OK")
    
    log("3. Testing StartReactionMDI...")
    from modules.gui.race_analysis.start_reaction.start_reaction_mdi import StartReactionMDI
    log("   StartReactionMDI OK")
    
    log("")
    log("All F101 imports successful!")
    
except Exception as e:
    log(f"\n ERROR: {e}")
    import traceback
    log(traceback.format_exc())

# 寫入檔案
with open("test_f101_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("Result written to test_f101_result.txt")
