#!/usr/bin/env python3
"""
全面分析 2025 FIA 文件中的車隊升級證據
分析範圍：
1. Parts and Parameters (Parc Fermé 變更記錄)
2. New PU elements (動力單元升級)
3. Technical Infringements (技術違規 - 可能包含新部件測試)
4. Car Presentation (新零件展示)
"""
import os
import re
import PyPDF2
import pandas as pd
from pathlib import Path
from collections import defaultdict


class ComprehensiveUpgradeAnalyzer:
    """全面升級分析器"""
    
    RACE_SCHEDULE = {
        "Australian": {"round": 1, "date": "2025-03-16"},
        "Chinese": {"round": 2, "date": "2025-04-06"},
        "Japanese": {"round": 3, "date": "2025-04-20"},
        "Bahrain": {"round": 4, "date": "2025-05-04"},
        "Saudi Arabian": {"round": 5, "date": "2025-05-18"},
        "Miami": {"round": 6, "date": "2025-06-01"},
        "Emilia Romagna": {"round": 7, "date": "2025-06-15"},
        "Monaco": {"round": 8, "date": "2025-06-29"},
        "Spanish": {"round": 9, "date": "2025-06-20"},
        "Canadian": {"round": 10, "date": "2025-06-29"},
        "Austrian": {"round": 11, "date": "2025-07-06"},
        "British": {"round": 12, "date": "2025-07-20"},
        "Belgian": {"round": 13, "date": "2025-08-03"},
        "Hungarian": {"round": 14, "date": "2025-08-17"},
        "Dutch": {"round": 15, "date": "2025-08-31"},
        "Italian": {"round": 16, "date": "2025-09-14"},
        "Azerbaijan": {"round": 17, "date": "2025-09-28"},
        "Singapore": {"round": 18, "date": "2025-10-12"},
        "United States": {"round": 19, "date": "2025-10-26"},
        "Mexico City": {"round": 20, "date": "2025-11-02"}
    }
    
    TEAM_MAPPING = {
        "1": "Red Bull Racing",
        "2": "Ferrari",
        "4": "McLaren",
        "5": "Alpine",
        "6": "Williams",
        "7": "Haas",
        "10": "Mercedes",
        "12": "Aston Martin",
        "14": "RB",
        "16": "Kick Sauber",
        "18": "Kick Sauber",
        "22": "Ferrari",
        "23": "Haas",
        "27": "Mercedes",
        "30": "Alpine",
        "31": "Red Bull Racing",
        "43": "RB",
        "44": "Mercedes",
        "55": "Ferrari",
        "63": "McLaren",
        "81": "McLaren",
        "87": "Williams"
    }
    
    TEAM_FULL_NAMES = {
        "Oracle Red Bull Racing": "Red Bull Racing",
        "Scuderia Ferrari": "Ferrari",
        "Mercedes-AMG Petronas": "Mercedes",
        "McLaren": "McLaren",
        "Aston Martin": "Aston Martin",
        "BWT Alpine": "Alpine",
        "Atlassian Williams Racing": "Williams",
        "Visa Cash App RB": "RB",
        "MoneyGram Haas": "Haas",
        "Stake F1 Team Kick Sauber": "Kick Sauber"
    }
    
    def __init__(self, fiadoc_dir="fiadoc"):
        self.fiadoc_dir = Path(fiadoc_dir)
        self.upgrades = []
    
    def extract_text_from_pdf(self, pdf_path):
        """從 PDF 提取文字"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            return ""
    
    def analyze_parc_ferme_document(self, pdf_path, race_name, race_date):
        """
        分析 Parc Fermé 文件
        重點：Parts and Parameters been replaced
        """
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return []
        
        upgrades = []
        
        # 尋找 "Car XX" 模式
        car_pattern = r"Car\s+(\d{1,2})"
        cars_found = re.findall(car_pattern, text, re.IGNORECASE)
        
        # 部件關鍵字
        component_keywords = [
            "front wing", "rear wing", "floor", "diffuser", "sidepod",
            "nose", "suspension", "brake duct", "beam wing", "bodywork",
            "bargeboard", "cooling", "engine cover"
        ]
        
        for car_num in set(cars_found):
            team = self.TEAM_MAPPING.get(car_num, "Unknown")
            
            # 檢查該車號周圍的文字是否有部件關鍵字
            car_context_pattern = rf"Car\s+{car_num}.{{0,300}}"
            matches = re.finditer(car_context_pattern, text, re.IGNORECASE)
            
            for match in matches:
                context = match.group(0)
                for component in component_keywords:
                    if component.lower() in context.lower():
                        upgrades.append({
                            "team": team,
                            "race": race_name,
                            "date": race_date,
                            "car_number": car_num,
                            "component": component,
                            "evidence_type": "Parc Fermé 變更",
                            "source_file": pdf_path.name,
                            "context": context[:200]
                        })
        
        return upgrades
    
    def analyze_new_pu_elements(self, pdf_path, race_name, race_date):
        """
        分析 New PU elements 文件
        記錄動力單元升級
        """
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return []
        
        upgrades = []
        
        # 尋找車隊名稱或車號
        for team_long, team_short in self.TEAM_FULL_NAMES.items():
            if team_long.lower() in text.lower():
                upgrades.append({
                    "team": team_short,
                    "race": race_name,
                    "date": race_date,
                    "car_number": "N/A",
                    "component": "Power Unit",
                    "evidence_type": "新 PU 元件",
                    "source_file": pdf_path.name,
                    "context": f"在 {race_name} 使用新動力單元元件"
                })
        
        # 也尋找車號
        car_pattern = r"Car\s+(\d{1,2})"
        cars_found = re.findall(car_pattern, text, re.IGNORECASE)
        
        for car_num in set(cars_found):
            team = self.TEAM_MAPPING.get(car_num, "Unknown")
            if team != "Unknown":
                # 避免重複
                if not any(u["team"] == team and u["component"] == "Power Unit" 
                          and u["race"] == race_name for u in upgrades):
                    upgrades.append({
                        "team": team,
                        "race": race_name,
                        "date": race_date,
                        "car_number": car_num,
                        "component": "Power Unit",
                        "evidence_type": "新 PU 元件",
                        "source_file": pdf_path.name,
                        "context": f"車號 {car_num} 使用新 PU 元件"
                    })
        
        return upgrades
    
    def analyze_all_documents(self):
        """分析所有相關文件"""
        if not self.fiadoc_dir.exists():
            print(f"❌ 找不到資料夾: {self.fiadoc_dir}")
            return
        
        print("\n📂 正在掃描 FIA 文件...")
        
        # 1. Parts and Parameters 文件
        parc_ferme_files = list(self.fiadoc_dir.glob("*Parts and parameters*.pdf"))
        print(f"\n🔧 找到 {len(parc_ferme_files)} 個 Parc Fermé 文件")
        
        for pdf_file in sorted(parc_ferme_files):
            race_name = None
            race_date = None
            
            for race_key in self.RACE_SCHEDULE.keys():
                if race_key in pdf_file.name:
                    race_name = race_key
                    race_date = self.RACE_SCHEDULE[race_key]["date"]
                    break
            
            if race_name:
                print(f"   分析: {pdf_file.name[:60]}...")
                upgrades = self.analyze_parc_ferme_document(pdf_file, race_name, race_date)
                if upgrades:
                    print(f"      ✅ 發現 {len(upgrades)} 筆變更記錄")
                    self.upgrades.extend(upgrades)
        
        # 2. New PU elements 文件
        pu_files = list(self.fiadoc_dir.glob("*New PU elements*.pdf"))
        print(f"\n⚙️  找到 {len(pu_files)} 個 PU 元件文件")
        
        for pdf_file in sorted(pu_files):
            race_name = None
            race_date = None
            
            for race_key in self.RACE_SCHEDULE.keys():
                if race_key in pdf_file.name:
                    race_name = race_key
                    race_date = self.RACE_SCHEDULE[race_key]["date"]
                    break
            
            if race_name:
                print(f"   分析: {pdf_file.name[:60]}...")
                upgrades = self.analyze_new_pu_elements(pdf_file, race_name, race_date)
                if upgrades:
                    print(f"      ✅ 發現 {len(upgrades)} 個 PU 升級")
                    self.upgrades.extend(upgrades)
        
        print(f"\n✅ 分析完成！共發現 {len(self.upgrades)} 個升級/變更記錄")
    
    def generate_report(self):
        """生成報告"""
        if not self.upgrades:
            print("\n⚠️ 未發現任何升級資料")
            return None
        
        df = pd.DataFrame(self.upgrades)
        
        # 去重
        df_unique = df.drop_duplicates(subset=['team', 'race', 'component', 'evidence_type'])
        
        print("\n" + "="*120)
        print("📊 2025 F1 車隊升級 & 部件變更彙總（基於 FIA 官方文件）")
        print("="*120)
        print(f"{'車隊':<18} {'分站':<18} {'日期':<12} {'部件':<20} {'證據類型':<18} {'車號':<8} {'文件來源':<30}")
        print("="*120)
        
        for _, row in df_unique.sort_values(['date', 'team']).iterrows():
            print(f"{row['team']:<18} {row['race']:<18} {row['date']:<12} "
                  f"{row['component']:<20} {row['evidence_type']:<18} {row['car_number']:<8} "
                  f"{row['source_file'][:28]:<30}")
        
        print("="*120)
        print(f"\n總計: {len(df_unique)} 個獨特記錄")
        
        # 按車隊統計
        print("\n📈 各車隊變更/升級次數:")
        team_counts = df_unique['team'].value_counts()
        for team, count in team_counts.items():
            print(f"   {team:<20} {count:>3} 次")
        
        # 按證據類型統計
        print("\n📋 證據類型分布:")
        evidence_counts = df_unique['evidence_type'].value_counts()
        for evidence, count in evidence_counts.items():
            print(f"   {evidence:<25} {count:>3} 次")
        
        # 導出 CSV
        output_file = "2025_upgrades_comprehensive.csv"
        df_unique.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 已匯出至: {output_file}")
        
        return df_unique


def main():
    print("\n" + "="*120)
    print("🏁 2025 F1 車隊升級全面分析器")
    print("="*120)
    
    analyzer = ComprehensiveUpgradeAnalyzer(fiadoc_dir="fiadoc")
    analyzer.analyze_all_documents()
    df = analyzer.generate_report()
    
    if df is not None:
        print("\n" + "="*120)
        print("📝 分析說明:")
        print("="*120)
        print("""
        本分析涵蓋以下 FIA 官方文件：
        
        1️⃣ Parts and Parameters (Parc Fermé)
           → 記錄賽車在 Parc Fermé 期間更換的部件
           → 雖非全部是"升級"，但包含重要零件變更
        
        2️⃣ New PU Elements
           → 記錄動力單元新元件的使用
           → 包含引擎、MGU-K、MGU-H、渦輪等
        
        ⚠️ 重要提醒：
        - "Parc Fermé 變更"不等於"性能升級"（可能是維修或策略性調整）
        - 需結合媒體報導（RaceFans、The Race）判斷是否為真正升級套件
        - 動力單元新元件可能是因超出配額或可靠性問題
        
        ✅ 下一步：
        1. 檢查 CSV 檔案中的 'context' 欄位
        2. 對照 RaceFans 等媒體的技術更新報導
        3. 篩選出真正的"空力/結構升級"
        """)
        print("="*120 + "\n")


if __name__ == '__main__':
    main()
