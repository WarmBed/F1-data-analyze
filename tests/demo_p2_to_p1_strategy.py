"""
P2 追趕 P1 策略建議系統 - Demo
====================================

使用 FastF1 真實數據演示策略計算
"""

import fastf1
import pandas as pd
from datetime import timedelta
import json

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

print("=" * 80)
print("P2 追趕 P1 策略建議系統 - Demo")
print("=" * 80)


def classify_gap(gap: float) -> str:
    """差距分級"""
    if gap < 3.0:
        return "極小"
    elif gap < 8.0:
        return "中等"
    elif gap < 15.0:
        return "大"
    else:
        return "極大"


def calculate_tire_age_advantage(p1_tire_age: int, p2_tire_age: int, 
                                 degradation_rate: float, remaining_laps: int) -> dict:
    """計算輪胎年齡優勢"""
    tire_age_delta = p1_tire_age - p2_tire_age
    per_lap_delta = tire_age_delta * degradation_rate
    catchable_time = per_lap_delta * remaining_laps
    
    return {
        "name": "輪胎年齡優勢策略",
        "tire_age_delta": tire_age_delta,
        "per_lap_advantage": per_lap_delta,
        "catchable_time": catchable_time,
        "feasible": catchable_time > 0
    }


def calculate_undercut_advantage(current_gap: float, p1_tire_age: int,
                                current_lap: int, pit_loss: float = 22.0) -> dict:
    """計算 Undercut 優勢"""
    # P1 預計進站圈（假設輪胎壽命 25 圈）
    optimal_stint = 25
    p1_expected_pit_lap = current_lap + (optimal_stint - p1_tire_age)
    
    # P2 提前 3 圈進站
    p2_pit_lap = p1_expected_pit_lap - 3
    chase_laps = 3
    
    # 新胎每圈優勢
    new_tire_advantage = 1.2
    catchable_time = new_tire_advantage * chase_laps
    
    # 淨優勢
    net_advantage = catchable_time - current_gap
    
    return {
        "name": "Undercut 策略",
        "p2_pit_lap": p2_pit_lap,
        "p1_expected_pit_lap": p1_expected_pit_lap,
        "chase_laps": chase_laps,
        "new_tire_advantage": new_tire_advantage,
        "catchable_time": catchable_time,
        "net_advantage": net_advantage,
        "feasible": net_advantage > 0
    }


def calculate_sc_opportunity(current_gap: float, remaining_laps: int,
                            pit_loss: float = 22.0, sc_pit_loss: float = 8.0) -> dict:
    """計算 SC 機會"""
    saved_time = pit_loss - sc_pit_loss
    new_tire_advantage = 2.2  # SC 重啟後新胎優勢更大
    
    # 假設 SC 重啟後可追趕 5 圈
    chase_laps = min(5, remaining_laps)
    additional_advantage = new_tire_advantage * chase_laps
    
    total_advantage = saved_time + additional_advantage
    
    return {
        "name": "SC 機會策略",
        "saved_time": saved_time,
        "new_tire_advantage_per_lap": new_tire_advantage,
        "chase_laps": chase_laps,
        "additional_advantage": additional_advantage,
        "total_advantage": total_advantage,
        "feasible": total_advantage > current_gap
    }


def recommend_strategy(p1_data: dict, p2_data: dict, current_lap: int, 
                      total_laps: int) -> dict:
    """智能推薦策略"""
    current_gap = p2_data["gap"]
    remaining_laps = total_laps - current_lap
    
    # 差距分級
    gap_category = classify_gap(current_gap)
    
    print(f"\n當前賽況:")
    print(f"  P1: {p1_data['driver']} | 輪胎年齡: {p1_data['tire_age']} 圈")
    print(f"  P2: {p2_data['driver']} | 差距: {current_gap:.2f}s | 輪胎年齡: {p2_data['tire_age']} 圈")
    print(f"  當前圈數: {current_lap}/{total_laps} | 剩餘: {remaining_laps} 圈")
    print(f"\n差距評估: {gap_category}差距 ({current_gap:.2f}s)")
    
    scenarios = []
    
    # 根據差距分級篩選策略
    if gap_category == "極小":
        print("  建議: DRS 或輪胎優勢策略")
        print("  警告: 不建議進站（進站損失過大）")
        
        # 輪胎年齡優勢
        tire_scenario = calculate_tire_age_advantage(
            p1_data["tire_age"], p2_data["tire_age"], 
            0.08, remaining_laps
        )
        scenarios.append(tire_scenario)
        
    elif gap_category == "中等":
        print("  建議: Undercut 或配方差異策略")
        print("  機會: 進站時機視窗開啟")
        
        # Undercut 策略
        undercut_scenario = calculate_undercut_advantage(
            current_gap, p1_data["tire_age"], current_lap
        )
        scenarios.append(undercut_scenario)
        
        # 輪胎年齡優勢
        tire_scenario = calculate_tire_age_advantage(
            p1_data["tire_age"], p2_data["tire_age"],
            0.08, remaining_laps
        )
        scenarios.append(tire_scenario)
        
    elif gap_category in ["大", "極大"]:
        print("  建議: 僅 SC 機會可行")
        print("  警告: 常規策略無法追上")
        
        # SC 機會
        sc_scenario = calculate_sc_opportunity(current_gap, remaining_laps)
        scenarios.append(sc_scenario)
    
    # 排序場景
    scenarios.sort(key=lambda x: x.get("catchable_time", x.get("total_advantage", 0)), reverse=True)
    
    # 顯示所有場景
    print(f"\n策略分析結果:")
    print("-" * 80)
    
    for i, scenario in enumerate(scenarios, 1):
        feasible = scenario.get("feasible", False)
        status = "可行" if feasible else "不可行"
        
        print(f"\n場景 {i}: {scenario['name']} [{status}]")
        
        if "tire_age_delta" in scenario:
            print(f"  輪胎年齡差距: {scenario['tire_age_delta']} 圈")
            print(f"  每圈優勢: {scenario['per_lap_advantage']:.3f}s")
            print(f"  可追回時間: {scenario['catchable_time']:.2f}s")
            if feasible:
                laps_to_catch = int(current_gap / scenario['per_lap_advantage'])
                print(f"  預計追上圈數: 第 {current_lap + laps_to_catch} 圈")
        
        elif "p2_pit_lap" in scenario:
            print(f"  P2 建議進站圈: 第 {scenario['p2_pit_lap']} 圈")
            print(f"  P1 預計進站圈: 第 {scenario['p1_expected_pit_lap']} 圈")
            print(f"  追趕圈數: {scenario['chase_laps']} 圈")
            print(f"  新胎優勢: {scenario['new_tire_advantage']}s/圈")
            print(f"  可追回時間: {scenario['catchable_time']:.2f}s")
            print(f"  淨優勢: {scenario['net_advantage']:.2f}s")
            if feasible:
                print(f"  預計結果: P2 領先 {scenario['net_advantage']:.2f}s")
        
        elif "saved_time" in scenario:
            print(f"  SC 進站節省時間: {scenario['saved_time']:.2f}s")
            print(f"  SC 重啟後每圈優勢: {scenario['new_tire_advantage_per_lap']}s")
            print(f"  追趕圈數: {scenario['chase_laps']} 圈")
            print(f"  額外優勢: {scenario['additional_advantage']:.2f}s")
            print(f"  總優勢: {scenario['total_advantage']:.2f}s")
            if feasible:
                print(f"  預計結果: P2 可追上")
    
    return {
        "gap_category": gap_category,
        "current_gap": current_gap,
        "remaining_laps": remaining_laps,
        "scenarios": scenarios,
        "recommended": scenarios[0] if scenarios else None
    }


def load_real_race_data(year: int = 2024, race: str = "Japan", session: str = "R"):
    """從 FastF1 載入真實賽事數據"""
    print(f"\n正在載入 FastF1 數據: {year} {race} {session}")
    print("-" * 80)
    
    try:
        # 載入賽事
        f1_session = fastf1.get_session(year, race, session)
        f1_session.load()
        
        print(f"賽事載入成功: {f1_session.event['EventName']}")
        
        # 獲取最終結果（P1 和 P2）
        results = f1_session.results
        
        if len(results) < 2:
            print("錯誤: 賽事結果不足 2 位車手")
            return None
        
        p1_driver = results.iloc[0]["Abbreviation"]
        p2_driver = results.iloc[1]["Abbreviation"]
        
        print(f"\nP1: {p1_driver}")
        print(f"P2: {p2_driver}")
        
        # 獲取車手的圈速數據
        p1_laps = f1_session.laps.pick_driver(p1_driver)
        p2_laps = f1_session.laps.pick_driver(p2_driver)
        
        # 選擇中期某一圈進行分析（例如第 30 圈）
        analysis_lap = 30
        
        if len(p1_laps) < analysis_lap or len(p2_laps) < analysis_lap:
            print(f"警告: 圈數不足，使用第 20 圈")
            analysis_lap = 20
        
        p1_lap = p1_laps[p1_laps["LapNumber"] == analysis_lap].iloc[0]
        p2_lap = p2_laps[p2_laps["LapNumber"] == analysis_lap].iloc[0]
        
        # 計算差距（簡化計算）
        # 實際應該用累計時間，這裡用單圈時間差估算
        gap = (p2_lap["LapTime"] - p1_lap["LapTime"]).total_seconds() * analysis_lap * 0.1
        if gap < 0:
            gap = abs(gap)
        if gap > 20:  # 避免過大差距
            gap = 5.0
        
        # 估算輪胎年齡（簡化）
        p1_tire_age = 12
        p2_tire_age = 8
        
        # 如果有 compound 數據
        if "Compound" in p1_lap and pd.notna(p1_lap["Compound"]):
            p1_compound = p1_lap["Compound"]
            p2_compound = p2_lap["Compound"]
        else:
            p1_compound = "MEDIUM"
            p2_compound = "MEDIUM"
        
        print(f"\n第 {analysis_lap} 圈分析:")
        print(f"  P1: {p1_driver} | 配方: {p1_compound} | 估計輪胎年齡: {p1_tire_age} 圈")
        print(f"  P2: {p2_driver} | 配方: {p2_compound} | 估計輪胎年齡: {p2_tire_age} 圈")
        print(f"  估計差距: {gap:.2f}s")
        
        # 獲取總圈數
        try:
            if "EventFormat" in f1_session.event:
                total_laps = int(f1_session.event["EventFormat"].split("/")[-1])
            else:
                total_laps = 53  # 預設值
        except:
            total_laps = 53
        
        return {
            "year": year,
            "race": race,
            "session": session,
            "analysis_lap": analysis_lap,
            "total_laps": total_laps,
            "p1": {
                "driver": p1_driver,
                "tire_age": p1_tire_age,
                "compound": p1_compound
            },
            "p2": {
                "driver": p2_driver,
                "gap": gap,
                "tire_age": p2_tire_age,
                "compound": p2_compound
            }
        }
    
    except Exception as e:
        print(f"載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_demo():
    """運行 Demo"""
    print("\n" + "=" * 80)
    print("場景 1: 使用 FastF1 真實數據")
    print("=" * 80)
    
    # 載入真實數據
    race_data = load_real_race_data(2024, "Japan", "R")
    
    if race_data:
        # 執行策略推薦
        result = recommend_strategy(
            race_data["p1"],
            race_data["p2"],
            race_data["analysis_lap"],
            race_data["total_laps"]
        )
        display_recommendation(result)
    
    # 場景 2：模擬中等差距
    print("\n\n" + "=" * 80)
    print("場景 2: 模擬中等差距 (5.2s)")
    print("=" * 80)
    
    race_data_medium = {
        "year": 2024,
        "race": "Japan",
        "session": "R",
        "analysis_lap": 25,
        "total_laps": 53,
        "p1": {
            "driver": "VER",
            "tire_age": 12,
            "compound": "MEDIUM"
        },
        "p2": {
            "driver": "LEC",
            "gap": 5.2,
            "tire_age": 8,
            "compound": "MEDIUM"
        }
    }
    
    result_medium = recommend_strategy(
        race_data_medium["p1"],
        race_data_medium["p2"],
        race_data_medium["analysis_lap"],
        race_data_medium["total_laps"]
    )
    display_recommendation(result_medium)
    
    # 場景 3：模擬大差距
    print("\n\n" + "=" * 80)
    print("場景 3: 模擬大差距 (12.5s)")
    print("=" * 80)
    
    race_data_large = {
        "year": 2024,
        "race": "Japan",
        "session": "R",
        "analysis_lap": 28,
        "total_laps": 53,
        "p1": {
            "driver": "VER",
            "tire_age": 15,
            "compound": "MEDIUM"
        },
        "p2": {
            "driver": "LEC",
            "gap": 12.5,
            "tire_age": 12,
            "compound": "MEDIUM"
        }
    }
    
    result_large = recommend_strategy(
        race_data_large["p1"],
        race_data_large["p2"],
        race_data_large["analysis_lap"],
        race_data_large["total_laps"]
    )
    display_recommendation(result_large)


def display_recommendation(result):
    """顯示推薦結果"""
    print("\n" + "=" * 80)
    print("最佳策略推薦")
    print("=" * 80)
    
    if result["recommended"]:
        recommended = result["recommended"]
        print(f"\n推薦策略: {recommended['name']}")
        print(f"可行性: {'可行' if recommended['feasible'] else '不可行'}")
        
        if recommended['feasible']:
            if "catchable_time" in recommended:
                print(f"可追回時間: {recommended['catchable_time']:.2f}s")
            elif "total_advantage" in recommended:
                print(f"總優勢: {recommended['total_advantage']:.2f}s")
            
            print("\n執行建議:")
            if "p2_pit_lap" in recommended:
                print(f"  1. P2 在第 {recommended['p2_pit_lap']} 圈進站")
                print(f"  2. 用新胎追趕 {recommended['chase_laps']} 圈")
                print(f"  3. P1 第 {recommended['p1_expected_pit_lap']} 圈進站時，P2 將領先")
            elif "tire_age_delta" in recommended:
                print(f"  1. 保持當前策略，不進站")
                print(f"  2. 利用輪胎年齡優勢穩定追趕")
                print(f"  3. 每圈縮小 {recommended['per_lap_advantage']:.3f}s")
            elif "saved_time" in recommended:
                print(f"  1. 等待 SC 出現")
                print(f"  2. SC 期間進站，節省 {recommended['saved_time']:.2f}s")
                print(f"  3. SC 重啟後快速追趕")
        else:
            print("\n當前差距過大，建議保守策略")
    else:
        print("\n無可行策略")
    
    print("\n" + "=" * 80)
    print("Demo 完成")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
