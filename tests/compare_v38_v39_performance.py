#!/usr/bin/env python3
"""
V3.8 vs V3.9 性能對比分析

對比硬編碼 is_top_driver (V3.8) vs 動態計算 (V3.9) 的性能差異
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime


def load_results(version: str) -> dict:
    """載入訓練結果 JSON"""
    file_path = Path(f"v3.{version}_training_results.json")
    
    if not file_path.exists():
        print(f"❌ 找不到 {file_path}")
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_versions():
    """對比 V3.8 vs V3.9"""
    print("="*80)
    print("V3.8 vs V3.9 性能對比分析")
    print("="*80)
    
    # 載入數據
    v38 = load_results('8')
    v39 = load_results('9')
    
    if not v38 or not v39:
        print("\n❌ 缺少訓練結果檔案，請確認:")
        print("  - v3.8_training_results.json")
        print("  - v3.9_training_results.json")
        return
    
    # 提取結果
    v38_results = v38.get('results', {})
    v39_results = v39.get('results', {})
    
    # 找出共同賽道
    common_tracks = set(v38_results.keys()) & set(v39_results.keys())
    
    if not common_tracks:
        print("\n❌ 沒有共同的賽道數據")
        return
    
    print(f"\n共同賽道數量: {len(common_tracks)}/24")
    
    # 彙總統計
    comparison_data = []
    
    for track in sorted(common_tracks):
        v38_data = v38_results[track]
        v39_data = v39_results[track]
        
        comparison_data.append({
            'track': track,
            'v38_cv_mae': v38_data['cv_mae'],
            'v39_cv_mae': v39_data['cv_mae'],
            'v38_train_mae': v38_data['train_mae'],
            'v39_train_mae': v39_data['train_mae'],
            'v38_r2': v38_data['train_r2'],
            'v39_r2': v39_data['train_r2'],
            'cv_mae_diff': v39_data['cv_mae'] - v38_data['cv_mae'],
            'train_mae_diff': v39_data['train_mae'] - v38_data['train_mae'],
            'r2_diff': v39_data['train_r2'] - v38_data['train_r2']
        })
    
    df = pd.DataFrame(comparison_data)
    
    # 整體統計
    print("\n" + "="*80)
    print("整體性能對比")
    print("="*80)
    
    avg_v38_cv_mae = df['v38_cv_mae'].mean()
    avg_v39_cv_mae = df['v39_cv_mae'].mean()
    avg_v38_r2 = df['v38_r2'].mean()
    avg_v39_r2 = df['v39_r2'].mean()
    
    print(f"\n【CV MAE (交叉驗證誤差 - 越小越好)】")
    print(f"  V3.8 平均: {avg_v38_cv_mae:.3f}s")
    print(f"  V3.9 平均: {avg_v39_cv_mae:.3f}s")
    print(f"  差異: {avg_v39_cv_mae - avg_v38_cv_mae:+.3f}s ({(avg_v39_cv_mae/avg_v38_cv_mae - 1)*100:+.1f}%)")
    
    print(f"\n【訓練 R² (決定係數 - 越大越好)】")
    print(f"  V3.8 平均: {avg_v38_r2:.4f}")
    print(f"  V3.9 平均: {avg_v39_r2:.4f}")
    print(f"  差異: {avg_v39_r2 - avg_v38_r2:+.4f} ({(avg_v39_r2 - avg_v38_r2)*100:+.2f}%)")
    
    # 改進/退步統計
    improved = len(df[df['cv_mae_diff'] < 0])
    degraded = len(df[df['cv_mae_diff'] > 0])
    unchanged = len(df[df['cv_mae_diff'] == 0])
    
    print(f"\n【賽道改進統計】")
    print(f"  改進 (CV MAE 降低): {improved}/{len(common_tracks)} ({improved/len(common_tracks)*100:.1f}%)")
    print(f"  退步 (CV MAE 增加): {degraded}/{len(common_tracks)} ({degraded/len(common_tracks)*100:.1f}%)")
    print(f"  持平: {unchanged}/{len(common_tracks)}")
    
    # 詳細對比表
    print("\n" + "="*80)
    print("各賽道詳細對比 (按 CV MAE 差異排序)")
    print("="*80)
    print(f"\n{'賽道':<20} {'V3.8 CV MAE':<12} {'V3.9 CV MAE':<12} {'差異':<10} {'趨勢':<6} {'R² 差異':<10}")
    print("-"*80)
    
    df_sorted = df.sort_values('cv_mae_diff')
    
    for _, row in df_sorted.iterrows():
        trend = "✅ 改進" if row['cv_mae_diff'] < -0.01 else ("❌ 退步" if row['cv_mae_diff'] > 0.01 else "➖ 持平")
        
        print(f"{row['track']:<20} "
              f"{row['v38_cv_mae']:>6.3f}s      "
              f"{row['v39_cv_mae']:>6.3f}s      "
              f"{row['cv_mae_diff']:>+6.3f}s   "
              f"{trend:<6} "
              f"{row['r2_diff']:>+6.4f}")
    
    # Top 改進/退步
    print("\n" + "="*80)
    print("Top 5 改進賽道")
    print("="*80)
    top_improved = df_sorted.head(5)
    for i, row in enumerate(top_improved.itertuples(), 1):
        print(f"{i}. {row.track:<20} CV MAE: {row.v38_cv_mae:.3f}s → {row.v39_cv_mae:.3f}s "
              f"({row.cv_mae_diff:+.3f}s, {row.cv_mae_diff/row.v38_cv_mae*100:+.1f}%)")
    
    print("\n" + "="*80)
    print("Top 5 退步賽道")
    print("="*80)
    top_degraded = df_sorted.tail(5).iloc[::-1]
    for i, row in enumerate(top_degraded.itertuples(), 1):
        print(f"{i}. {row.track:<20} CV MAE: {row.v38_cv_mae:.3f}s → {row.v39_cv_mae:.3f}s "
              f"({row.cv_mae_diff:+.3f}s, {row.cv_mae_diff/row.v38_cv_mae*100:+.1f}%)")
    
    # is_top_driver 特徵重要性對比
    print("\n" + "="*80)
    print("is_top_driver 特徵重要性對比")
    print("="*80)
    print(f"\n{'賽道':<20} {'V3.8 重要性':<15} {'V3.9 重要性':<15} {'差異':<10}")
    print("-"*80)
    
    for track in sorted(common_tracks):
        v38_fi = v38_results[track].get('feature_importance', {}).get('is_top_driver', 0) * 100
        v39_fi = v39_results[track].get('feature_importance', {}).get('is_top_driver', 0) * 100
        diff = v39_fi - v38_fi
        
        print(f"{track:<20} {v38_fi:>6.2f}%         {v39_fi:>6.2f}%         {diff:>+6.2f}%")
    
    # 保存對比結果
    output_file = Path(f"v38_v39_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    comparison_summary = {
        'metadata': {
            'comparison_date': datetime.now().isoformat(),
            'v38_method': 'hardcoded_driver_list',
            'v39_method': 'dynamic_season_avg',
            'tracks_compared': len(common_tracks)
        },
        'overall': {
            'v38_avg_cv_mae': float(avg_v38_cv_mae),
            'v39_avg_cv_mae': float(avg_v39_cv_mae),
            'cv_mae_change': float(avg_v39_cv_mae - avg_v38_cv_mae),
            'cv_mae_change_pct': float((avg_v39_cv_mae/avg_v38_cv_mae - 1)*100),
            'v38_avg_r2': float(avg_v38_r2),
            'v39_avg_r2': float(avg_v39_r2),
            'r2_change': float(avg_v39_r2 - avg_v38_r2),
            'improved_tracks': int(improved),
            'degraded_tracks': int(degraded)
        },
        'track_details': df.to_dict('records')
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n[保存對比結果] {output_file}")
    
    # 結論
    print("\n" + "="*80)
    print("結論與建議")
    print("="*80)
    
    if avg_v39_cv_mae < avg_v38_cv_mae:
        print("\n✅ V3.9 整體表現優於 V3.8")
        print(f"   - CV MAE 平均降低 {abs(avg_v39_cv_mae - avg_v38_cv_mae):.3f}s ({abs((avg_v39_cv_mae/avg_v38_cv_mae - 1)*100):.1f}%)")
    elif avg_v39_cv_mae > avg_v38_cv_mae:
        print("\n⚠️  V3.9 整體表現略遜於 V3.8")
        print(f"   - CV MAE 平均增加 {abs(avg_v39_cv_mae - avg_v38_cv_mae):.3f}s ({abs((avg_v39_cv_mae/avg_v38_cv_mae - 1)*100):.1f}%)")
    else:
        print("\n➖ V3.9 與 V3.8 表現相當")
    
    print(f"\n改進率: {improved/len(common_tracks)*100:.1f}% 的賽道有改進")
    
    if improved > degraded:
        print("\n💡 建議：採用 V3.9")
        print("   理由：")
        print("   - 多數賽道表現改進")
        print("   - 動態計算無需每年手動維護")
        print("   - 自動適應車手實力變化")
    elif improved < degraded * 0.8:
        print("\n💡 建議：保留 V3.8")
        print("   理由：退步賽道數量顯著高於改進賽道")
    else:
        print("\n💡 建議：保留兩版本並行")
        print("   理由：")
        print("   - 性能差異不大")
        print("   - V3.9 的維護優勢值得考慮")
        print("   - 可根據特定賽道選擇版本")


if __name__ == '__main__':
    compare_versions()
