#!/usr/bin/env python3
"""
分析 2025 年 FP2→Q 預測模型的準確度
生成詳細的 Markdown 報告
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

def analyze_fp2_q_predictions():
    """分析所有 2025 年 FP2→Q 預測檔案"""
    
    json_dir = Path("json")
    prediction_files = sorted(json_dir.glob("fp2_qualifying_prediction_2025_*.json"))
    
    if not prediction_files:
        print("找不到任何 2025 年 FP2→Q 預測檔案")
        return
    
    print(f"找到 {len(prediction_files)} 個預測檔案")
    
    # 儲存每場賽事的分析結果
    race_results = []
    all_predictions = []
    
    for json_file in prediction_files:
        race_name = json_file.stem.replace("fp2_qualifying_prediction_2025_", "")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            predictions = data.get('predictions', [])
            
            # 過濾有實際結果的預測
            valid_predictions = [p for p in predictions if p.get('actual_q_time') is not None]
            
            if not valid_predictions:
                print(f"⚠️  {race_name}: 無實際排位賽結果")
                race_results.append({
                    'race': race_name,
                    'has_actual': False,
                    'driver_count': len(predictions),
                    'model_r2': metadata.get('model_r2', 0),
                    'model_mae': metadata.get('model_mae', 0)
                })
                continue
            
            # 計算誤差
            time_errors = []
            rank_errors = []
            
            for pred in valid_predictions:
                # 時間誤差 (絕對值)
                time_error = abs(pred['predicted_time'] - pred['actual_q_time'])
                time_errors.append(time_error)
                
                # 排名誤差 (絕對值)
                if pred.get('fp2_predicted_rank') and pred.get('actual_q_rank'):
                    rank_error = abs(pred['fp2_predicted_rank'] - pred['actual_q_rank'])
                    rank_errors.append(rank_error)
                
                # 儲存每個預測的詳細資料
                all_predictions.append({
                    'race': race_name,
                    'driver': pred['driver'],
                    'team': pred['team'],
                    'fp2_time': pred['fp2_time'],
                    'predicted_time': pred['predicted_time'],
                    'actual_time': pred['actual_q_time'],
                    'time_error': time_error,
                    'improvement': pred['improvement'],
                    'fp2_rank': pred.get('fp2_predicted_rank'),
                    'predicted_rank': pred['rank'],
                    'actual_rank': pred.get('actual_q_rank'),
                    'rank_error': rank_error if pred.get('actual_q_rank') else None
                })
            
            # 計算該場賽事的統計數據
            mae = np.mean(time_errors)
            rmse = np.sqrt(np.mean([e**2 for e in time_errors]))
            max_error = max(time_errors)
            min_error = min(time_errors)
            
            avg_rank_error = np.mean(rank_errors) if rank_errors else None
            
            # 計算前3名預測準確度
            top3_correct = 0
            predicted_top3 = [p['driver'] for p in predictions[:3]]
            actual_top3 = sorted(valid_predictions, key=lambda x: x['actual_q_time'])[:3]
            actual_top3_drivers = [p['driver'] for p in actual_top3]
            
            for driver in predicted_top3:
                if driver in actual_top3_drivers:
                    top3_correct += 1
            
            race_results.append({
                'race': race_name,
                'has_actual': True,
                'driver_count': len(valid_predictions),
                'mae': mae,
                'rmse': rmse,
                'max_error': max_error,
                'min_error': min_error,
                'avg_rank_error': avg_rank_error,
                'top3_accuracy': top3_correct / 3 * 100,
                'model_r2': metadata.get('model_r2', 0),
                'model_mae': metadata.get('model_mae', 0)
            })
            
            print(f"✅ {race_name}: MAE = {mae:.3f}s, 排名誤差 = {avg_rank_error:.2f}")
            
        except Exception as e:
            print(f"❌ {race_name}: 處理失敗 - {e}")
            continue
    
    # 生成 Markdown 報告
    generate_markdown_report(race_results, all_predictions)
    
    return race_results, all_predictions

def generate_markdown_report(race_results, all_predictions):
    """生成詳細的 Markdown 報告"""
    
    md_content = []
    
    # 標題
    md_content.append("# 📊 FP2→Q 預測模型準確度分析報告 (2025 賽季)")
    md_content.append("")
    md_content.append(f"**生成時間**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    md_content.append("")
    md_content.append("---")
    md_content.append("")
    
    # 總覽
    valid_races = [r for r in race_results if r['has_actual']]
    invalid_races = [r for r in race_results if not r['has_actual']]
    
    md_content.append("## 📋 總覽")
    md_content.append("")
    md_content.append(f"- **總賽事數**: {len(race_results)} 場")
    md_content.append(f"- **有實際結果**: {len(valid_races)} 場")
    md_content.append(f"- **無實際結果**: {len(invalid_races)} 場")
    md_content.append("")
    
    if valid_races:
        overall_mae = np.mean([r['mae'] for r in valid_races])
        overall_rmse = np.mean([r['rmse'] for r in valid_races])
        overall_rank_error = np.mean([r['avg_rank_error'] for r in valid_races if r['avg_rank_error']])
        overall_top3_acc = np.mean([r['top3_accuracy'] for r in valid_races])
        
        md_content.append("### 🎯 整體表現指標")
        md_content.append("")
        md_content.append(f"- **平均時間誤差 (MAE)**: {overall_mae:.3f} 秒")
        md_content.append(f"- **平均 RMSE**: {overall_rmse:.3f} 秒")
        md_content.append(f"- **平均排名誤差**: {overall_rank_error:.2f} 位")
        md_content.append(f"- **前3名預測準確度**: {overall_top3_acc:.1f}%")
        md_content.append("")
    
    md_content.append("---")
    md_content.append("")
    
    # 各場賽事詳細結果
    md_content.append("## 📊 各場賽事詳細分析")
    md_content.append("")
    
    # 按 MAE 排序（由好到壞）
    sorted_races = sorted([r for r in race_results if r['has_actual']], 
                         key=lambda x: x['mae'])
    
    # 創建表格
    md_content.append("| 排名 | 賽事 | 車手數 | MAE (秒) | RMSE (秒) | 排名誤差 | 前3準確度 | 模型 R² |")
    md_content.append("|------|------|--------|----------|-----------|----------|-----------|---------|")
    
    for rank, race in enumerate(sorted_races, 1):
        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        top3_acc = f"{race['top3_accuracy']:.0f}%" if race['top3_accuracy'] else "N/A"
        rank_err = f"{race['avg_rank_error']:.2f}" if race['avg_rank_error'] else "N/A"
        
        md_content.append(
            f"| {emoji} {rank} | **{race['race']}** | {race['driver_count']} | "
            f"{race['mae']:.3f} | {race['rmse']:.3f} | {rank_err} | "
            f"{top3_acc} | {race['model_r2']:.3f} |"
        )
    
    md_content.append("")
    md_content.append("---")
    md_content.append("")
    
    # 最佳與最差表現
    if sorted_races:
        best_race = sorted_races[0]
        worst_race = sorted_races[-1]
        
        md_content.append("## 🏆 極端表現分析")
        md_content.append("")
        md_content.append("### ✅ 最佳預測")
        md_content.append("")
        md_content.append(f"- **賽事**: {best_race['race']}")
        md_content.append(f"- **MAE**: {best_race['mae']:.3f} 秒")
        md_content.append(f"- **排名誤差**: {best_race['avg_rank_error']:.2f} 位")
        md_content.append(f"- **前3準確度**: {best_race['top3_accuracy']:.0f}%")
        md_content.append("")
        md_content.append("### ⚠️ 最差預測")
        md_content.append("")
        md_content.append(f"- **賽事**: {worst_race['race']}")
        md_content.append(f"- **MAE**: {worst_race['mae']:.3f} 秒")
        md_content.append(f"- **排名誤差**: {worst_race['avg_rank_error']:.2f} 位")
        md_content.append(f"- **前3準確度**: {worst_race['top3_accuracy']:.0f}%")
        md_content.append("")
    
    md_content.append("---")
    md_content.append("")
    
    # 車手表現分析
    if all_predictions:
        driver_stats = {}
        for pred in all_predictions:
            driver = pred['driver']
            if driver not in driver_stats:
                driver_stats[driver] = {
                    'races': 0,
                    'total_error': 0,
                    'errors': []
                }
            driver_stats[driver]['races'] += 1
            driver_stats[driver]['total_error'] += pred['time_error']
            driver_stats[driver]['errors'].append(pred['time_error'])
        
        # 計算每位車手的平均誤差
        for driver in driver_stats:
            driver_stats[driver]['avg_error'] = driver_stats[driver]['total_error'] / driver_stats[driver]['races']
            driver_stats[driver]['std_error'] = np.std(driver_stats[driver]['errors'])
        
        # 排序
        sorted_drivers = sorted(driver_stats.items(), key=lambda x: x[1]['avg_error'])
        
        md_content.append("## 👤 車手預測表現分析 (Top 10)")
        md_content.append("")
        md_content.append("*預測最準確的車手 (平均誤差最小)*")
        md_content.append("")
        md_content.append("| 排名 | 車手 | 參賽數 | 平均誤差 (秒) | 標準差 |")
        md_content.append("|------|------|--------|---------------|--------|")
        
        for rank, (driver, stats) in enumerate(sorted_drivers[:10], 1):
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            md_content.append(
                f"| {emoji} {rank} | **{driver}** | {stats['races']} | "
                f"{stats['avg_error']:.3f} | {stats['std_error']:.3f} |"
            )
        
        md_content.append("")
    
    md_content.append("---")
    md_content.append("")
    
    # 無實際結果的賽事
    if invalid_races:
        md_content.append("## ⚠️ 無實際排位賽結果的賽事")
        md_content.append("")
        md_content.append("以下賽事僅有 FP2 預測，尚無實際排位賽數據進行驗證：")
        md_content.append("")
        for race in invalid_races:
            md_content.append(f"- **{race['race']}** ({race['driver_count']} 位車手)")
        md_content.append("")
    
    md_content.append("---")
    md_content.append("")
    
    # 技術說明
    md_content.append("## 📖 技術說明")
    md_content.append("")
    md_content.append("### 指標定義")
    md_content.append("")
    md_content.append("- **MAE (Mean Absolute Error)**: 平均絕對誤差，越小越好")
    md_content.append("- **RMSE (Root Mean Square Error)**: 均方根誤差，對大誤差更敏感")
    md_content.append("- **排名誤差**: 預測排名與實際排名的平均差距")
    md_content.append("- **前3準確度**: 預測前3名中有多少位車手真的進入前3")
    md_content.append("- **模型 R²**: 模型訓練時的決定係數 (0-1，越接近1越好)")
    md_content.append("")
    md_content.append("### 分析方法")
    md_content.append("")
    md_content.append("1. **數據來源**: FP2 (第二次練習賽) 的 Quali Sim 圈速")
    md_content.append("2. **預測目標**: Q (排位賽) 的最終成績")
    md_content.append("3. **模型**: 基於 XGBoost 的機器學習模型 (v3.10)")
    md_content.append("4. **特徵**: 包含分段時間、彎道速度、極速等 14 個特徵")
    md_content.append("")
    md_content.append("### 數據更新")
    md_content.append("")
    md_content.append(f"- **分析日期**: {datetime.now().strftime('%Y年%m月%d日')}")
    md_content.append("- **賽季**: 2025 Formula 1 World Championship")
    md_content.append("")
    md_content.append("---")
    md_content.append("")
    md_content.append("*本報告由 F1 TelemetryStation Pro 自動生成*")
    
    # 寫入檔案
    output_file = Path("FP2_Q_Prediction_Accuracy_Report_2025.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    print(f"\n✅ Markdown 報告已生成: {output_file}")
    
    return output_file

if __name__ == "__main__":
    print("=" * 70)
    print("FP2→Q 預測模型準確度分析 (2025 賽季)")
    print("=" * 70)
    print()
    
    race_results, all_predictions = analyze_fp2_q_predictions()
    
    print("\n" + "=" * 70)
    print("分析完成！")
    print("=" * 70)
