"""
測試 Workspace 載入成功訊息的多國語言化
Test workspace load success message i18n
"""

import sys
import os

# 設定 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.gui_i18n import tr, set_gui_language

def test_workspace_load_i18n():
    """測試 Workspace 載入相關的所有翻譯"""
    
    print("=" * 80)
    print("測試 Workspace 載入成功訊息多國語言化")
    print("Testing Workspace Load Success Message i18n")
    print("=" * 80)
    
    # 測試的翻譯鍵值
    test_keys = [
        ('workspace_load_success_title', {}),
        ('workspace_load_success_message', {'tabs': 4, 'windows': 14}),
        ('workspace_load_failed_title', {}),
        ('workspace_load_failed_message', {}),
        ('workspace_load_error_title', {}),
        ('workspace_load_error_message', {'error': 'Connection timeout'}),
    ]
    
    # 測試三種語言
    languages = [
        ('zh', '中文'),
        ('en', 'English'),
        ('ja', '日本語')
    ]
    
    for lang_code, lang_name in languages:
        print(f"\n{'=' * 80}")
        print(f"語言 / Language: {lang_name} ({lang_code})")
        print('=' * 80)
        
        set_gui_language(lang_code)
        
        for key, params in test_keys:
            try:
                if params:
                    result = tr(key).format(**params)
                else:
                    result = tr(key)
                    
                print(f"\n✅ {key}:")
                print(f"   {result}")
                
            except Exception as e:
                print(f"\n❌ {key}: 錯誤 - {e}")
    
    print("\n" + "=" * 80)
    print("✅ 所有翻譯測試完成！")
    print("=" * 80)
    
    # 測試實際使用場景
    print("\n" + "=" * 80)
    print("實際使用場景示範 (Practical Usage Example)")
    print("=" * 80)
    
    for lang_code, lang_name in languages:
        print(f"\n{lang_name} ({lang_code}):")
        print("-" * 60)
        
        set_gui_language(lang_code)
        
        # 成功載入訊息
        print(f"\n📥 {tr('workspace_load_success_title')}")
        print(tr('workspace_load_success_message').format(tabs=4, windows=14))
        
        # 載入失敗訊息
        print(f"\n❌ {tr('workspace_load_failed_title')}")
        print(tr('workspace_load_failed_message'))
        
        # 載入錯誤訊息
        print(f"\n⚠️ {tr('workspace_load_error_title')}")
        print(tr('workspace_load_error_message').format(error='Database connection failed'))

if __name__ == '__main__':
    test_workspace_load_i18n()
