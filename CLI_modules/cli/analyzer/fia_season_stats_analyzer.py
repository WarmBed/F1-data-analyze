#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIA 賽季統計分析器 (F143)
從 FIA 官網抓取 PU 元件使用狀況與部件更換記錄
支援增量更新，輸出完整賽季 JSON

使用方式:
    python f1_analysis_modular_main.py -f 143 -y 2025
"""

import sys
import json
import re
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

try:
    import requests
    import pdfplumber
except ImportError as e:
    print(f"[F143] 缺少必要套件: {e}")
    print("[F143] 請執行: pip install requests pdfplumber")

# =============================================================================
# 智能刷新配置
# =============================================================================

FIA_STATS_REFRESH_HOURS = 24  # 預設 24 小時刷新間隔
FIA_STATS_POST_RACE_REFRESH_HOURS = 4  # 賽後 4 小時內強制刷新
FIA_STATS_POST_RACE_WINDOW_HOURS = 72  # 賽後監控窗口 72 小時
JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")


# =============================================================================
# 智能刷新檢查
# =============================================================================

def check_fia_stats_freshness(year: int) -> Dict[str, Any]:
    """
    檢查 FIA 賽季統計 JSON 的新鮮度
    
    Args:
        year: 賽季年份
        
    Returns:
        包含檢查結果的字典
    """
    json_dir = Path(JSON_OUTPUT_DIR)
    json_path = json_dir / f"fia_season_stats_{year}.json"
    
    if not json_path.exists():
        return {
            "exists": False,
            "path": None,
            "age_hours": None,
            "is_fresh": False,
            "should_regenerate": True,
            "reason": f"JSON 檔案不存在: {json_path}"
        }
    
    # 計算檔案年齡
    file_mtime = datetime.fromtimestamp(json_path.stat().st_mtime)
    age = datetime.now() - file_mtime
    age_hours = age.total_seconds() / 3600
    
    # 檢查最近賽事
    race_config = _get_race_config(year)
    now = datetime.now()
    
    # 找出最近完成的賽事
    recent_race = None
    for race in race_config:
        race_date = datetime.strptime(race["date"], "%Y-%m-%d")
        if race_date < now:
            recent_race = race
    
    # 賽後監控邏輯
    if recent_race:
        race_date = datetime.strptime(recent_race["date"], "%Y-%m-%d")
        hours_since_race = (now - race_date).total_seconds() / 3600
        
        # 賽後 72 小時內，使用更短的刷新間隔
        if hours_since_race < FIA_STATS_POST_RACE_WINDOW_HOURS:
            refresh_interval = FIA_STATS_POST_RACE_REFRESH_HOURS
            reason_prefix = f"賽後監控模式 ({recent_race['name']})"
        else:
            refresh_interval = FIA_STATS_REFRESH_HOURS
            reason_prefix = "常規模式"
    else:
        refresh_interval = FIA_STATS_REFRESH_HOURS
        reason_prefix = "常規模式"
    
    is_fresh = age_hours < refresh_interval
    
    return {
        "exists": True,
        "path": str(json_path),
        "age_hours": round(age_hours, 2),
        "refresh_interval_hours": refresh_interval,
        "is_fresh": is_fresh,
        "should_regenerate": not is_fresh,
        "reason": f"{reason_prefix}: 檔案年齡 {age_hours:.1f} 小時, 刷新間隔 {refresh_interval} 小時",
        "recent_race": recent_race["name"] if recent_race else None,
    }


def _get_race_config(year: int) -> List[Dict]:
    """獲取指定年份的賽事配置"""
    if year == 2025:
        return RACE_CONFIG_2025
    elif year == 2024:
        return RACE_CONFIG_2024
    elif year == 2023:
        return RACE_CONFIG_2023
    else:
        return RACE_CONFIG_2025  # 預設使用 2025 配置


# =============================================================================
# 賽季配置
# =============================================================================

RACE_CONFIG_2025 = [
    {"round": 1, "name": "Australia", "slug": "australian", "date": "2025-03-16"},
    {"round": 2, "name": "China", "slug": "chinese", "date": "2025-03-23"},
    {"round": 3, "name": "Japan", "slug": "japanese", "date": "2025-04-06"},
    {"round": 4, "name": "Bahrain", "slug": "bahrain", "date": "2025-04-13"},
    {"round": 5, "name": "Saudi Arabia", "slug": "saudi_arabian", "date": "2025-04-20"},
    {"round": 6, "name": "Miami", "slug": "miami", "date": "2025-05-04"},
    {"round": 7, "name": "Emilia Romagna", "slug": "emilia_romagna", "date": "2025-05-18"},
    {"round": 8, "name": "Monaco", "slug": "monaco", "date": "2025-05-25"},
    {"round": 9, "name": "Spain", "slug": "spanish", "date": "2025-06-01"},
    {"round": 10, "name": "Canada", "slug": "canadian", "date": "2025-06-15"},
    {"round": 11, "name": "Austria", "slug": "austrian", "date": "2025-06-29"},
    {"round": 12, "name": "Great Britain", "slug": "british", "date": "2025-07-06"},
    {"round": 13, "name": "Belgium", "slug": "belgian", "date": "2025-07-27"},
    {"round": 14, "name": "Hungary", "slug": "hungarian", "date": "2025-08-03"},
    {"round": 15, "name": "Netherlands", "slug": "dutch", "date": "2025-08-31"},
    {"round": 16, "name": "Italy", "slug": "italian", "date": "2025-09-07"},
    {"round": 17, "name": "Azerbaijan", "slug": "azerbaijan", "date": "2025-09-21"},
    {"round": 18, "name": "Singapore", "slug": "singapore", "date": "2025-10-05"},
    {"round": 19, "name": "United States", "slug": "united_states", "date": "2025-10-19"},
    {"round": 20, "name": "Mexico", "slug": "mexico_city", "date": "2025-10-26"},
    {"round": 21, "name": "Brazil", "slug": "sao_paulo", "date": "2025-11-09"},
    {"round": 22, "name": "Las Vegas", "slug": "las_vegas", "date": "2025-11-22"},
    {"round": 23, "name": "Qatar", "slug": "qatar", "date": "2025-11-30"},
    {"round": 24, "name": "Abu Dhabi", "slug": "abu_dhabi", "date": "2025-12-07"},
]

RACE_CONFIG_2024 = [
    {"round": 1, "name": "Bahrain", "slug": "bahrain", "date": "2024-03-02"},
    {"round": 2, "name": "Saudi Arabia", "slug": "saudi_arabian", "date": "2024-03-09"},
    {"round": 3, "name": "Australia", "slug": "australian", "date": "2024-03-24"},
    {"round": 4, "name": "Japan", "slug": "japanese", "date": "2024-04-07"},
    {"round": 5, "name": "China", "slug": "chinese", "date": "2024-04-21"},
    {"round": 6, "name": "Miami", "slug": "miami", "date": "2024-05-05"},
    {"round": 7, "name": "Emilia Romagna", "slug": "emilia_romagna", "date": "2024-05-19"},
    {"round": 8, "name": "Monaco", "slug": "monaco", "date": "2024-05-26"},
    {"round": 9, "name": "Canada", "slug": "canadian", "date": "2024-06-09"},
    {"round": 10, "name": "Spain", "slug": "spanish", "date": "2024-06-23"},
    {"round": 11, "name": "Austria", "slug": "austrian", "date": "2024-06-30"},
    {"round": 12, "name": "Great Britain", "slug": "british", "date": "2024-07-07"},
    {"round": 13, "name": "Hungary", "slug": "hungarian", "date": "2024-07-21"},
    {"round": 14, "name": "Belgium", "slug": "belgian", "date": "2024-07-28"},
    {"round": 15, "name": "Netherlands", "slug": "dutch", "date": "2024-08-25"},
    {"round": 16, "name": "Italy", "slug": "italian", "date": "2024-09-01"},
    {"round": 17, "name": "Azerbaijan", "slug": "azerbaijan", "date": "2024-09-15"},
    {"round": 18, "name": "Singapore", "slug": "singapore", "date": "2024-09-22"},
    {"round": 19, "name": "United States", "slug": "united_states", "date": "2024-10-20"},
    {"round": 20, "name": "Mexico", "slug": "mexico_city", "date": "2024-10-27"},
    {"round": 21, "name": "Brazil", "slug": "sao_paulo", "date": "2024-11-03"},
    {"round": 22, "name": "Las Vegas", "slug": "las_vegas", "date": "2024-11-23"},
    {"round": 23, "name": "Qatar", "slug": "qatar", "date": "2024-12-01"},
    {"round": 24, "name": "Abu Dhabi", "slug": "abu_dhabi", "date": "2024-12-08"},
]

RACE_CONFIG_2023 = [
    {"round": 1, "name": "Bahrain", "slug": "bahrain", "date": "2023-03-05"},
    {"round": 2, "name": "Saudi Arabia", "slug": "saudi_arabian", "date": "2023-03-19"},
    {"round": 3, "name": "Australia", "slug": "australian", "date": "2023-04-02"},
    {"round": 4, "name": "Azerbaijan", "slug": "azerbaijan", "date": "2023-04-30"},
    {"round": 5, "name": "Miami", "slug": "miami", "date": "2023-05-07"},
    {"round": 6, "name": "Monaco", "slug": "monaco", "date": "2023-05-28"},
    {"round": 7, "name": "Spain", "slug": "spanish", "date": "2023-06-04"},
    {"round": 8, "name": "Canada", "slug": "canadian", "date": "2023-06-18"},
    {"round": 9, "name": "Austria", "slug": "austrian", "date": "2023-07-02"},
    {"round": 10, "name": "Great Britain", "slug": "british", "date": "2023-07-09"},
    {"round": 11, "name": "Hungary", "slug": "hungarian", "date": "2023-07-23"},
    {"round": 12, "name": "Belgium", "slug": "belgian", "date": "2023-07-30"},
    {"round": 13, "name": "Netherlands", "slug": "dutch", "date": "2023-08-27"},
    {"round": 14, "name": "Italy", "slug": "italian", "date": "2023-09-03"},
    {"round": 15, "name": "Singapore", "slug": "singapore", "date": "2023-09-17"},
    {"round": 16, "name": "Japan", "slug": "japanese", "date": "2023-09-24"},
    {"round": 17, "name": "Qatar", "slug": "qatar", "date": "2023-10-08"},
    {"round": 18, "name": "United States", "slug": "united_states", "date": "2023-10-22"},
    {"round": 19, "name": "Mexico", "slug": "mexico_city", "date": "2023-10-29"},
    {"round": 20, "name": "Brazil", "slug": "sao_paulo", "date": "2023-11-05"},
    {"round": 21, "name": "Las Vegas", "slug": "las_vegas", "date": "2023-11-18"},
    {"round": 22, "name": "Abu Dhabi", "slug": "abu_dhabi", "date": "2023-11-26"},
]

# 車手資訊對應表
DRIVER_META_2025 = {
    "1": {"code": "VER", "name": "Max Verstappen", "team": "Red Bull Racing"},
    "4": {"code": "NOR", "name": "Lando Norris", "team": "McLaren"},
    "5": {"code": "BOR", "name": "Gabriel Bortoleto", "team": "Kick Sauber"},
    "6": {"code": "HAD", "name": "Isack Hadjar", "team": "RB"},
    "7": {"code": "DOO", "name": "Jack Doohan", "team": "Alpine"},
    "10": {"code": "GAS", "name": "Pierre Gasly", "team": "Alpine"},
    "12": {"code": "ANT", "name": "Andrea Kimi Antonelli", "team": "Mercedes"},
    "14": {"code": "ALO", "name": "Fernando Alonso", "team": "Aston Martin"},
    "16": {"code": "LEC", "name": "Charles Leclerc", "team": "Ferrari"},
    "18": {"code": "STR", "name": "Lance Stroll", "team": "Aston Martin"},
    "22": {"code": "TSU", "name": "Yuki Tsunoda", "team": "RB"},
    "23": {"code": "ALB", "name": "Alexander Albon", "team": "Williams"},
    "27": {"code": "HUL", "name": "Nico Hulkenberg", "team": "Kick Sauber"},
    "30": {"code": "LAW", "name": "Liam Lawson", "team": "Red Bull Racing"},
    "31": {"code": "OCO", "name": "Esteban Ocon", "team": "Haas"},
    "44": {"code": "HAM", "name": "Lewis Hamilton", "team": "Ferrari"},
    "55": {"code": "SAI", "name": "Carlos Sainz", "team": "Williams"},
    "63": {"code": "RUS", "name": "George Russell", "team": "Mercedes"},
    "81": {"code": "PIA", "name": "Oscar Piastri", "team": "McLaren"},
    "87": {"code": "BEA", "name": "Oliver Bearman", "team": "Haas"},
}

DRIVER_META_2024 = {
    "1": {"code": "VER", "name": "Max Verstappen", "team": "Red Bull Racing"},
    "4": {"code": "NOR", "name": "Lando Norris", "team": "McLaren"},
    "10": {"code": "GAS", "name": "Pierre Gasly", "team": "Alpine"},
    "11": {"code": "PER", "name": "Sergio Perez", "team": "Red Bull Racing"},
    "14": {"code": "ALO", "name": "Fernando Alonso", "team": "Aston Martin"},
    "16": {"code": "LEC", "name": "Charles Leclerc", "team": "Ferrari"},
    "18": {"code": "STR", "name": "Lance Stroll", "team": "Aston Martin"},
    "20": {"code": "MAG", "name": "Kevin Magnussen", "team": "Haas"},
    "22": {"code": "TSU", "name": "Yuki Tsunoda", "team": "RB"},
    "23": {"code": "ALB", "name": "Alexander Albon", "team": "Williams"},
    "24": {"code": "ZHO", "name": "Zhou Guanyu", "team": "Kick Sauber"},
    "27": {"code": "HUL", "name": "Nico Hulkenberg", "team": "Haas"},
    "31": {"code": "OCO", "name": "Esteban Ocon", "team": "Alpine"},
    "44": {"code": "HAM", "name": "Lewis Hamilton", "team": "Mercedes"},
    "55": {"code": "SAI", "name": "Carlos Sainz", "team": "Ferrari"},
    "63": {"code": "RUS", "name": "George Russell", "team": "Mercedes"},
    "77": {"code": "BOT", "name": "Valtteri Bottas", "team": "Kick Sauber"},
    "81": {"code": "PIA", "name": "Oscar Piastri", "team": "McLaren"},
    "3": {"code": "RIC", "name": "Daniel Ricciardo", "team": "RB"},
    "2": {"code": "SAR", "name": "Logan Sargeant", "team": "Williams"},
    "43": {"code": "COL", "name": "Franco Colapinto", "team": "Williams"},
}

DRIVER_META_2023 = {
    "1": {"code": "VER", "name": "Max Verstappen", "team": "Red Bull Racing"},
    "4": {"code": "NOR", "name": "Lando Norris", "team": "McLaren"},
    "10": {"code": "GAS", "name": "Pierre Gasly", "team": "Alpine"},
    "11": {"code": "PER", "name": "Sergio Perez", "team": "Red Bull Racing"},
    "14": {"code": "ALO", "name": "Fernando Alonso", "team": "Aston Martin"},
    "16": {"code": "LEC", "name": "Charles Leclerc", "team": "Ferrari"},
    "18": {"code": "STR", "name": "Lance Stroll", "team": "Aston Martin"},
    "20": {"code": "MAG", "name": "Kevin Magnussen", "team": "Haas"},
    "21": {"code": "DEV", "name": "Nyck de Vries", "team": "AlphaTauri"},
    "22": {"code": "TSU", "name": "Yuki Tsunoda", "team": "AlphaTauri"},
    "23": {"code": "ALB", "name": "Alexander Albon", "team": "Williams"},
    "24": {"code": "ZHO", "name": "Zhou Guanyu", "team": "Alfa Romeo"},
    "27": {"code": "HUL", "name": "Nico Hulkenberg", "team": "Haas"},
    "31": {"code": "OCO", "name": "Esteban Ocon", "team": "Alpine"},
    "44": {"code": "HAM", "name": "Lewis Hamilton", "team": "Mercedes"},
    "55": {"code": "SAI", "name": "Carlos Sainz", "team": "Ferrari"},
    "63": {"code": "RUS", "name": "George Russell", "team": "Mercedes"},
    "77": {"code": "BOT", "name": "Valtteri Bottas", "team": "Alfa Romeo"},
    "81": {"code": "PIA", "name": "Oscar Piastri", "team": "McLaren"},
    "3": {"code": "RIC", "name": "Daniel Ricciardo", "team": "AlphaTauri"},
    "2": {"code": "SAR", "name": "Logan Sargeant", "team": "Williams"},
    "40": {"code": "LAW", "name": "Liam Lawson", "team": "AlphaTauri"},
}


# =============================================================================
# FIA 客戶端 (PDF 下載)
# =============================================================================

class FIAClient:
    """FIA 官網 PDF 抓取客戶端"""
    
    # 2025+ 新格式：https://www.fia.com/system/files/decision-document/2025_abu_dhabi_grand_prix_-_xxx.pdf
    BASE_URL_NEW = "https://www.fia.com/system/files/decision-document"
    
    # 2023-2024 舊格式：https://www.fia.com/sites/default/files/decision-document/2023%20Abu%20Dhabi%20Grand%20Prix%20-%20xxx.pdf
    BASE_URL_OLD = "https://www.fia.com/sites/default/files/decision-document"
    
    # 文件類型（根據 FIA 官網實際命名）
    DOC_TYPES_NEW = {
        # 2025+ 新格式
        "pu": "pu_elements_used_per_driver_up_to_now",
        "pu_new": "new_pu_elements_for_this_competition",
        "parts": "parts_and_parameters_been_replaced_and_or_changed_during_parc_ferme",
    }
    
    DOC_TYPES_OLD = {
        # 2023-2024 舊格式
        "pu": "PU elements used per driver up to now",
        "pu_new": "New PU elements for this Competition",
        "parts": "Parts and parameters been replaced and or changed during Parc Fermé",
    }
    
    # 賽事名稱對應（舊格式使用 Title Case）
    RACE_NAME_MAP = {
        "australian": "Australian",
        "chinese": "Chinese",
        "japanese": "Japanese",
        "bahrain": "Bahrain",
        "saudi_arabian": "Saudi Arabian",
        "miami": "Miami",
        "emilia_romagna": "Emilia Romagna",
        "monaco": "Monaco",
        "spanish": "Spanish",
        "canadian": "Canadian",
        "austrian": "Austrian",
        "british": "British",
        "belgian": "Belgian",
        "hungarian": "Hungarian",
        "dutch": "Dutch",
        "italian": "Italian",
        "azerbaijan": "Azerbaijan",
        "singapore": "Singapore",
        "united_states": "United States",
        "mexico_city": "Mexico City",
        "sao_paulo": "São Paulo",
        "las_vegas": "Las Vegas",
        "qatar": "Qatar",
        "abu_dhabi": "Abu Dhabi",
    }
    
    def __init__(self, cache_dir: str = "fia_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def _build_url_new(self, year: int, race_slug: str, doc_type: str) -> str:
        """建構 2025+ 新格式 URL"""
        doc_name = self.DOC_TYPES_NEW.get(doc_type, doc_type)
        return f"{self.BASE_URL_NEW}/{year}_{race_slug}_grand_prix_-_{doc_name}.pdf"
    
    def _build_url_old(self, year: int, race_slug: str, doc_type: str) -> str:
        """建構 2023-2024 舊格式 URL"""
        doc_name = self.DOC_TYPES_OLD.get(doc_type, doc_type)
        race_name = self.RACE_NAME_MAP.get(race_slug, race_slug.replace("_", " ").title())
        # 舊格式使用空格和 URL 編碼
        filename = f"{year} {race_name} Grand Prix - {doc_name}.pdf"
        # URL 編碼空格和特殊字符
        import urllib.parse
        encoded_filename = urllib.parse.quote(filename, safe='')
        return f"{self.BASE_URL_OLD}/{encoded_filename}"
    
    def _get_cache_path(self, year: int, race_slug: str, doc_type: str) -> Path:
        """取得本地快取路徑"""
        return self.cache_dir / f"{year}_{race_slug}_{doc_type}.pdf"
    
    def check_url_exists(self, url: str) -> bool:
        """使用 HEAD 請求檢查 URL 是否存在"""
        try:
            resp = self.session.head(url, timeout=10, allow_redirects=True)
            return resp.status_code == 200
        except Exception:
            return False
    
    def download_pdf(self, year: int, race_slug: str, doc_type: str, 
                     force: bool = False) -> Optional[Path]:
        """下載 PDF 文件（帶快取，自動選擇 URL 格式）"""
        cache_path = self._get_cache_path(year, race_slug, doc_type)
        
        # 檢查快取
        if not force and cache_path.exists():
            print(f"  [CACHE] 使用快取: {cache_path.name}")
            return cache_path
        
        # 根據年份選擇 URL 格式
        if year >= 2025:
            url = self._build_url_new(year, race_slug, doc_type)
        else:
            url = self._build_url_old(year, race_slug, doc_type)
        
        try:
            # 先用 HEAD 檢查
            if not self.check_url_exists(url):
                # 嘗試另一種格式
                if year >= 2025:
                    url = self._build_url_old(year, race_slug, doc_type)
                else:
                    url = self._build_url_new(year, race_slug, doc_type)
                
                if not self.check_url_exists(url):
                    print(f"  [SKIP] 文件不存在: {race_slug} {doc_type}")
                    return None
            
            # 下載
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            
            # 儲存
            cache_path.write_bytes(resp.content)
            print(f"  [OK] 下載成功: {cache_path.name}")
            return cache_path
            
        except requests.RequestException as e:
            print(f"  [ERROR] 下載失敗 {race_slug} {doc_type}: {e}")
            return None


# =============================================================================
# PDF 解析器
# =============================================================================

class FIAPDFParser:
    """FIA PDF 解析器（雙模態：PU + Parts）"""
    
    # PU 元件正則（車號 + 7 個數字）
    PU_PATTERN = re.compile(
        r'^(\d{1,2})\s+[\w\s]+\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
    )
    
    # PU 元件名稱
    PU_ELEMENTS = ["ICE", "TC", "MGU-H", "MGU-K", "ES", "CE", "EX"]
    
    def __init__(self, driver_meta: Dict):
        self.driver_meta = driver_meta
    
    def _normalize_car_number(self, num: str) -> str:
        """標準化車號（移除前導零）"""
        return str(int(num))
    
    def parse_pu_document(self, pdf_path: Path) -> Dict[str, Dict[str, int]]:
        """解析 PU 元件文件
        
        Returns:
            {
                "1": {"ICE": 3, "TC": 3, "MGU-H": 3, ...},
                "4": {"ICE": 2, "TC": 2, ...},
                ...
            }
        """
        result = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    
                    for line in text.split('\n'):
                        line = line.strip()
                        match = self.PU_PATTERN.match(line)
                        
                        if match:
                            car_num = self._normalize_car_number(match.group(1))
                            values = [int(match.group(i)) for i in range(2, 9)]
                            
                            result[car_num] = dict(zip(self.PU_ELEMENTS, values))
                            
        except Exception as e:
            print(f"  [ERROR] 解析 PU 文件失敗: {e}")
        
        return result
    
    def parse_parts_document(self, pdf_path: Path) -> Dict[str, List[str]]:
        """解析 Parts & Parameters 文件
        
        Returns:
            {
                "1": ["Front Wing Assembly", "Floor Edge"],
                "81": ["Thread insert for ICE sump bracket"],
                ...
            }
        """
        result = defaultdict(list)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                current_car = None
                
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    lines = [l.strip() for l in text.split('\n')]
                    
                    for line in lines:
                        if not line or len(line) < 3:
                            continue
                        
                        # 跳過標題等無關內容
                        if any(skip in line.lower() for skip in [
                            'from the fia', 'to the stewards', 'technical delegate',
                            'date', 'time', 'page', 'document', 'grand prix'
                        ]):
                            continue
                        
                        # 檢測車號行: "Car 81:" 或 "Car 1:"
                        car_match = re.match(r'Car\s+(\d+):\s*(.*)', line, re.IGNORECASE)
                        if car_match:
                            current_car = self._normalize_car_number(car_match.group(1))
                            part_on_line = car_match.group(2).strip()
                            
                            if part_on_line and len(part_on_line) > 3:
                                # 過濾 "Parameter changes associated..."
                                if not part_on_line.lower().startswith('parameter'):
                                    result[current_car].append(part_on_line)
                            continue
                        
                        # 車隊標題行（以 : 結尾，不是 Car 開頭）
                        if line.endswith(':') and not line.lower().startswith('car'):
                            continue
                        
                        # 如果有活動車號，且不是標題行，視為該車號的部件
                        if current_car and not line.endswith(':'):
                            # 跳過純數字或太短的行
                            if re.match(r'^\d+$', line) or len(line) < 4:
                                continue
                            # 過濾 "Parameter changes associated..."
                            if line.lower().startswith('parameter'):
                                continue
                            
                            result[current_car].append(line)
                            
        except Exception as e:
            print(f"  [ERROR] 解析 Parts 文件失敗: {e}")
        
        return dict(result)


# =============================================================================
# 賽季統計聚合器
# =============================================================================

class FIASeasonStatsAggregator:
    """FIA 賽季統計聚合器"""
    
    def __init__(self, year: int):
        self.year = year
        # 根據年份選擇配置
        if year >= 2025:
            self.race_config = RACE_CONFIG_2025
            self.driver_meta = DRIVER_META_2025
        elif year == 2024:
            self.race_config = RACE_CONFIG_2024
            self.driver_meta = DRIVER_META_2024
        else:  # 2023 or earlier
            self.race_config = RACE_CONFIG_2023
            self.driver_meta = DRIVER_META_2023
        
        self.client = FIAClient()
        self.parser = FIAPDFParser(self.driver_meta)
        
        # 數據存儲
        self.pu_data: Dict[str, Dict[str, Dict[str, int]]] = {}  # race -> car -> {ICE: n, ...}
        self.parts_data: Dict[str, Dict[str, List[str]]] = {}  # race -> car -> [parts]
        self.processed_races: List[str] = []
        self.failed_races: List[str] = []
    
    def _get_json_path(self) -> Path:
        """取得 JSON 輸出路徑"""
        json_dir = Path("json")
        json_dir.mkdir(exist_ok=True)
        return json_dir / f"fia_season_stats_{self.year}.json"
    
    def _load_existing_data(self) -> Optional[Dict]:
        """載入現有的 JSON 數據（增量更新用）"""
        json_path = self._get_json_path()
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] 無法載入現有數據: {e}")
        return None
    
    def _should_process_race(self, race_name: str, existing_data: Optional[Dict]) -> bool:
        """判斷是否需要處理該賽事（增量更新邏輯）"""
        if existing_data is None:
            return True
        
        processed = existing_data.get("races_processed", [])
        return race_name not in processed
    
    def _get_races_before_today(self) -> List[Dict]:
        """取得今日之前的所有賽事"""
        today = datetime.now().date()
        return [
            race for race in self.race_config
            if datetime.strptime(race["date"], "%Y-%m-%d").date() <= today
        ]
    
    def process_all_races(self, force: bool = False) -> Dict:
        """處理所有已完成的賽事
        
        Args:
            force: 是否強制重新處理所有賽事
        """
        # 載入現有數據
        existing_data = None if force else self._load_existing_data()
        
        if existing_data and not force:
            print(f"[INFO] 發現現有數據，啟用增量更新模式")
            print(f"[INFO] 已處理賽事: {len(existing_data.get('races_processed', []))} 場")
            
            # 恢復現有數據
            self.pu_data = existing_data.get("raw_pu_data", {})
            self.parts_data = existing_data.get("raw_parts_data", {})
            self.processed_races = existing_data.get("races_processed", [])
        
        # 取得需要處理的賽事
        races_to_process = self._get_races_before_today()
        print(f"\n{'='*60}")
        print(f"FIA {self.year} 賽季統計分析 (F143)")
        print(f"{'='*60}")
        print(f"賽季總場次: {len(self.race_config)}")
        print(f"已舉辦場次: {len(races_to_process)}")
        
        new_races_count = 0
        
        for race in races_to_process:
            race_name = race["name"]
            race_slug = race["slug"]
            
            # 增量更新：跳過已處理的賽事
            if not force and not self._should_process_race(race_name, existing_data):
                print(f"\n[SKIP] {race_name} - 已處理")
                continue
            
            print(f"\n[處理中] Round {race['round']}: {race_name} ({race['date']})")
            new_races_count += 1
            
            # 下載並解析 PU 文件
            pu_pdf = self.client.download_pdf(self.year, race_slug, "pu")
            if pu_pdf:
                pu_result = self.parser.parse_pu_document(pu_pdf)
                if pu_result:
                    self.pu_data[race_name] = pu_result
                    print(f"  [PU] 解析成功: {len(pu_result)} 位車手")
            
            # 下載並解析 Parts 文件
            parts_pdf = self.client.download_pdf(self.year, race_slug, "parts")
            if parts_pdf:
                parts_result = self.parser.parse_parts_document(parts_pdf)
                if parts_result:
                    self.parts_data[race_name] = parts_result
                    total_parts = sum(len(v) for v in parts_result.values())
                    print(f"  [Parts] 解析成功: {len(parts_result)} 位車手, {total_parts} 個部件")
            
            # 記錄已處理
            if race_name not in self.processed_races:
                self.processed_races.append(race_name)
        
        print(f"\n[完成] 新處理 {new_races_count} 場賽事")
        
        # 生成並保存結果
        return self._generate_output()
    
    def _aggregate_pu_totals(self) -> Dict[str, Dict[str, int]]:
        """聚合每位車手的 PU 累計使用量（取最後一場的數值）"""
        result = {}
        
        # 按賽程順序處理
        for race in self.race_config:
            race_name = race["name"]
            if race_name not in self.pu_data:
                continue
            
            for car_num, pu_counts in self.pu_data[race_name].items():
                result[car_num] = pu_counts  # 覆蓋為最新值
        
        return result
    
    def _aggregate_parts_history(self) -> Dict[str, List[Dict]]:
        """聚合每位車手的部件更換歷史"""
        result = defaultdict(list)
        
        for race in self.race_config:
            race_name = race["name"]
            if race_name not in self.parts_data:
                continue
            
            for car_num, parts_list in self.parts_data[race_name].items():
                if parts_list:
                    result[car_num].append({
                        "race": race_name,
                        "round": race["round"],
                        "date": race["date"],
                        "items": parts_list
                    })
        
        return dict(result)
    
    def _enrich_driver_data(self, car_num: str) -> Dict:
        """補充車手資訊"""
        meta = self.driver_meta.get(car_num, {})
        return {
            "number": car_num,
            "code": meta.get("code", "UNK"),
            "name": meta.get("name", "Unknown"),
            "team": meta.get("team", "Unknown"),
        }
    
    def _generate_output(self) -> Dict:
        """生成完整的 JSON 輸出"""
        pu_totals = self._aggregate_pu_totals()
        parts_history = self._aggregate_parts_history()
        
        # 合併所有車手
        all_car_nums = set(pu_totals.keys()) | set(parts_history.keys())
        
        drivers_data = {}
        for car_num in sorted(all_car_nums, key=lambda x: int(x)):
            driver_info = self._enrich_driver_data(car_num)
            driver_code = driver_info["code"]
            
            drivers_data[driver_code] = {
                **driver_info,
                "pu_elements": pu_totals.get(car_num, {}),
                "parts_changes": parts_history.get(car_num, []),
                "total_parts_changed": sum(
                    len(p["items"]) for p in parts_history.get(car_num, [])
                )
            }
        
        # 統計摘要
        total_parts_changes = sum(d["total_parts_changed"] for d in drivers_data.values())
        
        output = {
            "year": self.year,
            "last_updated": datetime.now().isoformat(),
            "total_races": len(self.race_config),
            "races_processed": sorted(self.processed_races, key=lambda x: next(
                (r["round"] for r in self.race_config if r["name"] == x), 99
            )),
            "races_count": len(self.processed_races),
            "summary": {
                "total_drivers": len(drivers_data),
                "total_parts_changes": total_parts_changes,
                "pu_penalties_risk": [
                    code for code, data in drivers_data.items()
                    if data.get("pu_elements", {}).get("ICE", 0) > 4
                ]
            },
            "drivers": drivers_data,
            # 保留原始數據（用於增量更新）
            "raw_pu_data": self.pu_data,
            "raw_parts_data": self.parts_data,
        }
        
        # 保存 JSON
        json_path = self._get_json_path()
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n[輸出] JSON 已保存: {json_path}")
        print(f"[統計] {len(drivers_data)} 位車手, {total_parts_changes} 次部件更換")
        
        return output


# =============================================================================
# 主函數（供 function_mapper 調用）
# =============================================================================

def run_fia_season_stats_analysis(year: int, force: bool = False) -> Dict[str, Any]:
    """執行 FIA 賽季統計分析 (支援智能刷新)
    
    Args:
        year: 賽季年份 (2024, 2025, ...)
        force: 是否強制重新處理所有數據
    
    Returns:
        標準化結果字典
    """
    print(f"\n{'='*60}")
    print(f"[F143] FIA 賽季統計分析")
    print(f"[F143] 年份: {year}")
    print(f"{'='*60}")
    
    # 智能刷新檢查
    if not force:
        freshness = check_fia_stats_freshness(year)
        print(f"\n[刷新檢查] {freshness['reason']}")
        
        if freshness["is_fresh"] and freshness["exists"]:
            print(f"[跳過] JSON 仍在有效期內 ({freshness['age_hours']:.1f} 小時)")
            print(f"[提示] 使用 --force 強制重新生成")
            
            # 讀取現有 JSON 返回
            try:
                with open(freshness["path"], "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                return {
                    "success": True,
                    "message": f"FIA {year} 賽季統計（從快取讀取，{freshness['age_hours']:.1f} 小時前更新）",
                    "data": existing_data,
                    "json_path": freshness["path"],
                    "from_cache": True,
                }
            except Exception as e:
                print(f"[警告] 讀取快取失敗，將重新生成: {e}")
        else:
            print(f"[更新] 需要重新生成 JSON")
    else:
        print(f"[F143] 模式: 強制重建")
    
    try:
        aggregator = FIASeasonStatsAggregator(year)
        result = aggregator.process_all_races(force=force)
        
        # 移除原始數據（API 傳輸時不需要）
        output = {k: v for k, v in result.items() if not k.startswith("raw_")}
        
        return {
            "success": True,
            "message": f"FIA {year} 賽季統計分析完成",
            "data": output,
            "json_path": str(aggregator._get_json_path()),
            "from_cache": False,
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"FIA 賽季統計分析失敗: {e}",
            "data": None,
        }


# =============================================================================
# CLI 測試入口
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FIA 賽季統計分析 (F143)")
    parser.add_argument("-y", "--year", type=int, default=2025, help="賽季年份")
    parser.add_argument("--force", action="store_true", help="強制重新處理所有數據")
    
    args = parser.parse_args()
    
    result = run_fia_season_stats_analysis(args.year, args.force)
    
    if result["success"]:
        print(f"\n[SUCCESS] {result['message']}")
        print(f"[JSON] {result['json_path']}")
    else:
        print(f"\n[FAILED] {result['message']}")
