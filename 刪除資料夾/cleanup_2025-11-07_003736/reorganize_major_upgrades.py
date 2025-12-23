#!/usr/bin/env python3
"""
重新組織主要部件升級 JSON 結構
按照: 車隊 → 車手 → 賽事 → 升級詳情
包含變更類型自動分類功能
"""
import json
from collections import defaultdict
from datetime import datetime
from upgrade_classifier import UpgradeClassifier


class MajorUpgradeReorganizer:
    """重新組織升級數據結構"""
    
    def __init__(self, input_file="2025_f1_major_upgrades.json"):
        self.input_file = input_file
        self.organized_data = {}
        self.classifier = UpgradeClassifier()  # 初始化分類器
    
    def load_data(self):
        """載入原始數據"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['主要部件升級記錄']
    
    def reorganize_by_team_driver(self, upgrades):
        """
        重新組織結構:
        {
            "車隊名稱": {
                "車隊統計": {...},
                "車手": {
                    "車手名稱": {
                        "車手統計": {...},
                        "升級記錄": [...]
                    }
                }
            }
        }
        """
        organized = defaultdict(lambda: {
            "車隊統計": {
                "總升級次數": 0,
                "涉及賽事": set(),
                "部件類別分佈": defaultdict(int)
            },
            "車手": defaultdict(lambda: {
                "車手資訊": {},
                "車手統計": {
                    "總升級次數": 0,
                    "涉及賽事": set(),
                    "部件類別分佈": defaultdict(int)
                },
                "升級記錄": []
            })
        })
        
        # 整理數據
        for upgrade in upgrades:
            team = upgrade['車隊']
            driver = upgrade['車手']
            race = upgrade['比賽']
            category = upgrade['部件類別']
            
            # 車隊統計
            organized[team]['車隊統計']['總升級次數'] += 1
            organized[team]['車隊統計']['涉及賽事'].add(race)
            organized[team]['車隊統計']['部件類別分佈'][category] += 1
            
            # 車手統計
            driver_data = organized[team]['車手'][driver]
            driver_data['車手資訊'] = {
                "車號": upgrade['車號'],
                "車手姓名": driver,
                "所屬車隊": team
            }
            driver_data['車手統計']['總升級次數'] += 1
            driver_data['車手統計']['涉及賽事'].add(race)
            driver_data['車手統計']['部件類別分佈'][category] += 1
            
            # 升級記錄（按賽事組織）
            upgrade_record = {
                "賽事名稱": race,
                "比賽日期": upgrade['日期'],
                "更換部件": upgrade['部件'],
                "部件類別": category,
                "資料來源": {
                    "文件名稱": upgrade['來源文件'],
                    "頁碼": upgrade['頁碼']
                },
                "原始記錄": upgrade['原始文本']
            }
            
            # 🆕 添加變更類型分類
            classification = self.classifier.classify_part_change(
                upgrade['部件'], 
                upgrade['原始文本']
            )
            upgrade_record["變更類型"] = classification['變更類型']
            upgrade_record["變更類型說明"] = classification['類型說明']
            upgrade_record["分類信心度"] = classification['信心度']
            
            driver_data['升級記錄'].append(upgrade_record)
        
        # 轉換 set 為 list（JSON 序列化）
        for team_name, team_data in organized.items():
            team_data['車隊統計']['涉及賽事'] = sorted(list(team_data['車隊統計']['涉及賽事']))
            team_data['車隊統計']['部件類別分佈'] = dict(team_data['車隊統計']['部件類別分佈'])
            
            for driver_name, driver_data in team_data['車手'].items():
                driver_data['車手統計']['涉及賽事'] = sorted(list(driver_data['車手統計']['涉及賽事']))
                driver_data['車手統計']['部件類別分佈'] = dict(driver_data['車手統計']['部件類別分佈'])
                
                # 按日期排序升級記錄
                driver_data['升級記錄'].sort(key=lambda x: x['比賽日期'])
        
        return dict(organized)
    
    def generate_final_structure(self):
        """生成最終 JSON 結構"""
        upgrades = self.load_data()
        organized = self.reorganize_by_team_driver(upgrades)
        
        # 計算全局統計
        total_upgrades = sum(
            team_data['車隊統計']['總升級次數'] 
            for team_data in organized.values()
        )
        
        all_races = set()
        change_type_stats = defaultdict(int)  # 🆕 變更類型統計
        
        for team_data in organized.values():
            all_races.update(team_data['車隊統計']['涉及賽事'])
            
            # 統計各變更類型
            for driver_data in team_data['車手'].values():
                for upgrade in driver_data['升級記錄']:
                    change_type = upgrade.get('變更類型', '未分類')
                    change_type_stats[change_type] += 1
        
        # 最終結構
        final_data = {
            "metadata": {
                "資料標題": "2025 F1 主要部件升級完整記錄",
                "生成時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "數據源": "2025_f1_parts_changes_complete.json",
                "全局統計": {
                    "總升級次數": total_upgrades,
                    "涉及車隊數": len(organized),
                    "涉及賽事數": len(all_races),
                    "涉及賽事": sorted(list(all_races)),
                    "變更類型分佈": dict(change_type_stats)  # 🆕 添加變更類型統計
                }
            },
            "車隊升級記錄": {}
        }
        
        # 按車隊總升級次數排序
        sorted_teams = sorted(
            organized.items(), 
            key=lambda x: x[1]['車隊統計']['總升級次數'], 
            reverse=True
        )
        
        for team_name, team_data in sorted_teams:
            final_data['車隊升級記錄'][team_name] = team_data
        
        return final_data
    
    def save_json(self, output_file="2025_f1_major_upgrades_organized.json"):
        """儲存重組後的 JSON"""
        final_data = self.generate_final_structure()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已儲存重組後的 JSON: {output_file}")
        
        # 顯示摘要
        metadata = final_data['metadata']
        print("\n" + "="*100)
        print("📊 重組完成統計")
        print("="*100)
        print(f"總升級次數: {metadata['全局統計']['總升級次數']}")
        print(f"涉及車隊數: {metadata['全局統計']['涉及車隊數']}")
        print(f"涉及賽事數: {metadata['全局統計']['涉及賽事數']}")
        
        print("\n🏆 各車隊升級次數:")
        for team_name, team_data in final_data['車隊升級記錄'].items():
            count = team_data['車隊統計']['總升級次數']
            drivers = len(team_data['車手'])
            print(f"  {team_name:<25} {count:>3} 次 ({drivers} 位車手)")
        
        return final_data


def main():
    print("\n" + "="*100)
    print("🔄 重新組織 2025 F1 主要部件升級 JSON 結構")
    print("="*100 + "\n")
    
    reorganizer = MajorUpgradeReorganizer()
    final_data = reorganizer.save_json()
    
    # 示範輸出第一個車隊的結構
    print("\n" + "="*100)
    print("📝 JSON 結構示範（第一個車隊）")
    print("="*100)
    
    first_team = list(final_data['車隊升級記錄'].keys())[0]
    first_team_data = final_data['車隊升級記錄'][first_team]
    
    print(f"\n車隊: {first_team}")
    print(f"總升級次數: {first_team_data['車隊統計']['總升級次數']}")
    print(f"涉及賽事: {', '.join(first_team_data['車隊統計']['涉及賽事'][:5])}...")
    
    first_driver = list(first_team_data['車手'].keys())[0]
    first_driver_data = first_team_data['車手'][first_driver]
    
    print(f"\n  車手: {first_driver}")
    print(f"  車號: {first_driver_data['車手資訊']['車號']}")
    print(f"  升級次數: {first_driver_data['車手統計']['總升級次數']}")
    
    if first_driver_data['升級記錄']:
        print(f"\n  第一筆升級記錄:")
        first_upgrade = first_driver_data['升級記錄'][0]
        print(f"    賽事: {first_upgrade['賽事名稱']}")
        print(f"    日期: {first_upgrade['比賽日期']}")
        print(f"    部件: {first_upgrade['更換部件']}")
        print(f"    類別: {first_upgrade['部件類別']}")
        print(f"    來源: {first_upgrade['資料來源']['文件名稱']} (第 {first_upgrade['資料來源']['頁碼']} 頁)")
    
    print("\n" + "="*100)
    print("✅ 完成！完整數據已儲存至: 2025_f1_major_upgrades_organized.json")
    print("="*100 + "\n")


if __name__ == '__main__':
    main()
