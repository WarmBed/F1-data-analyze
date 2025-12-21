#!/usr/bin/env python3
"""
F1 升級套件追蹤系統
整合 FIA 技術文件，識別和追蹤各車隊的升級套件
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import PyPDF2
import re
from collections import defaultdict


class UpgradeTracker:
    """升級套件追蹤器"""
    
    # 升級關鍵字（技術文件中常見用語）
    UPGRADE_KEYWORDS = {
        'aerodynamic': ['front wing', 'rear wing', 'floor', 'diffuser', 'sidepod', 
                       'beam wing', 'bargeboard', 'nose', 'endplate'],
        'mechanical': ['suspension', 'brake duct', 'cooling', 'gearbox', 
                      'hydraulic', 'steering'],
        'power_unit': ['engine', 'mgu-k', 'mgu-h', 'turbo', 'ers', 'battery',
                      'combustion', 'hybrid'],
        'other': ['weight reduction', 'reliability update', 'stiffness', 
                 'carbon fiber', 'composite']
    }
    
    # F1 車隊代碼
    TEAMS = {
        'Red Bull Racing': 'RBR',
        'Ferrari': 'FER',
        'Mercedes': 'MER',
        'McLaren': 'MCL',
        'Aston Martin': 'AMR',
        'Alpine': 'ALP',
        'Williams': 'WIL',
        'RB': 'RB',
        'Kick Sauber': 'SAU',
        'Haas': 'HAA'
    }
    
    def __init__(self, data_dir: str = "upgrade_data"):
        """初始化追蹤器"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.upgrades_db_file = self.data_dir / "upgrades_database.json"
        self.upgrades_db = self._load_database()
    
    def _load_database(self) -> Dict:
        """載入升級資料庫"""
        if self.upgrades_db_file.exists():
            with open(self.upgrades_db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'last_updated': None,
            'upgrades': []
        }
    
    def _save_database(self):
        """儲存升級資料庫"""
        self.upgrades_db['last_updated'] = datetime.now().isoformat()
        with open(self.upgrades_db_file, 'w', encoding='utf-8') as f:
            json.dump(self.upgrades_db, f, ensure_ascii=False, indent=2)
    
    def analyze_technical_document(self, pdf_path: Path) -> List[Dict]:
        """
        分析技術文件，提取升級套件資訊
        
        Args:
            pdf_path: PDF 檔案路徑
        
        Returns:
            升級資訊列表
        """
        print(f"\n🔍 分析文件: {pdf_path.name}")
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                full_text = ""
                
                for page in pdf_reader.pages:
                    full_text += page.extract_text()
            
            # 識別升級項目
            upgrades = self._extract_upgrades(full_text, pdf_path.name)
            
            if upgrades:
                print(f"✅ 找到 {len(upgrades)} 個升級項目")
                for upgrade in upgrades:
                    print(f"  • {upgrade['team']}: {upgrade['component']} ({upgrade['category']})")
            else:
                print("  ℹ️  未發現明確的升級資訊")
            
            return upgrades
            
        except Exception as e:
            print(f"❌ 分析失敗: {e}")
            return []
    
    def _extract_upgrades(self, text: str, source: str) -> List[Dict]:
        """從文件中提取升級資訊"""
        upgrades = []
        text_lower = text.lower()
        
        # 提取分站和日期資訊
        race_match = re.search(r'(\w+)\s+grand\s+prix', text, re.IGNORECASE)
        race = race_match.group(1) if race_match else "Unknown"
        
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', text)
        date = date_match.group(0) if date_match else None
        
        # 搜尋每個車隊的升級
        for team_name, team_code in self.TEAMS.items():
            team_lower = team_name.lower()
            
            # 檢查文件中是否提到該車隊
            if team_lower not in text_lower:
                continue
            
            # 找出該車隊提到的升級部件
            for category, components in self.UPGRADE_KEYWORDS.items():
                for component in components:
                    # 搜尋模式：車隊名稱 + 升級關鍵字 + 部件名稱
                    patterns = [
                        rf'{team_lower}.*?(?:new|updated|modified|upgraded).*?{component}',
                        rf'(?:new|updated|modified|upgraded).*?{component}.*?{team_lower}',
                        rf'{component}.*?upgrade.*?{team_lower}'
                    ]
                    
                    for pattern in patterns:
                        if re.search(pattern, text_lower):
                            # 提取周圍上下文
                            context_match = re.search(
                                rf'.{{0,100}}{pattern}.{{0,100}}',
                                text_lower,
                                re.DOTALL
                            )
                            context = context_match.group(0) if context_match else ""
                            
                            upgrades.append({
                                'team': team_name,
                                'team_code': team_code,
                                'component': component,
                                'category': category,
                                'race': race,
                                'date': date,
                                'source': source,
                                'context': context.strip(),
                                'detected_at': datetime.now().isoformat()
                            })
                            break  # 避免重複
        
        return upgrades
    
    def add_manual_upgrade(self, team: str, race: str, component: str, 
                          category: str, description: str = ""):
        """
        手動新增升級記錄
        
        Args:
            team: 車隊名稱
            race: 分站名稱
            component: 部件名稱
            category: 類別
            description: 描述
        """
        upgrade = {
            'team': team,
            'team_code': self.TEAMS.get(team, 'UNK'),
            'component': component,
            'category': category,
            'race': race,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'source': 'manual_entry',
            'description': description,
            'added_at': datetime.now().isoformat()
        }
        
        self.upgrades_db['upgrades'].append(upgrade)
        self._save_database()
        
        print(f"✅ 已新增升級記錄: {team} - {component} ({race})")
    
    def get_team_upgrades(self, team: str, year: Optional[int] = None) -> List[Dict]:
        """
        獲取特定車隊的升級歷史
        
        Args:
            team: 車隊名稱
            year: 年份（可選）
        
        Returns:
            升級記錄列表
        """
        upgrades = [u for u in self.upgrades_db['upgrades'] if u['team'] == team]
        
        if year:
            upgrades = [u for u in upgrades if str(year) in u.get('date', '')]
        
        return upgrades
    
    def get_race_upgrades(self, race: str) -> Dict[str, List[Dict]]:
        """
        獲取特定分站所有車隊的升級
        
        Args:
            race: 分站名稱
        
        Returns:
            按車隊分組的升級記錄
        """
        race_upgrades = defaultdict(list)
        
        for upgrade in self.upgrades_db['upgrades']:
            if upgrade['race'].lower() == race.lower():
                race_upgrades[upgrade['team']].append(upgrade)
        
        return dict(race_upgrades)
    
    def generate_upgrade_timeline(self, year: int = 2025) -> Dict:
        """
        生成年度升級時間線
        
        Args:
            year: 年份
        
        Returns:
            時間線資料
        """
        timeline = defaultdict(lambda: defaultdict(list))
        
        for upgrade in self.upgrades_db['upgrades']:
            if str(year) in upgrade.get('date', ''):
                race = upgrade['race']
                team = upgrade['team']
                timeline[race][team].append({
                    'component': upgrade['component'],
                    'category': upgrade['category'],
                    'date': upgrade.get('date')
                })
        
        return dict(timeline)
    
    def export_to_json(self, output_file: str = "upgrades_export.json"):
        """匯出升級資料"""
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_upgrades': len(self.upgrades_db['upgrades']),
            'by_team': {},
            'by_race': {},
            'by_category': {},
            'timeline': self.generate_upgrade_timeline(),
            'all_upgrades': self.upgrades_db['upgrades']
        }
        
        # 統計資料
        for upgrade in self.upgrades_db['upgrades']:
            team = upgrade['team']
            race = upgrade['race']
            category = upgrade['category']
            
            export_data['by_team'][team] = export_data['by_team'].get(team, 0) + 1
            export_data['by_race'][race] = export_data['by_race'].get(race, 0) + 1
            export_data['by_category'][category] = export_data['by_category'].get(category, 0) + 1
        
        output_path = self.data_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 資料已匯出: {output_path}")
        return export_data
    
    def print_summary(self):
        """列印摘要報告"""
        print("\n" + "="*70)
        print("📊 F1 升級套件追蹤摘要")
        print("="*70)
        print(f"總升級數量: {len(self.upgrades_db['upgrades'])}")
        print(f"最後更新: {self.upgrades_db.get('last_updated', 'Never')}")
        
        # 按車隊統計
        by_team = defaultdict(int)
        by_category = defaultdict(int)
        
        for upgrade in self.upgrades_db['upgrades']:
            by_team[upgrade['team']] += 1
            by_category[upgrade['category']] += 1
        
        print("\n📋 按車隊統計:")
        for team, count in sorted(by_team.items(), key=lambda x: x[1], reverse=True):
            print(f"  {team:20s}: {count:2d} 個升級")
        
        print("\n🔧 按類別統計:")
        for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category:15s}: {count:2d} 個升級")
        
        print("="*70 + "\n")


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='F1 升級套件追蹤系統')
    parser.add_argument('-a', '--analyze', type=str, help='分析 PDF 文件路徑')
    parser.add_argument('-t', '--team', type=str, help='查詢車隊升級')
    parser.add_argument('-r', '--race', type=str, help='查詢分站升級')
    parser.add_argument('-s', '--summary', action='store_true', help='顯示摘要')
    parser.add_argument('-e', '--export', action='store_true', help='匯出 JSON')
    parser.add_argument('--add', nargs=5, metavar=('TEAM', 'RACE', 'COMPONENT', 'CATEGORY', 'DESC'),
                       help='手動新增升級記錄')
    
    args = parser.parse_args()
    
    tracker = UpgradeTracker()
    
    if args.analyze:
        # 分析 PDF 文件
        pdf_path = Path(args.analyze)
        if pdf_path.exists():
            upgrades = tracker.analyze_technical_document(pdf_path)
            
            # 將找到的升級加入資料庫
            if upgrades:
                confirm = input(f"\n將 {len(upgrades)} 個升級加入資料庫？ (y/n): ")
                if confirm.lower() == 'y':
                    tracker.upgrades_db['upgrades'].extend(upgrades)
                    tracker._save_database()
                    print("✅ 已儲存至資料庫")
        else:
            print(f"❌ 找不到檔案: {pdf_path}")
    
    elif args.team:
        # 查詢車隊升級
        upgrades = tracker.get_team_upgrades(args.team)
        print(f"\n🏎️  {args.team} 的升級記錄 ({len(upgrades)} 項):")
        for upgrade in upgrades:
            print(f"  • {upgrade['race']:15s} - {upgrade['component']:20s} ({upgrade['category']})")
    
    elif args.race:
        # 查詢分站升級
        upgrades = tracker.get_race_upgrades(args.race)
        print(f"\n🏁 {args.race} 的升級記錄:")
        for team, team_upgrades in upgrades.items():
            print(f"\n  {team}:")
            for upgrade in team_upgrades:
                print(f"    • {upgrade['component']} ({upgrade['category']})")
    
    elif args.add:
        # 手動新增
        team, race, component, category, desc = args.add
        tracker.add_manual_upgrade(team, race, component, category, desc)
    
    elif args.export:
        # 匯出資料
        tracker.export_to_json()
    
    elif args.summary or not any([args.analyze, args.team, args.race, args.add, args.export]):
        # 顯示摘要
        tracker.print_summary()


if __name__ == '__main__':
    main()
