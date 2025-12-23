#!/usr/bin/env python3
"""
部件變更類型分類器
根據 FIA 技術規則和 Parc Fermé 文件內容，自動分類變更類型
"""
import re


class UpgradeClassifier:
    """升級套件分類器"""
    
    # 分類定義與關鍵字
    CLASSIFICATIONS = {
        "升級套件 (Upgrade Package)": {
            "description": "新設計、需 re-presented / re-homologated、性能提升",
            "keywords": [
                r'\bnew\b(?!.*previously)',  # "new" 但不含 "previously"
                r'\bre-presented\b',
                r'\bre-homologated\b',
                r'\bafter\s+modification\b',
                r'\bnew\s+specification\b',
                r'\bupgrade\b',
                r'\bupgraded\b',
                r'\bdevelopment\b',
                r'\bimproved\b',
                r'\benhanced\b',
                r'\bnew\s+design\b',
                r'\bmodified\s+design\b'
            ],
            "priority": 1  # 最高優先級
        },
        
        "重大更新 (Major Update)": {
            "description": "結構性改動、觸發 FIA 重新檢驗、但非全新套件",
            "keywords": [
                r'\bfloor\s+assembly\b',
                r'\bsidepod\s+assembly\b',  # 側箱總成
                r'\bsurvival\s+cell\b',
                r'\bmonocoque\b',
                r'\bchassis\b(?!.*saver)',  # chassis 但不是 saver plate
                r'\bgearbox\s+assembly\b',
                r'\bICE\b(?!.*sump)(?!.*cooling)(?!.*previously)',  # ICE 但不是 sump/cooling/previously
                r'\bMGU-[HK]\b(?!.*previously)',  # MGU 但不是 previously used
                r'\bturbo\b(?!.*previously)',
                r'\benergy\s+store\b(?!.*previously)',
                r'\bES\b(?=\s*\()(?!.*previously)',  # ES 後面有括號，但不是 previously
                r'\bCE\b(?=\s*\()(?!.*previously)',  # CE 後面有括號，但不是 previously
                r'\bECU\b(?!.*previously)',  # ECU 電子控制單元
                r'\bTAG\d+\s+ECU\b',  # TAG ECU（如 TAG320）
                r'\bSECU\b',  # 標準電子控制單元
                r'\bthrottle\s+motor\s+unit\b',  # 油門馬達單元
                r'\bthrottle\s+electric\s+motor\b',  # 電動油門馬達
            ],
            "priority": 2
        },
        
        "變更 (Change)": {
            "description": "Parc Fermé 內合法調整、空力/配置切換、摩擦材料更換、懸吊配置",
            "keywords": [
                r'\bwing\s+assembly\b',
                r'\bfront\s+wing\b',
                r'\brear\s+wing\b',
                r'\bbeam\s+wing\b',  # 後翼樑
                r'\bfloor\s+edge\b',
                r'\bfloor\s+stay\b',
                r'\bfloor\s+bolt\b',  # 底板螺栓
                r'\bforward\s+floor\s+panel\b',  # 底板前段
                r'\bbib\s+structure\b',  # Bib 結構
                r'\bbib\s+assembly\b',  # T-tray/Bib
                r'\bbib\s+tower\b',  # Bib 塔架
                r'\bt-tray\b',
                r'\bsuspension\s+assembly\b',  # 懸吊總成
                r'\bsuspension\s+assemblies\b',  # 懸吊總成（複數）
                r'\bsuspension\s+closing\s+panel\b',
                r'\bsuspension\s+fairing\b',
                r'\bwishbone\b',  # 懸吊臂
                r'\bpullrod\b',  # 拉桿
                r'\btrackrod\b',  # 橫拉桿
                r'\btrack\s+rod\b',
                r'\bheave\s+damper\b',  # 抗下壓阻尼器
                r'\btorsion\s+bar\b',  # 扭力桿
                r'\banti\s+roll\s+bar\b',  # 防傾桿
                r'\bdrop\s+link\b',  # 連桿
                r'\bRARB\s+closing\s+panels\b',  # RARB 關閉面板
                r'\bbrake\s+duct\b',
                r'\bbrake\s+duct\s+deflector\b',  # 煞車導流板
                r'\bendplate\b',
                r'\bflap\b',
                r'\bdiveplane\b',
                r'\bwinglet\b',
                r'\bbodywork\b',
                r'\bengine\s+cover\b',
                r'\bfriction\s+material\b',  # 摩擦材料
                r'\bbrake\s+friction\b',
                r'\bclutch\s+friction\b',
                r'\bconfiguration\b',
                r'\bsidepod(?!.*deflector)\b',  # 側箱（但不是小導流板）
                r'\bside\s+pod(?!.*deflector)\b',  # 側箱（含空格）
                r'\bsidepods\b',  # 側箱（複數形式）
                r'\btransponder\s+fairing\b',  # 應答器整流罩
                r'\bseating\s+assembly\b',  # 座椅總成
                r'\bdeflector(?!.*small)\b'  # 導流板（但不是小型的）
            ],
            "priority": 3
        },
        
        "參數調整 (Parameter Adjustment)": {
            "description": "軟體參數調整、校準、設定變更（不涉及硬體更換）",
            "keywords": [
                r'\bparameter\s+changes\b',
                r'\bparameter\s+adjustment\b',
                r'\bcalibration\b',
                r'\bsoftware\s+update\b',
                r'\bsettings\b',
                r'\btuning\b',
                r'\bmap\s+change\b',
                r'\bassociated\s+with.*replacement\b',  # 與硬體更換相關的參數調整
                r'\bparameter.*associated\b'
            ],
            "priority": 4
        },
        
        "安全/標準件 (Safety/Standard Parts)": {
            "description": "FIA 標準安全設備、駕駛介面、強制性部件",
            "keywords": [
                r'\bsteering\s+wheel\b',
                r'\bsteering\s+rack\b',
                r'\bsteering\s+column\b',
                r'\bheadrest\b',
                r'\bseatbelts?\b',  # 座椅安全帶（支援複數）
                r'\bseat\s+belts?\b',  # 座椅安全帶（支援複數）
                r'\bcrotch\s+belt\b',
                r'\bfire\s+extinguisher\b',
                r'\bFOM\s+microphone\b',
                r'\bFOM\s+camera\b',
                r'\bhelmet\s+camera\b',  # 頭盔攝影機
                r'\bthrottle\s+pedal\b',
                r'\bbrake\s+pedal\b',
                r'\bdriver\s+cooling\b',
                r'\bdriver.*cooling\s+store\b',
                r'\bdriver.*cooling\s+medium\b',
                r'\bDCS\s+cooling\b',  # Driver Cooling System
                r'\bBBW\s+unit\b',  # Brake-By-Wire
                r'\bBBW\b(?!\s+unit)',  # BBW (單獨出現)
                r'\bF1\s+MS\s+CDM',  # FIA 標準電子設備
                r'\bwindscreen\b',  # 擋風玻璃
                r'\brain\s+light\b',  # 雨燈
                r'\bto\s+the\s+stewards',  # PDF 文件標記（需過濾）
                r'\bdocument\s+\d+',  # PDF 文件編號（需過濾）
                r'\bfrom\s+the\s+fia\b',  # FIA 文件標記
                r'\btime\s+\d+:\d+\b',  # 時間戳記（PDF 解析誤判）
                r'\bdate\s+\d+\b'  # 日期（PDF 誤判）
            ],
            "priority": 5
        },
        
        "維修 (Repair)": {
            "description": "損壞後更換舊件或備件、小零件維護、冷卻系統管路",
            "keywords": [
                r'\bpreviously\s+used\b',
                r'\bdamaged\b',
                r'\breplacement\b(?!.*new)',
                r'\bupright\s+assembly\b',  # 立柱總成
                r'\bupright\s+cooling\b',  # 立柱冷卻
                r'\boutboard\s+suspension\b',
                r'\boutboard\s+rear\s+suspension\b',  # 外側後懸吊
                r'\binboard\s+suspension\b',
                r'\brear\s+suspension\b',  # 後懸吊
                r'\bsuspension\s+leg\b',  # 懸吊腿
                r'\bwishbone\s+leg\b',  # 懸吊臂腿
                r'\blower\s+forward\s+leg\b',  # 下前腿
                r'\brear\s+lower\s+forward\s+leg\b',  # 後下前腿
                r'\btrack\s+rod(?!.*assembly)\b',  # 拉桿（非總成）
                r'\baxle\s+plug\b',  # 軸塞
                r'\baxle\s+bung\b',  # 軸塞
                r'\bwheel\s+retention\b',  # 輪胎固定裝置
                r'\bwheel\s+nut\s+retention\b',  # 輪帽固定
                r'\bwheel\s+retainer\b',  # 輪胎固定器
                r'\bdisc\s+mounting\s+flange\b',  # 碟盤安裝法蘭
                r'\bdisc\s+mounting\s+flanges\b',  # 碟盤安裝法蘭（複數）
                r'\bfront\s+disc\s+mounting\s+flanges?\b',  # 前碟盤法蘭
                r'\bbrake\s+calipers?\b',  # 煞車卡鉗（支援複數）
                r'\bbrake\s+drum\b',  # 煞車鼓
                r'\bradiator\b',  # 散熱器
                r'\bradiator\s+skirt\b',  # 散熱器裙板
                r'\bcharge\s+air\s+cooler\b',  # 中冷器
                r'\boil\s+cooler\b',  # 機油冷卻器
                r'\bwastegate\b',  # 廢氣閥
                r'\bactuator\b',  # 執行器
                r'\bsensor\b',
                r'\bhose\b',
                r'\bpipe(?!.*assembly)\b',  # 管路（非總成）
                r'\bpipes\b',  # 管路（複數）
                r'\bCAC\s+return\s+pipes\b',  # 中冷器回流管
                r'\bcooling\s+pipe\b',
                r'\bcooling\s+duct(?!.*assembly)\b',  # 冷卻管道（非總成）
                r'\bcooling\s+exit\s+duct\b',  # 冷卻出口
                r'\bcooling\s+medium\b',  # 冷卻介質
                r'\bwater\s+cooling\b',
                r'\blift\s+pump\b',
                r'\bPRV\b',  # Pressure Relief Valve 壓力釋放閥
                r'\bPAS\s+assembly\b',  # 動力轉向總成
                r'\bPAS\s+rack\b',  # Power Assisted Steering
                r'\boil\s+filter\s+housing\b',  # 油濾殼
                r'\bretention\s+clip\b',  # 固定夾
                r'\bretention\s+device\b',  # 固定裝置
                r'\bwastegate\s+cooling\b',  # 廢氣閥冷卻
                r'\bfuel\s+system\s+internals\b',  # 燃油系統內部件
                r'\bharness\b',  # 線束
                r'\binterface\s+harness\b',  # 介面線束
                r'\bradio\s+harness\b',  # 無線電線束
                r'\bpitot\s+assembly\b',  # 皮托管總成
                r'\bMEMS\s+box\b',  # MEMS 感測器盒
                r'\bstrain\s+gauge\b',  # 應變計
                r'\bbattery\b',  # 電池
                r'\bbatteries\b',  # 電池（複數）
                r'\bLV\s+battery\b',  # 低壓電池
                r'\bcover\b',  # 蓋板
                r'\bhatch\b',  # 檢修口
                r'\bshroud\b',  # 護罩
                r'\bshrouds\b',  # 護罩（複數）
                r'\bhalo\s+shrouds?\b',  # Halo 護罩（單複數）
                r'\belectronic\s+box\b',  # 電子盒
                r'\binfill\b',  # 填充件
                r'\bseal\b',
                r'\bgasket\b',
                r'\bo-ring\b',  # O型環
                r'\bcirclip\b',  # 扣環
                r'\brubber\b',
                r'\bfoam\b',
                r'\bfixings\b',
                r'\bfastener\b',
                r'\bbearing\b',
                r'\bplank\b',
                r'\bskid\b',
                r'\bwear\s+component\b',
                r'\bgaiter\b',  # 護套
                r'\bmirror\s+lens\b',  # 後視鏡鏡片
                r'\bmirror\s+lense\b',  # 後視鏡鏡片（拼寫錯誤）
                r'\bmirror\s+assembl(?:y|ies)\b',  # 後視鏡總成（單複數）
                r'\blaser\s+lens\b',  # 雷射鏡片
                r'\bride\s+height\s+laser\b',  # 車高雷射
                r'\bdeflector(?!.*assembly)\b',  # 導流板（小零件）
                r'\blower\s+deflector\b',  # 前下導流板
                r'\blower\s+deflectors\b',  # 前下導流板（複數）
                r'\bfront\s+lower\s+deflectors?\b',  # 前下導流板（單複數）
                r'\bpotentiometer\b',  # 電位計
                r'\bsaver\s+plate\b',  # 保護板
                r'\bbumper(?!.*assembly)\b',  # 緩衝器（小零件）
                r'\bsump\s+bumper\b',  # 油底殼緩衝器
                r'\bprotection\b',  # 保護件
                r'\bconnector\b',  # 連接器
                r'\bwiggins\b',  # Wiggins 快速接頭
                r'\bQD\s+fitting\b',  # 快速接頭
                r'\bdetonator\b',  # 爆破裝置（滅火器）
                r'\bbottle\b',  # 瓶罐
                r'\bfuel\s+cell\b',  # 油箱（小零件更換）
                r'\bfuel\s+injectors?\b',  # 燃油噴嘴（單複數）
                r'\bfilm\b',  # 保護膜
                r'\bfloor\s+film\b',  # 底板保護膜
                r'\bsilicone\s+pad\b',  # 矽膠墊
                r'\bgas\s+strut\b',  # 氣壓桿
                r'\bspark\s+plug\b',  # 火星塞
                r'\bfuel\s+injector\b',  # 燃油噴嘴
                r'\bantenna\b',  # 天線
                r'\bSRU\s+antenna\b',  # 短距離天線
                r'\bsealing\s+panel\b',  # 密封板
                r'\bengine\s+sealing\s+panel\b',  # 引擎密封板
                r'\bcantilever\s+adjuster\b',  # 懸臂調整器
                r'\bHIU\s+housing\b',  # HIU 外殼
                r'\btailpipe\b',  # 排氣尾管
                r'\bexhaust\s+tailpipe\b',  # 排氣尾管
                r'\bdriveshaft\b',  # 傳動軸
                r'\bdriveshafts\b',  # 傳動軸（複數）
                r'\bbracket\b',  # 支架
                r'\bSIS\s+bracket\b',  # SIS 支架
                r'\bstay(?!.*assembly)\b'  # 支撐桿（非總成）
            ],
            "priority": 6  # 最低優先級（最後檢查）
        }
    }
    
    def classify_part_change(self, part_name: str, original_text: str = "") -> dict:
        """
        分類單一部件變更
        
        Args:
            part_name: 部件名稱
            original_text: 原始 FIA 文件文本（可選，提供更準確的分類）
        
        Returns:
            {
                "變更類型": "升級套件 (Upgrade Package)",
                "類型說明": "...",
                "匹配關鍵字": ["new", "specification"],
                "信心度": 0.95
            }
        """
        # 合併文本進行分析
        full_text = f"{part_name} {original_text}".lower()
        
        # 儲存所有匹配結果
        matches = []
        
        for classification, config in self.CLASSIFICATIONS.items():
            matched_keywords = []
            
            for keyword_pattern in config["keywords"]:
                if re.search(keyword_pattern, full_text, re.IGNORECASE):
                    # 提取實際匹配的文字
                    match = re.search(keyword_pattern, full_text, re.IGNORECASE)
                    if match:
                        matched_keywords.append(match.group(0))
            
            if matched_keywords:
                # 計算信心度（匹配的關鍵字越多，信心度越高）
                confidence = min(0.5 + len(matched_keywords) * 0.15, 0.99)
                
                matches.append({
                    "變更類型": classification,
                    "類型說明": config["description"],
                    "匹配關鍵字": matched_keywords,
                    "信心度": round(confidence, 2),
                    "優先級": config["priority"]
                })
        
        # 按優先級排序（優先級數字越小越優先）
        if matches:
            matches.sort(key=lambda x: (x["優先級"], -x["信心度"]))
            return matches[0]
        
        # 無法分類
        return {
            "變更類型": "未分類 (Unclassified)",
            "類型說明": "無法根據現有規則分類",
            "匹配關鍵字": [],
            "信心度": 0.0
        }
    
    def classify_batch(self, upgrades: list) -> list:
        """
        批次分類多個升級記錄
        
        Args:
            upgrades: 升級記錄列表，每個記錄需包含 "部件" 和 "原始文本" 欄位
        
        Returns:
            添加了分類資訊的升級記錄列表
        """
        classified = []
        
        for upgrade in upgrades:
            part_name = upgrade.get("部件", "")
            original_text = upgrade.get("原始文本", "")
            
            # 執行分類
            classification = self.classify_part_change(part_name, original_text)
            
            # 添加分類資訊
            upgrade_with_class = upgrade.copy()
            upgrade_with_class["變更類型資訊"] = classification
            
            classified.append(upgrade_with_class)
        
        return classified
    
    def get_classification_stats(self, classified_upgrades: list) -> dict:
        """獲取分類統計"""
        stats = {
            "總記錄數": len(classified_upgrades),
            "各類型統計": {}
        }
        
        for upgrade in classified_upgrades:
            change_type = upgrade.get("變更類型資訊", {}).get("變更類型", "未分類")
            
            if change_type not in stats["各類型統計"]:
                stats["各類型統計"][change_type] = {
                    "數量": 0,
                    "百分比": 0.0
                }
            
            stats["各類型統計"][change_type]["數量"] += 1
        
        # 計算百分比
        total = len(classified_upgrades)
        for type_info in stats["各類型統計"].values():
            type_info["百分比"] = round(type_info["數量"] / total * 100, 2)
        
        return stats


def main():
    """測試分類器"""
    classifier = UpgradeClassifier()
    
    # 測試案例
    test_cases = [
        {
            "部件": "Front wing assembly (new specification)",
            "原始文本": "Car 04: Front wing assembly (new specification)"
        },
        {
            "部件": "Floor assembly (excluding skids and plank)",
            "原始文本": "Car 18: Floor assembly (excluding skids and plank)"
        },
        {
            "部件": "ICE (previously used)",
            "原始文本": "Car 30: ICE (previously used)"
        },
        {
            "部件": "LHS front wing endplate",
            "原始文本": "Car 23: LHS front wing endplate"
        },
        {
            "部件": "Survival cell (in accordance with Article 27.1)",
            "原始文本": "Car 43: Survival cell (in accordance with Article 27.1)"
        },
        {
            "部件": "ICE sump rubber",
            "原始文本": "Car 04: ICE sump rubber"
        },
        {
            "部件": "Gearbox assembly and associated control hydraulics",
            "原始文本": "Car 04: Gearbox assembly and associated control hydraulics"
        },
        {
            "部件": "Floor edge winglet array (new design)",
            "原始文本": "Car 30: Floor edge winglet array (new design)"
        }
    ]
    
    print("\n" + "="*100)
    print("🔍 部件變更類型分類器測試")
    print("="*100)
    
    for i, test_case in enumerate(test_cases, 1):
        result = classifier.classify_part_change(
            test_case["部件"], 
            test_case["原始文本"]
        )
        
        print(f"\n測試 {i}:")
        print(f"  部件: {test_case['部件']}")
        print(f"  分類: {result['變更類型']}")
        print(f"  說明: {result['類型說明']}")
        print(f"  關鍵字: {', '.join(result['匹配關鍵字'])}")
        print(f"  信心度: {result['信心度']:.0%}")
    
    print("\n" + "="*100)
    print("✅ 分類規則:")
    print("="*100)
    
    for classification, config in classifier.CLASSIFICATIONS.items():
        print(f"\n{classification}")
        print(f"  說明: {config['description']}")
        print(f"  關鍵字範例: {', '.join(config['keywords'][:5])}")


if __name__ == '__main__':
    main()
