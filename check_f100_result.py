#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""檢查 F100 JSON 結果中的 Live Timing 整合"""

import json
import os
from pathlib import Path

def check_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ERROR: {e}")
        return None
    
    metadata = data['data']['metadata']
    yearly = data['data']['yearly_summary']
    
    years_avail = metadata.get('years_available', 0)
    
    # 檢查是否有 position_changes_detail 和 source 欄位
    has_detail = False
    has_source = False
    sources = []
    
    for year, info in yearly.items():
        detail = info.get('position_changes_detail', {})
        if detail:
            has_detail = True
            source = detail.get('source', '')
            if source:
                has_source = True
                sources.append(f"{year}:{source}")
    
    return {
        'years': years_avail,
        'has_detail': has_detail,
        'has_source': has_source,
        'sources': sources,
        'yearly_keys': list(yearly.keys())
    }

def check_single_file(filepath):
    """詳細檢查單一檔案"""
    print(f"\n{'='*60}")
    print(f"File: {filepath}")
    print("=" * 60)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    metadata = data['data']['metadata']
    yearly = data['data']['yearly_summary']
    
    print(f"Circuit: {metadata.get('circuit_name', 'N/A')}")
    print(f"Country: {metadata.get('country', 'N/A')}")
    print(f"Years Available: {metadata.get('years_available', 'N/A')}")
    print(f"Years Analyzed: {metadata.get('years_analyzed', 'N/A')}")
    print(f"Yearly Summary Keys: {list(yearly.keys())}")
    
    if not yearly:
        print("\n[WARNING] yearly_summary is EMPTY!")
        return
    
    print("\n--- Position Changes Detail ---")
    for year in sorted(yearly.keys()):
        info = yearly[year]
        detail = info.get('position_changes_detail', {})
        source = detail.get('source', 'N/A') if detail else 'N/A'
        pos_chg = info.get('position_changes', 'N/A')
        on_track = detail.get('on_track_overtakes', 'N/A') if detail else 'N/A'
        pit_rel = detail.get('pit_related', 'N/A') if detail else 'N/A'
        
        print(f"  {year}: pos_chg={pos_chg}, on_track={on_track}, pit={pit_rel}, source={source}")

def main():
    import sys
    
    if len(sys.argv) > 1:
        # 檢查指定檔案
        for fp in sys.argv[1:]:
            check_single_file(fp)
        return
    
    json_dir = Path('json')
    files = sorted(json_dir.glob('historical_flags_*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    print("=" * 80)
    print("F100 Historical Flags - Live Timing Integration Check")
    print("=" * 80)
    print(f"{'File':<45} {'Years':<6} {'Detail':<8} {'Source':<8} Sources")
    print("-" * 80)
    
    for fp in files[:25]:  # 檢查最新的 25 個
        result = check_file(fp)
        if result:
            detail_str = 'Yes' if result['has_detail'] else 'No'
            source_str = 'Yes' if result['has_source'] else 'No'
            sources = ', '.join(result['sources'][:3]) if result['sources'] else '-'
            print(f"{fp.name:<45} {result['years']:<6} {detail_str:<8} {source_str:<8} {sources}")
        else:
            print(f"{fp.name:<45} ERROR")

if __name__ == "__main__":
    main()
