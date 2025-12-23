#!/usr/bin/env python3
"""Quick test for F101"""
import sys
sys.path.insert(0, '.')

from CLI_modules.cli.analyzer.f101_season_start_reaction import run_season_start_reaction_analysis

result = run_season_start_reaction_analysis(2025)
print(f"\nSuccess: {result.get('success')}")
print(f"Message: {result.get('message')}")
if result.get('data'):
    data = result['data']
    print(f"Total races: {data.get('total_races_analyzed')}")
    print(f"P1 unchanged: {data.get('p1_lap2_position_unchanged', {}).get('count')}")
    print(f"P1 changed: {data.get('p1_lap2_position_changed', {}).get('count')}")
