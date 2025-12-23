"""
3 場比賽 F91 預測 vs 真實圈速對比圖表
比較：Japan, Abu Dhabi, Mexico (2025)
"""

import json
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 比賽設定
races = [
    {"name": "Japan", "display": "日本站 (鈴鹿)"},
    {"name": "Abu_Dhabi", "display": "阿布達比站"},
    {"name": "Mexico", "display": "墨西哥站"}
]

def load_real_laptimes(race_name: str):
    """從 FastF1 緩存載入真實圈速"""
    cache_file = Path(f"f1_analysis_cache/f1_data_2025_{race_name}_R.pkl")
    if not cache_file.exists():
        print(f"  [!] 找不到緩存: {cache_file}")
        return None
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        print(f"  [✓] 載入緩存: {cache_file.name}")
        return cache_data
    except Exception as e:
        print(f"  [!] 載入緩存失敗: {e}")
        return None

def load_f91_prediction(race_name: str):
    """載入 F91 預測數據"""
    json_dir = Path("json")
    f91_files = list(json_dir.glob(f"fp2_race_ml_prediction_v2_2025_{race_name}_*.json"))
    if not f91_files:
        print(f"  [!] 找不到 F91 預測: {race_name}")
        return None
    
    with open(f91_files[-1], 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_driver_laps(cache_data, driver_code: str):
    """從緩存數據提取車手圈速"""
    try:
        laps_data = cache_data.get('laps')
        if laps_data is None:
            print(f"  [!] 緩存中沒有 laps 數據")
            return {}
        
        # 如果是 DataFrame
        if hasattr(laps_data, 'iterrows'):
            driver_laps = laps_data[laps_data['Driver'] == driver_code]
            lap_dict = {}
            
            for idx, lap in driver_laps.iterrows():
                if lap['LapTime'] is not None and not pd.isna(lap['LapTime']):
                    lap_num = int(lap['LapNumber'])
                    # 處理 timedelta
                    if hasattr(lap['LapTime'], 'total_seconds'):
                        lap_time = lap['LapTime'].total_seconds()
                    else:
                        lap_time = float(lap['LapTime'])
                    # 排除進站圈和異常圈
                    if 80 < lap_time < 150:
                        lap_dict[lap_num] = lap_time
            
            return lap_dict
        else:
            print(f"  [!] laps 不是 DataFrame: {type(laps_data)}")
            return {}
            
    except Exception as e:
        print(f"  [!] 提取 {driver_code} 圈速失敗: {e}")
        return {}

def extract_f91_driver_laps(f91_data, driver_code: str):
    """從 F91 預測提取車手圈速"""
    predictions = f91_data.get("predictions", {})
    
    # F91 使用車號作為 key
    driver_number_map = {
        "VER": "1", "PER": "11", "HAM": "44", "RUS": "63",
        "LEC": "16", "SAI": "55", "NOR": "4", "PIA": "81",
        "ALO": "14", "STR": "18", "GAS": "10", "OCO": "31",
        "TSU": "22", "RIC": "3", "BOT": "77", "ZHO": "24",
        "MAG": "20", "HUL": "27", "ALB": "23", "SAR": "2",
        "ANT": "87", "BEA": "50", "COL": "43", "LAW": "30",
        "HAD": "6", "BOR": "38", "DOO": "61"
    }
    
    driver_num = driver_number_map.get(driver_code, driver_code)
    
    if driver_num in predictions:
        driver_pred = predictions[driver_num]
        predicted_laps = driver_pred.get("predicted_laps", {})
        return {int(k): v for k, v in predicted_laps.items()}
    
    return {}

def calculate_mae(real_laps, pred_laps):
    """計算 MAE"""
    errors = []
    for lap_num, real_time in real_laps.items():
        if lap_num in pred_laps:
            errors.append(abs(real_time - pred_laps[lap_num]))
    
    if errors:
        return np.mean(errors), len(errors)
    return None, 0

def plot_comparison():
    """繪製 3 場比賽對比圖表"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('F91 預測 vs 真實圈速對比 (2025 賽季 - VER)', fontsize=16, fontweight='bold')
    
    summary_data = []
    
    for idx, race_config in enumerate(races):
        ax = axes[idx]
        race_name = race_config["name"]
        display_name = race_config["display"]
        
        print(f"\n處理 {display_name}...")
        
        # 載入數據
        session = load_real_laptimes(race_name)
        f91_data = load_f91_prediction(race_name)
        
        if not session or not f91_data:
            ax.text(0.5, 0.5, f"數據不完整\n{race_name}", 
                   ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.set_title(display_name)
            continue
        
        # 提取 VER 圈速
        real_laps = extract_driver_laps(session, "VER")
        pred_laps = extract_f91_driver_laps(f91_data, "VER")
        
        if not real_laps:
            ax.text(0.5, 0.5, "找不到 VER 真實數據", 
                   ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.set_title(display_name)
            continue
            
        if not pred_laps:
            ax.text(0.5, 0.5, "找不到 VER 預測數據", 
                   ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.set_title(display_name)
            continue
        
        # 計算 MAE
        mae, count = calculate_mae(real_laps, pred_laps)
        
        # 找出共同圈數
        common_laps = sorted(set(real_laps.keys()) & set(pred_laps.keys()))
        
        if not common_laps:
            ax.text(0.5, 0.5, "無共同圈數", 
                   ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.set_title(display_name)
            continue
        
        real_plot = [real_laps[lap] for lap in common_laps]
        pred_plot = [pred_laps[lap] for lap in common_laps]
        
        # 繪製圖表
        ax.plot(common_laps, real_plot, 'b-o', label='真實圈速', linewidth=2, markersize=4)
        ax.plot(common_laps, pred_plot, 'r--s', label=f'F91 預測 (MAE={mae:.3f}s)', 
               linewidth=1.5, markersize=3, alpha=0.8)
        
        # 計算平均圈速
        avg_real = np.mean(real_plot)
        avg_pred = np.mean(pred_plot)
        
        ax.axhline(y=avg_real, color='blue', linestyle=':', alpha=0.5, label=f'真實平均: {avg_real:.3f}s')
        ax.axhline(y=avg_pred, color='red', linestyle=':', alpha=0.5, label=f'預測平均: {avg_pred:.3f}s')
        
        ax.set_title(f"{display_name}\nVER 圈速對比 ({count} 圈)", fontsize=12, fontweight='bold')
        ax.set_xlabel('圈數', fontsize=10)
        ax.set_ylabel('圈速 (秒)', fontsize=10)
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.3)
        
        # 儲存摘要
        if mae:
            summary_data.append({
                "race": display_name,
                "mae": mae,
                "count": count,
                "avg_real": avg_real,
                "avg_pred": avg_pred,
                "diff": avg_pred - avg_real
            })
            print(f"  ✓ MAE: {mae:.4f}s ({count} 圈)")
    
    plt.tight_layout()
    
    # 儲存圖表
    output_file = "reports/f91_vs_real_3_races_comparison.png"
    Path("reports").mkdir(exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n✅ 圖表已儲存: {output_file}")
    
    # 顯示摘要
    print("\n" + "="*60)
    print("F91 預測準確度摘要 (3 場比賽)")
    print("="*60)
    
    for data in summary_data:
        print(f"\n{data['race']}:")
        print(f"  MAE: {data['mae']:.4f}s ({data['count']} 圈)")
        print(f"  真實平均: {data['avg_real']:.3f}s")
        print(f"  預測平均: {data['avg_pred']:.3f}s")
        print(f"  偏差: {data['diff']:+.3f}s")
    
    if summary_data:
        avg_mae = np.mean([d["mae"] for d in summary_data])
        print(f"\n{'='*60}")
        print(f"整體平均 MAE: {avg_mae:.4f}s")
        print("="*60)
    
    return summary_data

if __name__ == "__main__":
    print("\n開始生成 F91 vs 真實圈速對比圖表...")
    plot_comparison()
