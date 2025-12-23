#!/usr/bin/env python3
"""
2025 全賽季起跑反應分布圖
Season Start Reaction Distribution Chart

分析所有 2025 賽事的起跑反應數據，生成類似箱形圖的分布圖
"""
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# F1 2025 車手顏色
TEAM_COLORS = {
    'VER': '#3671C6', 'NOR': '#FF8000', 'PIA': '#FF8000',
    'LEC': '#E8002D', 'SAI': '#E8002D', 'HAM': '#27F4D2', 
    'RUS': '#27F4D2', 'ALO': '#229971', 'STR': '#229971',
    'GAS': '#FF87BC', 'DOO': '#52E252', 'TSU': '#6692FF',
    'LAW': '#6692FF', 'ALB': '#1868DB', 'COL': '#1868DB',
    'HUL': '#B6BABD', 'BEA': '#52E252', 'OCO': '#FF87BC',
    'HAD': '#B6BABD', 'ANT': '#52E252', 'BOT': '#C92D4B',
    'ZHO': '#C92D4B', 'MAG': '#B6BABD', 'RIC': '#6692FF',
}

# 2025 車手代號對照
DRIVER_NAMES = {
    '1': 'VER', '4': 'NOR', '5': 'BEA', '6': 'TSU', '10': 'GAS',
    '12': 'DOO', '14': 'ALO', '16': 'LEC', '18': 'STR', '22': 'ANT',
    '23': 'ALB', '27': 'HUL', '30': 'LAW', '31': 'OCO', '43': 'COL',
    '44': 'HAM', '55': 'SAI', '63': 'RUS', '81': 'PIA', '87': 'HAD'
}


def parse_timestamp(ts: str) -> float:
    """解析 timestamp 字串為秒數"""
    if not ts:
        return 0.0
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def interpolate_time(t1: float, v1: float, t2: float, v2: float, target_v: float) -> float:
    """線性插值計算達到目標速度的時間"""
    if v2 == v1:
        return t1
    ratio = (target_v - v1) / (v2 - v1)
    return t1 + ratio * (t2 - t1)


def analyze_race(race_dir: Path) -> dict:
    """分析單場賽事的起跑反應"""
    results = {}
    
    # 檢查必要文件
    session_file = race_dir / 'SessionData.json'
    cardata_file = race_dir / 'CarData.json'
    
    if not session_file.exists() or not cardata_file.exists():
        return results
    
    try:
        # 1. 獲取比賽開始時間
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        race_start_ts = None
        for rec in session_data.get('records', []):
            status = rec.get('data', {}).get('StatusSeries', {})
            if isinstance(status, dict):
                for key, val in status.items():
                    if isinstance(val, dict) and val.get('SessionStatus') == 'Started':
                        race_start_ts = parse_timestamp(rec.get('timestamp', ''))
                        break
            if race_start_ts:
                break
        
        if not race_start_ts:
            return results
        
        # 2. 讀取 CarData
        with open(cardata_file, 'r', encoding='utf-8') as f:
            cardata = json.load(f)
        
        # 3. 收集車手速度數據
        driver_speeds = defaultdict(list)
        
        for rec in cardata.get('records', []):
            ts = parse_timestamp(rec.get('timestamp', ''))
            
            # 只分析起跑後 30 秒內的數據
            if ts < race_start_ts or ts > race_start_ts + 30:
                continue
            
            entries = rec.get('data', {}).get('Entries', [])
            if not entries:
                continue
            
            cars = entries[0].get('Cars', {})
            
            for drv_num, name in DRIVER_NAMES.items():
                if drv_num in cars:
                    speed = cars[drv_num].get('Channels', {}).get('2', 0)
                    relative_time = ts - race_start_ts
                    driver_speeds[name].append((relative_time, speed))
        
        # 4. 計算加速時間
        for name, speeds in driver_speeds.items():
            if not speeds or len(speeds) < 2:
                continue
            
            speeds.sort(key=lambda x: x[0])
            t10, t20 = None, None
            
            for i in range(1, len(speeds)):
                t_prev, v_prev = speeds[i-1]
                t_curr, v_curr = speeds[i]
                
                if t10 is None and v_prev < 10 <= v_curr:
                    t10 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 10)
                
                if t20 is None and v_prev < 20 <= v_curr:
                    t20 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 20)
            
            if t10 and t20:
                results[name] = {'t10': t10, 't20': t20}
        
    except Exception as e:
        print(f"  Error analyzing {race_dir.name}: {e}")
    
    return results


def create_distribution_chart(all_data: dict, metric: str = 't10'):
    """創建分布圖"""
    
    # 收集每位車手的所有數據
    driver_data = defaultdict(list)
    
    for race_name, race_results in all_data.items():
        for driver, times in race_results.items():
            if times.get(metric):
                driver_data[driver].append({
                    'time': times[metric],
                    'race': race_name
                })
    
    # 只保留有足夠數據的車手
    driver_data = {k: v for k, v in driver_data.items() if len(v) >= 3}
    
    # 按中位數排序車手
    driver_medians = {}
    for driver, data in driver_data.items():
        times = [d['time'] for d in data]
        driver_medians[driver] = np.median(times)
    
    sorted_drivers = sorted(driver_medians.keys(), key=lambda x: driver_medians[x])
    
    # 創建圖表
    fig, ax = plt.subplots(figsize=(18, 10))
    
    x_positions = np.arange(len(sorted_drivers))
    
    for i, driver in enumerate(sorted_drivers):
        data = driver_data[driver]
        times = [d['time'] for d in data]
        races = [d['race'] for d in data]
        
        color = TEAM_COLORS.get(driver, '#888888')
        
        # 繪製箱形圖背景
        q1 = np.percentile(times, 25)
        q3 = np.percentile(times, 75)
        median = np.median(times)
        
        # 箱形區域 (半透明)
        rect = mpatches.Rectangle(
            (i - 0.35, q1), 0.7, q3 - q1,
            facecolor=color, alpha=0.3, edgecolor=color, linewidth=1
        )
        ax.add_patch(rect)
        
        # 中位線
        ax.hlines(median, i - 0.35, i + 0.35, colors=color, linewidth=2)
        
        # 散點 (帶圈數標籤)
        jitter = np.random.uniform(-0.25, 0.25, len(times))
        
        for j, (time, race) in enumerate(zip(times, races)):
            # 從賽事名稱提取圈數或索引
            race_idx = list(all_data.keys()).index(race) + 1
            
            ax.scatter(i + jitter[j], time, c=color, s=50, alpha=0.8, 
                      edgecolors='white', linewidth=0.5, zorder=5)
            ax.annotate(str(race_idx), (i + jitter[j], time), 
                       fontsize=6, ha='center', va='center', color='white',
                       weight='bold')
    
    # 設置軸
    ax.set_xticks(x_positions)
    ax.set_xticklabels(sorted_drivers, fontsize=11, weight='bold')
    
    # 為 X 軸標籤添加顏色背景
    for i, driver in enumerate(sorted_drivers):
        color = TEAM_COLORS.get(driver, '#888888')
        ax.get_xticklabels()[i].set_bbox(dict(
            facecolor=color, alpha=0.7, edgecolor='none', pad=2
        ))
        ax.get_xticklabels()[i].set_color('white')
    
    # 標題和軸標籤
    metric_name = "0-10 km/h (Clutch Reaction)" if metric == 't10' else "0-20 km/h (Start Reaction)"
    ax.set_title(f'2025 Season Start Reaction Distribution\n{metric_name}', 
                fontsize=16, weight='bold', pad=20)
    ax.set_ylabel('Time (seconds)', fontsize=12)
    ax.set_xlabel('Driver', fontsize=12)
    
    # 網格
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    # 添加賽事圖例
    legend_text = "Race Index:\n"
    race_names = list(all_data.keys())
    for idx, race in enumerate(race_names, 1):
        # 簡化賽事名稱
        short_name = race.replace('_Race', '').replace('_', ' ')
        if idx <= 12:
            legend_text += f"{idx}: {short_name}\n"
    if len(race_names) > 12:
        legend_text += f"... (+{len(race_names) - 12} more)"
    
    ax.text(1.02, 0.98, legend_text, transform=ax.transAxes, fontsize=8,
           verticalalignment='top', family='monospace',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # 保存圖表
    output_dir = Path('charts')
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'2025_season_start_reaction_{metric}_{timestamp}.png'
    filepath = output_dir / filename
    
    plt.savefig(filepath, dpi=150, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    print(f"\n圖表已保存: {filepath}")
    
    plt.close()  # 關閉圖表避免阻塞
    
    return filepath


def main():
    base_dir = Path(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\json\LiveF1\2025")
    
    print("=" * 60)
    print("2025 全賽季起跑反應分析")
    print("=" * 60)
    
    # 找出所有正賽
    race_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.endswith('_Race')])
    
    print(f"\n找到 {len(race_dirs)} 場正賽:")
    
    all_data = {}
    
    for race_dir in race_dirs:
        race_name = race_dir.name.replace('_Race', '')
        print(f"  分析: {race_name}...", end='')
        
        results = analyze_race(race_dir)
        
        if results:
            all_data[race_name] = results
            print(f" ✓ ({len(results)} 車手)")
        else:
            print(" ✗ (無數據)")
    
    print(f"\n總計: {len(all_data)} 場賽事有效數據")
    
    # 統計每位車手的數據量
    driver_counts = defaultdict(int)
    for race_results in all_data.values():
        for driver in race_results.keys():
            driver_counts[driver] += 1
    
    print("\n車手數據量:")
    for driver, count in sorted(driver_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {driver}: {count} 場賽事")
    
    # 生成分布圖
    print("\n生成 0-10 km/h 分布圖...")
    create_distribution_chart(all_data, 't10')
    
    print("\n生成 0-20 km/h 分布圖...")
    create_distribution_chart(all_data, 't20')
    
    print("\n完成！")


if __name__ == '__main__':
    main()
