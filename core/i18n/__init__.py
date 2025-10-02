"""
F1T 國際化模組 - 集中式語言切換系統
支援語言：zh-TW (繁體中文), en-US (英文)
"""

from .translation_manager import TranslationManager, get_translator

# 全域翻譯器實例
_translator = TranslationManager()

def _(key: str, **kwargs) -> str:
    """
    主要翻譯函數
    
    Args:
        key: 翻譯鍵值
        **kwargs: 格式化參數
        
    Returns:
        str: 翻譯後的文字
    """
    return _translator.translate(key, **kwargs)

def set_language(language_code: str):
    """設定當前語言"""
    _translator.set_language(language_code)

def get_current_language() -> str:
    """獲取當前語言"""
    return _translator.current_language

def get_available_languages() -> list:
    """獲取可用語言列表"""
    return _translator.get_available_languages()

# 匯出主要功能
__all__ = ['_', 'set_language', 'get_current_language', 'get_available_languages', 'TranslationManager', 'get_translator']
