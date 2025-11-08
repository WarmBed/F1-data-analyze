#!/usr/bin/env python3
"""測試 API 回應格式"""

import json

# 讀取 API 回應
with open('temp_api_response.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 檢查結構
print("=" * 70)
print("API 回應檢查")
print("=" * 70)

print(f"\n✅ success: {data.get('success')}")
print(f"📝 message: {data.get('message')}")

# 檢查 metadata
meta = data['data']['metadata']
print(f"\n📊 Metadata:")
print(f"  track: {meta.get('track')}")
print(f"  year: {meta.get('year')}")
print(f"  model_r2: {meta.get('model_r2')}")
print(f"  model_mae: {meta.get('model_mae')}")
print(f"  sample_count: {meta.get('sample_count')}")
print(f"  has_actual_results: {meta.get('has_actual_results')}")

# 檢查 predictions
predictions = data['data']['predictions']
print(f"\n🏁 Predictions: {len(predictions)} 位車手")
print(f"  第1名: {predictions[0]['driver']} - {predictions[0]['predicted_time']:.3f}s")

print("\n" + "=" * 70)
