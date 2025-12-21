"""
完整策略比較 Demo - 展示所有策略結果
===========================================

展示所有 4 種策略的追趕結果：
1. 輪胎年齡優勢（繼續使用當前輪胎）
2. Undercut（立即進站換新胎）
3. SC 機會（等待安全車出現）
4. 主動進站模擬（用戶自定義配方）

每個策略都顯示：第幾圈追上 或 追不上

Author: F1T Team
Date: 2025-12-08
"""

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
# 策略 1: 輪胎年齡優勢
# ============================================

def calculate_tire_age_strategy(
    gap: float,
    tire_age_diff: int,
    remaining_laps: int,
    degradation_per_lap: float = 0.08
) -> StrategyResult:
    """
    策略 1: 輪胎年齡優勢
    
    P2 繼續使用當前輪胎，利用輪胎較新的優勢追趕
    """
    if tire_age_diff <= 0:
        return StrategyResult(
            strategy_name="輪胎年齡優勢 (繼續使用)",
            feasible=False,
            catchup_lap=None,
            total_advantage=0.0,
            details="P2 輪胎不比 P1 新，無優勢"
        )
    
    advantage_per_lap = tire_age_diff * degradation_per_lap
    total_advantage = advantage_per_lap * remaining_laps
    
    if total_advantage <= gap:
        return StrategyResult(
            strategy_name="輪胎年齡優勢 (繼續使用)",
            feasible=False,
            catchup_lap=None,
            total_advantage=total_advantage,
            details=f"總優勢 {total_advantage:.2f}s < 差距 {gap:.2f}s"
        )
    
    catchup_laps = int(gap / advantage_per_lap) + 1
    
    return StrategyResult(
        strategy_name="輪胎年齡優勢 (繼續使用)",
        feasible=True,
        catchup_lap=catchup_laps,
        total_advantage=total_advantage,
        details=f"每圈追回 {advantage_per_lap:.3f}s"
    )


# ============================================
# 策略 2: Undercut (立即進站)
# ============================================

def calculate_undercut_strategy(
    gap: float,
    current_lap: int,
    remaining_laps: int,
    pit_loss: float = 22.0,
    new_tire_advantage: float = 1.2
) -> StrategyResult:
    """
    策略 2: Undercut
    
    P2 立即進站換新胎，利用新胎優勢追趕
    """
    # 進站後差距會增加
    gap_after_pit = gap + pit_loss
    
    # 計算新胎優勢
    total_advantage = new_tire_advantage * remaining_laps
    
    if total_advantage <= gap_after_pit:
        return StrategyResult(
            strategy_name="Undercut (立即進站)",
            feasible=False,
            catchup_lap=None,
            total_advantage=total_advantage - pit_loss,
            details=f"進站後差距 {gap_after_pit:.1f}s，新胎優勢不足"
        )
    
    catchup_laps = int(gap_after_pit / new_tire_advantage) + 1
    catchup_lap = current_lap + catchup_laps
    
    return StrategyResult(
        strategy_name="Undercut (立即進站)",
        feasible=True,
        catchup_lap=catchup_lap,
        total_advantage=total_advantage - pit_loss,
        details=f"進站損失 {pit_loss}s，新胎每圈快 {new_tire_advantage}s"
    )


# ============================================
# 策略 3: SC 機會 (等待安全車)
# ============================================

def calculate_sc_opportunity_strategy(
    gap: float,
    current_lap: int,
    remaining_laps: int,
    sc_probability: float = 0.3,
    sc_pit_loss: float = 8.0,
    new_tire_advantage: float = 2.2
) -> StrategyResult:
    """
    策略 3: SC 機會
    
    等待安全車出現，利用 SC 期間進站節省時間
    """
    # SC 節省的進站時間
    pit_save = 22.0 - sc_pit_loss  # 節省 14 秒
    
    # 假設 SC 在剩餘圈數的中段出現
    sc_assumed_lap = current_lap + (remaining_laps // 3)
    laps_after_sc = remaining_laps - (remaining_laps // 3)
    
    # SC 後新胎優勢
    total_advantage = pit_save + (new_tire_advantage * laps_after_sc)
    
    if total_advantage <= gap:
        return StrategyResult(
            strategy_name="SC 機會 (等待安全車)",
            feasible=False,
            catchup_lap=None,
            total_advantage=total_advantage,
            details=f"即使有 SC，總優勢 {total_advantage:.1f}s < 差距 {gap:.1f}s"
        )
    
    # 計算追上圈數（假設 SC 出現）
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
        details=f"假設第 {sc_assumed_lap} 圈出現 SC (機率 {sc_probability*100:.0f}%)"
    )


# ============================================
# 策略 4: 主動進站模擬 (用戶自定義)
# ============================================

def calculate_active_pit_simulation(
    gap: float,
    current_lap: int,
    remaining_laps: int,
    tire_compound: str = "SOFT",
    pit_loss: float = 22.0
) -> StrategyResult:
    """
    策略 4: 主動進站模擬
    
    用戶可以自定義輪胎配方和進站時機
    """
    # 輪胎性能數據
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
            strategy_name=f"主動進站模擬 ({tire_compound})",
            feasible=False,
            catchup_lap=None,
            total_advantage=total_advantage - pit_loss,
            details=f"{tire_compound} 輪胎優勢不足"
        )
    
    catchup_laps = int(gap_after_pit / tire_data["advantage"]) + 1
    catchup_lap = current_lap + catchup_laps
    
    return StrategyResult(
        strategy_name=f"主動進站模擬 ({tire_compound})",
        feasible=True,
        catchup_lap=catchup_lap,
        total_advantage=total_advantage - pit_loss,
        details=f"{tire_compound}: 每圈快 {tire_data['advantage']}s，最佳 {tire_data['optimal_stint']} 圈"
    )


# ============================================
# 完整策略比較
# ============================================

def compare_all_strategies(
    gap: float,
    tire_age_diff: int,
    current_lap: int,
    total_laps: int
) -> List[StrategyResult]:
    """
    比較所有策略，返回完整結果列表
    """
    remaining_laps = total_laps - current_lap
    
    results = []
    
    # 策略 1: 輪胎年齡優勢
    results.append(calculate_tire_age_strategy(gap, tire_age_diff, remaining_laps))
    
    # 策略 2: Undercut
    results.append(calculate_undercut_strategy(gap, current_lap, remaining_laps))
    
    # 策略 3: SC 機會
    results.append(calculate_sc_opportunity_strategy(gap, current_lap, remaining_laps))
    
    # 策略 4: 主動進站模擬 (預設 SOFT)
    results.append(calculate_active_pit_simulation(gap, current_lap, remaining_laps, "SOFT"))
    
    return results


def print_strategy_comparison_table(results: List[StrategyResult], gap: float, remaining_laps: int):
    """列印策略比較表"""
    gap_category = classify_gap(gap)
    
    print("\n" + "=" * 90)
    print("策略比較表 (Strategy Comparison)")
    print("=" * 90)
    print(f"\n當前差距: {gap:.2f}s ({gap_category}) | 剩餘圈數: {remaining_laps} 圈\n")
    
    # 表頭
    print(f"{'#':<4} {'策略':<25} {'可行性':<10} {'追上圈數':<12} {'總優勢':<10}")
    print("-" * 90)
    
    # 每個策略
    for i, result in enumerate(results, 1):
        feasibility = "✅ 可行" if result.feasible else "❌ 不可行" if result.catchup_lap is None else "⏳ 待條件"
        catchup = f"第 {result.catchup_lap} 圈" if result.catchup_lap else "追不上"
        advantage = f"+{result.total_advantage:.1f}s" if result.total_advantage > 0 else f"{result.total_advantage:.1f}s"
        
        print(f"{i:<4} {result.strategy_name:<25} {feasibility:<10} {catchup:<12} {advantage:<10}")
        print(f"     {result.details}")
        print()
    
    # 推薦
    feasible_results = [r for r in results if r.feasible and r.catchup_lap]
    if feasible_results:
        best = min(feasible_results, key=lambda r: r.catchup_lap)
        print(f"💡 推薦: {best.strategy_name} - 最快可在第 {best.catchup_lap} 圈追上")
    else:
        print("⚠️  所有策略均無法保證追上 P1")
    
    print("=" * 90)


# ============================================
# 主程式：三種情境測試
# ============================================

def main():
    """測試三種不同差距情境"""
    
    print("=" * 90)
    print("完整策略比較 Demo")
    print("=" * 90)
    
    # 情境 1: 極小差距
    print("\n\n" + "🔹" * 45)
    print("情境 1: 極小差距 (0.8s)")
    print("🔹" * 45)
    
    results1 = compare_all_strategies(
        gap=0.8,
        tire_age_diff=2,
        current_lap=30,
        total_laps=58
    )
    print_strategy_comparison_table(results1, 0.8, 28)
    
    # 情境 2: 中等差距
    print("\n\n" + "🔹" * 45)
    print("情境 2: 中等差距 (5.2s)")
    print("🔹" * 45)
    
    results2 = compare_all_strategies(
        gap=5.2,
        tire_age_diff=4,
        current_lap=30,
        total_laps=58
    )
    print_strategy_comparison_table(results2, 5.2, 28)
    
    # 情境 3: 大差距
    print("\n\n" + "🔹" * 45)
    print("情境 3: 大差距 (13.5s)")
    print("🔹" * 45)
    
    results3 = compare_all_strategies(
        gap=13.5,
        tire_age_diff=0,  # P2 輪胎不比 P1 新
        current_lap=30,
        total_laps=58
    )
    print_strategy_comparison_table(results3, 13.5, 28)
    
    print("\n" + "=" * 90)
    print("✅ Demo 完成")
    print("=" * 90)


if __name__ == "__main__":
    main()
