#!/usr/bin/env python3
"""
提取 2025 F1 主要部件升級
僅輸出 JSON 格式
"""
import json
from pathlib import Path
import re


class MajorUpgradeExtractor:
    """主要部件升級提取器"""
    
    # 定義主要部件關鍵字（英文大小寫不敏感）
    MAJOR_COMPONENTS = {
        # 空氣動力學主要部件
        "前翼系統": [
            r'\bfront\s+wing\b', r'\bfw\s+assembly\b', r'\bmain\s+plane\b', 
            r'\bfront\s+wing\s+endplate\b', r'\bfront\s+wing\s+flap\b'
        ],
        "後翼系統": [
            r'\brear\s+wing\b', r'\brw\s+assembly\b', r'\bdrs\s+flap\b',
            r'\brear\s+wing\s+endplate\b', r'\brear\s+wing\s+main\s+plane\b'
        ],
        "底板系統": [
            r'\bfloor\s+assembly\b', r'\bfloor\s+body\b', r'\bfloor\s+edge\b',
            r'\bdiffuser\b', r'\bfloor\s+fence\b', r'\bfloor\s+stay\b'
        ],
        "側箱系統": [
            r'\bsidepod\b', r'\bengine\s+cover\b', r'\bcooling\s+inlet\b',
            r'\bside\s+bodywork\b'
        ],
        "車身外殼": [
            r'\bmonocoque\b', r'\bchassis\b', r'\bbodywork\b', r'\bnosecone\b'
        ],
        
        # 動力單元
        "引擎系統": [
            r'\bICE\b', r'\binternal\s+combustion\s+engine\b', r'\bturbo\b',
            r'\bturbocharger\b'
        ],
        "電能回收": [
            r'\bMGU-H\b', r'\bMGU-K\b', r'\benergy\s+store\b', r'\bES\b',
            r'\bcontrol\s+electronics\b', r'\bCE\b'
        ],
        
        # 傳動系統
        "變速箱": [
            r'\bgearbox\s+assembly\b', r'\bgearbox\s+casing\b', r'\btransmission\b'
        ],
        
        # 懸吊系統
        "懸吊系統": [
            r'\bfront\s+suspension\b', r'\brear\s+suspension\b',
            r'\bsuspension\s+assembly\b', r'\bpush\s+rod\b', r'\bpull\s+rod\b'
        ],
        
        # 煞車系統（主要組件）
        "煞車主組件": [
            r'\bbrake\s+disc\b', r'\bbrake\s+caliper\b', r'\bbrake\s+duct\s+assembly\b'
        ]
    }
    
    def __init__(self, json_file="2025_f1_parts_changes_complete.json"):
        self.json_file = json_file
        self.all_changes = []
        self.major_upgrades = []
    
    def load_data(self):
        """載入完整部件變更數據"""
        if not Path(self.json_file).exists():
            print(f"❌ 找不到檔案: {self.json_file}")
            return False
        
        with open(self.json_file, 'r', encoding='utf-8') as f:
            self.all_changes = json.load(f)
        
        return True
    
    def is_major_component(self, part_name):
        """
        判斷是否為主要部件
        返回: (是否主要部件, 類別名稱)
        """
        part_lower = part_name.lower()
        
        for category, patterns in self.MAJOR_COMPONENTS.items():
            for pattern in patterns:
                if re.search(pattern, part_lower, re.IGNORECASE):
                    return True, category
        
        return False, None
    
    def extract_major_upgrades(self):
        """提取所有主要部件升級"""
        for change in self.all_changes:
            is_major, category = self.is_major_component(change["部件"])
            
            if is_major:
                # 添加類別標籤
                upgrade_record = change.copy()
                upgrade_record["部件類別"] = category
                self.major_upgrades.append(upgrade_record)
    
    def save_to_json(self, output_file="2025_f1_major_upgrades.json", include_metadata=True):
        """輸出 JSON（可選擇是否包含 metadata）"""
        if include_metadata:
            stats = self.get_statistics()
            output_data = {
                "metadata": {
                    "生成時間": "2025-11-06",
                    "數據源": "2025_f1_parts_changes_complete.json",
                    "統計資訊": stats
                },
                "主要部件升級記錄": self.major_upgrades
            }
        else:
            output_data = self.major_upgrades
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    def get_statistics(self):
        """獲取統計資訊（用於 JSON metadata）"""
        stats = {
            "總升級次數": len(self.major_upgrades),
            "各車隊主要升級次數": {},
            "各部件類別次數": {},
            "各車手主要升級次數": {}
        }
        
        # 統計各車隊
        for upgrade in self.major_upgrades:
            team = upgrade["車隊"]
            category = upgrade["部件類別"]
            driver = upgrade["車手"]
            
            stats["各車隊主要升級次數"][team] = stats["各車隊主要升級次數"].get(team, 0) + 1
            stats["各部件類別次數"][category] = stats["各部件類別次數"].get(category, 0) + 1
            stats["各車手主要升級次數"][driver] = stats["各車手主要升級次數"].get(driver, 0) + 1
        
        # 排序
        stats["各車隊主要升級次數"] = dict(sorted(
            stats["各車隊主要升級次數"].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        stats["各部件類別次數"] = dict(sorted(
            stats["各部件類別次數"].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        stats["各車手主要升級次數"] = dict(sorted(
            stats["各車手主要升級次數"].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        return stats


def main():
    extractor = MajorUpgradeExtractor()
    
    # 載入數據
    if not extractor.load_data():
        return
    
    # 提取主要升級
    extractor.extract_major_upgrades()
    
    # 儲存檔案（包含完整 metadata）
    extractor.save_to_json(include_metadata=True)
    
    print(f"✅ 已提取 {len(extractor.major_upgrades)} 筆主要部件升級")
    print(f"💾 已儲存至: 2025_f1_major_upgrades.json")


if __name__ == '__main__':
    main()
