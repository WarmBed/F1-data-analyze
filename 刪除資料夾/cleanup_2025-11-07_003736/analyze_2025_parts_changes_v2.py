#!/usr/bin/env python3
"""
重新分析 2025 F1 Parc Fermé 文件
修正版本：
1. 正確的車號映射（2025 賽季）
2. 完整提取所有部件變更（包括維修）
3. 每個部件單獨一筆記錄
"""
import PyPDF2
import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
import re


class F1UpgradeAnalyzerV2:
    """升級分析器 V2 - 修正版"""
    
    # 2025 F1 車號對應表（來自 FastF1 + 測試/替補車手）
    CAR_NUMBER_TO_TEAM = {
        "1": "Red Bull Racing",
        "4": "McLaren",
        "5": "Kick Sauber",
        "6": "RB",
        "7": "Alpine",
        "10": "Alpine",
        "12": "Mercedes",
        "14": "Aston Martin",
        "16": "Ferrari",
        "18": "Aston Martin",
        "22": "RB",
        "23": "Williams",
        "27": "Kick Sauber",
        "30": "Red Bull Racing",
        "31": "Haas",
        "43": "Williams",  # Franco Colapinto (測試/替補車手)
        "44": "Ferrari",
        "55": "Williams",
        "63": "Mercedes",
        "81": "McLaren",
        "87": "Haas",
    }
    
    # 2025 車手對應表（來自 FastF1 + 測試/替補車手）
    CAR_NUMBER_TO_DRIVER = {
        "1": "Max Verstappen",
        "4": "Lando Norris",
        "5": "Gabriel Bortoleto",
        "6": "Isack Hadjar",
        "7": "Jack Doohan",
        "10": "Pierre Gasly",
        "12": "Andrea Kimi Antonelli",
        "14": "Fernando Alonso",
        "16": "Charles Leclerc",
        "18": "Lance Stroll",
        "22": "Yuki Tsunoda",
        "23": "Alexander Albon",
        "27": "Nico Hulkenberg",
        "30": "Liam Lawson",
        "31": "Esteban Ocon",
        "43": "Franco Colapinto",  # 測試/替補車手 (Williams)
        "44": "Lewis Hamilton",
        "55": "Carlos Sainz",
        "63": "George Russell",
        "81": "Oscar Piastri",
        "87": "Oliver Bearman",
    }
    
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
        "Mexico City": {"round": 20, "date": "2025-11-02"},
        "São Paulo": {"round": 21, "date": "2025-11-09"}
    }
    
    def __init__(self, fiadoc_dir="FIAdoc/2025"):
        self.fiadoc_dir = Path(fiadoc_dir)
        self.all_changes = []
        self.team_mapping_errors = []
    
    def extract_text_from_pdf(self, pdf_path):
        """從 PDF 提取文字"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                full_text = ""
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    # 標記頁碼
                    full_text += f"\n[PAGE_{page_num + 1}]\n{page_text}"
                return full_text
        except Exception as e:
            print(f"   ⚠️ 無法讀取 {pdf_path.name}: {e}")
            return ""
    
    def parse_parc_ferme_document(self, pdf_path, race_name, race_date):
        """
        解析 Parc Fermé 文件
        完整提取每一項部件變更
        """
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return []
        
        changes = []
        current_team = None
        current_page = 1
        
        # 分行處理
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # 檢測頁碼標記
            if line.startswith('[PAGE_'):
                current_page = int(line.replace('[PAGE_', '').replace(']', ''))
                continue
            
            # 檢測車隊名稱（通常是全大寫或包含特定關鍵字）
            if self._is_team_header(line):
                current_team = self._extract_team_name(line)
                continue
            
            # 檢測 Car XX: 格式
            car_match = re.match(r'Car\s+(\d+):\s*(.+)', line.strip())
            if car_match:
                car_num = car_match.group(1)
                first_part = car_match.group(2).strip()
                
                # 獲取車隊和車手（處理前導零）
                car_num_normalized = str(int(car_num)) if car_num.isdigit() else car_num
                team = self._get_team_from_car_number(car_num, current_team)
                driver = self.CAR_NUMBER_TO_DRIVER.get(car_num_normalized, "Unknown")
                
                # 第一個部件
                if first_part:
                    changes.append({
                        "車隊": team,
                        "車手": driver,
                        "車號": car_num,
                        "日期": race_date,
                        "比賽": race_name,
                        "部件": first_part,
                        "頁碼": current_page,
                        "來源文件": pdf_path.name,
                        "原始文本": f"Car {car_num}: {first_part}"
                    })
                
                # 檢查接下來的縮排行（同一車號的其他部件）
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    
                    # 如果是空行或新的 Car，停止
                    if not next_line or next_line.startswith('Car ') or self._is_team_header(next_line):
                        break
                    
                    # 如果是縮排的部件（繼續屬於當前車號）
                    if next_line and not next_line.startswith('[PAGE_'):
                        changes.append({
                            "車隊": team,
                            "車手": driver,
                            "車號": car_num,
                            "日期": race_date,
                            "比賽": race_name,
                            "部件": next_line,
                            "頁碼": current_page,
                            "來源文件": pdf_path.name,
                            "原始文本": f"Car {car_num}: {next_line}"
                        })
                    
                    j += 1
        
        return changes
    
    def _is_team_header(self, line):
        """判斷是否為車隊標題行"""
        line_upper = line.upper().strip()
        team_keywords = [
            'RED BULL', 'FERRARI', 'MERCEDES', 'MCLAREN', 'ASTON MARTIN',
            'ALPINE', 'WILLIAMS', 'RACING BULLS', 'HAAS', 'KICK SAUBER',
            'VISA CASH APP', 'ARAMCO', 'PETRONAS', 'HONDA RBPT', 'RENAULT'
        ]
        return any(keyword in line_upper for keyword in team_keywords) and ':' not in line
    
    def _extract_team_name(self, line):
        """從標題行提取車隊名稱（完全匹配 FIA 文件格式）"""
        line = line.strip().rstrip(':')
        line_upper = line.upper()
        
        # 順序很重要：先檢查完整名稱，再檢查部分名稱
        if 'MCLAREN' in line_upper:
            return 'McLaren'
        elif 'RED BULL RACING' in line_upper or 'ORACLE RED BULL' in line_upper:
            return 'Red Bull Racing'
        elif 'SCUDERIA FERRARI' in line_upper or ('FERRARI' in line_upper and 'HAAS' not in line_upper):
            return 'Ferrari'
        elif 'MERCEDES' in line_upper and 'MCLAREN' not in line_upper and 'ASTON MARTIN' not in line_upper and 'WILLIAMS' not in line_upper:
            return 'Mercedes'
        elif 'ASTON MARTIN' in line_upper:
            return 'Aston Martin'
        elif 'BWT ALPINE' in line_upper or 'ALPINE RENAULT' in line_upper or 'ALPINE' in line_upper:
            return 'Alpine'
        elif 'WILLIAMS' in line_upper or 'ATLASSIAN WILLIAMS' in line_upper:
            return 'Williams'
        elif 'VISA CASH APP RB' in line_upper or 'RACING BULLS' in line_upper or ('RB HONDA' in line_upper and 'RED BULL' not in line_upper):
            return 'RB'
        elif 'HAAS' in line_upper or 'MONEYGRAM HAAS' in line_upper:
            return 'Haas'
        elif 'KICK SAUBER' in line_upper or 'SAUBER' in line_upper:
            return 'Kick Sauber'
        
        return line  # 返回原始文字作為 fallback
    
    def _get_team_from_car_number(self, car_num, fallback_team):
        """根據車號獲取車隊（處理前導零）"""
        # 移除前導零後查找
        car_num_normalized = str(int(car_num)) if car_num.isdigit() else car_num
        team = self.CAR_NUMBER_TO_TEAM.get(car_num_normalized)
        
        if not team and fallback_team:
            # 記錄映射錯誤
            self.team_mapping_errors.append({
                "car_number": car_num,
                "car_number_normalized": car_num_normalized,
                "fallback_team": fallback_team
            })
            return fallback_team
        
        return team or "Unknown"
    
    def analyze_all_documents(self):
        """分析所有 Parc Fermé 文件"""
        print(f"\n🔍 檢查路徑: {self.fiadoc_dir}")
        print(f"   路徑存在: {self.fiadoc_dir.exists()}")
        
        if not self.fiadoc_dir.exists():
            print(f"❌ 找不到資料夾: {self.fiadoc_dir}")
            return
        
        # 使用多種模式匹配（大小寫不同）
        parc_ferme_files = []
        pattern1 = list(self.fiadoc_dir.glob("*Parts and parameters*.pdf"))
        pattern2 = list(self.fiadoc_dir.glob("*Parts and Parameters*.pdf"))
        print(f"   模式1 (*parameters*): {len(pattern1)} 個")
        print(f"   模式2 (*Parameters*): {len(pattern2)} 個")
        
        parc_ferme_files.extend(pattern1)
        parc_ferme_files.extend(pattern2)
        
        # 去除重複
        parc_ferme_files = list(set(parc_ferme_files))
        
        print(f"\n📂 找到 {len(parc_ferme_files)} 個 Parc Fermé 文件")
        print("="*100)
        
        for pdf_file in sorted(parc_ferme_files):
            race_name = None
            race_date = None
            
            for race_key in self.RACE_SCHEDULE.keys():
                if race_key in pdf_file.name:
                    race_name = race_key
                    race_date = self.RACE_SCHEDULE[race_key]["date"]
                    break
            
            if not race_name:
                continue
            
            print(f"\n🔍 分析: {pdf_file.name[:70]}...")
            changes = self.parse_parc_ferme_document(pdf_file, race_name, race_date)
            
            if changes:
                print(f"   ✅ 提取 {len(changes)} 筆部件變更")
                self.all_changes.extend(changes)
            else:
                print(f"   ⚪ 無變更記錄")
        
        print("\n" + "="*100)
        print(f"✅ 分析完成！共提取 {len(self.all_changes)} 筆部件變更記錄")
        
        if self.team_mapping_errors:
            print(f"\n⚠️ 發現 {len(self.team_mapping_errors)} 個車號映射問題")
    
    def save_to_json(self, output_file="2025_f1_parts_changes_complete.json"):
        """儲存為 JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_changes, f, ensure_ascii=False, indent=2)
        print(f"\n💾 已儲存至: {output_file}")
    
    def save_to_csv(self, output_file="2025_f1_parts_changes_complete.csv"):
        """儲存為 CSV"""
        df = pd.DataFrame(self.all_changes)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"💾 已儲存至: {output_file}")
    
    def generate_report(self):
        """生成報告"""
        if not self.all_changes:
            print("\n⚠️ 無數據")
            return
        
        df = pd.DataFrame(self.all_changes)
        
        print("\n" + "="*120)
        print("📊 2025 F1 部件變更完整記錄")
        print("="*120)
        print(f"{'車隊':<18} {'車手':<20} {'車號':<6} {'日期':<12} {'比賽':<18} {'部件':<40} {'頁碼':<6}")
        print("="*120)
        
        for _, row in df.head(20).iterrows():
            print(f"{row['車隊']:<18} {row['車手']:<20} {row['車號']:<6} {row['日期']:<12} "
                  f"{row['比賽']:<18} {row['部件']:<40} {row['頁碼']:<6}")
        
        print("="*120)
        print(f"\n總計: {len(df)} 筆記錄（僅顯示前 20 筆）")
        
        # 統計
        print("\n📈 各車隊變更次數:")
        team_counts = df['車隊'].value_counts()
        for team, count in team_counts.items():
            print(f"   {team:<20} {count:>3} 次")
        
        print("\n📋 各車手變更次數 (Top 10):")
        driver_counts = df['車手'].value_counts().head(10)
        for driver, count in driver_counts.items():
            print(f"   {driver:<20} {count:>3} 次")


def main():
    print("\n" + "="*120)
    print("🏁 2025 F1 部件變更完整分析器 V2 (修正版)")
    print("="*120)
    
    analyzer = F1UpgradeAnalyzerV2(fiadoc_dir="FIAdoc/2025")
    
    # 執行分析
    analyzer.analyze_all_documents()
    
    # 生成報告
    analyzer.generate_report()
    
    # 儲存檔案
    analyzer.save_to_json()
    analyzer.save_to_csv()
    
    print("\n" + "="*120)
    print("✅ 完成！")
    print("="*120 + "\n")


if __name__ == '__main__':
    main()
