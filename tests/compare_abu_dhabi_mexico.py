#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿布達比 vs 墨西哥 - 完整對比分析
為何阿布達比 R² 只有 0.5467 而非 0.80+？
"""
import pickle
import sys
from pathlib import Path

# 設定輸出編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 載入兩個模型
abu_dhabi_path = Path('models/track_specific_v3/Abu Dhabi.pkl')
mexico_path = Path('models/track_specific_v3/Mexico.pkl')

with open(abu_dhabi_path, 'rb') as f:
    abu_data = pickle.load(f)

with open(mexico_path, 'rb') as f:
    mex_data = pickle.load(f)

print("="*80)
print("阿布達比（Abu Dhabi）vs 墨西哥（Mexico）深度對比分析")
print("="*80)

# 效能對比
abu_perf = abu_data['performance']
mex_perf = mex_data['performance']

print(f"\n{'='*80}")
print("【效能指標對比】")
print(f"{'='*80}")
print(f"\n{'指標':<25} {'阿布達比':>12} {'墨西哥':>12} {'差異':>12} {'%變化':>10}")
print("-"*80)
print(f"{'測試 R²':<25} {abu_perf['test_r2']:>12.4f} {mex_perf['test_r2']:>12.4f} {abu_perf['test_r2']-mex_perf['test_r2']:>+12.4f} {((abu_perf['test_r2']/mex_perf['test_r2'])-1)*100:>+9.1f}%")
print(f"{'測試 MAE (秒)':<25} {abu_perf['test_mae']:>12.3f} {mex_perf['test_mae']:>12.3f} {abu_perf['test_mae']-mex_perf['test_mae']:>+12.3f} {((abu_perf['test_mae']/mex_perf['test_mae'])-1)*100:>+9.1f}%")
print(f"{'訓練 MAE (秒)':<25} {abu_perf['train_mae']:>12.3f} {mex_perf['train_mae']:>12.3f} {abu_perf['train_mae']-mex_perf['train_mae']:>+12.3f} {((abu_perf['train_mae']/mex_perf['train_mae'])-1)*100:>+9.1f}%")
print(f"{'總樣本數':<25} {abu_perf['samples']:>12} {mex_perf['samples']:>12} {abu_perf['samples']-mex_perf['samples']:>+12} {((abu_perf['samples']/mex_perf['samples'])-1)*100:>+9.1f}%")
print(f"{'訓練樣本':<25} {abu_perf['train_samples']:>12} {mex_perf['train_samples']:>12} {abu_perf['train_samples']-mex_perf['train_samples']:>+12} {((abu_perf['train_samples']/mex_perf['train_samples'])-1)*100:>+9.1f}%")
print(f"{'測試樣本':<25} {abu_perf['test_samples']:>12} {mex_perf['test_samples']:>12} {abu_perf['test_samples']-mex_perf['test_samples']:>+12} {((abu_perf['test_samples']/mex_perf['test_samples'])-1)*100:>+9.1f}%")

# 特徵重要性對比
abu_feat = abu_perf['feature_importances']
mex_feat = mex_perf['feature_importances']

feature_names_zh = {
    'ideal_s1': 'Sector 1 最佳時間',
    'ideal_s2': 'Sector 2 最佳時間',
    'ideal_s3': 'Sector 3 最佳時間',
    'ideal_lap': 'FP3 最佳圈速',
    'low_speed_apex': '低速彎頂點速度',
    'mid_speed_apex': '中速彎頂點速度',
    'high_speed_apex': '高速彎頂點速度',
    'max_speed': '最高速度'
}

print(f"\n{'='*80}")
print("【特徵重要性對比】")
print(f"{'='*80}")
print(f"\n{'特徵':<20} {'阿布達比':>12} {'墨西哥':>12} {'差異':>12} {'趨勢':<6} {'%變化':>10}")
print("-"*80)

# 按阿布達比重要性排序
for feature in sorted(abu_feat.keys(), key=lambda x: abu_feat[x], reverse=True):
    abu_imp = abu_feat[feature]
    mex_imp = mex_feat[feature]
    diff = abu_imp - mex_imp
    pct_change = ((abu_imp / mex_imp) - 1) * 100 if mex_imp > 0 else 0
    
    if abs(diff) > 0.10:
        trend = "🔴 大幅"
    elif abs(diff) > 0.05:
        trend = "⚠️  中度"
    else:
        trend = "✓ 相近"
    
    zh_name = feature_names_zh.get(feature, feature)
    print(f"{feature:<20} {abu_imp:>11.2%} {mex_imp:>11.2%} {diff:>+11.2%}  {trend:<6} {pct_change:>+9.1f}%")
    print(f"  └─ {zh_name}")

# 群組分析
print(f"\n{'='*80}")
print("【特徵群組分析】")
print(f"{'='*80}")

abu_sectors = sum([abu_feat.get(f'ideal_s{i}', 0) for i in [1,2,3]])
mex_sectors = sum([mex_feat.get(f'ideal_s{i}', 0) for i in [1,2,3]])

abu_corners = sum([abu_feat.get(f'{s}_speed_apex', 0) for s in ['low', 'mid', 'high']])
mex_corners = sum([mex_feat.get(f'{s}_speed_apex', 0) for s in ['low', 'mid', 'high']])

print(f"\n{'群組':<25} {'阿布達比':>12} {'墨西哥':>12} {'差異':>12}")
print("-"*80)
print(f"{'Sector 時間 (S1+S2+S3)':<25} {abu_sectors:>11.2%} {mex_sectors:>11.2%} {abu_sectors-mex_sectors:>+11.2%}")
print(f"{'  - S1':<25} {abu_feat['ideal_s1']:>11.2%} {mex_feat['ideal_s1']:>11.2%} {abu_feat['ideal_s1']-mex_feat['ideal_s1']:>+11.2%}")
print(f"{'  - S2':<25} {abu_feat['ideal_s2']:>11.2%} {mex_feat['ideal_s2']:>11.2%} {abu_feat['ideal_s2']-mex_feat['ideal_s2']:>+11.2%}")
print(f"{'  - S3':<25} {abu_feat['ideal_s3']:>11.2%} {mex_feat['ideal_s3']:>11.2%} {abu_feat['ideal_s3']-mex_feat['ideal_s3']:>+11.2%}")
print()
print(f"{'彎角速度總計':<25} {abu_corners:>11.2%} {mex_corners:>11.2%} {abu_corners-mex_corners:>+11.2%}")
print(f"{'  - 低速':<25} {abu_feat['low_speed_apex']:>11.2%} {mex_feat['low_speed_apex']:>11.2%} {abu_feat['low_speed_apex']-mex_feat['low_speed_apex']:>+11.2%}")
print(f"{'  - 中速':<25} {abu_feat['mid_speed_apex']:>11.2%} {mex_feat['mid_speed_apex']:>11.2%} {abu_feat['mid_speed_apex']-mex_feat['mid_speed_apex']:>+11.2%}")
print(f"{'  - 高速':<25} {abu_feat['high_speed_apex']:>11.2%} {mex_feat['high_speed_apex']:>11.2%} {abu_feat['high_speed_apex']-mex_feat['high_speed_apex']:>+11.2%}")
print()
print(f"{'其他特徵':<25}")
print(f"{'  - 最高速':<25} {abu_feat['max_speed']:>11.2%} {mex_feat['max_speed']:>11.2%} {abu_feat['max_speed']-mex_feat['max_speed']:>+11.2%}")
print(f"{'  - 理想圈速':<25} {abu_feat['ideal_lap']:>11.2%} {mex_feat['ideal_lap']:>11.2%} {abu_feat['ideal_lap']-mex_feat['ideal_lap']:>+11.2%}")

# 關鍵發現
print(f"\n{'='*80}")
print("【關鍵發現：為何阿布達比 R² 僅 0.5467？】")
print(f"{'='*80}")

findings = []

# 發現 1: S2 過度主導
if abu_feat['ideal_s2'] > 0.40:
    findings.append({
        'priority': 1,
        'title': 'S2 過度主導',
        'detail': f"阿布達比的 S2 重要性高達 {abu_feat['ideal_s2']:.2%}，遠超墨西哥的 {mex_feat['ideal_s2']:.2%}",
        'impact': '單一特徵過度主導導致模型過度依賴 S2，忽略其他重要特徵'
    })

# 發現 2: S1 重要性異常低
if abu_feat['ideal_s1'] < 0.10:
    findings.append({
        'priority': 2,
        'title': 'S1 重要性異常偏低',
        'detail': f"阿布達比的 S1 僅 {abu_feat['ideal_s1']:.2%}，墨西哥為 {mex_feat['ideal_s1']:.2%}（下降 {((abu_feat['ideal_s1']/mex_feat['ideal_s1'])-1)*100:.1f}%）",
        'impact': 'S1 對排位賽的預測能力被低估，可能是數據品質問題'
    })

# 發現 3: Ideal Lap 重要性偏高
if abu_feat['ideal_lap'] > mex_feat['ideal_lap'] * 2:
    findings.append({
        'priority': 3,
        'title': 'Ideal Lap 占比異常高',
        'detail': f"阿布達比 {abu_feat['ideal_lap']:.2%} vs 墨西哥 {mex_feat['ideal_lap']:.2%}（高出 {((abu_feat['ideal_lap']/mex_feat['ideal_lap'])-1)*100:.1f}%）",
        'impact': 'Ideal Lap 與 Sector 時間高度相關，可能導致多重共線性問題'
    })

# 發現 4: 測試 MAE 較高
if abu_perf['test_mae'] > mex_perf['test_mae'] * 1.2:
    findings.append({
        'priority': 4,
        'title': '測試誤差偏高',
        'detail': f"測試 MAE {abu_perf['test_mae']:.3f}秒 vs 墨西哥 {mex_perf['test_mae']:.3f}秒（高出 {((abu_perf['test_mae']/mex_perf['test_mae'])-1)*100:.1f}%）",
        'impact': '預測誤差大，表示模型泛化能力不足'
    })

# 顯示發現
for i, finding in enumerate(findings, 1):
    print(f"\n🔍 發現 {i}：{finding['title']}")
    print(f"   詳情：{finding['detail']}")
    print(f"   影響：{finding['impact']}")

# 建議
print(f"\n{'='*80}")
print("【改進建議】")
print(f"{'='*80}")

print("\n1. 數據品質檢查")
print("   - 檢查阿布達比 2022-2024 的 S1 數據是否異常")
print("   - 確認是否有缺失值或極端離群值")

print("\n2. 特徵工程優化")
print("   - 考慮移除 ideal_lap（與 S1+S2+S3 高度相關）")
print("   - 增加 Sector 時間的交互特徵（例如 S1/S2 比率）")

print("\n3. 模型參數調整")
print("   - 增加 max_depth 允許更複雜的特徵交互")
print("   - 調整 min_child_weight 降低 S2 的過度主導")

print("\n4. 樣本量分析")
print(f"   - 當前訓練樣本：{abu_perf['train_samples']} 個")
print(f"   - 建議：檢查樣本分佈是否均衡（各年份、各車隊）")

print(f"\n{'='*80}")
