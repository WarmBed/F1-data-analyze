#!/usr/bin/env python3
"""測試單個樣本的 v3.8.1 預測"""

from validate_v381_on_2025 import V381TwentyFiveValidator
import pickle
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# 初始化驗證器
v = V381TwentyFiveValidator()

# 載入 Japan 2025 數據
json_file = list(v.json_dir.glob('fp_q_data_2025_3_*.json'))[0]
df = v.extract_features_from_json(json_file, 'Japan')

# 載入模型
model_data = pickle.load(open('models/track_specific_v3.8.1/Japan.pkl', 'rb'))
model = model_data['model']

# 準備特徵
feature_cols = [
    'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
    'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
    's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
    'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
    'fp3_relative_position', 'fp3_gap_to_fastest', 'is_top_driver',
    'driver_historical_track_performance', 'driver_track_performance_gap'
]

# VER 的數據
ver_data = df[df['driver'] == 'VER'].iloc[0]
X_ver = df[df['driver'] == 'VER'][feature_cols]

print(f"VER 特徵值:")
for i, col in enumerate(feature_cols):
    print(f"  {i+1:2d}. {col:40s}: {ver_data[col]:8.3f}")

print(f"\nVER 實際排位時間: {ver_data['actual_q_time']:.3f}s")

# 預測
pred = model.predict(X_ver)
print(f"VER 預測時間: {pred[0]:.3f}s")
print(f"預測誤差: {pred[0] - ver_data['actual_q_time']:.3f}s")
