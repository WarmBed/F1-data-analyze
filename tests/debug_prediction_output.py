"""調查模型預測輸出的實際含義"""
import pickle
import json
import numpy as np

# 載入模型
model_data = pickle.load(open('models/track_specific_v3.10/Brazil.pkl', 'rb'))
model = model_data['model']
feature_names = model_data['feature_names']

print("=" * 70)
print("模型結構分析")
print("=" * 70)
print(f"特徵數: {len(feature_names)}")
print(f"特徵名稱: {feature_names}")
print(f"\n模型訓練指標:")
print(f"  Train R²: {model_data.get('train_r2', 'N/A')}")
print(f"  Train MAE: {model_data.get('train_mae', 'N/A')}")
print(f"  CV MAE: {model_data.get('cv_mae', 'N/A')}")

# 載入實際 JSON 檔案
with open('json/qualifying_prediction_2025_Brazil.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

print("\n" + "=" * 70)
print("JSON 檔案分析")
print("=" * 70)
print(f"車手數: {len(json_data['predictions'])}")

# 分析前 3 名
print("\n前 3 名車手數據:")
for i, pred in enumerate(json_data['predictions'][:3], 1):
    print(f"\n{i}. {pred['driver']} ({pred['team']})")
    print(f"   FP3 時間: {pred['fp3_time']:.3f}s")
    print(f"   預測時間: {pred['predicted_time']:.3f}s")
    print(f"   改進值: {pred['improvement']:.3f}s")
    print(f"   實際 Q 時間: {pred.get('actual_q_time', 'N/A')}")
    
    # 檢查邏輯
    if pred['predicted_time'] < 10:
        print(f"   ⚠️ 預測時間異常！只有 {pred['predicted_time']:.3f}秒")
    
    # 計算可能的正確值
    if abs(pred['improvement']) < 70:
        possible_correct = pred['fp3_time'] + pred['improvement']
        print(f"   💡 可能的正確預測: {possible_correct:.3f}s (FP3 + improvement)")

print("\n" + "=" * 70)
print("問題診斷")
print("=" * 70)

# 檢查是否所有預測值都小於 10
all_predictions = [p['predicted_time'] for p in json_data['predictions']]
print(f"預測值範圍: {min(all_predictions):.3f}s - {max(all_predictions):.3f}s")
print(f"FP3 值範圍: {min(p['fp3_time'] for p in json_data['predictions']):.3f}s - {max(p['fp3_time'] for p in json_data['predictions']):.3f}s")

if max(all_predictions) < 10:
    print("\n❌ 確認：所有預測值都小於 10秒，這是錯誤的！")
    print("💡 推測：模型預測的是「改進值」(delta)，而非絕對時間")
    print("💡 修正方案：predicted_time 應該是 FP3_time + model_prediction")
else:
    print("\n✅ 預測值範圍正常")

# 測試修正方案
print("\n" + "=" * 70)
print("修正方案驗證")
print("=" * 70)
print("\n修正後的預測（前 5 名）:")
for i, pred in enumerate(json_data['predictions'][:5], 1):
    corrected_time = pred['fp3_time'] + pred['predicted_time']
    print(f"{i}. {pred['driver']}: {corrected_time:.3f}s (原預測: {pred['predicted_time']:.3f}s)")
