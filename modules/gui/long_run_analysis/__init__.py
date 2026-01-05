#!/usr/bin/env python3
"""
Long Run & Degradation Analysis Module

Analyzes practice session (FP1/FP2/FP3) long run data to calculate true tire degradation rates.

API-ONLY Mode (2025-10-03):
- Uses Function 28 API for lap time data
- No direct FastF1 calls from GUI
- No automatic CLI subprocess invocation

Author: F1T Team
Date: 2025-12-30
Version: 1.0.0
"""

# Lazy import to avoid circular dependency issues
def get_long_run_analysis_class():
    """Get LongRunAnalysis class with lazy import"""
    from .long_run_mdi import LongRunAnalysis
    return LongRunAnalysis

__all__ = ['get_long_run_analysis_class']
