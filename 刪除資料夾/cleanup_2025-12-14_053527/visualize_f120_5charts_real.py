#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F120 + F121 綜合視覺化腳本（真實數據版本）
生成 5 張圖表：
1-3: 低速/中速/高速彎道（Entry vs Exit，Apex 熱力圖）- 使用真實 Entry/Exit 數據
4: 低速 vs 中速 vs 高速對比
5: 低速彎 vs 直線速度（空力特性分析）
"""

import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
from pathlib import Path

# 設定中文字體
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

def load_data():
    """載入 F120 和 F121 數據"""
    with open('json/fp2_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json', 'r', encoding='utf-8') as f:
        f120_data = json.load(f)
    
    with open('json/fp2_straight_line_all_laps_analysis_2025_Abu Dhabi_FP2.json', 'r', encoding='utf-8') as f:
        f121_data = json.load(f)
    
    return f120_data, f121_data

def extract_corner_data(f120_data):
    """提取彎道數據（Entry/Apex/Exit 真實數據）"""
    mode_a = f120_data['mode_a_unified']
    
    drivers_data = []
    for driver_info in mode_a['drivers']:
        driver = driver_info['driver']
        corners = driver_info.get('corners', {})
        
        driver_entry = {
            'driver': driver,
            # 低速彎 T6
            'low_entry': None, 'low_apex': None, 'low_exit': None,
            # 中速彎 T5
            'mid_entry': None, 'mid_apex': None, 'mid_exit': None,
            # 高速彎 T8
            'high_entry': None, 'high_apex': None, 'high_exit': None
        }
        
        # 提取低速彎 T6
        low_speed = corners.get('low_speed_corner_6', {})
        if low_speed:
            driver_entry['low_entry'] = low_speed.get('entry_speed_median')
            driver_entry['low_apex'] = low_speed.get('median_speed')
            driver_entry['low_exit'] = low_speed.get('exit_speed_median')
        
        # 提取中速彎 T5
        mid_speed = corners.get('mid_speed_corner_5', {})
        if mid_speed:
            driver_entry['mid_entry'] = mid_speed.get('entry_speed_median')
            driver_entry['mid_apex'] = mid_speed.get('median_speed')
            driver_entry['mid_exit'] = mid_speed.get('exit_speed_median')
        
        # 提取高速彎 T8
        high_speed = corners.get('high_speed_corner_8', {})
        if high_speed:
            driver_entry['high_entry'] = high_speed.get('entry_speed_median')
            driver_entry['high_apex'] = high_speed.get('median_speed')
            driver_entry['high_exit'] = high_speed.get('exit_speed_median')
        
        drivers_data.append(driver_entry)
    
    return pd.DataFrame(drivers_data)

def extract_straight_data(f121_data):
    """提取直線速度數據"""
    mode_a = f121_data['mode_a_unified']
    
    straight_data = {}
    for driver_info in mode_a['drivers']:
        driver = driver_info['driver']
        stats = driver_info.get('speed_stats', {})
        straight_data[driver] = stats.get('max', 0)
    
    return straight_data

def create_corner_scatter(ax, title, entry_speeds, exit_speeds, apex_speeds, drivers):
    """創建彎道散點圖（Entry vs Exit，Apex 熱力圖）"""
    scatter = ax.scatter(entry_speeds, exit_speeds, c=apex_speeds, 
                        s=200, cmap='RdYlGn', edgecolors='black', linewidth=1.5,
                        vmin=min(apex_speeds)*0.95, vmax=max(apex_speeds)*1.05)
    
    # 標註車手代碼
    for i, driver in enumerate(drivers):
        ax.annotate(driver, (entry_speeds[i], exit_speeds[i]), 
                   fontsize=8, ha='center', va='center', fontweight='bold')
    
    ax.set_xlabel('Entry Speed (-50m) [km/h]', fontsize=11)
    ax.set_ylabel('Exit Speed (+50m) [km/h]', fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3)
    
    # 添加顏色條
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Apex Speed [km/h]', fontsize=10)
    
    return scatter

def create_chart_1_3(corner_df, output_dir):
    """圖表 1-3: 低速/中速/高速彎道分析（使用真實 Entry/Exit 數據）"""
    
    # 過濾掉缺少數據的車手
    valid_df = corner_df.dropna(subset=['low_entry', 'low_exit', 'low_apex', 
                                         'mid_entry', 'mid_exit', 'mid_apex',
                                         'high_entry', 'high_exit', 'high_apex'])
    
    if len(valid_df) == 0:
        print("[WARNING] 沒有足夠的有效數據生成圖表 1-3")
        print(f"[DEBUG] 原始數據筆數: {len(corner_df)}")
        print(f"[DEBUG] 數據樣本:\n{corner_df.head()}")
        return None
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    
    drivers = valid_df['driver'].tolist()
    
    # 圖 1: 低速彎 T6
    low_entry = valid_df['low_entry'].tolist()
    low_exit = valid_df['low_exit'].tolist()
    low_apex = valid_df['low_apex'].tolist()
    
    create_corner_scatter(axes[0], 'T6 Low-Speed Corner Analysis', 
                         low_entry, low_exit, low_apex, drivers)
    
    # 圖 2: 中速彎 T5
    mid_entry = valid_df['mid_entry'].tolist()
    mid_exit = valid_df['mid_exit'].tolist()
    mid_apex = valid_df['mid_apex'].tolist()
    
    create_corner_scatter(axes[1], 'T5 Mid-Speed Corner Analysis',
                         mid_entry, mid_exit, mid_apex, drivers)
    
    # 圖 3: 高速彎 T8
    high_entry = valid_df['high_entry'].tolist()
    high_exit = valid_df['high_exit'].tolist()
    high_apex = valid_df['high_apex'].tolist()
    
    create_corner_scatter(axes[2], 'T8 High-Speed Corner Analysis',
                         high_entry, high_exit, high_apex, drivers)
    
    plt.tight_layout()
    output_path = output_dir / 'f120_charts_1_3_corner_analysis.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[SUCCESS] Charts 1-3 saved: {output_path}")
    return output_path

def create_chart_4(corner_df, output_dir):
    """圖表 4: 低速 vs 中速 vs 高速對比"""
    
    # 使用 Apex 速度作為對比基準
    valid_df = corner_df.dropna(subset=['low_apex', 'mid_apex', 'high_apex'])
    
    if len(valid_df) == 0:
        print("[WARNING] 沒有足夠的有效數據生成圖表 4")
        return None
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    drivers = valid_df['driver'].tolist()
    low_speeds = valid_df['low_apex'].tolist()
    mid_speeds = valid_df['mid_apex'].tolist()
    high_speeds = valid_df['high_apex'].tolist()
    
    # 使用高速彎速度作為顏色映射
    scatter = ax.scatter(mid_speeds, low_speeds, c=high_speeds,
                        s=300, cmap='RdYlGn', edgecolors='black', linewidth=2,
                        vmin=min(high_speeds)*0.95, vmax=max(high_speeds)*1.05)
    
    # 標註車手
    for i, driver in enumerate(drivers):
        ax.annotate(driver, (mid_speeds[i], low_speeds[i]),
                   fontsize=9, ha='center', va='center', fontweight='bold')
    
    ax.set_xlabel('T5 Mid-Speed Corner [km/h]', fontsize=12)
    ax.set_ylabel('T6 Low-Speed Corner [km/h]', fontsize=12)
    ax.set_title('Corner Speed Comparison\n(Color = T8 High-Speed)', 
                fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3)
    
    # 添加對角線參考
    ax.axline((90, 60), slope=0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    # 添加顏色條
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('T8 High-Speed [km/h]', fontsize=11)
    
    # 添加區域標註
    ax.text(0.05, 0.95, '高下壓力區\n(低速快)', transform=ax.transAxes,
           fontsize=10, va='top', bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
    ax.text(0.95, 0.05, '低阻力區\n(中速快)', transform=ax.transAxes,
           fontsize=10, ha='right', bbox=dict(boxstyle='round', facecolor='blue', alpha=0.3))
    
    plt.tight_layout()
    output_path = output_dir / 'f120_chart_4_corner_comparison.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[SUCCESS] Chart 4 saved: {output_path}")
    return output_path

def create_chart_5(corner_df, straight_data, output_dir):
    """圖表 5: 低速彎 vs 直線速度（空力特性分析）"""
    
    valid_df = corner_df.dropna(subset=['low_apex', 'high_apex'])
    
    if len(valid_df) == 0:
        print("[WARNING] 沒有足夠的有效數據生成圖表 5")
        return None
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    drivers = valid_df['driver'].tolist()
    low_speeds = valid_df['low_apex'].tolist()
    
    # 獲取直線速度
    straight_speeds = [straight_data.get(driver, 0) for driver in drivers]
    
    # 使用高速彎速度作為顏色
    high_speeds = valid_df['high_apex'].tolist()
    
    scatter = ax.scatter(straight_speeds, low_speeds, c=high_speeds,
                        s=300, cmap='RdYlGn', edgecolors='black', linewidth=2,
                        vmin=min(high_speeds)*0.95, vmax=max(high_speeds)*1.05)
    
    # 標註車手
    for i, driver in enumerate(drivers):
        ax.annotate(driver, (straight_speeds[i], low_speeds[i]),
                   fontsize=9, ha='center', va='center', fontweight='bold')
    
    ax.set_xlabel('Straight Line Max Speed (F121) [km/h]', fontsize=12)
    ax.set_ylabel('T6 Low-Speed Corner (F120) [km/h]', fontsize=12)
    ax.set_title('Aerodynamic Setup Analysis\nLow-Speed Corner vs Straight Line Speed',
                fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3)
    
    # 添加顏色條
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('T8 High-Speed [km/h]', fontsize=11)
    
    # 添加區域標註
    ax.text(0.05, 0.95, '高下壓力\n低速快 + 直線慢', transform=ax.transAxes,
           fontsize=10, va='top', bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
    ax.text(0.95, 0.05, '低阻力\n低速慢 + 直線快', transform=ax.transAxes,
           fontsize=10, ha='right', bbox=dict(boxstyle='round', facecolor='blue', alpha=0.3))
    
    # 添加對角線（平衡設定）
    x_range = [min(straight_speeds), max(straight_speeds)]
    y_range = [min(low_speeds), max(low_speeds)]
    ax.plot([x_range[0], x_range[1]], [y_range[1], y_range[0]], 
           'k--', alpha=0.3, linewidth=2, label='Balance Line')
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    output_path = output_dir / 'f120_chart_5_aero_analysis.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[SUCCESS] Chart 5 saved: {output_path}")
    return output_path

def main():
    print("=== F120 + F121 綜合視覺化腳本（真實數據版本） ===\n")
    
    # 創建輸出目錄
    output_dir = Path('charts/f120_5charts_real')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 載入數據
    print("[STEP 1] 載入數據...")
    f120_data, f121_data = load_data()
    
    # 提取數據
    print("[STEP 2] 提取彎道數據（Entry/Apex/Exit）...")
    corner_df = extract_corner_data(f120_data)
    print(f"  -> 提取 {len(corner_df)} 位車手數據")
    print(f"  -> 數據欄位: {corner_df.columns.tolist()}")
    
    print("\n[STEP 3] 提取直線速度數據...")
    straight_data = extract_straight_data(f121_data)
    print(f"  -> 提取 {len(straight_data)} 位車手直線速度")
    
    # 生成圖表
    print("\n[STEP 4] 生成圖表 1-3: 低速/中速/高速彎道分析...")
    result1 = create_chart_1_3(corner_df, output_dir)
    
    if result1:
        print("[STEP 5] 生成圖表 4: 彎道速度對比...")
        create_chart_4(corner_df, output_dir)
        
        print("[STEP 6] 生成圖表 5: 空力特性分析...")
        create_chart_5(corner_df, straight_data, output_dir)
        
        print(f"\n[COMPLETE] 所有圖表已保存至: {output_dir}")
        print("生成的圖表：")
        print("  1-3: f120_charts_1_3_corner_analysis.png")
        print("  4:   f120_chart_4_corner_comparison.png")
        print("  5:   f120_chart_5_aero_analysis.png")
    else:
        print("\n[ERROR] 圖表生成失敗 - 當前 JSON 檔案沒有 Entry/Exit 數據")
        print("請重新執行 F120 分析以生成包含三點速度的數據：")
        print("  python f1_analysis_modular_main.py -f 120 -y 2025 -r \"Abu Dhabi\" -s FP2")

if __name__ == '__main__':
    main()
