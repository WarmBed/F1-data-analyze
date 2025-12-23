"""簡化測試：驗證 3 場比賽的數據是否都存在"""
import json
from pathlib import Path

races = ["Japan", "Abu_Dhabi", "Mexico"]

print("\n檢查數據完整性:")
print("="*60)

for race in races:
    print(f"\n{race}:")
    
    # 檢查 FastF1 緩存
    cache_file = Path(f"f1_analysis_cache/f1_data_2025_{race}_R.pkl")
    print(f"  FastF1 緩存: {'✓' if cache_file.exists() else '✗'}")
    
    # 檢查 F57 預測
    f57_files = list(Path("json").glob(f"fp2_race_prediction_2025_{race}_*.json"))
    print(f"  F57 預測: {'✓ (' + str(len(f57_files)) + ' 個檔案)' if f57_files else '✗'}")
    
    # 檢查 F91 預測
    f91_files = list(Path("json").glob(f"fp2_race_ml_prediction_v2_2025_{race}_*.json"))
    print(f"  F91 預測: {'✓ (' + str(len(f91_files)) + ' 個檔案)' if f91_files else '✗'}")
    
    if f91_files:
        with open(f91_files[-1], 'r', encoding='utf-8') as f:
            f91_data = json.load(f)
            print(f"    車手數: {len(f91_data.get('predictions', []))}")
            print(f"    檔名: {f91_files[-1].name}")

print("\n" + "="*60)
