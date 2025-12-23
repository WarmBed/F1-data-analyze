import sys
sys.path.insert(0, r'C:\Users\mike2\OneDrive\Code\F1-data-analyze')

from CLI_modules.cli.prediction.overtake_prediction.data_collector import run_f81_data_collection

print("開始測試 F81 數據收集...")
result = run_f81_data_collection(years=[2024], split_by_year=False, verbose=True)
print(f"\n完成！收集了 {result.get('total_samples', 0)} 個樣本")
