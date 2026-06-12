#!/usr/bin/env python3
"""
2025 全賽季起跑反應分布圖 (含反應速度) - PyQt5
"""
import sys
import json
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

print("Starting...")

# 設置
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

TEAM_COLORS = {
    'VER': '#3671C6', 'NOR': '#FF8000', 'PIA': '#FF8000',
    'LEC': '#E8002D', 'SAI': '#E8002D', 'HAM': '#27F4D2', 
    'RUS': '#27F4D2', 'ALO': '#229971', 'STR': '#229971',
    'GAS': '#FF87BC', 'DOO': '#52E252', 'TSU': '#6692FF',
    'LAW': '#6692FF', 'ALB': '#1868DB', 'COL': '#1868DB',
    'HUL': '#B6BABD', 'BEA': '#52E252', 'OCO': '#FF87BC',
    'HAD': '#B6BABD', 'ANT': '#52E252',
}

DRIVER_NAMES = {
    '1': 'VER', '4': 'NOR', '5': 'BEA', '6': 'TSU', '10': 'GAS',
    '12': 'DOO', '14': 'ALO', '16': 'LEC', '18': 'STR', '22': 'ANT',
    '23': 'ALB', '27': 'HUL', '30': 'LAW', '31': 'OCO', '43': 'COL',
    '44': 'HAM', '55': 'SAI', '63': 'RUS', '81': 'PIA', '87': 'HAD'
}


def parse_timestamp(ts):
    if not ts:
        return 0.0
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def interpolate_time(t1, v1, t2, v2, target_v):
    if v2 == v1:
        return t1
    ratio = (target_v - v1) / (v2 - v1)
    return t1 + ratio * (t2 - t1)


def analyze_race(race_dir):
    """
    分析單場比賽的起跑數據
    返回: {driver_name: {'t10': ..., 't20': ..., 'reaction_speed': ..., ...}}
    """
    results = {}
    session_file = race_dir / 'SessionData.json'
    cardata_file = race_dir / 'CarData.json'
    
    if not session_file.exists() or not cardata_file.exists():
        return results
    
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Find race start timestamp
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
        
        with open(cardata_file, 'r', encoding='utf-8') as f:
            cardata = json.load(f)
        
        # Collect driver speeds
        driver_speeds = defaultdict(list)
        
        for rec in cardata.get('records', []):
            ts = parse_timestamp(rec.get('timestamp', ''))
            if ts < race_start_ts or ts > race_start_ts + 60:
                continue
            
            entries = rec.get('data', {}).get('Entries', [])
            if not entries:
                continue
            
            cars = entries[0].get('Cars', {})
            for drv_num, name in DRIVER_NAMES.items():
                if drv_num in cars:
                    speed = cars[drv_num].get('Channels', {}).get('2', 0)
                    driver_speeds[name].append((ts - race_start_ts, speed))
        
        # Find second batch time (all 20 drivers have data)
        all_times = set()
        for speeds in driver_speeds.values():
            all_times.update(t for t, _ in speeds)
        
        batch_times = sorted(all_times)
        second_batch_time = None
        if len(batch_times) >= 2:
            second_batch_time = batch_times[1]
        
        # Analyze each driver
        for name, speeds in driver_speeds.items():
            if not speeds or len(speeds) < 2:
                continue
            
            speeds.sort(key=lambda x: x[0])
            
            # Find reaction speed at second batch
            reaction_speed = None
            if second_batch_time:
                for t, v in speeds:
                    if abs(t - second_batch_time) < 0.01:  # Within 10ms
                        reaction_speed = v
                        break
            
            # Find t10, t20, t50, t100 via interpolation
            t10, t20, t50, t100 = None, None, None, None
            
            for i in range(1, len(speeds)):
                t_prev, v_prev = speeds[i-1]
                t_curr, v_curr = speeds[i]
                
                if t10 is None and v_prev < 10 <= v_curr:
                    t10 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 10)
                
                if t20 is None and v_prev < 20 <= v_curr:
                    t20 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 20)
                
                if t50 is None and v_prev < 50 <= v_curr:
                    t50 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 50)
                
                if t100 is None and v_prev < 100 <= v_curr:
                    t100 = interpolate_time(t_prev, v_prev, t_curr, v_curr, 100)
            
            # Filter outliers
            if t10 and t20:
                if t10 <= 2.5 and t20 <= 3.5:
                    results[name] = {
                        't10': t10, 
                        't20': t20, 
                        't50': t50, 
                        't100': t100,
                        'reaction_speed': reaction_speed,
                        'batch_time': second_batch_time
                    }
                else:
                    print(f"  Filtered {name}: T10={t10:.3f}s, T20={t20:.3f}s (outlier)")
    except Exception as e:
        print(f"Error: {e}")
    
    return results


def create_distribution_chart(driver_data, metric_key, title, ylabel, sort_reverse=False):
    """
    創建分布圖
    metric_key: 't10', 't20', 'reaction_speed' 等
    sort_reverse: True 表示由高到低排序 (反應速度), False 表示由低到高 (時間)
    """
    # Sort by median
    driver_medians = {}
    for driver, data in driver_data.items():
        values = [d[metric_key] for d in data if d.get(metric_key) is not None]
        if values:
            driver_medians[driver] = np.median(values)
    
    sorted_drivers = sorted(driver_medians.keys(), 
                           key=lambda x: driver_medians[x], 
                           reverse=sort_reverse)
    
    print(f"Plotting {len(sorted_drivers)} drivers for {metric_key}...")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(18, 10))
    
    for i, driver in enumerate(sorted_drivers):
        data = [d for d in driver_data[driver] if d.get(metric_key) is not None]
        values = [d[metric_key] for d in data]
        color = TEAM_COLORS.get(driver, '#888888')
        
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        median = np.median(values)
        
        # Box
        if sort_reverse:  # 反應速度: 高在上, 低在下
            rect = mpatches.Rectangle((i - 0.35, q1), 0.7, q3 - q1,
                facecolor=color, alpha=0.3, edgecolor=color, linewidth=1)
        else:  # 時間: 低在上, 高在下
            rect = mpatches.Rectangle((i - 0.35, q1), 0.7, q3 - q1,
                facecolor=color, alpha=0.3, edgecolor=color, linewidth=1)
        ax.add_patch(rect)
        ax.hlines(median, i - 0.35, i + 0.35, colors=color, linewidth=2)
        
        # Scatter with race numbers
        jitter = np.random.uniform(-0.25, 0.25, len(values))
        for j, value in enumerate(values):
            race_idx = list(all_data.keys()).index(data[j]['race']) + 1
            ax.scatter(i + jitter[j], value, c=color, s=60, alpha=0.8, 
                      edgecolors='white', linewidth=0.5, zorder=5)
            ax.annotate(str(race_idx), (i + jitter[j], value), 
                       fontsize=6, ha='center', va='center', color='white', weight='bold')
    
    # X-axis labels
    ax.set_xticks(range(len(sorted_drivers)))
    ax.set_xticklabels(sorted_drivers, fontsize=11, weight='bold')
    
    for i, driver in enumerate(sorted_drivers):
        color = TEAM_COLORS.get(driver, '#888888')
        ax.get_xticklabels()[i].set_bbox(dict(facecolor=color, alpha=0.7, edgecolor='none', pad=2))
    
    # Title and labels
    ax.set_title(title, fontsize=16, weight='bold', pad=20)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_xlabel('Driver', fontsize=12)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    fig.tight_layout()
    
    return fig


# ============ Main ============
base_dir = Path(__file__).parent / "json" / "LiveF1" / "2025"
race_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.endswith('_Race')])

print(f"Found {len(race_dirs)} races")

all_data = {}
for race_dir in race_dirs:
    race_name = race_dir.name.replace('_Race', '')
    results = analyze_race(race_dir)
    if results:
        all_data[race_name] = results
        print(f"  {race_name}: {len(results)} drivers")

print(f"Total: {len(all_data)} races")

# Collect driver data for each metric
def collect_metric_data(metric_key):
    driver_data = defaultdict(list)
    for race_name, race_results in all_data.items():
        for driver, metrics in race_results.items():
            value = metrics.get(metric_key)
            if value is not None:
                driver_data[driver].append({
                    'race': race_name,
                    metric_key: value
                })
    
    # Filter drivers with at least 3 races
    driver_data = {k: v for k, v in driver_data.items() if len(v) >= 3}
    return driver_data

# Create Qt Application
app = QApplication(sys.argv)

# Create main window
main_window = QMainWindow()
main_window.setWindowTitle("2025 Season Start Reaction Analysis (With Reaction Speed)")
main_window.setGeometry(100, 100, 1800, 1000)

# Create tab widget
tab_widget = QTabWidget()
main_window.setCentralWidget(tab_widget)

# ============ Tab 1: Reaction Speed ============
reaction_data = collect_metric_data('reaction_speed')
fig_reaction = create_distribution_chart(
    reaction_data, 
    'reaction_speed',
    'Reaction Speed at 2nd Batch (~2s after green light)',
    'Speed (km/h)',
    sort_reverse=True  # Higher is better
)
reaction_widget = QWidget()
reaction_layout = QVBoxLayout()
reaction_canvas = FigureCanvas(fig_reaction)
reaction_layout.addWidget(reaction_canvas)
reaction_widget.setLayout(reaction_layout)
tab_widget.addTab(reaction_widget, "Reaction Speed")
print("Reaction Speed chart created")

# ============ Tab 2: T10 (0-10 km/h) ============
t10_data = collect_metric_data('t10')
fig_t10 = create_distribution_chart(
    t10_data,
    't10',
    '0-10 km/h Time Distribution (2025 Season)',
    'Time (seconds)',
    sort_reverse=False  # Lower is better
)
t10_widget = QWidget()
t10_layout = QVBoxLayout()
t10_canvas = FigureCanvas(fig_t10)
t10_layout.addWidget(t10_canvas)
t10_widget.setLayout(t10_layout)
tab_widget.addTab(t10_widget, "T10 (0-10 km/h)")
print("T10 chart created")

# ============ Tab 3: T20 (0-20 km/h) ============
t20_data = collect_metric_data('t20')
fig_t20 = create_distribution_chart(
    t20_data,
    't20',
    '0-20 km/h Time Distribution (2025 Season)',
    'Time (seconds)',
    sort_reverse=False
)
t20_widget = QWidget()
t20_layout = QVBoxLayout()
t20_canvas = FigureCanvas(fig_t20)
t20_layout.addWidget(t20_canvas)
t20_widget.setLayout(t20_layout)
tab_widget.addTab(t20_widget, "T20 (0-20 km/h)")
print("T20 chart created")

# ============ Tab 4: T50 (0-50 km/h) ============
t50_data = collect_metric_data('t50')
fig_t50 = create_distribution_chart(
    t50_data,
    't50',
    '0-50 km/h Time Distribution (2025 Season)',
    'Time (seconds)',
    sort_reverse=False
)
t50_widget = QWidget()
t50_layout = QVBoxLayout()
t50_canvas = FigureCanvas(fig_t50)
t50_layout.addWidget(t50_canvas)
t50_widget.setLayout(t50_layout)
tab_widget.addTab(t50_widget, "T50 (0-50 km/h)")
print("T50 chart created")

# ============ Tab 5: T100 (0-100 km/h) ============
t100_data = collect_metric_data('t100')
fig_t100 = create_distribution_chart(
    t100_data,
    't100',
    '0-100 km/h Time Distribution (2025 Season)',
    'Time (seconds)',
    sort_reverse=False
)
t100_widget = QWidget()
t100_layout = QVBoxLayout()
t100_canvas = FigureCanvas(fig_t100)
t100_layout.addWidget(t100_canvas)
t100_widget.setLayout(t100_layout)
tab_widget.addTab(t100_widget, "T100 (0-100 km/h)")
print("T100 chart created")

# Show main window
main_window.show()
print("Done! Close the window to exit.")

# Start Qt event loop
sys.exit(app.exec_())
