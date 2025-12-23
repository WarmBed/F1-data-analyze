#!/usr/bin/env python3
"""
按年份分析 F1 Parc Fermé 文件
處理 FIAdoc/2024 和 FIAdoc/2025 資料夾
為每個年份生成獨立的分類 JSON
"""
import PyPDF2
import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
import re
import sys


class F1UpgradeAnalyzerByYear:
    """按年份分析 F1 部件變更"""
    
    # 2024 F1 車號對應表
    CAR_NUMBER_TO_TEAM_2024 = {
        "1": "Red Bull Racing",
        "2": "Kick Sauber",
        "3": "Williams",
        "4": "McLaren",
        "10": "Alpine",
        "11": "Red Bull Racing",
        "14": "Aston Martin",
        "16": "Ferrari",
        "18": "Aston Martin",
        "20": "Haas",
        "21": "RB",
        "22": "RB",
        "23": "Williams",
        "24": "Kick Sauber",
        "27": "Haas",
        "38": "Williams",  # Franco Colapinto
        "40": "Alpine",  # Jack Doohan (測試車手)
        "43": "Williams",  # Franco Colapinto
        "44": "Mercedes",
        "55": "Ferrari",
        "63": "Mercedes",
        "77": "Alpine",
        "81": "McLaren",
    }
    
    # 2024 車手對應表
    CAR_NUMBER_TO_DRIVER_2024 = {
        "1": "Max Verstappen",
        "2": "Logan Sargeant",
        "3": "Daniel Ricciardo",
        "4": "Lando Norris",
        "10": "Pierre Gasly",
        "11": "Sergio Perez",
        "14": "Fernando Alonso",
        "16": "Charles Leclerc",
        "18": "Lance Stroll",
        "20": "Kevin Magnussen",
        "21": "Nyck de Vries",
        "22": "Yuki Tsunoda",
        "23": "Alexander Albon",
        "24": "Zhou Guanyu",
        "27": "Nico Hulkenberg",
        "38": "Franco Colapinto",
        "40": "Jack Doohan",
        "43": "Franco Colapinto",
        "44": "Lewis Hamilton",
        "55": "Carlos Sainz",
        "63": "George Russell",
        "77": "Valtteri Bottas",
        "81": "Oscar Piastri",
    }
    
    # 2025 F1 車號對應表
    CAR_NUMBER_TO_TEAM_2025 = {
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
        "43": "Williams",  # Franco Colapinto
        "44": "Ferrari",
        "55": "Williams",
        "63": "Mercedes",
        "81": "McLaren",
        "87": "Haas",
    }
    
    # 2025 車手對應表
    CAR_NUMBER_TO_DRIVER_2025 = {
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
        "43": "Franco Colapinto",
        "44": "Lewis Hamilton",
        "55": "Carlos Sainz",
        "63": "George Russell",
        "81": "Oscar Piastri",
        "87": "Oliver Bearman",
    }
    
    def __init__(self, year, fiadoc_base_dir="FIAdoc"):
        self.year = year
        self.fiadoc_dir = Path(fiadoc_base_dir) / str(year)
        self.all_changes = []
        self.team_mapping_errors = []
        
        # 根據年份選擇對應表
        if year == 2024:
            self.CAR_NUMBER_TO_TEAM = self.CAR_NUMBER_TO_TEAM_2024
            self.CAR_NUMBER_TO_DRIVER = self.CAR_NUMBER_TO_DRIVER_2024
        elif year == 2025:
            self.CAR_NUMBER_TO_TEAM = self.CAR_NUMBER_TO_TEAM_2025
            self.CAR_NUMBER_TO_DRIVER = self.CAR_NUMBER_TO_DRIVER_2025
        else:
            raise ValueError(f"不支援的年份: {year}")
    
    def extract_text_from_pdf(self, pdf_path):
        """從 PDF 提取文字"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"❌ 讀取 {pdf_path.name} 失敗: {e}")
            return None
    
    def parse_race_name_from_filename(self, filename):
        """從檔名解析賽事名稱"""
        # 範例: "2025 Australian GP - Parc Fermé.pdf"
        match = re.search(r'\d{4}\s+(.+?)\s+GP', filename)
        if match:
            return match.group(1)
        return "Unknown"
    
    def categorize_component(self, part_description):
        """對部件進行分類"""
        part_upper = part_description.upper()
        
        # 前翼系統
        if any(keyword in part_upper for keyword in ['FRONT WING', 'NOSE', 'DIVEPLANE', 'ENDPLATE']):
            return "前翼系統"
        
        # 後翼系統
        if any(keyword in part_upper for keyword in ['REAR WING', 'DRS', 'BEAM WING']):
            return "後翼系統"
        
        # 底板系統
        if any(keyword in part_upper for keyword in ['FLOOR', 'DIFFUSER', 'PLANK', 'SKID']):
            return "底板系統"
        
        # 側箱/車身
        if any(keyword in part_upper for keyword in ['SIDEPOD', 'BODYWORK', 'ENGINE COVER', 'AIRBOX']):
            return "側箱/車身"
        
        # 動力單元
        if any(keyword in part_upper for keyword in ['ICE', 'MGU-H', 'MGU-K', 'TURBO', 'ES', 'CE', 'ENERGY STORE', 'CONTROL ELECTRONICS']):
            return "動力單元"
        
        # 變速箱/傳動
        if any(keyword in part_upper for keyword in ['GEARBOX', 'CLUTCH', 'DRIVESHAFT']):
            return "變速箱/傳動"
        
        # 懸吊系統
        if any(keyword in part_upper for keyword in ['SUSPENSION', 'DAMPER', 'SPRING', 'ANTI-ROLL']):
            return "懸吊系統"
        
        # 煞車系統
        if any(keyword in part_upper for keyword in ['BRAKE', 'CALIPER', 'DISC']):
            return "煞車系統"
        
        # 冷卻系統
        if any(keyword in part_upper for keyword in ['RADIATOR', 'COOLING', 'INTERCOOLER']):
            return "冷卻系統"
        
        # 電子/感測器
        if any(keyword in part_upper for keyword in ['SENSOR', 'ELECTRONICS', 'WIRE', 'CABLE']):
            return "電子/感測器"
        
        # 其他
        return "其他部件"
    
    def parse_parc_ferme_document(self, pdf_path):
        """解析 Parc Fermé 文件"""
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return []
        
        race_name = self.parse_race_name_from_filename(pdf_path.name)
        changes = []
        
        # 分頁處理
        pages = text.split('\f')
        
        for page_num, page_text in enumerate(pages, 1):
            # 尋找 "Parts and parameters been replaced and or changed" 區塊（不區分大小寫）
            if "parts and parameters been replaced" not in page_text.lower():
                continue
            
            # 提取車號
            car_match = re.search(r'Car\s+(\d+)', page_text, re.IGNORECASE)
            if not car_match:
                continue
            
            car_number = car_match.group(1)
            team = self.CAR_NUMBER_TO_TEAM.get(car_number, "Unknown")
            driver = self.CAR_NUMBER_TO_DRIVER.get(car_number, "Unknown")
            
            if team == "Unknown":
                self.team_mapping_errors.append({
                    "file": pdf_path.name,
                    "page": page_num,
                    "car_number": car_number
                })
            
            # 提取部件變更區塊（不區分大小寫搜尋）
            parts_section = re.split(r'Parts and parameters been replaced and or changed', page_text, maxsplit=1, flags=re.IGNORECASE)
            if len(parts_section) < 2:
                continue
            
            parts_text = parts_section[1]
            
            # 分行處理每個部件
            lines = parts_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                
                # 跳過標題和無關內容
                if any(skip in line.upper() for skip in ['PAGE', 'CAR', 'TEAM', 'DRIVER', 'DOCUMENT']):
                    continue
                
                # 清理特殊字元
                part = re.sub(r'[•\-→]', '', line).strip()
                
                if part:
                    changes.append({
                        "賽事名稱": race_name,
                        "車隊": team,
                        "車手": driver,
                        "車號": car_number,
                        "更換部件": part,
                        "部件類別": self.categorize_component(part),
                        "資料來源": pdf_path.name,
                        "頁碼": page_num,
                        "年份": self.year
                    })
        
        return changes
    
    def analyze_all_documents(self):
        """分析所有 PDF 文件"""
        pdf_files = sorted(self.fiadoc_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"⚠️  {self.fiadoc_dir} 中沒有找到 PDF 文件")
            return
        
        print(f"\n🔍 開始分析 {self.year} 年 Parc Fermé 文件...")
        print(f"📁 資料夾: {self.fiadoc_dir}")
        print(f"📄 文件數量: {len(pdf_files)}")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] 處理: {pdf_file.name}")
            changes = self.parse_parc_ferme_document(pdf_file)
            self.all_changes.extend(changes)
        
        print(f"\n✅ 分析完成！")
        print(f"📊 總變更次數: {len(self.all_changes)}")
        
        # 顯示車隊統計
        team_stats = defaultdict(int)
        for change in self.all_changes:
            team_stats[change["車隊"]] += 1
        
        print(f"\n🏎️ 車隊變更統計:")
        for team, count in sorted(team_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {team}: {count} 次")
        
        # 顯示映射錯誤
        if self.team_mapping_errors:
            print(f"\n⚠️  發現 {len(self.team_mapping_errors)} 個未知車號:")
            unknown_cars = defaultdict(int)
            for error in self.team_mapping_errors:
                unknown_cars[error["car_number"]] += 1
            for car, count in sorted(unknown_cars.items()):
                print(f"  車號 {car}: {count} 次")
    
    def export_to_json(self, output_file=None):
        """導出為 JSON"""
        if output_file is None:
            output_file = f"{self.year}_f1_parts_changes_complete.json"
        
        data = {
            "metadata": {
                "年份": self.year,
                "生成時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "總變更次數": len(self.all_changes),
                "分析文件數": len(list(self.fiadoc_dir.glob("*.pdf"))),
                "資料來源": str(self.fiadoc_dir)
            },
            "部件變更記錄": self.all_changes
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 完整數據已保存至: {output_file}")
        return output_file


class MajorUpgradeExtractorByYear:
    """提取主要部件升級（按年份）"""
    
    MAJOR_COMPONENTS = {
        "前翼": [r'front wing', r'nose assembly', r'nose', r'front wing.*assembly'],
        "後翼": [r'rear wing', r'rear wing.*assembly', r'drs', r'beam wing'],
        "底板": [r'floor', r'floor.*assembly', r'diffuser', r'floor.*edge', r'floor.*body'],
        "側箱": [r'sidepod', r'sidepod.*bodywork', r'engine cover'],
        "引擎": [r'\bICE\b', r'internal combustion engine'],
        "MGU": [r'MGU-H', r'MGU-K', r'mgu'],
        "渦輪": [r'turbo', r'turbocharger'],
        "能量儲存": [r'energy store', r'\bES\b'],
        "控制電子": [r'control electronics', r'\bCE\b'],
        "變速箱": [r'gearbox', r'gearbox.*assembly'],
        "懸吊": [r'suspension.*assembly', r'suspension.*system']
    }
    
    def __init__(self, year):
        self.year = year
    
    def is_major_component(self, part_description):
        """判斷是否為主要部件"""
        part_lower = part_description.lower()
        
        for component_type, patterns in self.MAJOR_COMPONENTS.items():
            for pattern in patterns:
                if re.search(pattern, part_lower):
                    return True
        return False
    
    def extract_major_upgrades(self, input_file, output_file=None):
        """提取主要升級"""
        if output_file is None:
            output_file = f"{self.year}_f1_major_upgrades.json"
        
        # 讀取完整數據
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 過濾主要部件
        major_upgrades = [
            change for change in data["部件變更記錄"]
            if self.is_major_component(change["更換部件"])
        ]
        
        # 準備輸出
        output_data = {
            "metadata": {
                "年份": self.year,
                "生成時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "主要升級次數": len(major_upgrades),
                "總變更次數": data["metadata"]["總變更次數"],
                "過濾比例": f"{len(major_upgrades) / data['metadata']['總變更次數'] * 100:.1f}%" if data["metadata"]["總變更次數"] > 0 else "0.0%"
            },
            "主要升級記錄": major_upgrades
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {self.year} 主要升級: {len(major_upgrades)} 次 (過濾自 {data['metadata']['總變更次數']} 次總變更)")
        print(f"💾 已保存至: {output_file}")
        
        return output_file


def main():
    """主程式"""
    years = [2024, 2025]
    
    for year in years:
        print(f"\n{'='*60}")
        print(f"🏁 處理 {year} 年數據")
        print(f"{'='*60}")
        
        try:
            # 步驟 1: 分析所有變更
            analyzer = F1UpgradeAnalyzerByYear(year=year)
            analyzer.analyze_all_documents()
            complete_file = analyzer.export_to_json()
            
            # 步驟 2: 提取主要升級
            extractor = MajorUpgradeExtractorByYear(year=year)
            major_file = extractor.extract_major_upgrades(complete_file)
            
            print(f"\n✅ {year} 年處理完成！")
            
        except Exception as e:
            print(f"❌ {year} 年處理失敗: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
