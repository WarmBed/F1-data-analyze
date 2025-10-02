#!/usr/bin/env python3
"""
語言系統切換深度測試
Language System Switching Deep Test
測試即時切換和檢查硬編碼問題
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.gui_i18n import tr, set_gui_language, get_gui_language

def test_basic_translation():
    """測試基本翻譯功能"""
    print("=" * 80)
    print("1. 測試基本翻譯功能")
    print("=" * 80)
    
    languages = ['en', 'zh', 'ja']
    test_keys = [
        'main_window_title',
        'ok',
        'cancel',
        'year_label',
        'race_label',
        'session_label',
        'ready',
    ]
    
    for lang in languages:
        set_gui_language(lang)
        print(f"\n--- 語言: {lang} ---")
        for key in test_keys:
            result = tr(key, f'[MISSING: {key}]')
            print(f"  {key:30} = {result}")

def test_messagebox_translations():
    """測試 QMessageBox 相關的翻譯鍵"""
    print("\n" + "=" * 80)
    print("2. 測試 QMessageBox 對話框翻譯鍵")
    print("=" * 80)
    
    # 這些是應該要有翻譯但可能缺少的鍵
    messagebox_keys = [
        'confirm_exit',
        'confirm_exit_title',
        'confirm_exit_message',
        'analysis_failed',
        'warning',
        'error',
        'information',
        'question',
        'api_check',
        'api_check_running',
        'api_restored',
        'tip',
        'no_charts_selected',
        'no_driver_selected',
        'module_unavailable',
        'track_analysis_unavailable',
        'cannot_find_mdi_area',
        'cannot_open_window',
        'language_switched',
        'language_switched_to',
    ]
    
    languages = ['en', 'zh', 'ja']
    
    for lang in languages:
        set_gui_language(lang)
        print(f"\n--- 語言: {lang} ---")
        missing_translations = []
        
        for key in messagebox_keys:
            result = tr(key, None)
            if result is None or result == key:
                missing_translations.append(key)
                print(f"  ❌ {key:40} = [MISSING]")
            else:
                print(f"  ✅ {key:40} = {result}")
        
        if missing_translations:
            print(f"\n  ⚠️  缺少 {len(missing_translations)} 個翻譯鍵")
        else:
            print(f"\n  ✅ 所有翻譯鍵完整")

def test_instant_switch():
    """測試即時切換"""
    print("\n" + "=" * 80)
    print("3. 測試即時語言切換")
    print("=" * 80)
    
    test_key = 'main_window_title'
    
    print(f"\n測試鍵: {test_key}")
    print("-" * 80)
    
    # 切換順序: en -> zh -> ja -> en
    languages = ['en', 'zh', 'ja', 'en']
    
    for lang in languages:
        set_gui_language(lang)
        current_lang = get_gui_language()
        result = tr(test_key)
        
        print(f"切換到 {lang:2} | 當前: {current_lang:2} | 結果: {result}")
        
        # 驗證是否真的切換了
        if current_lang != lang:
            print(f"  ❌ 語言切換失敗！期望 {lang}，實際 {current_lang}")
        else:
            print(f"  ✅ 語言切換成功")

def find_hardcoded_messagebox():
    """掃描主程式找出硬編碼的 QMessageBox"""
    print("\n" + "=" * 80)
    print("4. 掃描硬編碼的 QMessageBox")
    print("=" * 80)
    
    main_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'f1t_gui_main.py')
    
    if not os.path.exists(main_file):
        print(f"❌ 找不到檔案: {main_file}")
        return
    
    print(f"掃描檔案: {main_file}\n")
    
    hardcoded_patterns = []
    
    with open(main_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines, 1):
        # 檢查 QMessageBox 相關呼叫
        if 'QMessageBox.' in line and any(method in line for method in ['warning', 'information', 'question', 'critical']):
            # 檢查是否有中文字元（硬編碼的證據）
            if any('\u4e00' <= char <= '\u9fff' for char in line):
                hardcoded_patterns.append((i, line.strip()))
    
    if hardcoded_patterns:
        print(f"找到 {len(hardcoded_patterns)} 個硬編碼的 QMessageBox 呼叫：\n")
        for line_num, content in hardcoded_patterns:
            print(f"行 {line_num:5}: {content[:100]}...")
    else:
        print("✅ 未發現硬編碼的 QMessageBox")

def check_translation_completeness():
    """檢查翻譯完整性"""
    print("\n" + "=" * 80)
    print("5. 檢查翻譯完整性")
    print("=" * 80)
    
    # 從 gui_i18n.py 讀取所有翻譯鍵
    i18n_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core', 'gui_i18n.py')
    
    if not os.path.exists(i18n_file):
        print(f"❌ 找不到檔案: {i18n_file}")
        return
    
    print(f"分析檔案: {i18n_file}\n")
    
    # 統計每種語言的翻譯數量
    lang_stats = {'zh': 0, 'en': 0, 'ja': 0}
    total_keys = 0
    
    with open(i18n_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 簡單計數（這不是完美的方法，但可以快速了解）
    import re
    
    # 查找所有翻譯條目
    pattern = r"'([^']+)':\s*\{[^}]*'zh':\s*'([^']*)'[^}]*'en':\s*'([^']*)'[^}]*'ja':\s*'([^']*)'"
    matches = re.findall(pattern, content)
    
    total_keys = len(matches)
    
    for match in matches:
        key, zh, en, ja = match
        if zh: lang_stats['zh'] += 1
        if en: lang_stats['en'] += 1
        if ja: lang_stats['ja'] += 1
    
    print(f"總翻譯鍵數: {total_keys}")
    print(f"\n各語言完整度:")
    for lang, count in lang_stats.items():
        percentage = (count / total_keys * 100) if total_keys > 0 else 0
        status = "✅" if percentage == 100 else "⚠️"
        print(f"  {status} {lang:2}: {count:3}/{total_keys} ({percentage:5.1f}%)")

def test_specific_dialogs():
    """測試特定對話框的翻譯"""
    print("\n" + "=" * 80)
    print("6. 測試特定對話框翻譯")
    print("=" * 80)
    
    # 測試關閉確認對話框
    print("\n--- 關閉確認對話框 ---")
    
    languages = ['en', 'zh', 'ja']
    
    for lang in languages:
        set_gui_language(lang)
        
        # 應該要有的鍵
        title = tr('confirm_exit_title', '確認退出')
        message = tr('confirm_exit_message', '確定要退出 F1T 專業賽車分析工作站嗎？\n\n所有正在執行的分析將被停止。')
        yes = tr('yes', 'Yes')
        no = tr('no', 'No')
        
        print(f"\n語言: {lang}")
        print(f"  標題: {title}")
        print(f"  訊息: {message[:50]}...")
        print(f"  按鈕: {yes} / {no}")

def generate_missing_translations():
    """生成缺少的翻譯鍵建議"""
    print("\n" + "=" * 80)
    print("7. 生成缺少的翻譯鍵建議")
    print("=" * 80)
    
    # 從主程式掃描出現的硬編碼文字
    main_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'f1t_gui_main.py')
    
    if not os.path.exists(main_file):
        print(f"❌ 找不到檔案: {main_file}")
        return
    
    print(f"\n建議新增的翻譯鍵:\n")
    
    suggested_translations = {
        'confirm_exit_title': {
            'zh': '確認退出',
            'en': 'Confirm Exit',
            'ja': '終了確認'
        },
        'confirm_exit_message': {
            'zh': '確定要退出 F1T 專業賽車分析工作站嗎？\n\n所有正在執行的分析將被停止。',
            'en': 'Are you sure you want to exit F1T Professional Racing Analysis Workstation?\n\nAll running analyses will be stopped.',
            'ja': 'F1Tプロフェッショナルレーシング分析ワークステーションを終了してもよろしいですか？\n\n実行中のすべての分析が停止されます。'
        },
        'yes': {
            'zh': '是',
            'en': 'Yes',
            'ja': 'はい'
        },
        'no': {
            'zh': '否',
            'en': 'No',
            'ja': 'いいえ'
        },
        'analysis_failed': {
            'zh': '分析失敗',
            'en': 'Analysis Failed',
            'ja': '分析失敗'
        },
        'cli_analysis_error': {
            'zh': 'CLI 分析過程中發生錯誤',
            'en': 'Error occurred during CLI analysis',
            'ja': 'CLI分析中にエラーが発生しました'
        },
        'warning': {
            'zh': '警告',
            'en': 'Warning',
            'ja': '警告'
        },
        'error': {
            'zh': '錯誤',
            'en': 'Error',
            'ja': 'エラー'
        },
        'information': {
            'zh': '資訊',
            'en': 'Information',
            'ja': '情報'
        },
        'tip': {
            'zh': '提示',
            'en': 'Tip',
            'ja': 'ヒント'
        },
        'no_charts_selected': {
            'zh': '沒有選擇任何圖表，將不會開啟視窗。',
            'en': 'No charts selected. Window will not be opened.',
            'ja': 'チャートが選択されていません。ウィンドウは開きません。'
        },
        'no_driver_selected': {
            'zh': '請選擇至少一位車手。',
            'en': 'Please select at least one driver.',
            'ja': '少なくとも1人のドライバーを選択してください。'
        },
        'track_analysis_unavailable': {
            'zh': '賽道分析模組不可用',
            'en': 'Track analysis module unavailable',
            'ja': 'トラック分析モジュールは利用できません'
        },
        'cannot_find_mdi_area': {
            'zh': '無法找到當前 MDI 區域',
            'en': 'Cannot find current MDI area',
            'ja': '現在のMDIエリアが見つかりません'
        },
        'cannot_open_window': {
            'zh': '無法開啟視窗',
            'en': 'Cannot open window',
            'ja': 'ウィンドウを開けません'
        },
        'api_check': {
            'zh': 'API 檢查',
            'en': 'API Check',
            'ja': 'APIチェック'
        },
        'api_check_running': {
            'zh': 'API 健康檢查正在執行中，請稍候。',
            'en': 'API health check is already running. Please wait.',
            'ja': 'APIヘルスチェックが実行中です。お待ちください。'
        },
        'api_restored': {
            'zh': 'API 已恢復',
            'en': 'API Restored',
            'ja': 'API復元'
        }
    }
    
    print("```python")
    for key, translations in suggested_translations.items():
        print(f"'{key}': {translations},")
    print("```")

def main():
    """主測試函數"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "F1T 語言系統深度測試" + " " * 20 + "║")
    print("║" + " " * 15 + "F1T Language System Deep Test" + " " * 15 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    try:
        test_basic_translation()
        test_messagebox_translations()
        test_instant_switch()
        find_hardcoded_messagebox()
        check_translation_completeness()
        test_specific_dialogs()
        generate_missing_translations()
        
        print("\n" + "=" * 80)
        print("測試完成！Test Complete!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
