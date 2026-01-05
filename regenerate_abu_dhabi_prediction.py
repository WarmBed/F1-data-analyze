"""重新生成 2025 Abu Dhabi FP2→Q 預測"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from f1_analysis_modular_main import F1Analysis

print("=" * 80)
print("重新生成 2025 Abu Dhabi FP2→Q 預測（使用更新後的燃油校正）")
print("=" * 80)

# 初始化
print("\n初始化分析系統...")
f1 = F1Analysis()
f1.year = 2025
f1.race = 'Abu Dhabi'
f1.session = 'FP2'

# 執行 Function 74
print("\n執行 Function 74...")
result = f1.function_mapper.execute_function_by_number(74)

print("\n" + "=" * 80)
print("執行結果:")
print("=" * 80)
print(f"成功: {result.get('success')}")
print(f"訊息: {result.get('message')}")

if result.get('success'):
    data = result.get('data', {})
    metadata = data.get('metadata', {})
    predictions = data.get('predictions', [])
    
    print(f"\n模型資訊:")
    print(f"  - R²: {metadata.get('model_r2', 'N/A')}")
    print(f"  - MAE: {metadata.get('model_mae', 'N/A')}")
    print(f"  - 版本: {metadata.get('model_version', 'N/A')}")
    print(f"  - 樣本數: {metadata.get('sample_count', 'N/A')}")
    print(f"  - 燃油校正: {metadata.get('fuel_correction_enabled', False)}")
    print(f"  - 校正車隊數: {metadata.get('fuel_correction_teams_count', 0)}")
    
    print(f"\n預測結果 (前 10 名):")
    print(f"{'排名':<6} {'車手':<6} {'車隊':<20} {'預測時間':<12} {'燃油校正':<12}")
    print("-" * 70)
    
    for i, pred in enumerate(predictions[:10], 1):
        driver = pred.get('driver', 'N/A')
        team = pred.get('team', 'N/A')
        pred_time = pred.get('predicted_time_formatted', 'N/A')
        fuel_corr = pred.get('fuel_correction')
        fuel_corr_str = f"{fuel_corr:.3f}s" if fuel_corr else "N/A"
        
        print(f"{i:<6} {driver:<6} {team:<20} {pred_time:<12} {fuel_corr_str:<12}")
else:
    print(f"\n錯誤詳情: {result}")
