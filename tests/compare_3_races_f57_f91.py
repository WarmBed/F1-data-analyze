"""
3 場比賽 F91 預測準確度分析
比較 ML 預測 vs 真實圈速：Japan, Abu Dhabi, Mexico (2025)
"""

import json
import matplotlib
matplotlib.use('Agg')  # 非互動模式
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 比賽設定
races = [
    {"name": "Japan", "display": "日本站 (鈴鹿)"},
    {"name": "Abu_Dhabi", "display": "阿布達比站"},
    {"name": "Mexico", "display": "墨西哥站"}
]

def load_race_data(race_name: str):
    """載入真實正賽數據"""
    cache_file = Path(f"f1_analysis_cache/f1_data_2025_{race_name}_R.pkl")
    if cache_file.exists():
        import pickle
        with open(cache_file, 'rb') as f:
            session = pickle.load(f)
        return session
    return None

def load_f57_prediction(race_name: str):
    """載入 F57 預測數據"""
    json_dir = Path("json")
    f57_files = list(json_dir.glob(f"fp2_race_prediction_2025_{race_name}_*.json"))
    if f57_files:
        with open(f57_files[-1], 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_f91_prediction(race_name: str):
    """載入 F91 預測數據"""
    json_dir = Path("json")
    f91_files = list(json_dir.glob(f"fp2_race_ml_prediction_v2_2025_{race_name}_*.json"))
    if f91_files:
        with open(f91_files[-1], 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def extract_fastest_driver_laps(session, driver_code: str = "VER"):
    """從 FastF1 session 提取車手圈速"""
    try:
        driver_laps = session.laps.pick_driver(driver_code)
        lap_times = []
        lap_numbers = []
        
        for idx, lap in driver_laps.iterrows():
            if lap['LapTime'] is not None and not pd.isna(lap['LapTime']):
                lap_times.append(lap['LapTime'].total_seconds())
                lap_numbers.append(lap['LapNumber'])
        
        return lap_numbers, lap_times
    except:
        return [], []

def calculate_mae(real_laps, predicted_laps):
    """計算平均絕對誤差（MAE）"""
    errors = []
    for lap_num, real_time in real_laps.items():
        if lap_num in predicted_laps:
            pred_time = predicted_laps[lap_num]
            errors.append(abs(real_time - pred_time))
    
    if errors:
        return np.mean(errors)
    return None

def plot_comparison():
    """繪製 3 場比賽對比圖表"""
    import pandas as pd
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('F57 vs F91 預測準確度對比 (2025 賽季)', fontsize=16, fontweight='bold')
    
    summary_data = []
    
    for idx, race_config in enumerate(races):
        ax = axes[idx]
        race_name = race_config["name"]
        display_name = race_config["display"]
        
        # 載入數據
        session = load_race_data(race_name)
        f57_data = load_f57_prediction(race_name)
        f91_data = load_f91_prediction(race_name)
        
        if not session or not f57_data or not f91_data:
            ax.text(0.5, 0.5, f"數據不完整\n{race_name}", 
                   ha='center', va='center', fontsize=12)
            ax.set_title(display_name)
            continue
        
        # 提取真實圈速 (VER)
        real_laps, real_times = extract_fastest_driver_laps(session, "VER")
        if not real_laps:
            ax.text(0.5, 0.5, "找不到 VER 數據", ha='center', va='center')
            ax.set_title(display_name)
            continue
        
        real_dict = dict(zip(real_laps, real_times))
        
        # 提取 F57 預測
        f57_dict = {}
        for driver in f57_data.get("predictions", []):
            if driver["driver_code"] == "VER":
                for lap_info in driver["laps"]:
                    f57_dict[lap_info["lap"]] = lap_info["predicted_laptime"]
                break
        
        # 提取 F91 預測
        f91_dict = {}
        for driver in f91_data.get("predictions", []):
            if driver["driver_code"] == "VER":
                for lap_info in driver["laps"]:
                    f91_dict[lap_info["lap"]] = lap_info["predicted_laptime"]
                break
        
        # 計算 MAE
        f57_mae = calculate_mae(real_dict, f57_dict)
        f91_mae = calculate_mae(real_dict, f91_dict)
        
        # 繪製圖表
        common_laps = sorted(set(real_dict.keys()) & set(f57_dict.keys()) & set(f91_dict.keys()))
        
        real_plot = [real_dict[lap] for lap in common_laps]
        f57_plot = [f57_dict[lap] for lap in common_laps]
        f91_plot = [f91_dict[lap] for lap in common_laps]
        
        ax.plot(common_laps, real_plot, 'o-', label='真實圈速', linewidth=2, markersize=4)
        ax.plot(common_laps, f57_plot, 's--', label=f'F57 預測 (MAE={f57_mae:.3f}s)', linewidth=1.5, markersize=3, alpha=0.7)
        ax.plot(common_laps, f91_plot, '^--', label=f'F91 預測 (MAE={f91_mae:.3f}s)', linewidth=1.5, markersize=3, alpha=0.7)
        
        ax.set_title(f"{display_name}\nVER 圈速對比", fontsize=12, fontweight='bold')
        ax.set_xlabel('圈數', fontsize=10)
        ax.set_ylabel('圈速 (秒)', fontsize=10)
        ax.legend(fontsize=9, loc='best')
        ax.grid(True, alpha=0.3)
        
        # 儲存摘要數據
        if f57_mae and f91_mae:
            improvement = ((f57_mae - f91_mae) / f57_mae) * 100
            summary_data.append({
                "race": display_name,
                "f57_mae": f57_mae,
                "f91_mae": f91_mae,
                "improvement": improvement
            })
    
    plt.tight_layout()
    
    # 儲存圖表
    output_file = "reports/f57_vs_f91_3_races_comparison.png"
    Path("reports").mkdir(exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ 圖表已儲存: {output_file}")
    plt.close()  # 關閉圖表，不顯示視窗
    
    # 顯示摘要統計
    print("\n" + "="*60)
    print("F57 vs F91 準確度對比摘要 (3 場比賽)")
    print("="*60)
    for data in summary_data:
        print(f"\n{data['race']}:")
        print(f"  F57 MAE: {data['f57_mae']:.4f}s")
        print(f"  F91 MAE: {data['f91_mae']:.4f}s")
        print(f"  F91 改善: {data['improvement']:.2f}%")
    
    # 計算整體平均
    if summary_data:
        avg_f57 = np.mean([d["f57_mae"] for d in summary_data])
        avg_f91 = np.mean([d["f91_mae"] for d in summary_data])
        avg_improvement = np.mean([d["improvement"] for d in summary_data])
        
        print(f"\n{'='*60}")
        print("整體平均:")
        print(f"  F57 平均 MAE: {avg_f57:.4f}s")
        print(f"  F91 平均 MAE: {avg_f91:.4f}s")
        print(f"  F91 平均改善: {avg_improvement:.2f}%")
        print("="*60)

if __name__ == "__main__":
    print("\n開始生成 3 場比賽對比圖表...")
    plot_comparison()
