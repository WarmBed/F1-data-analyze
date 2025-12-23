#!/usr/bin/env python3
"""Test imports step by step"""
import sys
import os

os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

results = []

def test(name, code):
    try:
        exec(code)
        results.append(f"OK - {name}")
        return True
    except Exception as e:
        results.append(f"FAIL - {name}: {e}")
        return False

test("logging", "import logging")
test("typing", "from typing import Dict, Any, Optional, List")
test("json", "import json")
test("os", "import os")
test("datetime", "from datetime import datetime")

# 不使用 PyQt5 先測
test("core.gui_i18n", "from core.gui_i18n import tr")

# 寫結果
with open("test_f101_step.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))
    f.write("\n\nDone!")
