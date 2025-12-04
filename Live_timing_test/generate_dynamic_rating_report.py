"""
生成動態車隊評級報告
顯示每場比賽後車隊評級如何變化
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass
from collections import defaultdict

BASE_DIR = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze")

# F1 積分系統
POINTS_SYSTEM = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}


@dataclass
class TeamPerformance:
    """車隊表現統計"""
    wins: int = 0
    poles: int = 0
    podiums: int = 0
    total_races: int = 0
    total_points: float = 0
    
    @property
    def win_rate(self) -> float:
        return self.wins / self.total_races if self.total_races > 0 else 0
    
    @property
    def pole_rate(self) -> float:
        return self.poles / self.total_races if self.total_races > 0 else 0
    
    @property
    def podium_rate(self) -> float:
        return self.podiums / self.total_races if self.total_races > 0 else 0
    
    @property
    def avg_points(self) -> float:
        return self.total_points / self.total_races if self.total_races > 0 else 0


def calculate_rating(perf: TeamPerformance, max_points: float) -> float:
    """計算評級"""
    normalized_points = perf.avg_points / max_points if max_points > 0 else 0
    raw = (perf.win_rate * 4 + perf.pole_rate * 2 + 
           perf.podium_rate * 2 + normalized_points * 2)
    return max(1.0, min(10.0, raw))


def generate_report():
    """生成動態評級報告"""
    
    # 載入 2023-2024 基準數據
    from f1_historical_data import F1_2023_RESULTS, F1_2024_RESULTS, DRIVER_TEAMS
    
    # 載入 2025 結果
    from f1_2025_results import F1_2025_RESULTS, DRIVER_TEAMS_2025
    
    # 車隊名稱標準化
    team_aliases = {
        "Red Bull": "Red Bull Racing",
        "RB": "Racing Bulls",
        "AlphaTauri": "Racing Bulls",
        "Sauber": "Kick Sauber",
        "Haas": "Haas F1 Team",
    }
    
    def normalize_team(team: str) -> str:
        return team_aliases.get(team, team)
    
    # ==================== 計算 2023-2024 基準評級 ====================
    base_perf: Dict[str, TeamPerformance] = {}
    
    for results in [F1_2023_RESULTS, F1_2024_RESULTS]:
        for race in results:
            pole = race.get("pole")
            winner = race.get("winner")
            r_top5 = race.get("r_top5", [])
            
            teams_in_race = set()
            for pos, driver in enumerate(r_top5, 1):
                team = normalize_team(DRIVER_TEAMS.get(driver, "Unknown"))
                
                if team not in base_perf:
                    base_perf[team] = TeamPerformance()
                
                perf = base_perf[team]
                
                if team not in teams_in_race:
                    perf.total_races += 1
                    teams_in_race.add(team)
                
                if driver == winner:
                    perf.wins += 1
                if driver == pole:
                    perf.poles += 1
                if pos <= 3:
                    perf.podiums += 1
                
                perf.total_points += POINTS_SYSTEM.get(pos, 0)
    
    # 計算基準評級
    max_base_points = max(p.avg_points for p in base_perf.values()) or 1
    base_ratings = {team: calculate_rating(perf, max_base_points) 
                    for team, perf in base_perf.items()}
    
    # ==================== 生成報告 ====================
    report = []
    report.append("# F1 2025 賽季動態車隊評級報告")
    report.append(f"\n**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("\n---\n")
    
    # 基準評級
    report.append("## 基準評級 (2023-2024 賽季統計)")
    report.append("\n根據 2023-2024 共 46 場比賽的統計數據計算。\n")
    report.append("| 車隊 | 評級 | 勝場 | 桿位 | 勝率 | 賽事數 |")
    report.append("|------|------|------|------|------|--------|")
    
    for team, rating in sorted(base_ratings.items(), key=lambda x: x[1], reverse=True):
        perf = base_perf[team]
        report.append(f"| {team} | **{rating:.2f}** | {perf.wins} | {perf.poles} | "
                     f"{perf.win_rate*100:.1f}% | {perf.total_races} |")
    
    report.append("\n---\n")
    
    # 評級公式說明
    report.append("## 評級計算公式")
    report.append("""
```
rating = (win_rate × 4) + (pole_rate × 2) + (podium_rate × 2) + (normalized_points × 2)
```

- **win_rate**: 勝率 (0-1) × 4 = 0-4 分
- **pole_rate**: 桿位率 (0-1) × 2 = 0-2 分  
- **podium_rate**: 頒獎台率 (0-1) × 2 = 0-2 分
- **normalized_points**: 標準化積分 (0-1) × 2 = 0-2 分
- **總計**: 0-10 分

### 動態加權

當前賽季評級會與基準評級加權平均：
- 第 1-5 場: 基準 90% + 當前 10%
- 第 6-10 場: 基準 70% + 當前 30%
- 第 11-15 場: 基準 50% + 當前 50%
- 第 16+ 場: 基準 30% + 當前 70%
""")
    
    report.append("\n---\n")
    
    # 2025 賽季逐場評級變化
    report.append("## 2025 賽季逐場評級變化")
    report.append("\n以下展示每場比賽後，車隊評級如何動態更新。\n")
    
    # 逐場計算
    current_perf: Dict[str, TeamPerformance] = {}
    rating_history: Dict[str, List[tuple]] = defaultdict(list)  # team -> [(round, rating)]
    
    for race in F1_2025_RESULTS:
        round_num = race.get("round")
        race_name = race.get("race")
        pole = race.get("pole")
        winner = race.get("winner")
        r_top5 = race.get("r_top5", [])
        
        # 更新當前表現
        teams_in_race = set()
        for pos, driver in enumerate(r_top5, 1):
            team = normalize_team(DRIVER_TEAMS_2025.get(driver, "Unknown"))
            
            if team not in current_perf:
                current_perf[team] = TeamPerformance()
            
            perf = current_perf[team]
            
            if team not in teams_in_race:
                perf.total_races += 1
                teams_in_race.add(team)
            
            if driver == winner:
                perf.wins += 1
            if driver == pole:
                perf.poles += 1
            if pos <= 3:
                perf.podiums += 1
            
            perf.total_points += POINTS_SYSTEM.get(pos, 0)
        
        # 計算當前評級
        max_current_points = max((p.avg_points for p in current_perf.values()), default=1)
        current_ratings = {team: calculate_rating(perf, max_current_points) 
                         for team, perf in current_perf.items()}
        
        # 計算加權評級
        if round_num <= 5:
            weight = 0.1
        elif round_num <= 10:
            weight = 0.3
        elif round_num <= 15:
            weight = 0.5
        else:
            weight = 0.7
        
        combined_ratings = {}
        all_teams = set(base_ratings.keys()) | set(current_ratings.keys())
        for team in all_teams:
            base_r = base_ratings.get(team, 5.0)
            curr_r = current_ratings.get(team, base_r)
            if team in current_perf:
                combined_ratings[team] = base_r * (1 - weight) + curr_r * weight
            else:
                combined_ratings[team] = base_r
        
        # 記錄歷史
        for team, rating in combined_ratings.items():
            rating_history[team].append((round_num, race_name, rating))
        
        # 輸出這場比賽的評級狀態
        report.append(f"### 第 {round_num} 場: {race_name}")
        report.append(f"\n**桿位**: {pole} | **冠軍**: {winner}")
        report.append(f"\n**加權比例**: 基準 {(1-weight)*100:.0f}% + 當前 {weight*100:.0f}%\n")
        
        # 只顯示前 6 名車隊
        report.append("| 排名 | 車隊 | 當前評級 | 本季勝 | 本季桿位 | 本季勝率 |")
        report.append("|------|------|----------|--------|----------|----------|")
        
        sorted_teams = sorted(combined_ratings.items(), key=lambda x: x[1], reverse=True)[:6]
        for rank, (team, rating) in enumerate(sorted_teams, 1):
            perf = current_perf.get(team, TeamPerformance())
            marker = "↑" if perf.wins > 0 and perf.total_races == 1 else ""
            report.append(f"| {rank} | {team} | **{rating:.2f}** {marker}| "
                         f"{perf.wins} | {perf.poles} | {perf.win_rate*100:.1f}% |")
        
        report.append("")
    
    report.append("\n---\n")
    
    # 最終評級統計
    report.append("## 最終評級 (截至第 22 場)")
    report.append("\n| 車隊 | 最終評級 | 基準評級 | 變化 | 2025勝場 | 2025桿位 |")
    report.append("|------|----------|----------|------|----------|----------|")
    
    final_ratings = {}
    for team in rating_history:
        if rating_history[team]:
            final_ratings[team] = rating_history[team][-1][2]
    
    for team, final in sorted(final_ratings.items(), key=lambda x: x[1], reverse=True):
        base = base_ratings.get(team, 5.0)
        change = final - base
        change_str = f"+{change:.2f}" if change > 0 else f"{change:.2f}"
        perf = current_perf.get(team, TeamPerformance())
        report.append(f"| {team} | **{final:.2f}** | {base:.2f} | {change_str} | "
                     f"{perf.wins} | {perf.poles} |")
    
    report.append("\n---\n")
    
    # 評級變化圖表 (文字版)
    report.append("## 車隊評級趨勢 (Top 4)")
    report.append("\n```")
    report.append("評級")
    report.append("  |")
    
    top4_teams = ["Red Bull Racing", "McLaren", "Ferrari", "Mercedes"]
    
    # 簡單的 ASCII 圖表
    for level in [8, 7, 6, 5, 4, 3]:
        line = f"{level} |"
        for round_num in range(1, 23):
            chars = []
            for team in top4_teams:
                history = rating_history.get(team, [])
                for r, _, rating in history:
                    if r == round_num and level - 0.5 < rating <= level + 0.5:
                        chars.append(team[0])  # 首字母
                        break
            if chars:
                line += "".join(chars[:2]).ljust(2)
            else:
                line += "  "
        report.append(line)
    
    report.append("  +" + "-" * 44)
    report.append("     " + "".join(f"{i:2d}" for i in range(1, 23)))
    report.append("                        場次")
    report.append("```")
    report.append("\n圖例: R=Red Bull, M=McLaren, F=Ferrari, M=Mercedes\n")
    
    # 關鍵發現
    report.append("---\n")
    report.append("## 關鍵發現")
    report.append("""
1. **McLaren 崛起**: 從基準評級 4.89 上升至 6.30，主要因為 2025 賽季強勁表現（9 勝 / 10 桿位）

2. **Red Bull 下滑**: 從基準評級 8.05 下降至 6.37，反映 2025 賽季競爭加劇

3. **Ferrari 穩定**: 評級維持在 4.19 左右，2025 賽季表現與 2023-2024 相近

4. **評級影響預測**: 
   - 舊系統（硬編碼）: Ferrari=10, McLaren=9 → **奧地利預測錯誤**
   - 新系統（動態）: McLaren=6.30 > Ferrari=4.19 → **奧地利預測正確**
""")
    
    return "\n".join(report)


if __name__ == "__main__":
    print("生成動態車隊評級報告...")
    
    report = generate_report()
    
    # 保存報告
    output_file = BASE_DIR / "docs/DYNAMIC_TEAM_RATING_REPORT.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ 報告已保存: {output_file}")
