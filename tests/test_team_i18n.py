#!/usr/bin/env python3
"""
測試車隊名稱的多國語言化
Test Team Name Internationalization
"""

from core.gui_i18n import get_team_name_text, set_gui_language, get_gui_language

def test_team_i18n():
    """測試所有車隊名稱的翻譯"""
    
    # 測試車隊列表
    test_teams = [
        "Red Bull",
        "Red Bull Racing",
        "Ferrari",
        "Mercedes",
        "McLaren",
        "Aston Martin",
        "Alpine",
        "Williams",
        "RB",
        "Haas",
        "Sauber",
        "Kick Sauber",
        "AlphaTauri",
        "Alfa Romeo",
        "Unknown",
        "Red Bull Racing F1 Team",  # 測試自動去除後綴
        "McLaren F1 Team",
    ]
    
    languages = {
        'zh': '繁體中文',
        'en': 'English',
        'ja': '日本語'
    }
    
    print("=" * 80)
    print("F1 車隊名稱多國語言化測試")
    print("F1 Team Name Internationalization Test")
    print("=" * 80)
    
    for lang_code, lang_name in languages.items():
        print(f"\n{'=' * 80}")
        print(f"語言 / Language: {lang_name} ({lang_code})")
        print(f"{'=' * 80}")
        
        # 切換語言
        set_gui_language(lang_code)
        current_lang = get_gui_language()
        print(f"✓ 當前語言設定: {current_lang}\n")
        
        # 測試每個車隊
        print(f"{'原始名稱 (Original)':<30} → {'翻譯 (Translated)':<20}")
        print("-" * 80)
        for team in test_teams:
            translation = get_team_name_text(team)
            print(f"{team:<30} → {translation:<20}")
    
    print("\n" + "=" * 80)
    print("測試完成 / Test Completed")
    print("=" * 80)


if __name__ == "__main__":
    test_team_i18n()
