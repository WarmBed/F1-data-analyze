"""簡單測試：檢查 Japan F57 vs F91 數據"""
import json
from pathlib import Path

# 檢查 Japan 的檔案
print("\n檢查 Japan 數據檔案:")
print("="*60)

# F57
f57_files = list(Path("json").glob("*fp2_race_prediction_2025_Japan*.json"))
print(f"\nF57 檔案: {len(f57_files)} 個")
for f in f57_files:
    print(f"  {f.name}")
    
# F91
f91_files = list(Path("json").glob("*fp2_race_ml_prediction_v2_2025_Japan*.json"))
print(f"\nF91 檔案: {len(f91_files)} 個")
for f in f91_files:
    print(f"  {f.name}")

# 嘗試載入最新的 F91 檔案
if f91_files:
    with open(f91_files[-1], 'r', encoding='utf-8') as f:
        f91_data = json.load(f)
    print(f"\n✅ F91 數據載入成功")
    print(f"   車手數: {len(f91_data.get('predictions', []))}")
    print(f"   VER 圈數: {len([lap for d in f91_data['predictions'] if d['driver_code']=='VER' for lap in d['laps']])}")
