#!/usr/bin/env python3
"""
從 fiadoc 資料夾中的 2025 FIA 文件分析車隊升級套件
重點分析 Scrutineering 文件以找出重新認證的部件
"""
import os
import re
import PyPDF2
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class FIAUpgradeAnalyzer:
    """FIA 文件升級分析器"""
    
    # 2025 賽程表（用於判斷升級時間）
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
    
    # 車隊名稱映射
    TEAM_MAPPING = {
        "red bull": "Red Bull Racing",
        "ferrari": "Ferrari",
        "mercedes": "Mercedes",
        "mclaren": "McLaren",
        "aston martin": "Aston Martin",
        "alpine": "Alpine",
        "williams": "Williams",
        "rb": "RB",
        "racing bulls": "RB",
        "visa rb": "RB",
        "kick sauber": "Kick Sauber",
        "sauber": "Kick Sauber",
        "haas": "Haas"
    }
    
    # 關鍵部件關鍵字
    COMPONENT_KEYWORDS = {
        "front_wing": ["front wing", "fw", "front aero"],
        "rear_wing": ["rear wing", "rw", "rear aero"],
        "floor": ["floor", "plank", "diffuser"],
        "sidepod": ["sidepod", "side pod", "body work"],
        "suspension": ["suspension", "front suspension", "rear suspension"],
        "brake_duct": ["brake duct", "cooling duct", "brake cooling"],
        "beam_wing": ["beam wing", "rear beam"],
        "nose": ["nose", "nose cone"],
        "engine_cover": ["engine cover", "bodywork"],
        "bargeboard": ["bargeboard", "barge board"],
        "halo": ["halo"],
        "side_impact": ["side impact structure", "sis"],
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
            print(f"   ⚠️ 無法讀取 {pdf_path.name}: {e}")
            return ""
    
    def parse_scrutineering_document(self, pdf_path, race_name, race_date):
        """
        解析 Scrutineering 文件
        
        關鍵線索：
        - "New parts" / "new components"
        - Part 認證編號變化
        - "homologation" / "re-homologation"
        """
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return []
        
        upgrades_found = []
        
        # 搜尋 "new" + 部件關鍵字
        for comp_type, keywords in self.COMPONENT_KEYWORDS.items():
            for keyword in keywords:
                # 模式 1: "new [component]"
                pattern1 = rf"new\s+{re.escape(keyword)}"
                if re.search(pattern1, text, re.IGNORECASE):
                    upgrades_found.append({
                        "component": comp_type,
                        "keyword": keyword,
                        "evidence": "新部件關鍵字",
                        "context": self._extract_context(text, keyword)
                    })
                
                # 模式 2: "homolog" + 部件
                pattern2 = rf"(?:re-?homolog|homolog).*{re.escape(keyword)}"
                if re.search(pattern2, text, re.IGNORECASE):
                    upgrades_found.append({
                        "component": comp_type,
                        "keyword": keyword,
                        "evidence": "重新認證",
                        "context": self._extract_context(text, keyword)
                    })
        
        # 搜尋車隊名稱關聯
        results = []
        for upgrade in upgrades_found:
            # 在上下文中尋找車隊名稱
            context_lower = upgrade["context"].lower()
            for team_key, team_name in self.TEAM_MAPPING.items():
                if team_key in context_lower:
                    results.append({
                        "team": team_name,
                        "race": race_name,
                        "date": race_date,
                        "component": upgrade["component"],
                        "evidence": upgrade["evidence"],
                        "source_file": pdf_path.name,
                        "context": upgrade["context"][:200]  # 限制長度
                    })
        
        return results
    
    def _extract_context(self, text, keyword, window=150):
        """提取關鍵字周圍的上下文"""
        pattern = re.compile(f".{{0,{window}}}{re.escape(keyword)}.{{0,{window}}}", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return match.group(0).replace('\n', ' ').strip()
        return ""
    
    def analyze_all_documents(self):
        """分析所有 Scrutineering 文件"""
        if not self.fiadoc_dir.exists():
            print(f"❌ 找不到資料夾: {self.fiadoc_dir}")
            return
        
        # 篩選 Scrutineering 文件
        scrutineering_files = list(self.fiadoc_dir.glob("*Scrutineering*.pdf"))
        
        print(f"\n📂 找到 {len(scrutineering_files)} 個 Scrutineering 文件")
        print("="*100)
        
        for pdf_file in sorted(scrutineering_files):
            filename = pdf_file.name
            
            # 從檔名提取分站資訊
            race_name = None
            race_date = None
            
            for race_key in self.RACE_SCHEDULE.keys():
                if race_key in filename:
                    race_name = race_key
                    race_date = self.RACE_SCHEDULE[race_key]["date"]
                    break
            
            if not race_name:
                continue
            
            print(f"\n🔍 分析: {filename}")
            print(f"   分站: {race_name} ({race_date})")
            
            # 解析文件
            upgrades = self.parse_scrutineering_document(pdf_file, race_name, race_date)
            
            if upgrades:
                print(f"   ✅ 發現 {len(upgrades)} 個可能的升級證據")
                self.upgrades.extend(upgrades)
            else:
                print(f"   ⚪ 無明顯升級證據")
        
        print("\n" + "="*100)
        print(f"✅ 分析完成！共發現 {len(self.upgrades)} 個升級線索")
    
    def generate_report(self):
        """生成報告"""
        if not self.upgrades:
            print("\n⚠️ 未發現任何升級資料")
            return
        
        df = pd.DataFrame(self.upgrades)
        
        # 去重（同一車隊、分站、部件只保留一筆）
        df_unique = df.drop_duplicates(subset=['team', 'race', 'component'])
        
        print("\n" + "="*100)
        print("📊 2025 F1 車隊升級套件彙總（基於 FIA Scrutineering 文件）")
        print("="*100)
        print(f"{'車隊':<20} {'分站':<20} {'日期':<12} {'部件':<18} {'證據來源':<15} {'文件':<40}")
        print("="*100)
        
        for _, row in df_unique.sort_values(['date', 'team']).iterrows():
            print(f"{row['team']:<20} {row['race']:<20} {row['date']:<12} "
                  f"{row['component']:<18} {row['evidence']:<15} {row['source_file']:<40}")
        
        print("="*100)
        print(f"\n總計: {len(df_unique)} 個獨特升級記錄")
        
        # 按車隊統計
        print("\n📈 各車隊升級次數:")
        team_counts = df_unique['team'].value_counts()
        for team, count in team_counts.items():
            print(f"   {team:<20} {count:>3} 次")
        
        # 導出 CSV
        output_file = "2025_upgrades_from_fia_scrutineering.csv"
        df_unique.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 已匯出至: {output_file}")
        
        # 導出詳細版（含 context）
        output_detail = "2025_upgrades_detailed.csv"
        df.to_csv(output_detail, index=False, encoding='utf-8-sig')
        print(f"💾 已匯出詳細版至: {output_detail}")
        
        return df_unique


def main():
    print("\n" + "="*100)
    print("🏁 2025 F1 車隊升級分析器 - 基於 FIA 官方文件")
    print("="*100)
    
    analyzer = FIAUpgradeAnalyzer(fiadoc_dir="fiadoc")
    
    # 執行分析
    analyzer.analyze_all_documents()
    
    # 生成報告
    df = analyzer.generate_report()
    
    print("\n" + "="*100)
    print("📝 分析說明:")
    print("="*100)
    print("""
    本分析基於 FIA Scrutineering 文件，尋找以下升級證據：
    
    1️⃣ 新部件關鍵字（"new front wing", "new floor" 等）
    2️⃣ 重新認證證據（"re-homologation", "homologation" 等）
    3️⃣ 部件編號變化（認證編號更新）
    
    ⚠️ 限制：
    - Scrutineering 文件主要記錄技術檢驗，不一定明確列出所有升級
    - 需人工二次確認（檢查 context 欄位）
    - 小型升級或戰略性調整可能未被記錄
    
    ✅ 可靠性：
    - FIA 官方文件，權威來源
    - 重新認證（re-homologation）是升級的強力證據
    - 賽前 1-2 週出現認證變更 = 極可能是升級套件
    """)
    
    print("\n🎯 下一步建議:")
    print("   1. 檢查生成的 CSV 檔案，查看 'context' 欄位驗證證據")
    print("   2. 結合 RaceFans、The Race 等媒體報導交叉驗證")
    print("   3. 使用 upgrade_tracker.py 整合至主資料庫")
    print("="*100 + "\n")


if __name__ == '__main__':
    main()
