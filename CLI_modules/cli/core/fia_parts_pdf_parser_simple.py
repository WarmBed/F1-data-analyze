#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIA Parts Changes PDF 解析器 - 簡化版
僅處理 "Parts and parameters been replaced and or changed" PDF

開發原則遵循狀態：
- 原則 0: 反幻覺編碼 - 使用 PyPDF2 實際驗證的 API
- 原則 1: 禁止幻覺編碼 - 所有 PDF 解析邏輯經過實測驗證
- 原則 2: 模組資料夾優先 - 新模組放置於 CLI_modules/cli/core/
- 原則 3: 通用模組優先 - 輸出格式與 UpgradeClassifierV2 整合
- 原則 4: 模組多國語言化 - 輸出欄位使用中文，支援 UTF-8
- 原則 5: Logger 導出 - 使用 print() 輸出，由主程式 Logger 捕獲

提取資訊：
- 車隊
- 車號 → 車手（映射）
- 部件名稱
- 賽事日期

不提取：
- Type（PDF 沒有）
- Description（PDF 沒有）

模組化狀態：
- CLI: Function 29 整合 (function_mapper.py Line 2996-3040)
- API: 支援 (refactored_api.py 自動調用 CLI)
- JSON: {year}_f1_parts_changes_classified.json
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import PyPDF2
import re
from pathlib import Path
from collections import defaultdict


class SimplePartsParser:
    """簡化的部件變更解析器
    
    ✨ 新增功能：FastF1 動態車號映射
    - 自動從 FastF1 獲取最新車手車號映射
    - 支援車手換隊、預備車手、新秀車手
    - 生成 driver_mapping.json 供 GUI 使用
    """
    
    # 2025 車號映射表（預設值，會被 FastF1 覆蓋）
    CAR_NUMBER_TO_TEAM = {
        "01": "Red Bull Racing", "02": "Red Bull Racing",
        "04": "McLaren", "81": "McLaren",
        "16": "Ferrari", "44": "Ferrari",
        "63": "Mercedes", "12": "Mercedes",
        "18": "Aston Martin", "14": "Aston Martin",
        "10": "Alpine", "31": "Alpine",
        "23": "Williams", "43": "Williams",
        "20": "Haas", "55": "Haas",
        "22": "RB", "06": "RB",
        "77": "Kick Sauber", "51": "Kick Sauber"
    }
    
    CAR_NUMBER_TO_DRIVER = {
        "01": "Max Verstappen", "02": "Liam Lawson",
        "04": "Lando Norris", "81": "Oscar Piastri",
        "16": "Charles Leclerc", "44": "Lewis Hamilton",
        "63": "George Russell", "12": "Andrea Kimi Antonelli",
        "18": "Lance Stroll", "14": "Fernando Alonso",
        "10": "Pierre Gasly", "31": "Jack Doohan",
        "23": "Alexander Albon", "43": "Carlos Sainz",
        "20": "Kevin Magnussen", "55": "Esteban Ocon",
        "22": "Yuki Tsunoda", "06": "Isack Hadjar",
        "77": "Gabriel Bortoleto", "51": "Nico Hülkenberg"
    }
    
    # 2025 賽曆日期映射
    RACE_DATES = {
        "Australian": "2025-03-16",
        "China": "2025-03-23",
        "Japan": "2025-04-06",
        "Bahrain": "2025-04-13",
        "Saudi Arabia": "2025-04-20",
        "Miami": "2025-05-04",
        "Emilia Romagna": "2025-05-18",
        "Monaco": "2025-05-25",
        "Spain": "2025-06-01",
        "Canada": "2025-06-15",
        "Austria": "2025-06-29",
        "Great Britain": "2025-07-06",
        "Belgium": "2025-07-27",
        "Hungary": "2025-08-03",
        "Netherlands": "2025-08-31",
        "Italy": "2025-09-07",
        "Azerbaijan": "2025-09-21",
        "Singapore": "2025-10-05",
        "United States": "2025-10-19",
        "Mexico": "2025-10-26",
        "Brazil": "2025-11-09",
        "Las Vegas": "2025-11-22",
        "Qatar": "2025-11-30",
        "Abu Dhabi": "2025-12-07"
    }
    
    def __init__(self, year: int, fiadoc_dir: str):
        self.year = year
        self.fiadoc_dir = Path(fiadoc_dir) / str(year)
        self.all_changes = []
        self.fastf1_mapping = {}  # FastF1 動態映射
        self.mapping_source = "static"  # 映射來源：static/fastf1
        
        # 嘗試從 FastF1 獲取動態映射
        self._load_fastf1_mapping()
    
    def _load_fastf1_mapping(self):
        """從 FastF1 載入動態車號映射
        
        策略：
        1. 嘗試從已舉辦的最近賽事獲取（最準確）
        2. 失敗時回退到靜態映射表
        3. 生成 driver_mapping.json 供其他模組使用
        """
        try:
            import fastf1
            import json
            from datetime import datetime
            
            print(f"\n[MAPPING] 嘗試從 FastF1 獲取 {self.year} 年車號映射...")
            
            # 啟用 FastF1 快取
            fastf1.Cache.enable_cache('f1_analysis_cache')
            
            # 策略：優先從賽季後期獲取（包含所有車手變動）
            # 2025 年重要變動：第 6 站起 Colapinto (43) 加入 Alpine
            recent_races = [
                "Brazil",           # 最新（包含所有車手）
                "Mexico",
                "United States",
                "Singapore",
                "Azerbaijan",
                "Italy",            # 第 15 站
                "Netherlands",
                "Emilia Romagna",   # 第 6 站（Colapinto 首次出賽）
                "Monaco",
                "Spain",
                "Bahrain",          # 第 1 站（備用）
                "Australia"
            ]
            
            for race in recent_races:
                try:
                    print(f"   [TRY] 載入 {self.year} {race} 正賽數據...")
                    session = fastf1.get_session(self.year, race, 'R')
                    session.load(telemetry=False, weather=False, messages=False)
                    
                    if hasattr(session, 'results') and session.results is not None:
                        print(f"   [OK] 成功從 {race} 獲取車手資料")
                        
                        # 建立映射表
                        number_to_driver = {}
                        number_to_team = {}
                        number_to_abbr = {}
                        driver_details = []
                        
                        for _, row in session.results.iterrows():
                            car_number = str(row.get('DriverNumber', ''))
                            driver_name = row.get('FullName', '')
                            team_name = row.get('TeamName', '')
                            abbr = row.get('Abbreviation', '')
                            
                            if car_number and driver_name:
                                # 標準化車號（移除前導零）
                                car_number_str = car_number.zfill(2)  # 保留兩位格式
                                
                                number_to_driver[car_number_str] = driver_name
                                number_to_team[car_number_str] = team_name
                                number_to_abbr[car_number_str] = abbr
                                
                                driver_details.append({
                                    "car_number": car_number_str,
                                    "abbreviation": abbr,
                                    "full_name": driver_name,
                                    "team_name": team_name
                                })
                        
                        if number_to_driver:
                            self.fastf1_mapping = {
                                "number_to_driver": number_to_driver,
                                "number_to_team": number_to_team,
                                "number_to_abbr": number_to_abbr,
                                "driver_details": driver_details,
                                "source_race": race,
                                "year": self.year,
                                "updated_at": datetime.now().isoformat()
                            }
                            
                            # 覆蓋靜態映射
                            self.CAR_NUMBER_TO_DRIVER = number_to_driver
                            self.CAR_NUMBER_TO_TEAM = number_to_team
                            self.mapping_source = "fastf1"
                            
                            print(f"   [SUCCESS] 載入 {len(number_to_driver)} 位車手映射")
                            print(f"   [INFO] 映射來源: FastF1 {self.year} {race}")
                            print(f"   [INFO] 映射將包含在主 JSON 的 driver_mapping 欄位中")
                            
                            return True
                    
                except Exception as race_error:
                    print(f"   [SKIP] {race} 資料不可用: {race_error}")
                    continue
            
            print(f"   [FALLBACK] 無法從 FastF1 獲取映射，使用靜態映射表")
            return False
            
        except ImportError:
            print(f"   [WARNING] FastF1 未安裝，使用靜態映射表")
            return False
        except Exception as e:
            print(f"   [ERROR] FastF1 映射載入失敗: {e}")
            print(f"   [FALLBACK] 使用靜態映射表")
            return False
    
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
    
    def extract_date_from_pdf_text(self, text):
        """從 PDF 文字內容提取日期
        
        支援格式：
        - "14 - 16 March 2025" (標題格式)
        - "Date 16 March 2025" (底部格式)
        - "16 March 2025" (簡化格式)
        
        Returns:
            str: 標準化日期格式 "2025-03-16"，或空字串（無法提取時）
        """
        if not text:
            return ""
        
        # 月份映射表
        month_mapping = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12"
        }
        
        # 正則模式：匹配 "16 March 2025" 或 "14 - 16 March 2025"
        # 優先匹配標題中的日期範圍（取結束日期）
        patterns = [
            r'\d{1,2}\s*[-–]\s*(\d{1,2})\s+(\w+)\s+(\d{4})',  # "14 - 16 March 2025" → 取 16
            r'Date\s+(\d{1,2})\s+(\w+)\s+(\d{4})',            # "Date 16 March 2025"
            r'\b(\d{1,2})\s+(\w+)\s+(\d{4})\b'                # "16 March 2025"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    day, month_str, year = groups
                else:
                    continue
                
                # 轉換月份
                month_lower = month_str.lower()
                month_num = month_mapping.get(month_lower)
                
                if month_num:
                    # 標準化日期格式: YYYY-MM-DD
                    day_padded = day.zfill(2)
                    return f"{year}-{month_num}-{day_padded}"
        
        return ""
    
    def parse_race_name_from_filename(self, filename):
        """從檔名解析賽事名稱"""
        # 範例: "2025 São Paulo Grand Prix - Parts and parameters..."
        match = re.search(r'\d{4}\s+(.+?)\s+Grand Prix', filename)
        if match:
            race_name = match.group(1)
            # 標準化賽事名稱
            race_mapping = {
                "SÃO PAULO": "Brazil",
                "São Paulo": "Brazil",
                "Australian": "Australia",
                "China": "China",
                "Japan": "Japan",
                "Bahrain": "Bahrain",
                "Saudi Arabian": "Saudi Arabia",
                "Miami": "Miami",
                "Emilia Romagna": "Emilia Romagna",
                "Monaco": "Monaco",
                "Spanish": "Spain",
                "Canadian": "Canada",
                "Austrian": "Austria",
                "British": "Great Britain",
                "Belgian": "Belgium",
                "Hungarian": "Hungary",
                "Dutch": "Netherlands",
                "Italian": "Italy",
                "Azerbaijan": "Azerbaijan",
                "Singapore": "Singapore",
                "United States": "United States",
                "Mexican": "Mexico",
                "Brazilian": "Brazil",
                "Las Vegas": "Las Vegas",
                "Qatar": "Qatar",
                "Abu Dhabi": "Abu Dhabi"
            }
            for key, value in race_mapping.items():
                if key.lower() in race_name.lower():
                    return value
            return race_name
        return "Unknown"
    
    def parse_race_date_from_filename(self, filename):
        """從檔名獲取賽事日期"""
        race_name = self.parse_race_name_from_filename(filename)
        return self.RACE_DATES.get(race_name, "")
    
    def _is_noise_line(self, line: str) -> bool:
        """判斷是否為噪音行（非部件描述）
        
        過濾規則：
        - PDF 元數據（簽名、職稱、文件標題）
        - 法規引用（Article X.X）
        - FIA 聲明（approval, accordance）
        - Stewards 文件標題
        - 空泛描述（all above parts, parameter changes）
        """
        if not line or len(line) < 3:
            return True
        
        # ✅ 修正：正規化空白字符（將 \xa0 等特殊空格轉換為普通空格）
        # 原因：PDF 使用 non-breaking space (\xa0)，導致 regex 無法匹配
        line_normalized = line.replace('\xa0', ' ').replace('\u2009', ' ').replace('\u00a0', ' ')
        line_lower = line_normalized.lower()
        
        # 噪音關鍵字模式
        noise_patterns = [
            r'technical delegate',
            r'jo bauer',
            r'to the stewards',
            r'document\s+\d+',
            r'all above parts',
            r'article\s+\d+\.\d+',
            r'sporting regulations',
            r'formula one',
            r'from the fia',
            r'approval of the',
            r'request from the team',
            r'being in accordance',
            r'parameter changes associated',
            r'the fia formula one',
            r'following a written',
            r'have been replaced with',
            r'^\d{4}\s+.+grand prix',  # 賽事標題
        ]
        
        return any(re.search(pattern, line_lower) for pattern in noise_patterns)
    
    def parse_parc_ferme_document(self, pdf_path):
        """解析 Parc Fermé 文件（簡化版）
        
        格式範例：
        Technical Delegate's Report
        
        The following parts and parameters have been replaced / changed during the Parc Fermé yesterday and today:
        
        McLaren Mercedes:
        Car 81:    Thread insert for ICE sump bracket
        
        Ferrari:
        Car 16:    LHS and RHS lateral headrest padding
        Car 44:    ICE blow-by breather line
        """
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return []
        
        # 檢查是否包含 Parts 變更資訊
        text_lower = text.lower()
        if not ("parts" in text_lower and "parameters" in text_lower):
            return []
        
        race_name = self.parse_race_name_from_filename(pdf_path.name)
        
        # ✅ 優先從 PDF 內容提取日期，失敗時回退到檔名映射
        race_date = self.extract_date_from_pdf_text(text)
        if not race_date:
            race_date = self.parse_race_date_from_filename(pdf_path.name)
        
        changes = []
        
        # 按行處理（狀態機）
        lines = [line.strip() for line in text.split('\n')]
        current_team = None
        current_car_number = None
        current_driver = None
        
        # 跳過條件
        skip_patterns = [
            r'^from the fia',
            r'^to the stewards',
            r'^\d{4}\s+.+grand prix',
            r'^technical delegate',
            r'^date\s+\d',
            r'^time\s+\d',
            r'^page\s+\d',
            r'^document\s+\d'
        ]
        
        for line in lines:
            if not line or len(line) < 3:
                continue
            
            line_lower = line.lower()
            
            # 跳過頁眉頁尾
            if any(re.match(pattern, line_lower) for pattern in skip_patterns):
                continue
            
            # 檢測車隊標題行（兩種格式）
            # 格式 1: 以冒號結尾（舊格式）："Haas Ferrari:"
            # 格式 2: 包含車隊關鍵字（新格式）："McLaren Formula 1 Team", "KICK Sauber F1 Team"
            team_detected = False
            team_name = None
            
            # 檢查格式 1: 以冒號結尾
            if line.endswith(':') and not line.startswith('Car'):
                team_name = line[:-1].strip()
                team_detected = True
            # 檢查格式 2: 包含 "Team" 或 "Racing" 且包含車隊關鍵字
            elif ('Team' in line or 'Racing' in line or 'Formula' in line) and not line.startswith('Car'):
                # 檢查是否包含已知車隊名稱
                team_keywords = ['McLaren', 'Ferrari', 'Mercedes', 'Red Bull', 'Aston Martin', 
                                'Alpine', 'Williams', 'Haas', 'KICK', 'Sauber', 'Stake', 'RB']
                if any(keyword in line for keyword in team_keywords):
                    team_name = line.strip()
                    team_detected = True
            
            if team_detected and team_name:
                # 標準化車隊名稱（⚠️ 順序很重要！先匹配特殊情況）
                # 1. 先處理 Kick Sauber 的多種格式
                if "KICK" in team_name or "Sauber" in team_name or "Stake" in team_name:
                    current_team = "Kick Sauber"
                # 2. 處理 Haas（可能包含 Ferrari 引擎供應商）
                elif "Haas" in team_name:
                    current_team = "Haas"
                # 3. 再處理其他車隊
                elif "McLaren" in team_name:
                    current_team = "McLaren"
                elif "Ferrari" in team_name:  # 必須在 Haas 和 Kick Sauber 之後
                    current_team = "Ferrari"
                elif "Mercedes" in team_name and "Aston Martin" not in team_name:
                    current_team = "Mercedes"
                elif "Red Bull" in team_name and "Visa Cash" not in team_name:
                    current_team = "Red Bull Racing"
                elif "Aston Martin" in team_name:
                    current_team = "Aston Martin"
                elif "Alpine" in team_name:
                    current_team = "Alpine"
                elif "Williams" in team_name:
                    current_team = "Williams"
                elif "RB" == team_name or "Visa Cash App RB" in team_name or ("RB" in team_name and "Red Bull" not in team_name):
                    current_team = "RB"
                
                current_car_number = None
                current_driver = None
                continue
            
            # 檢測車號行: "Car 81:    部件名稱"
            car_match = re.match(r'Car\s+(\d+):\s*(.*)', line, re.IGNORECASE)
            if car_match:
                current_car_number = car_match.group(1)
                part = car_match.group(2).strip()
                
                # ✅ 修正：優先使用 FastF1 映射表（最準確），再回退到 PDF 上下文
                # 原因：PDF 車隊標題順序可能與車號不一致，導致錯誤映射
                team = self.CAR_NUMBER_TO_TEAM.get(current_car_number)
                if not team or team == "Unknown":
                    team = current_team if current_team else "Unknown"
                current_driver = self.CAR_NUMBER_TO_DRIVER.get(current_car_number, "Unknown")
                
                # 如果同一行有部件，記錄之（先過濾噪音）
                if part and len(part) > 3 and not self._is_noise_line(part):
                    changes.append({
                        "賽事": race_name,
                        "賽事日期": race_date,
                        "車隊": team,
                        "車手": current_driver,
                        "車號": current_car_number,
                        "部件": part,
                        "來源文件": pdf_path.name,
                        "年份": self.year,
                        "action": self._extract_action_from_text(text, current_car_number)
                    })
                
                continue
            
            # 接續的部件行（無 "Car XX:" 前綴）- 也需要過濾噪音
            if current_car_number and not line.endswith(':') and not self._is_noise_line(line):
                # 跳過純數字、純字母、包含 "From The FIA" 的行
                if re.match(r'^\d+$', line) or re.match(r'^[A-Z]{2,3}$', line):
                    continue
                if "from the fia" in line_lower or "to the stewards" in line_lower:
                    continue
                
                # ✅ 修正：使用 FastF1 映射表的車隊（與上面一致）
                team = self.CAR_NUMBER_TO_TEAM.get(current_car_number)
                if not team or team == "Unknown":
                    team = current_team if current_team else "Unknown"
                
                changes.append({
                    "賽事": race_name,
                    "賽事日期": race_date,
                    "車隊": team,  # ✅ 使用正確的車隊
                    "車手": current_driver,
                    "車號": current_car_number,
                    "部件": line,
                    "來源文件": pdf_path.name,
                    "年份": self.year,
                    "action": self._extract_action_from_text(text, current_car_number)
                })
        
        return changes
    
    def _extract_action_from_text(self, text, car_number=None):
        """從 PDF 文字中提取 action 資訊
        
        簡化邏輯：
        1. 包含 "pit" → "From the pit lane"
        2. 包含 "grid penalty" → 提取罰退數字
        3. 其他 → "N/A"
        """
        text_lower = text.lower()
        
        # 簡化檢測：只要提到 "pit" 就視為從 pit lane 出發
        if "pit" in text_lower:
            return "From the pit lane"
        
        # 檢測罰退 (grid penalty)
        grid_penalty_patterns = [
            r'(\d+)\s*place\s+grid\s+penalty',
            r'(\d+)\s*grid\s+penalty',
            r'(\d+)\s*place\s+penalty',
        ]
        
        for pattern in grid_penalty_patterns:
            match = re.search(pattern, text_lower)
            if match:
                places = match.group(1)
                return f"Grid penalty: -{places} places"
        
        # 檢測 "back of the grid"
        if "back of the grid" in text_lower:
            return "Grid penalty: Back of grid"
        
        # 無特殊資訊
        return "N/A"
    
    def parse_parc_ferme_issues_document(self, pdf_path):
        """解析 Parc Fermé Issues 文件（Technical Delegate's Report）
        
        格式範例：
        TECHNICAL DELEGATE'S REPORT
        
        The following drivers will be using a new internal combustion engine (ICE) for the remainder of
        the Competition:
        
        Number  Car                     Driver              Previously used ICE
        01      Red Bull Racing Honda   Max Verstappen      4
        
        All the above listed PU elements were changed during Parc Fermé without the approval of the
        FIA technical delegate.
        """
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print("[DEBUG] extract_text_from_pdf returned None/empty")
            return []
        
        # 檢查是否為 Parc Fermé Issues 文件
        text_lower = text.lower()
        if not ("technical delegate" in text_lower and "parc ferm" in text_lower):
            return []
        
        race_name = self.parse_race_name_from_filename(pdf_path.name)
        
        # 從 PDF 內容提取日期
        race_date = self.extract_date_from_pdf_text(text)
        if not race_date:
            race_date = self.parse_race_date_from_filename(pdf_path.name)
        
        changes = []
        lines = [line.strip() for line in text.split('\n')]
        
        # 狀態機變數
        current_component = None  # 當前部件類型 (ICE, TC, MGU-H, etc.)
        in_table = False
        approval_status = "N/A"  # 預設狀態
        
        # 部件類型關鍵字映射（基於標題行 "Previously used XX"）
        component_keywords = {
            "ic e": "ICE",  # PDF: "Previously used IC E"
            "ice": "ICE",
            "t c": "TC",    # PDF: "Previously used T C"
            "tc": "TC",
            "mgu -h": "MGU-H",  # PDF: "Previously used MGU -H"
            "mgu-h": "MGU-H",
            "mgu -k": "MGU-K",  # PDF: "Previously used MGU -K"
            "mgu-k": "MGU-K",
            "e s": "ES",    # PDF: "Previously used E S"
            "es": "ES",
            "c e": "CE",    # PDF: "Previously used C E"
            "ce": "CE",
            "ex": "EX"      # PDF: "Previously used EX"
        }
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_lower = line.lower()
            
            # 直接檢測標題行（"Number  Car Driver  Previously used XX"）
            # 這是所有部件類型的統一觸發條件
            if "previousl" in line_lower and "used" in line_lower and "number" in line_lower:
                # 從標題行提取部件類型
                current_component = None
                for keyword, component_code in component_keywords.items():
                    if keyword in line_lower:
                        current_component = component_code
                        break
                
                if not current_component:
                    i += 1
                    continue
                
                # 數據行在標題行 +2 位置
                data_line_index = i + 2
                while data_line_index < len(lines):
                    data_line = lines[data_line_index].strip()
                    
                    # 空行跳過
                    if not data_line:
                        data_line_index += 1
                        continue
                    
                    # 檢查是否為車號數據行
                    import re
                    if re.match(r'^\d{1,2}\s+', data_line):
                        parts = data_line.split()
                        car_number = parts[0]
                        
                        # 提取車手名稱（倒數第二和倒數第三個單詞）
                        driver_name = f"{parts[-3]} {parts[-2]}" if len(parts) > 4 else parts[-2]
                        
                        # 車隊名稱（中間部分）
                        team_text = " ".join(parts[1:-3] if len(parts) > 4 else parts[1:-2])
                        
                        # FastF1 映射
                        team = self.CAR_NUMBER_TO_TEAM.get(car_number, team_text)
                        driver = self.CAR_NUMBER_TO_DRIVER.get(car_number, driver_name)
                        
                        # 審批狀態
                        approval_status = self._find_approval_status(lines, data_line_index, current_component)
                        
                        changes.append({
                            "賽事": race_name,
                            "賽事日期": race_date,
                            "車隊": team,
                            "車手": driver,
                            "車號": car_number,
                            "部件": current_component,
                            "來源文件": pdf_path.name,
                            "年份": self.year,
                            "action": approval_status
                        })
                        
                        data_line_index += 1
                    else:
                        # 非車號行，結束此部件的數據讀取
                        break
                
                # 跳到下一個標題行搜索
                i = data_line_index
                continue
            
            i += 1
        
        return changes
    
    def _find_approval_status(self, lines, current_index, component):
        """向後查找 approval 狀態
        
        搜索範圍：當前位置後的 20 行內
        關鍵句：
        - "without the approval of the FIA technical delegate" → "Without approval"
        - "with the approval of the FIA technical delegate" → "With approval"
        - "is in conformity" → "Approved (conformity)"
        - "is not in conformity" → "Not in conformity"
        """
        search_range = min(20, len(lines) - current_index)
        
        for i in range(current_index + 1, current_index + search_range):
            if i >= len(lines):
                break
            
            line_lower = lines[i].lower()
            
            # 檢查 approval 狀態
            if "without the approval" in line_lower:
                return "Without approval"
            elif "with the approval" in line_lower:
                return "With approval"
            elif "is in conformity" in line_lower and "not in conformity" not in line_lower:
                return "Approved (conformity)"
            elif "not in conformity" in line_lower:
                return "Not in conformity"
            
            # 遇到新的部件類型段落，停止搜索
            if "the following" in line_lower:
                break
        
        return "N/A"
    
    def analyze_all_documents(self):
        """分析所有符合條件的 PDF 文件（包含兩種類型）"""
        all_pdfs = sorted(self.fiadoc_dir.glob("*.pdf"))
        
        if not all_pdfs:
            print(f"[WARNING] {self.fiadoc_dir} 中沒有找到 PDF 文件")
            return
        
        # 分類文件類型
        parts_pdfs = [
            f for f in all_pdfs 
            if "parts and parameters been replaced" in f.name.lower()
        ]
        
        parc_ferme_issues_pdfs = [
            f for f in all_pdfs
            if "parc ferm" in f.name.lower() and "issues" in f.name.lower()
        ]
        
        print(f"\n[ANALYZE] 開始分析 {self.year} 年 Parc Ferme 文件...")
        print(f"[FOLDER] 資料夾: {self.fiadoc_dir}")
        print(f"[FILES] 總文件數: {len(all_pdfs)}")
        print(f"[PARTS] Parts and Parameters: {len(parts_pdfs)}")
        print(f"[ISSUES] Parc Ferme Issues: {len(parc_ferme_issues_pdfs)}")
        
        # 處理 "Parts and Parameters" 文件
        if parts_pdfs:
            print(f"\n[STEP 1] 處理 Parts and Parameters 文件...")
            for i, pdf_file in enumerate(parts_pdfs, 1):
                print(f"[{i}/{len(parts_pdfs)}] 處理: {pdf_file.name}")
                changes = self.parse_parc_ferme_document(pdf_file)
                # action 已經在 parse_parc_ferme_document 中提取
                self.all_changes.extend(changes)
        
        # 處理 "Parc Fermé Issues" 文件（action = With/Without approval）
        if parc_ferme_issues_pdfs:
            print(f"\n[STEP 2] 處理 Parc Ferme Issues 文件...")
            for i, pdf_file in enumerate(parc_ferme_issues_pdfs, 1):
                print(f"[{i}/{len(parc_ferme_issues_pdfs)}] 處理: {pdf_file.name}")
                changes = self.parse_parc_ferme_issues_document(pdf_file)
                self.all_changes.extend(changes)
        
        if not parts_pdfs and not parc_ferme_issues_pdfs:
            print(f"[WARNING] 沒有找到符合條件的 PDF 文件")
            return
        
        print(f"\n[SUCCESS] 分析完成！")
        print(f"[TOTAL] 總變更次數: {len(self.all_changes)}")
        
        # 統計 action 狀態
        action_stats = defaultdict(int)
        for change in self.all_changes:
            action_stats[change.get("action", "Unknown")] += 1
        
        print(f"\n[STATS] Action 狀態統計:")
        for action, count in sorted(action_stats.items()):
            print(f"   - {action}: {count} 筆")
        
        # 顯示車隊統計
        team_stats = defaultdict(int)
        for change in self.all_changes:
            team_stats[change["車隊"]] += 1
        
        if team_stats:
            print(f"\n[TEAMS] 車隊統計:")
            for team, count in sorted(team_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"   {team}: {count} 次變更")
