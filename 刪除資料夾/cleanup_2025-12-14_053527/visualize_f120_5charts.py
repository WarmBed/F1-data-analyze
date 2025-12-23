#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F120 + F121 綜合視覺化腳本
生成 5 張圖表：
1-3: 低速/中速/高速彎道（Entry vs Exit，Apex 熱力圖）
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
    with open('json/F120_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json', 'r', encoding='utf-8') as f:
        f120_data = json.load(f)
    
    with open('json/fp2_straight_line_all_laps_analysis_2025_Abu Dhabi_FP2.json', 'r', encoding='utf-8') as f:
        f121_data = json.load(f)
    
    return f120_data, f121_data

def _filter_outlier_by_apex(entry_or_exit_speed, apex_speed, max_ratio=2.5):
    """根據 Apex 速度過濾異常值
    
    Args:
        entry_or_exit_speed: Entry 或 Exit 速度
        apex_speed: Apex 速度
        max_ratio: 允許的最大比值（Entry/Apex 或 Exit/Apex）
    
    Returns:
        過濾後的速度（如果異常則返回估算值）
    """
    if entry_or_exit_speed is None or entry_or_exit_speed == 0:
        return None
    
    ratio = entry_or_exit_speed / apex_speed if apex_speed > 0 else 0
    
    # 如果比值過大，視為異常，返回 None
    if ratio > max_ratio:
        return None
    
    return entry_or_exit_speed

def extract_corner_data(f120_data):
    """提取彎道數據（Entry/Apex/Exit）- 優先使用真實數據，套用異常值過濾"""
    mode_a = f120_data['mode_a_unified']
    
    drivers_data = []
    has_entry_exit_data = False  # 檢測是否有真實的 Entry/Exit 數據
    
    for driver_info in mode_a['drivers']:
        driver = driver_info['driver']
        corners = driver_info.get('corners', {})
        
        driver_entry = {
            'driver': driver,
            # 低速彎 T6
            'low_entry': None, 'low_apex': None, 'low_exit': None,
            'low_entry_filtered': False, 'low_exit_filtered': False,
            # 中速彎 T5
            'mid_entry': None, 'mid_apex': None, 'mid_exit': None,
            'mid_entry_filtered': False, 'mid_exit_filtered': False,
            # 高速彎 T8
            'high_entry': None, 'high_apex': None, 'high_exit': None,
            'high_entry_filtered': False, 'high_exit_filtered': False
        }
        
        # 提取低速彎 T6
        low_speed = corners.get('low_speed_corner_6', {})
        if low_speed:
            low_apex = low_speed.get('median_speed', 0)
            low_entry_raw = low_speed.get('entry_50m_speed') or low_speed.get('entry_speed_median')
            low_exit_raw = low_speed.get('exit_50m_speed') or low_speed.get('exit_speed_median')
            
            # 套用異常值過濾（低速彎：Entry/Apex < 2.0, Exit/Apex < 2.0）
            low_entry = _filter_outlier_by_apex(low_entry_raw, low_apex, max_ratio=2.0)
            low_exit = _filter_outlier_by_apex(low_exit_raw, low_apex, max_ratio=2.0)
            
            # 如果過濾後沒有數據，用物理合理的估算，並標記為過濾
            if low_entry is None:
                low_entry = low_apex * 1.35  # 低速彎 Entry 約 1.35 倍 Apex
                driver_entry['low_entry_filtered'] = True
            else:
                has_entry_exit_data = True
                driver_entry['low_entry_filtered'] = False
            
            if low_exit is None:
                low_exit = low_apex * 1.40  # 低速彎 Exit 約 1.40 倍 Apex
                driver_entry['low_exit_filtered'] = True
            else:
                driver_entry['low_exit_filtered'] = False
                
            driver_entry['low_entry'] = low_entry
            driver_entry['low_apex'] = low_apex
            driver_entry['low_exit'] = low_exit
        
        # 提取中速彎 T5
        mid_speed = corners.get('mid_speed_corner_5', {})
        if mid_speed:
            mid_apex = mid_speed.get('median_speed', 0)
            mid_entry_raw = mid_speed.get('entry_50m_speed') or mid_speed.get('entry_speed_median')
            mid_exit_raw = mid_speed.get('exit_50m_speed') or mid_speed.get('exit_speed_median')
            
            # 套用異常值過濾（中速彎：Entry/Apex < 1.5, Exit/Apex < 1.5）
            mid_entry = _filter_outlier_by_apex(mid_entry_raw, mid_apex, max_ratio=1.5)
            mid_exit = _filter_outlier_by_apex(mid_exit_raw, mid_apex, max_ratio=1.5)
            
            if mid_entry is None:
                mid_entry = mid_apex * 1.25  # 中速彎 Entry 約 1.25 倍 Apex
                driver_entry['mid_entry_filtered'] = True
            else:
                driver_entry['mid_entry_filtered'] = False
                
            if mid_exit is None:
                mid_exit = mid_apex * 1.20  # 中速彎 Exit 約 1.20 倍 Apex
                driver_entry['mid_exit_filtered'] = True
            else:
                driver_entry['mid_exit_filtered'] = False
                
            driver_entry['mid_entry'] = mid_entry
            driver_entry['mid_apex'] = mid_apex
            driver_entry['mid_exit'] = mid_exit
        
        # 提取高速彎 T8
        high_speed = corners.get('high_speed_corner_8', {})
        if high_speed:
            high_apex = high_speed.get('median_speed', 0)
            high_entry_raw = high_speed.get('entry_50m_speed') or high_speed.get('entry_speed_median')
            high_exit_raw = high_speed.get('exit_50m_speed') or high_speed.get('exit_speed_median')
            
            # 套用異常值過濾（高速彎：Entry/Apex < 1.2, Exit/Apex < 1.1）
            high_entry = _filter_outlier_by_apex(high_entry_raw, high_apex, max_ratio=1.2)
            high_exit = _filter_outlier_by_apex(high_exit_raw, high_apex, max_ratio=1.1)
            
            if high_entry is None:
                high_entry = high_apex * 1.10  # 高速彎 Entry 約 1.10 倍 Apex
                driver_entry['high_entry_filtered'] = True
            else:
                driver_entry['high_entry_filtered'] = False
                
            if high_exit is None:
                high_exit = high_apex * 1.05  # 高速彎 Exit 約 1.05 倍 Apex
                driver_entry['high_exit_filtered'] = True
            else:
                driver_entry['high_exit_filtered'] = False
                
            driver_entry['high_entry'] = high_entry
            driver_entry['high_apex'] = high_apex
            driver_entry['high_exit'] = high_exit
        
        drivers_data.append(driver_entry)
    
    # 打印數據來源信息
    data_source = "真實 Entry/Exit 數據" if has_entry_exit_data else "估算 Entry/Exit 數據（基於 Apex）"
    print(f"\n[INFO] 使用 {data_source}")
    
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

def create_corner_scatter(ax, title, entry_speeds, exit_speeds, apex_speeds, drivers, 
                         entry_filtered, exit_filtered):
    """創建彎道散點圖（Entry vs Exit，Apex 熱力圖）
    
    Args:
        entry_filtered: List[bool] - 標記哪些 Entry 數據被過濾（使用估算值）
        exit_filtered: List[bool] - 標記哪些 Exit 數據被過濾（使用估算值）
    """
    # 為每個點設置顏色：過濾的點用淺紫色，正常的點用 Apex 速度映射顏色
    colors = []
    for i in range(len(drivers)):
        if entry_filtered[i] or exit_filtered[i]:
            colors.append('#D8BFD8')  # 淺紫色 (Thistle)
        else:
            colors.append(apex_speeds[i])  # 使用 Apex 速度
    
    # 分開繪製正常點和過濾點
    normal_mask = [not (entry_filtered[i] or exit_filtered[i]) for i in range(len(drivers))]
    filtered_mask = [entry_filtered[i] or exit_filtered[i] for i in range(len(drivers))]
    
    # 繪製正常點（用 Apex 速度映射顏色）
    if any(normal_mask):
        normal_entry = [entry_speeds[i] for i in range(len(drivers)) if normal_mask[i]]
        normal_exit = [exit_speeds[i] for i in range(len(drivers)) if normal_mask[i]]
        normal_apex = [apex_speeds[i] for i in range(len(drivers)) if normal_mask[i]]
        
        scatter_normal = ax.scatter(normal_entry, normal_exit, c=normal_apex, 
                            s=200, cmap='RdYlGn', edgecolors='black', linewidth=1.5,
                            vmin=min(apex_speeds)*0.95, vmax=max(apex_speeds)*1.05,
                            label='Normal Data', zorder=2)
    
    # 繪製過濾點（淺紫色）
    if any(filtered_mask):
        filtered_entry = [entry_speeds[i] for i in range(len(drivers)) if filtered_mask[i]]
        filtered_exit = [exit_speeds[i] for i in range(len(drivers)) if filtered_mask[i]]
        
        scatter_filtered = ax.scatter(filtered_entry, filtered_exit, 
                            c='#D8BFD8', s=200, edgecolors='purple', linewidth=2,
                            label='Filtered (Estimated)', zorder=3, alpha=0.8)
    
    # 標註車手代碼
    for i, driver in enumerate(drivers):
        color = 'purple' if filtered_mask[i] else 'black'
        weight = 'bold' if filtered_mask[i] else 'normal'
        ax.annotate(driver, (entry_speeds[i], exit_speeds[i]), 
                   fontsize=8, ha='center', va='center', 
                   fontweight=weight, color=color, zorder=4)
    
    ax.set_xlabel('Entry Speed (-50m) [km/h]', fontsize=11)
    ax.set_ylabel('Exit Speed (+50m) [km/h]', fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3)
    
    # 添加圖例
    ax.legend(loc='upper left', fontsize=9)
    
    # 添加顏色條（僅針對正常數據）
    if any(normal_mask):
        cbar = plt.colorbar(scatter_normal, ax=ax)
        cbar.set_label('Apex Speed [km/h]', fontsize=10)

def create_chart_1_3(corner_df, output_dir):
    """圖表 1-3: 低速/中速/高速彎道分析（Entry vs Exit，Apex 熱力圖，過濾數據標紫色）"""
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    
    drivers = corner_df['driver'].tolist()
    
    # 圖 1: 低速彎 T6
    low_entry = corner_df['low_entry'].tolist()
    low_exit = corner_df['low_exit'].tolist()
    low_apex = corner_df['low_apex'].tolist()
    low_entry_filtered = corner_df['low_entry_filtered'].tolist()
    low_exit_filtered = corner_df['low_exit_filtered'].tolist()
    
    create_corner_scatter(axes[0], 'T6 Low-Speed Corner Analysis', 
                         low_entry, low_exit, low_apex, drivers,
                         low_entry_filtered, low_exit_filtered)
    
    # 圖 2: 中速彎 T5
    mid_entry = corner_df['mid_entry'].tolist()
    mid_exit = corner_df['mid_exit'].tolist()
    mid_apex = corner_df['mid_apex'].tolist()
    mid_entry_filtered = corner_df['mid_entry_filtered'].tolist()
    mid_exit_filtered = corner_df['mid_exit_filtered'].tolist()
    
    create_corner_scatter(axes[1], 'T5 Mid-Speed Corner Analysis',
                         mid_entry, mid_exit, mid_apex, drivers,
                         mid_entry_filtered, mid_exit_filtered)
    
    # 圖 3: 高速彎 T8
    high_entry = corner_df['high_entry'].tolist()
    high_exit = corner_df['high_exit'].tolist()
    high_apex = corner_df['high_apex'].tolist()
    high_entry_filtered = corner_df['high_entry_filtered'].tolist()
    high_exit_filtered = corner_df['high_exit_filtered'].tolist()
    
    create_corner_scatter(axes[2], 'T8 High-Speed Corner Analysis',
                         high_entry, high_exit, high_apex, drivers,
                         high_entry_filtered, high_exit_filtered)
    
    plt.tight_layout()
    output_path = output_dir / 'f120_charts_1_3_corner_analysis.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[SUCCESS] Charts 1-3 saved: {output_path}")
    return output_path

def create_chart_4(corner_df, output_dir):
    """圖表 4: 低速 vs 中速 vs 高速對比"""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    drivers = corner_df['driver'].tolist()
    low_apex = corner_df['low_apex'].tolist()
    mid_apex = corner_df['mid_apex'].tolist()
    high_apex = corner_df['high_apex'].tolist()
    
    # 使用高速彎速度作為顏色映射
    scatter = ax.scatter(mid_apex, low_apex, c=high_apex,
                        s=300, cmap='RdYlGn', edgecolors='black', linewidth=2,
                        vmin=min(high_apex)*0.95, vmax=max(high_apex)*1.05)
    
    # 標註車手
    for i, driver in enumerate(drivers):
        ax.annotate(driver, (mid_apex[i], low_apex[i]),
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
    fig, ax = plt.subplots(figsize=(12, 10))
    
    drivers = corner_df['driver'].tolist()
    low_apex = corner_df['low_apex'].tolist()
    
    # 獲取直線速度
    straight_speeds = [straight_data.get(driver, 0) for driver in drivers]
    
    # 使用高速彎速度作為顏色
    high_apex = corner_df['high_apex'].tolist()
    
    scatter = ax.scatter(straight_speeds, low_apex, c=high_apex,
                        s=300, cmap='RdYlGn', edgecolors='black', linewidth=2,
                        vmin=min(high_apex)*0.95, vmax=max(high_apex)*1.05)
    
    # 標註車手
    for i, driver in enumerate(drivers):
        ax.annotate(driver, (straight_speeds[i], low_apex[i]),
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
    y_range = [min(low_apex), max(low_apex)]
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
    print("=== F120 + F121 綜合視覺化腳本 ===\n")
    
    # 創建輸出目錄
    output_dir = Path('charts/f120_5charts')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 載入數據
    print("[STEP 1] 載入數據...")
    f120_data, f121_data = load_data()
    
    # 提取數據
    print("[STEP 2] 提取彎道數據...")
    corner_df = extract_corner_data(f120_data)
    
    print("[STEP 3] 提取直線速度數據...")
    straight_data = extract_straight_data(f121_data)
    
    # 生成圖表
    print("\n[STEP 4] 生成圖表 1-3: 低速/中速/高速彎道分析...")
    create_chart_1_3(corner_df, output_dir)
    
    print("[STEP 5] 生成圖表 4: 彎道速度對比...")
    create_chart_4(corner_df, output_dir)
    
    print("[STEP 6] 生成圖表 5: 空力特性分析...")
    create_chart_5(corner_df, straight_data, output_dir)
    
    print(f"\n[COMPLETE] 所有圖表已保存至: {output_dir}")
    print("生成的圖表：")
    print("  1-3: f120_charts_1_3_corner_analysis.png")
    print("  4:   f120_chart_4_corner_comparison.png")
    print("  5:   f120_chart_5_aero_analysis.png")

if __name__ == '__main__':
    main()
