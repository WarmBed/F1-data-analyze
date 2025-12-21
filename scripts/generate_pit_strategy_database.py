#!/usr/bin/env python3
"""
生成進站策略資料庫 - pit_strategy_database.json

將 F58 進站策略預測器的計算結果，為所有賽道生成預計算的進站窗口和策略推薦。
類似於 fuel_coefficients_database.json 的設計。

使用方式:
    python scripts/generate_pit_strategy_database.py

輸出:
    config/pit_strategy_database.json
"""

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加專案根目錄到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 資料庫路徑
TIRE_DEGRADATION_DB_PATH = project_root / "config" / "tire_degradation_database.json"
PIT_LOSS_DB_PATH = project_root / "config" / "pit_loss_database.json"


def load_database(path: str) -> dict:
    """載入 JSON 資料庫"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] 無法載入 {path}: {e}")
        return {}


def calculate_optimal_stint_length(
    compound: str,
    base_degradation: float,
    acceleration: float,
    pit_loss: float,
    total_laps: int,
    base_lap_time: float = 90.0
) -> int:
    """
    計算最佳 stint 長度
    
    使用公式: 當累積衰退 = 進站損失時，進站變得有利
    累積衰退 = base_rate * n + 0.5 * acceleration * n²
    
    解 n: base_rate * n + 0.5 * acceleration * n² = pit_loss
    """
    # 二次方程式: 0.5*a*n² + b*n - pit_loss = 0
    a = 0.5 * acceleration
    b = base_degradation
    c = -pit_loss
    
    if a == 0:
        # 線性情況
        if b > 0:
            n = pit_loss / b
        else:
            n = total_laps
    else:
        # 二次公式
        discriminant = b * b - 4 * a * c
        if discriminant >= 0:
            n = (-b + math.sqrt(discriminant)) / (2 * a)
        else:
            n = total_laps
    
    # 限制在合理範圍內
    n = max(5, min(int(n), total_laps - 1))
    
    return n


def calculate_stint_time(
    laps: int,
    base_lap_time: float,
    base_degradation: float,
    acceleration: float,
    grip_advantage: float
) -> float:
    """
    計算 stint 總時間
    
    每圈時間 = base_time + grip_advantage + 累積衰退
    累積衰退(lap i) = base_deg * i + 0.5 * accel * i²
    """
    total_time = 0.0
    for lap in range(1, laps + 1):
        lap_degradation = base_degradation * lap + 0.5 * acceleration * (lap ** 2)
        lap_time = base_lap_time + grip_advantage + lap_degradation
        total_time += lap_time
    return total_time


def generate_strategy_options(
    circuit_name: str,
    total_laps: int,
    pit_loss: float,
    tire_data: dict,
    base_lap_time: float = 90.0,
    optimal_stint_db: dict = None
) -> list:
    """
    生成策略選項並計算預測時間
    """
    strategies = []
    compounds = ["SOFT", "MEDIUM", "HARD"]
    
    # 獲取輪胎參數
    def get_tire_params(compound: str):
        data = tire_data.get(compound, {})
        return {
            "base_deg": data.get("base_degradation", 0.06),
            "accel": data.get("degradation_acceleration", 0.002),
            "grip": data.get("grip_advantage", 0.0)
        }
    
    # 獲取最佳 stint 長度 (優先使用資料庫)
    def get_optimal_stint(compound: str, p: dict) -> int:
        if optimal_stint_db and compound in optimal_stint_db:
            return optimal_stint_db[compound]
        return calculate_optimal_stint_length(
            compound, p["base_deg"], p["accel"], pit_loss, total_laps, base_lap_time
        )
    
    # 1-Stop 策略
    one_stop_combos = [
        ("SOFT", "HARD"),
        ("SOFT", "MEDIUM"),
        ("MEDIUM", "HARD"),
    ]
    
    for c1, c2 in one_stop_combos:
        p1 = get_tire_params(c1)
        p2 = get_tire_params(c2)
        
        # 使用資料庫中的最佳換胎點
        optimal_pit = get_optimal_stint(c1, p1)
        
        stint1_laps = min(optimal_pit, total_laps - 5)
        stint2_laps = total_laps - stint1_laps
        
        stint1_time = calculate_stint_time(
            stint1_laps, base_lap_time, p1["base_deg"], p1["accel"], p1["grip"]
        )
        stint2_time = calculate_stint_time(
            stint2_laps, base_lap_time, p2["base_deg"], p2["accel"], p2["grip"]
        )
        
        total_time = stint1_time + stint2_time + pit_loss
        
        strategies.append({
            "strategy_name": f"1-Stop ({c1[0]}→{c2[0]})",
            "stops": 1,
            "stints": [
                {"compound": c1, "laps": stint1_laps},
                {"compound": c2, "laps": stint2_laps}
            ],
            "predicted_time_seconds": round(total_time, 3),
            "pit_loss_total": pit_loss
        })
    
    # 2-Stop 策略
    two_stop_combos = [
        ("SOFT", "MEDIUM", "SOFT"),
        ("MEDIUM", "HARD", "MEDIUM"),
        ("SOFT", "HARD", "SOFT"),
    ]
    
    for c1, c2, c3 in two_stop_combos:
        p1 = get_tire_params(c1)
        p2 = get_tire_params(c2)
        p3 = get_tire_params(c3)
        
        # 平均分配圈數 (可優化)
        stint1_laps = max(10, total_laps // 4)
        stint2_laps = max(15, total_laps // 2 - 5)
        stint3_laps = total_laps - stint1_laps - stint2_laps
        
        stint1_time = calculate_stint_time(
            stint1_laps, base_lap_time, p1["base_deg"], p1["accel"], p1["grip"]
        )
        stint2_time = calculate_stint_time(
            stint2_laps, base_lap_time, p2["base_deg"], p2["accel"], p2["grip"]
        )
        stint3_time = calculate_stint_time(
            stint3_laps, base_lap_time, p3["base_deg"], p3["accel"], p3["grip"]
        )
        
        total_time = stint1_time + stint2_time + stint3_time + (pit_loss * 2)
        
        strategies.append({
            "strategy_name": f"2-Stop ({c1[0]}→{c2[0]}→{c3[0]})",
            "stops": 2,
            "stints": [
                {"compound": c1, "laps": stint1_laps},
                {"compound": c2, "laps": stint2_laps},
                {"compound": c3, "laps": stint3_laps}
            ],
            "predicted_time_seconds": round(total_time, 3),
            "pit_loss_total": pit_loss * 2
        })
    
    # 排序策略
    strategies.sort(key=lambda x: x["predicted_time_seconds"])
    
    # 計算與最佳策略的差距
    best_time = strategies[0]["predicted_time_seconds"]
    for s in strategies:
        gap = s["predicted_time_seconds"] - best_time
        s["gap_to_optimal_seconds"] = round(gap, 3)
    
    return strategies


def format_time(seconds: float) -> str:
    """格式化時間為 H:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:06.3f}"
    else:
        return f"{minutes}:{secs:06.3f}"


def generate_pit_strategy_database():
    """
    生成完整的進站策略資料庫
    """
    print("=" * 60)
    print("F1 進站策略資料庫生成器")
    print("=" * 60)
    
    # 載入資料庫
    tire_db = load_database(TIRE_DEGRADATION_DB_PATH)
    pit_loss_db = load_database(PIT_LOSS_DB_PATH)
    
    if not tire_db or not pit_loss_db:
        print("[ERROR] 無法載入必要的資料庫")
        return None
    
    tire_circuits = tire_db.get("circuits", {})
    pit_circuits = pit_loss_db.get("circuits", {})
    compound_info = tire_db.get("compounds", {})
    
    print(f"[INFO] 載入 {len(tire_circuits)} 個賽道的輪胎衰退資料")
    print(f"[INFO] 載入 {len(pit_circuits)} 個賽道的進站損失資料")
    
    # 建立輸出結構
    database = {
        "_metadata": {
            "version": "1.0.0",
            "description": "F1 賽道進站策略資料庫 - 預計算的進站窗口與策略推薦",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "generated_by": "generate_pit_strategy_database.py",
            "sources": [
                "tire_degradation_database.json",
                "pit_loss_database.json",
                "Cappello & Hoegh 2025: Time-Varying Linear Degradation Model"
            ],
            "model": {
                "type": "Time-Varying Linear Degradation",
                "formula": "degradation(t) = base_rate + acceleration * tire_age",
                "crossover_formula": "optimal_pit = solve(cumulative_degradation = pit_loss)"
            },
            "usage": {
                "pit_windows": "各輪胎的最佳進站時機區間",
                "recommended_strategy": "基於計算的最佳策略",
                "all_strategies": "所有策略的時間預測排名"
            }
        },
        "circuits": {}
    }
    
    # 處理每個賽道
    for circuit_name, tire_data in tire_circuits.items():
        print(f"\n[處理] {circuit_name}...")
        
        # 獲取賽道資料
        total_laps = tire_data.get("typical_race_laps", 55)
        
        # 估算基礎圈速 (根據賽道長度)
        track_length = tire_data.get("track_length_km", 5.0)
        base_lap_time = track_length * 17  # 大約每公里 17 秒
        
        # 獲取進站損失
        pit_data = pit_circuits.get(circuit_name, {})
        pit_loss = pit_data.get("pit_loss_seconds", 24.0)
        
        # 獲取各胎質資料 - 使用正確的 tire_degradation_database 結構
        base_degradation = tire_data.get("base_degradation", {})
        degradation_acceleration = tire_data.get("degradation_acceleration", {})
        optimal_stint_from_db = tire_data.get("optimal_stint_length", {})
        
        # 構建 compounds_data 結構
        compounds_data = {}
        grip_advantages = {"SOFT": -0.5, "MEDIUM": -0.25, "HARD": 0.0}
        
        for compound in ["SOFT", "MEDIUM", "HARD"]:
            compounds_data[compound] = {
                "base_degradation": base_degradation.get(compound, 0.06),
                "degradation_acceleration": degradation_acceleration.get(compound, 0.002),
                "grip_advantage": grip_advantages.get(compound, 0.0)
            }
        
        # 計算進站窗口 - 優先使用資料庫中的 optimal_stint_length
        pit_windows = {}
        for compound in ["SOFT", "MEDIUM", "HARD"]:
            comp_data = compounds_data.get(compound, {})
            base_deg = comp_data.get("base_degradation", 0.06)
            accel = comp_data.get("degradation_acceleration", 0.002)
            
            # 優先使用資料庫中的最佳 stint 長度
            if optimal_stint_from_db and compound in optimal_stint_from_db:
                optimal_lap = optimal_stint_from_db[compound]
            else:
                # 否則用公式計算
                optimal_lap = calculate_optimal_stint_length(
                    compound, base_deg, accel, pit_loss, total_laps, base_lap_time
                )
            
            # 進站窗口 (±3 圈)
            window_start = max(5, optimal_lap - 3)
            window_end = min(total_laps - 3, optimal_lap + 3)
            
            pit_windows[compound] = {
                "optimal_pit_lap": optimal_lap,
                "pit_window": {
                    "start": window_start,
                    "end": window_end
                },
                "max_stint_laps": min(optimal_lap + 10, total_laps),
                "confidence": 0.85
            }
        
        # 生成策略選項 - 傳入資料庫中的最佳 stint 長度
        strategies = generate_strategy_options(
            circuit_name, total_laps, pit_loss, compounds_data, base_lap_time,
            optimal_stint_db=optimal_stint_from_db
        )
        
        # 建立賽道資料
        database["circuits"][circuit_name] = {
            "official_name": tire_data.get("official_name", circuit_name),
            "track_length_km": tire_data.get("track_length_km", 5.0),
            "typical_race_laps": total_laps,
            "base_lap_time_seconds": base_lap_time,
            "pit_loss_seconds": pit_loss,
            "track_abrasiveness": tire_data.get("track_abrasiveness", "medium"),
            
            "pit_windows": pit_windows,
            
            "recommended_strategy": {
                "name": strategies[0]["strategy_name"],
                "stops": strategies[0]["stops"],
                "stints": strategies[0]["stints"],
                "predicted_time": format_time(strategies[0]["predicted_time_seconds"]),
                "predicted_time_seconds": strategies[0]["predicted_time_seconds"]
            },
            
            "all_strategies": [
                {
                    "rank": i + 1,
                    "name": s["strategy_name"],
                    "stops": s["stops"],
                    "stints": s["stints"],
                    "predicted_time": format_time(s["predicted_time_seconds"]),
                    "gap_to_optimal": f"+{s['gap_to_optimal_seconds']:.1f}s" if s['gap_to_optimal_seconds'] > 0 else "最佳"
                }
                for i, s in enumerate(strategies)
            ],
            
            "notes": tire_data.get("notes", "")
        }
        
        print(f"  ✓ 最佳策略: {strategies[0]['strategy_name']} ({format_time(strategies[0]['predicted_time_seconds'])})")
    
    # 輸出 JSON
    output_path = project_root / "config" / "pit_strategy_database.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"[SUCCESS] 資料庫已生成: {output_path}")
    print(f"[INFO] 共處理 {len(database['circuits'])} 個賽道")
    print("=" * 60)
    
    return database


if __name__ == "__main__":
    generate_pit_strategy_database()
