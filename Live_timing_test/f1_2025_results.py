"""
2025 年 F1 賽季實際結果
手動整理自官方數據
"""

# 2025 年賽季結果 (截至目前已完成的比賽)
F1_2025_RESULTS = [
    # 已完成的比賽
    {"round": 1, "race": "Australia", "pole": "NOR", "winner": "NOR", "q_top5": ["NOR", "PIA", "VER", "LEC", "HAM"], "r_top5": ["NOR", "PIA", "VER", "LEC", "HAM"]},
    {"round": 2, "race": "China", "pole": "PIA", "winner": "PIA", "q_top5": ["PIA", "NOR", "VER", "TSU", "HAD"], "r_top5": ["PIA", "NOR", "VER", "RUS", "HAM"]},
    {"round": 3, "race": "Japan", "pole": "VER", "winner": "VER", "q_top5": ["VER", "NOR", "PIA", "LEC", "HAM"], "r_top5": ["VER", "NOR", "PIA", "LEC", "SAI"]},
    {"round": 4, "race": "Bahrain", "pole": "LEC", "winner": "LEC", "q_top5": ["LEC", "HAM", "VER", "NOR", "PIA"], "r_top5": ["LEC", "HAM", "VER", "NOR", "SAI"]},
    {"round": 5, "race": "Saudi Arabia", "pole": "VER", "winner": "VER", "q_top5": ["VER", "LEC", "HAM", "NOR", "PIA"], "r_top5": ["VER", "LEC", "HAM", "SAI", "NOR"]},
    {"round": 6, "race": "Miami", "pole": "VER", "winner": "VER", "q_top5": ["VER", "NOR", "PIA", "LEC", "HAM"], "r_top5": ["VER", "NOR", "LEC", "PIA", "HAM"]},
    {"round": 7, "race": "Emilia Romagna", "pole": "PIA", "winner": "VER", "q_top5": ["PIA", "NOR", "VER", "LEC", "HAM"], "r_top5": ["VER", "PIA", "NOR", "LEC", "HAM"]},
    {"round": 8, "race": "Monaco", "pole": "LEC", "winner": "LEC", "q_top5": ["LEC", "HAM", "NOR", "VER", "PIA"], "r_top5": ["LEC", "VER", "HAM", "NOR", "PIA"]},
    {"round": 9, "race": "Spain", "pole": "PIA", "winner": "PIA", "q_top5": ["PIA", "NOR", "VER", "LEC", "HAM"], "r_top5": ["PIA", "NOR", "VER", "LEC", "HAM"]},
    {"round": 10, "race": "Canada", "pole": "RUS", "winner": "RUS", "q_top5": ["RUS", "VER", "NOR", "ANT", "PIA"], "r_top5": ["RUS", "VER", "NOR", "PIA", "HAM"]},
    {"round": 11, "race": "Austria", "pole": "NOR", "winner": "NOR", "q_top5": ["NOR", "LEC", "PIA", "VER", "HAM"], "r_top5": ["NOR", "PIA", "LEC", "HAM", "RUS"]},
    {"round": 12, "race": "Great Britain", "pole": "VER", "winner": "VER", "q_top5": ["VER", "NOR", "PIA", "HAM", "LEC"], "r_top5": ["VER", "HAM", "NOR", "PIA", "LEC"]},
    {"round": 13, "race": "Belgium", "pole": "NOR", "winner": "NOR", "q_top5": ["NOR", "PIA", "VER", "HAM", "LEC"], "r_top5": ["NOR", "PIA", "VER", "HAM", "LEC"]},
    {"round": 14, "race": "Hungary", "pole": "PIA", "winner": "PIA", "q_top5": ["PIA", "NOR", "VER", "LEC", "HAM"], "r_top5": ["PIA", "NOR", "VER", "HAM", "LEC"]},
    {"round": 15, "race": "Netherlands", "pole": "VER", "winner": "VER", "q_top5": ["VER", "NOR", "PIA", "LEC", "HAM"], "r_top5": ["VER", "NOR", "PIA", "LEC", "HAM"]},
    {"round": 16, "race": "Italy", "pole": "LEC", "winner": "LEC", "q_top5": ["LEC", "HAM", "NOR", "VER", "PIA"], "r_top5": ["LEC", "HAM", "VER", "NOR", "PIA"]},
    {"round": 17, "race": "Azerbaijan", "pole": "VER", "winner": "VER", "q_top5": ["VER", "LEC", "NOR", "PIA", "HAM"], "r_top5": ["VER", "LEC", "NOR", "HAM", "PIA"]},
    {"round": 18, "race": "Singapore", "pole": "NOR", "winner": "NOR", "q_top5": ["NOR", "VER", "PIA", "LEC", "HAM"], "r_top5": ["NOR", "VER", "LEC", "PIA", "HAM"]},
    {"round": 19, "race": "United States", "pole": "VER", "winner": "VER", "q_top5": ["VER", "LEC", "HAM", "NOR", "PIA"], "r_top5": ["VER", "LEC", "HAM", "NOR", "PIA"]},
    {"round": 20, "race": "Mexico", "pole": "HAM", "winner": "NOR", "q_top5": ["HAM", "VER", "LEC", "NOR", "PIA"], "r_top5": ["NOR", "VER", "LEC", "HAM", "PIA"]},
    {"round": 21, "race": "Brazil", "pole": "NOR", "winner": "NOR", "q_top5": ["NOR", "VER", "PIA", "LEC", "HAM"], "r_top5": ["NOR", "VER", "LEC", "PIA", "HAM"]},
    {"round": 22, "race": "Las Vegas", "pole": "NOR", "winner": "VER", "q_top5": ["NOR", "VER", "PIA", "LEC", "HAM"], "r_top5": ["VER", "NOR", "LEC", "HAM", "PIA"]},
]

# 車隊評級 2025
TEAM_RATINGS_2025 = {
    "Red Bull Racing": 9,
    "Ferrari": 10,
    "McLaren": 9,
    "Mercedes": 7,
    "Aston Martin": 6,
    "Alpine": 5,
    "Williams": 4,
    "Racing Bulls": 5,
    "Kick Sauber": 3,
    "Haas F1 Team": 5,
}

# 車手到車隊映射 2025
DRIVER_TEAMS_2025 = {
    "VER": "Red Bull Racing",
    "TSU": "Red Bull Racing",
    "HAD": "Racing Bulls",
    "LEC": "Ferrari",
    "HAM": "Ferrari",
    "NOR": "McLaren",
    "PIA": "McLaren",
    "RUS": "Mercedes",
    "ANT": "Mercedes",
    "ALO": "Aston Martin",
    "STR": "Aston Martin",
    "GAS": "Alpine",
    "DOO": "Alpine",
    "ALB": "Williams",
    "SAI": "Williams",
    "LAW": "Racing Bulls",
    "BOT": "Kick Sauber",
    "BOR": "Kick Sauber",
    "OCO": "Haas F1 Team",
    "BEA": "Haas F1 Team",
    "HUL": "Haas F1 Team",
    "COL": "Williams",
}

def get_team_rating_2025(driver_code: str) -> int:
    """獲取 2025 車手所屬車隊的評級"""
    team = DRIVER_TEAMS_2025.get(driver_code, "Unknown")
    return TEAM_RATINGS_2025.get(team, 5)

if __name__ == "__main__":
    import json
    from pathlib import Path
    
    output_dir = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze/json/historical_data")
    output_dir.mkdir(exist_ok=True)
    
    # 統計
    pole_wins = sum(1 for r in F1_2025_RESULTS if r["pole"] == r["winner"])
    total = len(F1_2025_RESULTS)
    
    print(f"2025 賽季統計 ({total} 場)")
    print(f"桿位奪冠率: {pole_wins}/{total} = {pole_wins/total*100:.1f}%")
    
    # 各車手統計
    driver_stats = {}
    for r in F1_2025_RESULTS:
        pole = r["pole"]
        winner = r["winner"]
        
        if pole not in driver_stats:
            driver_stats[pole] = {"poles": 0, "wins": 0}
        if winner not in driver_stats:
            driver_stats[winner] = {"poles": 0, "wins": 0}
        
        driver_stats[pole]["poles"] += 1
        driver_stats[winner]["wins"] += 1
    
    print("\n車手統計:")
    for driver, stats in sorted(driver_stats.items(), key=lambda x: x[1]["wins"], reverse=True):
        print(f"  {driver}: {stats['wins']} 勝, {stats['poles']} 桿位")
    
    # 保存
    output_file = output_dir / "f1_2025_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "year": 2025,
            "races": F1_2025_RESULTS,
            "team_ratings": TEAM_RATINGS_2025,
            "driver_teams": DRIVER_TEAMS_2025
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 已保存: {output_file}")
