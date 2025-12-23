#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F120 FP2 Corner Analysis 視覺化腳本
生成 Box Plot、Violin Plot 和 Heatmap
"""

import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path
from datetime import datetime

# 設定中文字體
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

def load_f120_data(json_path: str) -> dict:
    """載入 F120 JSON 數據"""
    with open(json_path, encoding='utf-8') as f:
        return json.load(f)

def create_box_plot(data: dict, output_dir: Path):
    """
    創建 Box Plot - 比較各車手在三種彎道類型的速度分布
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 8))
    
    corner_types = ['low_speed_corner_6', 'mid_speed_corner_5', 'high_speed_corner_8']
    corner_labels = ['T6 (Low Speed)', 'T5 (Mid Speed)', 'T8 (High Speed)']
    
    for idx, (corner_key, corner_label) in enumerate(zip(corner_types, corner_labels)):
        ax = axes[idx]
        
        # 收集各車手數據
        driver_data = []
        driver_names = []
        
        for driver_info in data['mode_a_unified']['drivers']:
            driver = driver_info['driver']
            corners = driver_info.get('corners', {})
            corner_stats = corners.get(corner_key, {})
            speeds_raw = corner_stats.get('speeds_raw', [])
            
            if speeds_raw:
                for speed in speeds_raw:
                    driver_data.append({'Driver': driver, 'Speed': speed})
                driver_names.append(driver)
        
        if driver_data:
            df = pd.DataFrame(driver_data)
            
            # 繪製 Box Plot
            sns.boxplot(data=df, x='Driver', y='Speed', ax=ax, palette='Set2')
            ax.set_title(corner_label, fontsize=14, fontweight='bold')
            ax.set_xlabel('Driver', fontsize=11)
            ax.set_ylabel('Speed (km/h)', fontsize=11)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y', alpha=0.3)
    
    plt.suptitle(f"FP2 Corner Speed Distribution - {data.get('race', 'Unknown')} {data.get('year', '')}",
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path = output_dir / 'f120_box_plot.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[SUCCESS] Box Plot saved: {output_path}")
    return output_path

def create_violin_plot(data: dict, output_dir: Path):
    """
    創建 Violin Plot - 顯示速度分布形狀
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 8))
    
    corner_types = ['low_speed_corner_6', 'mid_speed_corner_5', 'high_speed_corner_8']
    corner_labels = ['T6 (Low Speed)', 'T5 (Mid Speed)', 'T8 (High Speed)']
    
    for idx, (corner_key, corner_label) in enumerate(zip(corner_types, corner_labels)):
        ax = axes[idx]
        
        # 收集各車手數據
        driver_data = []
        
        for driver_info in data['mode_a_unified']['drivers']:
            driver = driver_info['driver']
            corners = driver_info.get('corners', {})
            corner_stats = corners.get(corner_key, {})
            speeds_raw = corner_stats.get('speeds_raw', [])
            
            if speeds_raw:
                for speed in speeds_raw:
                    driver_data.append({'Driver': driver, 'Speed': speed})
        
        if driver_data:
            df = pd.DataFrame(driver_data)
            
            # 繪製 Violin Plot
            sns.violinplot(data=df, x='Driver', y='Speed', ax=ax, palette='muted', inner='box')
            ax.set_title(corner_label, fontsize=14, fontweight='bold')
            ax.set_xlabel('Driver', fontsize=11)
            ax.set_ylabel('Speed (km/h)', fontsize=11)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y', alpha=0.3)
    
    plt.suptitle(f"FP2 Corner Speed Distribution (Violin) - {data.get('race', 'Unknown')} {data.get('year', '')}",
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path = output_dir / 'f120_violin_plot.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[SUCCESS] Violin Plot saved: {output_path}")
    return output_path

def create_heatmap(data: dict, output_dir: Path):
    """
    創建 Heatmap - 各車手在各彎道的中位數速度
    """
    # 收集數據
    drivers = []
    corner_types = ['low_speed_corner_6', 'mid_speed_corner_5', 'high_speed_corner_8']
    corner_labels = ['T6 (Low)', 'T5 (Mid)', 'T8 (High)']
    
    heatmap_data = []
    
    for driver_info in data['mode_a_unified']['drivers']:
        driver = driver_info['driver']
        drivers.append(driver)
        
        row = []
        for corner_key in corner_types:
            corners = driver_info.get('corners', {})
            corner_stats = corners.get(corner_key, {})
            median_speed = corner_stats.get('median_speed', np.nan)
            row.append(median_speed)
        
        heatmap_data.append(row)
    
    # 創建 DataFrame
    df = pd.DataFrame(heatmap_data, index=drivers, columns=corner_labels)
    
    # 繪製 Heatmap
    fig, ax = plt.subplots(figsize=(10, 12))
    
    sns.heatmap(df, annot=True, fmt='.1f', cmap='RdYlGn_r', 
                ax=ax, cbar_kws={'label': 'Median Speed (km/h)'},
                linewidths=0.5, linecolor='white')
    
    ax.set_title(f"FP2 Corner Median Speed Heatmap\n{data.get('race', 'Unknown')} {data.get('year', '')}",
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Corner Type', fontsize=12)
    ax.set_ylabel('Driver', fontsize=12)
    
    plt.tight_layout()
    
    output_path = output_dir / 'f120_heatmap.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[SUCCESS] Heatmap saved: {output_path}")
    return output_path

def create_ant_comparison_chart(data: dict, output_dir: Path):
    """
    創建 ANT T6 特別分析圖表
    """
    # 找 ANT 數據
    ant_data = None
    for driver_info in data['mode_a_unified']['drivers']:
        if driver_info['driver'] == 'ANT':
            ant_data = driver_info
            break
    
    if not ant_data:
        print("[WARNING] ANT driver data not found")
        return None
    
    t6_stats = ant_data['corners'].get('low_speed_corner_6', {})
    speeds_raw = t6_stats.get('speeds_raw', [])
    
    if not speeds_raw:
        print("[WARNING] ANT T6 has no speed data")
        return None
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 左圖：速度分布直方圖
    ax1 = axes[0]
    ax1.hist(speeds_raw, bins=15, color='steelblue', edgecolor='white', alpha=0.8)
    ax1.axvline(t6_stats.get('median_speed', 0), color='red', linestyle='--', linewidth=2, 
                label=f"Median: {t6_stats.get('median_speed', 0):.1f} km/h")
    ax1.axvline(t6_stats.get('mean_speed', 0), color='orange', linestyle='--', linewidth=2,
                label=f"Mean: {t6_stats.get('mean_speed', 0):.1f} km/h")
    ax1.set_title('ANT T6 Speed Distribution', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Speed (km/h)')
    ax1.set_ylabel('Frequency')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # 右圖：各圈速度
    ax2 = axes[1]
    laps = list(range(1, len(speeds_raw) + 1))
    colors = ['green' if s < 100 else 'red' for s in speeds_raw]
    ax2.bar(laps, speeds_raw, color=colors, edgecolor='white')
    ax2.axhline(t6_stats.get('median_speed', 0), color='blue', linestyle='--', 
                linewidth=2, label=f"Median: {t6_stats.get('median_speed', 0):.1f}")
    ax2.set_title('ANT T6 Speed per Valid Lap', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Lap Index')
    ax2.set_ylabel('Speed (km/h)')
    ax2.legend()
    ax2.grid(alpha=0.3, axis='y')
    
    plt.suptitle(f"ANT T6 Analysis - {data.get('race', 'Unknown')} {data.get('year', '')} FP2\n"
                 f"Valid Laps: {t6_stats.get('valid_laps', 'N/A')}, "
                 f"Filtered: {t6_stats.get('filtered_laps', 'N/A')}",
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    output_path = output_dir / 'f120_ant_t6_analysis.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[SUCCESS] ANT T6 Analysis saved: {output_path}")
    return output_path

def main():
    """主函數"""
    # JSON 檔案路徑
    json_path = Path('json/fp2_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json')
    
    if not json_path.exists():
        print(f"[ERROR] JSON file not found: {json_path}")
        print("[INFO] Please run: python f1_analysis_modular_main.py -f 120 -y 2025 -r 'Abu Dhabi' -s FP2")
        return
    
    # 輸出目錄
    output_dir = Path('charts/f120')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 載入數據
    print(f"[INFO] Loading data from: {json_path}")
    data = load_f120_data(str(json_path))
    
    print(f"[INFO] Race: {data.get('race', 'Unknown')}, Year: {data.get('year', 'Unknown')}")
    print(f"[INFO] Drivers: {len(data.get('mode_a_unified', {}).get('drivers', []))}")
    
    # 生成圖表
    print("\n[STEP 1] Creating Box Plot...")
    create_box_plot(data, output_dir)
    
    print("\n[STEP 2] Creating Violin Plot...")
    create_violin_plot(data, output_dir)
    
    print("\n[STEP 3] Creating Heatmap...")
    create_heatmap(data, output_dir)
    
    print("\n[STEP 4] Creating ANT T6 Analysis...")
    create_ant_comparison_chart(data, output_dir)
    
    print(f"\n[COMPLETE] All charts saved to: {output_dir}")

if __name__ == '__main__':
    main()
