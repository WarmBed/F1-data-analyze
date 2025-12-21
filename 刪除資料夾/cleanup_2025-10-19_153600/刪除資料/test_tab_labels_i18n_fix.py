"""
測試 Tab 標籤國際化修復
驗證 home_page 和 tab_page 翻譯是否正常運作
"""

from core.gui_i18n import tr, _gui_translator

print("="*70)
print("[TEST] Tab 標籤國際化測試")
print("="*70)

# 測試 1: 檢查當前語言設定
current_lang = _gui_translator.get_language()
print(f"\n[TEST 1] 當前語言設定: {current_lang}")

# 測試 2: 測試 home_page 翻譯
print("\n[TEST 2] home_page 翻譯測試")
home_zh = _gui_translator.t('home_page', default='主頁')
print(f"  繁體中文 (zh): {home_zh}")

_gui_translator.set_language('en')
home_en = _gui_translator.t('home_page', default='主頁')
print(f"  英文 (en): {home_en}")

_gui_translator.set_language('ja')
home_ja = _gui_translator.t('home_page', default='主頁')
print(f"  日文 (ja): {home_ja}")

# 測試 3: 測試 tab_page 翻譯（帶參數）
print("\n[TEST 3] tab_page 翻譯測試（帶參數）")
_gui_translator.set_language('zh')
tab_zh = _gui_translator.t('tab_page', default='分頁{number}').format(number='一')
print(f"  繁體中文 (zh): {tab_zh}")

_gui_translator.set_language('en')
tab_en = _gui_translator.t('tab_page', default='分頁{number}').format(number='一')
print(f"  英文 (en): {tab_en}")

_gui_translator.set_language('ja')
tab_ja = _gui_translator.t('tab_page', default='分頁{number}').format(number='一')
print(f"  日文 (ja): {tab_ja}")

# 測試 4: 測試中文數字轉換
print("\n[TEST 4] 中文數字轉換測試")
chinese_numbers = ['一', '二', '三', '四', '五']
for i, cn in enumerate(chinese_numbers, 1):
    _gui_translator.set_language('zh')
    tab_label_zh = tr('tab_page', '分頁{number}').format(number=cn)
    _gui_translator.set_language('en')
    tab_label_en = tr('tab_page', '分頁{number}').format(number=cn)
    print(f"  分頁 {i}: zh='{tab_label_zh}' | en='{tab_label_en}'")

# 測試 5: 驗證翻譯字典
print("\n[TEST 5] 驗證翻譯字典")
translations = _gui_translator._translations
if 'home_page' in translations:
    print(f"  [OK] 'home_page' 存在於翻譯字典中")
    print(f"       zh: {translations['home_page']['zh']}")
    print(f"       en: {translations['home_page']['en']}")
    print(f"       ja: {translations['home_page']['ja']}")
else:
    print(f"  [FAIL] 'home_page' 不存在於翻譯字典中")

if 'tab_page' in translations:
    print(f"  [OK] 'tab_page' 存在於翻譯字典中")
    print(f"       zh: {translations['tab_page']['zh']}")
    print(f"       en: {translations['tab_page']['en']}")
    print(f"       ja: {translations['tab_page']['ja']}")
else:
    print(f"  [FAIL] 'tab_page' 不存在於翻譯字典中")

# 恢復語言設定
_gui_translator.set_language(current_lang)

print("\n" + "="*70)
print("[TEST] 測試完成")
print("="*70)
print(f"\n[INFO] 當前語言已恢復為: {current_lang}")
print(f"[INFO] 如果要在 GUI 中顯示中文，請將語言設定改為 'zh'")
