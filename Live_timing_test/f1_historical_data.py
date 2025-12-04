"""
2023-2024 年 F1 賽事結果數據
從官方統計手動整理
格式: {year: [{race: name, q_top3: [driver_codes], r_top3: [driver_codes]}]}
"""

# 2023 年賽季結果 (22場比賽)
F1_2023_RESULTS = [
    {"round": 1, "race": "Bahrain", "pole": "VER", "winner": "VER", "q_top5": ["VER", "LEC", "SAI", "PER", "ALO"], "r_top5": ["VER", "PER", "ALO", "SAI", "HAM"]},
    {"round": 2, "race": "Saudi Arabia", "pole": "PER", "winner": "PER", "q_top5": ["PER", "LEC", "ALO", "RUS", "SAI"], "r_top5": ["PER", "VER", "ALO", "RUS", "HAM"]},
    {"round": 3, "race": "Australia", "pole": "VER", "winner": "VER", "q_top5": ["VER", "RUS", "HAM", "ALO", "SAI"], "r_top5": ["VER", "HAM", "ALO", "STR", "PER"]},
    {"round": 4, "race": "Azerbaijan", "pole": "LEC", "winner": "PER", "q_top5": ["LEC", "VER", "PER", "SAI", "HAM"], "r_top5": ["PER", "VER", "LEC", "ALO", "SAI"]},
    {"round": 5, "race": "Miami", "pole": "PER", "winner": "VER", "q_top5": ["PER", "ALO", "SAI", "MAG", "NOR"], "r_top5": ["VER", "PER", "ALO", "RUS", "SAI"]},
    {"round": 6, "race": "Monaco", "pole": "VER", "winner": "VER", "q_top5": ["VER", "ALO", "LEC", "OCO", "SAI"], "r_top5": ["VER", "ALO", "OCO", "HAM", "RUS"]},
    {"round": 7, "race": "Spain", "pole": "VER", "winner": "VER", "q_top5": ["VER", "SAI", "NOR", "STR", "HAM"], "r_top5": ["VER", "HAM", "RUS", "PER", "SAI"]},
    {"round": 8, "race": "Canada", "pole": "VER", "winner": "VER", "q_top5": ["VER", "HUL", "ALO", "HAM", "RUS"], "r_top5": ["VER", "ALO", "HAM", "LEC", "SAI"]},
    {"round": 9, "race": "Austria", "pole": "VER", "winner": "VER", "q_top5": ["VER", "LEC", "SAI", "NOR", "HAM"], "r_top5": ["VER", "LEC", "PER", "NOR", "ALO"]},
    {"round": 10, "race": "Britain", "pole": "VER", "winner": "VER", "q_top5": ["VER", "NOR", "HAM", "PIA", "PER"], "r_top5": ["VER", "NOR", "HAM", "PIA", "ALO"]},
    {"round": 11, "race": "Hungary", "pole": "HAM", "winner": "VER", "q_top5": ["HAM", "VER", "NOR", "PER", "SAI"], "r_top5": ["VER", "NOR", "PER", "HAM", "PIA"]},
    {"round": 12, "race": "Belgium", "pole": "LEC", "winner": "VER", "q_top5": ["LEC", "PER", "HAM", "SAI", "ALO"], "r_top5": ["VER", "PER", "LEC", "HAM", "ALO"]},
    {"round": 13, "race": "Netherlands", "pole": "VER", "winner": "VER", "q_top5": ["VER", "NOR", "RUS", "ALO", "SAI"], "r_top5": ["VER", "ALO", "GAS", "PER", "SAI"]},
    {"round": 14, "race": "Italy", "pole": "SAI", "winner": "VER", "q_top5": ["SAI", "VER", "PER", "LEC", "RUS"], "r_top5": ["VER", "PER", "SAI", "LEC", "RUS"]},
    {"round": 15, "race": "Singapore", "pole": "SAI", "winner": "SAI", "q_top5": ["SAI", "RUS", "LEC", "NOR", "VER"], "r_top5": ["SAI", "NOR", "HAM", "LEC", "VER"]},
    {"round": 16, "race": "Japan", "pole": "VER", "winner": "VER", "q_top5": ["VER", "PIA", "NOR", "HAM", "LEC"], "r_top5": ["VER", "NOR", "PIA", "LEC", "HAM"]},
    {"round": 17, "race": "Qatar", "pole": "VER", "winner": "VER", "q_top5": ["VER", "RUS", "HAM", "LEC", "NOR"], "r_top5": ["VER", "PIA", "NOR", "RUS", "LEC"]},
    {"round": 18, "race": "United States", "pole": "LEC", "winner": "VER", "q_top5": ["LEC", "NOR", "VER", "SAI", "PER"], "r_top5": ["VER", "HAM", "NOR", "SAI", "PER"]},
    {"round": 19, "race": "Mexico", "pole": "LEC", "winner": "VER", "q_top5": ["LEC", "SAI", "VER", "RUS", "HAM"], "r_top5": ["VER", "HAM", "LEC", "SAI", "NOR"]},
    {"round": 20, "race": "Brazil", "pole": "VER", "winner": "VER", "q_top5": ["VER", "LEC", "STR", "NOR", "SAI"], "r_top5": ["VER", "NOR", "ALO", "PER", "STR"]},
    {"round": 21, "race": "Las Vegas", "pole": "LEC", "winner": "VER", "q_top5": ["LEC", "SAI", "VER", "RUS", "HAM"], "r_top5": ["VER", "LEC", "PER", "OCO", "STR"]},
    {"round": 22, "race": "Abu Dhabi", "pole": "VER", "winner": "VER", "q_top5": ["VER", "LEC", "RUS", "SAI", "HAM"], "r_top5": ["VER", "LEC", "RUS", "HAM", "NOR"]},
]

# 2024 年賽季結果 (24場比賽)
F1_2024_RESULTS = [
    {"round": 1, "race": "Bahrain", "pole": "VER", "winner": "VER", "q_top5": ["VER", "LEC", "RUS", "SAI", "PER"], "r_top5": ["VER", "PER", "SAI", "LEC", "RUS"]},
    {"round": 2, "race": "Saudi Arabia", "pole": "VER", "winner": "VER", "q_top5": ["VER", "LEC", "SAI", "PER", "ALO"], "r_top5": ["VER", "PER", "LEC", "PIA", "ALO"]},
    {"round": 3, "race": "Australia", "pole": "VER", "winner": "SAI", "q_top5": ["VER", "SAI", "NOR", "PIA", "PER"], "r_top5": ["SAI", "LEC", "NOR", "PER", "PIA"]},
    {"round": 4, "race": "Japan", "pole": "VER", "winner": "VER", "q_top5": ["VER", "PER", "SAI", "NOR", "LEC"], "r_top5": ["VER", "PER", "SAI", "LEC", "NOR"]},
    {"round": 5, "race": "China", "pole": "VER", "winner": "VER", "q_top5": ["VER", "PER", "ALO", "SAI", "LEC"], "r_top5": ["VER", "NOR", "PER", "LEC", "SAI"]},
    {"round": 6, "race": "Miami", "pole": "VER", "winner": "NOR", "q_top5": ["VER", "LEC", "SAI", "PER", "RIC"], "r_top5": ["NOR", "VER", "LEC", "PER", "SAI"]},
    {"round": 7, "race": "Emilia Romagna", "pole": "VER", "winner": "VER", "q_top5": ["VER", "PIA", "NOR", "LEC", "SAI"], "r_top5": ["VER", "NOR", "LEC", "PIA", "SAI"]},
    {"round": 8, "race": "Monaco", "pole": "LEC", "winner": "LEC", "q_top5": ["LEC", "PIA", "SAI", "NOR", "RUS"], "r_top5": ["LEC", "PIA", "SAI", "NOR", "RUS"]},
    {"round": 9, "race": "Canada", "pole": "RUS", "winner": "VER", "q_top5": ["RUS", "VER", "NOR", "PIA", "RIC"], "r_top5": ["VER", "NOR", "RUS", "HAM", "PIA"]},
    {"round": 10, "race": "Spain", "pole": "NOR", "winner": "VER", "q_top5": ["NOR", "VER", "HAM", "RUS", "LEC"], "r_top5": ["VER", "NOR", "HAM", "RUS", "LEC"]},
    {"round": 11, "race": "Austria", "pole": "VER", "winner": "RUS", "q_top5": ["VER", "NOR", "SAI", "LEC", "HAM"], "r_top5": ["RUS", "PIA", "SAI", "HAM", "VER"]},
    {"round": 12, "race": "Britain", "pole": "RUS", "winner": "HAM", "q_top5": ["RUS", "HAM", "NOR", "VER", "PIA"], "r_top5": ["HAM", "VER", "NOR", "PIA", "SAI"]},
    {"round": 13, "race": "Hungary", "pole": "NOR", "winner": "PIA", "q_top5": ["NOR", "PIA", "VER", "SAI", "HAM"], "r_top5": ["PIA", "NOR", "HAM", "LEC", "VER"]},
    {"round": 14, "race": "Belgium", "pole": "LEC", "winner": "HAM", "q_top5": ["LEC", "PER", "HAM", "NOR", "PIA"], "r_top5": ["HAM", "PIA", "LEC", "VER", "NOR"]},
    {"round": 15, "race": "Netherlands", "pole": "NOR", "winner": "NOR", "q_top5": ["NOR", "VER", "PIA", "RUS", "SAI"], "r_top5": ["NOR", "VER", "LEC", "PIA", "SAI"]},
    {"round": 16, "race": "Italy", "pole": "NOR", "winner": "LEC", "q_top5": ["NOR", "PIA", "RUS", "LEC", "SAI"], "r_top5": ["LEC", "PIA", "NOR", "SAI", "HAM"]},
    {"round": 17, "race": "Azerbaijan", "pole": "LEC", "winner": "PIA", "q_top5": ["LEC", "PIA", "SAI", "PER", "VER"], "r_top5": ["PIA", "LEC", "RUS", "NOR", "VER"]},
    {"round": 18, "race": "Singapore", "pole": "NOR", "winner": "NOR", "q_top5": ["NOR", "VER", "HAM", "RUS", "PIA"], "r_top5": ["NOR", "VER", "PIA", "RUS", "LEC"]},
    {"round": 19, "race": "United States", "pole": "NOR", "winner": "LEC", "q_top5": ["NOR", "VER", "SAI", "LEC", "HAM"], "r_top5": ["LEC", "SAI", "VER", "NOR", "PIA"]},
    {"round": 20, "race": "Mexico", "pole": "SAI", "winner": "SAI", "q_top5": ["SAI", "VER", "NOR", "LEC", "RUS"], "r_top5": ["SAI", "NOR", "LEC", "HAM", "RUS"]},
    {"round": 21, "race": "Brazil", "pole": "NOR", "winner": "VER", "q_top5": ["NOR", "RUS", "TSU", "OCO", "NOR"], "r_top5": ["VER", "OCO", "GAS", "RUS", "LEC"]},
    {"round": 22, "race": "Las Vegas", "pole": "RUS", "winner": "RUS", "q_top5": ["RUS", "SAI", "GAS", "LEC", "VER"], "r_top5": ["RUS", "HAM", "SAI", "LEC", "VER"]},
    {"round": 23, "race": "Qatar", "pole": "VER", "winner": "VER", "q_top5": ["VER", "RUS", "NOR", "PIA", "SAI"], "r_top5": ["VER", "LEC", "PIA", "RUS", "NOR"]},
    {"round": 24, "race": "Abu Dhabi", "pole": "NOR", "winner": "NOR", "q_top5": ["NOR", "PIA", "SAI", "VER", "HAM"], "r_top5": ["NOR", "SAI", "LEC", "HAM", "VER"]},
]

# 車隊評級 (用於訓練)
TEAM_RATINGS = {
    "Red Bull Racing": 10,
    "Red Bull": 10,
    "Ferrari": 9,
    "McLaren": 8,
    "Mercedes": 8,
    "Aston Martin": 7,
    "Alpine": 5,
    "Williams": 4,
    "RB": 5,  # AlphaTauri -> RB
    "AlphaTauri": 5,
    "Kick Sauber": 3,
    "Sauber": 3,
    "Haas F1 Team": 4,
    "Haas": 4,
}

# 車手所屬車隊
DRIVER_TEAMS = {
    # 2023-2024 常見車手
    "VER": "Red Bull",
    "PER": "Red Bull",
    "LEC": "Ferrari",
    "SAI": "Ferrari",
    "HAM": "Mercedes",
    "RUS": "Mercedes",
    "NOR": "McLaren",
    "PIA": "McLaren",
    "ALO": "Aston Martin",
    "STR": "Aston Martin",
    "GAS": "Alpine",
    "OCO": "Alpine",
    "BOT": "Sauber",
    "ZHO": "Sauber",
    "TSU": "RB",
    "RIC": "RB",
    "DEV": "RB",
    "LAW": "RB",
    "ALB": "Williams",
    "SAR": "Williams",
    "COL": "Williams",
    "HUL": "Haas",
    "MAG": "Haas",
    "BEA": "Haas",
}

def get_team_rating(driver_code: str) -> int:
    """獲取車手所屬車隊的評級"""
    team = DRIVER_TEAMS.get(driver_code, "Unknown")
    return TEAM_RATINGS.get(team, 5)

def build_training_samples(results_list: list, year: int) -> list:
    """從結果列表建立訓練樣本"""
    samples = []
    
    for race in results_list:
        race_name = race["race"]
        q_top5 = race["q_top5"]
        r_top5 = race["r_top5"]
        winner = race["winner"]
        
        # 為 Q 前 5 名建立樣本
        for q_pos, driver in enumerate(q_top5, 1):
            # 查找正賽排名
            r_pos = r_top5.index(driver) + 1 if driver in r_top5 else 10
            
            sample = {
                "year": year,
                "race": race_name,
                "driver": driver,
                "team": DRIVER_TEAMS.get(driver, "Unknown"),
                "team_rating": get_team_rating(driver),
                "q_position": q_pos,
                "r_position": r_pos,
                "is_winner": 1 if driver == winner else 0,
                "pole_to_win": 1 if q_pos == 1 and driver == winner else 0
            }
            samples.append(sample)
    
    return samples

if __name__ == "__main__":
    import json
    from pathlib import Path
    
    output_dir = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze/json/historical_data")
    output_dir.mkdir(exist_ok=True)
    
    # 建立 2023 訓練數據
    samples_2023 = build_training_samples(F1_2023_RESULTS, 2023)
    print(f"2023 樣本數: {len(samples_2023)}")
    
    # 建立 2024 訓練數據
    samples_2024 = build_training_samples(F1_2024_RESULTS, 2024)
    print(f"2024 樣本數: {len(samples_2024)}")
    
    # 合併
    all_samples = samples_2023 + samples_2024
    print(f"總樣本數: {len(all_samples)}")
    
    # 統計
    wins_from_pole = sum(1 for s in all_samples if s["pole_to_win"])
    total_races = len(F1_2023_RESULTS) + len(F1_2024_RESULTS)
    print(f"\n桿位奪冠率: {wins_from_pole}/{total_races} = {wins_from_pole/total_races*100:.1f}%")
    
    # 各位置奪冠統計
    for pos in range(1, 6):
        wins = sum(1 for s in all_samples if s["q_position"] == pos and s["is_winner"])
        print(f"Q{pos} 奪冠: {wins} 次")
    
    # 保存
    output_file = output_dir / "f1_2023_2024_training_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "2023": samples_2023,
            "2024": samples_2024,
            "all": all_samples,
            "metadata": {
                "total_races": total_races,
                "total_samples": len(all_samples),
                "pole_to_win_rate": wins_from_pole / total_races
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 已保存: {output_file}")
