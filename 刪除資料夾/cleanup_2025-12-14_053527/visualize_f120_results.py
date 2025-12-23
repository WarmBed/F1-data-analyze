"""
F120 FP2 彎道分析 - 視覺化腳本

讀取 F120 生成的 JSON，產生 6 種互補的視覺化圖表：
1. Box Plot - 統計分布概覽
2. Violin Plot - 完整分布形狀
3. Heatmap - 標準差熱力圖（一致性比較）
4. Scatter Plot - 速度 vs 一致性分析
5. Line Plot - Long Run vs Quali Sim 對比
6. Radar Chart - 車手全方位評估

作者：AI Assistant
日期：2025-12-13
"""

import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from matplotlib.patches import Rectangle
import matplotlib.font_manager as fm
import os

# ==================== 終極中文字體解決方案 ====================

print("=" * 60)
print("設定中文字體（終極版本）...")

# Windows 系統字體路徑
windows_fonts_paths = [
    r'C:\Windows\Fonts\msjh.ttc',      # Microsoft JhengHei (微軟正黑體)
    r'C:\Windows\Fonts\msyh.ttc',      # Microsoft YaHei (微軟雅黑體)
    r'C:\Windows\Fonts\simhei.ttf',    # SimHei (黑體)
    r'C:\Windows\Fonts\mingliu.ttc',   # MingLiU (細明體)
]

# 尋找可用的字體檔案
font_file = None
for font_path in windows_fonts_paths:
    if os.path.exists(font_path):
        font_file = font_path
        print(f"✅ 找到字體檔案: {font_path}")
        break

if font_file:
    # 方法 1: 直接從字體檔案建立 FontProperties
    from matplotlib.font_manager import FontProperties
    chinese_font = FontProperties(fname=font_file)
    print(f"✅ 已載入字體檔案")
    
    # 方法 2: 註冊字體到 matplotlib
    try:
        fm.fontManager.addfont(font_file)
        font_name = fm.FontProperties(fname=font_file).get_name()
        print(f"✅ 字體名稱: {font_name}")
        
        # 設定為預設字體
        plt.rcParams['font.family'] = font_name
        plt.rcParams['font.sans-serif'] = [font_name]
        plt.rcParams['axes.unicode_minus'] = False
        
        matplotlib.rcParams['font.family'] = font_name
        matplotlib.rcParams['font.sans-serif'] = [font_name]
        matplotlib.rcParams['axes.unicode_minus'] = False
        
    except Exception as e:
        print(f"⚠️  註冊字體時發生錯誤: {e}")
        print("使用 FontProperties 作為備用方案")
else:
    print("❌ 找不到任何中文字體檔案！")
    chinese_font = None
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

print("=" * 60)
print()

# 設定 Seaborn 樣式
sns.set_style("whitegrid")
sns.set_palette("husl")


class F120Visualizer:
    """F120 數據視覺化類別"""
    
    def __init__(self, json_path: str):
        """
        初始化
        
        Args:
            json_path: F120 輸出的 JSON 檔案路徑
        """
        self.json_path = Path(json_path)
        self.data = self._load_json()
        self.race_info = f"{self.data['year']} {self.data['race']} {self.data['session']}"
        
        # 載入中文字體（如果可用）
        self.chinese_font = self._get_chinese_font()
        
    def _get_chinese_font(self):
        """取得中文字體 FontProperties"""
        try:
            from matplotlib.font_manager import FontProperties
            windows_fonts_paths = [
                r'C:\Windows\Fonts\msjh.ttc',
                r'C:\Windows\Fonts\msyh.ttc',
                r'C:\Windows\Fonts\simhei.ttf',
            ]
            
            for font_path in windows_fonts_paths:
                if os.path.exists(font_path):
                    return FontProperties(fname=font_path)
            
            return None
        except:
            return None
        
    def _load_json(self) -> Dict[str, Any]:
        """載入 JSON 檔案"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_all_visualizations(self, output_dir: str = "visualizations"):
        """建立所有視覺化圖表"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print("=" * 80)
        print(f"F120 視覺化 - {self.race_info}")
        print("=" * 80)
        
        # 1. Box Plot（盒鬚圖）
        print("\n[1/6] 建立 Box Plot...")
        self.plot_box_plot(output_path)
        
        # 2. Violin Plot（小提琴圖）
        print("[2/6] 建立 Violin Plot...")
        self.plot_violin_plot(output_path)
        
        # 3. Heatmap（標準差熱力圖）
        print("[3/6] 建立 Heatmap...")
        self.plot_std_heatmap(output_path)
        
        # 4. Scatter Plot（速度 vs 一致性）
        print("[4/6] 建立 Scatter Plot...")
        self.plot_speed_vs_consistency(output_path)
        
        # 5. Line Plot（Long Run vs Quali Sim）
        print("[5/6] 建立 Line Plot...")
        self.plot_group_comparison(output_path)
        
        # 6. Radar Chart（車手全方位評估）
        print("[6/6] 建立 Radar Chart...")
        self.plot_radar_chart(output_path)
        
        print("\n" + "=" * 80)
        print(f"✅ 所有視覺化完成！檔案儲存於: {output_path.absolute()}")
        print("=" * 80)
    
    # ==================== 1. Box Plot ====================
    
    def plot_box_plot(self, output_path: Path):
        """
        Box Plot（盒鬚圖）- 統計分布概覽
        
        顯示每位車手在 3 個彎道的速度分布
        - 中位數（橘線）
        - Q1-Q3 範圍（盒子）
        - 最小/最大值（鬚）
        - 異常值（點）
        """
        mode_a = self.data.get('mode_a_unified', {})
        drivers = mode_a.get('drivers', [])
        
        if not drivers:
            print("  ⚠️  無數據，跳過 Box Plot")
            return
        
        # 準備數據
        corner_types = ['low_speed', 'mid_speed', 'high_speed']
        corner_names = ['低速彎', '中速彎', '高速彎']
        selected_corners = self.data.get('selected_corners', {})
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f'FP2 彎道速度分布（Box Plot）\n{self.race_info}', 
                     fontsize=16, fontweight='bold', fontproperties=self.chinese_font)
        
        for idx, (corner_type, corner_name) in enumerate(zip(corner_types, corner_names)):
            ax = axes[idx]
            
            # 獲取彎道資訊
            corner_info = selected_corners.get(corner_type)
            if not corner_info:
                ax.text(0.5, 0.5, '無數據', ha='center', va='center', fontsize=14)
                ax.set_title(corner_name)
                continue
            
            corner_number = corner_info['corner_number']
            corner_key = f"{corner_type}_corner_{corner_number}"
            
            # 收集所有車手的速度數據
            box_data = []
            labels = []
            
            for driver_data in drivers:
                driver = driver_data['driver']
                corners = driver_data.get('corners', {})
                corner_stats = corners.get(corner_key)
                
                if corner_stats and 'speeds_raw' in corner_stats:
                    speeds = corner_stats['speeds_raw']
                    if speeds:
                        box_data.append(speeds)
                        labels.append(driver)
            
            if box_data:
                # 繪製 Box Plot
                bp = ax.boxplot(box_data, labels=labels, patch_artist=True,
                               showmeans=True, meanline=True,
                               boxprops=dict(facecolor='lightblue', alpha=0.7),
                               medianprops=dict(color='red', linewidth=2),
                               meanprops=dict(color='green', linewidth=2, linestyle='--'),
                               whiskerprops=dict(linewidth=1.5),
                               capprops=dict(linewidth=1.5))
                
                ax.set_xlabel('車手', fontsize=11, fontweight='bold')
                ax.set_ylabel('速度 (km/h)', fontsize=11, fontweight='bold')
                ax.set_title(f'{corner_name} (T{corner_number})', fontsize=12, fontweight='bold')
                ax.tick_params(axis='x', rotation=45, labelsize=9)
                ax.grid(True, alpha=0.3)
                
                # 添加圖例
                from matplotlib.lines import Line2D
                legend_elements = [
                    Line2D([0], [0], color='red', linewidth=2, label='中位數'),
                    Line2D([0], [0], color='green', linewidth=2, linestyle='--', label='平均數'),
                    Rectangle((0, 0), 1, 1, fc='lightblue', alpha=0.7, label='Q1-Q3 範圍')
                ]
                ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
        
        plt.tight_layout()
        save_path = output_path / f"f120_boxplot_{self.data['year']}_{self.data['race']}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 已儲存: {save_path.name}")
    
    # ==================== 2. Violin Plot ====================
    
    def plot_violin_plot(self, output_path: Path):
        """
        Violin Plot（小提琴圖）- 完整分布形狀
        
        顯示速度分布的機率密度，比 Box Plot 更詳細
        可看出數據是集中還是分散
        """
        mode_a = self.data.get('mode_a_unified', {})
        drivers = mode_a.get('drivers', [])
        
        if not drivers:
            print("  ⚠️  無數據，跳過 Violin Plot")
            return
        
        # 準備數據
        corner_types = ['low_speed', 'mid_speed', 'high_speed']
        corner_names = ['低速彎', '中速彎', '高速彎']
        selected_corners = self.data.get('selected_corners', {})
        
        # 收集前 10 位車手數據（避免圖表過於擁擠）
        top_drivers = [d['driver'] for d in drivers[:10]]
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f'FP2 彎道速度分布（Violin Plot - Top 10 車手）\n{self.race_info}', 
                     fontsize=16, fontweight='bold')
        
        for idx, (corner_type, corner_name) in enumerate(zip(corner_types, corner_names)):
            ax = axes[idx]
            
            corner_info = selected_corners.get(corner_type)
            if not corner_info:
                ax.text(0.5, 0.5, '無數據', ha='center', va='center', fontsize=14)
                ax.set_title(corner_name)
                continue
            
            corner_number = corner_info['corner_number']
            corner_key = f"{corner_type}_corner_{corner_number}"
            
            # 準備 DataFrame
            plot_data = []
            
            for driver_data in drivers:
                driver = driver_data['driver']
                if driver not in top_drivers:
                    continue
                
                corners = driver_data.get('corners', {})
                corner_stats = corners.get(corner_key)
                
                if corner_stats and 'speeds_raw' in corner_stats:
                    for speed in corner_stats['speeds_raw']:
                        plot_data.append({
                            'driver': driver,
                            'speed': speed
                        })
            
            if plot_data:
                df = pd.DataFrame(plot_data)
                
                # 繪製 Violin Plot
                sns.violinplot(data=df, x='driver', y='speed', ax=ax, 
                              palette='Set2', inner='quartile')
                
                ax.set_xlabel('車手', fontsize=11, fontweight='bold')
                ax.set_ylabel('速度 (km/h)', fontsize=11, fontweight='bold')
                ax.set_title(f'{corner_name} (T{corner_number})', fontsize=12, fontweight='bold')
                ax.tick_params(axis='x', rotation=45, labelsize=9)
                ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        save_path = output_path / f"f120_violin_{self.data['year']}_{self.data['race']}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 已儲存: {save_path.name}")
    
    # ==================== 3. Heatmap ====================
    
    def plot_std_heatmap(self, output_path: Path):
        """
        Heatmap（標準差熱力圖）- 一致性比較
        
        顯示每位車手在 3 個彎道的標準差
        顏色越深 = 標準差越大 = 越不穩定
        顏色越淺 = 標準差越小 = 越穩定
        """
        mode_a = self.data.get('mode_a_unified', {})
        drivers = mode_a.get('drivers', [])
        
        if not drivers:
            print("  ⚠️  無數據，跳過 Heatmap")
            return
        
        corner_types = ['low_speed', 'mid_speed', 'high_speed']
        corner_names = ['低速彎', '中速彎', '高速彎']
        selected_corners = self.data.get('selected_corners', {})
        
        # 建立數據矩陣
        driver_names = []
        std_matrix = []
        
        for driver_data in drivers:
            driver = driver_data['driver']
            driver_names.append(driver)
            
            row = []
            for corner_type in corner_types:
                corner_info = selected_corners.get(corner_type)
                if not corner_info:
                    row.append(np.nan)
                    continue
                
                corner_number = corner_info['corner_number']
                corner_key = f"{corner_type}_corner_{corner_number}"
                
                corners = driver_data.get('corners', {})
                corner_stats = corners.get(corner_key)
                
                if corner_stats:
                    std = corner_stats.get('std_dev', np.nan)
                    row.append(std)
                else:
                    row.append(np.nan)
            
            std_matrix.append(row)
        
        # 轉換為 DataFrame
        df = pd.DataFrame(std_matrix, index=driver_names, columns=corner_names)
        
        # 繪製 Heatmap
        fig, ax = plt.subplots(figsize=(10, 12))
        
        sns.heatmap(df, annot=True, fmt='.2f', cmap='RdYlGn_r', 
                   cbar_kws={'label': '標準差 (km/h)'}, ax=ax,
                   linewidths=0.5, linecolor='gray')
        
        ax.set_title(f'FP2 彎道速度標準差熱力圖（一致性分析）\n{self.race_info}', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('彎道類型', fontsize=12, fontweight='bold')
        ax.set_ylabel('車手', fontsize=12, fontweight='bold')
        
        # 添加說明
        textstr = '顏色說明：\n綠色 = 穩定（低標準差）\n黃色 = 中等\n紅色 = 不穩定（高標準差）'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(1.35, 0.5, textstr, transform=ax.transAxes, fontsize=10,
               verticalalignment='center', bbox=props)
        
        plt.tight_layout()
        save_path = output_path / f"f120_heatmap_{self.data['year']}_{self.data['race']}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 已儲存: {save_path.name}")
    
    # ==================== 4. Scatter Plot ====================
    
    def plot_speed_vs_consistency(self, output_path: Path):
        """
        Scatter Plot（散點圖）- 速度 vs 一致性分析
        
        X 軸：平均速度（快慢）
        Y 軸：標準差（穩定度）
        
        理想位置：右下角（又快又穩）
        """
        mode_a = self.data.get('mode_a_unified', {})
        drivers = mode_a.get('drivers', [])
        
        if not drivers:
            print("  ⚠️  無數據，跳過 Scatter Plot")
            return
        
        corner_types = ['low_speed', 'mid_speed', 'high_speed']
        corner_names = ['低速彎', '中速彎', '高速彎']
        selected_corners = self.data.get('selected_corners', {})
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f'速度 vs 一致性分析（越右下越理想）\n{self.race_info}', 
                     fontsize=16, fontweight='bold')
        
        for idx, (corner_type, corner_name) in enumerate(zip(corner_types, corner_names)):
            ax = axes[idx]
            
            corner_info = selected_corners.get(corner_type)
            if not corner_info:
                ax.text(0.5, 0.5, '無數據', ha='center', va='center', fontsize=14)
                ax.set_title(corner_name)
                continue
            
            corner_number = corner_info['corner_number']
            corner_key = f"{corner_type}_corner_{corner_number}"
            
            # 收集數據
            means = []
            stds = []
            labels = []
            
            for driver_data in drivers:
                driver = driver_data['driver']
                corners = driver_data.get('corners', {})
                corner_stats = corners.get(corner_key)
                
                if corner_stats:
                    mean_speed = corner_stats.get('mean_speed')
                    std_dev = corner_stats.get('std_dev')
                    
                    if mean_speed is not None and std_dev is not None:
                        means.append(mean_speed)
                        stds.append(std_dev)
                        labels.append(driver)
            
            if means and stds:
                # 繪製散點圖
                scatter = ax.scatter(means, stds, s=100, alpha=0.6, c=range(len(means)), cmap='viridis')
                
                # 添加車手標籤
                for i, label in enumerate(labels):
                    ax.annotate(label, (means[i], stds[i]), 
                               xytext=(5, 5), textcoords='offset points',
                               fontsize=8, alpha=0.8)
                
                # 添加參考線（平均值）
                mean_mean = np.mean(means)
                mean_std = np.mean(stds)
                ax.axvline(mean_mean, color='red', linestyle='--', alpha=0.5, label='平均速度')
                ax.axhline(mean_std, color='blue', linestyle='--', alpha=0.5, label='平均標準差')
                
                # 標註象限
                ax.text(0.05, 0.95, '慢且不穩', transform=ax.transAxes, 
                       fontsize=10, va='top', ha='left', alpha=0.5)
                ax.text(0.95, 0.95, '快但不穩', transform=ax.transAxes, 
                       fontsize=10, va='top', ha='right', alpha=0.5)
                ax.text(0.05, 0.05, '慢但穩', transform=ax.transAxes, 
                       fontsize=10, va='bottom', ha='left', alpha=0.5)
                ax.text(0.95, 0.05, '✨ 又快又穩', transform=ax.transAxes, 
                       fontsize=10, va='bottom', ha='right', alpha=0.5, 
                       fontweight='bold', color='green')
                
                ax.set_xlabel('平均速度 (km/h)', fontsize=11, fontweight='bold')
                ax.set_ylabel('標準差 (km/h)', fontsize=11, fontweight='bold')
                ax.set_title(f'{corner_name} (T{corner_number})', fontsize=12, fontweight='bold')
                ax.legend(loc='upper left', fontsize=9)
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_path = output_path / f"f120_scatter_{self.data['year']}_{self.data['race']}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 已儲存: {save_path.name}")
    
    # ==================== 5. Line Plot ====================
    
    def plot_group_comparison(self, output_path: Path):
        """
        Line Plot（趨勢圖）- Long Run vs Quali Sim 對比
        
        比較高燃油（Long Run）vs 低燃油（Quali Sim）的速度差異
        量化燃油對速度的影響
        """
        mode_b = self.data.get('mode_b_grouped', {})
        groups = mode_b.get('groups', {})
        
        long_run = groups.get('long_run', {})
        quali_sim = groups.get('quali_sim', {})
        
        if not long_run.get('drivers') or not quali_sim.get('drivers'):
            print("  ⚠️  分組數據不足，跳過 Line Plot")
            return
        
        corner_types = ['low_speed', 'mid_speed', 'high_speed']
        corner_names = ['低速彎', '中速彎', '高速彎']
        selected_corners = self.data.get('selected_corners', {})
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f'Long Run vs Quali Sim 速度對比\n{self.race_info}', 
                     fontsize=16, fontweight='bold')
        
        for idx, (corner_type, corner_name) in enumerate(zip(corner_types, corner_names)):
            ax = axes[idx]
            
            corner_info = selected_corners.get(corner_type)
            if not corner_info:
                ax.text(0.5, 0.5, '無數據', ha='center', va='center', fontsize=14)
                ax.set_title(corner_name)
                continue
            
            corner_number = corner_info['corner_number']
            corner_key = f"{corner_type}_corner_{corner_number}"
            
            # 收集 Long Run 數據
            lr_drivers = []
            lr_medians = []
            
            for driver_data in long_run.get('drivers', []):
                driver = driver_data['driver']
                corners = driver_data.get('corners', {})
                corner_stats = corners.get(corner_key)
                
                if corner_stats:
                    median = corner_stats.get('median_speed')
                    if median is not None:
                        lr_drivers.append(driver)
                        lr_medians.append(median)
            
            # 收集 Quali Sim 數據
            qs_drivers = []
            qs_medians = []
            
            for driver_data in quali_sim.get('drivers', []):
                driver = driver_data['driver']
                corners = driver_data.get('corners', {})
                corner_stats = corners.get(corner_key)
                
                if corner_stats:
                    median = corner_stats.get('median_speed')
                    if median is not None:
                        qs_drivers.append(driver)
                        qs_medians.append(median)
            
            # 找出共同車手
            common_drivers = list(set(lr_drivers) & set(qs_drivers))
            common_drivers.sort()
            
            if common_drivers:
                # 取得共同車手的數據
                lr_speeds = [lr_medians[lr_drivers.index(d)] for d in common_drivers]
                qs_speeds = [qs_medians[qs_drivers.index(d)] for d in common_drivers]
                
                x = range(len(common_drivers))
                width = 0.35
                
                # 繪製柱狀圖
                bars1 = ax.bar([i - width/2 for i in x], lr_speeds, width, 
                              label='Long Run（高燃油）', alpha=0.8, color='steelblue')
                bars2 = ax.bar([i + width/2 for i in x], qs_speeds, width,
                              label='Quali Sim（低燃油）', alpha=0.8, color='coral')
                
                # 添加數值標籤
                for bar in bars1:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=8)
                
                for bar in bars2:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=8)
                
                ax.set_xlabel('車手', fontsize=11, fontweight='bold')
                ax.set_ylabel('中位數速度 (km/h)', fontsize=11, fontweight='bold')
                ax.set_title(f'{corner_name} (T{corner_number})', fontsize=12, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(common_drivers, rotation=45, ha='right', fontsize=9)
                ax.legend(loc='upper left', fontsize=9)
                ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        save_path = output_path / f"f120_group_comparison_{self.data['year']}_{self.data['race']}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 已儲存: {save_path.name}")
    
    # ==================== 6. Radar Chart ====================
    
    def plot_radar_chart(self, output_path: Path):
        """
        Radar Chart（雷達圖）- 車手全方位評估
        
        顯示前 6 位車手在 3 個彎道的相對排名
        可視覺化車手的「彎道風格」
        """
        mode_a = self.data.get('mode_a_unified', {})
        drivers = mode_a.get('drivers', [])[:6]  # 取前 6 位
        
        if not drivers:
            print("  ⚠️  無數據，跳過 Radar Chart")
            return
        
        corner_types = ['low_speed', 'mid_speed', 'high_speed']
        corner_names = ['低速彎', '中速彎', '高速彎']
        selected_corners = self.data.get('selected_corners', {})
        
        # 計算每位車手的相對排名（百分位數）
        driver_scores = {}
        
        for driver_data in drivers:
            driver = driver_data['driver']
            scores = []
            
            for corner_type in corner_types:
                corner_info = selected_corners.get(corner_type)
                if not corner_info:
                    scores.append(50)  # 預設 50 分
                    continue
                
                corner_number = corner_info['corner_number']
                corner_key = f"{corner_type}_corner_{corner_number}"
                
                corners = driver_data.get('corners', {})
                corner_stats = corners.get(corner_key)
                
                if corner_stats:
                    # 使用 top3_avg 作為評分基準
                    top3_avg = corner_stats.get('top3_avg', corner_stats.get('median_speed', 0))
                    scores.append(top3_avg)
                else:
                    scores.append(0)
            
            driver_scores[driver] = scores
        
        # 正規化分數到 0-100
        for corner_idx in range(3):
            corner_speeds = [scores[corner_idx] for scores in driver_scores.values()]
            if corner_speeds:
                min_speed = min(corner_speeds)
                max_speed = max(corner_speeds)
                speed_range = max_speed - min_speed
                
                if speed_range > 0:
                    for driver in driver_scores:
                        original = driver_scores[driver][corner_idx]
                        normalized = ((original - min_speed) / speed_range) * 100
                        driver_scores[driver][corner_idx] = normalized
        
        # 繪製雷達圖
        angles = np.linspace(0, 2 * np.pi, len(corner_names), endpoint=False).tolist()
        angles += angles[:1]  # 閉合
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(driver_scores)))
        
        for idx, (driver, scores) in enumerate(driver_scores.items()):
            values = scores + scores[:1]  # 閉合
            ax.plot(angles, values, 'o-', linewidth=2, label=driver, color=colors[idx])
            ax.fill(angles, values, alpha=0.15, color=colors[idx])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(corner_names, fontsize=12, fontweight='bold')
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
        ax.grid(True, alpha=0.3)
        
        ax.set_title(f'車手彎道表現雷達圖（Top 6）\n{self.race_info}', 
                    fontsize=14, fontweight='bold', pad=20)
        
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
        
        plt.tight_layout()
        save_path = output_path / f"f120_radar_{self.data['year']}_{self.data['race']}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 已儲存: {save_path.name}")


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='F120 FP2 彎道分析視覺化')
    parser.add_argument('json_file', type=str, nargs='?',
                       help='F120 輸出的 JSON 檔案路徑')
    parser.add_argument('-o', '--output', type=str, default='visualizations',
                       help='輸出目錄（預設：visualizations）')
    
    args = parser.parse_args()
    
    # 如果未指定檔案，自動尋找最新的 F120 JSON
    if not args.json_file:
        json_files = list(Path('json').glob('fp2_corner_all_laps_analysis_*.json'))
        if not json_files:
            print("❌ 找不到 F120 JSON 檔案！")
            print("請先執行: python f1_analysis_modular_main.py -f 120 -y 2024 -r \"Abu Dhabi\" -s FP2")
            return
        
        # 取最新的檔案
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"📁 自動選擇最新檔案: {latest_file}")
        args.json_file = str(latest_file)
    
    # 建立視覺化
    visualizer = F120Visualizer(args.json_file)
    visualizer.create_all_visualizations(args.output)


if __name__ == "__main__":
    main()
