#!/usr/bin/env python3
"""Test F101 module imports"""
import sys
print("Testing F101 module imports...")

try:
    print("1. Testing StartReactionDataLoader...")
    from modules.gui.race_analysis.start_reaction.start_reaction_loader import StartReactionDataLoader
    print("   OK")
    
    print("2. Testing StartReactionWidget...")
    from modules.gui.race_analysis.start_reaction.start_reaction_widget import StartReactionWidget
    print("   OK")
    
    print("3. Testing StartReactionMDI...")
    from modules.gui.race_analysis.start_reaction.start_reaction_mdi import StartReactionMDI
    print("   OK")
    
    print("\n All F101 imports successful!")
    
except Exception as e:
    print(f"\n ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
