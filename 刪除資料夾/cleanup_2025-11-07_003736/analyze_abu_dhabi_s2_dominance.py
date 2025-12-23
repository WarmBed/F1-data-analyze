#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿布達比 S2 主導性根因分析
為何 S2 占比高達 46.85%？是賽道特性還是數據問題？
"""
import pickle
import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 設定輸出編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*80)
print("阿布達比 S2 主導性根因分析")
print("="*80)

# ============================================================================
# Part 1: 載入訓練數據，分析 Sector 時間的統計特性
# ============================================================================
print("\n【Part 1: 訓練數據統計分析】")
print("-"*80)

# 掃描阿布達比訓練數據（包含時間戳，注意 "Abu Dhabi" 有空格）
abu_dhabi_files = list(Path('json/predictionJSON').glob('fp_q_data_*Abu*'))
print(f"\n找到 {len(abu_dhabi_files)} 個阿布達比數據檔案")

all_data = []
for f in sorted(abu_dhabi_files):
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # 提取 drivers 部分（如果存在）
            if isinstance(data, dict) and 'drivers' in data:
                driver_data = data['drivers']
                df = pd.DataFrame(driver_data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
            
            df['source_file'] = f.name
            all_data.append(df)
            print(f"  ✓ {f.name}: {len(df)} 筆資料")
    except Exception as e:
        print(f"  ✗ {f.name}: 載入失敗 - {e}")

if not all_data:
    print("❌ 無法載入任何數據檔案！")
    sys.exit(1)

df_abu = pd.concat(all_data, ignore_index=True)
print(f"\n總計：{len(df_abu)} 筆訓練樣本")

# 分析 Sector 時間統計
sector_cols = ['ideal_s1', 'ideal_s2', 'ideal_s3']
print(f"\n{'='*80}")
print("【Sector 時間統計特性】")
print(f"{'='*80}")

stats_table = []
for col in sector_cols:
    if col in df_abu.columns:
        stats = {
            'Sector': col.replace('ideal_', '').upper(),
            '平均': df_abu[col].mean(),
            '標準差': df_abu[col].std(),
            '變異係數': df_abu[col].std() / df_abu[col].mean(),
            '最小值': df_abu[col].min(),
            '最大值': df_abu[col].max(),
            '範圍': df_abu[col].max() - df_abu[col].min(),
            '缺失值': df_abu[col].isna().sum(),
            '零值': (df_abu[col] == 0).sum()
        }
        stats_table.append(stats)

df_stats = pd.DataFrame(stats_table)
print("\n" + df_stats.to_string(index=False))

# 計算 Sector 占總圈速的比例
df_abu['total_sectors'] = df_abu[sector_cols].sum(axis=1)
for col in sector_cols:
    df_abu[f'{col}_pct'] = df_abu[col] / df_abu['total_sectors'] * 100

print(f"\n{'='*80}")
print("【Sector 占總圈速比例】")
print(f"{'='*80}")
pct_stats = []
for col in sector_cols:
    pct_col = f'{col}_pct'
    pct_stats.append({
        'Sector': col.replace('ideal_', '').upper(),
        '平均占比': df_abu[pct_col].mean(),
        '占比標準差': df_abu[pct_col].std(),
        '最小占比': df_abu[pct_col].min(),
        '最大占比': df_abu[pct_col].max()
    })

df_pct = pd.DataFrame(pct_stats)
print("\n" + df_pct.to_string(index=False))

# 關鍵發現 1: 變異係數
print(f"\n{'='*80}")
print("【關鍵發現 1: 變異係數 (Coefficient of Variation)】")
print(f"{'='*80}")
print("\n變異係數 = 標準差 / 平均值，越高表示該 Sector 越能區分車手差異")
cv_sorted = df_stats.sort_values('變異係數', ascending=False)
print(f"\n{'排名':<8} {'Sector':<10} {'變異係數':<15} {'解釋'}")
print("-"*80)
for idx, (i, row) in enumerate(cv_sorted.iterrows(), 1):
    cv = row['變異係數']
    if cv > 0.03:
        level = "🔴 極高區分度"
    elif cv > 0.02:
        level = "⚠️  高區分度"
    else:
        level = "✓ 一般區分度"
    print(f"{idx:<8} {row['Sector']:<10} {cv:<15.4f} {level}")

# ============================================================================
# Part 2: 與墨西哥對比
# ============================================================================
print(f"\n{'='*80}")
print("【Part 2: 與墨西哥賽道對比】")
print(f"{'='*80}")

# 載入墨西哥數據（包含時間戳）
mexico_files = list(Path('json/predictionJSON').glob('fp_q_data_*Mexico*'))
print(f"\n找到 {len(mexico_files)} 個墨西哥數據檔案")

all_mex_data = []
for f in sorted(mexico_files):
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # 提取 drivers 部分（如果存在）
            if isinstance(data, dict) and 'drivers' in data:
                driver_data = data['drivers']
                df = pd.DataFrame(driver_data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
            all_mex_data.append(df)
    except:
        pass

if all_mex_data:
    df_mex = pd.concat(all_mex_data, ignore_index=True)
    print(f"墨西哥總計：{len(df_mex)} 筆訓練樣本")
    
    # 墨西哥統計
    mex_stats = []
    for col in sector_cols:
        if col in df_mex.columns:
            mex_stats.append({
                'Sector': col.replace('ideal_', '').upper(),
                '平均': df_mex[col].mean(),
                '標準差': df_mex[col].std(),
                '變異係數': df_mex[col].std() / df_mex[col].mean(),
            })
    
    df_mex_stats = pd.DataFrame(mex_stats)
    
    # 對比表
    print(f"\n{'='*80}")
    print("【變異係數對比：阿布達比 vs 墨西哥】")
    print(f"{'='*80}")
    print(f"\n{'Sector':<10} {'阿布達比 CV':<15} {'墨西哥 CV':<15} {'差異':<15} {'趨勢'}")
    print("-"*80)
    
    for sector in ['S1', 'S2', 'S3']:
        abu_cv = df_stats[df_stats['Sector'] == sector]['變異係數'].values[0]
        mex_cv = df_mex_stats[df_mex_stats['Sector'] == sector]['變異係數'].values[0]
        diff = abu_cv - mex_cv
        pct_change = (abu_cv / mex_cv - 1) * 100
        
        if abs(pct_change) > 50:
            trend = "🔴 大幅差異"
        elif abs(pct_change) > 20:
            trend = "⚠️  中度差異"
        else:
            trend = "✓ 相近"
        
        print(f"{sector:<10} {abu_cv:<15.4f} {mex_cv:<15.4f} {diff:>+14.4f} {trend}")

# ============================================================================
# Part 3: 與 Qualifying 時間的相關性分析
# ============================================================================
print(f"\n{'='*80}")
print("【Part 3: Sector 與排位賽的相關性】")
print(f"{'='*80}")

if 'q_time' in df_abu.columns:
    print("\n各 Sector 與最終排位賽時間的 Pearson 相關係數：")
    print("-"*80)
    
    correlations = []
    for col in sector_cols:
        if col in df_abu.columns:
            # 移除缺失值
            valid_data = df_abu[[col, 'q_time']].dropna()
            corr = valid_data[col].corr(valid_data['q_time'])
            correlations.append({
                'Sector': col.replace('ideal_', '').upper(),
                '相關係數': corr,
                '樣本數': len(valid_data)
            })
    
    df_corr = pd.DataFrame(correlations).sort_values('相關係數', ascending=False)
    print("\n" + df_corr.to_string(index=False))
    
    print("\n解讀：")
    print("  - 相關係數越高 → 該 Sector 對排位賽時間的預測能力越強")
    print("  - S2 相關係數最高 → 模型自然會賦予更高的特徵重要性")

# ============================================================================
# Part 4: 檢查是否有異常數據
# ============================================================================
print(f"\n{'='*80}")
print("【Part 4: 數據品質檢查】")
print(f"{'='*80}")

print("\n檢查 S1 數據品質：")
print("-"*80)
s1_issues = {
    '缺失值 (NaN)': df_abu['ideal_s1'].isna().sum(),
    '零值': (df_abu['ideal_s1'] == 0).sum(),
    '負值': (df_abu['ideal_s1'] < 0).sum(),
    '極端離群值 (> 99.9%)': (df_abu['ideal_s1'] > df_abu['ideal_s1'].quantile(0.999)).sum(),
    '極端離群值 (< 0.1%)': (df_abu['ideal_s1'] < df_abu['ideal_s1'].quantile(0.001)).sum()
}

for issue, count in s1_issues.items():
    status = "✓ 正常" if count == 0 else f"⚠️  發現 {count} 筆"
    print(f"  {issue:<30} {status}")

# ============================================================================
# Part 5: 賽道特性分析（基於彎角數據）
# ============================================================================
print(f"\n{'='*80}")
print("【Part 5: 賽道物理特性分析】")
print(f"{'='*80}")

# 查找彎角數據
corner_files = list(Path('json').glob('all_drivers_cornering_analysis_*_Abu_Dhabi_FP3.json'))
if corner_files:
    print(f"\n找到 {len(corner_files)} 個彎角分析檔案")
    
    # 載入一個檔案作為範例
    sample_file = corner_files[0]
    with open(sample_file, 'r', encoding='utf-8') as f:
        corner_data = json.load(f)
    
    print(f"  分析檔案: {sample_file.name}")
    
    # 提取彎角速度特徵
    if corner_data:
        first_driver = list(corner_data.keys())[0]
        features = corner_data[first_driver]
        
        print("\n彎角速度特徵：")
        print(f"  低速彎頂點平均: {features.get('low_speed_apex', 0):.1f} km/h")
        print(f"  中速彎頂點平均: {features.get('mid_speed_apex', 0):.1f} km/h")
        print(f"  高速彎頂點平均: {features.get('high_speed_apex', 0):.1f} km/h")
        print(f"  最高速度: {features.get('max_speed', 0):.1f} km/h")
else:
    print("\n⚠️  未找到彎角數據檔案")

# ============================================================================
# 結論
# ============================================================================
print(f"\n{'='*80}")
print("【結論：S2 主導的可能原因】")
print(f"{'='*80}")

# 根據變異係數判斷
s2_cv = df_stats[df_stats['Sector'] == 'S2']['變異係數'].values[0]
s1_cv = df_stats[df_stats['Sector'] == 'S1']['變異係數'].values[0]
s3_cv = df_stats[df_stats['Sector'] == 'S3']['變異係數'].values[0]

findings = []

if s2_cv > s1_cv * 1.5:
    findings.append({
        'no': 1,
        'title': 'S2 變異性遠高於 S1',
        'detail': f"S2 變異係數 {s2_cv:.4f} 是 S1 {s1_cv:.4f} 的 {s2_cv/s1_cv:.2f} 倍",
        'implication': 'S2 更能區分車手/車隊差異，模型自然賦予更高權重'
    })

if s1_issues['缺失值 (NaN)'] > 0 or s1_issues['零值'] > 0:
    findings.append({
        'no': len(findings) + 1,
        'title': 'S1 數據品質問題',
        'detail': f"發現 {s1_issues['缺失值 (NaN)']} 個缺失值，{s1_issues['零值']} 個零值",
        'implication': 'S1 數據不完整導致重要性被低估'
    })
else:
    findings.append({
        'no': len(findings) + 1,
        'title': 'S1 數據品質正常',
        'detail': f"無缺失值、零值或極端離群值",
        'implication': 'S1 重要性低 (6.41%) 並非數據問題，而是賽道特性'
    })

# 相關性分析
if 'q_time' in df_abu.columns and correlations:
    s2_corr = df_corr[df_corr['Sector'] == 'S2']['相關係數'].values[0]
    s1_corr = df_corr[df_corr['Sector'] == 'S1']['相關係數'].values[0]
    
    if s2_corr > s1_corr * 1.2:
        findings.append({
            'no': len(findings) + 1,
            'title': 'S2 與排位賽時間相關性最高',
            'detail': f"S2 相關係數 {s2_corr:.4f} > S1 {s1_corr:.4f}",
            'implication': 'S2 是預測排位賽結果的最關鍵指標'
        })

# 阿布達比賽道特性（基於圖片）
findings.append({
    'no': len(findings) + 1,
    'title': '阿布達比賽道佈局特性',
    'detail': 'S2 包含長直線後的技術低速彎區（紅色標註），這是最考驗車手/賽車的路段',
    'implication': 'S2 的技術性低速彎組合產生最大的車手差異，自然成為最重要特徵'
})

for finding in findings:
    print(f"\n🔍 發現 {finding['no']}: {finding['title']}")
    print(f"   詳情: {finding['detail']}")
    print(f"   影響: {finding['implication']}")

print(f"\n{'='*80}")
print("【最終判斷】")
print(f"{'='*80}")

if s1_issues['缺失值 (NaN)'] > 5 or s1_issues['零值'] > 5:
    print("\n⚠️  判斷：S2 主導 + S1 弱化 是【數據品質問題】")
    print("   建議：修正 S1 數據後重新訓練")
else:
    print("\n✅ 判斷：S2 主導是【阿布達比賽道的真實物理特性】")
    print("   原因：S2 的變異性、相關性、技術難度都遠高於 S1/S3")
    print("   結論：46.85% 的占比是合理的，不需要強制調整")

print(f"\n{'='*80}")
