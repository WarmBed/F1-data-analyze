#!/usr/bin/env python3
"""
按年份重新組織主要部件升級 JSON 結構
按照: 年份 → 車隊 → 車手 → 賽事 → 升級詳情
包含變更類型自動分類功能
"""
import json
from collections import defaultdict
from datetime import datetime
from upgrade_classifier import UpgradeClassifier


class MajorUpgradeReorganizerByYear:
    """按年份重新組織升級數據結構"""
    
    def __init__(self, year):
        self.year = year
        self.input_file = f"{year}_f1_major_upgrades.json"
        self.output_file = f"{year}_f1_major_upgrades_organized.json"
        self.organized_data = {}
        self.classifier = UpgradeClassifier()  # 初始化分類器
    
    def load_data(self):
        """載入原始數據"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('主要升級記錄', data.get('主要部件升級記錄', []))
    
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
                "部件類別分佈": defaultdict(int),
                "變更類型分佈": defaultdict(int)  # 新增：變更類型統計
            },
            "車手": defaultdict(lambda: {
                "車手資訊": {},
                "車手統計": {
                    "總升級次數": 0,
                    "涉及賽事": set(),
                    "部件類別分佈": defaultdict(int),
                    "變更類型分佈": defaultdict(int)  # 新增：變更類型統計
                },
                "升級記錄": []
            })
        })
        
        # 遍歷所有升級記錄
        for upgrade in upgrades:
            team = upgrade['車隊']
            driver = upgrade['車手']
            
            # 對部件變更進行分類
            classification = self.classifier.classify_part_change(upgrade['更換部件'])
            
            # 創建升級記錄（包含分類資訊）
            upgrade_record = {
                "賽事名稱": upgrade['賽事名稱'],
                "更換部件": upgrade['更換部件'],
                "部件類別": upgrade['部件類別'],
                "變更類型": classification['變更類型'],  # 新增：變更類型
                "變更類型說明": classification['變更類型說明'],  # 新增：類型說明
                "分類信心度": classification['信心度'],  # 新增：分類信心度
                "資料來源": {
                    "文件名稱": upgrade['資料來源'],
                    "頁碼": upgrade['頁碼']
                }
            }
            
            # 更新車手資訊
            if not organized[team]["車手"][driver]["車手資訊"]:
                organized[team]["車手"][driver]["車手資訊"] = {
                    "車號": upgrade['車號'],
                    "車隊": team
                }
            
            # 添加升級記錄
            organized[team]["車手"][driver]["升級記錄"].append(upgrade_record)
            
            # 更新車手統計
            driver_stats = organized[team]["車手"][driver]["車手統計"]
            driver_stats["總升級次數"] += 1
            driver_stats["涉及賽事"].add(upgrade['賽事名稱'])
            driver_stats["部件類別分佈"][upgrade['部件類別']] += 1
            driver_stats["變更類型分佈"][classification['變更類型']] += 1  # 新增：統計變更類型
            
            # 更新車隊統計
            team_stats = organized[team]["車隊統計"]
            team_stats["總升級次數"] += 1
            team_stats["涉及賽事"].add(upgrade['賽事名稱'])
            team_stats["部件類別分佈"][upgrade['部件類別']] += 1
            team_stats["變更類型分佈"][classification['變更類型']] += 1  # 新增：統計變更類型
        
        return organized
    
    def convert_sets_to_lists(self, obj):
        """將 set 轉換為 list（用於 JSON 序列化）"""
        if isinstance(obj, dict):
            return {k: self.convert_sets_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, (set, frozenset)):
            return sorted(list(obj))
        elif isinstance(obj, list):
            return [self.convert_sets_to_lists(item) for item in obj]
        else:
            return obj
    
    def finalize_statistics(self, organized):
        """最終化統計數據（將集合轉為列表，計算百分比等）"""
        finalized = {}
        
        for team, team_data in organized.items():
            finalized[team] = {
                "車隊統計": {
                    "總升級次數": team_data["車隊統計"]["總升級次數"],
                    "涉及賽事數量": len(team_data["車隊統計"]["涉及賽事"]),
                    "涉及賽事列表": sorted(team_data["車隊統計"]["涉及賽事"]),
                    "部件類別分佈": dict(team_data["車隊統計"]["部件類別分佈"]),
                    "變更類型分佈": dict(team_data["車隊統計"]["變更類型分佈"])  # 新增
                },
                "車手": {}
            }
            
            for driver, driver_data in team_data["車手"].items():
                finalized[team]["車手"][driver] = {
                    "車手資訊": driver_data["車手資訊"],
                    "車手統計": {
                        "總升級次數": driver_data["車手統計"]["總升級次數"],
                        "涉及賽事數量": len(driver_data["車手統計"]["涉及賽事"]),
                        "涉及賽事列表": sorted(driver_data["車手統計"]["涉及賽事"]),
                        "部件類別分佈": dict(driver_data["車手統計"]["部件類別分佈"]),
                        "變更類型分佈": dict(driver_data["車手統計"]["變更類型分佈"])  # 新增
                    },
                    "升級記錄": driver_data["升級記錄"]
                }
        
        return finalized
    
    def generate_global_statistics(self, organized):
        """生成全局統計"""
        total_upgrades = sum(team["車隊統計"]["總升級次數"] for team in organized.values())
        
        all_races = set()
        all_categories = defaultdict(int)
        all_change_types = defaultdict(int)  # 新增：全局變更類型統計
        
        for team_data in organized.values():
            all_races.update(team_data["車隊統計"]["涉及賽事列表"])
            for category, count in team_data["車隊統計"]["部件類別分佈"].items():
                all_categories[category] += count
            for change_type, count in team_data["車隊統計"]["變更類型分佈"].items():
                all_change_types[change_type] += count
        
        return {
            "年份": self.year,
            "生成時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "全局統計": {
                "總升級次數": total_upgrades,
                "涉及車隊數": len(organized),
                "涉及賽事數": len(all_races),
                "涉及賽事列表": sorted(all_races),
                "部件類別分佈": dict(all_categories),
                "變更類型分佈": dict(all_change_types)  # 新增：全局變更類型統計
            }
        }
    
    def reorganize_and_export(self):
        """主執行流程：重組並導出"""
        print(f"\n🔄 開始重組 {self.year} 年主要升級數據...")
        
        # 載入數據
        upgrades = self.load_data()
        print(f"📊 載入 {len(upgrades)} 筆升級記錄")
        
        # 重組數據
        print(f"🔧 重組數據結構...")
        organized = self.reorganize_by_team_driver(upgrades)
        
        # 最終化統計
        print(f"📈 計算統計數據...")
        finalized = self.finalize_statistics(organized)
        
        # 生成全局統計
        metadata = self.generate_global_statistics(finalized)
        
        # 準備輸出
        output = {
            "metadata": metadata,
            "車隊升級記錄": finalized
        }
        
        # 導出 JSON
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 重組完成！")
        print(f"💾 已保存至: {self.output_file}")
        
        # 顯示摘要
        print(f"\n📊 {self.year} 年摘要:")
        print(f"  總升級次數: {metadata['全局統計']['總升級次數']}")
        print(f"  涉及車隊: {metadata['全局統計']['涉及車隊數']} 隊")
        print(f"  涉及賽事: {metadata['全局統計']['涉及賽事數']} 場")
        
        print(f"\n🏷️ 變更類型分佈:")
        for change_type, count in sorted(metadata['全局統計']['變更類型分佈'].items(), 
                                         key=lambda x: x[1], reverse=True):
            percentage = count / metadata['全局統計']['總升級次數'] * 100
            print(f"  {change_type}: {count} 次 ({percentage:.1f}%)")
        
        print(f"\n🏎️ 車隊升級排名:")
        team_ranking = sorted(
            finalized.items(),
            key=lambda x: x[1]["車隊統計"]["總升級次數"],
            reverse=True
        )
        for i, (team, data) in enumerate(team_ranking[:5], 1):
            count = data["車隊統計"]["總升級次數"]
            print(f"  {i}. {team}: {count} 次")


def main():
    """主程式"""
    years = [2024, 2025]
    
    for year in years:
        print(f"\n{'='*60}")
        print(f"🏁 重組 {year} 年數據")
        print(f"{'='*60}")
        
        try:
            reorganizer = MajorUpgradeReorganizerByYear(year=year)
            reorganizer.reorganize_and_export()
            
        except FileNotFoundError:
            print(f"❌ 找不到 {year}_f1_major_upgrades.json")
            print(f"💡 請先執行: python analyze_parts_changes_by_year.py")
        except Exception as e:
            print(f"❌ {year} 年重組失敗: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
