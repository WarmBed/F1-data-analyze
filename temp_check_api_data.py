# -*- coding: utf-8 -*-
"""
檢查 ChampionshipPrediction 和 PitStopSeries 數據結構
"""
import json
from pathlib import Path

# 讀取錄製的數據
data_file = Path(r"data\live_timing_recordings\raw_20251207_220227.jsonl")

with open(data_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 解析第一行 (通常包含完整初始狀態)
first_line = content.split('\n')[0]
data = json.loads(first_line)

print("=" * 60)
print("📊 ChampionshipPrediction 數據結構")
print("=" * 60)

if 'ChampionshipPrediction' in str(data):
    # 搜索 ChampionshipPrediction
    import re
    match = re.search(r'"ChampionshipPrediction":\s*(\{[^}]+\})', content)
    if match:
        print(match.group(0)[:500])
        
# 搜索 PitStopSeries
print("\n" + "=" * 60)
print("🔧 PitStopSeries 數據結構")
print("=" * 60)

match = re.search(r'"PitStopSeries":\s*(\{[^}]+\})', content)
if match:
    print(match.group(0)[:1000])
