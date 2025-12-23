#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 v3.8 訓練結果報告
"""
import json
from pathlib import Path

def generate_report():
    results_file = Path("v3.8_training_results.json")
    
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data['metadata']
    results = data['results']
    
    # 計算統計數據
    cv_maes = [r['cv_mae'] for r in results.values()]
    train_maes = [r['train_mae'] for r in results.values()]
    train_r2s = [r['train_r2'] for r in results.values()]
    sample_counts = [r['sample_count'] for r in results.values()]
    
    avg_cv_mae = sum(cv_maes) / len(cv_maes)
    avg_train_mae = sum(train_maes) / len(train_maes)
    avg_train_r2 = sum(train_r2s) / len(train_r2s)
    total_samples = sum(sample_counts)
    
    # 排序賽道
    best_tracks = sorted(results.items(), key=lambda x: x[1]['cv_mae'])[:5]
    worst_tracks = sorted(results.items(), key=lambda x: x[1]['cv_mae'], reverse=True)[:5]
    
    # 生成報告
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║           F1T v3.8 賽道特定模型 - 訓練完成報告              ║
╚══════════════════════════════════════════════════════════════╝

【訓練概況】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
模型版本:            {metadata['version']}
訓練日期:            {metadata['training_date'][:10]}
特徵數量:            {metadata['feature_count']} 個
已訓練賽道:          {metadata['tracks_trained']} / 24
總訓練樣本數:        {total_samples}

【架構改進】
移除特徵 (零重要性):
  • track_avg_improvement_rate
  • adjusted_ideal_lap
  • driver_historical_improvement

【整體表現指標】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
平均交叉驗證 MAE:    {avg_cv_mae:.4f}s
平均訓練 MAE:        {avg_train_mae:.4f}s
平均訓練 R²:         {avg_train_r2:.4f}

【最佳表現賽道】(基於 CV MAE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for i, (track, r) in enumerate(best_tracks, 1):
        report += f"{i}. {track:20s}  CV MAE: {r['cv_mae']:.4f}s  (樣本: {r['sample_count']})\n"
    
    report += f"""
【最差表現賽道】(基於 CV MAE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for i, (track, r) in enumerate(worst_tracks, 1):
        report += f"{i}. {track:20s}  CV MAE: {r['cv_mae']:.4f}s  (樣本: {r['sample_count']})\n"
    
    # 未訓練賽道分析
    all_tracks = [
        'Australia', 'China', 'Japan', 'Bahrain', 'Saudi Arabia', 'Miami',
        'Emilia Romagna', 'Monaco', 'Spain', 'Canada', 'Austria', 
        'Great Britain', 'Belgium', 'Hungary', 'Netherlands', 'Italy',
        'Azerbaijan', 'Singapore', 'United States', 'Mexico', 'Brazil',
        'Las Vegas', 'Qatar', 'Abu Dhabi'
    ]
    
    trained_tracks = set(results.keys())
    missing_tracks = [t for t in all_tracks if t not in trained_tracks]
    
    report += f"""
【未訓練賽道】({len(missing_tracks)} 個)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for track in missing_tracks:
        report += f"  • {track}\n"
    
    if missing_tracks:
        report += """
原因: 缺少必要的數據檔案 (FP3 或 Corner Analysis JSON)
建議: 使用 CLI 功能 70 (FP-Q) 和功能 47 (Cornering) 生成遺漏數據

"""
    
    report += f"""
【優化配置】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Optuna 試驗次數:     500
並行工作數:          4
交叉驗證折數:        3
採樣器:              TPESampler
剪枝器:              MedianPruner

【模型儲存位置】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
模型檔案:            models/track_specific_v3.8/{{track}}.pkl
結果檔案:            v3.8_training_results.json

【後續步驟】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 使用 validate_v381_on_2025.py 在 2025 賽季數據上驗證模型
2. 針對缺失賽道生成必要的 JSON 數據
3. 比較 v3.8 與 v3.5 的性能差異
4. 分析移除特徵後的影響

╔══════════════════════════════════════════════════════════════╗
║                      訓練完成！                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    
    print(report)
    
    # 保存報告
    report_file = Path("v3.8_training_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"報告已保存至: {report_file}")

if __name__ == "__main__":
    generate_report()
