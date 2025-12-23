"""
測試 F120 FP2 彎道分析 - 驗證 _get_speed_at_distance_v2 修復

目標：驗證 ANT T6 速度是否從 282 km/h 降到 ~65 km/h
"""
import fastf1
import pandas as pd
import sys
sys.path.insert(0, '.')

from CLI_modules.cli.analyzer.fp2_corner_all_laps_analysis import FP2CornerAllLapsAnalysis

# 載入數據
print("[1/4] 載入 Abu Dhabi 2025 FP2 數據...")
fastf1.Cache.enable_cache('cache')
session = fastf1.get_session(2025, 'Abu Dhabi', 'FP2')
session.load()

# 創建簡單的 data_loader 物件
class SimpleDataLoader:
    def __init__(self, session):
        self.session = session
        self.laps = session.laps
        self.session_type = 'FP2'
        self.year = 2025
        self.race_name = 'Abu Dhabi'

data_loader = SimpleDataLoader(session)

# 初始化分析器
print("[2/4] 初始化分析器...")
analyzer = FP2CornerAllLapsAnalysis(data_loader)

# 獲取 T6 位置
circuit_info = session.get_circuit_info()
corners = circuit_info.corners
t6 = corners[corners['Number'] == 6].iloc[0]
t6_distance = t6['Distance']
print(f"[INFO] T6 距離: {t6_distance:.1f} m")

# 測試 ANT 的所有圈數
print("[3/4] 測試 ANT (Antonelli) 的 T6 速度...")
ant_laps = session.laps.pick_drivers('ANT')
print(f"[INFO] ANT 總圈數: {len(ant_laps)}")

results_v2 = []
results_old = []

for idx, lap in ant_laps.iterrows():
    lap_num = lap['LapNumber']
    
    # 新方法 v2
    speed_v2 = analyzer._get_speed_at_distance_v2(lap, t6_distance, tolerance=20)
    
    # 舊方法（對比用）
    try:
        tel = lap.get_telemetry()
        if tel is not None and not tel.empty:
            speed_old = analyzer._get_speed_at_distance_fallback(tel, t6_distance, tolerance=20)
        else:
            speed_old = None
    except:
        speed_old = None
    
    results_v2.append({'Lap': lap_num, 'Speed_v2': speed_v2})
    results_old.append({'Lap': lap_num, 'Speed_old': speed_old})

# 合併結果
df_v2 = pd.DataFrame(results_v2)
df_old = pd.DataFrame(results_old)
df = pd.merge(df_v2, df_old, on='Lap')

print()
print("=" * 70)
print("ANT T6 速度比較（新 v2 方法 vs 舊方法）")
print("=" * 70)
print(f"{'Lap':>4} | {'v2 (原始 car_data)':>20} | {'舊方法 (get_telemetry)':>22} | {'差異':>8}")
print("-" * 70)

anomaly_count_v2 = 0
anomaly_count_old = 0

for _, row in df.iterrows():
    lap = int(row['Lap'])
    v2 = row['Speed_v2']
    old = row['Speed_old']
    
    v2_str = f"{v2:.1f} km/h" if v2 is not None else "N/A"
    old_str = f"{old:.1f} km/h" if old is not None else "N/A"
    
    if v2 is not None and old is not None:
        diff = old - v2
        diff_str = f"{diff:+.1f}"
        
        # 標記異常值
        flag_v2 = "!" if v2 > 100 else ""
        flag_old = "!" if old > 100 else ""
        
        if v2 > 100:
            anomaly_count_v2 += 1
        if old > 100:
            anomaly_count_old += 1
    else:
        diff_str = "-"
        flag_v2 = ""
        flag_old = ""
    
    print(f"{lap:4d} | {v2_str:>18}{flag_v2:>2} | {old_str:>20}{flag_old:>2} | {diff_str:>8}")

print("-" * 70)
print()
print("[4/4] 統計結果:")
print(f"  舊方法異常圈數（>100 km/h）: {anomaly_count_old}")
print(f"  新方法異常圈數（>100 km/h）: {anomaly_count_v2}")

if anomaly_count_v2 < anomaly_count_old:
    print()
    print("  [SUCCESS] 新方法有效減少了異常值！")
else:
    print()
    print("  [WARNING] 新方法未能減少異常值，需要進一步調查")

# 計算統計
valid_v2 = df['Speed_v2'].dropna()
valid_old = df['Speed_old'].dropna()

print()
print("[統計摘要]")
print(f"  v2 方法: 中位數={valid_v2.median():.1f}, 平均={valid_v2.mean():.1f}, 最小={valid_v2.min():.1f}, 最大={valid_v2.max():.1f}")
print(f"  舊方法:  中位數={valid_old.median():.1f}, 平均={valid_old.mean():.1f}, 最小={valid_old.min():.1f}, 最大={valid_old.max():.1f}")
