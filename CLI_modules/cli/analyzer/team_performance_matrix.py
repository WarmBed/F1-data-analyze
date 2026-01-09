"""
F137: 車隊性能差係數計算器

計算車隊間的相對性能差異係數，用於位置追蹤模擬器的超車成功率模型。

處理邏輯:
  1. 從 F134 (成功超車) 和 F135 (失敗嘗試) 提取車隊對戰數據
  2. 計算車隊間的超車成功率矩陣
  3. 計算車隊性能層級 (tier)
  
輸出: team_performance_matrix.json
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict
from datetime import datetime


class TeamPerformanceMatrixAnalyzer:
    """車隊性能矩陣分析器"""
    
    # 2024-2025 賽季的車隊列表
    TEAMS = [
        'Red Bull Racing',
        'Ferrari',
        'McLaren',
        'Mercedes',
        'Aston Martin',
        'Alpine',
        'Williams',
        'RB',
        'Kick Sauber',
        'Haas F1 Team'
    ]
    
    def __init__(self):
        self.json_dir = Path("json")
        self.output_path = self.json_dir / "team_performance_matrix.json"
        
    def analyze(self) -> Dict[str, Any]:
        """執行車隊性能分析"""
        print("\n" + "="*60)
        print("F137: Team Performance Matrix Analyzer")
        print("="*60)
        
        # 讀取成功超車數據 (F134)
        success_data = self._load_json("overtake_events_history_2024_2025.json")
        if not success_data:
            print("[F137] Error: Cannot load F134 data")
            return {}
            
        # 讀取失敗嘗試數據 (F135)
        failed_data = self._load_json("overtake_attempts_failed_2024_2025.json")
        if not failed_data:
            print("[F137] Error: Cannot load F135 data")
            return {}
            
        # 收集車隊對戰統計
        battle_stats = self._collect_battle_stats(success_data, failed_data)
        
        # 計算超車成功率矩陣
        success_matrix = self._calculate_success_matrix(battle_stats)
        
        # 計算車隊層級
        team_tier = self._calculate_team_tier(battle_stats)
        
        # 計算車隊整體統計
        team_stats = self._calculate_team_stats(battle_stats)
        
        # 組建結果
        result = {
            'metadata': {
                'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'data_source': {
                    'success_events': 'overtake_events_history_2024_2025.json (F134)',
                    'failed_events': 'overtake_attempts_failed_2024_2025.json (F135)'
                },
                'teams': list(team_stats.keys()),
                'total_battles': sum(v['total_attacks'] for v in team_stats.values())
            },
            'overtake_success_matrix': success_matrix,
            'team_tier': team_tier,
            'team_stats': team_stats,
            'battle_counts': self._get_battle_counts(battle_stats)
        }
        
        # 保存結果
        self._save_result(result)
        
        return result
        
    def _load_json(self, filename: str) -> Dict:
        """讀取 JSON 檔案"""
        filepath = self.json_dir / filename
        if not filepath.exists():
            print(f"[F137] File not found: {filepath}")
            return {}
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[F137] Error loading {filename}: {e}")
            return {}
            
    def _collect_battle_stats(
        self, 
        success_data: Dict, 
        failed_data: Dict
    ) -> Dict[Tuple[str, str], Dict]:
        """收集車隊對戰統計 (攻擊方, 防守方) -> 統計"""
        battle_stats = defaultdict(lambda: {
            'success': 0,
            'failed': 0,
            'events': []
        })
        
        # 處理成功超車事件 (F134 結構: attacker.team, defender.team)
        for event in success_data.get('events', []):
            # F134 使用嵌套結構
            attacker_data = event.get('attacker', {})
            defender_data = event.get('defender', {})
            
            attacker_team = attacker_data.get('team', '') if isinstance(attacker_data, dict) else ''
            defender_team = defender_data.get('team', '') if isinstance(defender_data, dict) else ''
            
            if not attacker_team or not defender_team:
                continue
            if attacker_team == defender_team:
                continue  # 排除隊內超車
                
            key = (attacker_team, defender_team)
            battle_stats[key]['success'] += 1
            
        # 處理失敗嘗試事件
        for event in failed_data.get('events', []):
            attacker_team = event.get('attacker_team', '')
            defender_team = event.get('defender_team', '')
            
            if not attacker_team or not defender_team:
                continue
            if attacker_team == defender_team:
                continue
                
            key = (attacker_team, defender_team)
            battle_stats[key]['failed'] += 1
            
        return dict(battle_stats)
        
    def _calculate_success_matrix(
        self, 
        battle_stats: Dict[Tuple[str, str], Dict]
    ) -> Dict[str, Dict[str, float]]:
        """計算車隊對車隊的超車成功率矩陣"""
        matrix = {}
        
        # 獲取所有出現過的車隊
        all_teams = set()
        for (attacker, defender) in battle_stats.keys():
            all_teams.add(attacker)
            all_teams.add(defender)
            
        for attacker in sorted(all_teams):
            matrix[attacker] = {}
            for defender in sorted(all_teams):
                if attacker == defender:
                    matrix[attacker][defender] = None  # 隊內不適用
                    continue
                    
                key = (attacker, defender)
                stats = battle_stats.get(key, {'success': 0, 'failed': 0})
                total = stats['success'] + stats['failed']
                
                if total > 0:
                    success_rate = stats['success'] / total
                    matrix[attacker][defender] = round(success_rate, 4)
                else:
                    matrix[attacker][defender] = None  # 無數據
                    
        return matrix
        
    def _calculate_team_tier(
        self, 
        battle_stats: Dict[Tuple[str, str], Dict]
    ) -> Dict[str, int]:
        """計算車隊層級 (1-4)"""
        team_scores = defaultdict(lambda: {'wins': 0, 'total': 0})
        
        for (attacker, defender), stats in battle_stats.items():
            # 攻擊方成功 = 攻擊方得分
            team_scores[attacker]['wins'] += stats['success']
            team_scores[attacker]['total'] += stats['success'] + stats['failed']
            
            # 防守方成功 = 防守方得分 (對方失敗)
            team_scores[defender]['wins'] += stats['failed']
            team_scores[defender]['total'] += stats['success'] + stats['failed']
            
        # 計算綜合勝率
        team_win_rates = {}
        for team, scores in team_scores.items():
            if scores['total'] > 0:
                team_win_rates[team] = scores['wins'] / scores['total']
            else:
                team_win_rates[team] = 0.5
                
        # 按勝率排序並分配層級
        sorted_teams = sorted(team_win_rates.items(), key=lambda x: x[1], reverse=True)
        
        tiers = {}
        for i, (team, win_rate) in enumerate(sorted_teams):
            if i < 3:
                tiers[team] = 1  # Top 3 = Tier 1
            elif i < 6:
                tiers[team] = 2  # 4-6 = Tier 2
            elif i < 8:
                tiers[team] = 3  # 7-8 = Tier 3
            else:
                tiers[team] = 4  # 9-10 = Tier 4
                
        return tiers
        
    def _calculate_team_stats(
        self, 
        battle_stats: Dict[Tuple[str, str], Dict]
    ) -> Dict[str, Dict]:
        """計算每個車隊的整體統計"""
        team_stats = defaultdict(lambda: {
            'total_attacks': 0,
            'successful_attacks': 0,
            'total_defenses': 0,
            'successful_defenses': 0
        })
        
        for (attacker, defender), stats in battle_stats.items():
            # 攻擊統計
            team_stats[attacker]['total_attacks'] += stats['success'] + stats['failed']
            team_stats[attacker]['successful_attacks'] += stats['success']
            
            # 防守統計
            team_stats[defender]['total_defenses'] += stats['success'] + stats['failed']
            team_stats[defender]['successful_defenses'] += stats['failed']  # 對方失敗 = 成功防守
            
        # 計算成功率
        for team, data in team_stats.items():
            if data['total_attacks'] > 0:
                data['attack_success_rate'] = round(
                    data['successful_attacks'] / data['total_attacks'], 4
                )
            else:
                data['attack_success_rate'] = 0.0
                
            if data['total_defenses'] > 0:
                data['defense_success_rate'] = round(
                    data['successful_defenses'] / data['total_defenses'], 4
                )
            else:
                data['defense_success_rate'] = 0.0
                
        return dict(team_stats)
        
    def _get_battle_counts(
        self, 
        battle_stats: Dict[Tuple[str, str], Dict]
    ) -> Dict[str, Dict[str, int]]:
        """獲取對戰次數矩陣"""
        all_teams = set()
        for (attacker, defender) in battle_stats.keys():
            all_teams.add(attacker)
            all_teams.add(defender)
            
        counts = {}
        for attacker in sorted(all_teams):
            counts[attacker] = {}
            for defender in sorted(all_teams):
                if attacker == defender:
                    counts[attacker][defender] = 0
                    continue
                    
                key = (attacker, defender)
                stats = battle_stats.get(key, {'success': 0, 'failed': 0})
                counts[attacker][defender] = stats['success'] + stats['failed']
                
        return counts
        
    def _save_result(self, result: Dict):
        """保存結果到 JSON"""
        self.json_dir.mkdir(exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print(f"\n[F137] Results saved to: {self.output_path}")
        print(f"  - Teams analyzed: {len(result.get('team_stats', {}))}")
        
        # 顯示摘要
        print("\n[F137] Team Stats Summary:")
        print("-" * 80)
        print(f"{'Team':<20} {'Attack%':>10} {'Defense%':>10} {'Attacks':>10} {'Tier':>6}")
        print("-" * 80)
        
        team_stats = result.get('team_stats', {})
        team_tier = result.get('team_tier', {})
        
        # 按攻擊成功率排序
        sorted_teams = sorted(
            team_stats.items(), 
            key=lambda x: x[1].get('attack_success_rate', 0), 
            reverse=True
        )
        
        for team, data in sorted_teams[:10]:
            tier = team_tier.get(team, '-')
            print(f"{team:<20} {data['attack_success_rate']*100:>9.1f}% {data['defense_success_rate']*100:>9.1f}% {data['total_attacks']:>10} {tier:>6}")


def execute_team_performance_matrix(
    year: int = None,
    race: str = None,
    session: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    執行車隊性能矩陣分析器
    
    這是 CLI 模組的入口點
    """
    analyzer = TeamPerformanceMatrixAnalyzer()
    return analyzer.analyze()


# 直接執行測試
if __name__ == "__main__":
    result = execute_team_performance_matrix()
    print(f"\nAnalysis complete. Teams analyzed: {len(result.get('team_stats', {}))}")
