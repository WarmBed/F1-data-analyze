#!/usr/bin/env python3
"""
Tab 標籤多國語言化修復驗證腳本
測試不同語言下 Tab 標籤的數字格式
"""

import sys
from core.gui_i18n import set_gui_language, get_gui_language, tr

def _convert_to_chinese_number(num: int) -> str:
    """將數字轉換為中文數字（一、二、三...）"""
    chinese_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
                    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"]
    if 1 <= num <= 20:
        return chinese_nums[num - 1]
    else:
        return str(num)

def generate_tab_name(tab_count: int) -> str:
    """生成 Tab 標籤名稱（模擬修復後的邏輯）"""
    current_lang = get_gui_language()
    if current_lang == "zh":
        number_str = _convert_to_chinese_number(tab_count)
    else:
        number_str = str(tab_count)
    tab_name = tr("tab_page", "Tab {number}").format(number=number_str)
    return tab_name

def test_tab_names():
    """測試不同語言下的 Tab 標籤生成"""
    print("=" * 80)
    print("Tab 標籤多國語言化修復驗證")
    print("=" * 80)
    
    languages = ["zh", "en", "ja"]
    tab_counts = [1, 2, 3, 5, 10]
    
    for lang in languages:
        print(f"\n{'─' * 80}")
        print(f"🌐 語言: {lang.upper()}")
        print(f"{'─' * 80}")
        
        set_gui_language(lang)
        current = get_gui_language()
        print(f"✅ 當前語言設定: {current}")
        
        print(f"\n生成的 Tab 標籤:")
        for count in tab_counts:
            tab_name = generate_tab_name(count)
            print(f"  Tab {count}: {tab_name}")
    
    print(f"\n{'=' * 80}")
    print("✅ 測試完成")
    print("=" * 80)
    
    # 驗證期望結果
    print("\n預期結果驗證:")
    print("─" * 80)
    
    # 中文
    set_gui_language("zh")
    assert generate_tab_name(1) == "分頁一", "❌ 中文測試失敗"
    assert generate_tab_name(2) == "分頁二", "❌ 中文測試失敗"
    print("✅ 中文語言測試通過 - Tab 使用中文數字（一、二、三）")
    
    # 英文
    set_gui_language("en")
    assert generate_tab_name(1) == "Tab 1", "❌ 英文測試失敗"
    assert generate_tab_name(2) == "Tab 2", "❌ 英文測試失敗"
    print("✅ 英文語言測試通過 - Tab 使用阿拉伯數字（1, 2, 3）")
    
    # 日文
    set_gui_language("ja")
    assert generate_tab_name(1) == "Tab 1", "❌ 日文測試失敗"
    assert generate_tab_name(2) == "Tab 2", "❌ 日文測試失敗"
    print("✅ 日文語言測試通過 - Tab 使用阿拉伯數字（1, 2, 3）")
    
    print("─" * 80)
    print("\n🎉 所有測試通過！Tab 標籤多國語言化修復成功")

if __name__ == "__main__":
    try:
        test_tab_names()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
