"""
深度調查 Great Britain max_speed 主導現象
1. 驗證特徵重要性計算
2. 分析訓練數據 max_speed 分佈
3. 檢查 max_speed 與排位結果的相關性
4. 對比其他高速賽道（Italy, Belgium）
5. 評估添加 max_speed_lap_ratio 交互特徵的潛力
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

print("="*80)
print("Great Britain max_speed 主導現象深度調查")
print("="*80)

# 1. 重新載入模型，驗證特徵重要性
print("\n### 1. 驗證 Great Britain 模型特徵重要性")
print("-"*80)

gb_model_path = Path("models/track_specific_v3.3/Great Britain.pkl")
if gb_model_path.exists():
    with open(gb_model_path, 'rb') as f:
        gb_model = pickle.load(f)
    
    feature_names = [
        'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
        's1_s2_ratio', 'sector_cv', 's2_lap_ratio'
    ]
    
    importances = gb_model.feature_importances_
    
    # 排序並顯示
    feature_importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print("✅ 特徵重要性（完整列表）:")
    for idx, row in feature_importance_df.iterrows():
        print(f"  {row['feature']:20s} {row['importance']*100:6.2f}%")
    
    max_speed_importance = feature_importance_df[feature_importance_df['feature'] == 'max_speed']['importance'].values[0]
    print(f"\n⚠️  max_speed 占比: {max_speed_importance*100:.2f}%")
    
    # 檢查是否真的這麼高
    if max_speed_importance > 0.5:
        print("❌ 確認: max_speed 確實超過 50%，這非常異常！")
    else:
        print("✅ max_speed 占比正常")

# 2. 載入 Great Britain 訓練數據
print("\n### 2. 分析 Great Britain 訓練數據")
print("-"*80)

# 搜索 Great Britain 訓練數據 JSON
json_dir = Path("json/predictionJSON")
gb_training_files = []

if json_dir.exists():
    for year in [2022, 2023, 2024]:
        # 正確的檔案名稱格式
        pattern = f"fp_q_data_{year}_Great Britain_*.json"
        files = list(json_dir.glob(pattern))
        gb_training_files.extend(files)

print(f"找到 {len(gb_training_files)} 個 Great Britain 訓練數據檔案")

if gb_training_files:
    # 收集所有數據
    all_data = []
    
    for file_path in sorted(gb_training_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取排位賽數據
            if 'qualifying' in data and 'drivers' in data['qualifying']:
                for driver in data['qualifying']['drivers']:
                    if 'track_features' in driver:
                        features = driver['track_features']
                        row = {
                            'year': data.get('year', 'unknown'),
                            'driver': driver.get('driver_name', 'unknown'),
                            'position': driver.get('position', None),
                            'ideal_lap': features.get('ideal_lap'),
                            'max_speed': features.get('max_speed'),
                            'ideal_s1': features.get('ideal_s1'),
                            'ideal_s2': features.get('ideal_s2'),
                            'ideal_s3': features.get('ideal_s3')
                        }
                        all_data.append(row)
        except Exception as e:
            print(f"❌ 讀取 {file_path.name} 失敗: {e}")
    
    if all_data:
        df = pd.DataFrame(all_data)
        print(f"\n✅ 成功載入 {len(df)} 筆訓練樣本")
        
        # 3. max_speed 統計分析
        print("\n### 3. max_speed 統計分析")
        print("-"*80)
        print(f"max_speed 範圍: {df['max_speed'].min():.1f} - {df['max_speed'].max():.1f} km/h")
        print(f"max_speed 平均: {df['max_speed'].mean():.1f} km/h")
        print(f"max_speed 標準差: {df['max_speed'].std():.2f} km/h")
        print(f"max_speed 變異係數 (CV): {(df['max_speed'].std() / df['max_speed'].mean())*100:.2f}%")
        
        # 4. 相關性分析
        print("\n### 4. max_speed 與排位結果的相關性")
        print("-"*80)
        
        # 移除缺失值
        df_clean = df.dropna(subset=['max_speed', 'position'])
        
        if len(df_clean) > 0:
            # Spearman 相關性（排名）
            spearman_corr, spearman_p = spearmanr(df_clean['max_speed'], df_clean['position'])
            print(f"Spearman 相關性: {spearman_corr:.4f} (p={spearman_p:.4f})")
            
            # Pearson 相關性（線性）
            pearson_corr, pearson_p = pearsonr(df_clean['max_speed'], df_clean['position'])
            print(f"Pearson 相關性:  {pearson_corr:.4f} (p={pearson_p:.4f})")
            
            if abs(spearman_corr) > 0.7:
                print("✅ max_speed 與排位結果強相關（合理）")
            elif abs(spearman_corr) > 0.5:
                print("⚠️  max_speed 與排位結果中等相關")
            else:
                print("❌ max_speed 與排位結果弱相關（不應該主導模型！）")
        
        # 5. ideal_lap 相關性對比
        print("\n### 5. ideal_lap vs max_speed 相關性對比")
        print("-"*80)
        
        df_clean_lap = df.dropna(subset=['ideal_lap', 'position'])
        if len(df_clean_lap) > 0:
            spearman_lap, _ = spearmanr(df_clean_lap['ideal_lap'], df_clean_lap['position'])
            print(f"ideal_lap Spearman:  {spearman_lap:.4f}")
            print(f"max_speed Spearman:  {spearman_corr:.4f}")
            print(f"差異: {abs(spearman_lap) - abs(spearman_corr):.4f}")
            
            if abs(spearman_lap) > abs(spearman_corr):
                print("✅ ideal_lap 的預測能力更強（理論上應該如此）")
            else:
                print("⚠️  max_speed 的預測能力竟然更強（異常！）")
        
        # 6. 檢查 max_speed 與 ideal_lap 的關係
        print("\n### 6. max_speed vs ideal_lap 關係分析")
        print("-"*80)
        
        df_features = df.dropna(subset=['max_speed', 'ideal_lap'])
        if len(df_features) > 0:
            corr_ms_lap, _ = pearsonr(df_features['max_speed'], df_features['ideal_lap'])
            print(f"max_speed 與 ideal_lap 相關性: {corr_ms_lap:.4f}")
            
            if abs(corr_ms_lap) < 0.3:
                print("✅ 兩者獨立性高，適合作為獨立特徵")
            elif abs(corr_ms_lap) < 0.7:
                print("⚠️  中等相關，可能存在冗餘")
            else:
                print("❌ 高度相關，存在多重共線性")
            
            # 計算 max_speed_lap_ratio 的潛力
            df_features['max_speed_lap_ratio'] = df_features['max_speed'] / (df_features['ideal_lap'] * 10)  # 標準化
            
            df_with_position = df_features.dropna(subset=['max_speed_lap_ratio', 'position'])
            if len(df_with_position) > 0:
                corr_ratio, _ = spearmanr(df_with_position['max_speed_lap_ratio'], df_with_position['position'])
                print(f"\n💡 max_speed_lap_ratio 與排位相關性: {corr_ratio:.4f}")
                
                if abs(corr_ratio) > abs(spearman_corr):
                    print("✅ 交互特徵 max_speed_lap_ratio 可能更有效！")
                else:
                    print("⚠️  交互特徵沒有明顯優勢")

# 7. 對比其他高速賽道
print("\n### 7. 對比其他高速賽道的 max_speed 占比")
print("-"*80)

high_speed_tracks = ["Great Britain", "Italy", "Belgium", "Saudi Arabia"]
track_max_speed_importance = {}

for track in high_speed_tracks:
    model_path = Path(f"models/track_specific_v3.3/{track}.pkl")
    if model_path.exists():
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        importances = model.feature_importances_
        max_speed_idx = 7  # max_speed 是第 8 個特徵（0-indexed）
        max_speed_imp = importances[max_speed_idx] * 100
        track_max_speed_importance[track] = max_speed_imp
        
        print(f"{track:20s} max_speed 占比: {max_speed_imp:6.2f}%")

if track_max_speed_importance:
    gb_importance = track_max_speed_importance.get("Great Britain", 0)
    others_avg = np.mean([v for k, v in track_max_speed_importance.items() if k != "Great Britain"])
    
    print(f"\nGreat Britain max_speed: {gb_importance:.2f}%")
    print(f"其他高速賽道平均:     {others_avg:.2f}%")
    print(f"差異:                  {gb_importance - others_avg:.2f}%")
    
    if gb_importance > others_avg * 3:
        print("❌ Great Britain 的 max_speed 占比異常高（超過 3 倍）！")

# 8. 結論與建議
print("\n" + "="*80)
print("結論與建議")
print("="*80)

print("""
如果 max_speed 確實占比 55.50%，可能的原因：

1. **訓練數據異常**
   - 2022-2024 年 Great Britain 數據中 max_speed 碰巧與排位相關性極高
   - 可能存在數據質量問題（測速點位置變化、DRS 調整）

2. **賽道特定現象**
   - Silverstone 的長直道使得 max_speed 變異度高
   - 但這不應該壓倒 sector times 的重要性

3. **模型過度擬合**
   - XGBoost 在小樣本下過度擬合 max_speed 模式
   - 2025 年這個模式失效

建議的解決方案：

✅ 方案 1: 添加 max_speed 相關的交互特徵
   - max_speed_lap_ratio = max_speed / ideal_lap
   - max_speed_s2_ratio = max_speed / ideal_s2
   - 提供多樣化的速度表示

✅ 方案 2: 限制 max_speed 權重
   - XGBoost feature_weights: {'max_speed': 0.3}
   - 強制模型更多使用 sector times

✅ 方案 3: Great Britain 專用特徵集
   - 移除 max_speed，只用 sector times + apex speeds
   - 添加更多交互特徵來補償
""")
