#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
賽道分類定義模組

用途：為 FP->Q 預測提供賽道分類，支援按類別訓練獨立模型
創建時間：2025-11-02
相關文檔：docs/develop task/CLI develop task/AI分析FP,Q,R-精簡版.md
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# 賽道分類定義
TRACK_CATEGORIES = {
    # 高速賽道（引擎馬力、直線速度主導）
    "high_speed": [
        "Monza",                    # 義大利 GP - 最高速賽道
        "Spa-Francorchamps",        # 比利時 GP - 高速+技術
        "Spa",                      # 比利時 GP（別名）
        "Silverstone",              # 英國 GP - 高速彎道
        "Jeddah",                   # 沙烏地阿拉伯 GP - 長直線
        "Baku",                     # 亞塞拜然 GP - 長直線（兼具街道特性）
        "Azerbaijan",               # 亞塞拜然 GP（別名）
    ],
    
    # 街道賽道（底盤穩定性、煞車、精準度）
    "street": [
        "Monaco",                   # 摩納哥 GP - 最窄賽道
        "Monte Carlo",              # 摩納哥 GP（別名）
        "Singapore",                # 新加坡 GP - 夜間街道
        "Marina Bay",               # 新加坡 GP（別名）
        "Miami",                    # 邁阿密 GP - 新街道
        "Las Vegas",                # 拉斯維加斯 GP - 夜間街道
    ],
    
    # 混合賽道（綜合平衡，無明顯偏重）
    "mixed": [
        "Suzuka",                   # 日本 GP - 技術賽道
        "Barcelona",                # 西班牙 GP - 測試基準
        "Catalunya",                # 西班牙 GP（別名）
        "Austin",                   # 美國 GP - 綜合挑戰
        "Circuit of the Americas",  # 美國 GP（別名）
        "Interlagos",               # 巴西 GP - 短而精
        "São Paulo",                # 巴西 GP（別名）
        "Melbourne",                # 澳洲 GP - 半街道
        "Albert Park",              # 澳洲 GP（別名）
        "Zandvoort",                # 荷蘭 GP - 技術彎道
        "Imola",                    # 艾米利亞-羅馬涅 GP - 老式賽道
        "Emilia Romagna",           # 艾米利亞-羅馬涅 GP（別名）
        "Hungaroring",              # 匈牙利 GP - 狹窄彎道
        "Hungary",                  # 匈牙利 GP（別名）
        "Red Bull Ring",            # 奧地利 GP - 短而快
        "Austria",                  # 奧地利 GP（別名）
        "Spielberg",                # 奧地利 GP（別名）
        "Bahrain",                  # 巴林 GP - 沙漠賽道
        "Sakhir",                   # 巴林 GP（別名）
        "Saudi Arabia",             # 沙烏地阿拉伯 GP（若非 Jeddah）
        "China",                    # 中國 GP - 上海
        "Shanghai",                 # 中國 GP（別名）
        "Canada",                   # 加拿大 GP - 半街道
        "Montreal",                 # 加拿大 GP（別名）
        "Circuit Gilles Villeneuve", # 加拿大 GP（別名）
        "France",                   # 法國 GP - Paul Ricard
        "Paul Ricard",              # 法國 GP（別名）
        "Mexico",                   # 墨西哥 GP - 高海拔
        "Mexico City",              # 墨西哥 GP（別名）
        "Abu Dhabi",                # 阿布達比 GP - 混合類型
        "Yas Marina",               # 阿布達比 GP（別名）
        "Portugal",                 # 葡萄牙 GP - Portimão
        "Portimão",                 # 葡萄牙 GP（別名）
        "Algarve",                  # 葡萄牙 GP（別名）
        "Turkey",                   # 土耳其 GP - Istanbul Park
        "Istanbul",                 # 土耳其 GP（別名）
        "Russia",                   # 俄羅斯 GP - Sochi
        "Sochi",                    # 俄羅斯 GP（別名）
        "Japan",                    # 日本 GP（若非 Suzuka）
        "Belgium",                  # 比利時 GP（備用）
        "Italy",                    # 義大利 GP（備用，若非 Monza 則為 Imola）
        "Great Britain",            # 英國 GP（備用）
        "United States",            # 美國 GP（備用）
        "Brazil",                   # 巴西 GP（備用）
        "Australia",                # 澳洲 GP（備用）
        "Netherlands",              # 荷蘭 GP（備用）
        "Hungary",                  # 匈牙利 GP（備用）
    ]
}


def get_track_category(race_name: str) -> str:
    """
    根據賽事名稱獲取賽道類別
    
    Args:
        race_name: 賽事名稱（如 "Japan", "Monza", "Singapore"）
        
    Returns:
        str: 賽道類別（"high_speed", "street", "mixed"）
        
    Examples:
        >>> get_track_category("Monza")
        'high_speed'
        >>> get_track_category("Monaco")
        'street'
        >>> get_track_category("Japan")
        'mixed'
    """
    if not race_name:
        return "mixed"  # 預設為混合類型
    
    # 標準化賽事名稱（移除多餘空格、統一大小寫）
    race_name_normalized = race_name.strip()
    
    # 逐個類別檢查
    for category, tracks in TRACK_CATEGORIES.items():
        for track in tracks:
            # 不區分大小寫的比對
            if track.lower() in race_name_normalized.lower() or \
               race_name_normalized.lower() in track.lower():
                return category
    
    # 未找到匹配，預設為混合類型
    print(f"[WARNING] 賽道 '{race_name}' 未在分類清單中，預設為 'mixed'")
    return "mixed"


def get_all_categories() -> list:
    """
    獲取所有賽道類別
    
    Returns:
        list: 類別清單 ["high_speed", "street", "mixed"]
    """
    return list(TRACK_CATEGORIES.keys())


def get_tracks_in_category(category: str) -> list:
    """
    獲取指定類別的所有賽道
    
    Args:
        category: 賽道類別（"high_speed", "street", "mixed"）
        
    Returns:
        list: 賽道名稱清單
    """
    return TRACK_CATEGORIES.get(category, [])


def get_category_statistics() -> dict:
    """
    獲取賽道分類統計資訊
    
    Returns:
        dict: 各類別賽道數量
    """
    return {
        category: len(tracks) 
        for category, tracks in TRACK_CATEGORIES.items()
    }


# 測試代碼
if __name__ == "__main__":
    print("賽道分類定義測試")
    print("=" * 60)
    
    # 測試 1: 獲取類別
    test_races = [
        "Monza", "Monaco", "Japan", "Suzuka", 
        "Singapore", "Silverstone", "Unknown Track"
    ]
    
    print("\n測試 1: 賽道分類")
    for race in test_races:
        category = get_track_category(race)
        print(f"  {race:20s} → {category}")
    
    # 測試 2: 統計資訊
    print("\n測試 2: 分類統計")
    stats = get_category_statistics()
    for category, count in stats.items():
        print(f"  {category:12s}: {count} 個賽道")
    
    # 測試 3: 列出各類別賽道
    print("\n測試 3: 各類別賽道清單")
    for category in get_all_categories():
        tracks = get_tracks_in_category(category)
        print(f"\n{category.upper()}:")
        for i, track in enumerate(tracks[:5], 1):  # 只顯示前 5 個
            print(f"  {i}. {track}")
        if len(tracks) > 5:
            print(f"  ... 還有 {len(tracks) - 5} 個")
