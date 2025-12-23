"""
快速分析 Great Britain max_speed 與排位結果的相關性
"""

import json
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

print("="*80)
print("Great Britain max_speed 相關性分析（簡化版）")
print("="*80)

# 從 2025 Great Britain 預測數據中提取實際值
gb_2025_file = Path("json/predictionJSON/race_21_Great Britain_20251102_200952.json")

if gb_2025_file.exists():
    print(f"\n載入 2025 Great Britain 數據: {gb_2025_file.name}")
    
    with open(gb_2025_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取實際數據
    max_speeds = []
    ideal_laps = []
    positions = []
    drivers = []
    
    if 'qualifying' in data and 'drivers' in data['qualifying']:
        for driver_data in data['qualifying']['drivers']:
            if isinstance(driver_data, dict):
                driver_name = driver_data.get('driver_name', 'unknown')
                position = driver_data.get('position')
                
                if 'track_features' in driver_data:
                    tf = driver_data['track_features']
                    max_speed = tf.get('max_speed')
                    ideal_lap = tf.get('ideal_lap')
                    
                    if max_speed and ideal_lap and position:
                        max_speeds.append(max_speed)
                        ideal_laps.append(ideal_lap)
                        positions.append(position)
                        drivers.append(driver_name)
    
    print(f"✅ 成功提取 {len(drivers)} 名車手數據")
    
    if len(drivers) > 0:
        # 轉換為 numpy 陣列
        max_speeds = np.array(max_speeds)
        ideal_laps = np.array(ideal_laps)
        positions = np.array(positions)
        
        print(f"\n### max_speed 統計")
        print(f"範圍: {max_speeds.min():.1f} - {max_speeds.max():.1f} km/h")
        print(f"平均: {max_speeds.mean():.1f} km/h")
        print(f"標準差: {max_speeds.std():.2f} km/h")
        print(f"變異係數: {(max_speeds.std() / max_speeds.mean())*100:.2f}%")
        
        print(f"\n### ideal_lap 統計")
        print(f"範圍: {ideal_laps.min():.3f} - {ideal_laps.max():.3f} s")
        print(f"平均: {ideal_laps.mean():.3f} s")
        print(f"標準差: {ideal_laps.std():.4f} s")
        print(f"變異係數: {(ideal_laps.std() / ideal_laps.mean())*100:.2f}%")
        
        # 相關性分析
        print(f"\n### max_speed 與排位結果的相關性")
        spearman_ms, p_ms = spearmanr(max_speeds, positions)
        print(f"Spearman 相關性: {spearman_ms:.4f} (p={p_ms:.4f})")
        
        # 負相關表示速度越快排位越前（position 數字越小）
        if spearman_ms < -0.7:
            print("✅ 強負相關：max_speed 越快，排位越前（合理）")
        elif spearman_ms < -0.5:
            print("⚠️  中等負相關")
        else:
            print("❌ 弱相關或正相關（異常！max_speed 不應該與排位無關）")
        
        print(f"\n### ideal_lap 與排位結果的相關性")
        spearman_lap, p_lap = spearmanr(ideal_laps, positions)
        print(f"Spearman 相關性: {spearman_lap:.4f} (p={p_lap:.4f})")
        
        # 正相關表示時間越長排位越後（position 數字越大）
        if spearman_lap > 0.9:
            print("✅ 強正相關：ideal_lap 越快（時間越短），排位越前（正常）")
        elif spearman_lap > 0.7:
            print("⚠️  中強正相關")
        else:
            print("❌ 弱相關（異常！）")
        
        # 對比
        print(f"\n### 預測能力對比")
        print(f"max_speed 相關性: {abs(spearman_ms):.4f}")
        print(f"ideal_lap 相關性: {abs(spearman_lap):.4f}")
        print(f"差異: {abs(spearman_lap) - abs(spearman_ms):.4f}")
        
        if abs(spearman_lap) > abs(spearman_ms):
            gap = abs(spearman_lap) - abs(spearman_ms)
            print(f"✅ ideal_lap 預測能力強 {gap:.4f}（理論上正確）")
        else:
            gap = abs(spearman_ms) - abs(spearman_lap)
            print(f"⚠️  max_speed 預測能力竟然強 {gap:.4f}（可能是模型過度擬合的根源）")
        
        # 計算 max_speed_lap_ratio
        max_speed_lap_ratio = max_speeds / ideal_laps
        spearman_ratio, p_ratio = spearmanr(max_speed_lap_ratio, positions)
        
        print(f"\n### max_speed_lap_ratio 交互特徵潛力")
        print(f"Spearman 相關性: {spearman_ratio:.4f} (p={p_ratio:.4f})")
        
        if abs(spearman_ratio) > max(abs(spearman_ms), abs(spearman_lap)):
            print("✅ 交互特徵 max_speed_lap_ratio 比單獨特徵更強！")
            print("💡 建議: 添加 max_speed_lap_ratio 到 v3.4")
        elif abs(spearman_ratio) > abs(spearman_ms):
            print("⚠️  交互特徵比 max_speed 強，但不如 ideal_lap")
        else:
            print("❌ 交互特徵沒有明顯優勢")
        
        # 顯示前 5 名數據
        print(f"\n### 前 5 名車手數據（驗證）")
        print(f"{'排名':<6} {'車手':<15} {'max_speed':>12} {'ideal_lap':>12} {'ratio':>12}")
        print("-"*70)
        
        # 按排位排序
        sorted_indices = np.argsort(positions)
        for i in sorted_indices[:5]:
            ratio = max_speeds[i] / ideal_laps[i]
            print(f"P{positions[i]:<5} {drivers[i]:<15} {max_speeds[i]:>10.1f} km/h {ideal_laps[i]:>10.3f}s {ratio:>11.2f}")

print("\n" + "="*80)
print("結論")
print("="*80)
print("""
如果 max_speed 與排位相關性弱於 ideal_lap：
  → 模型不應該過度依賴 max_speed（55.50% 異常）
  → 可能是訓練數據小樣本偶然性造成

如果 max_speed_lap_ratio 相關性更強：
  → 建議添加此交互特徵到 v3.4
  → 可能解決 Great Britain 預測問題
""")
