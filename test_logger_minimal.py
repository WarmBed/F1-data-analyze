#!/usr/bin/env python3
"""Minimal test for core.logger"""
import sys
import os

# 寫標記檔案
os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

with open("step1.txt", "w") as f:
    f.write("Step 1: Before import\n")

try:
    from core.logger import get_logger
    with open("step2.txt", "w") as f:
        f.write("Step 2: After import\n")
    
    logger = get_logger(__name__)
    with open("step3.txt", "w") as f:
        f.write("Step 3: Logger created\n")
        
except Exception as e:
    with open("error.txt", "w") as f:
        f.write(f"Error: {e}\n")
