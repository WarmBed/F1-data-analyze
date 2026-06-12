#!/usr/bin/env python3
"""
簡化版：2025 全賽季起跑反應分布圖 (PyQt5)
"""
import sys
import json
import matplotlib
matplotlib.use('Qt5Agg')  # PyQt5 後端
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
    results = {}
    session_file = race_dir / 'SessionData.json'
    cardata_file = race_dir / 'CarData.json'
    
    if not session_file.exists() or not cardata_file.exists():
        return results
    
    try:
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
        
        with open(cardata_file, 'r', encoding='utf-8') as f:
            cardata = json.load(f)
        
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
        
        for name, speeds in driver_speeds.items():
            if not speeds or len(speeds) < 2:
                continue
            
            speeds.sort(key=lambda x: x[0])
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
            # T10 < 2.5s, T20 < 3.5s, T50 < 6s, T100 < 12s
            if t10 and t20:
                if t10 <= 2.5 and t20 <= 3.5:
                    results[name] = {'t10': t10, 't20': t20, 't50': t50, 't100': t100}
                else:
                    print(f"  Filtered {name}: T10={t10:.3f}s, T20={t20:.3f}s (outlier)")
    except Exception as e:
        print(f"Error: {e}")
    
    return results


# Main
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

# Collect driver data for T10
driver_data = defaultdict(list)
for race_name, race_results in all_data.items():
    for driver, times in race_results.items():
        t10_val = times.get('t10')
        if t10_val and t10_val <= 2.5:
            driver_data[driver].append({'time': t10_val, 'race': race_name})

driver_data = {k: v for k, v in driver_data.items() if len(v) >= 3}

# Sort by median
driver_medians = {}
for driver, data in driver_data.items():
    times = [d['time'] for d in data]
    driver_medians[driver] = np.median(times)

sorted_drivers = sorted(driver_medians.keys(), key=lambda x: driver_medians[x])

print(f"Plotting {len(sorted_drivers)} drivers...")

# Create Qt Application
app = QApplication(sys.argv)

# Create main window
main_window = QMainWindow()
main_window.setWindowTitle("2025 Season Start Reaction Analysis")
main_window.setGeometry(100, 100, 1800, 1000)

# Create tab widget
tab_widget = QTabWidget()
main_window.setCentralWidget(tab_widget)

# ============ T10 Chart ============
fig, ax = plt.subplots(figsize=(18, 10))

for i, driver in enumerate(sorted_drivers):
    data = driver_data[driver]
    times = [d['time'] for d in data]
    color = TEAM_COLORS.get(driver, '#888888')
    
    q1 = np.percentile(times, 25)
    q3 = np.percentile(times, 75)
    median = np.median(times)
    
    rect = mpatches.Rectangle((i - 0.35, q1), 0.7, q3 - q1,
        facecolor=color, alpha=0.3, edgecolor=color, linewidth=1)
    ax.add_patch(rect)
    ax.hlines(median, i - 0.35, i + 0.35, colors=color, linewidth=2)
    
    jitter = np.random.uniform(-0.25, 0.25, len(times))
    for j, time in enumerate(times):
        race_idx = list(all_data.keys()).index(data[j]['race']) + 1
        ax.scatter(i + jitter[j], time, c=color, s=60, alpha=0.8, 
                  edgecolors='white', linewidth=0.5, zorder=5)
        ax.annotate(str(race_idx), (i + jitter[j], time), 
                   fontsize=6, ha='center', va='center', color='white', weight='bold')

ax.set_xticks(range(len(sorted_drivers)))
ax.set_xticklabels(sorted_drivers, fontsize=11, weight='bold')

for i, driver in enumerate(sorted_drivers):
    color = TEAM_COLORS.get(driver, '#888888')
    ax.get_xticklabels()[i].set_bbox(dict(facecolor=color, alpha=0.7, edgecolor='none', pad=2))
    ax.get_xticklabels()[i].set_color('white')

ax.set_title('2025 Season Start Reaction Distribution\n0-10 km/h (Clutch Reaction)', 
            fontsize=16, weight='bold', pad=20)
ax.set_ylabel('Time (seconds)', fontsize=12)
ax.set_xlabel('Driver', fontsize=12)
ax.yaxis.grid(True, linestyle='--', alpha=0.3)
ax.set_axisbelow(True)

fig.tight_layout()

# Create T10 tab
t10_widget = QWidget()
t10_layout = QVBoxLayout()
t10_canvas = FigureCanvas(fig)
t10_layout.addWidget(t10_canvas)
t10_widget.setLayout(t10_layout)
tab_widget.addTab(t10_widget, "T10 (0-10 km/h)")

print("T10 chart created")

# ============ T20 Chart ============
fig2, ax2 = plt.subplots(figsize=(18, 10))

driver_data_t20 = defaultdict(list)
for race_name, race_results in all_data.items():
    for driver, times in race_results.items():
        t20_val = times.get('t20')
        if t20_val and t20_val <= 3.5:
            driver_data_t20[driver].append({'time': t20_val, 'race': race_name})

driver_data_t20 = {k: v for k, v in driver_data_t20.items() if len(v) >= 3}

driver_medians_t20 = {}
for driver, data in driver_data_t20.items():
    times = [d['time'] for d in data]
    driver_medians_t20[driver] = np.median(times)

sorted_drivers_t20 = sorted(driver_medians_t20.keys(), key=lambda x: driver_medians_t20[x])

for i, driver in enumerate(sorted_drivers_t20):
    data = driver_data_t20[driver]
    times = [d['time'] for d in data]
    color = TEAM_COLORS.get(driver, '#888888')
    
    q1 = np.percentile(times, 25)
    q3 = np.percentile(times, 75)
    median = np.median(times)
    
    rect = mpatches.Rectangle((i - 0.35, q1), 0.7, q3 - q1,
        facecolor=color, alpha=0.3, edgecolor=color, linewidth=1)
    ax2.add_patch(rect)
    ax2.hlines(median, i - 0.35, i + 0.35, colors=color, linewidth=2)
    
    jitter = np.random.uniform(-0.25, 0.25, len(times))
    for j, time in enumerate(times):
        race_idx = list(all_data.keys()).index(data[j]['race']) + 1
        ax2.scatter(i + jitter[j], time, c=color, s=60, alpha=0.8, 
                  edgecolors='white', linewidth=0.5, zorder=5)
        ax2.annotate(str(race_idx), (i + jitter[j], time), 
                   fontsize=6, ha='center', va='center', color='white', weight='bold')

ax2.set_xticks(range(len(sorted_drivers_t20)))
ax2.set_xticklabels(sorted_drivers_t20, fontsize=11, weight='bold')

for i, driver in enumerate(sorted_drivers_t20):
    color = TEAM_COLORS.get(driver, '#888888')
    ax2.get_xticklabels()[i].set_bbox(dict(facecolor=color, alpha=0.7, edgecolor='none', pad=2))
    ax2.get_xticklabels()[i].set_color('white')

ax2.set_title('2025 Season Start Reaction Distribution\n0-20 km/h (Start Reaction)', 
            fontsize=16, weight='bold', pad=20)
ax2.set_ylabel('Time (seconds)', fontsize=12)
ax2.set_xlabel('Driver', fontsize=12)
ax2.yaxis.grid(True, linestyle='--', alpha=0.3)
ax2.set_axisbelow(True)

fig2.tight_layout()

# Create T20 tab
t20_widget = QWidget()
t20_layout = QVBoxLayout()
t20_canvas = FigureCanvas(fig2)
t20_layout.addWidget(t20_canvas)
t20_widget.setLayout(t20_layout)
tab_widget.addTab(t20_widget, "T20 (0-20 km/h)")

print("T20 chart created")

# ============ T50 Chart ============
fig3, ax3 = plt.subplots(figsize=(18, 10))

driver_data_t50 = defaultdict(list)
for race_name, race_results in all_data.items():
    for driver, times in race_results.items():
        t50_val = times.get('t50')
        if t50_val and t50_val <= 6.0:
            driver_data_t50[driver].append({'time': t50_val, 'race': race_name})

driver_data_t50 = {k: v for k, v in driver_data_t50.items() if len(v) >= 3}

driver_medians_t50 = {}
for driver, data in driver_data_t50.items():
    times = [d['time'] for d in data]
    driver_medians_t50[driver] = np.median(times)

sorted_drivers_t50 = sorted(driver_medians_t50.keys(), key=lambda x: driver_medians_t50[x])

for i, driver in enumerate(sorted_drivers_t50):
    data = driver_data_t50[driver]
    times = [d['time'] for d in data]
    color = TEAM_COLORS.get(driver, '#888888')
    
    q1 = np.percentile(times, 25)
    q3 = np.percentile(times, 75)
    median = np.median(times)
    
    rect = mpatches.Rectangle((i - 0.35, q1), 0.7, q3 - q1,
        facecolor=color, alpha=0.3, edgecolor=color, linewidth=1)
    ax3.add_patch(rect)
    ax3.hlines(median, i - 0.35, i + 0.35, colors=color, linewidth=2)
    
    jitter = np.random.uniform(-0.25, 0.25, len(times))
    for j, time in enumerate(times):
        race_idx = list(all_data.keys()).index(data[j]['race']) + 1
        ax3.scatter(i + jitter[j], time, c=color, s=60, alpha=0.8, 
                  edgecolors='white', linewidth=0.5, zorder=5)
        ax3.annotate(str(race_idx), (i + jitter[j], time), 
                   fontsize=6, ha='center', va='center', color='white', weight='bold')

ax3.set_xticks(range(len(sorted_drivers_t50)))
ax3.set_xticklabels(sorted_drivers_t50, fontsize=11, weight='bold')

for i, driver in enumerate(sorted_drivers_t50):
    color = TEAM_COLORS.get(driver, '#888888')
    ax3.get_xticklabels()[i].set_bbox(dict(facecolor=color, alpha=0.7, edgecolor='none', pad=2))
    ax3.get_xticklabels()[i].set_color('white')

ax3.set_title('2025 Season Start Reaction Distribution\n0-50 km/h (Initial Acceleration)', 
            fontsize=16, weight='bold', pad=20)
ax3.set_ylabel('Time (seconds)', fontsize=12)
ax3.set_xlabel('Driver', fontsize=12)
ax3.yaxis.grid(True, linestyle='--', alpha=0.3)
ax3.set_axisbelow(True)

fig3.tight_layout()

# Create T50 tab
t50_widget = QWidget()
t50_layout = QVBoxLayout()
t50_canvas = FigureCanvas(fig3)
t50_layout.addWidget(t50_canvas)
t50_widget.setLayout(t50_layout)
tab_widget.addTab(t50_widget, "T50 (0-50 km/h)")

print("T50 chart created")

# ============ T100 Chart ============
fig4, ax4 = plt.subplots(figsize=(18, 10))

driver_data_t100 = defaultdict(list)
for race_name, race_results in all_data.items():
    for driver, times in race_results.items():
        t100_val = times.get('t100')
        if t100_val and t100_val <= 12.0:
            driver_data_t100[driver].append({'time': t100_val, 'race': race_name})

driver_data_t100 = {k: v for k, v in driver_data_t100.items() if len(v) >= 3}

driver_medians_t100 = {}
for driver, data in driver_data_t100.items():
    times = [d['time'] for d in data]
    driver_medians_t100[driver] = np.median(times)

sorted_drivers_t100 = sorted(driver_medians_t100.keys(), key=lambda x: driver_medians_t100[x])

for i, driver in enumerate(sorted_drivers_t100):
    data = driver_data_t100[driver]
    times = [d['time'] for d in data]
    color = TEAM_COLORS.get(driver, '#888888')
    
    q1 = np.percentile(times, 25)
    q3 = np.percentile(times, 75)
    median = np.median(times)
    
    rect = mpatches.Rectangle((i - 0.35, q1), 0.7, q3 - q1,
        facecolor=color, alpha=0.3, edgecolor=color, linewidth=1)
    ax4.add_patch(rect)
    ax4.hlines(median, i - 0.35, i + 0.35, colors=color, linewidth=2)
    
    jitter = np.random.uniform(-0.25, 0.25, len(times))
    for j, time in enumerate(times):
        race_idx = list(all_data.keys()).index(data[j]['race']) + 1
        ax4.scatter(i + jitter[j], time, c=color, s=60, alpha=0.8, 
                  edgecolors='white', linewidth=0.5, zorder=5)
        ax4.annotate(str(race_idx), (i + jitter[j], time), 
                   fontsize=6, ha='center', va='center', color='white', weight='bold')

ax4.set_xticks(range(len(sorted_drivers_t100)))
ax4.set_xticklabels(sorted_drivers_t100, fontsize=11, weight='bold')

for i, driver in enumerate(sorted_drivers_t100):
    color = TEAM_COLORS.get(driver, '#888888')
    ax4.get_xticklabels()[i].set_bbox(dict(facecolor=color, alpha=0.7, edgecolor='none', pad=2))
    ax4.get_xticklabels()[i].set_color('white')

ax4.set_title('2025 Season Start Reaction Distribution\n0-100 km/h (Full Acceleration)', 
            fontsize=16, weight='bold', pad=20)
ax4.set_ylabel('Time (seconds)', fontsize=12)
ax4.set_xlabel('Driver', fontsize=12)
ax4.yaxis.grid(True, linestyle='--', alpha=0.3)
ax4.set_axisbelow(True)

fig4.tight_layout()

# Create T100 tab
t100_widget = QWidget()
t100_layout = QVBoxLayout()
t100_canvas = FigureCanvas(fig4)
t100_layout.addWidget(t100_canvas)
t100_widget.setLayout(t100_layout)
tab_widget.addTab(t100_widget, "T100 (0-100 km/h)")

print("T100 chart created")

# Show main window
main_window.show()
print("Done! Close the window to exit.")

# Start Qt event loop
sys.exit(app.exec_())
