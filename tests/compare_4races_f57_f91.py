#!/usr/bin/env python3
"""
4 場賽事對比分析 - F57 vs F91
生成 4 個對比圖表和準確度分析
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 賽事配置
races = [
    {
        "name": "Japan",
        "display_name": "日本大獎賽 (Japanese GP)",
        "folder": "Japanese_Race",
        "real_avg": 90.5  # 估計值，需從圖表調整
    },
    {
        "name": "Abu_Dhabi",
        "display_name": "阿布達比大獎賽 (Abu Dhabi GP)",
        "folder": "Abu_Dhabi_Race",
        "real_avg": 89.0
    },
    {
        "name": "Las_Vegas",
        "display_name": "拉斯維加斯大獎賽 (Las Vegas GP)",
        "folder": "Las_Vegas_Race",
        "real_avg": 96.0  # 估計值
    },
    {
        "name": "Mexico",
        "display_name": "墨西哥大獎賽 (Mexico City GP)",
        "folder": "Mexico_City_Race",
        "real_avg": 80.0  # 估計值
    }
]

def load_f57_data(race_name):
    """載入 F57 預測數據"""
    pattern = f"combined_laptime_2025_{race_name}_R_*.json"
    files = sorted(Path("json").glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not files:
        return None
    
    with open(files[0], encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data['drivers']['1']['predictions']
    return [lap['predicted_time'] for lap in predictions if lap['predicted_time'] < 100]

def load_f91_data(race_name):
    """載入 F91 預測數據"""
    pattern = f"fp2_race_ml_prediction_v2_2025_{race_name}_*.json"
    files = sorted(Path("json").glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not files:
        return None
    
    with open(files[0], encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data['predictions']['1']['predicted_laps']
    return [float(v) for v in predictions.values() if float(v) < 100]

def create_comparison_chart(race_info, f57_data, f91_data, subplot_ax):
    """創建單一賽事對比圖表"""
    
    # 準備數據
    laps_f57 = list(range(1, len(f57_data) + 1))
    laps_f91 = list(range(1, len(f91_data) + 1))
    
    # 繪製圖表
    subplot_ax.plot(laps_f57, f57_data, 'b--', label='F57 (燃油+輪胎模型)', linewidth=2, alpha=0.8)
    subplot_ax.plot(laps_f91, f91_data, 'r-.', label='F91 (機器學習預測)', linewidth=2, alpha=0.8)
    subplot_ax.axhline(y=race_info['real_avg'], color='g', linestyle='-', 
                      label=f'Real 平均 ({race_info["real_avg"]:.1f}s)', linewidth=2)
    
    # 設置標題和標籤
    subplot_ax.set_title(race_info['display_name'], fontsize=14, fontweight='bold', pad=10)
    subplot_ax.set_xlabel('圈數', fontsize=11)
    subplot_ax.set_ylabel('圈速 (秒)', fontsize=11)
    subplot_ax.legend(loc='upper right', fontsize=9)
    subplot_ax.grid(True, alpha=0.3)
    
    # 計算誤差
    f57_avg = np.mean(f57_data)
    f91_avg = np.mean(f91_data)
    f57_error = abs(f57_avg - race_info['real_avg'])
    f91_error = abs(f91_avg - race_info['real_avg'])
    
    # 添加統計信息
    stats_text = f"F57 MAE: {f57_error:.3f}s\nF91 MAE: {f91_error:.3f}s"
    if f91_error < f57_error:
        improvement = ((f57_error - f91_error) / f57_error) * 100
        stats_text += f"\n✓ F91 勝出 ({improvement:.1f}%)"
    
    subplot_ax.text(0.02, 0.98, stats_text, transform=subplot_ax.transAxes,
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    return f57_avg, f91_avg, f57_error, f91_error

# 主程序
print("\n" + "="*70)
print("F57 vs F91 四場賽事對比分析 - 2025 賽季")
print("="*70)

# 創建 2x2 子圖
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('2025 賽季 F57 vs F91 預測準確度對比', fontsize=16, fontweight='bold', y=0.995)

# 準確度統計
results = []

for idx, race in enumerate(races):
    row = idx // 2
    col = idx % 2
    ax = axes[row, col]
    
    print(f"\n處理: {race['display_name']}")
    
    # 載入數據
    f57_data = load_f57_data(race['name'])
    f91_data = load_f91_data(race['name'])
    
    if f57_data is None or f91_data is None:
        print(f"  ❌ 數據缺失")
        ax.text(0.5, 0.5, f"{race['display_name']}\n數據缺失", 
               ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        continue
    
    print(f"  ✓ F57: {len(f57_data)} 圈, F91: {len(f91_data)} 圈")
    
    # 創建圖表
    f57_avg, f91_avg, f57_error, f91_error = create_comparison_chart(
        race, f57_data, f91_data, ax
    )
    
    results.append({
        'race': race['display_name'],
        'f57_avg': f57_avg,
        'f91_avg': f91_avg,
        'real_avg': race['real_avg'],
        'f57_error': f57_error,
        'f91_error': f91_error,
        'f91_wins': f91_error < f57_error
    })
    
    print(f"  F57 平均: {f57_avg:.3f}s (誤差: {f57_error:.3f}s)")
    print(f"  F91 平均: {f91_avg:.3f}s (誤差: {f91_error:.3f}s)")
    print(f"  {'✅ F91 勝出' if f91_error < f57_error else '✅ F57 勝出'}")

plt.tight_layout()

# 保存圖表
output_file = f"reports/f57_f91_comparison_4races_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
Path("reports").mkdir(exist_ok=True)
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"\n圖表已保存: {output_file}")

# 顯示圖表
plt.show()

# 生成準確度總結
print("\n" + "="*70)
print("準確度總結")
print("="*70)

print(f"\n{'賽事':<25} {'F57誤差':<12} {'F91誤差':<12} {'勝者':<10}")
print("-" * 70)

f91_win_count = 0
for r in results:
    winner = "F91 ✓" if r['f91_wins'] else "F57 ✓"
    if r['f91_wins']:
        f91_win_count += 1
    print(f"{r['race']:<25} {r['f57_error']:<12.3f} {r['f91_error']:<12.3f} {winner:<10}")

print("\n" + "="*70)
print(f"F91 勝出: {f91_win_count}/{len(results)} 場 ({f91_win_count/len(results)*100:.1f}%)")
print(f"F57 勝出: {len(results)-f91_win_count}/{len(results)} 場 ({(len(results)-f91_win_count)/len(results)*100:.1f}%)")
print("="*70)

if f91_win_count > len(results) / 2:
    print("\n✅ 結論: F91 (機器學習) 在多數賽事中更準確")
else:
    print("\n✅ 結論: F57 (物理模型) 在多數賽事中更穩定")

print("\n")
