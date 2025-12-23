#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastF1 名次分析實戰範例
展示如何使用 FastF1 數據進行名次分析和視覺化
"""

import fastf1
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
from datetime import datetime

# 設定中文字體
rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

def create_position_change_analysis(year: int, race: str, session_type: str = "R"):
    """創建名次變化分析和視覺化"""
    
    print("=" * 80)
    print(f"🏁 F1 名次變化分析 - {year} {race} {session_type}")
    print("=" * 80)
    
    # 載入賽事數據
    print(f"\n📊 載入賽事數據...")
    session = fastf1.get_session(year, race, session_type)
    session.load()
    print("✅ 數據載入完成\n")
    
    # 獲取賽事結果
    results = session.results
    
    # =================================================================
    # 1. 計算名次變化
    # =================================================================
    position_data = []
    
    for idx, row in results.iterrows():
        if pd.notna(row['GridPosition']) and pd.notna(row['Position']):
            position_change = int(row['GridPosition']) - int(row['Position'])
            
            position_data.append({
                'Driver': row['Abbreviation'],
                'FullName': row['FullName'],
                'Team': row['TeamName'],
                'GridPosition': int(row['GridPosition']),
                'FinalPosition': int(row['Position']),
                'PositionChange': position_change,
                'Points': row['Points'],
                'Status': row['Status']
            })
    
    # 轉換為 DataFrame
    df = pd.DataFrame(position_data)
    
    # 排序：按名次變化排序
    df_sorted = df.sort_values('PositionChange', ascending=False)
    
    # =================================================================
    # 2. 創建視覺化圖表
    # =================================================================
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{year} {race} Grand Prix - 名次變化分析', 
                 fontsize=16, fontweight='bold')
    
    # -----------------------------------------------------------------
    # 圖表 1: 名次變化條形圖
    # -----------------------------------------------------------------
    ax1 = axes[0, 0]
    
    colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' 
              for x in df_sorted['PositionChange']]
    
    bars = ax1.barh(df_sorted['Driver'], df_sorted['PositionChange'], color=colors, alpha=0.7)
    ax1.set_xlabel('名次變化 (正值 = 上升，負值 = 下降)', fontsize=10)
    ax1.set_ylabel('車手', fontsize=10)
    ax1.set_title('車手名次變化排行', fontsize=12, fontweight='bold')
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
    ax1.grid(axis='x', alpha=0.3)
    
    # 添加數值標籤
    for i, (driver, change) in enumerate(zip(df_sorted['Driver'], df_sorted['PositionChange'])):
        if change > 0:
            ax1.text(change + 0.2, i, f'+{change}', va='center', fontsize=8)
        elif change < 0:
            ax1.text(change - 0.2, i, f'{change}', va='center', ha='right', fontsize=8)
    
    # -----------------------------------------------------------------
    # 圖表 2: 起始 vs 最終名次對比
    # -----------------------------------------------------------------
    ax2 = axes[0, 1]
    
    # 繪製連接線
    for _, row in df.iterrows():
        color = 'green' if row['PositionChange'] > 0 else 'red' if row['PositionChange'] < 0 else 'gray'
        ax2.plot([0, 1], [row['GridPosition'], row['FinalPosition']], 
                color=color, alpha=0.6, linewidth=2)
    
    # 繪製起點和終點
    ax2.scatter([0]*len(df), df['GridPosition'], s=100, c='blue', 
               label='起始名次', zorder=3, alpha=0.7)
    ax2.scatter([1]*len(df), df['FinalPosition'], s=100, c='orange', 
               label='最終名次', zorder=3, alpha=0.7)
    
    # 添加車手標籤
    for _, row in df.iterrows():
        ax2.text(-0.05, row['GridPosition'], row['Driver'], 
                ha='right', va='center', fontsize=8)
        ax2.text(1.05, row['FinalPosition'], row['Driver'], 
                ha='left', va='center', fontsize=8)
    
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['起始名次', '最終名次'], fontsize=10)
    ax2.set_ylabel('名次 (數字越小越前)', fontsize=10)
    ax2.set_title('名次變化軌跡', fontsize=12, fontweight='bold')
    ax2.invert_yaxis()  # 反轉 Y 軸，讓第 1 名在最上方
    ax2.legend(loc='upper right')
    ax2.grid(axis='y', alpha=0.3)
    
    # -----------------------------------------------------------------
    # 圖表 3: 名次變化分布
    # -----------------------------------------------------------------
    ax3 = axes[1, 0]
    
    # 統計名次變化分布
    gained = df[df['PositionChange'] > 0]
    lost = df[df['PositionChange'] < 0]
    same = df[df['PositionChange'] == 0]
    
    categories = ['上升', '下降', '不變']
    counts = [len(gained), len(lost), len(same)]
    colors_dist = ['green', 'red', 'gray']
    
    wedges, texts, autotexts = ax3.pie(counts, labels=categories, colors=colors_dist, 
                                        autopct='%1.1f%%', startangle=90, 
                                        textprops={'fontsize': 10})
    
    ax3.set_title('名次變化分布', fontsize=12, fontweight='bold')
    
    # 添加統計資訊
    stats_text = f"""
    上升: {len(gained)} 位車手
    下降: {len(lost)} 位車手
    不變: {len(same)} 位車手
    
    最大上升: +{df['PositionChange'].max()} 位 ({df[df['PositionChange'] == df['PositionChange'].max()]['Driver'].values[0]})
    最大下降: {df['PositionChange'].min()} 位 ({df[df['PositionChange'] == df['PositionChange'].min()]['Driver'].values[0]})
    """
    ax3.text(1.3, 0, stats_text, transform=ax3.transAxes, 
            fontsize=9, verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    # -----------------------------------------------------------------
    # 圖表 4: 前 10 名車手詳細對比
    # -----------------------------------------------------------------
    ax4 = axes[1, 1]
    
    # 選擇名次變化最顯著的前 10 名
    top_changes = df_sorted.head(10)
    
    x = np.arange(len(top_changes))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, top_changes['GridPosition'], width, 
                    label='起始名次', color='skyblue', alpha=0.8)
    bars2 = ax4.bar(x + width/2, top_changes['FinalPosition'], width, 
                    label='最終名次', color='orange', alpha=0.8)
    
    ax4.set_xlabel('車手', fontsize=10)
    ax4.set_ylabel('名次', fontsize=10)
    ax4.set_title('Top 10 名次變化車手對比', fontsize=12, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(top_changes['Driver'], rotation=45, ha='right')
    ax4.legend()
    ax4.invert_yaxis()  # 反轉 Y 軸
    ax4.grid(axis='y', alpha=0.3)
    
    # 添加變化箭頭
    for i, (idx, row) in enumerate(top_changes.iterrows()):
        change = row['PositionChange']
        if change > 0:
            ax4.annotate('', xy=(i, row['FinalPosition']), 
                        xytext=(i, row['GridPosition']),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2))
            ax4.text(i, (row['GridPosition'] + row['FinalPosition']) / 2, 
                    f'+{change}', ha='center', va='center', 
                    fontsize=8, color='green', fontweight='bold')
    
    # 調整佈局
    plt.tight_layout()
    
    # 儲存圖表
    filename = f"position_analysis_{year}_{race}_{session_type}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ 圖表已儲存: {filename}")
    
    # 顯示圖表
    plt.show()
    
    # =================================================================
    # 3. 輸出統計報告
    # =================================================================
    print("\n" + "=" * 80)
    print("📊 統計報告")
    print("=" * 80)
    
    print(f"\n總車手數: {len(df)}")
    print(f"名次上升: {len(gained)} 位車手")
    print(f"名次下降: {len(lost)} 位車手")
    print(f"名次不變: {len(same)} 位車手")
    
    print(f"\n🏆 最大名次上升:")
    max_gain = df_sorted.head(1).iloc[0]
    print(f"  {max_gain['Driver']} ({max_gain['FullName']})")
    print(f"  {max_gain['Team']}")
    print(f"  P{max_gain['GridPosition']} → P{max_gain['FinalPosition']} (上升 {max_gain['PositionChange']} 位)")
    
    print(f"\n⚠️  最大名次下降:")
    max_loss = df_sorted.tail(1).iloc[0]
    print(f"  {max_loss['Driver']} ({max_loss['FullName']})")
    print(f"  {max_loss['Team']}")
    print(f"  P{max_loss['GridPosition']} → P{max_loss['FinalPosition']} (下降 {abs(max_loss['PositionChange'])} 位)")
    
    # 平均名次變化
    avg_change = df['PositionChange'].mean()
    print(f"\n📈 平均名次變化: {avg_change:.2f} 位")
    
    return df

if __name__ == "__main__":
    # 測試案例
    df = create_position_change_analysis(
        year=2024,
        race="Japan",
        session_type="R"
    )
    
    print("\n" + "=" * 80)
    print("✅ 分析完成")
    print("=" * 80)
