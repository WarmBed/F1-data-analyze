"""
完整策略比較 - 使用 Abu Dhabi PKL 真實數據
===============================================

從 Live Timing PKL 提取真實賽事數據，
展示所有 4 種策略的完整比較結果。

數據源: data/live_timing_cache/2025/Abu_Dhabi_Race.pkl

Author: F1T Team
Date: 2025-12-08
"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class StrategyResult:
    """策略結果"""
    strategy_name: str
    feasible: bool
    catchup_lap: Optional[int]  # None = 追不上
    total_advantage: float
    details: str


def classify_gap(gap: float) -> str:
    """差距分類"""
    if gap < 3.0:
        return "極小差距"
    elif gap < 8.0:
        return "中等差距"
    elif gap < 15.0:
        return "大差距"
    else:
        return "極大差距"


# ============================================
# 載入 PKL 數據
# ============================================

def load_livetiming_pkl(pkl_path: str) -> Optional[Dict]:
    """載入 Live Timing PKL"""
    try:
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
        print(f"[載入] PKL 版本: {data.get('version', 'unknown')}")
        print(f"[載入] 快照數量: {len(data.get('snapshots', []))}")
        return data
    except Exception as e:
        print(f"[錯誤] 載入失敗: {e}")
        return None


def extract_position_data_at_lap(pkl_data: Dict, target_lap: int) -> Optional[Dict]:
    """提取指定圈數的位置資料"""
    snapshots = pkl_data.get('snapshots', [])
    
    # 找到目標圈數的快照
    target_snapshot = None
    for snapshot in snapshots:
        if snapshot.get('current_lap', 0) >= target_lap:
            target_snapshot = snapshot
            break
    
    if not target_snapshot:
        return None
    
    drivers = target_snapshot.get('drivers', {})
    sorted_drivers = sorted(
        [(num, data) for num, data in drivers.items()],
        key=lambda x: x[1].get('position', 99)
    )
    
    if len(sorted_drivers) < 2:
        return None
    
    p1_num, p1_data = sorted_drivers[0]
    p2_num, p2_data = sorted_drivers[1]
    
    # 獲取輪胎資訊
    driver_stints = pkl_data.get('driver_stints', {})
    
    def get_tire_info(driver_num_str, current_lap):
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
    
    race_time_seconds = target_snapshot.get('race_time_seconds', 0)
    
    result = {
        "lap": target_snapshot.get('current_lap', 0),
        "race_time": race_time_seconds,
        "p1": {
            "number": p1_num,
            "abbr": p1_data.get('driver_tla', 'UNK'),
            "name": p1_data.get('driver_name', 'UNKNOWN'),
            "team": p1_data.get('team_name', 'Unknown'),
            "position": p1_data.get('position', 1),
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
            "team": p2_data.get('team_name', 'Unknown'),
            "position": p2_data.get('position', 2),
            "tire_compound": p2_tire['compound'],
            "tire_age": p2_tire['age'],
            "gap_to_leader": p2_data.get('gap_to_leader', 0.0),
            "last_lap_time": p2_data.get('last_lap_time', 'N/A'),
            "best_lap_time": p2_data.get('best_lap_time', 'N/A')
        }
    }
    
    # 計算差距
    p1_gap = p1_data.get('gap_to_leader', 0.0)
    p2_gap = p2_data.get('gap_to_leader', 0.0)
    
    if isinstance(p2_gap, str):
        p2_gap = float(p2_gap.replace('+', ''))
    if isinstance(p1_gap, str):
        p1_gap = float(p1_gap.replace('+', ''))
    
    result["gap"] = abs(p2_gap - p1_gap)
    result["tire_age_diff"] = result["p1"]["tire_age"] - result["p2"]["tire_age"]
    
    return result


# ============================================
# 策略計算
# ============================================

def calculate_tire_age_strategy(
    gap: float,
    tire_age_diff: int,
    remaining_laps: int,
    current_lap: int,
    degradation_per_lap: float = 0.08
) -> StrategyResult:
    """策略 1: 輪胎年齡優勢"""
    if tire_age_diff <= 0:
        return StrategyResult(
            strategy_name="輪胎年齡優勢",
            feasible=False,
            catchup_lap=None,
            total_advantage=0.0,
            details="P2 輪胎不比 P1 新，無優勢"
        )
    
    advantage_per_lap = tire_age_diff * degradation_per_lap
    total_advantage = advantage_per_lap * remaining_laps
    
    if total_advantage <= gap:
        return StrategyResult(
            strategy_name="輪胎年齡優勢",
            feasible=False,
            catchup_lap=None,
            total_advantage=total_advantage,
            details=f"總優勢 {total_advantage:.2f}s < 差距 {gap:.2f}s"
        )
    
    catchup_laps = int(gap / advantage_per_lap) + 1
    
    return StrategyResult(
        strategy_name="輪胎年齡優勢",
        feasible=True,
        catchup_lap=current_lap + catchup_laps,
        total_advantage=total_advantage,
        details=f"每圈追回 {advantage_per_lap:.3f}s，輪胎年齡差 {tire_age_diff} 圈"
    )


def calculate_undercut_strategy(
    gap: float,
    current_lap: int,
    remaining_laps: int,
    pit_loss: float = 22.0,
    new_tire_advantage: float = 1.2
) -> StrategyResult:
    """策略 2: Undercut (立即進站)"""
    gap_after_pit = gap + pit_loss
    total_advantage = new_tire_advantage * remaining_laps
    
    if total_advantage <= gap_after_pit:
        return StrategyResult(
            strategy_name="Undercut (立即進站)",
            feasible=False,
            catchup_lap=None,
            total_advantage=total_advantage - pit_loss,
            details=f"進站後差距 {gap_after_pit:.1f}s，新胎優勢 {total_advantage:.1f}s 不足"
        )
    
    catchup_laps = int(gap_after_pit / new_tire_advantage) + 1
    
    return StrategyResult(
        strategy_name="Undercut (立即進站)",
        feasible=True,
        catchup_lap=current_lap + catchup_laps,
        total_advantage=total_advantage - pit_loss,
        details=f"進站損失 {pit_loss}s，新胎每圈快 {new_tire_advantage}s"
    )


def calculate_sc_opportunity_strategy(
    gap: float,
    current_lap: int,
    remaining_laps: int,
    sc_probability: float = 0.3,
    sc_pit_loss: float = 8.0,
    new_tire_advantage: float = 2.2
) -> StrategyResult:
    """策略 3: SC 機會 (等待安全車)"""
    pit_save = 22.0 - sc_pit_loss  # 節省 14 秒
    
    sc_assumed_lap = current_lap + (remaining_laps // 3)
    laps_after_sc = remaining_laps - (remaining_laps // 3)
    
    total_advantage = pit_save + (new_tire_advantage * laps_after_sc)
    
    if total_advantage <= gap:
        return StrategyResult(
            strategy_name="SC 機會 (等待安全車)",
            feasible=False,
            catchup_lap=None,
            total_advantage=total_advantage,
            details=f"即使有 SC，總優勢 {total_advantage:.1f}s < 差距 {gap:.1f}s"
        )
    
    gap_after_sc_pit = gap - pit_save
    if gap_after_sc_pit <= 0:
        catchup_lap = sc_assumed_lap + 1
    else:
        catchup_laps = int(gap_after_sc_pit / new_tire_advantage) + 1
        catchup_lap = sc_assumed_lap + catchup_laps
    
    return StrategyResult(
        strategy_name="SC 機會 (等待安全車)",
        feasible=True,
        catchup_lap=catchup_lap,
        total_advantage=total_advantage,
        details=f"假設第 {sc_assumed_lap} 圈出現 SC，節省 {pit_save:.0f}s 進站時間"
    )


def calculate_active_pit_simulation(
    gap: float,
    current_lap: int,
    remaining_laps: int,
    tire_compound: str = "SOFT",
    pit_loss: float = 22.0
) -> StrategyResult:
    """策略 4: 主動進站模擬 (用戶自定義)"""
    tire_performance = {
        "SOFT": {"advantage": 1.5, "optimal_stint": 15},
        "MEDIUM": {"advantage": 1.0, "optimal_stint": 25},
        "HARD": {"advantage": 0.6, "optimal_stint": 35}
    }
    
    tire_data = tire_performance.get(tire_compound, tire_performance["MEDIUM"])
    
    gap_after_pit = gap + pit_loss
    total_advantage = tire_data["advantage"] * remaining_laps
    
    if total_advantage <= gap_after_pit:
        return StrategyResult(
            strategy_name=f"主動進站 ({tire_compound})",
            feasible=False,
            catchup_lap=None,
            total_advantage=total_advantage - pit_loss,
            details=f"{tire_compound} 輪胎優勢 {total_advantage:.1f}s 不足"
        )
    
    catchup_laps = int(gap_after_pit / tire_data["advantage"]) + 1
    
    return StrategyResult(
        strategy_name=f"主動進站 ({tire_compound})",
        feasible=True,
        catchup_lap=current_lap + catchup_laps,
        total_advantage=total_advantage - pit_loss,
        details=f"{tire_compound}: 每圈快 {tire_data['advantage']}s"
    )


def calculate_both_pit_scenario(
    gap: float,
    current_lap: int,
    p1_tire_age: int,
    p2_tire_age: int,
    pit_loss: float = 22.0,
    new_tire_advantage: float = 1.2
) -> StrategyResult:
    """
    策略 5: P1 和 P2 都進站的情境分析
    
    分析三種情境：
    1. P2 先進站 (Undercut)
    2. P1 先進站 (Cover)
    3. 同圈進站
    """
    
    # 情境 1: P2 先進站 (Undercut 嘗試)
    # P2 進站後，P1 多跑一圈再進站
    p2_pit_first_gap = gap + pit_loss  # P2 進站後差距
    p1_runs_one_more = p2_pit_first_gap - new_tire_advantage  # P1 多跑一圈的優勢
    p1_then_pits = p1_runs_one_more + pit_loss  # P1 進站後
    
    # 進站後誰在前面？
    if p1_then_pits > 0:
        result_p2_first = f"P1 領先 {p1_then_pits:.1f}s"
    else:
        result_p2_first = f"P2 領先 {abs(p1_then_pits):.1f}s (Undercut 成功!)"
    
    # 情境 2: P1 先進站 (防守性進站 Cover)
    # P1 進站，P2 多跑一圈
    p1_pit_first_gap = gap - pit_loss  # P1 進站損失
    p2_runs_one_more = p1_pit_first_gap + new_tire_advantage  # P2 多跑一圈
    
    if p2_runs_one_more > 0:
        result_p1_first = f"P1 領先 {p2_runs_one_more:.1f}s (Cover 成功)"
    else:
        result_p1_first = f"P2 反超 {abs(p2_runs_one_more):.1f}s"
    
    # 情境 3: 同圈進站
    # 差距不變（除非進站速度不同）
    result_same_lap = f"維持差距 {gap:.1f}s"
    
    # 判斷最佳策略
    undercut_success = p1_then_pits < 0
    
    details = (
        f"情境 1: P2 先進站 → {result_p2_first}\n"
        f"     情境 2: P1 先進站 → {result_p1_first}\n"
        f"     情境 3: 同圈進站 → {result_same_lap}"
    )
    
    return StrategyResult(
        strategy_name="雙重進站分析",
        feasible=undercut_success,
        catchup_lap=current_lap + 1 if undercut_success else None,
        total_advantage=abs(p1_then_pits) if undercut_success else p1_then_pits,
        details=details
    )


# ============================================
# 結果展示
# ============================================

def print_race_situation(position_data: Dict, race_info: Dict):
    """列印賽事狀態"""
    print("\n" + "=" * 90)
    print("賽事狀態 (Current Situation)")
    print("=" * 90)
    
    print(f"\n賽事: {race_info.get('race', 'N/A')} {race_info.get('year', 'N/A')}")
    print(f"圈數: 第 {position_data['lap']} 圈 / {race_info.get('total_laps', 'N/A')} 圈")
    print(f"比賽時間: {position_data['race_time']:.1f} 秒\n")
    
    print(f"P1: {position_data['p1']['abbr']} (#{position_data['p1']['number']}) - {position_data['p1']['name']}")
    print(f"    車隊: {position_data['p1']['team']}")
    print(f"    輪胎: {position_data['p1']['tire_compound']} ({position_data['p1']['tire_age']} 圈)")
    print(f"    上圈: {position_data['p1']['last_lap_time']} | 最快: {position_data['p1']['best_lap_time']}")
    
    print(f"\nP2: {position_data['p2']['abbr']} (#{position_data['p2']['number']}) - {position_data['p2']['name']}")
    print(f"    車隊: {position_data['p2']['team']}")
    print(f"    輪胎: {position_data['p2']['tire_compound']} ({position_data['p2']['tire_age']} 圈)")
    print(f"    上圈: {position_data['p2']['last_lap_time']} | 最快: {position_data['p2']['best_lap_time']}")
    
    print(f"\n差距: {position_data['gap']:.3f}s ({classify_gap(position_data['gap'])})")
    print(f"輪胎年齡差: {position_data['tire_age_diff']} 圈")


def print_strategy_comparison(results: List[StrategyResult]):
    """列印策略比較表"""
    print("\n" + "=" * 100)
    print("策略比較表 (Strategy Comparison)")
    print("=" * 100)
    
    print(f"\n{'#':<4} {'策略':<28} {'可行性':<12} {'追上圈數':<14} {'總優勢':<10}")
    print("-" * 100)
    
    for i, result in enumerate(results, 1):
        feasibility = "✅ 可行" if result.feasible else "❌ 不可行"
        catchup = f"第 {result.catchup_lap} 圈" if result.catchup_lap else "追不上" if not result.feasible else "-"
        advantage = f"+{result.total_advantage:.1f}s" if result.total_advantage > 0 else f"{result.total_advantage:.1f}s"
        
        print(f"{i:<4} {result.strategy_name:<28} {feasibility:<12} {catchup:<14} {advantage:<10}")
        
        # 多行詳情處理（針對雙重進站分析）
        if '\n' in result.details:
            for line in result.details.split('\n'):
                print(f"     {line}")
        else:
            print(f"     {result.details}")
        print()
    
    # 推薦
    feasible_results = [r for r in results if r.feasible and r.catchup_lap]
    if feasible_results:
        best = min(feasible_results, key=lambda r: r.catchup_lap)
        print(f"💡 推薦: {best.strategy_name} - 最快可在第 {best.catchup_lap} 圈追上")
    else:
        print("⚠️  所有策略均無法保證追上 P1")
    
    print("=" * 100)


# ============================================
# 主程式
# ============================================

def main():
    """主程式"""
    print("=" * 90)
    print("完整策略比較 - Abu Dhabi 2025 真實數據")
    print("=" * 90)
    
    # 載入 PKL
    pkl_path = "data/live_timing_cache/2025/Abu_Dhabi_Race.pkl"
    
    if not Path(pkl_path).exists():
        print(f"\n[錯誤] 找不到 PKL: {pkl_path}")
        return
    
    pkl_data = load_livetiming_pkl(pkl_path)
    if not pkl_data:
        return
    
    race_info = pkl_data.get('race_info', {})
    
    # 測試三個不同的圈數
    test_laps = [15, 30, 45]
    
    for lap in test_laps:
        print(f"\n\n{'🏁' * 45}")
        print(f"分析第 {lap} 圈")
        print(f"{'🏁' * 45}")
        
        position_data = extract_position_data_at_lap(pkl_data, lap)
        
        if not position_data:
            print(f"[跳過] 第 {lap} 圈無數據")
            continue
        
        # 顯示賽事狀態
        print_race_situation(position_data, race_info)
        
        # 計算所有策略
        current_lap = position_data['lap']
        total_laps = race_info.get('total_laps', 58)
        remaining_laps = total_laps - current_lap
        gap = position_data['gap']
        tire_age_diff = position_data['tire_age_diff']
        
        results = [
            calculate_tire_age_strategy(gap, tire_age_diff, remaining_laps, current_lap),
            calculate_undercut_strategy(gap, current_lap, remaining_laps),
            calculate_sc_opportunity_strategy(gap, current_lap, remaining_laps),
            calculate_active_pit_simulation(gap, current_lap, remaining_laps, "SOFT"),
            calculate_both_pit_scenario(
                gap, 
                current_lap, 
                position_data['p1']['tire_age'],
                position_data['p2']['tire_age']
            )
        ]
        
        # 顯示策略比較
        print_strategy_comparison(results)
    
    print("\n" + "=" * 90)
    print("✅ 分析完成")
    print("=" * 90)


if __name__ == "__main__":
    main()
