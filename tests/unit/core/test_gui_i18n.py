"""
測試 3: core/gui_i18n.py - GUI 國際化翻譯系統
===============================================
重要發現：GuiTranslator.__init__() 會優先從設定檔讀取語言，
覆蓋傳入的 language 參數。因此測試必須透過 set_language() 
明確切換語言，而非依賴建構子參數。
"""
import pytest
from core.gui_i18n import GuiTranslator, tr, set_gui_language, get_gui_language


# ── GuiTranslator 基礎翻譯行為 ────────────────────────────────────────────────

class TestGuiTranslatorBasics:
    """GuiTranslator 的核心翻譯邏輯，使用 set_language() 明確設定語言。"""

    def test_close_key_english_returns_close(self):
        """英文語種的 'close' key 應回傳 'Close'。"""
        translator = GuiTranslator()
        translator.set_language("en")
        assert translator.t("close") == "Close"

    def test_close_key_chinese_returns_chinese(self):
        """中文語種的 'close' key 應回傳 '關閉'。"""
        translator = GuiTranslator()
        translator.set_language("zh")
        assert translator.t("close") == "關閉"

    def test_close_key_japanese_returns_japanese(self):
        """日文語種的 'close' key 應回傳 '閉じる'。"""
        translator = GuiTranslator()
        translator.set_language("ja")
        assert translator.t("close") == "閉じる"

    def test_unknown_key_returns_key_itself(self):
        """未知的 key 在沒有 default 時應回傳 key 本身。"""
        translator = GuiTranslator()
        result = translator.t("this_key_does_not_exist_xyz")
        assert result == "this_key_does_not_exist_xyz"

    def test_unknown_key_with_default_returns_default(self):
        """未知的 key 有 default 時應回傳 default。"""
        translator = GuiTranslator()
        result = translator.t("this_key_does_not_exist_xyz", default="FALLBACK")
        assert result == "FALLBACK"

    def test_f1tv_login_english_returns_login(self):
        """'f1tv_login' key 在英文語種應為 'Login'。"""
        translator = GuiTranslator()
        translator.set_language("en")
        assert translator.t("f1tv_login") == "Login"

    def test_known_key_returns_non_empty_string(self):
        """已知的 key 應回傳非空字串（任何語種）。"""
        translator = GuiTranslator()
        for lang in ("zh", "en", "ja"):
            translator.set_language(lang)
            result = translator.t("close")
            assert isinstance(result, str)
            assert len(result) > 0, f"{lang} 語種的 'close' 翻譯不得為空"

    def test_all_languages_give_different_close_values(self):
        """三個語種的 'close' 翻譯必須各自不同。"""
        translator = GuiTranslator()
        results = {}
        for lang in ("zh", "en", "ja"):
            translator.set_language(lang)
            results[lang] = translator.t("close")
        assert results["zh"] != results["en"], "中文和英文的 close 應不同"
        assert results["en"] != results["ja"], "英文和日文的 close 應不同"
        assert results["zh"] != results["ja"], "中文和日文的 close 應不同"


# ── 語言切換 ─────────────────────────────────────────────────────────────────

class TestLanguageSwitching:
    """GuiTranslator.set_language() 的語言切換行為。"""

    def test_set_language_to_zh_returns_true(self):
        """切換到 zh 應回傳 True。"""
        translator = GuiTranslator()
        assert translator.set_language("zh") is True

    def test_set_language_to_en_returns_true(self):
        """切換到 en 應回傳 True。"""
        translator = GuiTranslator()
        assert translator.set_language("en") is True

    def test_set_language_to_ja_returns_true(self):
        """切換到 ja 應回傳 True。"""
        translator = GuiTranslator()
        assert translator.set_language("ja") is True

    def test_set_language_invalid_returns_false(self):
        """切換到不支援的語種應回傳 False。"""
        translator = GuiTranslator()
        translator.set_language("en")  # 先設為已知語言
        result = translator.set_language("fr")
        assert result is False

    def test_invalid_language_does_not_change_language(self):
        """切換到無效語種後，語言應保持不變。"""
        translator = GuiTranslator()
        translator.set_language("en")
        translator.set_language("fr")  # 無效
        assert translator.get_language() == "en"

    def test_get_language_reflects_set_language(self):
        """get_language() 必須反映 set_language() 的設定。"""
        translator = GuiTranslator()
        translator.set_language("zh")
        assert translator.get_language() == "zh"

    def test_translation_changes_after_language_switch(self):
        """切換語言後，t() 的結果應改變。"""
        translator = GuiTranslator()
        translator.set_language("zh")
        zh_result = translator.t("close")
        translator.set_language("en")
        en_result = translator.t("close")
        assert zh_result != en_result, "中英文翻譯結果應不同"


# ── 全域 tr() 函數 ──────────────────────────────────────────────────────────

class TestTrGlobalFunction:
    """全域 tr() 快捷函數行為。"""

    def test_tr_returns_string(self):
        """tr() 必須回傳字串。"""
        result = tr("close")
        assert isinstance(result, str)

    def test_tr_returns_non_empty_for_known_key(self):
        """tr() 對已知 key 必須回傳非空字串。"""
        result = tr("close")
        assert len(result) > 0

    def test_tr_unknown_key_returns_key(self):
        """tr() 對未知 key 應回傳 key 本身。"""
        result = tr("nonexistent_translation_key_abc123")
        assert result == "nonexistent_translation_key_abc123"
