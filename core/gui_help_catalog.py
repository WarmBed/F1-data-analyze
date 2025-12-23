"""Help center content catalog for the GUI application."""

from __future__ import annotations

from typing import Iterable, List

from .gui_i18n import get_gui_language

_DEFAULT_LANGUAGE = "zh"

_HELP_MESSAGES = {
    "zh": (
        "F1T 遙測分析工作站\n\n"
        "1. 使用上方工具列的年份、賽事與會話選單設定分析範圍。\n"
        "2. 在左側功能樹選擇需要的分析模組，雙擊或使用右鍵選單即可開啟。\n"
        "3. 遙測、進站或圈速比較模組開啟後會顯示額外的圈速選擇控件。\n"
        "4. 若遇到 REST API 服務問題，可在「工具」>「Check API Status」執行健康檢查。\n"
        "5. 根據 2025-10-03 API-ONLY 政策，GUI 僅能透過 API 或既有 JSON 讀取資料，請手動執行 CLI 取得新數據。\n\n"
        "更多詳細教學請參考 docs/ 與 README.md，或聯繫系統維護人員。"
    ),
    "en": (
        "F1T Telemetry Analysis Workstation\n\n"
        "1. Configure the analysis scope with the toolbar selectors for year, race, and session.\n"
        "2. Choose modules from the left analysis tree; double-click or use the context menu to open them.\n"
        "3. Telemetry, pit stop, and lap-comparison modules expose extra lap selectors once opened.\n"
        "4. If the REST API reports issues, run Tools > Check API Status to trigger a health check.\n"
        "5. Per the 2025-10-03 API-ONLY policy, the GUI may only load data via the API or existing JSON files—run the CLI manually to generate fresh datasets.\n\n"
        "See docs/ and README.md for full tutorials, or contact the maintenance team for assistance."
    ),
    "ja": (
        "F1T テレメトリー分析ワークステーション\n\n"
        "1. ツールバーの年・レース・セッションを設定して分析対象を決めます。\n"
        "2. 左側の分析モジュールツリーから必要なモジュールを選び、ダブルクリックまたは右クリックメニューで開きます。\n"
        "3. テレメトリー、ピットストップ、ラップ比較モジュールを開くと、追加のラップ選択コントロールが表示されます。\n"
        "4. REST API に問題がある場合は、ツール > Check API Status でヘルスチェックを実行してください。\n"
        "5. 2025-10-03 の API-ONLY ポリシーにより、GUI は API または既存の JSON のみを読み込めます。新しいデータが必要な場合は CLI を手動で実行してください。\n\n"
        "詳細なチュートリアルは docs/ と README.md を参照するか、メンテナンスチームにお問い合わせください。"
    ),
}


def get_gui_help_message(language: str | None = None) -> str:
    """Return the help message for the requested language."""
    lang = (language or get_gui_language() or _DEFAULT_LANGUAGE).lower()
    if lang not in _HELP_MESSAGES:
        lang = _DEFAULT_LANGUAGE
    return _HELP_MESSAGES[lang]


def get_gui_help_lines(language: str | None = None) -> List[str]:
    """Return the help message split into individual lines."""
    return get_gui_help_message(language).splitlines()


def iter_gui_help_lines(language: str | None = None) -> Iterable[str]:
    """Yield help lines lazily for streaming scenarios."""
    for line in get_gui_help_lines(language):
        yield line
