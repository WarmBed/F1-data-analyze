#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regenerate F100 Abu Dhabi JSON"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import warnings
warnings.filterwarnings('ignore')

from CLI_modules.cli.analyzer.historical_flags_analysis import run_historical_flags_analysis_json

print("Regenerating F100 Abu Dhabi JSON...")
result = run_historical_flags_analysis_json(
    'Abu Dhabi', 
    start_year=2022, 
    end_year=2025, 
    session_type='R'
)
print(f"\nDone: {result}")
