"""
P2 追 P1 策略建議 Demo - 使用 Live Timing PKL 數據
=================================================

這個 Demo 展示如何從 Live Timing PKL 快取中提取位置數據，
分析 P2 是否能追上 P1，並推薦可行的策略。

數據來源：Abu Dhabi 的 Live Timing PKL
路徑：data/live_timing_cache/2025/Abu_Dhabi_Race.pkl

Author: F1T Team
Date: 2025-12-08
"""

import pickle
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ===== 策略計算函數（從前一版 Demo 複製） =====

def classify_gap(gap: float) -> str:
    """
    根據差距分類策略可行性
    
    Args:
        gap: P1 與 P2 的時間差距（秒）
    
    Returns:
        差距類別：極小 | 中等 | 大 | 極大
    """
    if gap < 3.0:
        return "極小差距"
    elif gap < 8.0:
        return "中等差距"
    elif gap < 15.0:
        return "大差距"
    else:
        return "極大差距"


def calculate_tire_age_advantage(
    tire_age_diff: int,
    remaining_laps: int,
    degradation_per_lap: float = 0.08
) -> Tuple[float, int]:
    """
    計算輪胎年齡優勢策略
    
    Args:
        tire_age_diff: 輪胎年齡差（P1 - P2，正值表示 P2 輪胎更新）
        remaining_laps: 剩餘圈數
        degradation_per_lap: 每圈退化時間（秒）
    
    Returns:
        (總可追回時間, 預計追上圈數)
    """
    advantage_per_lap = tire_age_diff * degradation_per_lap
    total_advantage = advantage_per_lap * remaining_laps
    
    return total_advantage, advantage_per_lap


def calculate_undercut_advantage(
    gap: float,
    pit_loss: float = 22.0,
    new_tire_advantage: float = 1.2,
    chase_laps: int = 10
) -> Tuple[bool, float, int]:
    """
    計算 Undercut 策略可行性
    
    Args:
        gap: 當前差距（秒）
        pit_loss: 進站損失時間（秒）
        new_tire_advantage: 新胎優勢（秒/圈）
        chase_laps: 追趕圈數
    
    Returns:
        (是否可行, 總優勢, 預計追上圈數)
    """
    total_advantage = new_tire_advantage * chase_laps
    net_advantage = total_advantage - pit_loss
    
    is_feasible = net_advantage > gap
    catchup_laps = int((gap + pit_loss) / new_tire_advantage) + 1 if new_tire_advantage > 0 else 999
    
    return is_feasible, net_advantage, catchup_laps


def calculate_sc_opportunity(
    gap: float,
    sc_pit_loss: float = 8.0,
    new_tire_advantage: float = 2.2,
    chase_laps: int = 15
) -> Tuple[bool, float, int]:
    """
    計算安全車機會策略
    
    Args:
        gap: 當前差距（秒）
        sc_pit_loss: SC 期間進站損失（秒）
        new_tire_advantage: SC 後新胎優勢（秒/圈）
        chase_laps: 追趕圈數
    
    Returns:
        (是否可行, 總優勢, 預計追上圈數)
    """
    pit_save = 22.0 - sc_pit_loss  # 節省 14 秒
    total_advantage = pit_save + (new_tire_advantage * chase_laps)
    
    is_feasible = total_advantage > gap
    catchup_laps = int((gap - pit_save) / new_tire_advantage) + 1 if new_tire_advantage > 0 else 999
    
    return is_feasible, total_advantage, catchup_laps


def recommend_strategy(gap: float, tire_age_diff: int, remaining_laps: int) -> Dict:
    """
    智能推薦策略（根據差距過濾）
    
    Args:
        gap: 當前差距（秒）
        tire_age_diff: 輪胎年齡差
        remaining_laps: 剩餘圈數
    
    Returns:
        推薦結果字典
    """
    gap_category = classify_gap(gap)
    
    # 計算所有策略
    tire_adv, tire_per_lap = calculate_tire_age_advantage(tire_age_diff, remaining_laps)
    undercut_feasible, undercut_adv, undercut_laps = calculate_undercut_advantage(gap)
    sc_feasible, sc_adv, sc_laps = calculate_sc_opportunity(gap)
    
    # 根據差距類別過濾推薦
    recommendations = []
    
    if gap_category == "極小差距":  # 0-3s：只推薦線性策略
        if tire_age_diff > 0:
            recommendations.append({
                "strategy": "輪胎年齡優勢策略",
                "feasible": tire_adv > gap,
                "advantage": tire_adv,
                "per_lap": tire_per_lap,
                "catchup_lap": int(gap / tire_per_lap) + 1 if tire_per_lap > 0 else 999,
                "priority": 1
            })
    
    elif gap_category == "中等差距":  # 3-8s：輪胎 + Undercut
        if tire_age_diff > 0:
            recommendations.append({
                "strategy": "輪胎年齡優勢策略",
                "feasible": tire_adv > gap,
                "advantage": tire_adv,
                "per_lap": tire_per_lap,
                "catchup_lap": int(gap / tire_per_lap) + 1 if tire_per_lap > 0 else 999,
                "priority": 1
            })
        
        recommendations.append({
            "strategy": "Undercut 策略",
            "feasible": undercut_feasible,
            "advantage": undercut_adv,
            "catchup_lap": undercut_laps,
            "priority": 2
        })
    
    elif gap_category == "大差距":  # 8-15s：所有策略
        if tire_age_diff > 0:
            recommendations.append({
                "strategy": "輪胎年齡優勢策略",
                "feasible": tire_adv > gap,
                "advantage": tire_adv,
                "per_lap": tire_per_lap,
                "catchup_lap": int(gap / tire_per_lap) + 1 if tire_per_lap > 0 else 999,
                "priority": 3
            })
        
        recommendations.append({
            "strategy": "Undercut 策略",
            "feasible": undercut_feasible,
            "advantage": undercut_adv,
            "catchup_lap": undercut_laps,
            "priority": 3
        })
        
        recommendations.append({
            "strategy": "SC 機會策略",
            "feasible": sc_feasible,
            "advantage": sc_adv,
            "catchup_lap": sc_laps,
            "priority": 1  # 大差距唯一可行
        })
    
    else:  # 極大差距 >15s：只有 SC
        recommendations.append({
            "strategy": "SC 機會策略",
            "feasible": sc_feasible,
            "advantage": sc_adv,
            "catchup_lap": sc_laps,
            "priority": 1
        })
    
    # 排序：priority 低的在前，同 priority 按 feasible 排序
    recommendations.sort(key=lambda x: (x["priority"], not x["feasible"]))
    
    return {
        "gap_category": gap_category,
        "recommendations": recommendations
    }


# ===== Live Timing PKL 數據載入 =====

def load_livetiming_pkl(pkl_path: str) -> Optional[Dict]:
    """
    載入 Live Timing PKL 快取
    
    Args:
        pkl_path: PKL 檔案路徑
    
    Returns:
        快取數據字典，或 None
    """
    try:
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"[載入成功] PKL 版本: {data.get('version', 'unknown')}")
        print(f"[載入成功] 快照數量: {len(data.get('snapshots', []))}")
        print(f"[載入成功] 賽事資訊: {data.get('race_info', {})}")
        
        return data
    
    except FileNotFoundError:
        print(f"[錯誤] 找不到檔案: {pkl_path}")
        return None
    except Exception as e:
        print(f"[錯誤] 載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_position_data_at_lap(pkl_data: Dict, target_lap: int) -> Optional[Dict]:
    """
    從 PKL 數據中提取指定圈數的位置資料
    
    Args:
        pkl_data: PKL 快取數據
        target_lap: 目標圈數
    
    Returns:
        位置資料字典，包含 P1 和 P2 的資訊
    """
    snapshots = pkl_data.get('snapshots', [])
    
    if not snapshots:
        print("[錯誤] PKL 中無快照數據")
        return None
    
    # 尋找接近目標圈數的快照
    target_snapshot = None
    for snapshot in snapshots:
        current_lap = snapshot.get('current_lap', 0)
        if current_lap >= target_lap:
            target_snapshot = snapshot
            break
    
    if not target_snapshot:
        print(f"[錯誤] 找不到第 {target_lap} 圈的數據")
        return None
    
    drivers = target_snapshot.get('drivers', {})
    
    # 按位置排序找出 P1 和 P2
    sorted_drivers = sorted(
        [(num, data) for num, data in drivers.items()],
        key=lambda x: x[1].get('position', 99)
    )
    
    if len(sorted_drivers) < 2:
        print("[錯誤] 數據不足，無法分析")
        return None
    
    p1_num, p1_data = sorted_drivers[0]
    p2_num, p2_data = sorted_drivers[1]
    
    # 提取關鍵資訊
    race_time = target_snapshot.get('race_time_seconds', 0)
    if not race_time:
        race_time_str = target_snapshot.get('race_time', '00:00:00')
        try:
            parts = race_time_str.split(':')
            if len(parts) == 3:
                race_time = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except:
            race_time = 0.0
    
    # 獲取輪胎資訊（從 driver_stints）
    driver_stints = pkl_data.get('driver_stints', {})
    
    def get_tire_info(driver_num_str, current_lap):
        """從 driver_stints 獲取輪胎資訊"""
        stints = driver_stints.get(driver_num_str, [])
        for stint in stints:
            if stint.get('lap_start', 0) <= current_lap <= stint.get('lap_end', 999):
                return {
                    'compound': stint.get('compound', 'UNKNOWN'),
                    'age': current_lap - stint.get('lap_start', 0) + 1
                }
        return {'compound': 'UNKNOWN', 'age': 0}
    
    p1_tire = get_tire_info(str(p1_num), target_lap)
    p2_tire = get_tire_info(str(p2_num), target_lap)
    
    result = {
        "lap": target_snapshot.get('current_lap', 0),
        "race_time": race_time,
        "p1": {
            "number": p1_num,
            "abbr": p1_data.get('driver_tla', 'UNK'),
            "name": p1_data.get('driver_name', 'UNKNOWN'),
            "team": p1_data.get('team_name', 'Unknown Team'),
            "position": p1_data.get('position', 1),
            "lap": p1_data.get('lap', 0),
            "tire_compound": p1_tire['compound'],
            "tire_age": p1_tire['age'],
            "gap_to_leader": p1_data.get('gap_to_leader', 0.0),
            "last_lap_time": p1_data.get('last_lap_time', 'N/A'),
            "best_lap_time": p1_data.get('best_lap_time', 'N/A')
        },
        "p2": {
            "number": p2_num,
            "abbr": p2_data.get('driver_tla', 'UNK'),
            "name": p2_data.get('driver_name', 'UNKNOWN'),
            "team": p2_data.get('team_name', 'Unknown Team'),
            "position": p2_data.get('position', 2),
            "lap": p2_data.get('lap', 0),
            "tire_compound": p2_tire['compound'],
            "tire_age": p2_tire['age'],
            "gap_to_leader": p2_data.get('gap_to_leader', 0.0),
            "last_lap_time": p2_data.get('last_lap_time', 'N/A'),
            "best_lap_time": p2_data.get('best_lap_time', 'N/A')
        }
    }
    
    # 計算 P2 與 P1 的差距
    p1_gap = p1_data.get('gap_to_leader', 0.0)
    p2_gap = p2_data.get('gap_to_leader', 0.0)
    
    # 確保 gap 是數字
    if isinstance(p1_gap, str):
        try:
            p1_gap = float(p1_gap.replace('+', ''))
        except:
            p1_gap = 0.0
    if isinstance(p2_gap, str):
        try:
            p2_gap = float(p2_gap.replace('+', ''))
        except:
            p2_gap = 0.0
    
    result["gap"] = abs(p2_gap - p1_gap)
    result["tire_age_diff"] = result["p1"]["tire_age"] - result["p2"]["tire_age"]
    
    return result


def print_position_summary(position_data: Dict, race_info: Dict):
    """列印位置資料摘要"""
    print("\n" + "=" * 80)
    print("📊 Live Timing 位置資料")
    print("=" * 80)
    
    print(f"\n🏁 賽事資訊:")
    print(f"   年份: {race_info.get('year', 'N/A')}")
    print(f"   賽事: {race_info.get('race', 'N/A')}")
    print(f"   總圈數: {race_info.get('total_laps', 'N/A')}")
    
    print(f"\n⏱️  當前狀態:")
    print(f"   圈數: 第 {position_data['lap']} 圈")
    print(f"   比賽時間: {position_data['race_time']:.1f} 秒")
    
    print(f"\n🥇 P1 - {position_data['p1']['abbr']} (#{position_data['p1']['number']}) - {position_data['p1']['name']}")
    print(f"   車隊: {position_data['p1']['team']}")
    print(f"   輪胎: {position_data['p1']['tire_compound']} ({position_data['p1']['tire_age']} 圈)")
    print(f"   上圈圈速: {position_data['p1']['last_lap_time']}")
    print(f"   最快圈速: {position_data['p1']['best_lap_time']}")
    print(f"   與領先差距: {position_data['p1']['gap_to_leader']:.3f}s")
    
    print(f"\n🥈 P2 - {position_data['p2']['abbr']} (#{position_data['p2']['number']}) - {position_data['p2']['name']}")
    print(f"   車隊: {position_data['p2']['team']}")
    print(f"   輪胎: {position_data['p2']['tire_compound']} ({position_data['p2']['tire_age']} 圈)")
    print(f"   上圈圈速: {position_data['p2']['last_lap_time']}")
    print(f"   最快圈速: {position_data['p2']['best_lap_time']}")
    print(f"   與領先差距: {position_data['p2']['gap_to_leader']:.3f}s")
    
    print(f"\n📏 P2 與 P1 的差距: {position_data['gap']:.3f}s")
    print(f"🔧 輪胎年齡差: {position_data['tire_age_diff']} 圈 (正值 = P2 輪胎更新)")


def print_strategy_recommendations(position_data: Dict, race_info: Dict):
    """列印策略推薦"""
    gap = position_data['gap']
    tire_age_diff = position_data['tire_age_diff']
    current_lap = position_data['lap']
    total_laps = race_info.get('total_laps', 60)
    remaining_laps = total_laps - current_lap
    
    result = recommend_strategy(gap, tire_age_diff, remaining_laps)
    
    print("\n" + "=" * 80)
    print("🎯 智能策略推薦")
    print("=" * 80)
    
    print(f"\n差距類別: {result['gap_category']} ({gap:.2f}s)")
    print(f"剩餘圈數: {remaining_laps} 圈")
    
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"\n策略 {i}: {rec['strategy']}")
        print(f"  ├─ 可行性: {'✅ 可行' if rec['feasible'] else '❌ 不可行'}")
        print(f"  ├─ 總優勢: {rec['advantage']:.2f}s")
        if 'per_lap' in rec:
            print(f"  ├─ 每圈優勢: {rec['per_lap']:.3f}s")
        print(f"  └─ 預計追上: 第 {rec['catchup_lap']} 圈")


# ===== 主程式 =====

def main():
    """主程式流程"""
    print("=" * 80)
    print("P2 追 P1 策略建議 Demo - Live Timing PKL 版本")
    print("=" * 80)
    
    # 1. 載入 Abu Dhabi PKL
    pkl_path = "data/live_timing_cache/2025/Abu_Dhabi_Race.pkl"
    
    if not Path(pkl_path).exists():
        print(f"\n[錯誤] 找不到 PKL 檔案: {pkl_path}")
        print("\n可用的 PKL 檔案:")
        cache_dir = Path("data/live_timing_cache")
        if cache_dir.exists():
            for pkl in cache_dir.rglob("*.pkl"):
                print(f"  - {pkl}")
        return
    
    pkl_data = load_livetiming_pkl(pkl_path)
    if not pkl_data:
        return
    
    race_info = pkl_data.get('race_info', {})
    
    # 2. 提取第 30 圈的位置資料
    print("\n[分析] 提取第 30 圈的位置資料...")
    position_data = extract_position_data_at_lap(pkl_data, target_lap=30)
    
    if not position_data:
        return
    
    # 3. 列印位置摘要
    print_position_summary(position_data, race_info)
    
    # 4. 列印策略推薦
    print_strategy_recommendations(position_data, race_info)
    
    print("\n" + "=" * 80)
    print("✅ Demo 完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
