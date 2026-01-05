#!/usr/bin/env python3
"""Minimal test - no logger"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import statistics

@dataclass
class LapData:
    lap_number: int
    lap_time: float
    stint: int
    compound: str
    tyre_life: int

@dataclass
class StintInfo:
    driver_code: str
    stint_number: int
    start_lap: int
    end_lap: int
    lap_count: int
    compound: str
    is_long_run: bool = False
    confidence: float = 0.0
    selected: bool = False

print("Step 1 - dataclasses OK")

class LongRunCalc:
    MIN_CONSECUTIVE_LAPS = 4
    
    def __init__(self):
        self._all_laps = {}
        self._detected_stints = []
        print("Step 2 - LongRunCalc init OK")

calc = LongRunCalc()
print("Step 3 - Instance created OK")
print("ALL TESTS PASSED!")
