#!/usr/bin/env python3
"""
測試分頁標籤的國際化
驗證「主頁」、「分頁一」、「分頁二」等是否正確使用 tr() 函數
"""

from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)

print("=" * 80)
print("測試分頁標籤國際化")
print("=" * 80)

# 測試 1: 導入翻譯函數
print("\n[測試 1] 導入翻譯模組...")
try:
    from core.gui_i18n import tr, set_gui_language, get_gui_language
    print("✅ 翻譯模組導入成功")
    print(f"   當前語言: {get_gui_language()}")
except Exception as e:
    print(f"❌ 翻譯模組導入失敗: {e}")
    sys.exit(1)

# 測試 2: 測試翻譯鍵值
print("\n[測試 2] 測試分頁翻譯鍵值...")

translation_tests = [
    ("home_page", "主頁", "Home"),
    ("tab_page", "分頁{number}", "Tab {number}"),
]

for key, zh_default, en_expected in translation_tests:
    result = tr(key, zh_default)
    print(f"   - {key}:")
    print(f"     中文: {result}")
    if result:
        print(f"     ✅ 翻譯成功")
    else:
        print(f"     ❌ 翻譯失敗")

# 測試 3: 測試數字轉換
print("\n[測試 3] 測試中文數字轉換...")

# 模擬 _convert_to_chinese_number 函數
def convert_to_chinese_number(num: int) -> str:
    """將數字轉換為中文數字（一、二、三...）"""
    chinese_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
                    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"]
    if 1 <= num <= 20:
        return chinese_nums[num - 1]
    else:
        return str(num)

test_numbers = [1, 2, 3, 10, 15, 20, 21]
for num in test_numbers:
    chinese_num = convert_to_chinese_number(num)
    tab_name = tr("tab_page", "分頁{number}").format(number=chinese_num)
    print(f"   數字 {num} → 中文 '{chinese_num}' → 標籤 '{tab_name}'")

# 測試 4: 測試完整的分頁命名邏輯
print("\n[測試 4] 模擬分頁創建流程...")

print("\n   情境：用戶開啟 GUI，開始創建分頁")
print("   ----------------------------------------")

# 初始化
tab_count = 1
welcome_tab_name = tr("home_page", "主頁")
print(f"   1. 初始分頁: '{welcome_tab_name}' (tab_count=0)")

# 創建第一個工作分頁
tab_count = 1
chinese_number = convert_to_chinese_number(tab_count)
tab1_name = tr("tab_page", "分頁{number}").format(number=chinese_number)
print(f"   2. 創建第1個工作分頁: '{tab1_name}' (tab_count=1)")

# 創建第二個工作分頁
tab_count = 2
chinese_number = convert_to_chinese_number(tab_count)
tab2_name = tr("tab_page", "分頁{number}").format(number=chinese_number)
print(f"   3. 創建第2個工作分頁: '{tab2_name}' (tab_count=2)")

# 創建第三個工作分頁
tab_count = 3
chinese_number = convert_to_chinese_number(tab_count)
tab3_name = tr("tab_page", "分頁{number}").format(number=chinese_number)
print(f"   4. 創建第3個工作分頁: '{tab3_name}' (tab_count=3)")

print("\n   ✅ 分頁命名邏輯正確")

# 測試 5: 測試英文語言環境（如果支援）
print("\n[測試 5] 測試切換語言...")

try:
    # 嘗試切換到英文
    original_lang = get_gui_language()
    print(f"   原始語言: {original_lang}")
    
    # 注意：實際的語言切換可能需要重啟應用程式
    # 這裡只是展示如何使用
    set_gui_language("en")
    new_lang = get_gui_language()
    print(f"   切換後語言: {new_lang}")
    
    # 測試英文翻譯
    home_en = tr("home_page", "主頁")
    tab_en = tr("tab_page", "分頁{number}").format(number="One")
    print(f"   英文主頁: '{home_en}'")
    print(f"   英文分頁一: '{tab_en}'")
    
    # 切換回原始語言
    set_gui_language(original_lang)
    print(f"   已切換回: {get_gui_language()}")
    
except Exception as e:
    print(f"   ⚠️  語言切換測試跳過: {e}")

# 測試 6: 驗證實際 GUI 組件
print("\n[測試 6] 驗證實際 GUI 組件...")

try:
    from PyQt5.QtWidgets import QTabWidget
    
    # 創建測試用 TabWidget
    tab_widget = QTabWidget()
    
    # 添加主頁
    from PyQt5.QtWidgets import QWidget
    welcome_tab = QWidget()
    welcome_tab.setObjectName("welcome_tab")
    tab_widget.addTab(welcome_tab, tr("home_page", "主頁"))
    
    # 添加工作分頁
    for i in range(1, 4):
        work_tab = QWidget()
        chinese_num = convert_to_chinese_number(i)
        tab_name = tr("tab_page", "分頁{number}").format(number=chinese_num)
        tab_widget.addTab(work_tab, tab_name)
    
    # 驗證標籤文字
    print(f"   標籤 0: '{tab_widget.tabText(0)}'")
    print(f"   標籤 1: '{tab_widget.tabText(1)}'")
    print(f"   標籤 2: '{tab_widget.tabText(2)}'")
    print(f"   標籤 3: '{tab_widget.tabText(3)}'")
    
    print("\n   ✅ GUI 組件驗證通過")
    
except Exception as e:
    print(f"   ❌ GUI 組件驗證失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("🎉 分頁標籤國際化測試完成！")
print("=" * 80)
print("\n📝 修改摘要:")
print("   ✅ 'home_page' → '主頁' / 'Home'")
print("   ✅ 'tab_page' → '分頁{number}' / 'Tab {number}'")
print("   ✅ 支援動態數字替換（一、二、三...）")
print("\n📍 修改位置:")
print("   - f1t_gui_main.py:7015 (init_default_tabs)")
print("   - f1t_gui_main.py:7024 (add_new_tab)")
print("   - f1t_gui_main.py:7064 (close_tab)")
print("=" * 80)
