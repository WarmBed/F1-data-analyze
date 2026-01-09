"""
F139: 新車手係數補全器 (Driver Coefficient Completer)

目標: 
1. 整合 F134 成功超車 + F135 失敗嘗試，計算真正的成功率
2. 為缺乏歷史數據的新車手/替補車手生成預設係數
3. 識別數據不足的車手 (少於 10 次超車嘗試)
4. 使用該車手所屬車隊的平均值作為回退
5. 如果是完全新車手，使用全場平均值

輸出: driver_coefficients_complete.json
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class DriverCoefficientCompleter:
    """
    整合 F134 + F135 數據，為所有車手生成完整係數
    """
    
    # 最小樣本數閾值
    MIN_SAMPLE_SIZE = 10
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent.parent
        self.json_dir = self.base_dir / "json"
        
        # 數據容器
        self.success_events_path = self.json_dir / "overtake_events_history_2024_2025.json"
        self.failed_events_path = self.json_dir / "overtake_attempts_failed_2024_2025.json"
        self.team_matrix_path = self.json_dir / "team_performance_matrix.json"
        
        # 結果
        self.driver_coefficients: Dict[str, Any] = {}
        self.global_stats = {
            "avg_attack_success_rate": 0.0,
            "avg_defense_success_rate": 0.0,
            "total_attempts": 0
        }
        
    def run(self) -> bool:
        """執行係數補全流程"""
        print("=" * 60)
        print("F139: 車手係數補全器")
        print("=" * 60)
        
        # Step 1: 載入數據
        success_data = self._load_json(self.success_events_path)
        failed_data = self._load_json(self.failed_events_path)
        team_matrix = self._load_json(self.team_matrix_path)
        
        if not success_data or not failed_data:
            print("[ERROR] 無法載入必要數據檔案")
            return False
            
        # Step 2: 整合車手統計
        combined_stats = self._combine_driver_stats(success_data, failed_data)
        print(f"\n[INFO] 整合完成: {len(combined_stats)} 位車手")
        
        # Step 3: 計算全場平均
        self._calculate_global_averages(combined_stats)
        print(f"[INFO] 全場平均攻擊成功率: {self.global_stats['avg_attack_success_rate']:.2%}")
        print(f"[INFO] 全場平均防守成功率: {self.global_stats['avg_defense_success_rate']:.2%}")
        
        # Step 4: 建立車隊平均 (從 team_matrix 或計算)
        team_averages = self._get_team_averages(combined_stats, team_matrix)
        
        # Step 5: 為每位車手生成係數
        self._generate_coefficients(combined_stats, team_averages)
        
        # Step 6: 輸出結果
        self._save_results()
        
        return True
        
    def _load_json(self, path: Path) -> Optional[Dict]:
        """載入 JSON 檔案"""
        if not path.exists():
            print(f"[WARN] 檔案不存在: {path}")
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] 載入失敗 {path}: {e}")
            return None
            
    def _combine_driver_stats(self, success_data: Dict, failed_data: Dict) -> Dict[str, Dict]:
        """
        整合 F134 成功數據 + F135 失敗數據
        
        F134 driver_stats: {driver: {total_attacks, successful_attacks, team, ...}}
        F135: {attacker_failed_stats: {driver: count}, defender_held_stats: {driver: count}}
        """
        combined = {}
        
        # 從 F134 獲取基礎統計
        f134_stats = success_data.get("driver_stats", {})
        
        # 從 F135 獲取失敗統計
        attacker_failed = failed_data.get("attacker_failed_stats", {})
        defender_held = failed_data.get("defender_held_stats", {})
        
        # 收集所有車手
        all_drivers = set(f134_stats.keys()) | set(attacker_failed.keys()) | set(defender_held.keys())
        
        for driver in all_drivers:
            # F134 數據 (成功)
            f134 = f134_stats.get(driver, {})
            successful_attacks = f134.get("successful_attacks", 0)
            successful_defenses = f134.get("successful_defenses", 0)  # F134 中防守成功 = 0 (因為每次成功超車，防守方都失敗)
            team = f134.get("team", "Unknown")
            
            # F135 數據 (失敗)
            failed_attacks = attacker_failed.get(driver, 0)
            held_defenses = defender_held.get(driver, 0)  # 成功防守 = 對方超車失敗
            
            # 計算真正的統計
            total_attacks = successful_attacks + failed_attacks
            total_defenses = f134.get("total_defenses", 0) + held_defenses
            
            # 真正的成功率
            attack_success_rate = successful_attacks / total_attacks if total_attacks > 0 else 0.0
            defense_success_rate = held_defenses / total_defenses if total_defenses > 0 else 0.0
            
            combined[driver] = {
                "team": team,
                "total_attacks": total_attacks,
                "successful_attacks": successful_attacks,
                "failed_attacks": failed_attacks,
                "attack_success_rate": attack_success_rate,
                "total_defenses": total_defenses,
                "successful_defenses": held_defenses,
                "defense_success_rate": defense_success_rate
            }
            
        return combined
        
    def _calculate_global_averages(self, combined_stats: Dict[str, Dict]) -> None:
        """計算全場平均成功率"""
        total_attacks = 0
        total_successful_attacks = 0
        total_defenses = 0
        total_successful_defenses = 0
        
        for driver, stats in combined_stats.items():
            total_attacks += stats["total_attacks"]
            total_successful_attacks += stats["successful_attacks"]
            total_defenses += stats["total_defenses"]
            total_successful_defenses += stats["successful_defenses"]
            
        self.global_stats = {
            "avg_attack_success_rate": total_successful_attacks / total_attacks if total_attacks > 0 else 0.0,
            "avg_defense_success_rate": total_successful_defenses / total_defenses if total_defenses > 0 else 0.0,
            "total_attempts": total_attacks,
            "total_defenses": total_defenses
        }
        
    def _get_team_averages(self, combined_stats: Dict[str, Dict], team_matrix: Optional[Dict]) -> Dict[str, Dict]:
        """
        獲取車隊平均值
        優先使用 team_matrix (F137)，否則從 combined_stats 計算
        """
        team_avgs = {}
        
        if team_matrix:
            # 使用 F137 的 team_stats (包含 attack_success_rate, defense_success_rate)
            team_stats = team_matrix.get("team_stats", {})
            
            for team, stats in team_stats.items():
                team_avgs[team] = {
                    "attack_success_rate": stats.get("attack_success_rate", self.global_stats["avg_attack_success_rate"]),
                    "defense_success_rate": stats.get("defense_success_rate", self.global_stats["avg_defense_success_rate"])
                }
                
            print(f"[INFO] 從 F137 team_matrix 載入 {len(team_avgs)} 個車隊平均值")
        else:
            # 從 combined_stats 計算
            team_stats = {}
            for driver, stats in combined_stats.items():
                team = stats["team"]
                if team not in team_stats:
                    team_stats[team] = {
                        "total_attacks": 0, "successful_attacks": 0,
                        "total_defenses": 0, "successful_defenses": 0
                    }
                team_stats[team]["total_attacks"] += stats["total_attacks"]
                team_stats[team]["successful_attacks"] += stats["successful_attacks"]
                team_stats[team]["total_defenses"] += stats["total_defenses"]
                team_stats[team]["successful_defenses"] += stats["successful_defenses"]
                
            for team, ts in team_stats.items():
                team_avgs[team] = {
                    "attack_success_rate": ts["successful_attacks"] / ts["total_attacks"] if ts["total_attacks"] > 0 else self.global_stats["avg_attack_success_rate"],
                    "defense_success_rate": ts["successful_defenses"] / ts["total_defenses"] if ts["total_defenses"] > 0 else self.global_stats["avg_defense_success_rate"]
                }
                
            print(f"[INFO] 從 combined_stats 計算 {len(team_avgs)} 個車隊平均值")
            
        return team_avgs
        
    def _generate_coefficients(self, combined_stats: Dict[str, Dict], team_averages: Dict[str, Dict]) -> None:
        """
        為每位車手生成係數
        
        係數定義:
        - attack_coefficient = driver_attack_rate / global_attack_rate
        - defense_coefficient = driver_defense_rate / global_defense_rate
        
        數據來源分類:
        - "historical": 樣本數 >= MIN_SAMPLE_SIZE
        - "team_average": 樣本數 < MIN_SAMPLE_SIZE，使用車隊平均
        - "global_average": 沒有車隊數據，使用全場平均
        """
        global_attack = self.global_stats["avg_attack_success_rate"]
        global_defense = self.global_stats["avg_defense_success_rate"]
        
        print(f"\n[INFO] 生成車手係數 (最小樣本數: {self.MIN_SAMPLE_SIZE})")
        print("-" * 60)
        
        historical_count = 0
        team_avg_count = 0
        global_avg_count = 0
        
        for driver, stats in combined_stats.items():
            sample_size = stats["total_attacks"] + stats["total_defenses"]
            team = stats["team"]
            
            if sample_size >= self.MIN_SAMPLE_SIZE:
                # 足夠樣本，使用歷史數據
                attack_rate = stats["attack_success_rate"]
                defense_rate = stats["defense_success_rate"]
                data_source = "historical"
                fallback_team = None
                historical_count += 1
            elif team in team_averages:
                # 樣本不足，使用車隊平均
                attack_rate = team_averages[team]["attack_success_rate"]
                defense_rate = team_averages[team]["defense_success_rate"]
                data_source = "team_average"
                fallback_team = team
                team_avg_count += 1
            else:
                # 沒有車隊數據，使用全場平均
                attack_rate = global_attack
                defense_rate = global_defense
                data_source = "global_average"
                fallback_team = None
                global_avg_count += 1
                
            # 計算係數 (相對於全場平均的倍率)
            attack_coefficient = attack_rate / global_attack if global_attack > 0 else 1.0
            defense_coefficient = defense_rate / global_defense if global_defense > 0 else 1.0
            
            self.driver_coefficients[driver] = {
                "team": team,
                "data_source": data_source,
                "sample_size": sample_size,
                "attack_success_rate": round(attack_rate, 4),
                "defense_success_rate": round(defense_rate, 4),
                "attack_coefficient": round(attack_coefficient, 4),
                "defense_coefficient": round(defense_coefficient, 4)
            }
            
            if fallback_team:
                self.driver_coefficients[driver]["fallback_team"] = fallback_team
                
        print(f"[INFO] 歷史數據: {historical_count} 位")
        print(f"[INFO] 車隊平均: {team_avg_count} 位")
        print(f"[INFO] 全場平均: {global_avg_count} 位")
        
    def _save_results(self) -> None:
        """儲存結果到 JSON"""
        output_path = self.json_dir / "driver_coefficients_complete.json"
        
        result = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "min_sample_size": self.MIN_SAMPLE_SIZE,
                "total_drivers": len(self.driver_coefficients),
                "data_sources": {
                    "overtake_success": str(self.success_events_path.name),
                    "overtake_failed": str(self.failed_events_path.name)
                }
            },
            "global_stats": {
                "avg_attack_success_rate": round(self.global_stats["avg_attack_success_rate"], 4),
                "avg_defense_success_rate": round(self.global_stats["avg_defense_success_rate"], 4),
                "total_attempts": self.global_stats["total_attempts"],
                "total_defenses": self.global_stats.get("total_defenses", 0)
            },
            "drivers": self.driver_coefficients
        }
        
        # 排序：按 attack_coefficient 降序
        sorted_drivers = dict(sorted(
            self.driver_coefficients.items(),
            key=lambda x: x[1]["attack_coefficient"],
            reverse=True
        ))
        result["drivers"] = sorted_drivers
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print(f"\n[SUCCESS] 已儲存: {output_path}")
        
        # 顯示 Top 5 攻擊者和 Top 5 防守者
        print("\n=== Top 5 攻擊係數 ===")
        for i, (driver, coef) in enumerate(sorted_drivers.items()):
            if i >= 5:
                break
            print(f"  {driver}: {coef['attack_coefficient']:.2f} ({coef['data_source']}, {coef['sample_size']} samples)")
            
        print("\n=== Top 5 防守係數 ===")
        sorted_by_defense = sorted(
            self.driver_coefficients.items(),
            key=lambda x: x[1]["defense_coefficient"],
            reverse=True
        )
        for i, (driver, coef) in enumerate(sorted_by_defense):
            if i >= 5:
                break
            print(f"  {driver}: {coef['defense_coefficient']:.2f} ({coef['data_source']}, {coef['sample_size']} samples)")


def main():
    completer = DriverCoefficientCompleter()
    success = completer.run()
    
    if success:
        print("\n" + "=" * 60)
        print("F139 完成!")
        print("=" * 60)
    else:
        print("\n[ERROR] F139 執行失敗")
        

if __name__ == "__main__":
    main()
