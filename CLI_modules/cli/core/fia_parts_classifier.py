#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部件變更類型分類器 V3.0
版本：v3.0 (2025-11-08)
改進：
  1. 資料前處理規則（過濾無效行、去重、正規化）
  2. 精簡為 6 類（REPAIR, CHANGE, MAJOR_UPDATE, PARAM_ADJUST, SAFETY_STD, NOISE）
  3. 動態信心度評分（0.60-0.95+）
  4. 關鍵字權重表
  5. 新增：15 個主分類 (Main Category) + 61 個子分類 (Sub Category) 層級系統
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import re
from typing import Dict, List, Tuple


class UpgradeClassifierV2:
    """升級套件分類器 V3.0 - 完整分類層級版"""
    
    # === 15 個主分類 + 61 個子分類層級系統 ===
    CATEGORY_HIERARCHY = {
        "Aerodynamics": {
            "display_name": "空力套件",
            "sub_categories": {
                "Front Wing": ["front wing", "fw", "front wing assembly", "front wing endplate", "front wing flap"],
                "Rear Wing": ["rear wing", "rw", "rear wing assembly", "beam wing", "rear wing endplate", "rear wing flap"],
                "Floor": ["floor", "floor assembly", "floor panel", "forward floor", "floor edge", "floor body"],
                "Diffuser": ["diffuser", "rear diffuser", "floor tunnels"],
                "Sidepods": ["sidepod", "sidepod assembly", "sidepod vane", "sidepod deflector"],
                "Bargeboard": ["bargeboard", "barge board", "deflector", "vane"],
                "Engine Cover": ["engine cover", "bodywork", "rear bodywork"],
            }
        },
        "Cooling": {
            "display_name": "冷卻系統",
            "sub_categories": {
                "Radiators": ["radiator", "CAC", "charge air cooler", "oil cooler"],
                "Cooling Ducts": ["cooling duct", "cooling inlet", "cooling outlet"],
                "Cooling Pipes": ["cooling pipe", "water pipe", "coolant pipe", "return pipe"],
                "Pumps": ["pump", "water pump", "coolant pump", "lift pump"],
                "Heat Exchangers": ["heat exchanger", "intercooler"],
            }
        },
        "Suspension": {
            "display_name": "懸吊系統",
            "sub_categories": {
                "Front Suspension": ["front suspension", "front inboard", "front outboard", "front pushrod", "front pullrod"],
                "Rear Suspension": ["rear suspension", "rear inboard", "rear outboard", "rear pushrod", "rear pullrod"],
                "Wishbones": ["wishbone", "track rod", "suspension leg"],
                "Dampers": ["damper", "shock absorber", "heave damper"],
                "Anti-roll Bar": ["anti roll bar", "arb", "roll bar"],
                "Uprights": ["upright", "upright assembly"],
            }
        },
        "Powertrain": {
            "display_name": "動力單元",
            "sub_categories": {
                "ICE": ["ice", "internal combustion engine", "engine"],
                "Turbocharger": ["tc", "turbocharger", "turbo"],
                "MGU-K": ["mgu-k", "mgu k", "kinetic"],
                "MGU-H": ["mgu-h", "mgu h", "heat"],
                "Energy Store": ["es", "energy store", "battery"],
                "Control Electronics": ["ce", "control electronics", "powerbox"],
                "Exhaust": ["exhaust", "tailpipe", "exhaust pipe"],
            }
        },
        "Brakes": {
            "display_name": "煞車系統",
            "sub_categories": {
                "Brake Discs": ["brake disc", "brake drum"],
                "Brake Calipers": ["caliper", "brake caliper"],
                "Brake Ducts": ["brake duct", "brake cooling"],
                "Brake Pads": ["brake pad", "friction material"],
                "Brake Lines": ["brake line", "brake pipe"],
                "BBW": ["bbw", "brake by wire"],
            }
        },
        "Chassis": {
            "display_name": "底盤結構",
            "sub_categories": {
                "Monocoque": ["monocoque", "survival cell", "chassis"],
                "Cockpit": ["cockpit", "cockpit surround"],
                "Plank": ["plank", "skid block", "reference plane"],
                "Crash Structures": ["crash structure", "nose cone", "impact attenuator"],
            }
        },
        "Electronics": {
            "display_name": "電子系統",
            "sub_categories": {
                "ECU": ["ecu", "electronic control unit"],
                "Sensors": ["sensor", "potentiometer", "transducer"],
                "Wiring": ["wiring", "harness", "loom"],
                "Data Logger": ["data logger", "data acquisition"],
                "Cameras": ["camera", "onboard camera"],
            }
        },
        "Safety": {
            "display_name": "安全設備",
            "sub_categories": {
                "Headrest": ["headrest", "head rest"],
                "Seat Belts": ["seat belt", "harness", "crotch belt"],
                "Fire Extinguisher": ["fire extinguisher", "fire system"],
                "Roll Hoop": ["roll hoop", "roll structure"],
            }
        },
        "Hydraulics": {
            "display_name": "液壓系統",
            "sub_categories": {
                "Hydraulic Lines": ["hydraulic line", "hydraulic pipe"],
                "Hydraulic Pumps": ["hydraulic pump"],
                "Accumulators": ["accumulator", "hydraulic accumulator"],
            }
        },
        "Transmission": {
            "display_name": "變速箱",
            "sub_categories": {
                "Gearbox": ["gearbox", "gearbox assembly", "transmission"],
                "Clutch": ["clutch", "clutch assembly"],
                "Driveshafts": ["driveshaft", "drive shaft", "cv joint"],
                "Differential": ["differential", "diff"],
            }
        },
        "Steering": {
            "display_name": "轉向系統",
            "sub_categories": {
                "Steering Wheel": ["steering wheel"],
                "Steering Column": ["steering column", "steering shaft"],
                "Steering Rack": ["steering rack", "pas rack", "power steering"],
                "Steering Arms": ["steering arm", "steering linkage"],
            }
        },
        "Wheels": {
            "display_name": "輪胎與輪圈",
            "sub_categories": {
                "Wheel Rims": ["rim", "wheel rim"],
                "Wheel Nuts": ["wheel nut", "wheel retention"],
                "Tire Blankets": ["tire blanket", "tyre warmer"],
            }
        },
        "Bodywork": {
            "display_name": "車身外殼",
            "sub_categories": {
                "Nose": ["nose", "nose cone", "nose assembly"],
                "Mirrors": ["mirror", "mirror assembly"],
                "T-Tray": ["t-tray", "t tray", "bib assembly"],
                "Fairings": ["fairing", "suspension fairing"],
            }
        },
        "Fuel System": {
            "display_name": "燃油系統",
            "sub_categories": {
                "Fuel Tank": ["fuel tank", "fuel cell"],
                "Fuel Lines": ["fuel line", "fuel pipe"],
                "Fuel Pumps": ["fuel pump"],
            }
        },
        "Miscellaneous": {
            "display_name": "其他部件",
            "sub_categories": {
                "Parameter Adjustments": ["parameter", "calibration", "setting"],
                "Seals & Gaskets": ["seal", "gasket", "o-ring", "circlip"],
                "Fasteners": ["bolt", "fixing", "clip"],
                "Covers & Panels": ["cover", "panel", "hatch"],
                "Other": ["other", "miscellaneous", "various"],
            }
        },
    }
    
    # === 分類定義與關鍵字權重表 ===
    
    # === 分類定義與關鍵字權重表 ===
    CLASSIFICATIONS = {
        "PARAM_ADJUST": {
            "description": "純軟體參數變更，無硬體更換",
            "display_name": "參數調整 (Parameter Adjustment)",
            "weight": 0.95,
            "keywords": [
                (r'\bparameter\s+changes?\b', 0.95),
                (r'\bassociated\s+with\b', 0.90),
                (r'\bparameter\s+adjustment\b', 0.95),
                (r'\bcalibration\b', 0.85),
                (r'\bsoftware\s+update\b', 0.90),
                (r'\bsettings?\b', 0.75),
                (r'\btuning\b', 0.75),
                (r'\bmap\s+change\b', 0.85),
            ],
            "priority": 1  # 最高優先級（最先檢查）
        },
        
        "MAJOR_UPDATE": {
            "description": "結構性改動、觸發 FIA 重新檢驗、非全新套件",
            "display_name": "重大更新 (Major Update)",
            "weight": 0.90,
            "keywords": [
                (r'\bfloor\s+assembly\b', 0.90),
                (r'\bgearbox\s+assembly\b', 0.90),
                (r'\bchassis\b(?!.*saver)', 0.90),
                (r'\bbib\s+assembly\b', 0.85),
                (r'\bmonocoque\b', 0.95),
                (r'\bsurvival\s+cell\b', 0.95),
                (r'\bsidepod\s+assembly\b', 0.85),
                (r'\bCE\s*\(', 0.90),  # CE (powerbox, new)
                (r'\bpowerbox\b', 0.85),
            ],
            "priority": 2
        },
        
        "CHANGE": {
            "description": "Parc Fermé 內合法調整、空力/配置切換、摩擦材料、懸吊",
            "display_name": "變更 (Change)",
            "weight": 0.80,
            "keywords": [
                (r'\bduct\b', 0.75),
                (r'\bvane\b', 0.75),
                (r'\bdeflector\b', 0.75),
                (r'\bwinglet\b', 0.80),
                (r'\bblanking\b', 0.80),
                (r'\bfriction\s+material\b', 0.85),
                (r'\bsuspension\s+leg\b', 0.80),
                (r'\bsidepod\b(?!.*assembly)', 0.75),
                (r'\bwing\s+assembly\b', 0.80),
                (r'\bfront\s+wing\b', 0.80),
                (r'\brear\s+wing\b', 0.80),
                (r'\bendplate\b', 0.75),
                (r'\bflap\b', 0.75),
                (r'\bbib\s+structure\b', 0.80),
                (r'\bbib\s+tower\b', 0.80),
                (r'\bfloor\s+panel\b', 0.75),
                (r'\bforward\s+floor\b', 0.75),
                (r'\bengine\s+cover\b', 0.75),
                (r'\bcantilever\s+adjuster\b', 0.75),
                (r'\bbrake\s+pedal\b', 0.75),
                (r'\bt-tray\b', 0.80),
                (r'\bthrottle\s+pedal\b', 0.75),
                (r'\bwishbone\b', 0.75),
                (r'\boutboard\s+suspension\b', 0.75),
                (r'\binboard\s+suspension\b', 0.75),
                (r'\btransponder\s+fairing\b', 0.75),
                (r'\bbeam\s+wing\b', 0.80),
            ],
            "priority": 3
        },
        
        "SAFETY_STD": {
            "description": "FIA 標準安全設備、駕駛介面",
            "display_name": "安全/標準件 (Safety/Standard Parts)",
            "weight": 0.80,
            "keywords": [
                (r'\bsteering\s+wheel\b', 0.85),
                (r'\bheadrest\b', 0.85),
                (r'\bcrotch\s+belt\b', 0.85),
                (r'\bfire\s+extinguisher\b', 0.85),
                (r'\bsteering\s+column\b', 0.80),
                (r'\bBBW\b', 0.80),
                (r'\bFOM\s+(?:microphone|camera)\b', 0.85),
                (r'\bF1\s+MS\s+CDM\b', 0.85),
                (r'\bhelmet\s+camera\b', 0.80),
                (r'\bdriver.*harness\b', 0.75),
                (r'\bradio\s+harness\b', 0.75),
                (r'\bprotection\s+foam\b', 0.75),
                (r'\bsteering\s+rack\b', 0.80),
            ],
            "priority": 4
        },
        
        "REPAIR": {
            "description": "損壞後更換舊件/備件、小零件維護、冷卻系統管路",
            "display_name": "維修 (Repair)",
            "weight": 0.80,
            "keywords": [
                (r'\bsump\b', 0.75),
                (r'\brubber\b', 0.65),
                (r'\bpipes?\b', 0.70),
                (r'\bpump\b', 0.70),
                (r'\bPRV\b', 0.75),
                (r'\bseal\b', 0.65),
                (r'\bclip\b', 0.65),
                (r'\bdrum\b', 0.70),
                (r'\bcalipers?\b', 0.75),
                (r'\blift\b', 0.70),
                (r'\breturn\b', 0.65),
                (r'\bcooling\b', 0.70),
                (r'\bpreviously\s+used\b', 0.85),
                (r'\bdamaged\b', 0.80),
                (r'\bhose\b', 0.70),
                (r'\bsensor\b', 0.70),
                (r'\bplank\b', 0.70),
                (r'\bglass\b', 0.65),
                (r'\bcover\b', 0.65),
                (r'\btailpipe\b', 0.70),
                (r'\bexhaust\b', 0.70),
                (r'\bspark\s+plug\b', 0.75),
                (r'\bgas\s+strut\b', 0.70),
                (r'\bhatch\b', 0.65),
                (r'\bfitting\b', 0.65),
                (r'\bQD\s+fitting\b', 0.70),
                (r'\binfill\b', 0.65),
                (r'\btunnel\b', 0.65),
                (r'\bfoam\b', 0.65),
                (r'\bcorrevit\b', 0.70),
                (r'\boil\s+cooler\b', 0.75),
                (r'\bauxiliary\b', 0.70),
                (r'\bcylinder\b', 0.70),
                (r'\bfixing\b', 0.65),
                (r'\bstrut\b', 0.65),
                (r'\bgaiter\b', 0.70),
                (r'\bmirror\s+lens\b', 0.70),
                (r'\bpotentiometer\b', 0.70),
                (r'\bfilter\s+housing\b', 0.70),
                (r'\bo-ring\b', 0.65),
                (r'\bcirclip\b', 0.65),
                (r'\bwheel\s+retention\b', 0.70),
                (r'\bPAS\s+rack\b', 0.75),
                (r'\baxle\s+plug\b', 0.70),
            ],
            "priority": 5
        },
        
        "NOISE": {
            "description": "非零件描述、OCR 殘留、PDF 元數據",
            "display_name": "噪音 (Noise)",
            "weight": 0.90,
            "keywords": [
                (r'\bTo\s+The\s+Stewards\b', 0.95),
                (r'\bFrom\s+The\s+FIA\b', 0.95),
                (r'\bDocument\s+\d+\b', 0.95),
                (r'\bDate\s+\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', 0.95),
                (r'\bTime\s+\d{1,2}:\d{2}\b', 0.95),
                (r'^\s*\d+\s*$', 0.85),  # 純數字
                (r'^[A-Z\s]{50,}$', 0.80),  # 長全大寫標題
                (r'\bTechnical\s+Delegate\b', 0.90),
            ],
            "priority": 0  # 最先過濾
        }
    }
    
    # === 前處理規則 ===
    INVALID_LINE_PATTERNS = [
        r'From\s+The\s+FIA',
        r'To\s+The\s+Stewards',
        r'Document\s+\d+',
        r'Date\s+\d+',
        r'Time\s+\d{1,2}:\d{2}',
        r'^\s*Page\s+\d+',
        r'^\s*\d+\s*$',  # 純數字行
    ]
    
    def __init__(self):
        """初始化分類器"""
        # 構建反向索引：關鍵字 → (主分類, 子分類)
        self._keyword_to_category = {}
        for main_cat, main_info in self.CATEGORY_HIERARCHY.items():
            for sub_cat, keywords in main_info["sub_categories"].items():
                for keyword in keywords:
                    # 使用正規表達式模式進行匹配
                    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                    self._keyword_to_category[pattern] = (main_cat, sub_cat)
    
    def classify_part_category(self, part_name: str, original_text: str = "") -> Tuple[str, str]:
        """
        根據部件名稱分類主分類和子分類
        
        Args:
            part_name: 部件名稱
            original_text: 原始文本（可選）
        
        Returns:
            (主分類, 子分類) 元組，例如 ("Aerodynamics", "Front Wing")
        """
        # 前處理並合併文本
        part_name_clean = self.preprocess_text(part_name).lower()
        original_text_clean = self.preprocess_text(original_text).lower()
        full_text = f"{part_name_clean} {original_text_clean}"
        
        # 儲存所有匹配結果（按優先級：關鍵字長度）
        matches = []
        
        for pattern, (main_cat, sub_cat) in self._keyword_to_category.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                # 優先級：關鍵字長度（越長越精確）
                keyword_length = len(pattern)
                matches.append((keyword_length, main_cat, sub_cat))
        
        if matches:
            # 返回最長匹配（最精確）
            matches.sort(reverse=True)
            _, main_cat, sub_cat = matches[0]
            return (main_cat, sub_cat)
        
        # 無法分類：返回 Miscellaneous / Other
        return ("Miscellaneous", "Other")
    
    def preprocess_text(self, text: str) -> str:
        """
        前處理文本
        
        Args:
            text: 原始文本
        
        Returns:
            處理後的文本
        """
        # 移除無效行
        for pattern in self.INVALID_LINE_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 正規化空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 正規化 LHS/RHS
        text = re.sub(r'\bL\.?H\.?S\.?\b', 'LHS', text, flags=re.IGNORECASE)
        text = re.sub(r'\bR\.?H\.?S\.?\b', 'RHS', text, flags=re.IGNORECASE)
        
        return text
    
    def normalize_part_name(self, part_name: str) -> Tuple[str, Dict[str, any]]:
        """
        部件名稱正規化
        
        Args:
            part_name: 原始部件名稱
        
        Returns:
            (正規化後的名稱, 元數據字典)
        """
        metadata = {
            "used_part": False,
            "notes": []
        }
        
        normalized = part_name
        
        # 檢測 "previously used"
        if re.search(r'\bpreviously\s+used\b', normalized, re.IGNORECASE):
            metadata["used_part"] = True
            normalized = re.sub(r'\(?\s*previously\s+used\s*\)?', '', normalized, flags=re.IGNORECASE)
        
        # 移除括號註解並保存
        bracket_match = re.search(r'\(([^)]+)\)', normalized)
        if bracket_match:
            note = bracket_match.group(1)
            if note not in ["LHS", "RHS"]:  # 保留方向標記
                metadata["notes"].append(note)
                normalized = re.sub(r'\([^)]+\)', '', normalized)
        
        # 清理多餘空格
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized, metadata
    
    def calculate_confidence(
        self, 
        matched_keywords: List[Tuple[str, float]], 
        text_length: int,
        has_context: bool = False
    ) -> float:
        """
        計算信心度（0.60 - 0.95+）
        
        Args:
            matched_keywords: 匹配的關鍵字與權重列表
            text_length: 文本長度
            has_context: 是否有明確上下文
        
        Returns:
            信心度 (0.0 - 1.0)
        """
        if not matched_keywords:
            return 0.0
        
        # 基礎分數：最高權重關鍵字
        max_weight = max(weight for _, weight in matched_keywords)
        base_score = max_weight
        
        # 多關鍵字加成
        if len(matched_keywords) > 1:
            base_score = min(base_score + 0.05 * (len(matched_keywords) - 1), 0.99)
        
        # 上下文加成
        if has_context:
            base_score = min(base_score + 0.05, 0.99)
        
        # 文本長度懲罰（過短可能是噪音）
        if text_length < 10:
            base_score *= 0.9
        
        return round(base_score, 2)
    
    def classify_part_change(
        self, 
        part_name: str, 
        original_text: str = ""
    ) -> Dict[str, any]:
        """
        分類單一部件變更
        
        Args:
            part_name: 部件名稱
            original_text: 原始 FIA 文件文本（可選）
        
        Returns:
            {
                "變更類型": "REPAIR",
                "變更類型顯示": "維修 (Repair)",
                "類型說明": "...",
                "匹配關鍵字": ["sump", "rubber"],
                "信心度": 0.75,
                "主分類": "Cooling",
                "子分類": "Cooling Pipes",
                "元數據": {...}
            }
        """
        # 前處理
        part_name_clean = self.preprocess_text(part_name)
        original_text_clean = self.preprocess_text(original_text)
        
        # 正規化部件名稱
        normalized_name, metadata = self.normalize_part_name(part_name_clean)
        
        # 合併文本
        full_text = f"{normalized_name} {original_text_clean}".lower()
        text_length = len(full_text)
        
        # 檢測是否有上下文
        has_context = len(original_text_clean) > 20
        
        # ✨ 新增：分類主分類和子分類
        main_category, sub_category = self.classify_part_category(part_name, original_text)
        
        # 儲存所有匹配結果
        matches = []
        
        # 按優先級順序檢查
        for class_key, config in sorted(
            self.CLASSIFICATIONS.items(), 
            key=lambda x: x[1]["priority"]
        ):
            matched_keywords = []
            
            for keyword_pattern, weight in config["keywords"]:
                if re.search(keyword_pattern, full_text, re.IGNORECASE):
                    match = re.search(keyword_pattern, full_text, re.IGNORECASE)
                    if match:
                        matched_keywords.append((match.group(0), weight))
            
            if matched_keywords:
                confidence = self.calculate_confidence(
                    matched_keywords, 
                    text_length, 
                    has_context
                )
                
                # 信心度閾值過濾
                if confidence >= 0.60:
                    matches.append({
                        "變更類型": class_key,
                        "變更類型顯示": config["display_name"],
                        "類型說明": config["description"],
                        "匹配關鍵字": [kw for kw, _ in matched_keywords],
                        "信心度": confidence,
                        "優先級": config["priority"],
                        "主分類": main_category,
                        "子分類": sub_category,
                        "元數據": metadata
                    })
        
        # 返回最高優先級且信心度最高的結果
        if matches:
            # 先按優先級，再按信心度排序
            matches.sort(key=lambda x: (x["優先級"], -x["信心度"]))
            return matches[0]
        
        # 無法分類
        return {
            "變更類型": "UNCLASSIFIED",
            "變更類型顯示": "未分類 (Unclassified)",
            "類型說明": "無法根據現有規則分類（信心度低於 0.60）",
            "匹配關鍵字": [],
            "信心度": 0.0,
            "主分類": main_category,
            "子分類": sub_category,
            "元數據": metadata
        }
    
    def remove_duplicates(
        self, 
        records: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        去重邏輯
        Unique Key: 車號 + 部件 + 日期 + 來源文件
        
        Args:
            records: 原始記錄列表
        
        Returns:
            去重後的記錄列表
        """
        unique_dict = {}
        
        for record in records:
            # 構建唯一鍵
            unique_key = (
                record.get("車號", ""),
                record.get("部件", ""),
                record.get("日期", ""),
                record.get("來源文件", "")
            )
            
            # 保留頁碼最小或信心度最高者
            if unique_key not in unique_dict:
                unique_dict[unique_key] = record
            else:
                existing = unique_dict[unique_key]
                
                # 優先保留信心度高的
                if record.get("信心度", 0) > existing.get("信心度", 0):
                    unique_dict[unique_key] = record
                # 信心度相同時保留頁碼小的
                elif (record.get("信心度", 0) == existing.get("信心度", 0) and
                      record.get("頁碼", 999) < existing.get("頁碼", 999)):
                    unique_dict[unique_key] = record
        
        return list(unique_dict.values())
    
    def classify_batch(
        self, 
        upgrades: List[Dict[str, any]],
        remove_duplicates: bool = True
    ) -> List[Dict[str, any]]:
        """
        批次分類多個升級記錄
        
        Args:
            upgrades: 升級記錄列表
            remove_duplicates: 是否執行去重
        
        Returns:
            分類並去重後的記錄列表
        """
        # 去重（可選）
        if remove_duplicates:
            upgrades = self.remove_duplicates(upgrades)
        
        classified = []
        
        for upgrade in upgrades:
            part_name = upgrade.get("部件", "")
            original_text = upgrade.get("原始文本", "")
            
            # 執行分類
            classification = self.classify_part_change(part_name, original_text)
            
            # 添加分類資訊（扁平化結構）
            upgrade_with_class = upgrade.copy()
            upgrade_with_class["變更類型"] = classification["變更類型顯示"]
            upgrade_with_class["類型說明"] = classification["類型說明"]
            upgrade_with_class["匹配關鍵字"] = ", ".join(classification["匹配關鍵字"])
            upgrade_with_class["分類信心度"] = classification["信心度"]
            
            # ✨ 新增：添加主分類和子分類
            upgrade_with_class["主分類"] = classification["主分類"]
            upgrade_with_class["子分類"] = classification["子分類"]
            
            # 添加元數據標記
            if classification["元數據"]["used_part"]:
                upgrade_with_class["previously_used"] = True
            if classification["元數據"]["notes"]:
                upgrade_with_class["notes"] = "; ".join(classification["元數據"]["notes"])
            
            classified.append(upgrade_with_class)
        
        return classified
    
    def get_classification_stats(self, classified_upgrades: List[Dict[str, any]]) -> Dict[str, any]:
        """獲取分類統計"""
        from collections import Counter
        
        stats = {
            "總記錄數": len(classified_upgrades),
            "各類型統計": {},
            "平均信心度": 0.0,
            "低信心度記錄": 0
        }
        
        type_counts = Counter([r.get("變更類型", "未知") for r in classified_upgrades])
        confidences = [r.get("分類信心度", 0.0) for r in classified_upgrades]
        
        total = len(classified_upgrades)
        for change_type, count in type_counts.items():
            stats["各類型統計"][change_type] = {
                "數量": count,
                "百分比": round(count / total * 100, 2) if total > 0 else 0.0
            }
        
        stats["平均信心度"] = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        stats["低信心度記錄"] = sum(1 for c in confidences if c < 0.70)
        
        return stats


def main():
    """測試分類器 V3"""
    classifier = UpgradeClassifierV2()
    
    # 測試案例
    test_cases = [
        {
            "部件": "parameter changes associated with gearbox",
            "原始文本": "Car 04: parameter changes associated with gearbox assembly replacement"
        },
        {
            "部件": "Floor assembly (excluding skids and plank)",
            "原始文本": "Car 18: Floor assembly (excluding skids and plank)"
        },
        {
            "部件": "ICE sump rubber",
            "原始文本": "Car 04: ICE sump rubber"
        },
        {
            "部件": "LHS brake duct vane",
            "原始文本": "Car 23: LHS brake duct vane"
        },
        {
            "部件": "steering wheel",
            "原始文本": "Car 43: steering wheel"
        },
        {
            "部件": "Front wing assembly",
            "原始文本": "Car 01: Front wing assembly"
        },
    ]
    
    print("\n" + "="*100)
    print("分類器 V3.0 測試報告 (含完整分類層級)")
    print("="*100)
    
    for i, test_case in enumerate(test_cases, 1):
        result = classifier.classify_part_change(
            test_case["部件"], 
            test_case["原始文本"]
        )
        
        print(f"\n測試 {i}:")
        print(f"  部件: {test_case['部件']}")
        print(f"  變更類型: {result['變更類型']} - {result['變更類型顯示']}")
        print(f"  主分類: {result['主分類']}")
        print(f"  子分類: {result['子分類']}")
        print(f"  說明: {result['類型說明']}")
        print(f"  關鍵字: {', '.join(result['匹配關鍵字']) if result['匹配關鍵字'] else '無'}")
        print(f"  信心度: {result['信心度']:.0%}")
        if result['元數據']['used_part']:
            print(f"  ⚠️  Previously Used Part")
    
    print("\n" + "="*100)
    print("✨ 新增功能:")
    print("="*100)
    print("  • 15 個主分類 (Main Category)")
    print("  • 61 個子分類 (Sub Category)")
    print("  • 自動層級映射")
    print("\n信心度評分標準:")
    print("="*100)
    print("  0.95+ = 關鍵字完全命中 + 上下文明確")
    print("  0.90  = 標準部件名稱 + 明確動詞")
    print("  0.80  = 多關鍵字命中 或 單一高權重詞")
    print("  0.70  = 單一關鍵字 + 合理上下文")
    print("  0.60  = 僅單一模糊詞")
    print("  <0.60 = 需人工審核或標為 NOISE")


if __name__ == '__main__':
    main()
