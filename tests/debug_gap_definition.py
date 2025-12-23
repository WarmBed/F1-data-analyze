"""
驗證 Gap 定義的正確性

檢查 Lap 15-20 的實際數據來理解 gap_to_leader 的含義
"""
import pickle
from pathlib import Path

pkl_path = Path("data/live_timing_cache/2025/Abu_Dhabi_Race.pkl")
with open(pkl_path, 'rb') as f:
    data = pickle.load(f)

snapshots = data.get('snapshots', [])

print("=" * 80)
print("🔍 Gap 定義驗證 - TSU vs NOR (Lap 15-20)")
print("=" * 80)

for target_lap in range(15, 21):
    for snapshot in snapshots:
        if snapshot.get('current_lap') == target_lap:
            drivers = snapshot.get('drivers', {})
            
            tsu_data = None
            nor_data = None
            leader_data = None
            
            # 找到 TSU, NOR 和領先者（P1）
            for driver in drivers.values():
                tla = driver.get('driver_tla')
                pos = driver.get('position')
                if tla == 'TSU':
                    tsu_data = driver
                elif tla == 'NOR':
                    nor_data = driver
                if pos == 1:
                    leader_data = driver
            
            if tsu_data and nor_data and leader_data:
                # 提取數據
                tsu_pos = tsu_data.get('position')
                nor_pos = nor_data.get('position')
                tsu_gap = float(tsu_data.get('gap_to_leader', 0))
                nor_gap = float(nor_data.get('gap_to_leader', 0))
                leader_tla = leader_data.get('driver_tla')
                
                # 計算相對 Gap（TSU 相對於 NOR）
                # 方法 1: gap_to_leader 差值
                gap_method1 = tsu_gap - nor_gap
                
                # 方法 2: 根據位置判斷
                if tsu_pos < nor_pos:
                    # TSU 在前
                    gap_method2 = -(tsu_gap - nor_gap)  # 負值表示 TSU 領先
                else:
                    # NOR 在前
                    gap_method2 = tsu_gap - nor_gap  # 正值表示 TSU 落後
                
                print(f"\nLap {target_lap}:")
                print(f"  領先者: {leader_tla} (P1)")
                print(f"  TSU: P{tsu_pos}, gap_to_leader = {tsu_gap:.3f}s")
                print(f"  NOR: P{nor_pos}, gap_to_leader = {nor_gap:.3f}s")
                print(f"  Gap (方法1: TSU_gap - NOR_gap) = {gap_method1:.3f}s")
                print(f"  Gap (方法2: 位置判斷) = {gap_method2:.3f}s")
                print(f"  實際情況: {'TSU 領先' if tsu_pos < nor_pos else 'NOR 領先'}")
            
            break

print("\n" + "=" * 80)
print("💡 Gap 定義分析")
print("=" * 80)
print("gap_to_leader 含義：")
print("  - 該車手落後領先者（P1）的秒數")
print("  - 領先者的 gap_to_leader = 0")
print("  - 數值越大 = 落後越多")
print("\n相對 Gap 計算（TSU vs NOR）：")
print("  - Gap = TSU_gap_to_leader - NOR_gap_to_leader")
print("  - 正值: TSU 落後 NOR")
print("  - 負值: TSU 領先 NOR")
